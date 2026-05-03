"""Authority engagement polling.

For each entry in config/authorities.yaml, poll their public activity on
supported platforms and record engagements in corpus/_index.sqlite.

v1 supports:
- GitHub stars (canonical "I endorse this" signal)

v2 will add:
- GitHub events feed (PRs, commits, issues; 90-day retention)
- Reddit user submissions (PRAW, requires REDDIT_* in .env)
- HN Algolia searches (no auth needed)
- arXiv co-authorship via OpenAlex

Twitter/X is deferred indefinitely per PLAN.md.

Run as a separate systemd-timer unit; uses corpus/.poll.lock so it can run
alongside ingestion (different DB tables, different rate-limit budget).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import yaml

from ingest._index import connect, init_schema
from ingest.canonicalize import canonicalize, source_id

log = logging.getLogger("ingest.poll_authorities")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GITHUB_API = "https://api.github.com"


def slugify(name: str) -> str:
    """Authority id slug: lowercase, alphanumeric+underscore."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def load_dotenv_into_environ(path: Path) -> None:
    """Minimal .env loader. No dep on python-dotenv."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def acquire_lock(path: Path) -> Any:
    """Exclusive flock; returns fd or None if already held."""
    import fcntl
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = path.open("w")
    try:
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log.info("poll already running; exiting")
        fd.close()
        return None
    return fd


def github_client(token: str) -> httpx.Client:
    return httpx.Client(
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.star+json",  # gives us starred_at
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "deep-ai-research/0.1 (deep-ai-research; personal use)",
        },
        timeout=30.0,
        follow_redirects=True,
    )


def poll_github_stars(
    authority_id: str,
    github_handle: str,
    conn: Any,
    gh: httpx.Client,
    *,
    max_pages: int = 20,
    per_page: int = 100,
) -> tuple[int, int]:
    """Poll authority's starred repos. Returns (total_seen, new_engagements).

    Idempotent via UNIQUE(authority_id, source_id, kind). Pagination via
    GitHub Link header. Stops on empty page or after `max_pages`.
    """
    seen = 0
    new = 0
    page = 1
    while page <= max_pages:
        url = f"{GITHUB_API}/users/{github_handle}/starred"
        try:
            resp = gh.get(url, params={"page": page, "per_page": per_page})
        except httpx.HTTPError as e:
            log.error("github request failed for %s page %d: %s", github_handle, page, e)
            break

        if resp.status_code == 404:
            log.warning("github user %s not found", github_handle)
            break
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            reset = resp.headers.get("X-RateLimit-Reset", "0")
            log.warning("rate limited; reset at %s", reset)
            break
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            log.error("github error for %s page %d: %s", github_handle, page, e)
            break

        items = resp.json()
        if not items:
            break

        for item in items:
            seen += 1
            # With star+json Accept header, items are {starred_at, repo}
            # Without it (fallback), items ARE the repo dicts.
            repo = item.get("repo") if isinstance(item, dict) and "repo" in item else item
            if not isinstance(repo, dict):
                continue
            html_url = repo.get("html_url")
            if not html_url:
                continue
            canon = canonicalize(html_url)
            sid = source_id(canon)
            starred_at = item.get("starred_at") if isinstance(item, dict) else None
            metadata = json.dumps({
                "url": canon,
                "starred_at": starred_at,
                "repo_full_name": repo.get("full_name"),
                "stargazers_count": repo.get("stargazers_count"),
                "language": repo.get("language"),
            })
            try:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO engagements(authority_id, source_id, kind, metadata) "
                    "VALUES (?, ?, ?, ?)",
                    (authority_id, sid, "star", metadata),
                )
                if cur.rowcount > 0:
                    new += 1
            except Exception as e:  # noqa: BLE001
                log.warning("engagement insert failed for %s star %s: %s", authority_id, html_url, e)

        # Pagination via Link header
        link = resp.headers.get("Link", "")
        if 'rel="next"' not in link:
            break
        page += 1

    return seen, new


def upsert_health(conn: Any, name: str, *, ok: bool, error: str | None = None) -> None:
    if ok:
        conn.execute(
            "INSERT INTO adapter_health(adapter_name, last_success_at, consecutive_failures) "
            "VALUES (?, CURRENT_TIMESTAMP, 0) "
            "ON CONFLICT(adapter_name) DO UPDATE SET "
            "  last_success_at = CURRENT_TIMESTAMP, consecutive_failures = 0",
            (name,),
        )
    else:
        conn.execute(
            "INSERT INTO adapter_health(adapter_name, last_error_at, last_error_message, consecutive_failures) "
            "VALUES (?, CURRENT_TIMESTAMP, ?, 1) "
            "ON CONFLICT(adapter_name) DO UPDATE SET "
            "  last_error_at = CURRENT_TIMESTAMP, last_error_message = excluded.last_error_message, "
            "  consecutive_failures = adapter_health.consecutive_failures + 1",
            (name, error),
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authority", help="poll only one authority (slug match)")
    parser.add_argument("--max-pages", type=int, default=20,
                        help="max pages of stars per authority (100/page)")
    parser.add_argument("--no-lock", action="store_true")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose >= 2 else logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    load_dotenv_into_environ(PROJECT_ROOT / ".env")
    gh_token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not gh_token:
        log.error("GITHUB_TOKEN not set in .env")
        return 1

    paths = yaml.safe_load((PROJECT_ROOT / "config" / "paths.yaml").read_text())
    sqlite_path = (PROJECT_ROOT / paths["sqlite_path"]).resolve()
    lock_path = (PROJECT_ROOT / paths["authority_poll_lock"]).resolve()

    lock_fd = None if args.no_lock else acquire_lock(lock_path)
    if not args.no_lock and lock_fd is None:
        return 0  # not an error — another run in progress

    try:
        authorities_doc = yaml.safe_load((PROJECT_ROOT / "config" / "authorities.yaml").read_text())
        authorities = authorities_doc.get("authorities", [])

        conn = connect(sqlite_path)
        init_schema(conn)
        gh = github_client(gh_token)

        total_seen = 0
        total_new = 0
        polled = 0
        skipped = 0

        for entry in authorities:
            name = entry.get("name", "")
            handles = entry.get("handles", {}) or {}
            authority_id = slugify(name)

            if args.authority and authority_id != args.authority:
                continue

            github_handle = handles.get("github")
            if not github_handle:
                log.debug("%s has no github handle, skipping", authority_id)
                skipped += 1
                continue

            # Polite pacing — github limit is 5K/hr but we don't want to burn it.
            time.sleep(0.3)

            log.info("polling github stars for %s (@%s)", authority_id, github_handle)
            try:
                seen, new = poll_github_stars(
                    authority_id, github_handle, conn, gh, max_pages=args.max_pages
                )
                total_seen += seen
                total_new += new
                polled += 1
                log.info("  %d seen, %d new", seen, new)
                upsert_health(conn, f"poll_github:{authority_id}", ok=True)
            except Exception as e:  # noqa: BLE001
                log.error("polling failed for %s: %s", authority_id, e)
                upsert_health(conn, f"poll_github:{authority_id}", ok=False, error=str(e)[:200])

            conn.commit()

        log.info("done: polled=%d skipped=%d total_seen=%d total_new=%d",
                 polled, skipped, total_seen, total_new)
        gh.close()
        conn.close()
        return 0
    finally:
        if lock_fd is not None:
            lock_fd.close()


if __name__ == "__main__":
    sys.exit(main())

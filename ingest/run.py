"""Ingestion runner. Called by systemd-timer every 15 min.

Acquires flock on the lock file (single-writer guarantee), iterates over
configured adapters, runs each, writes markdown files to corpus/.
"""

from __future__ import annotations

import argparse
import importlib
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ingest.adapters._base import Adapter, RawSource
from ingest.canonicalize import canonicalize, content_hash, source_id
from ingest.frontmatter import Frontmatter, write_post

log = logging.getLogger("ingest.run")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_paths() -> dict:
    with open(PROJECT_ROOT / "config" / "paths.yaml") as f:
        return yaml.safe_load(f)


def load_sources() -> dict:
    with open(PROJECT_ROOT / "config" / "sources.yaml") as f:
        return yaml.safe_load(f)


def acquire_lock(path: Path) -> int | None:
    """Acquire exclusive flock on `path`. Returns fd if acquired, else None.

    Caller must keep fd open for the lock's lifetime.
    """
    import fcntl
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = path.open("w")
    try:
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log.info("ingest already running (lock held); exiting")
        fd.close()
        return None
    return fd  # type: ignore[return-value]


def load_adapter(name: str, *, spec: dict | None = None) -> Adapter:
    """Resolve an adapter by name. First try ingest.adapters.<name>.build();
    fall back to instantiating a generic RSSAdapter from the sources.yaml spec.
    """
    try:
        module = importlib.import_module(f"ingest.adapters.{name}")
        if hasattr(module, "build"):
            return module.build()
    except ImportError:
        pass

    if not spec:
        raise RuntimeError(f"no adapter module ingest.adapters.{name} and no fallback spec given")

    source_type = spec.get("source_type", "blog_post")

    # Reddit fallback: source_type == reddit_post, needs subreddit name.
    if source_type == "reddit_post":
        from ingest.adapters._reddit import RedditAdapter
        subreddit = spec.get("subreddit")
        if not subreddit:
            raise RuntimeError(f"adapter {name} has source_type=reddit_post but no subreddit field")
        return RedditAdapter(
            name=name,
            publication=spec.get("publication", f"r/{subreddit}"),
            subreddit=subreddit,
            source_type=source_type,
            poll_interval_seconds=spec.get("poll_interval_seconds", 14400),
            rate_limit_key=spec.get("rate_limit_key", "reddit"),
            posts_limit=spec.get("posts_limit", 100),
            top_comments=spec.get("top_comments", 3),
        )

    # Generic RSS-style adapter from yaml fields.
    from ingest.adapters._rss import RSSAdapter
    feed_url = spec.get("feed_url")
    if not feed_url:
        raise RuntimeError(f"adapter {name} has no feed_url; can't build generic RSS adapter")
    return RSSAdapter(
        name=name,
        publication=spec.get("publication", name),
        feed_url=feed_url,
        source_type=source_type,
        poll_interval_seconds=spec.get("poll_interval_seconds", 21600),
        rate_limit_key=spec.get("rate_limit_key", "default"),
    )


def write_one(raw: RawSource, *, corpus_dir: Path, dry_run: bool) -> Path | None:
    """Write a single RawSource to corpus/. Returns the file path, or None on skip."""
    canon = canonicalize(raw.url)
    sid = source_id(canon)
    body = raw.body
    chash = content_hash(body)

    # File path: corpus/<source_type>/<adapter-style-slug>.md
    # Slug: date + first-30-of-title for readability.
    slug = f"{raw.date.isoformat()}-{_slugify(raw.title)[:60]}-{sid[:8]}"
    type_dir = corpus_dir / _type_subdir(raw.source_type)
    out = type_dir / f"{slug}.md"

    if out.exists():
        # Compare content hash; if same, no-op (idempotent).
        try:
            from ingest.frontmatter import read_post
            existing_fm, _ = read_post(out)
            if existing_fm.content_hash == chash:
                log.debug("unchanged: %s", out.name)
                return out
        except Exception:  # noqa: BLE001
            pass  # fall through to overwrite

    fm_obj = Frontmatter(
        source_id=sid,
        source_type=raw.source_type,
        publication=raw.publication,
        url=raw.url,
        canonical_url=canon,
        date=raw.date,
        authors=raw.authors,
        mentioned_entities=raw.mentioned_entities,
        mentioned_authorities=raw.mentioned_authorities,
        tags=raw.tags,
        ingested_at=datetime.now(timezone.utc),
        content_hash=chash,
        revision=1,
    )

    if dry_run:
        log.info("[dry-run] would write %s", out)
        return out

    write_post(out, fm_obj, body)
    log.info("wrote %s", out)
    return out


def _slugify(s: str) -> str:
    """Cheap slug: lowercase, alphanumeric and dashes."""
    import re
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _type_subdir(source_type: str) -> str:
    return {
        "newsletter": "newsletters",
        "lab_blog": "lab-blogs",
        "reddit_post": "reddit",
        "hn_post": "hn",
        "podcast_episode": "podcasts",
        "hf_daily_papers": "hf-daily-papers",
        "arxiv_paper": "promoted-arxiv",
        "benchmark_snapshot": "benchmarks",
    }.get(source_type, source_type)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--adapter", help="run only this adapter (default: all enabled)")
    p.add_argument("--dry-run", action="store_true", help="don't write files")
    p.add_argument("--since", help="ISO datetime; only fetch entries newer", default=None)
    p.add_argument("--no-lock", action="store_true", help="skip flock (debug only)")
    p.add_argument("-v", "--verbose", action="count", default=0)
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose >= 2 else logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    paths = load_paths()
    corpus_dir = (PROJECT_ROOT / paths["corpus_dir"]).resolve()
    lock_path = (PROJECT_ROOT / paths["ingest_lock"]).resolve()

    lock_fd = None
    if not args.no_lock:
        lock_fd = acquire_lock(lock_path)
        if lock_fd is None:
            return 0  # not an error — another run is in progress

    try:
        sources = load_sources()
        since_dt = datetime.fromisoformat(args.since) if args.since else None

        # Collect adapters from all categories (newsletters, lab_blogs, ...).
        adapter_specs: list[dict] = []
        for category in ("newsletters", "lab_blogs", "reddit", "hn", "hf_daily_papers", "podcasts"):
            adapter_specs.extend(sources.get(category) or [])

        if args.adapter:
            adapter_specs = [s for s in adapter_specs if s.get("name") == args.adapter]
            if not adapter_specs:
                log.error("no adapter named %s", args.adapter)
                return 2

        total_written = 0
        for spec in adapter_specs:
            if not spec.get("enabled", True):
                continue
            name = spec["name"]
            try:
                adapter = load_adapter(name, spec=spec)
            except Exception as e:  # noqa: BLE001
                log.error("failed to load adapter %s: %s", name, e)
                continue

            log.info("running adapter %s", name)
            for raw in adapter.iter_new(since=since_dt):
                try:
                    write_one(raw, corpus_dir=corpus_dir, dry_run=args.dry_run)
                    total_written += 1
                except Exception as e:  # noqa: BLE001
                    log.error("write failed for %s: %s", raw.url, e)

        log.info("ingestion complete: %d items processed", total_written)
        return 0
    finally:
        if lock_fd is not None:
            lock_fd.close()


if __name__ == "__main__":
    sys.exit(main())

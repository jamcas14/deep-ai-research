"""Ingestion runner. Called by systemd-timer every 15 min.

Acquires flock on the lock file (single-writer guarantee), iterates over
configured adapters, runs each, writes markdown files to corpus/.
"""

from __future__ import annotations

import argparse
import importlib
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ingest.adapters._base import Adapter, RawSource
from ingest.canonicalize import canonicalize, content_hash, source_id
from ingest.frontmatter import Frontmatter, write_post
from ingest.mention_detect import MentionDetector

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


def load_dotenv_into_environ(path: Path) -> None:
    """Minimal .env loader so adapter creds (HF_TOKEN, REDDIT_*) are picked up."""
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


def build_canonical_url_index(corpus_dir: Path) -> dict[str, Path]:
    """Patch SS — build canonical_url → existing-path map for ingestion-time dedup.

    The same arXiv paper / blog post often comes in via 5+ adapters (HF Daily
    Papers, AINews, Import AI, the lab blog itself, HN). Without dedup, each
    adapter writes a separate chunk under a different slug — the corpus ends up
    with 5 competing copies, confusing both retrieval ranking and the digest.

    Walks corpus/ once at run-start. ~50ms on 8K chunks.
    """
    out: dict[str, Path] = {}
    for path in corpus_dir.rglob("*.md"):
        if not path.is_file() or "digests" in path.parts:
            continue
        try:
            from ingest.frontmatter import read_post
            fm, _ = read_post(path)
        except Exception:  # noqa: BLE001
            continue
        if fm.canonical_url and fm.canonical_url not in out:
            out[fm.canonical_url] = path
    return out


def write_one(
    raw: RawSource,
    *,
    corpus_dir: Path,
    dry_run: bool,
    detector: MentionDetector | None = None,
    canonical_index: dict[str, Path] | None = None,
) -> Path | None:
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

    # Patch SS: skip if canonical_url already in corpus under a different path.
    # The same arXiv paper from N adapters would otherwise produce N chunks.
    if canonical_index is not None and canon in canonical_index:
        existing = canonical_index[canon]
        if existing != out:
            log.debug("dedup skip: %s already at %s", canon, existing.name)
            return existing

    if out.exists():
        # Compare content hash; if same, no-op (idempotent).
        try:
            from ingest.frontmatter import read_post
            existing_fm, _ = read_post(out)
            if existing_fm.content_hash == chash:
                log.debug("unchanged: %s", out.name)
                return out
        except Exception:
            pass  # fall through to overwrite

    # Patch NN: populate mentioned_authorities + mentioned_entities at write time.
    # Adapter-supplied values win when non-empty; otherwise the detector fills them.
    mentioned_authorities = list(raw.mentioned_authorities)
    mentioned_entities = list(raw.mentioned_entities)
    if detector is not None and not mentioned_authorities and not mentioned_entities:
        try:
            mentioned_authorities, mentioned_entities = detector.detect(
                body, source_type=raw.source_type, title=raw.title
            )
        except Exception as e:
            log.warning("mention detection failed for %s: %s", raw.url, e)

    fm_obj = Frontmatter(
        source_id=sid,
        source_type=raw.source_type,
        publication=raw.publication,
        url=raw.url,
        canonical_url=canon,
        date=raw.date,
        authors=raw.authors,
        mentioned_entities=mentioned_entities,
        mentioned_authorities=mentioned_authorities,
        tags=raw.tags,
        ingested_at=datetime.now(timezone.utc),
        content_hash=chash,
        revision=1,
    )

    if dry_run:
        log.info("[dry-run] would write %s", out)
        return out

    write_post(out, fm_obj, body)
    if canonical_index is not None:
        canonical_index[canon] = out
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
        "github_release": "github-releases",  # Patch RR
        "bluesky_post": "bluesky",            # Patch WW
    }.get(source_type, source_type)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--adapter", help="run only this adapter (default: all enabled)")
    p.add_argument("--dry-run", action="store_true", help="don't write files")
    p.add_argument("--since", help="ISO datetime; only fetch entries newer", default=None)
    p.add_argument("--no-lock", action="store_true", help="skip flock (debug only)")
    p.add_argument(
        "--use-llm",
        action="store_true",
        help="enable Haiku-based mention disambiguation via `claude -p` "
             "(opt-in; consumes Max-plan rate limits — ~4.5K tokens/call)",
    )
    p.add_argument("-v", "--verbose", action="count", default=0)
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose >= 2 else logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    load_dotenv_into_environ(PROJECT_ROOT / ".env")

    paths = load_paths()
    corpus_dir = (PROJECT_ROOT / paths["corpus_dir"]).resolve()
    lock_path = (PROJECT_ROOT / paths["ingest_lock"]).resolve()

    lock_fd = None
    if not args.no_lock:
        lock_fd = acquire_lock(lock_path)
        if lock_fd is None:
            return 0  # not an error — another run is in progress

    detector = MentionDetector(use_llm=args.use_llm)
    log.info(
        "mention-detector: %d authorities loaded, llm_disambiguation=%s",
        len(detector.authorities),
        detector.use_llm,
    )

    canonical_index = build_canonical_url_index(corpus_dir)
    log.info("canonical-url index built: %d existing URLs", len(canonical_index))

    try:
        sources = load_sources()
        since_dt = datetime.fromisoformat(args.since) if args.since else None

        # Collect adapters from fast categories. `podcasts` is intentionally
        # excluded — Patch QQ moves it to a separate `python -m ingest.podcasts`
        # entry point on its own systemd timer because transcription is slow
        # (~5-10 min per hour of audio) and would block other adapters.
        adapter_specs: list[dict] = []
        for category in (
            "newsletters",
            "lab_blogs",
            "reddit",
            "hn",
            "hf_daily_papers",
            "github_releases",  # Patch RR (2026-05-04)
            "bluesky",          # Patch WW (2026-05-04)
        ):
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
            except Exception as e:
                log.error("failed to load adapter %s: %s", name, e)
                continue

            log.info("running adapter %s", name)
            for raw in adapter.iter_new(since=since_dt):
                try:
                    write_one(
                        raw,
                        corpus_dir=corpus_dir,
                        dry_run=args.dry_run,
                        detector=detector,
                        canonical_index=canonical_index,
                    )
                    total_written += 1
                except Exception as e:
                    log.error("write failed for %s: %s", raw.url, e)

        log.info("ingestion complete: %d items processed", total_written)
        return 0
    finally:
        detector.close()
        if lock_fd is not None:
            lock_fd.close()


if __name__ == "__main__":
    sys.exit(main())

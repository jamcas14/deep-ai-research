"""Patch QQ — podcast-specific ingestion entry point.

Runs out-of-band from the every-15-min `ingest/run.py` because transcription
takes 5-10 min per hour of audio and would block all other adapters. Driven
by its own systemd timer (`deep-ai-research-podcasts.timer`, daily).

Reads the `podcasts:` section of `config/sources.yaml`, instantiates one
PodcastAdapter per feed, fetches new episodes, transcribes via faster-whisper,
and writes RawSources through the same `ingest/run.py` write_one pipeline so
mention detection + frontmatter consistency apply identically.

Usage:
    uv run python -m ingest.podcasts                       # all feeds
    uv run python -m ingest.podcasts --podcast latent_space  # one feed
    uv run python -m ingest.podcasts --since 2026-04-01    # date-bounded
    uv run python -m ingest.podcasts --episode-cap 20      # raise per-run cap
    uv run python -m ingest.podcasts --dry-run             # don't write
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime

from ingest.adapters.podcast import PodcastAdapter, build_from_spec
from ingest.mention_detect import MentionDetector
from ingest.run import (
    PROJECT_ROOT,
    acquire_lock,
    build_canonical_url_index,
    load_dotenv_into_environ,
    load_paths,
    load_sources,
    write_one,
)

log = logging.getLogger("ingest.podcasts")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--podcast", help="run only this podcast (name from sources.yaml)")
    p.add_argument("--since", help="ISO datetime; only fetch episodes newer", default=None)
    p.add_argument("--episode-cap", type=int, help="override per-feed episode cap")
    p.add_argument("--no-lock", action="store_true", help="skip flock (debug only)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--use-llm",
        action="store_true",
        help="enable Haiku-based mention disambiguation via `claude -p` "
             "(off by default — uses Max plan rate limits)",
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
    # Separate lock from the main ingest timer so they can run concurrently.
    lock_path = (PROJECT_ROOT / paths.get("ingest_lock", "var/ingest.lock")).resolve()
    lock_path = lock_path.parent / (lock_path.stem + "-podcasts" + lock_path.suffix)

    lock_fd = None
    if not args.no_lock:
        lock_fd = acquire_lock(lock_path)
        if lock_fd is None:
            return 0  # another podcasts run in progress

    detector = MentionDetector(use_llm=args.use_llm)
    log.info(
        "podcasts ingestion: %d authorities loaded, llm_disambiguation=%s",
        len(detector.authorities),
        detector.use_llm,
    )

    canonical_index = build_canonical_url_index(corpus_dir)
    log.info("canonical-url index: %d existing URLs", len(canonical_index))

    try:
        sources = load_sources()
        podcast_specs = sources.get("podcasts") or []
        if args.podcast:
            podcast_specs = [s for s in podcast_specs if s.get("name") == args.podcast]
            if not podcast_specs:
                log.error("no podcast named %s", args.podcast)
                return 2

        if not podcast_specs:
            log.info("no podcasts configured in sources.yaml — nothing to do")
            return 0

        since_dt = datetime.fromisoformat(args.since) if args.since else None
        shared_state: dict = {}  # caches the faster-whisper model across adapters

        total_written = 0
        for spec in podcast_specs:
            if not spec.get("enabled", True):
                continue
            if args.episode_cap is not None:
                spec = {**spec, "episode_cap_per_run": args.episode_cap}
            adapter: PodcastAdapter = build_from_spec(spec, shared_state)

            log.info("podcast: %s", adapter.name)
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

        log.info("podcasts ingestion complete: %d items processed", total_written)
        return 0
    finally:
        detector.close()
        if lock_fd is not None:
            lock_fd.close()


if __name__ == "__main__":
    sys.exit(main())

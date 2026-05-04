"""Patch NN backfill — populate mentioned_authorities and mentioned_entities on
existing corpus markdown files.

mention_detect runs at write time, so it only tags NEW or CHANGED chunks. This
backfill walks the existing corpus and re-tags everything in place. Idempotent
via content_hash (running twice on the same file is a no-op when content
unchanged), but safe to re-run after authorities.yaml changes.

Cost note: regex-only (default) is zero subscription cost — only full-name
matches are tagged, handle-only matches are skipped. Add `--use-llm` to invoke
Haiku 4.5 via `claude -p` headless mode for handle disambiguation and entity
extraction; this consumes the user's Max-plan rate limits (~4.5K tokens/call).
NOT a metered API key path — uses the logged-in `claude` CLI session.

After backfill, run `python -m ingest.tag_engagements` to insert the
'mentioned_with_link' engagement records that drive the retrieval-time boost.

Usage:
    uv run python -m ingest.backfill_mentions                  # regex-only, all corpus
    uv run python -m ingest.backfill_mentions --use-llm        # Haiku via `claude -p`
    uv run python -m ingest.backfill_mentions --since 2026-01  # date-filtered
    uv run python -m ingest.backfill_mentions --limit 100      # cap for testing
    uv run python -m ingest.backfill_mentions --dry-run        # don't write
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date as date_cls
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ingest.frontmatter import Frontmatter, read_post, write_post
from ingest.mention_detect import MentionDetector
from ingest.run import load_dotenv_into_environ, load_paths

log = logging.getLogger("ingest.backfill_mentions")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _parse_since(s: str | None) -> date_cls | None:
    if not s:
        return None
    # Accept YYYY, YYYY-MM, or YYYY-MM-DD
    parts = s.split("-")
    try:
        if len(parts) == 1:
            return date_cls(int(parts[0]), 1, 1)
        if len(parts) == 2:
            return date_cls(int(parts[0]), int(parts[1]), 1)
        return date_cls(int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        raise SystemExit(f"--since must be YYYY[-MM[-DD]]: got {s!r}") from None


def _read_body_only(path: Path) -> tuple[Frontmatter, str]:
    """Read frontmatter + raw body. Reuses ingest.frontmatter.read_post so
    schema validation matches the rest of the pipeline."""
    return read_post(path)


def backfill(
    corpus_dir: Path,
    *,
    since: date_cls | None,
    limit: int | None,
    skip_existing: bool,
    dry_run: bool,
    detector: MentionDetector,
) -> dict[str, int]:
    """Walk corpus_dir and update mentions. Returns counters."""
    counters = {
        "scanned": 0,
        "skipped_unreadable": 0,
        "skipped_existing": 0,
        "skipped_pre_since": 0,
        "no_hits": 0,
        "updated": 0,
        "wrote": 0,
    }

    for path in corpus_dir.rglob("*.md"):
        if not path.is_file():
            continue
        # Skip the digests subdir — those are derived, not source content.
        if "digests" in path.parts:
            continue
        if limit is not None and counters["scanned"] >= limit:
            break

        counters["scanned"] += 1
        try:
            fm_obj, body = _read_body_only(path)
        except Exception as e:
            log.debug("unreadable %s: %s", path, e)
            counters["skipped_unreadable"] += 1
            continue

        if since is not None and fm_obj.date < since:
            counters["skipped_pre_since"] += 1
            continue

        if skip_existing and (fm_obj.mentioned_authorities or fm_obj.mentioned_entities):
            counters["skipped_existing"] += 1
            continue

        try:
            auths, ents = detector.detect(
                body, source_type=fm_obj.source_type, title=fm_obj.publication
            )
        except Exception as e:
            log.warning("detect failed on %s: %s", path, e)
            continue

        if not auths and not ents:
            counters["no_hits"] += 1
            continue

        # Don't overwrite when both lists already match — protects against
        # spurious revision bumps when a re-run produces identical output.
        if (
            auths == list(fm_obj.mentioned_authorities or [])
            and ents == list(fm_obj.mentioned_entities or [])
        ):
            counters["no_hits"] += 1
            continue

        counters["updated"] += 1

        if dry_run:
            log.info(
                "[dry-run] would update %s: auths=%s entities=%d",
                path.name, auths, len(ents),
            )
            continue

        # Write back via the same Frontmatter pipeline. Bump revision so
        # downstream consumers (chunk indexer, embed) know to re-process.
        new_fm = fm_obj.model_copy(
            update={
                "mentioned_authorities": auths,
                "mentioned_entities": ents,
                "revision": (fm_obj.revision or 1) + 1,
                "ingested_at": datetime.now(timezone.utc),
            }
        )
        write_post(path, new_fm, body)
        counters["wrote"] += 1
        log.info("updated %s: auths=%s entities=%d", path.name, auths, len(ents))

    return counters


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--since",
        help="Only backfill files with frontmatter date >= YYYY[-MM[-DD]] (default: all)",
    )
    p.add_argument(
        "--limit",
        type=int,
        help="Cap files processed (useful for cost-bounded test runs)",
    )
    p.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Re-run on chunks that already have any mentions populated "
             "(default: skip them to save cost)",
    )
    p.add_argument(
        "--use-llm",
        action="store_true",
        help="Enable Haiku disambiguation via `claude -p` headless mode. "
             "Off by default to keep zero subscription rate-limit cost. "
             "Each call consumes ~4.5K tokens of the user's Max plan budget.",
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("-v", "--verbose", action="count", default=0)
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose >= 2 else logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    load_dotenv_into_environ(PROJECT_ROOT / ".env")

    paths = load_paths()
    corpus_dir = (PROJECT_ROOT / paths["corpus_dir"]).resolve()
    since_d = _parse_since(args.since)

    detector = MentionDetector(use_llm=args.use_llm)
    log.info(
        "backfill starting: %d authorities loaded, llm_disambiguation=%s, since=%s, limit=%s",
        len(detector.authorities),
        detector.use_llm,
        since_d,
        args.limit,
    )

    try:
        counters = backfill(
            corpus_dir,
            since=since_d,
            limit=args.limit,
            skip_existing=not args.no_skip_existing,
            dry_run=args.dry_run,
            detector=detector,
        )
    finally:
        detector.close()

    log.info("backfill done: %s", counters)
    print(yaml.safe_dump(counters, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

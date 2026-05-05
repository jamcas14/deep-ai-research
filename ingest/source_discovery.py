"""Patch FFF — Source-discovery automation.

Walks the corpus and surfaces ENTITIES (names, models, labs, frameworks)
that appear frequently in `mentioned_entities` / `mentioned_authorities`
but have NO corresponding source adapter or authority in
`config/sources.yaml` or `config/authorities.yaml`.

Output: `digests/source_candidates_YYYY-MM-DD.md` (gitignored) — a markdown
report with top-N candidates ranked by mention count, plus an optional
"action" column suggesting how to add each (RSS adapter? authority entry?
GitHub releases.atom? new sources.yaml line?).

Cadence: monthly via a separate systemd timer, or run on demand. Cheap —
no LLM call required; pure SQL-style aggregation over corpus frontmatter.

Usage:
    python -m ingest.source_discovery                     # last 30 days
    python -m ingest.source_discovery --since-days 90     # full quarter
    python -m ingest.source_discovery --top-n 50          # show more
    python -m ingest.source_discovery --include-known     # include already-tracked
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from ingest.frontmatter import read_post
from ingest.run import PROJECT_ROOT, load_paths, load_sources

log = logging.getLogger("ingest.source_discovery")

DEFAULT_TOP_N = 30
DEFAULT_SINCE_DAYS = 30


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def load_known_authorities() -> set[str]:
    """Set of authority full names (matches frontmatter mentioned_authorities)."""
    path = PROJECT_ROOT / "config" / "authorities.yaml"
    if not path.exists():
        return set()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {a.get("name", "") for a in raw.get("authorities", []) if a.get("name")}


def load_known_source_publications() -> set[str]:
    """Set of publication strings already tracked in sources.yaml.

    Lower-cased + slugified for fuzzy match against entities like 'Anthropic'
    that the source adapter calls 'Anthropic News'.
    """
    sources = load_sources()
    out: set[str] = set()
    for category in (
        "newsletters", "lab_blogs", "reddit", "hn", "hf_daily_papers",
        "podcasts", "github_releases", "bluesky",
    ):
        for spec in sources.get(category) or []:
            pub = spec.get("publication") or ""
            if pub:
                out.add(pub.lower())
                out.add(_slugify(pub))
    return out


def gather_mentions(corpus_dir: Path, *, since: date) -> tuple[Counter[str], Counter[str]]:
    """Walk corpus chunks since `since` and tally mentioned_entities and
    mentioned_authorities counts. Returns (entity_counts, authority_counts).
    """
    entity_counts: Counter[str] = Counter()
    authority_counts: Counter[str] = Counter()
    scanned = 0
    for path in corpus_dir.rglob("*.md"):
        if "digests" in path.parts:
            continue
        try:
            fm, _ = read_post(path)
        except Exception:  # noqa: BLE001
            continue
        if fm.date < since:
            continue
        scanned += 1
        for e in fm.mentioned_entities or []:
            if isinstance(e, str) and e.strip():
                entity_counts[e.strip()] += 1
        for a in fm.mentioned_authorities or []:
            if isinstance(a, str) and a.strip():
                authority_counts[a.strip()] += 1
    log.info("scanned %d chunks since %s", scanned, since.isoformat())
    return entity_counts, authority_counts


def render_report(
    *,
    since: date,
    today: date,
    entity_counts: Counter[str],
    authority_counts: Counter[str],
    known_authorities: set[str],
    known_publications: set[str],
    top_n: int,
    include_known: bool,
) -> str:
    """Render the markdown report."""
    lines: list[str] = []
    lines.append(f"# Source-discovery candidates — {today.isoformat()}")
    lines.append("")
    lines.append(
        f"_Window: {since.isoformat()} → {today.isoformat()}. "
        f"Mentions tallied from corpus frontmatter `mentioned_authorities` "
        f"and `mentioned_entities`. Patch NN populates these — denser counts "
        f"after running `python -m ingest.backfill_mentions --use-llm`._"
    )
    lines.append("")
    lines.append("## Authority candidates (people)")
    lines.append("")
    lines.append("Names appearing in `mentioned_authorities` that are NOT in "
                 "`config/authorities.yaml`. Each candidate is a potential "
                 "addition — review for sustained signal before adding.")
    lines.append("")

    # Authority candidates
    auth_rows: list[tuple[str, int]] = []
    for name, n in authority_counts.most_common():
        if name in known_authorities and not include_known:
            continue
        auth_rows.append((name, n))
        if len(auth_rows) >= top_n:
            break
    if auth_rows:
        lines.append("| Mentions | Name | Action |")
        lines.append("|---:|---|---|")
        for name, n in auth_rows:
            in_yaml = "✓" if name in known_authorities else ""
            action = (
                f"already in authorities.yaml {in_yaml}" if name in known_authorities
                else "→ add to `config/authorities.yaml` if sustained engagement"
            )
            lines.append(f"| {n} | {name} | {action} |")
    else:
        lines.append("_No new authority candidates surfaced in window._")
    lines.append("")

    lines.append("## Entity candidates (models, labs, frameworks, papers)")
    lines.append("")
    lines.append("Entities appearing in `mentioned_entities` that don't match "
                 "any tracked publication. Adapter-worthy candidates: lab blogs, "
                 "framework releases, conference proceedings.")
    lines.append("")

    # Entity candidates: filter to entities not already a tracked publication.
    entity_rows: list[tuple[str, int]] = []
    for ent, n in entity_counts.most_common():
        ent_slug = _slugify(ent)
        if (ent.lower() in known_publications or ent_slug in known_publications) and not include_known:
            continue
        entity_rows.append((ent, n))
        if len(entity_rows) >= top_n:
            break
    if entity_rows:
        lines.append("| Mentions | Entity | Suggested action |")
        lines.append("|---:|---|---|")
        for ent, n in entity_rows:
            ent_slug = _slugify(ent)
            tracked = ent.lower() in known_publications or ent_slug in known_publications
            if tracked:
                action = "already tracked"
            elif "github.com/" in ent.lower() or any(k in ent.lower() for k in ("vllm", "sglang", "llama.cpp", "transformers")):
                action = "→ candidate for `github_releases:` adapter"
            elif any(k in ent.lower() for k in ("blog", "lab", "ai", "research")):
                action = "→ candidate for `lab_blogs:` adapter (check for RSS)"
            else:
                action = "→ track as keyword / add to authorities if it's a person"
            lines.append(f"| {n} | {ent} | {action} |")
    else:
        lines.append("_No new entity candidates surfaced in window._")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "_Generated by `python -m ingest.source_discovery`. To raise mention-"
        "detection coverage, run `python -m ingest.backfill_mentions --use-llm` "
        "(consumes Max-plan rate limits; opt-in)._"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Patch FFF — source-discovery automation")
    p.add_argument("--since-days", type=int, default=DEFAULT_SINCE_DAYS,
                   help=f"Window in days (default {DEFAULT_SINCE_DAYS}).")
    p.add_argument("--top-n", type=int, default=DEFAULT_TOP_N,
                   help=f"Max candidates per section (default {DEFAULT_TOP_N}).")
    p.add_argument("--include-known", action="store_true",
                   help="Include already-tracked authorities/publications in output.")
    p.add_argument("--dry-run", action="store_true", help="Don't write the report file.")
    p.add_argument("-v", "--verbose", action="count", default=0)
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose >= 2 else logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    paths = load_paths()
    corpus_dir = (PROJECT_ROOT / paths["corpus_dir"]).resolve()
    digests_dir = (PROJECT_ROOT / "digests").resolve()
    today = datetime.now(timezone.utc).date()
    since = today - timedelta(days=args.since_days)

    known_authorities = load_known_authorities()
    known_publications = load_known_source_publications()
    log.info(
        "loaded %d known authorities, %d known publications",
        len(known_authorities), len(known_publications),
    )

    entity_counts, authority_counts = gather_mentions(corpus_dir, since=since)
    log.info(
        "tallied %d unique entities, %d unique authorities",
        len(entity_counts), len(authority_counts),
    )

    report = render_report(
        since=since,
        today=today,
        entity_counts=entity_counts,
        authority_counts=authority_counts,
        known_authorities=known_authorities,
        known_publications=known_publications,
        top_n=args.top_n,
        include_known=args.include_known,
    )

    out_path = digests_dir / f"source_candidates_{today.isoformat()}.md"
    if args.dry_run:
        log.info("[dry-run] would write %s (%d chars)", out_path, len(report))
        print(report)
        return 0

    digests_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    log.info("wrote %s", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

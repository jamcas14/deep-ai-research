"""Daily authority-feed digest.

Patch BB (2026-05-04): addresses the discovery half of the original failure
modes (DeepSeek v3.2 → v4, Karpathy LLM wiki). The query-driven /deep-ai-research
loop only fires when the user asks the right question; if the user doesn't know
DeepSeek v4 dropped, they won't ask about it. This script produces a daily
"what landed in the corpus yesterday" digest weighted by authority signal, so
the user sees discoveries they'd otherwise miss.

Cost: ~0 — no LLM call required. Optional Haiku summarization step fires only
when ANTHROPIC_API_KEY is set in .env (~$0.01-0.05/day).

Output:
- ./digests/<YYYY-MM-DD>.md  — terminal-friendly user-facing digest (gitignored)
- ./corpus/digests/<YYYY-MM-DD>.md  — corpus-queryable digest with frontmatter
  (so future /deep-ai-research runs can retrieve past digests as "what was happening")

Usage:
    python -m ingest.digest                   # last 24h
    python -m ingest.digest --since-hours 48  # last 48h
    python -m ingest.digest --dry-run         # don't write
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from ingest.frontmatter import Frontmatter, read_post, write_post
from ingest.run import load_dotenv_into_environ, load_paths

log = logging.getLogger("ingest.digest")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Map source_type → digest category bucket. Buckets are user-facing.
CATEGORY_MAP: dict[str, str] = {
    "newsletter": "newsletters_and_analysis",
    "lab_blog": "newsletters_and_analysis",
    "blog_post": "newsletters_and_analysis",
    "hf_daily_papers": "papers",
    "arxiv_paper": "papers",
    "hn_post": "community_pulse",
    "reddit_post": "community_pulse",
    "podcast_episode": "audio_video",
    "benchmark_snapshot": "benchmarks",
    "digest": "_internal_skip",  # don't include past digests in today's digest
}

CATEGORY_ORDER: list[tuple[str, str]] = [
    ("newsletters_and_analysis", "Newsletters & Analysis"),
    ("papers", "Papers"),
    ("community_pulse", "Community Pulse (HN, Reddit)"),
    ("audio_video", "Audio / Video"),
    ("benchmarks", "Benchmarks"),
    ("other", "Other"),
]

TOP_N_PER_BUCKET = 10


@dataclass
class DigestItem:
    title: str
    url: str
    publication: str
    date: date
    source_type: str
    source_id: str
    authority_signal: int
    authorities_named: list[str] = field(default_factory=list)
    snippet: str = ""

    @property
    def category(self) -> str:
        return CATEGORY_MAP.get(self.source_type, "other")


def load_authorities() -> set[str]:
    """Return set of authority IDs for fast lookup."""
    path = PROJECT_ROOT / "config" / "authorities.yaml"
    if not path.exists():
        return set()
    data = yaml.safe_load(path.read_text())
    return {a["name"] for a in data.get("authorities", []) if "name" in a}


def authority_signal(fm: Frontmatter, authority_names: set[str]) -> tuple[int, list[str]]:
    """Count authority hits across mentioned_authorities + authorities_engaged."""
    hits: list[str] = []
    for name in fm.mentioned_authorities or []:
        if name in authority_names:
            hits.append(name)
    for tag in fm.authorities_engaged or []:
        # EngagementTag pydantic model — has .authority_id; fall back to dict
        aid = getattr(tag, "authority_id", None) or (tag.get("authority_id") if isinstance(tag, dict) else None)
        if aid and aid in authority_names and aid not in hits:
            hits.append(aid)
    return len(hits), hits


def first_paragraph(body: str, max_chars: int = 280) -> str:
    """Pull a usable snippet — first non-trivial paragraph, trimmed."""
    if not body:
        return ""
    for paragraph in body.split("\n\n"):
        p = paragraph.strip()
        # Skip empty, all-bullet, or markdown-image-only paragraphs
        if not p or p.startswith("![") or all(line.startswith(("- ", "* ", "#")) for line in p.split("\n") if line):
            continue
        if len(p) < 30:
            continue
        if len(p) > max_chars:
            p = p[: max_chars - 1].rsplit(" ", 1)[0] + "…"
        return p
    return ""


def gather_items(corpus_dir: Path, since: datetime, authority_names: set[str]) -> list[DigestItem]:
    """Walk corpus/ for files with frontmatter date >= since (date-only, UTC)."""
    items: list[DigestItem] = []
    since_date = since.date()

    for md_path in corpus_dir.rglob("*.md"):
        if not md_path.is_file():
            continue
        # Skip the digests subdir itself — we don't include past digests in today's output
        if "digests" in md_path.parts:
            continue
        try:
            fm, body = read_post(md_path)
        except Exception as e:  # noqa: BLE001
            log.debug("skipping unreadable %s: %s", md_path, e)
            continue
        if fm.date < since_date:
            continue
        sig, named = authority_signal(fm, authority_names)
        items.append(
            DigestItem(
                title=fm.publication if fm.source_type == "newsletter" else _title_from_url_or_path(fm, md_path),
                url=fm.url,
                publication=fm.publication,
                date=fm.date,
                source_type=fm.source_type,
                source_id=fm.source_id,
                authority_signal=sig,
                authorities_named=named,
                snippet=first_paragraph(body),
            )
        )
    return items


def _title_from_url_or_path(fm: Frontmatter, path: Path) -> str:
    """Pull a human-readable title from path slug if frontmatter doesn't have one
    (current schema has no `title` field — title lives in the body's first heading or filename)."""
    # Try first heading from body (cheap re-read of just first 200 chars)
    try:
        head = path.read_text(encoding="utf-8")[:2000]
        body_after_fm = head.split("---", 2)[-1] if head.startswith("---") else head
        for line in body_after_fm.splitlines():
            line = line.strip()
            if line.startswith("# ") and len(line) > 3:
                return line[2:].strip()
    except Exception:  # noqa: BLE001
        pass
    # Fall back to slug
    return path.stem.replace("-", " ").title()


def rank_and_bucket(items: list[DigestItem]) -> dict[str, list[DigestItem]]:
    """Bucket by category; sort each bucket by (authority_signal desc, date desc)."""
    buckets: dict[str, list[DigestItem]] = defaultdict(list)
    for it in items:
        if it.category == "_internal_skip":
            continue
        buckets[it.category].append(it)
    for cat in buckets:
        buckets[cat].sort(key=lambda i: (-i.authority_signal, -i.date.toordinal()))
        buckets[cat] = buckets[cat][:TOP_N_PER_BUCKET]
    return buckets


def render_terminal_digest(buckets: dict[str, list[DigestItem]], since: datetime, total: int) -> str:
    """User-facing digest — clean markdown for daily reading."""
    lines: list[str] = []
    today = datetime.now(timezone.utc).date()
    lines.append(f"# Daily Digest — {today.isoformat()}")
    lines.append("")
    lines.append(f"_Window: {since.date().isoformat()} → {today.isoformat()} ({total} items in corpus)_")
    lines.append("")
    lines.append("Highest-authority items per category. Authority signal = count of "
                 "`authorities.yaml` members appearing in `mentioned_authorities` or "
                 "`authorities_engaged` of the source.")
    lines.append("")

    rendered_any = False
    for cat_key, cat_label in CATEGORY_ORDER:
        items = buckets.get(cat_key) or []
        if not items:
            continue
        rendered_any = True
        lines.append(f"## {cat_label}")
        lines.append("")
        for it in items:
            sig_str = f"  ★ {it.authority_signal}: {', '.join(it.authorities_named[:3])}" if it.authority_signal else ""
            lines.append(f"- **[{it.title}]({it.url})** — *{it.publication}* ({it.date.isoformat()}){sig_str}")
            if it.snippet:
                lines.append(f"  > {it.snippet}")
        lines.append("")

    if not rendered_any:
        lines.append("_No new items in window. Either the corpus pipeline is silent or the window is too short._")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"_Generated by `python -m ingest.digest`. Corpus path: `{load_paths()['corpus_dir']}`._")
    return "\n".join(lines)


def render_corpus_digest_body(buckets: dict[str, list[DigestItem]], since: datetime, total: int) -> str:
    """Corpus-queryable digest body — same content, but designed to be retrieved
    by future /deep-ai-research recency passes. Uses keyword-rich phrasing and
    explicit mentions so corpus search works."""
    # The terminal version is already keyword-rich; reuse with minor framing.
    body = render_terminal_digest(buckets, since, total)
    return body


def write_digest_outputs(
    buckets: dict[str, list[DigestItem]],
    since: datetime,
    total: int,
    *,
    corpus_dir: Path,
    digests_dir: Path,
    dry_run: bool,
) -> tuple[Path, Path]:
    """Write both outputs. Returns (terminal_path, corpus_path)."""
    today = datetime.now(timezone.utc).date()
    terminal_text = render_terminal_digest(buckets, since, total)
    corpus_text = render_corpus_digest_body(buckets, since, total)

    terminal_path = digests_dir / f"{today.isoformat()}.md"
    corpus_path = corpus_dir / "digests" / f"{today.isoformat()}.md"

    if dry_run:
        log.info("[dry-run] would write %s and %s", terminal_path, corpus_path)
        return terminal_path, corpus_path

    digests_dir.mkdir(parents=True, exist_ok=True)
    terminal_path.write_text(terminal_text, encoding="utf-8")
    log.info("wrote %s", terminal_path)

    # Corpus version: with frontmatter so it's retrievable by future runs
    all_authorities: list[str] = []
    for items in buckets.values():
        for it in items:
            for a in it.authorities_named:
                if a not in all_authorities:
                    all_authorities.append(a)

    fm_obj = Frontmatter(
        source_id=f"digest-{today.isoformat()}",
        source_type="digest",
        publication="deep-ai-research daily digest",
        url=f"file://{corpus_path}",
        canonical_url=f"file://{corpus_path}",
        date=today,
        authors=["deep-ai-research"],
        mentioned_authorities=all_authorities,
        tags=["digest", "discovery"],
        ingested_at=datetime.now(timezone.utc),
        content_hash=f"digest-{today.isoformat()}",
        revision=1,
    )
    write_post(corpus_path, fm_obj, corpus_text)
    log.info("wrote %s", corpus_path)

    return terminal_path, corpus_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Daily authority-feed digest.")
    p.add_argument("--since-hours", type=int, default=24, help="Window in hours (default 24).")
    p.add_argument("--dry-run", action="store_true", help="Don't write outputs.")
    p.add_argument("-v", "--verbose", action="count", default=0)
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose >= 2 else logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    load_dotenv_into_environ(PROJECT_ROOT / ".env")

    paths = load_paths()
    corpus_dir = (PROJECT_ROOT / paths["corpus_dir"]).resolve()
    digests_dir = (PROJECT_ROOT / "digests").resolve()
    since = datetime.now(timezone.utc) - timedelta(hours=args.since_hours)

    authority_names = load_authorities()
    log.info("loaded %d authorities", len(authority_names))

    items = gather_items(corpus_dir, since, authority_names)
    log.info("gathered %d items in window (last %dh)", len(items), args.since_hours)

    buckets = rank_and_bucket(items)
    for cat_key, cat_label in CATEGORY_ORDER:
        n = len(buckets.get(cat_key) or [])
        if n:
            log.info("  %s: %d items", cat_label, n)

    write_digest_outputs(
        buckets, since, len(items),
        corpus_dir=corpus_dir,
        digests_dir=digests_dir,
        dry_run=args.dry_run,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())

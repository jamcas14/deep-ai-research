"""Author engagement tagger.

Walks corpus markdown and writes engagement records of kind='author' whenever
a corpus item's publication or authors list matches an authority in
config/authorities.yaml.

This is the cheapest and most accurate authority signal we have for blog and
newsletter content: if Simon Willison wrote it, that IS authority engagement
on it. Doesn't need any external API call. Idempotent via the UNIQUE
constraint on engagements(authority_id, source_id, kind).

Run after ingestion. Wired into the systemd-timer chain via deep-ai-research-poll-authorities
or a separate deep-ai-research-tag-engagements unit (see ops/).
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

import yaml

from ingest._index import connect, init_schema
from ingest.frontmatter import read_post

log = logging.getLogger("ingest.tag_engagements")
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def load_authorities() -> list[dict]:
    raw = yaml.safe_load((PROJECT_ROOT / "config" / "authorities.yaml").read_text())
    return raw.get("authorities", []) or []


def build_matchers(authorities: list[dict]) -> list[tuple[str, list[str]]]:
    """For each authority, list lowercase patterns that should match in
    publication or author strings. Returns [(authority_id, [patterns])].
    """
    matchers: list[tuple[str, list[str]]] = []
    for entry in authorities:
        name = entry.get("name") or ""
        if not name:
            continue
        slug = slugify(name)
        patterns = {name.lower()}

        # Common name variants (handle nicknames in YAML like "swyx (Shawn Wang)")
        m = re.match(r"^(.*?)\s*\((.+?)\)\s*$", name)
        if m:
            patterns.add(m.group(1).lower())
            patterns.add(m.group(2).lower())

        # Map common github handles → also acceptable as authoring marker
        # (e.g., a blog whose author field is just "rasbt").
        for plat, handle in (entry.get("handles") or {}).items():
            if isinstance(handle, str) and handle.strip():
                patterns.add(handle.lower())

        matchers.append((slug, sorted(patterns)))
    return matchers


def detect_authors(
    publication: str, authors: list[str], matchers: list[tuple[str, list[str]]]
) -> set[str]:
    """Return authority_ids that authored or own this source."""
    haystack = " ".join([publication or "", " ".join(authors or [])]).lower()
    out: set[str] = set()
    for slug, patterns in matchers:
        for p in patterns:
            if p and p in haystack:
                out.add(slug)
                break
    return out


def _name_to_slug_map(authorities: list[dict]) -> dict[str, str]:
    """Map authority full-name → slug, for resolving Frontmatter.mentioned_authorities
    (which stores full names) to engagement authority_ids (which use slugs)."""
    out: dict[str, str] = {}
    for entry in authorities:
        name = entry.get("name") or ""
        if not name:
            continue
        out[name] = slugify(name)
    return out


def tag(corpus_dir: Path, sqlite_path: Path, *, dry_run: bool = False) -> tuple[int, int]:
    """Returns (sources_examined, engagements_inserted).

    Two engagement kinds are written:
      - 'author' — when fm.publication or fm.authors matches an authority
      - 'mentioned_with_link' — when fm.mentioned_authorities lists an authority
        (populated by ingest.mention_detect at write time, Patch NN). Drives the
        4× retrieval boost on third-party content that DISCUSSES an authority's
        work without being authored by them.
    """
    authorities = load_authorities()
    matchers = build_matchers(authorities)
    name_to_slug = _name_to_slug_map(authorities)
    log.info(
        "loaded %d authority matchers, %d name->slug entries",
        len(matchers),
        len(name_to_slug),
    )

    conn = connect(sqlite_path)
    init_schema(conn)

    examined = 0
    inserted = 0
    for path in corpus_dir.rglob("*.md"):
        try:
            fm, _ = read_post(path)
        except Exception:
            continue
        examined += 1

        author_matches = detect_authors(fm.publication or "", fm.authors or [], matchers)
        for authority_id in author_matches:
            if dry_run:
                log.debug("[dry-run] would tag %s → %s (author)", fm.source_id, authority_id)
                continue
            cur = conn.execute(
                "INSERT OR IGNORE INTO engagements"
                "(authority_id, source_id, kind, metadata) "
                "VALUES (?, ?, 'author', ?)",
                (authority_id, fm.source_id, json.dumps({
                    "publication": fm.publication, "via": "publication-or-author-match",
                })),
            )
            if cur.rowcount > 0:
                inserted += 1

        # Patch NN: write 'mentioned_with_link' records from frontmatter mentions.
        # Skip authorities already tagged as authors (the 'author' record dominates
        # in the boost calculation; double-counting would inflate the score).
        for mentioned_name in (fm.mentioned_authorities or []):
            slug = name_to_slug.get(mentioned_name)
            if not slug or slug in author_matches:
                continue
            if dry_run:
                log.debug("[dry-run] would tag %s → %s (mentioned)", fm.source_id, slug)
                continue
            cur = conn.execute(
                "INSERT OR IGNORE INTO engagements"
                "(authority_id, source_id, kind, metadata) "
                "VALUES (?, ?, 'mentioned_with_link', ?)",
                (slug, fm.source_id, json.dumps({
                    "via": "mention-detect-haiku",
                    "name": mentioned_name,
                })),
            )
            if cur.rowcount > 0:
                inserted += 1

    if not dry_run:
        conn.commit()
    conn.close()
    return examined, inserted


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("-v", "--verbose", action="count", default=0)
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose >= 2 else logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    paths = yaml.safe_load((PROJECT_ROOT / "config" / "paths.yaml").read_text())
    corpus_dir = (PROJECT_ROOT / paths["corpus_dir"]).resolve()
    sqlite_path = (PROJECT_ROOT / paths["sqlite_path"]).resolve()

    examined, inserted = tag(corpus_dir, sqlite_path, dry_run=args.dry_run)
    log.info("examined=%d engagements_inserted=%d", examined, inserted)
    return 0


if __name__ == "__main__":
    sys.exit(main())

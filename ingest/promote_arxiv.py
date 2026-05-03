"""Promoted arXiv pipeline.

Detects arXiv papers worth full-text persistence based on signals already in
the corpus, then fetches and writes them as `arxiv_paper` source_type.

Signal threshold for promotion: any of
  - mentioned in 2+ distinct publications across the corpus
  - in HF Daily Papers AND mentioned in 1+ other publication
  - manually flagged via --paper-id (CLI override)

For each promoted id:
  - Check if already a corpus arxiv_paper (idempotent skip)
  - Fetch arXiv API metadata (title, abstract, authors, categories)
  - Try the HTML version (https://arxiv.org/html/<id>) for full text;
    fall back to abstract only if unavailable
  - Write to corpus/promoted-arxiv/ with source_type='arxiv_paper'

Polite throttling: 3 sec between arXiv requests per their API ToU.

Usage:
    uv run python -m ingest.promote_arxiv -v          # detect + promote
    uv run python -m ingest.promote_arxiv --dry-run   # detect only
    uv run python -m ingest.promote_arxiv --paper-id 2401.10020  # force one
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

import httpx
import yaml
from bs4 import BeautifulSoup

from ingest.canonicalize import canonicalize, content_hash, source_id
from ingest.frontmatter import Frontmatter, read_post, write_post

log = logging.getLogger("ingest.promote_arxiv")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
USER_AGENT = "dair/0.1 (deep-ai-research; personal use; mailto:noreply@example.com)"

# Match arXiv IDs that have an explicit "arxiv" context — avoids
# false-positives on version numbers / phone numbers.
ARXIV_ID_RE = re.compile(
    r"(?:arXiv\s*:?\s*|arxiv\.org/(?:abs|pdf|html)/)\s*(\d{4}\.\d{4,5})(?:v\d+)?",
    re.IGNORECASE,
)


def _load_paths() -> dict:
    return yaml.safe_load((PROJECT_ROOT / "config" / "paths.yaml").read_text())


def scan_corpus_for_arxiv_ids(corpus_dir: Path) -> dict[str, set[str]]:
    """Return arxiv_id → set of publication names that mentioned it."""
    out: dict[str, set[str]] = defaultdict(set)
    for path in corpus_dir.rglob("*.md"):
        try:
            fm, body = read_post(path)
        except Exception:  # noqa: BLE001
            continue
        ids = ARXIV_ID_RE.findall(body)
        if not ids:
            continue
        pub = fm.publication or "unknown"
        for arxiv_id in ids:
            out[arxiv_id].add(pub)
    return out


def filter_promoted(
    mentions: dict[str, set[str]],
    *,
    min_distinct_publications: int = 2,
) -> list[str]:
    """Pick arxiv_ids meeting the promotion threshold."""
    promoted: list[str] = []
    for arxiv_id, pubs in mentions.items():
        if len(pubs) >= min_distinct_publications:
            promoted.append(arxiv_id)
        elif "HuggingFace Daily Papers" in pubs and len(pubs) >= 2:
            # Already covered by min_distinct_publications=2 above; kept for
            # readability of the rule.
            promoted.append(arxiv_id)
    return sorted(set(promoted))


def fetch_arxiv_metadata(client: httpx.Client, arxiv_id: str) -> dict | None:
    """Hit arXiv Atom API. Returns dict with title/abstract/authors/categories
    or None on failure.
    """
    try:
        resp = client.get(ARXIV_API, params={"id_list": arxiv_id, "max_results": 1})
        resp.raise_for_status()
    except httpx.HTTPError as e:
        log.warning("arxiv API fetch failed for %s: %s", arxiv_id, e)
        return None

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        log.warning("arxiv API XML parse failed for %s: %s", arxiv_id, e)
        return None

    entry = root.find("atom:entry", ATOM_NS)
    if entry is None:
        log.warning("arxiv %s: no entry returned", arxiv_id)
        return None

    title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
    if not title:
        return None
    abstract = (entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").strip()
    published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
    updated = entry.findtext("atom:updated", default="", namespaces=ATOM_NS)
    authors = [
        (a.findtext("atom:name", default="", namespaces=ATOM_NS) or "").strip()
        for a in entry.findall("atom:author", ATOM_NS)
    ]
    authors = [a for a in authors if a]
    categories = [
        c.attrib.get("term", "")
        for c in entry.findall("atom:category", ATOM_NS)
        if c.attrib.get("term")
    ]
    primary = entry.find("arxiv:primary_category", ATOM_NS)
    primary_cat = primary.attrib.get("term") if primary is not None else None

    return {
        "arxiv_id": arxiv_id,
        "title": re.sub(r"\s+", " ", title),
        "abstract": abstract,
        "published": published,
        "updated": updated,
        "authors": authors,
        "categories": categories,
        "primary_category": primary_cat,
    }


def fetch_arxiv_html(client: httpx.Client, arxiv_id: str) -> str | None:
    """Try arXiv's HTML version. Returns plain-text body or None."""
    url = f"https://arxiv.org/html/{arxiv_id}"
    try:
        resp = client.get(url)
        if resp.status_code != 200:
            log.debug("arxiv html %s returned %d", arxiv_id, resp.status_code)
            return None
    except httpx.HTTPError as e:
        log.debug("arxiv html %s fetch failed: %s", arxiv_id, e)
        return None

    soup = BeautifulSoup(resp.content, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    main = soup.find("article") or soup.find("main") or soup.body
    if main is None:
        return None
    text = main.get_text(separator="\n\n", strip=True)
    if len(text) < 500:
        return None  # too short — likely an error page
    return text


def promote_one(
    client: httpx.Client,
    arxiv_id: str,
    mentions: set[str],
    *,
    corpus_dir: Path,
    dry_run: bool,
) -> Path | None:
    """Fetch + write one promoted paper. Idempotent (skips if already present)."""
    canonical_url = f"https://arxiv.org/abs/{arxiv_id}"
    canon = canonicalize(canonical_url)
    sid = source_id(canon)

    out_dir = corpus_dir / "promoted-arxiv"
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = list(out_dir.glob(f"*{sid[:8]}.md"))
    if existing:
        log.debug("skip %s — already promoted at %s", arxiv_id, existing[0].name)
        return existing[0]

    meta = fetch_arxiv_metadata(client, arxiv_id)
    if meta is None:
        return None
    time.sleep(3.0)  # arXiv ToU: 1 req per 3 sec

    full_text = fetch_arxiv_html(client, arxiv_id)
    time.sleep(3.0)

    # Body: title + metadata + abstract + (full HTML if available) + back-refs
    sections = [
        f"# {meta['title']}",
        "",
        f"**arXiv {arxiv_id}** · {meta.get('primary_category') or '?'} · "
        f"{meta.get('published', '?')[:10]}",
        "",
        f"Authors: {', '.join(meta['authors']) if meta['authors'] else '(none)'}",
        f"Categories: {', '.join(meta['categories']) if meta['categories'] else '(none)'}",
        f"arXiv abs: {canonical_url}",
        f"PDF: https://arxiv.org/pdf/{arxiv_id}",
        "",
        "## Abstract",
        "",
        meta["abstract"] or "(no abstract)",
    ]

    if full_text:
        sections.extend([
            "",
            "## Full text (arXiv HTML)",
            "",
            full_text,
        ])

    sections.extend([
        "",
        "## Mentioned by (corpus)",
        "",
        *[f"- {p}" for p in sorted(mentions)],
    ])

    body = "\n".join(sections)

    pub_str = meta.get("published") or ""
    try:
        pub_date = date.fromisoformat(pub_str[:10]) if pub_str else date.today()
    except ValueError:
        pub_date = date.today()

    fm_obj = Frontmatter(
        source_id=sid,
        source_type="arxiv_paper",
        publication="arXiv (promoted)",
        url=canonical_url,
        canonical_url=canon,
        date=pub_date,
        authors=meta["authors"][:10],
        mentioned_entities=[arxiv_id] + (meta.get("categories") or []),
        tags=["arxiv", "promoted"]
            + ([meta["primary_category"]] if meta.get("primary_category") else []),
        ingested_at=datetime.now(timezone.utc),
        content_hash=content_hash(body),
        revision=1,
    )

    title_slug = re.sub(r"[^a-z0-9]+", "-", meta["title"].lower()).strip("-")[:60]
    out_path = out_dir / f"{pub_date.isoformat()}-{title_slug}-{sid[:8]}.md"

    if dry_run:
        log.info("[dry-run] would promote %s → %s", arxiv_id, out_path.name)
        return out_path

    write_post(out_path, fm_obj, body)
    log.info("promoted %s → %s (full_text=%s, mentions=%d)",
             arxiv_id, out_path.name, bool(full_text), len(mentions))
    return out_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--paper-id", help="force-promote one specific arxiv_id (skips threshold)")
    p.add_argument("--min-publications", type=int, default=2,
                   help="min distinct publications mentioning a paper for promotion")
    p.add_argument("--max-promotions", type=int, default=50,
                   help="cap promotions per run (avoid hammering arXiv)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("-v", "--verbose", action="count", default=0)
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose >= 2 else logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    paths = _load_paths()
    corpus_dir = (PROJECT_ROOT / paths["corpus_dir"]).resolve()

    client = httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=30.0,
        follow_redirects=True,
    )

    try:
        if args.paper_id:
            mentions: dict[str, set[str]] = {args.paper_id: {"manual"}}
            promoted_ids = [args.paper_id]
        else:
            log.info("scanning corpus for arXiv references")
            mentions = scan_corpus_for_arxiv_ids(corpus_dir)
            log.info("found %d distinct arXiv IDs across corpus", len(mentions))
            promoted_ids = filter_promoted(
                mentions, min_distinct_publications=args.min_publications
            )
            log.info("%d papers meet the promotion threshold (>=%d publications)",
                     len(promoted_ids), args.min_publications)

        promoted_ids = promoted_ids[: args.max_promotions]
        log.info("processing %d papers (capped at --max-promotions=%d)",
                 len(promoted_ids), args.max_promotions)

        n_promoted = 0
        n_skipped = 0
        for arxiv_id in promoted_ids:
            try:
                result = promote_one(
                    client,
                    arxiv_id,
                    mentions[arxiv_id],
                    corpus_dir=corpus_dir,
                    dry_run=args.dry_run,
                )
                if result is None:
                    n_skipped += 1
                else:
                    n_promoted += 1
            except Exception as e:  # noqa: BLE001
                log.warning("failed to promote %s: %s", arxiv_id, e)
                n_skipped += 1

        log.info("done: promoted=%d skipped=%d", n_promoted, n_skipped)
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())

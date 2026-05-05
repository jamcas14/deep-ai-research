"""Eval harness — v1 (retrieval-layer evals).

Runs each unblocked case in evals/cases.yaml against the corpus-server's
search() function and checks behavioral assertions. Writes a per-run
summary to evals/runs/<run-id>/ and appends to evals/runs/_history.jsonl.

This is the v1 eval — it tests the retrieval moat (authority boost +
recency decay + RRF), not the full /deep-ai-research loop. Full-loop evals
land once the user has actually run the skill end-to-end and we can
shape behavioral assertions on run traces.

Usage:
    uv run python -m evals.run_all
    uv run python -m evals.run_all --case recency_deepseek_latest
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from corpus_server.server import search

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASES_FILE = PROJECT_ROOT / "evals" / "cases.yaml"
RUNS_DIR = PROJECT_ROOT / "evals" / "runs"
HISTORY_FILE = RUNS_DIR / "_history.jsonl"

log = logging.getLogger("evals.run_all")


# ---------- behavioral assertions ----------

def assert_must_mention(hits: list[dict[str, Any]], terms: list) -> tuple[bool, str]:
    """At least one hit's text/snippet/url/publication/authors must mention
    one of `terms`.

    `terms` accepts:
      - "string" (literal substring match)
      - {"any of": ["a", "b"]} (substring match against any of)
    """
    parts: list[str] = []
    for h in hits:
        parts.append(h.get("snippet") or "")
        parts.append(h.get("title_or_url") or "")
        parts.append(h.get("publication") or "")
        parts.append(" ".join(h.get("tags") or []))
        parts.append(" ".join(h.get("mentioned_authorities") or []))
    haystack = " ".join(parts).lower()
    flat: list[str] = []
    for t in terms:
        if isinstance(t, str):
            flat.append(t)
        elif isinstance(t, dict) and "any of" in t:
            flat.extend(t["any of"])
    matched = [t for t in flat if t.lower() in haystack]
    if matched:
        return True, f"matched: {matched[:3]}{'...' if len(matched) > 3 else ''}"
    return False, f"none of {flat} found in {len(hits)} hits"


def assert_must_not_mention(hits: list[dict[str, Any]], terms: list[str]) -> tuple[bool, str]:
    """No hit's snippet should contain any of `terms` (anti-regression)."""
    haystack = " ".join(h.get("snippet", "") for h in hits).lower()
    found = [t for t in terms if t.lower() in haystack]
    if found:
        return False, f"unexpectedly found: {found}"
    return True, "clean"


def assert_recency(hits: list[dict[str, Any]], within_days: int) -> tuple[bool, str]:
    """At least one hit's date must be within `within_days` of today."""
    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=within_days))
    fresh = []
    for h in hits:
        d = _parse_date(h.get("date"))
        if d and d >= cutoff:
            fresh.append(d.isoformat())
    if fresh:
        return True, f"{len(fresh)} hits within {within_days} days; freshest: {max(fresh)}"
    return False, f"no hits within {within_days} days; oldest cutoff was {cutoff.isoformat()}"


def assert_min_hits(hits: list[dict[str, Any]], n: int) -> tuple[bool, str]:
    if len(hits) >= n:
        return True, f"{len(hits)} hits ≥ {n}"
    return False, f"{len(hits)} hits < {n}"


def assert_authority_boost_present(hits: list[dict[str, Any]]) -> tuple[bool, str]:
    """At least one hit should have authority_boost > 1.0 (some authority engaged)."""
    boosted = [h for h in hits if h.get("components", {}).get("authority_boost", 1.0) > 1.0]
    if boosted:
        return True, f"{len(boosted)} of {len(hits)} hits authority-boosted"
    return False, "no hits had authority_boost > 1.0"


def assert_mentioned_authorities_populated(hits: list[dict[str, Any]], min_fraction: float = 0.05) -> tuple[bool, str]:
    """Patch NN — at least `min_fraction` of hits should have non-empty
    mentioned_authorities. Validates that mention-detection at ingestion
    is producing signal."""
    if not hits:
        return False, "no hits"
    populated = [h for h in hits if h.get("mentioned_authorities")]
    fraction = len(populated) / len(hits)
    if fraction >= min_fraction:
        return True, f"{len(populated)}/{len(hits)} ({fraction:.0%}) hits have mentioned_authorities ≥ {min_fraction:.0%}"
    return False, f"only {len(populated)}/{len(hits)} ({fraction:.0%}) hits have mentioned_authorities (< {min_fraction:.0%})"


def assert_domain_penalty_applied(hits: list[dict[str, Any]], penalized_domains: list[str]) -> tuple[bool, str]:
    """Patch VV — no hit in the top-K should be from a penalized domain
    when better alternatives exist. Soft check: penalized_domains absent
    from top-3 OR all hits with penalty < 1.0 (Patch VV doesn't filter,
    just down-ranks; if ALL candidates are penalized, one will surface)."""
    top3 = hits[:3]
    if not top3:
        return False, "no hits"
    bad = [
        h for h in top3
        if any(d in (h.get("title_or_url") or "").lower() for d in penalized_domains)
    ]
    if bad:
        # Check if those hits were actually penalized at retrieval time.
        any_unpenalized = any(
            h.get("components", {}).get("domain_penalty", 1.0) < 1.0 for h in bad
        )
        if not any_unpenalized:
            return False, f"top-3 has unpenalized hits from {penalized_domains}: {[h.get('title_or_url') for h in bad]}"
    return True, f"top-3 clean of {penalized_domains}"


def assert_engagements_kind_present(kind: str, *, min_count: int = 1) -> tuple[bool, str]:
    """Patch NN tag_engagements — engagements table has ≥`min_count` records
    of a given kind."""
    from ingest._index import connect
    paths_yaml = yaml.safe_load((PROJECT_ROOT / "config" / "paths.yaml").read_text())
    sqlite_path = (PROJECT_ROOT / paths_yaml["sqlite_path"]).resolve()
    try:
        conn = connect(sqlite_path)
        n = conn.execute("SELECT COUNT(*) FROM engagements WHERE kind = ?", (kind,)).fetchone()[0]
        conn.close()
    except Exception as e:  # noqa: BLE001
        return False, f"sqlite query failed: {e}"
    if n >= min_count:
        return True, f"engagements has {n} '{kind}' records (≥ {min_count})"
    return False, f"engagements has only {n} '{kind}' records (< {min_count})"


def assert_cross_run_memory_finds(query: str, *, min_similarity: float = 0.5) -> tuple[bool, str]:
    """Patch ZZ — cross-run memory returns at least one match for `query`
    with similarity ≥ min_similarity. Tests that the index is populated
    AND that the embedding pipeline works."""
    try:
        from corpus_server.cross_run_memory import find_similar
    except ImportError as e:
        return False, f"cross_run_memory import failed: {e}"
    matches = find_similar(query, threshold=min_similarity, top_k=3)
    if matches:
        top = matches[0]
        return True, f"top match sim={top['similarity']} run={top['run_id']}"
    return False, f"no matches ≥ {min_similarity} for {query!r}"


def assert_source_types_present(hits: list[dict[str, Any]], expected_types: list[str]) -> tuple[bool, str]:
    """Patch RR/WW — at least one hit's source_type matches expected_types.
    The hit dict doesn't expose source_type directly; we check publication
    or path heuristics."""
    found_types: set[str] = set()
    for h in hits:
        path = (h.get("path") or "").lower()
        for t in expected_types:
            if t in path or t.replace("_", "-") in path:
                found_types.add(t)
    if found_types:
        return True, f"found source_types {sorted(found_types)} in hit paths"
    return False, f"no hits with source_type in {expected_types}"


def _parse_date(s: Any) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(str(s))
    except ValueError:
        return None


# ---------- per-case runner ----------

def run_case(case: dict[str, Any], top_n: int = 20) -> dict[str, Any]:
    """Execute one case. Returns a result dict with pass/fail + per-assertion detail."""
    cid = case["id"]
    query = case["query"]
    expected = case.get("expected", {}) or {}
    case_filters = case.get("filters") or {}  # Patch BBB — pass-through search filters

    log.info("running %s: %r", cid, query[:80])
    try:
        hits = search(query, top_n=top_n, filters=case_filters or None)
    except Exception as e:  # noqa: BLE001
        return {
            "id": cid,
            "category": case.get("category"),
            "status": "error",
            "error": str(e)[:500],
            "hits_count": 0,
        }

    assertions: list[dict[str, Any]] = []

    if "must_mention" in expected:
        ok, msg = assert_must_mention(hits, expected["must_mention"])
        assertions.append({"type": "must_mention", "ok": ok, "message": msg})

    if "must_not_mention" in expected:
        ok, msg = assert_must_not_mention(hits, expected["must_not_mention"])
        assertions.append({"type": "must_not_mention", "ok": ok, "message": msg})

    # Behavioral asserts that are universal (not in case yaml yet, but we check)
    universal_min = expected.get("min_hits", 3)
    ok, msg = assert_min_hits(hits, universal_min)
    assertions.append({"type": "min_hits", "ok": ok, "message": msg})

    if case.get("category") == "recency":
        ok, msg = assert_recency(hits, within_days=60)
        assertions.append({"type": "recency", "ok": ok, "message": msg})

    if case.get("category") == "authority":
        ok, msg = assert_authority_boost_present(hits)
        assertions.append({"type": "authority_boost", "ok": ok, "message": msg})

    # Patch BBB — new behavioral assertions for Wave 1-3 patches.
    if "must_have_mentioned_authorities" in expected:
        cfg = expected["must_have_mentioned_authorities"]
        min_frac = cfg.get("min_fraction", 0.05) if isinstance(cfg, dict) else 0.05
        ok, msg = assert_mentioned_authorities_populated(hits, min_fraction=min_frac)
        assertions.append({"type": "must_have_mentioned_authorities", "ok": ok, "message": msg})

    if "must_avoid_domains" in expected:
        ok, msg = assert_domain_penalty_applied(hits, expected["must_avoid_domains"])
        assertions.append({"type": "must_avoid_domains", "ok": ok, "message": msg})

    if "must_have_engagements_kind" in expected:
        cfg = expected["must_have_engagements_kind"]
        if isinstance(cfg, str):
            kind, min_count = cfg, 1
        else:
            kind, min_count = cfg.get("kind", "author"), cfg.get("min_count", 1)
        ok, msg = assert_engagements_kind_present(kind, min_count=min_count)
        assertions.append({"type": "must_have_engagements_kind", "ok": ok, "message": msg})

    if "must_match_cross_run_memory" in expected:
        cfg = expected["must_match_cross_run_memory"]
        sim = cfg.get("min_similarity", 0.5) if isinstance(cfg, dict) else 0.5
        target_query = cfg.get("query", query) if isinstance(cfg, dict) else query
        ok, msg = assert_cross_run_memory_finds(target_query, min_similarity=sim)
        assertions.append({"type": "must_match_cross_run_memory", "ok": ok, "message": msg})

    if "must_have_source_types" in expected:
        ok, msg = assert_source_types_present(hits, expected["must_have_source_types"])
        assertions.append({"type": "must_have_source_types", "ok": ok, "message": msg})

    overall = all(a["ok"] for a in assertions)
    status = "pass" if overall else "fail"
    blocked_until = case.get("blocked_until")
    if blocked_until and not overall:
        # Allowed-to-fail cases stay marked but don't poison the summary.
        status = "blocked"

    return {
        "id": cid,
        "category": case.get("category"),
        "status": status,
        "hits_count": len(hits),
        "assertions": assertions,
        "top_hit": hits[0] if hits else None,
        "blocked_until": blocked_until,
    }


# ---------- main ----------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case", help="run only this case id")
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("-v", "--verbose", action="count", default=0)
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cases_doc = yaml.safe_load(CASES_FILE.read_text())
    cases = cases_doc.get("cases", [])
    if args.case:
        cases = [c for c in cases if c.get("id") == args.case]
        if not cases:
            log.error("no case named %s", args.case)
            return 2

    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out_dir = RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    results = [run_case(c, top_n=args.top_n) for c in cases]

    counts: dict[str, int] = {"pass": 0, "fail": 0, "blocked": 0, "error": 0}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    # Per-run JSON
    (out_dir / "results.json").write_text(json.dumps(results, indent=2, default=str))

    # Markdown summary
    summary = [f"# Eval run {run_id}", ""]
    summary.append(f"- pass: **{counts['pass']}**, fail: {counts['fail']}, blocked: {counts['blocked']}, error: {counts['error']}")
    summary.append("")
    for r in results:
        emoji = {"pass": "✅", "fail": "❌", "blocked": "⏸", "error": "💥"}.get(r["status"], "?")
        summary.append(f"## {emoji} `{r['id']}` ({r['category']}) — {r['status']}")
        if r.get("blocked_until"):
            summary.append(f"  - blocked_until: {r['blocked_until']}")
        summary.append(f"  - hits: {r['hits_count']}")
        for a in r.get("assertions", []):
            mark = "✓" if a["ok"] else "✗"
            summary.append(f"  - {mark} `{a['type']}`: {a['message']}")
        if r.get("top_hit"):
            t = r["top_hit"]
            summary.append(f"  - top: score={t.get('score')} pub={t.get('publication')} date={t.get('date')}")
        summary.append("")
    (out_dir / "summary.md").write_text("\n".join(summary))

    # Append to history
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a") as f:
        f.write(json.dumps({
            "run_id": run_id,
            "ran_at": datetime.now(timezone.utc).isoformat(),
            "counts": counts,
            "case_results": [{"id": r["id"], "status": r["status"]} for r in results],
        }) + "\n")

    print((out_dir / "summary.md").read_text())
    return 0 if counts["fail"] == 0 and counts["error"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

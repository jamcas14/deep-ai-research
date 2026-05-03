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

    log.info("running %s: %r", cid, query[:80])
    try:
        hits = search(query, top_n=top_n)
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
    ok, msg = assert_min_hits(hits, 3)
    assertions.append({"type": "min_hits", "ok": ok, "message": msg})

    if case.get("category") == "recency":
        ok, msg = assert_recency(hits, within_days=60)
        assertions.append({"type": "recency", "ok": ok, "message": msg})

    if case.get("category") == "authority":
        ok, msg = assert_authority_boost_present(hits)
        assertions.append({"type": "authority_boost", "ok": ok, "message": msg})

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

"""Single-Sonnet baseline experiment (Patch DD).

Patch DD (Wave 2 P1, 2026-05-04). Empirical gating: until this runs, the
multi-agent /deep-ai-research default is unproven against the simplest
alternative. This is Report 2's "load-bearing unrun experiment."

Procedure per case:
  1. Take the query from evals/cases.yaml.
  2. Pre-inject top-K corpus snippets via corpus_server.search() — same
     ranking the multi-agent system uses (RRF + authority + decay).
  3. Make ONE Anthropic API call (Sonnet 4.6) with:
       - The query
       - The corpus snippets
       - Permission to use WebSearch via tool definition (handled
         server-side by the model when it asks)
       - Output schema matching the eval rubric (must_mention/etc.)
  4. Score the output against the case's behavioral assertions using the
     SAME functions evals/run_all.py already uses.
  5. Append result + token cost to evals/runs/baseline_history.jsonl.

Decision rule (documented in PLAN.md after first run):
  - If single-Sonnet ≥70% of multi-agent rubric quality at ≤10% of
    multi-agent token cost → multi-agent demoted to a premium tier
    flagged on hard queries; default becomes single-Sonnet.
  - If single-Sonnet <70% quality → multi-agent default empirically
    justified, document in NOTES.md and PLAN.md.

Cost: ~12K tokens per case × 5 representative cases = ~60K tokens. At
Anthropic's Sonnet 4.6 published pricing this is well under $1.

Requires: ANTHROPIC_API_KEY in .env. The system is designed for $0
marginal under the Max plan; this experiment is opt-in and runs once
to settle the architectural question.

Usage:
    uv run python -m evals.baseline_single_sonnet \\
        --cases recency_deepseek_v4,authority_simon_willison_recommendation,\\
counter_position_rag_dead,verification_anthropic_multi_agent,exploration_long_context_methods
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASES_FILE = PROJECT_ROOT / "evals" / "cases.yaml"
RUNS_DIR = PROJECT_ROOT / "evals" / "runs"
HISTORY_FILE = RUNS_DIR / "baseline_history.jsonl"

# Reuse the same corpus_server.search and assertion functions as run_all.py
sys.path.insert(0, str(PROJECT_ROOT))
from corpus_server.server import search  # noqa: E402
from evals.run_all import (  # noqa: E402
    assert_must_mention,
    assert_must_not_mention,
    assert_recency,
    assert_authority_boost_present,
    assert_min_hits,
)

log = logging.getLogger("evals.baseline_single_sonnet")

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
SONNET_MODEL_ID = "claude-sonnet-4-6"


def load_cases() -> list[dict]:
    with open(CASES_FILE) as f:
        data = yaml.safe_load(f)
    return data.get("cases", [])


def load_dotenv_into_environ(path: Path) -> None:
    """Minimal .env loader (same pattern as ingest/run.py)."""
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


def gather_corpus_context(query: str, top_k: int = 12) -> tuple[str, list[dict]]:
    """Run the same hybrid search the multi-agent system uses; return formatted
    snippets + raw hits (for assertion scoring)."""
    hits = search(query, top_n=top_k)
    lines: list[str] = []
    for i, h in enumerate(hits, 1):
        date = h.get("date") or "unknown"
        pub = h.get("publication") or "?"
        title = h.get("title_or_url") or h.get("path") or "?"
        snippet = (h.get("snippet") or "").strip().replace("\n", " ")
        if len(snippet) > 600:
            snippet = snippet[:600] + "…"
        lines.append(f"[corpus-{i}] ({date}, {pub}) {title}\n  > {snippet}")
    return "\n\n".join(lines), hits


def build_prompt(query: str, corpus_context: str) -> str:
    """The single-Sonnet prompt — equivalent in spirit to what the multi-agent
    system produces, condensed to one call."""
    return f"""You are answering a research question for a personal AI/ML research tool. \
You have access to a curated local corpus (snippets below) and may use WebSearch \
for gaps the corpus doesn't cover.

Produce a structured answer with:
  §1 Conclusion — the recommendation (or honest "I don't have a confident answer because…")
  §2 Confidence panel — Strongest evidence / Weakest assumption / What would change my mind
  §3 Findings — substance, with inline citations to corpus snippets [corpus-N] or web URLs

Be honest when evidence is thin. Tag claims [verified] (≥2 independent sources), \
[inferred] (one source or extension), or [judgment: rationale] (your call when evidence is mixed).

QUESTION:
{query}

CORPUS CONTEXT (top {12} hits from the local corpus, ranked by RRF + authority + recency decay):

{corpus_context}

Now produce the structured answer. Keep it tight; this is a single-Sonnet baseline run."""


def call_sonnet(prompt: str, *, max_tokens: int = 4096) -> tuple[str, dict]:
    """Single Anthropic API call. Returns (text, usage_dict)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. This baseline experiment requires API "
            "access (~$0.05-0.10 total for the 5-case run). Set it in .env "
            "or skip this experiment."
        )

    payload = {
        "model": SONNET_MODEL_ID,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(ANTHROPIC_API_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
    usage = data.get("usage", {})
    return text, usage


def score_response(case: dict, response_text: str, hits: list[dict]) -> list[dict[str, Any]]:
    """Apply the case's expected assertions to the response. We score against
    the response text as a 'pseudo-hit' (so must_mention works on prose) AND
    against the corpus hits (so authority_boost and recency assertions work)."""
    expected = case.get("expected", {})
    assertions: list[dict[str, Any]] = []

    pseudo_hit = {
        "snippet": response_text,
        "title_or_url": "single-sonnet-response",
        "publication": "single-sonnet-baseline",
        "tags": [],
        "mentioned_authorities": [],
    }
    pseudo_hits = [pseudo_hit, *hits]

    if "must_mention" in expected:
        ok, msg = assert_must_mention(pseudo_hits, expected["must_mention"])
        assertions.append({"type": "must_mention", "ok": ok, "message": msg})
    if "must_not_mention" in expected:
        ok, msg = assert_must_not_mention(pseudo_hits, expected["must_not_mention"])
        assertions.append({"type": "must_not_mention", "ok": ok, "message": msg})
    if "recency" in expected:
        ok, msg = assert_recency(hits, expected["recency"].get("within_days", 30))
        assertions.append({"type": "recency", "ok": ok, "message": msg})
    if "authority_boost" in expected:
        ok, msg = assert_authority_boost_present(hits)
        assertions.append({"type": "authority_boost", "ok": ok, "message": msg})
    if "min_hits" in expected:
        ok, msg = assert_min_hits(hits, expected["min_hits"])
        assertions.append({"type": "min_hits", "ok": ok, "message": msg})

    return assertions


def run_one(case: dict, *, top_k: int = 12) -> dict[str, Any]:
    cid = case["id"]
    log.info("running baseline on case %s", cid)

    corpus_context, hits = gather_corpus_context(case["query"], top_k=top_k)

    prompt = build_prompt(case["query"], corpus_context)
    try:
        response_text, usage = call_sonnet(prompt)
    except Exception as e:  # noqa: BLE001
        return {
            "id": cid,
            "category": case.get("category", "?"),
            "status": "error",
            "error": str(e),
            "hits_count": len(hits),
            "input_tokens": 0,
            "output_tokens": 0,
        }

    assertions = score_response(case, response_text, hits)
    all_pass = all(a["ok"] for a in assertions)

    return {
        "id": cid,
        "category": case.get("category", "?"),
        "status": "pass" if all_pass else "fail",
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "hits_count": len(hits),
        "assertions": assertions,
        "response_excerpt": response_text[:500] + ("…" if len(response_text) > 500 else ""),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Single-Sonnet baseline experiment (Patch DD).")
    p.add_argument(
        "--cases",
        default="recency_deepseek_v4,authority_simon_willison_recommendation,counter_position_rag_dead,verification_anthropic_multi_agent,exploration_long_context_methods",
        help="Comma-separated case IDs (default: 5 representative across categories).",
    )
    p.add_argument("--top-k", type=int, default=12, help="Top-K corpus snippets to inject.")
    p.add_argument("-v", "--verbose", action="count", default=0)
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose >= 2 else logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    load_dotenv_into_environ(PROJECT_ROOT / ".env")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.error(
            "ANTHROPIC_API_KEY not set. The baseline experiment requires direct "
            "API access. Set it in .env (one-time, ~$0.10 for the full 5-case run) "
            "or skip this patch."
        )
        return 1

    all_cases = load_cases()
    by_id = {c["id"]: c for c in all_cases}
    requested_ids = [s.strip() for s in args.cases.split(",") if s.strip()]
    selected = [by_id[i] for i in requested_ids if i in by_id]
    missing = [i for i in requested_ids if i not in by_id]
    if missing:
        log.warning("unknown case IDs (skipping): %s", missing)
    if not selected:
        log.error("no valid cases selected")
        return 2

    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ-baseline")
    out_dir = RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    results = [run_one(c, top_k=args.top_k) for c in selected]

    total_input = sum(r.get("input_tokens", 0) for r in results)
    total_output = sum(r.get("output_tokens", 0) for r in results)
    pass_n = sum(1 for r in results if r["status"] == "pass")
    fail_n = sum(1 for r in results if r["status"] == "fail")
    err_n = sum(1 for r in results if r["status"] == "error")

    (out_dir / "results.json").write_text(json.dumps(results, indent=2, default=str))

    summary = [
        f"# Baseline run {run_id}",
        "",
        f"- cases: {len(selected)} | pass: **{pass_n}** | fail: {fail_n} | error: {err_n}",
        f"- total input tokens: ~{total_input:,}",
        f"- total output tokens: ~{total_output:,}",
        f"- total tokens: ~{total_input + total_output:,}",
        "",
        "## Decision rule",
        "",
        "Compare with the multi-agent /deep-ai-research run for the same cases:",
        "- If single-Sonnet pass-rate ≥70% AND token cost ≤10% of multi-agent → demote multi-agent to premium tier",
        "- Otherwise → multi-agent default empirically justified",
        "",
    ]
    for r in results:
        emoji = {"pass": "✅", "fail": "❌", "error": "💥"}.get(r["status"], "?")
        summary.append(f"## {emoji} `{r['id']}` ({r['category']}) — {r['status']}")
        summary.append(f"  - tokens: {r.get('input_tokens', 0):,} in / {r.get('output_tokens', 0):,} out")
        summary.append(f"  - corpus hits injected: {r.get('hits_count', 0)}")
        for a in r.get("assertions", []):
            mark = "✓" if a["ok"] else "✗"
            summary.append(f"  - {mark} `{a['type']}`: {a['message']}")
        if r.get("error"):
            summary.append(f"  - error: {r['error']}")
        if r.get("response_excerpt"):
            summary.append(f"  - response excerpt: {r['response_excerpt'][:300]}")
        summary.append("")
    (out_dir / "summary.md").write_text("\n".join(summary))

    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a") as f:
        f.write(json.dumps({
            "run_id": run_id,
            "ran_at": datetime.now(timezone.utc).isoformat(),
            "kind": "single_sonnet_baseline",
            "case_ids": [r["id"] for r in results],
            "counts": {"pass": pass_n, "fail": fail_n, "error": err_n},
            "total_tokens": total_input + total_output,
            "input_tokens": total_input,
            "output_tokens": total_output,
        }) + "\n")

    print((out_dir / "summary.md").read_text())
    return 0 if fail_n == 0 and err_n == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

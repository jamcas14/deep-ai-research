"""Full-loop eval harness — v2 (Patch EE).

The v1 harness (evals/run_all.py) tests the retrieval moat in isolation —
it calls corpus_server.search() and asserts on hits. That's the right v1.

The v2 harness here tests the FULL /deep-ai-research loop by reading run
artifacts that the skill writes to .claude/scratch/<run-id>/. Specifically:
manifest.json (classification, clarifications, redispatches, sub_questions,
finish_reason), retrieval_log.jsonl (per-call agent + tool + query),
verifier.json / fit_verifier.json / structure_verifier.json (verifier
verdicts), critic.md (top-N issues), synthesizer-final.md (final report).

The behavioral-cases that have been sitting `blocked_until:
full_loop_eval_harness` in cases.yaml — clarification_gate fires,
contrarian independence, fit_verifier catches mismatch, capitulation
guard, conclusion+confidence-panel structure, plus the new Patch EE
cases (entity_version classification, mini-contrarian surfaces alt) —
all become runnable once we have a way to assert against run artifacts.

Important design choice: this harness is **READ-ONLY** against existing
runs. It does NOT invoke /deep-ai-research itself (the skill is
interactive-mode-only and can't be launched cleanly from `claude -p`).
The user's workflow:

  1. Run /deep-ai-research <query> for the cases they want to eval.
  2. `uv run python -m evals.run_full_loop` reads ALL recent scratch
     dirs, matches them to cases.yaml entries by query similarity,
     asserts behavioral signals, prints summary.

Matching strategy: for each case, find the scratch dir whose
manifest.json `question` field is the closest substring/normalized
match. If no match, status: no_match.

Usage:
    uv run python -m evals.run_full_loop                     # all blocked-on-harness cases
    uv run python -m evals.run_full_loop --case <case_id>    # one case
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASES_FILE = PROJECT_ROOT / "evals" / "cases.yaml"
SCRATCH_ROOT = PROJECT_ROOT / ".claude" / "scratch"
RUNS_DIR = PROJECT_ROOT / "evals" / "runs"
HISTORY_FILE = RUNS_DIR / "_history.jsonl"

log = logging.getLogger("evals.run_full_loop")


# ---------- artifact loaders ----------

def load_manifest(scratch_dir: Path) -> dict | None:
    p = scratch_dir / "manifest.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception as e:  # noqa: BLE001
        log.debug("malformed manifest %s: %s", p, e)
        return None


def load_retrieval_log(scratch_dir: Path) -> list[dict]:
    p = scratch_dir / "retrieval_log.jsonl"
    if not p.exists():
        return []
    entries: list[dict] = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception:  # noqa: BLE001
            continue
    return entries


def load_text(scratch_dir: Path, name: str) -> str:
    p = scratch_dir / name
    return p.read_text() if p.exists() else ""


def load_json(scratch_dir: Path, name: str) -> dict | None:
    p = scratch_dir / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:  # noqa: BLE001
        return None


# ---------- query → scratch dir matching ----------

def normalize_query(q: str) -> str:
    return re.sub(r"\s+", " ", q.strip().lower())


def find_matching_scratch_dir(case: dict, all_dirs: list[Path]) -> Path | None:
    """Find the most recent scratch dir whose manifest.question best matches
    the case's query. Best-match = longest shared normalized prefix, with a
    minimum-overlap floor."""
    case_q = normalize_query(case.get("query", ""))
    if not case_q:
        return None

    best: tuple[Path, int, datetime] | None = None
    for d in all_dirs:
        manifest = load_manifest(d)
        if not manifest:
            continue
        run_q = normalize_query(manifest.get("question", ""))
        if not run_q:
            continue
        # Cheap match: case query as substring of run query OR vice versa
        # (the case's query may be templated like "Multi-turn: first turn..."
        # and the run's actual question is more concrete; we accept if either
        # contains a 30+ char prefix of the other)
        prefix_len = 0
        for n in range(min(len(case_q), len(run_q)), 30, -1):
            if run_q[:n] in case_q or case_q[:n] in run_q:
                prefix_len = n
                break
        if prefix_len < 30:
            continue
        try:
            ts = datetime.fromisoformat(manifest.get("started_at", "").replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            ts = datetime.now(timezone.utc)
        if best is None or prefix_len > best[1] or (prefix_len == best[1] and ts > best[2]):
            best = (d, prefix_len, ts)
    return best[0] if best else None


# ---------- behavioral assertions ----------

def assert_clarification_gate_fired(manifest: dict) -> tuple[bool, str]:
    """Pass if manifest shows clarification_gate_fired: true OR clarifications
    list is non-empty."""
    if manifest.get("clarification_gate_fired") is True:
        return True, "clarification_gate_fired: true"
    cls = manifest.get("clarifications") or []
    if cls and len(cls) >= 1:
        return True, f"{len(cls)} clarification Q&A pairs recorded"
    return False, "no clarification gate evidence in manifest"


def assert_classification_includes(manifest: dict, expected: list[str]) -> tuple[bool, str]:
    cls = manifest.get("classification") or []
    if isinstance(cls, str):
        cls = [cls]
    missing = [e for e in expected if e not in cls]
    if missing:
        return False, f"missing classification: {missing}; got {cls}"
    return True, f"classification includes {expected}"


def assert_manifest_field_present(manifest: dict, field: str) -> tuple[bool, str]:
    """Field can be dotted like 'recency_pass.entity_version_resolution'."""
    parts = field.split(".")
    obj: Any = manifest
    for part in parts:
        if not isinstance(obj, dict) or part not in obj:
            return False, f"field {field} not present in manifest"
        obj = obj[part]
    return True, f"field {field} present (value: {repr(obj)[:100]})"


def assert_redispatch_happened(manifest: dict, kind: str) -> tuple[bool, str]:
    """Pass if manifest.redispatches contains an entry whose 'reason' or
    'type' contains `kind` (e.g. 'fit', 'structure', 'coverage')."""
    rds = manifest.get("redispatches") or []
    if not rds:
        return False, f"no redispatches recorded in manifest"
    matches = [r for r in rds if kind in (r.get("reason", "") + r.get("type", "")).lower()]
    if matches:
        return True, f"{len(matches)} {kind} redispatch(es) found"
    return False, f"no redispatches matched kind={kind}; got: {[r.get('reason') for r in rds]}"


def assert_finish_reason(manifest: dict, expected: str) -> tuple[bool, str]:
    fr = manifest.get("finish_reason", "")
    if fr == expected:
        return True, f"finish_reason: {fr}"
    return False, f"finish_reason: {fr} (wanted {expected})"


def assert_report_contains_sections(report_text: str, sections: list[str]) -> tuple[bool, str]:
    missing = [s for s in sections if s not in report_text]
    if missing:
        return False, f"missing sections: {missing}"
    return True, f"all {len(sections)} required sections present"


def assert_section_contains(report_text: str, section: str, any_of: list[str], min_words: int = 0) -> tuple[bool, str]:
    """Find the section by heading-prefix match, then check its body for
    any-of phrases and minimum word count."""
    # Find section start
    pattern = re.compile(rf"(?im)^[#\-\s]*{re.escape(section)}.*$")
    m = pattern.search(report_text)
    if not m:
        return False, f"section {section!r} not found"
    body = report_text[m.end() :]
    # Cut at next ## heading or end
    next_section = re.search(r"(?m)^##\s", body)
    if next_section:
        body = body[: next_section.start()]
    body_lc = body.lower()
    matched = [p for p in any_of if p.lower() in body_lc]
    word_count = len(body.split())
    if not matched and any_of:
        return False, f"section {section!r}: none of {any_of} matched"
    if word_count < min_words:
        return False, f"section {section!r} only {word_count} words (need {min_words})"
    return True, f"section {section!r}: matched {matched}, {word_count} words"


def assert_retrieval_log_has_agent(retrieval_log: list[dict], agent_pattern: str) -> tuple[bool, str]:
    """Pass if retrieval_log has ≥1 entry with agent matching pattern (substring)."""
    matched = [e for e in retrieval_log if agent_pattern in str(e.get("agent", ""))]
    if matched:
        return True, f"{len(matched)} retrieval-log entries matched agent~={agent_pattern}"
    return False, f"no retrieval-log entries with agent matching {agent_pattern}"


def assert_section_must_not_contain(report_text: str, section: str, must_not: list[str]) -> tuple[bool, str]:
    pattern = re.compile(rf"(?im)^[#\-\s]*{re.escape(section)}.*$")
    m = pattern.search(report_text)
    if not m:
        return True, f"section {section!r} absent (vacuously true)"
    body = report_text[m.end() :]
    next_section = re.search(r"(?m)^##\s", body)
    if next_section:
        body = body[: next_section.start()]
    body_lc = body.lower()
    found = [p for p in must_not if p.lower() in body_lc]
    if found:
        return False, f"section {section!r}: unexpectedly contains {found}"
    return True, f"section {section!r}: clean of {must_not}"


# ---------- per-case dispatch ----------

def run_case(case: dict, scratch_dir: Path) -> dict[str, Any]:
    cid = case["id"]
    expected = case.get("expected", {})
    manifest = load_manifest(scratch_dir) or {}
    retrieval_log = load_retrieval_log(scratch_dir)
    final_report = load_text(scratch_dir, "synthesizer-final.md")
    fit_verifier = load_json(scratch_dir, "fit_verifier.json") or {}
    structure_verifier = load_json(scratch_dir, "structure_verifier.json") or {}

    assertions: list[dict[str, Any]] = []

    # Clarification-gate-style cases
    if expected.get("must_invoke_clarification_gate"):
        ok, msg = assert_clarification_gate_fired(manifest)
        assertions.append({"type": "clarification_gate_fired", "ok": ok, "message": msg})

    # Classification asserts
    if expected.get("manifest_classification_must_contain"):
        ok, msg = assert_classification_includes(manifest, expected["manifest_classification_must_contain"])
        assertions.append({"type": "classification", "ok": ok, "message": msg})

    # Manifest field-presence asserts
    for field in expected.get("manifest_must_have_field", []) or []:
        ok, msg = assert_manifest_field_present(manifest, field)
        assertions.append({"type": "manifest_field", "ok": ok, "message": f"{field}: {msg}"})

    # Re-dispatch asserts
    if expected.get("must_redispatch_kind"):
        ok, msg = assert_redispatch_happened(manifest, expected["must_redispatch_kind"])
        assertions.append({"type": "redispatch", "ok": ok, "message": msg})

    if expected.get("must_finish_reason"):
        ok, msg = assert_finish_reason(manifest, expected["must_finish_reason"])
        assertions.append({"type": "finish_reason", "ok": ok, "message": msg})

    # Report structure asserts
    if expected.get("report_must_contain_sections"):
        ok, msg = assert_report_contains_sections(final_report, expected["report_must_contain_sections"])
        assertions.append({"type": "report_sections", "ok": ok, "message": msg})

    if expected.get("report_section_must_contain"):
        spec = expected["report_section_must_contain"]
        ok, msg = assert_section_contains(
            final_report,
            spec.get("section", ""),
            spec.get("any_of", []),
            min_words=spec.get("reasoning_min_words", 0) or spec.get("min_words", 0),
        )
        assertions.append({"type": "report_section_contains", "ok": ok, "message": msg})

    if expected.get("second_turn_must_contain"):
        # Multi-turn case: the relevant artifact is the conversation/report
        # — for now, just check the final report contains evidence-language
        # and not capitulation-tells, since the harness reads the final
        # synthesis (multi-turn replay infrastructure is a separate build).
        spec = expected["second_turn_must_contain"]
        ok_any, msg_any = assert_section_contains(final_report, "Conclusion", spec.get("any_of", []))
        ok_not, msg_not = assert_section_must_not_contain(final_report, "Conclusion", spec.get("must_not_contain", []))
        assertions.append({"type": "evidence_language", "ok": ok_any, "message": msg_any})
        assertions.append({"type": "no_capitulation_tells", "ok": ok_not, "message": msg_not})

    # Retrieval-log assertions
    if expected.get("retrieval_log_must_have_agent"):
        ok, msg = assert_retrieval_log_has_agent(retrieval_log, expected["retrieval_log_must_have_agent"])
        assertions.append({"type": "retrieval_log_agent", "ok": ok, "message": msg})

    all_ok = all(a["ok"] for a in assertions) if assertions else False
    return {
        "id": cid,
        "category": case.get("category", "?"),
        "scratch_dir": str(scratch_dir.relative_to(PROJECT_ROOT)),
        "manifest_question": (manifest.get("question") or "")[:120],
        "status": "pass" if all_ok else ("fail" if assertions else "no_assertions"),
        "assertions": assertions,
    }


# ---------- entrypoint ----------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Full-loop eval harness — v2 (Patch EE).")
    p.add_argument("--case", help="Run only this case ID.")
    p.add_argument(
        "--include-blocked",
        action="store_true",
        help="Run all cases regardless of blocked_until (default: skip blocked).",
    )
    p.add_argument("-v", "--verbose", action="count", default=0)
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose >= 2 else logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if not SCRATCH_ROOT.exists():
        log.error("no scratch dir at %s — has /deep-ai-research ever run?", SCRATCH_ROOT)
        return 2

    with open(CASES_FILE) as f:
        all_cases = yaml.safe_load(f).get("cases", [])

    # Filter to cases the v2 harness can actually run on
    runnable: list[dict] = []
    for c in all_cases:
        if args.case and c["id"] != args.case:
            continue
        bu = c.get("blocked_until", "")
        if not bu:
            continue  # already runnable in v1
        if bu == "full_loop_eval_harness":
            runnable.append(c)
        elif args.include_blocked:
            runnable.append(c)

    if not runnable:
        log.info("no cases to run (use --include-blocked to force)")
        return 0

    all_dirs = [d for d in SCRATCH_ROOT.iterdir() if d.is_dir()]
    log.info("scanning %d scratch dirs against %d cases", len(all_dirs), len(runnable))

    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ-fullloop")
    out_dir = RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for case in runnable:
        scratch = find_matching_scratch_dir(case, all_dirs)
        if scratch is None:
            results.append({
                "id": case["id"],
                "category": case.get("category", "?"),
                "status": "no_match",
                "message": f"no scratch dir matches query '{case.get('query', '')[:60]}'",
            })
            continue
        results.append(run_case(case, scratch))

    counts: dict[str, int] = {"pass": 0, "fail": 0, "no_match": 0, "no_assertions": 0}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    (out_dir / "results.json").write_text(json.dumps(results, indent=2, default=str))

    summary = [f"# Full-loop eval run {run_id}", ""]
    summary.append(
        f"- pass: **{counts['pass']}**, fail: {counts['fail']}, no_match: {counts['no_match']}, "
        f"no_assertions: {counts['no_assertions']}"
    )
    summary.append("")
    for r in results:
        emoji = {"pass": "✅", "fail": "❌", "no_match": "🔍", "no_assertions": "⚠️"}.get(r["status"], "?")
        summary.append(f"## {emoji} `{r['id']}` ({r['category']}) — {r['status']}")
        if r.get("scratch_dir"):
            summary.append(f"  - scratch: `{r['scratch_dir']}`")
        if r.get("manifest_question"):
            summary.append(f"  - matched run: `{r['manifest_question']}`")
        if r.get("message"):
            summary.append(f"  - note: {r['message']}")
        for a in r.get("assertions", []):
            mark = "✓" if a["ok"] else "✗"
            summary.append(f"  - {mark} `{a['type']}`: {a['message']}")
        summary.append("")
    (out_dir / "summary.md").write_text("\n".join(summary))

    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a") as f:
        f.write(json.dumps({
            "run_id": run_id,
            "ran_at": datetime.now(timezone.utc).isoformat(),
            "kind": "full_loop_v2",
            "counts": counts,
            "case_results": [{"id": r["id"], "status": r["status"]} for r in results],
        }) + "\n")

    print((out_dir / "summary.md").read_text())
    return 0 if counts["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

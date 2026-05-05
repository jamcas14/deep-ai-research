"""Visualize a /deep-ai-research run from its scratch artifacts.

The pipeline is a fixed-depth DAG with two parallel fan-out points
(Stage 3 researchers + contrarian; Stage 5 verifiers + critic), not a
recursive tree. This script renders three views from the existing
artifacts (`stage_log.jsonl`, `retrieval_log.jsonl`, `manifest.json`):

  1. ASCII swimlane — per-stage wall-time + 5h-window delta
  2. Per-researcher retrieval call breakdown
  3. Optional Mermaid `gantt` block for inline rendering in editors/browsers

Usage:
    uv run python -m ingest.viz_run                          # latest run
    uv run python -m ingest.viz_run <run-id>                 # specific run
    uv run python -m ingest.viz_run <run-id> --mermaid       # also emit Mermaid
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRATCH_DIR = PROJECT_ROOT / ".claude" / "scratch"


def _latest_run_id() -> str | None:
    if not SCRATCH_DIR.exists():
        return None
    runs = [p for p in SCRATCH_DIR.iterdir() if p.is_dir() and (p / "manifest.json").exists()]
    if not runs:
        return None
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0].name


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def render_swimlane(run_dir: Path) -> str:
    """ASCII timeline + per-researcher retrieval breakdown."""
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    stages = _read_jsonl(run_dir / "stage_log.jsonl")
    retrieval = _read_jsonl(run_dir / "retrieval_log.jsonl")

    out: list[str] = []
    out.append(f"# Run: {manifest.get('run_id', run_dir.name)}")
    out.append("")
    out.append(f"**Question:** {manifest.get('question', '?')}")
    out.append(f"**Classification:** {', '.join(manifest.get('classification') or ['?'])}")
    out.append(f"**Started:** {manifest.get('started_at', '?')}  |  "
               f"**Finished:** {manifest.get('finished_at', '?')}  |  "
               f"**Reason:** {manifest.get('finish_reason', '?')}")
    out.append("")

    # Stage timeline
    out.append("## Pipeline timeline")
    out.append("")
    if not stages:
        out.append("_(no stage_log.jsonl — Patch UU not active for this run)_")
    else:
        out.append("| Stage | Started | Wall | Δ5h % |")
        out.append("|---|---|---:|---:|")
        # Compute wall by diffing consecutive entries; last stage uses finished_at.
        finished = _parse_iso(manifest.get("finished_at"))
        max_wall = 0.0
        rows: list[tuple[str, str, float, float | None]] = []
        for i, s in enumerate(stages):
            t0 = _parse_iso(s.get("started_at"))
            if i + 1 < len(stages):
                t1 = _parse_iso(stages[i + 1].get("started_at"))
            else:
                t1 = finished
            wall = (t1 - t0).total_seconds() if t0 and t1 else 0.0
            max_wall = max(max_wall, wall)
            d5h: float | None = None
            this_pct = (s.get("snapshot_before") or {}).get("five_hour_pct")
            next_snap = stages[i + 1].get("snapshot_before") if i + 1 < len(stages) else None
            next_pct = (next_snap or {}).get("five_hour_pct") if next_snap else None
            if isinstance(this_pct, (int, float)) and isinstance(next_pct, (int, float)):
                d5h = next_pct - this_pct
            rows.append((s.get("stage", "?"), s.get("started_at", "?"), wall, d5h))
        for stage, started, wall, d5h in rows:
            d5h_str = f"+{d5h:.2f}" if isinstance(d5h, (int, float)) else "—"
            out.append(f"| `{stage}` | {started} | {wall:.0f}s | {d5h_str} |")

        # Bar chart
        out.append("")
        out.append("```")
        for stage, _, wall, _ in rows:
            bar_len = int(round((wall / max_wall) * 40)) if max_wall > 0 else 0
            bar = "█" * bar_len if bar_len > 0 else "·"
            out.append(f"  {stage:<32}  {bar}  {wall:.0f}s")
        out.append("```")

    # Retrieval breakdown
    out.append("")
    out.append("## Retrieval calls per agent")
    out.append("")
    if not retrieval:
        out.append("_(no retrieval_log.jsonl)_")
    else:
        per_agent: dict[str, Counter] = defaultdict(Counter)
        for r in retrieval:
            agent = r.get("agent") or "unknown"
            tool = r.get("tool") or "unknown"
            per_agent[agent][tool] += 1
        # Order agents: skill-orchestrator first, then researcher-N numerically, then contrarian, then rest.
        def _agent_sort_key(a: str) -> tuple[int, str]:
            if a == "skill-orchestrator":
                return (0, a)
            if a.startswith("researcher-"):
                try:
                    return (1, f"{int(a.split('-')[1]):03d}")
                except (ValueError, IndexError):
                    return (1, a)
            if a == "contrarian":
                return (2, a)
            return (3, a)
        max_calls = max(sum(c.values()) for c in per_agent.values())
        out.append("```")
        for agent in sorted(per_agent.keys(), key=_agent_sort_key):
            counts = per_agent[agent]
            total = sum(counts.values())
            bar_len = int(round((total / max_calls) * 30)) if max_calls > 0 else 0
            bar = "█" * bar_len if bar_len > 0 else "·"
            tool_breakdown = ", ".join(f"{t}×{n}" for t, n in counts.most_common())
            cap_flag = ""
            if agent.startswith("researcher-") and total > 8:
                cap_flag = " ⚠ over 8-call cap"
            out.append(f"  {agent:<24}  {bar:<30}  {total} ({tool_breakdown}){cap_flag}")
        out.append("```")

    return "\n".join(out)


def render_mermaid(run_dir: Path) -> str:
    """Mermaid gantt + flowchart blocks. Render-ready in editors that support it."""
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    stages = _read_jsonl(run_dir / "stage_log.jsonl")

    out: list[str] = ["", "## Mermaid: pipeline gantt", "", "```mermaid", "gantt"]
    out.append(f"    title {manifest.get('run_id', run_dir.name)}")
    out.append("    dateFormat HH:mm:ss")
    out.append("    axisFormat %M:%S")
    out.append("    section Pipeline")
    finished = _parse_iso(manifest.get("finished_at"))
    for i, s in enumerate(stages):
        t0 = _parse_iso(s.get("started_at"))
        t1 = _parse_iso(stages[i + 1].get("started_at")) if i + 1 < len(stages) else finished
        if not t0:
            continue
        wall = max(int((t1 - t0).total_seconds()), 1) if t1 else 1
        label = s.get("stage", f"stage_{i}").replace("stage_", "")
        out.append(f"    {label} :{t0.strftime('%H:%M:%S')}, {wall}s")
    out.append("```")
    out.append("")

    # Flowchart of the DAG itself (independent of run)
    out.append("## Mermaid: pipeline structure")
    out.append("")
    out.append("```mermaid")
    out.append("flowchart TD")
    out.append("    S0[Stage 0 clarification gate]")
    out.append("    S05[Stage 0.5 query-classifier gate]")
    out.append("    S1[Stage 1 classification + sub-questions]")
    out.append("    S2[Stage 2 forced recency pass]")
    out.append("    R1[researcher-1]:::par")
    out.append("    R2[researcher-2]:::par")
    out.append("    R3[researcher-N]:::par")
    out.append("    C[contrarian]:::par")
    out.append("    S4[Stage 4 synthesizer draft]")
    out.append("    V1[citation verifier]:::par")
    out.append("    V2[fit verifier]:::par")
    out.append("    V3[structure verifier]:::par")
    out.append("    CR[critic]:::par")
    out.append("    S6{fit/structure fail?}")
    out.append("    S8[Stage 8 synthesizer final]")
    out.append("    S9[Stage 9 finalize + index]")
    out.append("    S0 --> S05 --> S1 --> S2")
    out.append("    S2 --> R1 & R2 & R3 & C --> S4")
    out.append("    S4 --> V1 & V2 & V3 & CR --> S6")
    out.append("    S6 -- yes --> S2")
    out.append("    S6 -- no --> S8 --> S9")
    out.append("    classDef par fill:#e8f5e9,stroke:#43a047")
    out.append("```")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run_id", nargs="?", help="run id (default: latest)")
    p.add_argument("--mermaid", action="store_true", help="also emit Mermaid blocks")
    args = p.parse_args(argv)

    run_id = args.run_id or _latest_run_id()
    if not run_id:
        print("No runs found in .claude/scratch/", file=sys.stderr)
        return 2
    run_dir = SCRATCH_DIR / run_id
    if not run_dir.exists() or not (run_dir / "manifest.json").exists():
        print(f"Run not found or missing manifest: {run_dir}", file=sys.stderr)
        return 2

    print(render_swimlane(run_dir))
    if args.mermaid:
        print(render_mermaid(run_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())

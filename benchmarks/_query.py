"""Query functions over benchmark snapshots stored on disk.

Read-only — all writes go through scraper run() → write_snapshot.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from benchmarks._base import Snapshot

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SNAPSHOTS_DIR = PROJECT_ROOT / "corpus" / "benchmarks"


def _snapshots_dir(benchmark_name: str | None = None) -> Path:
    base = DEFAULT_SNAPSHOTS_DIR
    return base / benchmark_name if benchmark_name else base


def _iter_snapshot_files(benchmark_name: str | None = None):
    d = _snapshots_dir(benchmark_name)
    if not d.exists():
        return
    yield from sorted(d.rglob("*.json"))


def _load_file(path: Path) -> list[Snapshot]:
    raw = json.loads(path.read_text())
    out: list[Snapshot] = []
    for r in raw if isinstance(raw, list) else [raw]:
        try:
            out.append(Snapshot(
                benchmark_name=r["benchmark_name"],
                model=r["model"],
                score=float(r["score"]),
                metric_type=r["metric_type"],
                snapshot_at=datetime.fromisoformat(r["snapshot_at"]),
                metadata=r.get("metadata") or {},
            ))
        except (KeyError, ValueError, TypeError):
            continue
    return out


def write_snapshots(benchmark_name: str, snapshots: list[Snapshot]) -> Path:
    """Append-only: write today's snapshots as a single timestamped JSON file."""
    if not snapshots:
        return _snapshots_dir(benchmark_name)
    snapshot_at = snapshots[0].snapshot_at
    out_dir = _snapshots_dir(benchmark_name)
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = snapshot_at.strftime("%Y-%m-%dT%H%M%SZ") + ".json"
    out_path = out_dir / fname
    out_path.write_text(json.dumps([s.to_dict() for s in snapshots], indent=2))
    return out_path


def current(benchmark: str, model: str) -> Snapshot | None:
    """Most recent snapshot for (benchmark, model)."""
    best: Snapshot | None = None
    for path in _iter_snapshot_files(benchmark):
        for s in _load_file(path):
            if s.model.lower() == model.lower():
                if best is None or s.snapshot_at > best.snapshot_at:
                    best = s
    return best


def history(benchmark: str, model: str, *, since: datetime | None = None) -> list[Snapshot]:
    """All snapshots for (benchmark, model), sorted oldest → newest."""
    out: list[Snapshot] = []
    for path in _iter_snapshot_files(benchmark):
        for s in _load_file(path):
            if s.model.lower() != model.lower():
                continue
            if since and s.snapshot_at < since:
                continue
            out.append(s)
    out.sort(key=lambda s: s.snapshot_at)
    return out


def top(benchmark: str, *, n: int = 10, snapshot_at: datetime | None = None) -> list[Snapshot]:
    """Top-N models by score for the most recent (or specified) snapshot."""
    by_model: dict[str, Snapshot] = {}
    for path in _iter_snapshot_files(benchmark):
        for s in _load_file(path):
            if snapshot_at and s.snapshot_at > snapshot_at:
                continue
            existing = by_model.get(s.model)
            if existing is None or s.snapshot_at > existing.snapshot_at:
                by_model[s.model] = s
    snapshots = list(by_model.values())
    snapshots.sort(key=lambda s: s.score, reverse=True)
    return snapshots[:n]


def staleness(*, max_silence_hours: int = 168) -> list[dict[str, Any]]:
    """Per-benchmark health: how recent is the latest snapshot."""
    out: list[dict[str, Any]] = []
    base = DEFAULT_SNAPSHOTS_DIR
    if not base.exists():
        return out
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_silence_hours)
    for benchmark_dir in sorted(base.iterdir()):
        if not benchmark_dir.is_dir():
            continue
        latest_at: datetime | None = None
        for path in benchmark_dir.rglob("*.json"):
            for s in _load_file(path):
                if latest_at is None or s.snapshot_at > latest_at:
                    latest_at = s.snapshot_at
        out.append({
            "benchmark": benchmark_dir.name,
            "latest_at": latest_at.isoformat() if latest_at else None,
            "stale": (latest_at is None) or (latest_at < cutoff),
        })
    return out

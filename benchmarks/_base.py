"""Snapshot type + scraper protocol shared by all benchmarks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Protocol


@dataclass
class Snapshot:
    """One model's score on one benchmark at one point in time."""

    benchmark_name: str
    model: str                       # normalized model identifier
    score: float
    metric_type: str                 # 'elo', 'accuracy', 'pct_correct', 'pass@1', ...
    snapshot_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_name": self.benchmark_name,
            "model": self.model,
            "score": self.score,
            "metric_type": self.metric_type,
            "snapshot_at": self.snapshot_at.isoformat(),
            "metadata": self.metadata,
        }


class Scraper(Protocol):
    """Each benchmarks/scrapers/<name>.py module exposes a `scrape()` callable."""

    def __call__(self) -> Iterable[Snapshot]: ...

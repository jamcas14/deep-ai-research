"""Benchmarks subsystem.

Separate from the markdown corpus because benchmark data is shaped differently:
- snapshot-not-summary
- comparison-oriented retrieval (current + history)
- per-benchmark cadence
- authority weighting is meaningless on LMArena ELO

Snapshots stored as JSON files in `corpus/benchmarks/<benchmark>/<YYYY-MM-DD>.json`.
Public surface: `current()`, `history()`, `top()`, `staleness()`.

Add a benchmark by:
  1. Adding a scraper module under `benchmarks/scrapers/<name>.py` with a
     `scrape() -> list[Snapshot]` function.
  2. Adding a config entry under `benchmarks/configs/<name>.toml`.
  3. Running `python -m benchmarks.run --benchmark <name>` to verify.
"""

from benchmarks._base import Snapshot
from benchmarks._query import current, history, staleness, top

__all__ = ["Snapshot", "current", "history", "staleness", "top"]

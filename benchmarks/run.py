"""Run benchmark scrapers and write snapshots to corpus/benchmarks/."""

from __future__ import annotations

import argparse
import importlib
import logging
import sys
from typing import Iterable

from benchmarks._base import Snapshot
from benchmarks._query import write_snapshots

log = logging.getLogger("benchmarks.run")

# Scraper registry. Add new ones here.
SCRAPERS = [
    "openrouter",
    # Step 8 v2: lmarena, artificial_analysis, livebench, hf_leaderboards.
    # Each needs its own scraper module under benchmarks/scrapers/.
]


def run_one(name: str) -> int:
    """Import scraper module and write its snapshots. Returns count written."""
    try:
        module = importlib.import_module(f"benchmarks.scrapers.{name}")
    except ImportError as e:
        log.error("no scraper for %s: %s", name, e)
        return 0
    if not hasattr(module, "scrape"):
        log.error("scraper %s has no scrape() function", name)
        return 0
    snapshots = list(module.scrape())
    if not snapshots:
        log.warning("scraper %s produced 0 snapshots", name)
        return 0
    out = write_snapshots(name, snapshots)
    log.info("wrote %d snapshots for %s → %s", len(snapshots), name, out)
    return len(snapshots)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--benchmark", help="run only this scraper (default: all)")
    p.add_argument("-v", "--verbose", action="count", default=0)
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    targets = [args.benchmark] if args.benchmark else SCRAPERS
    total = 0
    for name in targets:
        total += run_one(name)
    log.info("total snapshots written: %d", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())

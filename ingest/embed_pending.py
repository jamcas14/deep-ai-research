"""CLI entry point: embed any markdown sources whose chunks aren't yet in sqlite-vec.

Usage:
    uv sync --extra embed                    # one-time, downloads PyTorch (~3GB)
    uv run python -m ingest.embed_pending    # embed pending; idempotent

This script is separate from ingest/run.py so users can run ingestion without
PyTorch installed. The corpus markdown is usable on its own; embeddings just
unlock semantic search.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml

from ingest.embed import embed_pending

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("-v", "--verbose", action="count", default=0)
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose >= 2 else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    with open(PROJECT_ROOT / "config" / "paths.yaml") as f:
        paths = yaml.safe_load(f)

    corpus_dir = (PROJECT_ROOT / paths["corpus_dir"]).resolve()
    sqlite_path = (PROJECT_ROOT / paths["sqlite_path"]).resolve()

    count = embed_pending(corpus_dir, sqlite_path, batch_size=args.batch_size)
    print(f"Embedded {count} sources into {sqlite_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

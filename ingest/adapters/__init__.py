"""Source adapters. Each module implements `iter_new() -> Iterable[RawSource]`."""

from ingest.adapters._base import RawSource

__all__ = ["RawSource"]

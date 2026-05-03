"""Adapter contract. Each source adapter yields RawSource records; the runner
handles canonicalization, dedup, and write."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable, Protocol


@dataclass
class RawSource:
    """One ingested item, before canonicalization + summarization."""

    url: str
    title: str
    publication: str
    source_type: str
    date: date
    authors: list[str]
    body: str  # full content; format varies by source
    content_format: str = "markdown"  # markdown | html | plain
    tags: list[str] = field(default_factory=list)

    # Hints for engagement detection — adapters fill these where they know.
    # Otherwise summarization (Haiku) extracts.
    mentioned_entities: list[str] = field(default_factory=list)
    mentioned_authorities: list[str] = field(default_factory=list)


class Adapter(Protocol):
    """Adapter contract."""

    name: str
    publication: str
    poll_interval_seconds: int
    rate_limit_key: str

    def iter_new(self, since: datetime | None = None) -> Iterable[RawSource]:
        """Yield items newer than `since`. If None, yield everything available."""
        ...

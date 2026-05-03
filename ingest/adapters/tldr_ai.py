"""TLDR AI adapter. Daily-weekday, model releases / research / launches / funding."""

from __future__ import annotations

from ingest.adapters._rss import RSSAdapter


def build() -> RSSAdapter:
    return RSSAdapter(
        name="tldr_ai",
        publication="TLDR AI",
        feed_url="https://tldr.tech/api/rss/ai",
        source_type="newsletter",
        poll_interval_seconds=7200,
        rate_limit_key="tldr.tech",
    )

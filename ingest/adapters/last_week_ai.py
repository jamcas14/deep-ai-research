"""Last Week in AI adapter."""

from __future__ import annotations

from ingest.adapters._rss import RSSAdapter


def build() -> RSSAdapter:
    return RSSAdapter(
        name="last_week_ai",
        publication="Last Week in AI",
        feed_url="https://lastweekin.ai/feed",
        source_type="newsletter",
        poll_interval_seconds=21600,
        rate_limit_key="lastweekin.ai",
    )

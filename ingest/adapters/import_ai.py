"""Import AI adapter. Weekly newsletter by Jack Clark (Anthropic co-founder)."""

from __future__ import annotations

from ingest.adapters._rss import RSSAdapter


def build() -> RSSAdapter:
    return RSSAdapter(
        name="import_ai",
        publication="Import AI",
        feed_url="https://importai.substack.com/feed",
        source_type="newsletter",
        poll_interval_seconds=21600,  # 6h; weekly newsletter
        rate_limit_key="substack",
    )

"""Smol AI / AINews adapter. Tier 1 — partially compensates for no Twitter.

AINews migrated from Buttondown to news.smol.ai in 2025/26. Joined Latent Space
under one subscription. Daily, summarizes top AI Discords / Reddits / X posts.
"""

from __future__ import annotations

from ingest.adapters._rss import RSSAdapter


class AINewsAdapter(RSSAdapter):
    pass


def build() -> AINewsAdapter:
    return AINewsAdapter(
        name="ainews",
        publication="Smol AI / AINews",
        feed_url="https://news.smol.ai/rss.xml",
        source_type="newsletter",
        poll_interval_seconds=3600,
        rate_limit_key="news.smol.ai",
    )

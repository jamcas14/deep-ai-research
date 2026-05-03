"""OpenRouter rankings scraper.

OpenRouter publishes per-model usage / popularity rankings via their public API
at https://openrouter.ai/api/v1/models. Free, no auth required for reads.

This is a "popularity by usage" signal, not a quality benchmark — useful as a
proxy for what people actually use. Snapshot weekly.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable

import httpx

from benchmarks._base import Snapshot

log = logging.getLogger(__name__)

ENDPOINT = "https://openrouter.ai/api/v1/models"
NAME = "openrouter"


def scrape() -> Iterable[Snapshot]:
    """Fetch /api/v1/models and emit one snapshot per model.

    OpenRouter response includes per-model pricing + context length + a usage
    proxy. We record context_length as the score (most universally comparable
    across models) and stash full pricing/metadata.
    """
    snapshot_at = datetime.now(timezone.utc)
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(ENDPOINT, headers={
                "User-Agent": "deep-ai-research/0.1 (deep-ai-research; personal use)"
            })
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        log.error("openrouter fetch failed: %s", e)
        return

    models = data.get("data") or []
    for m in models:
        model_id = m.get("id")
        if not model_id:
            continue
        ctx = m.get("context_length")
        if ctx is None:
            continue
        try:
            score = float(ctx)
        except (TypeError, ValueError):
            continue
        yield Snapshot(
            benchmark_name=NAME,
            model=model_id,
            score=score,
            metric_type="context_length",
            snapshot_at=snapshot_at,
            metadata={
                "name": m.get("name"),
                "description": m.get("description"),
                "pricing": m.get("pricing"),
                "top_provider": m.get("top_provider"),
                "architecture": m.get("architecture"),
            },
        )

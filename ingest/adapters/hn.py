"""Hacker News adapter via the Algolia HN Search API (free, no auth).

Fetches AI/ML-keyword-filtered stories. Persists titles + top-comment summary
(not full comment trees — too much noise).

API docs: https://hn.algolia.com/api
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Iterable

import httpx

from ingest.adapters._base import RawSource

log = logging.getLogger(__name__)

ALGOLIA_BASE = "https://hn.algolia.com/api/v1"

# Keywords that mark an AI/ML story. Substantial enough to filter signal,
# loose enough to not miss new terminology.
AI_KEYWORDS = [
    "LLM", "transformer", "Claude", "GPT", "Gemini", "Sonnet", "Opus", "Haiku",
    "DeepSeek", "Anthropic", "OpenAI", "Mistral", "Llama", "Qwen", "Kimi",
    "embedding", "vector", "RAG", "agent", "MCP", "fine-tun", "PPO", "DPO",
    "attention", "diffusion", "multimodal", "inference", "tokeniz",
    "CUDA", "Triton", "VLLM", "pytorch", "JAX", "TensorRT",
]


@dataclass
class HNAdapter:
    name: str = "hn_ai"
    publication: str = "Hacker News (AI filter)"
    feed_url: str = ""  # unused; we hit the API directly
    source_type: str = "hn_post"
    poll_interval_seconds: int = 14400
    rate_limit_key: str = "hn-algolia"
    user_agent: str = "dair/0.1 (deep-ai-research; personal use)"
    timeout_seconds: float = 20.0
    hits_per_page: int = 50
    max_pages: int = 4

    def iter_new(self, since: datetime | None = None) -> Iterable[RawSource]:
        with httpx.Client(timeout=self.timeout_seconds, headers={"User-Agent": self.user_agent}) as client:
            for kw in AI_KEYWORDS:
                yield from self._search(client, kw, since)

    def _search(self, client: httpx.Client, keyword: str,
                since: datetime | None) -> Iterable[RawSource]:
        params = {
            "query": keyword,
            "tags": "story",
            "hitsPerPage": self.hits_per_page,
        }
        if since is not None:
            params["numericFilters"] = f"created_at_i>{int(since.timestamp())}"

        for page in range(self.max_pages):
            params["page"] = page
            try:
                resp = client.get(f"{ALGOLIA_BASE}/search_by_date", params=params)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                log.warning("HN search failed for %r page %d: %s", keyword, page, e)
                break
            data = resp.json()
            hits = data.get("hits") or []
            if not hits:
                break
            for hit in hits:
                raw = self._parse_hit(hit)
                if raw is not None:
                    yield raw
            if len(hits) < self.hits_per_page:
                break

    @staticmethod
    def _parse_hit(hit: dict) -> RawSource | None:
        # Prefer the externally-linked URL; fall back to the HN item URL.
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        title = hit.get("title") or ""
        if not title:
            return None
        author = hit.get("author") or ""
        created_at = hit.get("created_at")
        if not created_at:
            return None
        try:
            d = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
        except ValueError:
            return None
        # We don't fetch comments — just title + points + URL hint.
        body = (
            f"# {title}\n\n"
            f"By {author} on Hacker News. "
            f"Points: {hit.get('points', 0)}. "
            f"Comments: {hit.get('num_comments', 0)}.\n\n"
            f"Original link: {hit.get('url') or 'self post'}\n\n"
            f"HN: https://news.ycombinator.com/item?id={hit.get('objectID')}\n"
        )
        return RawSource(
            url=url,
            title=title,
            publication="Hacker News (AI filter)",
            source_type="hn_post",
            date=d,
            authors=[author] if author else [],
            body=body,
            content_format="markdown",
            tags=["hn"],
        )


def build() -> HNAdapter:
    return HNAdapter()

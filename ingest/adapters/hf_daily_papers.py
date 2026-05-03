"""HuggingFace Daily Papers adapter.

Hits HF's native API (https://huggingface.co/api/daily_papers) which returns
JSON. Authenticated via HF_TOKEN in .env (free; bumps rate limits to 100K
monthly Inference credits — way more than we need).

The HF Daily Papers list is curated by HF staff: ~5-10 papers per day,
selected as notable. The curation IS the value — we persist title +
abstract + authors + arXiv id + HF discussion URL.

For backfill: pass `--since=YYYY-MM-DD` to ingest.run; the adapter walks
day-by-day from `since` to today.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

import httpx

from ingest.adapters._base import RawSource

log = logging.getLogger(__name__)

API_ENDPOINT = "https://huggingface.co/api/daily_papers"


@dataclass
class HFDailyPapersAdapter:
    name: str = "hf_daily_papers"
    publication: str = "HuggingFace Daily Papers"
    source_type: str = "hf_daily_papers"
    poll_interval_seconds: int = 14400
    rate_limit_key: str = "huggingface.co"
    backfill_days: int = 7  # walk back N days when no `since` given
    user_agent: str = "deep-ai-research/0.1 (deep-ai-research; personal use)"
    timeout_seconds: float = 20.0

    def iter_new(self, since: datetime | None = None) -> Iterable[RawSource]:
        token = os.environ.get("HF_TOKEN", "").strip()
        headers = {"User-Agent": self.user_agent}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        today = datetime.now(timezone.utc).date()
        if since is not None:
            start = since.date() if isinstance(since, datetime) else since
        else:
            start = today - timedelta(days=self.backfill_days)

        with httpx.Client(headers=headers, timeout=self.timeout_seconds) as client:
            cur = start
            while cur <= today:
                yield from self._fetch_day(client, cur)
                cur += timedelta(days=1)

    def _fetch_day(self, client: httpx.Client, day: date) -> Iterable[RawSource]:
        try:
            resp = client.get(API_ENDPOINT, params={"date": day.isoformat()})
            resp.raise_for_status()
        except httpx.HTTPError as e:
            log.warning("hf daily-papers fetch for %s failed: %s", day.isoformat(), e)
            return
        data = resp.json()
        if not isinstance(data, list):
            return
        for entry in data:
            raw = self._render(entry, fallback_day=day)
            if raw is not None:
                yield raw

    @staticmethod
    def _render(entry: dict, *, fallback_day: date) -> RawSource | None:
        paper = entry.get("paper") if isinstance(entry, dict) else None
        if not isinstance(paper, dict):
            return None

        arxiv_id = paper.get("id")
        if not arxiv_id:
            return None

        title = (paper.get("title") or "").strip()
        if not title:
            return None
        abstract = (paper.get("summary") or "").strip()
        authors = []
        for a in paper.get("authors", []) or []:
            if isinstance(a, dict) and a.get("name"):
                authors.append(a["name"])

        # HF discussion URL is the canonical landing page
        url = f"https://huggingface.co/papers/{arxiv_id}"

        # Date: prefer the curated `publishedAt` from HF, else the query day.
        published_at = paper.get("publishedAt") or entry.get("publishedAt")
        if published_at:
            try:
                d = datetime.fromisoformat(str(published_at).replace("Z", "+00:00")).date()
            except (ValueError, TypeError):
                d = fallback_day
        else:
            d = fallback_day

        upvotes = entry.get("numVotes") or 0
        n_comments = entry.get("numComments") or 0

        body_parts = [
            f"# {title}",
            "",
            f"**HF Daily Papers** · {len(authors)} authors · "
            f"{upvotes} upvotes · {n_comments} comments · arXiv {arxiv_id}",
            "",
            f"Authors: {', '.join(authors) if authors else '(none listed)'}",
            "",
            f"arXiv: https://arxiv.org/abs/{arxiv_id}",
            f"HF discussion: {url}",
            "",
            "## Abstract",
            "",
            abstract or "(no abstract available)",
        ]

        return RawSource(
            url=url,
            title=title,
            publication="HuggingFace Daily Papers",
            source_type="hf_daily_papers",
            date=d,
            authors=authors,
            body="\n".join(body_parts),
            content_format="markdown",
            tags=["hf-daily-papers", "arxiv"],
            mentioned_entities=[arxiv_id],
        )


def build() -> HFDailyPapersAdapter:
    return HFDailyPapersAdapter()

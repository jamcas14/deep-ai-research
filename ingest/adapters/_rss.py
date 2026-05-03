"""Generic RSS / Atom feed adapter. Most newsletters and lab blogs subclass this."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Iterable

import feedparser
import httpx
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from ingest.adapters._base import RawSource

log = logging.getLogger(__name__)


@dataclass
class RSSAdapter:
    """Subclass / instantiate this for RSS-based sources.

    Fields set per-instance:
        name              — adapter id (matches sources.yaml entry)
        publication       — display name
        feed_url          — RSS / Atom feed URL
        source_type       — `newsletter`, `lab_blog`, etc.
        poll_interval_seconds
        rate_limit_key    — for shared rate-limit broker
    """

    name: str
    publication: str
    feed_url: str
    source_type: str
    poll_interval_seconds: int = 3600
    rate_limit_key: str = "default"
    user_agent: str = "deep-ai-research/0.1 (deep-ai-research; personal use)"
    timeout_seconds: float = 20.0

    def iter_new(self, since: datetime | None = None) -> Iterable[RawSource]:
        log.info("fetching %s from %s", self.name, self.feed_url)

        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                resp = client.get(self.feed_url, headers={"User-Agent": self.user_agent})
                resp.raise_for_status()
                feed = feedparser.parse(resp.content)
        except (httpx.HTTPError, Exception) as e:
            log.error("failed to fetch %s: %s", self.feed_url, e)
            return

        if feed.bozo and not feed.entries:
            log.error("malformed feed %s: %s", self.feed_url, feed.bozo_exception)
            return

        for entry in feed.entries:
            try:
                raw = self._parse_entry(entry)
            except Exception as e:  # noqa: BLE001 — adapter resilience
                log.warning("skipping malformed entry from %s: %s", self.name, e)
                continue
            if raw is None:
                continue
            if since is not None and datetime.combine(raw.date, datetime.min.time(), timezone.utc) < since:
                continue
            yield raw

    def _parse_entry(self, entry: dict) -> RawSource | None:
        url = entry.get("link") or entry.get("id")
        if not url:
            return None

        title = entry.get("title", "").strip() or "(untitled)"

        # Date — try multiple fields. Fall back to today only if nothing else.
        d = self._extract_date(entry)
        if d is None:
            log.warning("no date for %s — skipping", url)
            return None

        authors = self._extract_authors(entry)
        body, fmt = self._extract_body(entry)
        tags = [t.term for t in entry.get("tags", []) if hasattr(t, "term")]

        return RawSource(
            url=url,
            title=title,
            publication=self.publication,
            source_type=self.source_type,
            date=d,
            authors=authors,
            body=body,
            content_format=fmt,
            tags=tags,
        )

    @staticmethod
    def _extract_date(entry: dict) -> date | None:
        for key in ("published", "updated", "created"):
            value = entry.get(key)
            if value:
                try:
                    return dateparser.parse(value).date()
                except (ValueError, TypeError):
                    continue
        # feedparser sometimes parses to a struct_time
        for key in ("published_parsed", "updated_parsed"):
            t = entry.get(key)
            if t:
                return date(t.tm_year, t.tm_mon, t.tm_mday)
        return None

    @staticmethod
    def _extract_authors(entry: dict) -> list[str]:
        authors: list[str] = []
        for a in entry.get("authors", []) or []:
            if isinstance(a, dict) and a.get("name"):
                authors.append(a["name"])
            elif isinstance(a, str) and a:
                authors.append(a)
        if not authors and entry.get("author"):
            authors.append(entry["author"])
        return authors

    @staticmethod
    def _extract_body(entry: dict) -> tuple[str, str]:
        # Prefer content[].value over summary; some feeds put full text in content.
        content_list = entry.get("content")
        if content_list:
            html = content_list[0].get("value", "") if isinstance(content_list, list) else ""
        else:
            html = entry.get("summary", "")

        if not html:
            return "", "plain"

        # Convert HTML to readable markdown-ish plain text.
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator="\n\n", strip=True)
        return text, "plain"

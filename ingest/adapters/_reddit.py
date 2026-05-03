"""Reddit adapter (PRAW). One adapter instance per subreddit.

Routed by `source_type: reddit_post` in `config/sources.yaml`. Runs only when
`REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` are present in
`.env`. No-op gracefully otherwise — first-run UX matters.

Persists titles + selftext + URL + score + a top-comment-summary (top-3
top-level comments concatenated). Not the full thread — too noisy.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Iterable

from ingest.adapters._base import RawSource

log = logging.getLogger(__name__)


@dataclass
class RedditAdapter:
    name: str
    publication: str
    subreddit: str
    source_type: str = "reddit_post"
    poll_interval_seconds: int = 14400
    rate_limit_key: str = "reddit"
    posts_limit: int = 100
    top_comments: int = 3

    def iter_new(self, since: datetime | None = None) -> Iterable[RawSource]:
        try:
            import praw  # noqa: F401
        except ImportError:
            log.error("praw not installed; run `uv sync` (it's in main deps)")
            return

        client_id = os.environ.get("REDDIT_CLIENT_ID", "").strip()
        client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "").strip()
        user_agent = os.environ.get("REDDIT_USER_AGENT", "").strip()

        if not (client_id and client_secret and user_agent):
            log.warning(
                "Reddit credentials missing; skipping r/%s. "
                "Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT in .env.",
                self.subreddit,
            )
            return

        import praw
        try:
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                check_for_async=False,
            )
            reddit.read_only = True
        except Exception as e:  # noqa: BLE001
            log.error("praw init failed: %s", e)
            return

        try:
            subreddit = reddit.subreddit(self.subreddit)
            for submission in subreddit.new(limit=self.posts_limit):
                created = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
                if since is not None and created < since:
                    continue
                raw = self._render(submission, created.date())
                if raw is not None:
                    yield raw
        except Exception as e:  # noqa: BLE001
            log.error("reddit fetch failed for r/%s: %s", self.subreddit, e)

    def _render(self, submission, post_date: date) -> RawSource | None:
        try:
            title = (submission.title or "").strip()
            if not title:
                return None
            url = f"https://reddit.com{submission.permalink}"
            external_url = submission.url
            author = str(submission.author) if submission.author else "[deleted]"
            score = submission.score
            num_comments = submission.num_comments
            selftext = (submission.selftext or "").strip()

            top_comment_blob = self._collect_top_comments(submission)

            body = (
                f"# {title}\n\n"
                f"r/{self.subreddit} · u/{author} · {score} pts · "
                f"{num_comments} comments · {post_date.isoformat()}\n\n"
                f"Reddit thread: {url}\n"
            )
            if external_url and external_url != url:
                body += f"External link: {external_url}\n"
            if selftext:
                body += f"\n## Self text\n\n{selftext}\n"
            if top_comment_blob:
                body += f"\n## Top discussion (top {self.top_comments} top-level comments)\n\n{top_comment_blob}\n"

            return RawSource(
                url=url,
                title=title,
                publication=self.publication,
                source_type=self.source_type,
                date=post_date,
                authors=[author] if author and author != "[deleted]" else [],
                body=body,
                content_format="markdown",
                tags=[f"r/{self.subreddit}"],
                mentioned_authorities=[author] if author and author != "[deleted]" else [],
            )
        except Exception as e:  # noqa: BLE001
            log.warning("failed to render reddit submission: %s", e)
            return None

    def _collect_top_comments(self, submission) -> str:
        try:
            submission.comments.replace_more(limit=0)  # don't recurse into "more comments"
            top = sorted(submission.comments[:30], key=lambda c: getattr(c, "score", 0), reverse=True)
            out_lines: list[str] = []
            for c in top[: self.top_comments]:
                if not hasattr(c, "body") or not c.body:
                    continue
                author = str(c.author) if c.author else "[deleted]"
                score = getattr(c, "score", 0)
                body = c.body.strip().replace("\n\n\n", "\n\n")
                if len(body) > 1500:
                    body = body[:1500] + "..."
                out_lines.append(f"### u/{author} ({score} pts)\n\n{body}\n")
            return "\n".join(out_lines)
        except Exception as e:  # noqa: BLE001
            log.debug("comment fetch skipped for %s: %s", self.subreddit, e)
            return ""

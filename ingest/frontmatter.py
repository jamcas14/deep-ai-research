"""Frontmatter schema. Pydantic catches malformed frontmatter at ingestion."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import frontmatter as fm  # python-frontmatter
from pydantic import BaseModel, ConfigDict, Field


class EngagementTag(BaseModel):
    """Inline engagement record in frontmatter (for engagement-at-ingestion-time)."""

    authority_id: str
    kind: str  # author | mentioned_with_link | guest | host | etc.


class Frontmatter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_type: str  # newsletter | lab_blog | reddit_post | hn_post | podcast_episode | ...
    publication: str
    url: str
    canonical_url: str
    date: date
    authors: list[str] = Field(default_factory=list)

    # Authority engagement
    authorities_engaged: list[EngagementTag] = Field(default_factory=list)
    mentioned_entities: list[str] = Field(default_factory=list)
    mentioned_authorities: list[str] = Field(default_factory=list)

    tags: list[str] = Field(default_factory=list)
    ingested_at: datetime
    content_hash: str
    revision: int = 1
    parent_id: str | None = None

    chunker_version: str = "v1"
    embed_model: str = "snowflake-arctic-embed-s"
    embed_dim: int = 384


def write_post(path: Path, fm_obj: Frontmatter, body: str) -> None:
    """Write a markdown file with validated frontmatter + body."""
    path.parent.mkdir(parents=True, exist_ok=True)
    post = fm.Post(
        body,
        **fm_obj.model_dump(mode="json", exclude_none=True),
    )
    path.write_text(fm.dumps(post), encoding="utf-8")


def read_post(path: Path) -> tuple[Frontmatter, str]:
    """Read a markdown file, validate frontmatter, return (fm, body)."""
    post = fm.load(path)
    return Frontmatter(**post.metadata), post.content

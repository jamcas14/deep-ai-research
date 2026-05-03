"""Tests for frontmatter schema + read/write round-trip."""

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from ingest.frontmatter import EngagementTag, Frontmatter, read_post, write_post


def _sample_fm() -> Frontmatter:
    return Frontmatter(
        source_id="abc1234567890def",
        source_type="newsletter",
        publication="Test Newsletter",
        url="https://example.com/post",
        canonical_url="https://example.com/post",
        date=date(2026, 5, 3),
        authors=["Test Author"],
        authorities_engaged=[EngagementTag(authority_id="karpathy", kind="author")],
        mentioned_entities=["DeepSeek V4"],
        mentioned_authorities=["karpathy"],
        tags=["release"],
        ingested_at=datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc),
        content_hash="sha256:abc",
    )


def test_round_trip(tmp_path: Path) -> None:
    fm = _sample_fm()
    body = "## Hello\n\nThis is the body."
    out = tmp_path / "test.md"
    write_post(out, fm, body)

    fm_read, body_read = read_post(out)
    assert fm_read.source_id == fm.source_id
    assert fm_read.publication == fm.publication
    assert fm_read.date == fm.date
    assert fm_read.tags == fm.tags
    assert fm_read.authorities_engaged[0].authority_id == "karpathy"
    assert body_read.strip() == body.strip()


def test_extra_fields_rejected() -> None:
    """Schema should reject unknown fields (model_config = forbid)."""
    with pytest.raises(Exception):
        Frontmatter(
            source_id="x",
            source_type="newsletter",
            publication="t",
            url="https://e.com",
            canonical_url="https://e.com",
            date=date(2026, 5, 3),
            ingested_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
            content_hash="sha256:x",
            unknown_field="should fail",  # type: ignore[call-arg]
        )


def test_creates_parent_dir(tmp_path: Path) -> None:
    fm = _sample_fm()
    out = tmp_path / "deep" / "nested" / "path" / "test.md"
    write_post(out, fm, "body")
    assert out.exists()

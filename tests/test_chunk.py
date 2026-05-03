"""Tests for the versioned chunker."""

import pytest

from ingest.chunk import CHUNKER_VERSION, chunk_text


def test_empty_returns_empty_list() -> None:
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_short_text_one_chunk() -> None:
    chunks = chunk_text("Hello world.")
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert "Hello world" in chunks[0].text


def test_paragraph_split() -> None:
    text = "\n\n".join([f"Paragraph {i} " * 100 for i in range(5)])
    chunks = chunk_text(text)
    assert len(chunks) >= 2
    # Indexes start at 0 and increment.
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_long_paragraph_split_on_sentences() -> None:
    para = ". ".join(f"Sentence {i}" for i in range(500)) + "."
    chunks = chunk_text(para)
    assert len(chunks) >= 2


def test_version_mismatch_raises() -> None:
    with pytest.raises(ValueError, match="version mismatch"):
        chunk_text("hello", version="v999")


def test_current_version_is_v1() -> None:
    assert CHUNKER_VERSION == "v1"


def test_deterministic() -> None:
    """Same input → same chunk count + identical text."""
    text = "\n\n".join([f"Para {i} " * 50 for i in range(10)])
    a = chunk_text(text)
    b = chunk_text(text)
    assert len(a) == len(b)
    assert all(x.text == y.text for x, y in zip(a, b))

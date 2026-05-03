"""Versioned chunker. Pin chunker version alongside embed model — changing
the chunker breaks reproducibility even with the same model.

v1: paragraph-aware chunking with target ~512-token chunks (rough approx via
char count; precise tokenization not necessary at this scale).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

CHUNKER_VERSION = "v1"

# Rough target: ~512 tokens ≈ ~2000 characters for English.
_TARGET_CHARS = 2000
_MIN_CHARS = 600
_MAX_CHARS = 3500


@dataclass
class Chunk:
    index: int
    text: str


def chunk_text(text: str, *, version: str = CHUNKER_VERSION) -> list[Chunk]:
    """Split text into chunks. version must be CHUNKER_VERSION (no fallback)."""
    if version != CHUNKER_VERSION:
        raise ValueError(f"chunker version mismatch: {version} vs current {CHUNKER_VERSION}")

    text = text.strip()
    if not text:
        return []

    # Split on blank lines (paragraph boundaries) first.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return [Chunk(index=0, text=text[:_MAX_CHARS])]

    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0

    for p in paragraphs:
        plen = len(p)

        # If a single paragraph is huge, split it on sentence boundaries.
        if plen > _MAX_CHARS:
            if cur:
                chunks.append("\n\n".join(cur))
                cur, cur_len = [], 0
            for piece in _split_long_paragraph(p):
                chunks.append(piece)
            continue

        if cur_len + plen > _TARGET_CHARS and cur_len >= _MIN_CHARS:
            chunks.append("\n\n".join(cur))
            cur, cur_len = [p], plen
        else:
            cur.append(p)
            cur_len += plen + 2  # for the joining separator

    if cur:
        chunks.append("\n\n".join(cur))

    return [Chunk(index=i, text=t) for i, t in enumerate(chunks)]


def _split_long_paragraph(p: str) -> list[str]:
    """Split a single huge paragraph on sentence boundaries up to ~_MAX_CHARS."""
    sentences = re.split(r"(?<=[.!?])\s+", p)
    out: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for s in sentences:
        slen = len(s)
        if cur_len + slen > _MAX_CHARS and cur:
            out.append(" ".join(cur))
            cur, cur_len = [s], slen
        else:
            cur.append(s)
            cur_len += slen + 1
    if cur:
        out.append(" ".join(cur))
    return out

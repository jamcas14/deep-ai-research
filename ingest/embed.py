"""Embedding interface. Default: snowflake-arctic-embed-s (33M, 384-dim, Apache-2.0).

Lazy import sentence-transformers — it pulls in PyTorch, so we only do it
when actually generating embeddings. Install with:

    uv sync --extra embed

Then run:

    uv run python -m ingest.embed_pending

to embed any chunks that don't yet have vectors.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Iterable, Iterator

from ingest._index import EMBED_DIM, connect, get_pinned, init_schema
from ingest.chunk import CHUNKER_VERSION, chunk_text
from ingest.frontmatter import read_post

log = logging.getLogger(__name__)

EMBED_MODEL_NAME = "Snowflake/snowflake-arctic-embed-s"


def _chunk_id(source_id: str, chunk_index: int) -> str:
    return hashlib.sha256(f"{source_id}:{chunk_index}".encode()).hexdigest()[:16]


def _load_model():  # type: ignore[no-untyped-def]
    """Lazy import. Raises with actionable message if dep not installed."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise ImportError(
            "sentence-transformers not installed. Run: uv sync --extra embed"
        ) from e
    log.info("loading %s (CPU)", EMBED_MODEL_NAME)
    return SentenceTransformer(EMBED_MODEL_NAME, device="cpu")


def iter_unembedded_sources(conn, corpus_dir: Path) -> Iterator[Path]:  # type: ignore[no-untyped-def]
    """Yield markdown files whose chunks aren't all in the embeddings table yet."""
    seen = {row["source_id"] for row in conn.execute(
        "SELECT DISTINCT c.source_id FROM chunks c "
        "JOIN embeddings e ON e.chunk_id = c.chunk_id"
    )}
    for path in corpus_dir.rglob("*.md"):
        try:
            fm, _ = read_post(path)
        except Exception:  # noqa: BLE001
            continue
        if fm.source_id not in seen:
            yield path


def embed_pending(corpus_dir: Path, sqlite_path: Path, *, batch_size: int = 32) -> int:
    """Embed every source that doesn't have embeddings yet. Returns count embedded."""
    conn = connect(sqlite_path)
    init_schema(conn)

    # Verify version pins match.
    pinned_chunker = get_pinned(conn, "chunker")
    pinned_model = get_pinned(conn, "embed_model")
    assert pinned_chunker == CHUNKER_VERSION, f"chunker pin mismatch: {pinned_chunker}"
    assert pinned_model == EMBED_MODEL_NAME.split("/")[-1] or pinned_model == EMBED_MODEL_NAME, \
        f"embed_model pin mismatch: {pinned_model}"

    pending = list(iter_unembedded_sources(conn, corpus_dir))
    if not pending:
        log.info("no pending sources to embed")
        return 0

    model = _load_model()
    log.info("embedding %d sources", len(pending))

    embedded = 0
    for path in pending:
        try:
            fm, body = read_post(path)
        except Exception as e:  # noqa: BLE001
            log.warning("skipping unreadable %s: %s", path, e)
            continue

        chunks = chunk_text(body, version=CHUNKER_VERSION)
        if not chunks:
            continue

        # Insert chunks into chunks table first.
        for c in chunks:
            cid = _chunk_id(fm.source_id, c.index)
            conn.execute(
                "INSERT OR REPLACE INTO chunks(chunk_id, source_id, chunk_index, text) "
                "VALUES (?, ?, ?, ?)",
                (cid, fm.source_id, c.index, c.text),
            )

        # Encode and store vectors.
        texts = [c.text for c in chunks]
        embeddings = model.encode(
            texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False
        )
        for c, emb in zip(chunks, embeddings):
            cid = _chunk_id(fm.source_id, c.index)
            # vec0 expects bytes; use tobytes() on a float32 numpy array.
            emb_bytes = emb.astype("float32").tobytes()
            conn.execute(
                "DELETE FROM embeddings WHERE chunk_id = ?", (cid,),
            )
            conn.execute(
                "INSERT INTO embeddings(chunk_id, embedding) VALUES (?, ?)",
                (cid, emb_bytes),
            )

        conn.commit()
        embedded += 1
        if embedded % 25 == 0:
            log.info("embedded %d/%d", embedded, len(pending))

    log.info("done: embedded %d sources", embedded)
    conn.close()
    return embedded

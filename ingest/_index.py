"""sqlite sidecar — schema init + connection helper.

Holds engagement edges, embedding vectors (via sqlite-vec), version pins, and
adapter health. The corpus markdown is the primary store; this DB is derived.
Always recreatable from the markdown by re-running ingestion + polling.
"""

from __future__ import annotations

import logging
from pathlib import Path

# Use pysqlite3 (modern bundled SQLite) so sqlite-vec ABI matches.
import pysqlite3 as sqlite3
import sqlite_vec

log = logging.getLogger(__name__)

EMBED_DIM = 384  # snowflake-arctic-embed-s


SCHEMA = """
CREATE TABLE IF NOT EXISTS engagements (
    id INTEGER PRIMARY KEY,
    authority_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    UNIQUE(authority_id, source_id, kind)
);
CREATE INDEX IF NOT EXISTS idx_engagements_source ON engagements(source_id);
CREATE INDEX IF NOT EXISTS idx_engagements_authority ON engagements(authority_id, recorded_at DESC);

CREATE TABLE IF NOT EXISTS pin_versions (
    name TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    pinned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS adapter_health (
    adapter_name TEXT PRIMARY KEY,
    last_success_at TIMESTAMP,
    last_error_at TIMESTAMP,
    last_error_message TEXT,
    consecutive_failures INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS run_costs (
    run_id TEXT PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    finished_at TIMESTAMP,
    finish_reason TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    UNIQUE(source_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id);
"""

# FTS5 keyword index over chunks. External-content style: stores only what's
# needed to rank; chunks table is the source of truth for text.
FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text,
    chunk_id UNINDEXED,
    source_id UNINDEXED,
    tokenize = 'porter unicode61'
);
"""

# vec0 virtual table — created separately because it requires the extension loaded.
EMBEDDINGS_DDL = f"""
CREATE VIRTUAL TABLE IF NOT EXISTS embeddings USING vec0(
    chunk_id TEXT PRIMARY KEY,
    embedding float[{EMBED_DIM}]
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    """Open the index DB with sqlite-vec loaded. Caller manages lifecycle."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def init_schema(conn: sqlite3.Connection, *, chunker_version: str = "v1",
                embed_model: str = "snowflake-arctic-embed-s") -> None:
    """Create tables. Idempotent — safe to call on every run."""
    conn.executescript(SCHEMA)
    conn.execute(EMBEDDINGS_DDL)
    conn.execute(FTS_DDL)
    # Pin chunker + embed model versions; only insert if missing.
    conn.execute(
        "INSERT OR IGNORE INTO pin_versions(name, value) VALUES (?, ?)",
        ("chunker", chunker_version),
    )
    conn.execute(
        "INSERT OR IGNORE INTO pin_versions(name, value) VALUES (?, ?)",
        ("embed_model", embed_model),
    )
    conn.commit()


def get_pinned(conn: sqlite3.Connection, name: str) -> str | None:
    row = conn.execute("SELECT value FROM pin_versions WHERE name = ?", (name,)).fetchone()
    return row["value"] if row else None


def backfill_fts(conn: sqlite3.Connection) -> int:
    """Rebuild chunks_fts from current chunks. Idempotent."""
    conn.execute("DELETE FROM chunks_fts")
    cur = conn.execute(
        "INSERT INTO chunks_fts(text, chunk_id, source_id) "
        "SELECT text, chunk_id, source_id FROM chunks"
    )
    conn.commit()
    return cur.rowcount or 0


def insert_chunk_into_fts(conn: sqlite3.Connection, chunk_id: str, source_id: str, text: str) -> None:
    """Called from embed.py when a new chunk is created."""
    # Delete first to keep one row per chunk_id (FTS5 doesn't have UNIQUE).
    conn.execute("DELETE FROM chunks_fts WHERE chunk_id = ?", (chunk_id,))
    conn.execute(
        "INSERT INTO chunks_fts(text, chunk_id, source_id) VALUES (?, ?, ?)",
        (text, chunk_id, source_id),
    )

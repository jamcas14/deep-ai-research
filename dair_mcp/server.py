"""corpus-server — the MCP exposed to Claude Code subagents.

Run via `python -m dair_mcp.server` (configured in .mcp.json).

Implements the four tools defined in PLAN.md. Hybrid retrieval combines
FTS5 (keyword) + sqlite-vec (semantic) via RRF k=60, then applies
authority boost + per-content-type recency decay.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from ingest._index import EMBED_DIM, connect, init_schema
from ingest.frontmatter import read_post

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Lazy globals — initialized on first call so server starts fast.
_state: dict[str, Any] = {
    "conn": None,
    "model": None,
    "paths": None,
    "decay": None,
    "authorities": None,
    "kind_weights": {
        "author": 1.0,
        "commit_author": 1.0,
        "pr_author": 0.8,
        "review": 0.6,
        "star": 0.5,
        "fork": 0.4,
        "issue_open": 0.3,
        "post_author": 1.0,
        "comment_author_top_level": 0.4,
        "guest": 1.0,
        "host": 0.7,
        "mentioned_with_link": 0.5,
        "cited_by_tracked": 0.6,
        "retweet": 0.8,
        "quote": 0.7,
        "reply": 0.4,
    },
}

log = logging.getLogger("dair_mcp.server")
RRF_K = 60
DEFAULT_TOP_N = 20
CANDIDATE_K = 100
AUTHORITY_BOOST_CAP = 4.0


# ---------- bootstrapping ----------

def _load_paths() -> dict[str, str]:
    return yaml.safe_load((PROJECT_ROOT / "config" / "paths.yaml").read_text())


def _load_decay() -> dict[str, Any]:
    return yaml.safe_load((PROJECT_ROOT / "config" / "decay.yaml").read_text())


def _load_authorities() -> dict[str, dict[str, Any]]:
    """authority_id (slug) → entry. Used for weight lookups in scoring."""
    raw = yaml.safe_load((PROJECT_ROOT / "config" / "authorities.yaml").read_text())
    out: dict[str, dict[str, Any]] = {}
    for entry in raw.get("authorities", []) or []:
        name = entry.get("name", "")
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        out[slug] = entry
    return out


def _ensure_state() -> None:
    if _state["conn"] is None:
        paths = _load_paths()
        sqlite_path = (PROJECT_ROOT / paths["sqlite_path"]).resolve()
        conn = connect(sqlite_path)
        init_schema(conn)
        _state["conn"] = conn
        _state["paths"] = paths
        _state["decay"] = _load_decay()
        _state["authorities"] = _load_authorities()


def _ensure_model() -> None:
    if _state["model"] is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            log.warning("sentence-transformers not installed; vector search disabled")
            _state["model"] = False  # sentinel: tried, failed
            return
        log.info("loading embedding model (CPU)")
        _state["model"] = SentenceTransformer("Snowflake/snowflake-arctic-embed-s", device="cpu")


# ---------- hit assembly ----------

@dataclass
class Hit:
    source_id: str
    chunk_id: str | None
    text: str
    score: float
    rrf_score: float
    authority_boost: float
    recency_decay: float
    frontmatter: dict[str, Any] = field(default_factory=dict)
    path: str | None = None
    snippet: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "chunk_id": self.chunk_id,
            "score": round(self.score, 4),
            "components": {
                "rrf": round(self.rrf_score, 4),
                "authority_boost": round(self.authority_boost, 3),
                "recency_decay": round(self.recency_decay, 3),
            },
            "publication": self.frontmatter.get("publication"),
            "title_or_url": self.frontmatter.get("url"),
            "date": str(self.frontmatter.get("date") or ""),
            "path": self.path,
            "snippet": self.snippet,
            "tags": self.frontmatter.get("tags", []),
            "mentioned_authorities": self.frontmatter.get("mentioned_authorities", []),
        }


# ---------- ranking pieces ----------

def _bm25_candidates(query: str, k: int = CANDIDATE_K) -> list[tuple[str, str, str, int]]:
    """Returns [(chunk_id, source_id, text, rank)] for FTS5 BM25 top-k."""
    conn = _state["conn"]
    safe = _sanitize_fts_query(query)
    if not safe:
        return []
    rows = conn.execute(
        "SELECT chunk_id, source_id, text FROM chunks_fts "
        "WHERE chunks_fts MATCH ? "
        "ORDER BY bm25(chunks_fts) "
        "LIMIT ?",
        (safe, k),
    ).fetchall()
    return [(r["chunk_id"], r["source_id"], r["text"], i + 1) for i, r in enumerate(rows)]


def _sanitize_fts_query(q: str) -> str:
    """FTS5 has special chars; quote each term to avoid syntax errors."""
    terms = re.findall(r"[A-Za-z0-9_]+", q)
    if not terms:
        return ""
    return " OR ".join(f'"{t}"' for t in terms)


def _vector_candidates(query: str, k: int = CANDIDATE_K) -> list[tuple[str, str, int]]:
    """Returns [(chunk_id, source_id, rank)] for top-k vector similarity."""
    _ensure_model()
    model = _state["model"]
    if not model:
        return []
    conn = _state["conn"]
    emb = model.encode(query, normalize_embeddings=True).astype("float32")
    rows = conn.execute(
        "SELECT e.chunk_id AS chunk_id, c.source_id AS source_id, distance "
        "FROM embeddings e JOIN chunks c ON c.chunk_id = e.chunk_id "
        "WHERE e.embedding MATCH ? AND k = ? "
        "ORDER BY distance",
        (emb.tobytes(), k),
    ).fetchall()
    return [(r["chunk_id"], r["source_id"], i + 1) for i, r in enumerate(rows)]


def _rrf_combine(bm25_hits, vec_hits) -> dict[str, dict[str, Any]]:
    """Reciprocal Rank Fusion. Returns chunk_id → {rrf, source_id, text, snippet}."""
    by_chunk: dict[str, dict[str, Any]] = {}
    for chunk_id, source_id, text, rank in bm25_hits:
        d = by_chunk.setdefault(chunk_id, {"source_id": source_id, "text": text, "rrf": 0.0})
        d["rrf"] += 1.0 / (RRF_K + rank)
    for chunk_id, source_id, rank in vec_hits:
        d = by_chunk.setdefault(chunk_id, {"source_id": source_id, "text": "", "rrf": 0.0})
        d["rrf"] += 1.0 / (RRF_K + rank)
    # Backfill missing text from chunks table (vector-only hits)
    missing = [cid for cid, d in by_chunk.items() if not d["text"]]
    if missing:
        conn = _state["conn"]
        placeholders = ",".join("?" for _ in missing)
        rows = conn.execute(
            f"SELECT chunk_id, text FROM chunks WHERE chunk_id IN ({placeholders})",
            missing,
        ).fetchall()
        for r in rows:
            by_chunk[r["chunk_id"]]["text"] = r["text"]
    return by_chunk


def _engagements_for(source_ids: list[str]) -> dict[str, list[tuple[str, str]]]:
    """source_id → [(authority_id, kind), ...]."""
    if not source_ids:
        return {}
    conn = _state["conn"]
    placeholders = ",".join("?" for _ in source_ids)
    rows = conn.execute(
        f"SELECT source_id, authority_id, kind FROM engagements "
        f"WHERE source_id IN ({placeholders})",
        source_ids,
    ).fetchall()
    out: dict[str, list[tuple[str, str]]] = {}
    for r in rows:
        out.setdefault(r["source_id"], []).append((r["authority_id"], r["kind"]))
    return out


def _authority_boost(engagements: list[tuple[str, str]]) -> float:
    """min(cap, 1 + Σ weight(a) * kind_weight(kind))."""
    if not engagements:
        return 1.0
    auths = _state["authorities"] or {}
    kw = _state["kind_weights"]
    boost = 1.0
    for authority_id, kind in engagements:
        a = auths.get(authority_id, {})
        a_weight = float(a.get("weight", 0.5))  # unknown authorities still get a small bump
        k_weight = kw.get(kind, 0.0)
        boost += a_weight * k_weight
    return min(AUTHORITY_BOOST_CAP, boost)


def _recency_decay(content_type: str, age_days: float) -> float:
    """exp(-ln(2) * age_days / half_life)."""
    decay = _state["decay"] or {}
    half_lives = decay.get("half_lives_days", {})
    half_life = half_lives.get(content_type, 60)  # default 60d for unknown types
    if isinstance(half_life, str):
        return 1.0  # special-handling types (benchmarks); skip decay
    return math.exp(-math.log(2) * age_days / half_life)


def _resolve_source_paths(source_ids: list[str], corpus_dir: Path) -> dict[str, Path]:
    """Find the markdown file for each source_id by scanning frontmatter.

    For correctness over speed; on 1000s of files this is ~30ms.
    """
    out: dict[str, Path] = {}
    needed = set(source_ids)
    for path in corpus_dir.rglob("*.md"):
        if not needed:
            break
        # Cheap pre-filter: filename ends with -<sourceid>.md (per ingest/run.py slug)
        try:
            fm, _ = read_post(path)
        except Exception:  # noqa: BLE001
            continue
        if fm.source_id in needed:
            out[fm.source_id] = path
            needed.discard(fm.source_id)
    return out


def _load_frontmatters(paths_by_id: dict[str, Path]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for sid, path in paths_by_id.items():
        try:
            fm, _ = read_post(path)
            out[sid] = fm.model_dump(mode="json")
        except Exception:  # noqa: BLE001
            out[sid] = {}
    return out


def _content_type_from_fm(fm: dict[str, Any]) -> str:
    return fm.get("source_type") or "blog_post"


def _age_days(fm: dict[str, Any]) -> float:
    raw = fm.get("date")
    if raw is None:
        return 0
    try:
        d = date.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return 0
    today = datetime.now(timezone.utc).date()
    return max(0.0, (today - d).days)


# ---------- public tools ----------

def search(query: str, *, top_n: int = DEFAULT_TOP_N, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Hybrid corpus search. RRF + authority boost + recency decay.

    Filters supported:
      since (ISO date), until (ISO date), source_types (list[str]),
      min_authority_boost (float), authors (list[str]).
    """
    _ensure_state()
    filters = filters or {}

    bm25 = _bm25_candidates(query)
    vec = _vector_candidates(query)
    by_chunk = _rrf_combine(bm25, vec)
    if not by_chunk:
        return []

    # Group by source_id, keep the best chunk per source.
    best_per_source: dict[str, tuple[str, dict[str, Any]]] = {}
    for chunk_id, d in by_chunk.items():
        sid = d["source_id"]
        existing = best_per_source.get(sid)
        if existing is None or d["rrf"] > existing[1]["rrf"]:
            best_per_source[sid] = (chunk_id, d)

    source_ids = list(best_per_source)
    eng_map = _engagements_for(source_ids)

    paths = _state["paths"]
    corpus_dir = (PROJECT_ROOT / paths["corpus_dir"]).resolve()
    paths_by_id = _resolve_source_paths(source_ids, corpus_dir)
    fms = _load_frontmatters(paths_by_id)

    # Apply filters + score
    hits: list[Hit] = []
    since_d = _parse_date(filters.get("since"))
    until_d = _parse_date(filters.get("until"))
    type_filter = filters.get("source_types")
    author_filter = filters.get("authors")
    min_boost = filters.get("min_authority_boost")

    for sid in source_ids:
        chunk_id, d = best_per_source[sid]
        fm = fms.get(sid, {})
        path = paths_by_id.get(sid)
        d_date = _parse_date(fm.get("date"))

        if type_filter and fm.get("source_type") not in type_filter:
            continue
        if since_d and d_date and d_date < since_d:
            continue
        if until_d and d_date and d_date > until_d:
            continue
        if author_filter:
            authors = fm.get("authors", [])
            if not any(a in author_filter for a in authors):
                continue

        boost = _authority_boost(eng_map.get(sid, []))
        if min_boost is not None and boost < min_boost:
            continue
        decay = _recency_decay(_content_type_from_fm(fm), _age_days(fm))
        score = d["rrf"] * boost * decay
        snippet = (d["text"] or "")[:300]
        hits.append(Hit(
            source_id=sid,
            chunk_id=chunk_id,
            text=d["text"],
            score=score,
            rrf_score=d["rrf"],
            authority_boost=boost,
            recency_decay=decay,
            frontmatter=fm,
            path=str(path.relative_to(PROJECT_ROOT)) if path else None,
            snippet=snippet,
        ))

    hits.sort(key=lambda h: h.score, reverse=True)
    return [h.to_dict() for h in hits[:top_n]]


def find_by_authority(authority_id: str, *, since: str | None = None, top_n: int = 50) -> list[dict[str, Any]]:
    """Engagements by authority_id, optionally time-filtered.

    Returns engagement records joined with corpus source if available.
    """
    _ensure_state()
    conn = _state["conn"]
    params: list[Any] = [authority_id]
    where = "authority_id = ?"
    if since:
        where += " AND recorded_at >= ?"
        params.append(since)
    rows = conn.execute(
        f"SELECT source_id, kind, recorded_at, metadata FROM engagements "
        f"WHERE {where} ORDER BY recorded_at DESC LIMIT ?",
        (*params, top_n),
    ).fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        meta = json.loads(r["metadata"]) if r["metadata"] else {}
        out.append({
            "source_id": r["source_id"],
            "kind": r["kind"],
            "recorded_at": r["recorded_at"],
            "url": meta.get("url"),
            "metadata": meta,
        })
    return out


def recent(topic: str | None = None, *, hours: int = 168, top_n: int = 20) -> list[dict[str, Any]]:
    """Hard recency cut. Optionally narrow with vector similarity if topic given.

    Powers the orchestrator's forced recency pass.
    """
    _ensure_state()
    if topic:
        # Run search with strict since filter
        from datetime import timedelta
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).date().isoformat()
        return search(topic, top_n=top_n, filters={"since": since})

    # No topic: just list recent corpus items by frontmatter date.
    conn = _state["conn"]
    paths = _state["paths"]
    corpus_dir = (PROJECT_ROOT / paths["corpus_dir"]).resolve()
    cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
    out: list[dict[str, Any]] = []
    seen = 0
    for path in sorted(corpus_dir.rglob("*.md"), reverse=True):
        if seen >= top_n * 5:
            break
        try:
            fm, _ = read_post(path)
        except Exception:  # noqa: BLE001
            continue
        d_date = _parse_date(fm.date)
        if not d_date:
            continue
        if d_date.timestamp() < cutoff:
            continue
        out.append({
            "source_id": fm.source_id,
            "publication": fm.publication,
            "url": fm.url,
            "date": str(fm.date),
            "path": str(path.relative_to(PROJECT_ROOT)),
            "tags": fm.tags,
        })
        seen += 1
    out.sort(key=lambda x: x["date"], reverse=True)
    return out[:top_n]


def fetch_detail(source_id: str) -> dict[str, Any]:
    """Return full markdown content + frontmatter for a source_id."""
    _ensure_state()
    paths = _state["paths"]
    corpus_dir = (PROJECT_ROOT / paths["corpus_dir"]).resolve()
    for path in corpus_dir.rglob("*.md"):
        try:
            fm, body = read_post(path)
        except Exception:  # noqa: BLE001
            continue
        if fm.source_id == source_id:
            return {
                "source_id": source_id,
                "frontmatter": fm.model_dump(mode="json"),
                "body": body,
                "path": str(path.relative_to(PROJECT_ROOT)),
            }
    return {"error": f"source_id {source_id} not found"}


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


# ---------- MCP server entry point ----------

def main() -> None:
    """Run as a stdio MCP server. Configured in .mcp.json."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        log.error("mcp package not installed. Run: uv sync")
        sys.exit(1)

    server = FastMCP("dair-corpus")

    @server.tool()
    def corpus_search(query: str, top_n: int = DEFAULT_TOP_N,
                      since: str | None = None, until: str | None = None,
                      source_types: list[str] | None = None,
                      min_authority_boost: float | None = None,
                      authors: list[str] | None = None) -> list[dict[str, Any]]:
        """Hybrid corpus search (RRF k=60 over FTS5 + sqlite-vec) with
        authority boost and per-content-type recency decay.

        Args:
            query: search terms.
            top_n: max results.
            since/until: ISO date filters (YYYY-MM-DD).
            source_types: e.g. ["newsletter", "blog_post"].
            min_authority_boost: only return results with boost >= this.
            authors: restrict to specific authors.
        """
        filters: dict[str, Any] = {}
        if since: filters["since"] = since
        if until: filters["until"] = until
        if source_types: filters["source_types"] = source_types
        if min_authority_boost is not None: filters["min_authority_boost"] = min_authority_boost
        if authors: filters["authors"] = authors
        return search(query, top_n=top_n, filters=filters)

    @server.tool()
    def corpus_find_by_authority(authority_id: str,
                                 since: str | None = None,
                                 top_n: int = 50) -> list[dict[str, Any]]:
        """Engagement records by an authority (e.g., 'andrej_karpathy', 'tri_dao').

        Args:
            authority_id: slug from config/authorities.yaml.
            since: ISO datetime filter for recorded_at.
            top_n: max results.
        """
        return find_by_authority(authority_id, since=since, top_n=top_n)

    @server.tool()
    def corpus_recent(topic: str | None = None,
                      hours: int = 168,
                      top_n: int = 20) -> list[dict[str, Any]]:
        """Recency-filtered search; powers the forced recency pass.

        Args:
            topic: if given, vector-narrows within the time window.
            hours: lookback window (default 168 = 7 days).
            top_n: max results.
        """
        return recent(topic, hours=hours, top_n=top_n)

    @server.tool()
    def corpus_fetch_detail(source_id: str) -> dict[str, Any]:
        """Full markdown content + frontmatter for a given source_id.

        Args:
            source_id: 16-char hex from frontmatter (e.g., '77bbb793bcbcdc7c').
        """
        return fetch_detail(source_id)

    # ---- benchmarks tools ----
    @server.tool()
    def benchmark_current(benchmark: str, model: str) -> dict[str, Any] | None:
        """Most recent snapshot for (benchmark, model).

        Args:
            benchmark: e.g., 'openrouter', 'lmarena'.
            model: model identifier (case-insensitive).
        """
        from benchmarks import current as _current
        snap = _current(benchmark, model)
        return snap.to_dict() if snap else None

    @server.tool()
    def benchmark_top(benchmark: str, n: int = 10) -> list[dict[str, Any]]:
        """Top-N models by score on a benchmark.

        Args:
            benchmark: e.g., 'openrouter'.
            n: max results.
        """
        from benchmarks import top as _top
        return [s.to_dict() for s in _top(benchmark, n=n)]

    @server.tool()
    def benchmark_history(benchmark: str, model: str) -> list[dict[str, Any]]:
        """Score history for (benchmark, model), oldest → newest."""
        from benchmarks import history as _history
        return [s.to_dict() for s in _history(benchmark, model)]

    server.run()


if __name__ == "__main__":
    main()

"""corpus-server — the MCP exposed to Claude Code subagents.

Run via `python -m corpus_server.server` (configured in .mcp.json).

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


def _load_dotenv_into_environ(path: Path) -> None:
    """Minimal .env loader so HF_TOKEN reaches sentence-transformers when
    the MCP runtime spawns this server (same pattern as ingest/run.py)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

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

log = logging.getLogger("corpus_server.server")
RRF_K = 60
DEFAULT_TOP_N = 20
CANDIDATE_K = 100
AUTHORITY_BOOST_CAP = 4.0


# ---------- bootstrapping ----------

def _load_paths() -> dict[str, str]:
    return yaml.safe_load((PROJECT_ROOT / "config" / "paths.yaml").read_text())


def _load_decay() -> dict[str, Any]:
    return yaml.safe_load((PROJECT_ROOT / "config" / "decay.yaml").read_text())


def _load_domain_penalties() -> dict[str, float]:
    """Patch VV — load per-domain score multipliers. Missing file → no penalties."""
    path = PROJECT_ROOT / "config" / "domain_penalties.yaml"
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        log.warning("domain_penalties.yaml malformed; ignoring")
        return {}
    raw = data.get("penalties") or {}
    return {str(k).lower(): float(v) for k, v in raw.items()}


def _domain_penalty(url: str) -> float:
    """Patch VV — return penalty for the URL's host (1.0 if no penalty applies)."""
    if not url:
        return 1.0
    penalties = _state.get("domain_penalties") or {}
    if not penalties:
        return 1.0
    # Cheap host extraction: scheme://host/path → host.
    m = re.match(r"^[a-z]+://([^/]+)", url, re.IGNORECASE)
    host = (m.group(1) if m else url).lower()
    # Strip leading "www."
    if host.startswith("www."):
        host = host[4:]
    if host in penalties:
        return penalties[host]
    # Suffix match — "blog.medium.com" should hit "medium.com".
    for d, p in penalties.items():
        if host.endswith("." + d):
            return p
    return 1.0


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
        _state["domain_penalties"] = _load_domain_penalties()


def _ensure_model() -> None:
    if _state["model"] is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            log.warning("sentence-transformers not installed; vector search disabled")
            _state["model"] = False  # sentinel: tried, failed
            return
        # Patch AAA — read model + device from config/embedding.yaml.
        cfg_path = PROJECT_ROOT / "config" / "embedding.yaml"
        model_id = "Snowflake/snowflake-arctic-embed-s"
        device_pref = "auto"
        if cfg_path.exists():
            try:
                data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
                model_id = str(data.get("model") or model_id)
                device_pref = str(data.get("device") or "auto")
            except yaml.YAMLError:
                pass
        device = device_pref
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        log.info("loading embedding model %s on %s", model_id, device)
        _state["model"] = SentenceTransformer(model_id, device=device)


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
    domain_penalty: float = 1.0  # Patch VV
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
                "domain_penalty": round(self.domain_penalty, 3),
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


# ---------- query result cache (Patch YY) ----------

# In-process TTL cache. Scope: the lifetime of one corpus_server process,
# which spans ~one /deep-ai-research run. Researchers issuing identical
# queries (e.g. orchestrator's recency pass and a researcher's first call
# overlap on "embedding reranker contextual chunking") hit the cache.
# TTL covers a typical 25-min run with margin; longer-lived processes
# self-trim on access so the cache doesn't grow unbounded.

_CACHE_TTL_SECONDS = 600  # 10 minutes
_CACHE_MAX_ENTRIES = 256
_query_cache: dict[str, tuple[float, Any]] = {}


def _cache_key(name: str, args: tuple, kwargs: dict[str, Any]) -> str:
    """Deterministic cache key — JSON serialization with sorted kwargs."""
    payload = {
        "name": name,
        "args": list(args),
        "kwargs": {k: kwargs[k] for k in sorted(kwargs)},
    }
    return json.dumps(payload, default=str, sort_keys=True)


def _cache_get(key: str) -> Any | None:
    """Return cached value if present + not expired; else None."""
    import time
    entry = _query_cache.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.time() - ts > _CACHE_TTL_SECONDS:
        _query_cache.pop(key, None)
        return None
    return value


def _cache_put(key: str, value: Any) -> None:
    """Store value with current timestamp. LRU-evict on overflow."""
    import time
    if len(_query_cache) >= _CACHE_MAX_ENTRIES:
        # Evict the oldest entry (least-recently-stored).
        oldest_key = min(_query_cache, key=lambda k: _query_cache[k][0])
        _query_cache.pop(oldest_key, None)
    _query_cache[key] = (time.time(), value)


def _purge_expired() -> int:
    """Remove all expired entries. Returns number removed."""
    import time
    now = time.time()
    expired = [k for k, (ts, _) in _query_cache.items() if now - ts > _CACHE_TTL_SECONDS]
    for k in expired:
        _query_cache.pop(k, None)
    return len(expired)


# ---------- public tools ----------

def search(query: str, *, top_n: int = DEFAULT_TOP_N, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Hybrid corpus search. RRF + authority boost + recency decay.

    Filters supported:
      since (ISO date), until (ISO date), source_types (list[str]),
      min_authority_boost (float), authors (list[str]).

    Patch YY: results are TTL-cached for 10 minutes within the corpus_server
    process. Identical (query, top_n, filters) calls hit the cache; the cache
    is per-process (one /deep-ai-research run shares one cache).
    """
    cache_key = _cache_key("search", (query,), {"top_n": top_n, "filters": filters})
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    _ensure_state()
    filters = filters or {}

    bm25 = _bm25_candidates(query)
    vec = _vector_candidates(query)
    by_chunk = _rrf_combine(bm25, vec)
    if not by_chunk:
        return []

    # Patch TT — optional cross-encoder rerank. When enabled, replaces RRF
    # as the relevance score; authority boost / decay / domain penalty still
    # apply as multiplicative factors. When disabled, this is a no-op.
    from corpus_server import reranker as _rr
    if _rr.is_enabled():
        candidates = [(cid, d["text"]) for cid, d in by_chunk.items()]
        reranked = _rr.rerank(query, candidates)
        # Update the per-chunk relevance score in-place so downstream code
        # that reads d["rrf"] continues to work — the field now holds the
        # cross-encoder score rather than the RRF score.
        score_lookup = {cid: rerank_score for cid, _, rerank_score in reranked}
        for cid, d in by_chunk.items():
            d["rrf"] = score_lookup.get(cid, 0.0)

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
    entity_filter = filters.get("entity")  # Patch DDD — match in mentioned_*
    entity_filter_lower = entity_filter.lower() if isinstance(entity_filter, str) else None

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
        # Patch DDD — entity filter matches mentioned_entities OR mentioned_authorities.
        # Case-insensitive substring within each tag (so "qwen" matches
        # "Qwen3-Embedding-0.6B"). Empty entity filter is a no-op.
        if entity_filter_lower:
            mentioned = [
                *(fm.get("mentioned_entities") or []),
                *(fm.get("mentioned_authorities") or []),
            ]
            if not any(entity_filter_lower in str(m).lower() for m in mentioned):
                continue

        boost = _authority_boost(eng_map.get(sid, []))
        if min_boost is not None and boost < min_boost:
            continue
        decay = _recency_decay(_content_type_from_fm(fm), _age_days(fm))
        # Patch VV — domain penalty multiplies score; default 1.0 (no penalty).
        penalty = _domain_penalty(fm.get("canonical_url") or fm.get("url") or "")
        score = d["rrf"] * boost * decay * penalty
        snippet = (d["text"] or "")[:300]
        hits.append(Hit(
            source_id=sid,
            chunk_id=chunk_id,
            text=d["text"],
            score=score,
            rrf_score=d["rrf"],
            authority_boost=boost,
            recency_decay=decay,
            domain_penalty=penalty,
            frontmatter=fm,
            path=str(path.relative_to(PROJECT_ROOT)) if path else None,
            snippet=snippet,
        ))

    hits.sort(key=lambda h: h.score, reverse=True)
    result = [h.to_dict() for h in hits[:top_n]]
    _cache_put(cache_key, result)
    return result


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

    Powers the orchestrator's forced recency pass. Patch YY: TTL-cached.
    """
    cache_key = _cache_key("recent", (), {"topic": topic, "hours": hours, "top_n": top_n})
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    _ensure_state()
    if topic:
        # Run search with strict since filter
        from datetime import timedelta
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).date().isoformat()
        result = search(topic, top_n=top_n, filters={"since": since})
        _cache_put(cache_key, result)
        return result

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
    result = out[:top_n]
    _cache_put(cache_key, result)
    return result


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


def count(
    topic: str | None = None,
    *,
    since: str | None = None,
    until: str | None = None,
    source_types: list[str] | None = None,
    entity: str | None = None,
) -> dict[str, Any]:
    """Patch DDD — corpus_count tool. Density monitoring for any topic +
    filter combination. Cheaper than search because it skips score
    computation.

    Returns:
        {"count": <int>, "filters": {...}, "topic": "..."}
    """
    _ensure_state()
    cache_key = _cache_key("count", (topic,), {
        "since": since, "until": until,
        "source_types": tuple(source_types) if source_types else None,
        "entity": entity,
    })
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    paths = _state["paths"]
    corpus_dir = (PROJECT_ROOT / paths["corpus_dir"]).resolve()
    since_d = _parse_date(since)
    until_d = _parse_date(until)
    entity_lower = entity.lower() if entity else None
    topic_terms = [t.lower() for t in re.findall(r"[A-Za-z0-9_]+", topic)] if topic else []

    n = 0
    for path in corpus_dir.rglob("*.md"):
        if "digests" in path.parts:
            continue
        try:
            fm, body = read_post(path)
        except Exception:  # noqa: BLE001
            continue
        if since_d and fm.date < since_d:
            continue
        if until_d and fm.date > until_d:
            continue
        if source_types and fm.source_type not in source_types:
            continue
        if entity_lower:
            mentioned = [
                *(fm.mentioned_entities or []),
                *(fm.mentioned_authorities or []),
            ]
            if not any(entity_lower in str(m).lower() for m in mentioned):
                continue
        if topic_terms:
            haystack = (body or "").lower()
            if not any(t in haystack for t in topic_terms):
                continue
        n += 1

    result: dict[str, Any] = {
        "count": n,
        "topic": topic,
        "filters": {
            "since": since,
            "until": until,
            "source_types": source_types,
            "entity": entity,
        },
    }
    _cache_put(cache_key, result)
    return result


def related(source_id: str, *, top_n: int = 10) -> list[dict[str, Any]]:
    """Patch DDD — corpus_related tool. Returns the top-N chunks most
    similar (by vector cosine) to the given source_id, excluding the
    source itself. For cluster navigation: 'show me other things like
    this one'.
    """
    _ensure_state()
    cache_key = _cache_key("related", (source_id,), {"top_n": top_n})
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    detail = fetch_detail(source_id)
    if "error" in detail:
        return []
    body = detail.get("body") or ""
    if not body.strip():
        return []

    # Use the first ~1500 chars as the query — captures topic without
    # blowing past the embedding model's input window.
    query_text = body[:1500]
    hits = search(query_text, top_n=top_n + 1)
    # Drop the source itself if it shows up first (it usually does).
    filtered = [h for h in hits if h.get("source_id") != source_id][:top_n]
    _cache_put(cache_key, filtered)
    return filtered


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

    # Load .env so HF_TOKEN (and any other model credentials) reach the
    # embedding-model loader. The MCP runtime spawns this process directly
    # and does NOT inherit shell-level env, so we need an explicit loader
    # — same pattern as ingest/run.py uses.
    _load_dotenv_into_environ(PROJECT_ROOT / ".env")

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        log.error("mcp package not installed. Run: uv sync")
        sys.exit(1)

    server = FastMCP("deep-ai-research-corpus")

    @server.tool()
    def corpus_search(query: str, top_n: int = DEFAULT_TOP_N,
                      since: str | None = None, until: str | None = None,
                      source_types: list[str] | None = None,
                      min_authority_boost: float | None = None,
                      authors: list[str] | None = None,
                      entity: str | None = None) -> list[dict[str, Any]]:
        """Hybrid corpus search (RRF k=60 over FTS5 + sqlite-vec) with
        authority boost and per-content-type recency decay.

        Args:
            query: search terms.
            top_n: max results.
            since/until: ISO date filters (YYYY-MM-DD).
            source_types: e.g. ["newsletter", "blog_post"].
            min_authority_boost: only return results with boost >= this.
            authors: restrict to specific authors.
            entity: Patch DDD — restrict to chunks whose mentioned_entities
                or mentioned_authorities contains this string (case-insensitive
                substring match). Combine with date_range and source_types
                for sharply-targeted retrieval ("Karpathy mentions in lab
                blogs since 2026-01").
        """
        filters: dict[str, Any] = {}
        if since: filters["since"] = since
        if until: filters["until"] = until
        if source_types: filters["source_types"] = source_types
        if min_authority_boost is not None: filters["min_authority_boost"] = min_authority_boost
        if authors: filters["authors"] = authors
        if entity: filters["entity"] = entity
        return search(query, top_n=top_n, filters=filters)

    @server.tool()
    def corpus_count(topic: str | None = None,
                     since: str | None = None,
                     until: str | None = None,
                     source_types: list[str] | None = None,
                     entity: str | None = None) -> dict[str, Any]:
        """Patch DDD — count chunks matching filters. Density-monitoring tool;
        cheaper than corpus_search since it skips ranking. Useful for
        deciding whether the corpus has enough coverage on a topic before
        spending researcher budget on it.

        Args:
            topic: optional substring filter on chunk body.
            since/until: ISO date filters.
            source_types: restrict to e.g. ["newsletter", "lab_blog"].
            entity: same semantics as corpus_search entity filter.

        Returns:
            {"count": int, "topic": ..., "filters": {...}}
        """
        return count(topic, since=since, until=until,
                     source_types=source_types, entity=entity)

    @server.tool()
    def corpus_related(source_id: str, top_n: int = 10) -> list[dict[str, Any]]:
        """Patch DDD — find chunks similar to a given source. Cluster
        navigation: 'show me other things like this one'. Useful when
        the user retrieves a single load-bearing source and wants to
        broaden context without composing a fresh query.

        Args:
            source_id: 16-char hex from frontmatter.
            top_n: max results.

        Returns:
            corpus_search-style hit dicts, excluding the source itself.
        """
        return related(source_id, top_n=top_n)

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

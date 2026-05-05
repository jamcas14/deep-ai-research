"""Patch TT — cross-encoder reranker.

⚠ KEPT OFF under the current compute envelope.
   568M-param cross-encoder × top-50 candidates per researcher call × 8-call
   cap = multi-minute reranking PER RUN on CPU. Doesn't fit "small CPU model
   in the hot path." (See ~/.claude/projects/.../memory/feedback_no_gpu_no_api.md.)
   Skeleton kept for the case where the constraint changes (spare GPU, smaller
   corpus, or a 100M-class reranker becomes available).

Reranks the top-K candidates from the RRF combine step using a query×candidate
cross-encoder. Cross-encoders process the query and each candidate together,
producing a relevance score that's substantially better than bi-encoder
(embedding) similarity for ranking.

Default model: BAAI/bge-reranker-v2-m3 (568M params, Apache 2.0, MTEB-R 57.03).
Alternative: Qwen/Qwen3-Reranker-0.6B (MTEB-R 65.80) — better quality but
requires custom inference code via AutoModelForCausalLM (yes/no token trick).
The default uses sentence-transformers' CrossEncoder API for portability.

Activation:
  1. `uv sync --extra reranker` — installs sentence-transformers + torch.
  2. Set `DAIR_RERANKER_ENABLED=1` in env, OR
     `enable: true` in config/reranker.yaml.
  3. First call downloads ~500MB of model weights to ~/.cache/huggingface.

Off by default. With reranker off, retrieval is unchanged — RRF + boost +
decay + domain_penalty is the score. With reranker on, RRF is replaced by
the cross-encoder relevance score in the final formula:

    final_score = rerank_score * authority_boost * recency_decay * domain_penalty

Cost: CPU inference is ~1-2s for 50 candidates per query (medium model on
2024-era CPU). GPU inference is ~30-60ms — install with CUDA-enabled torch
to use GPU automatically.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger("corpus_server.reranker")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_MODEL_ID = "BAAI/bge-reranker-v2-m3"
DEFAULT_TOP_K = 50  # rerank the top-K from RRF; 50 is enough for quality, fast

_state: dict[str, Any] = {
    "enabled": None,  # tri-state: None=not loaded, True=on, False=off
    "model": None,
    "model_id": DEFAULT_MODEL_ID,
}


def _is_enabled() -> bool:
    """Tri-state load: env var, then config file, else off."""
    cached = _state["enabled"]
    if cached is not None:
        return bool(cached)
    # Env var override.
    env = os.environ.get("DAIR_RERANKER_ENABLED", "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        _state["enabled"] = True
        return True
    if env in ("0", "false", "no", "off"):
        _state["enabled"] = False
        return False
    # Config file.
    cfg_path = PROJECT_ROOT / "config" / "reranker.yaml"
    if cfg_path.exists():
        try:
            data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            log.warning("config/reranker.yaml malformed; reranker disabled")
            _state["enabled"] = False
            return False
        enabled = bool(data.get("enable", False))
        _state["enabled"] = enabled
        if "model" in data:
            _state["model_id"] = str(data["model"])
        return enabled
    _state["enabled"] = False
    return False


def _load_model() -> Any | None:
    """Lazy-load cross-encoder. Returns None on failure (reranker disabled)."""
    if _state["model"] is not None:
        return _state["model"]
    try:
        from sentence_transformers import CrossEncoder
    except ImportError:
        log.warning(
            "sentence-transformers not installed; reranker disabled "
            "(install with: uv sync --extra reranker)"
        )
        _state["enabled"] = False
        return None
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        device = "cpu"

    log.info("loading cross-encoder %s on %s", _state["model_id"], device)
    try:
        model = CrossEncoder(_state["model_id"], device=device)
    except Exception as e:
        log.error("failed to load reranker model %s: %s", _state["model_id"], e)
        _state["enabled"] = False
        return None
    _state["model"] = model
    return model


def is_enabled() -> bool:
    """Public probe. Returns True iff reranker is configured and loadable."""
    return _is_enabled()


def rerank(
    query: str, candidates: list[tuple[str, str]], *, top_k: int | None = None
) -> list[tuple[str, str, float]]:
    """Rerank candidate (chunk_id, text) pairs against the query.

    Returns [(chunk_id, text, rerank_score)] sorted by score descending.
    On failure (model not loaded, sentence-transformers missing), returns
    candidates unchanged with score=0.0. Caller should treat 0.0 as a signal
    to fall back to the RRF-only score path.
    """
    if not _is_enabled():
        return [(cid, text, 0.0) for cid, text in candidates]

    model = _load_model()
    if model is None:
        return [(cid, text, 0.0) for cid, text in candidates]

    if top_k is None:
        top_k = DEFAULT_TOP_K
    sliced = candidates[:top_k]
    if not sliced:
        return []

    # Build (query, candidate_text) pairs for CrossEncoder.predict.
    pairs = [(query, _truncate_for_rerank(text)) for _, text in sliced]
    try:
        scores = model.predict(pairs, show_progress_bar=False)
    except Exception as e:
        log.warning("reranker predict failed: %s — falling back to no rerank", e)
        return [(cid, text, 0.0) for cid, text in candidates]

    # Pair with chunk_ids and sort.
    scored = [
        (cid, text, float(s))
        for (cid, text), s in zip(sliced, scores, strict=True)
    ]
    scored.sort(key=lambda x: x[2], reverse=True)

    # Append any candidates beyond top_k (untouched, score=0.0) so caller
    # has the full set if they need it.
    leftover = [(cid, text, 0.0) for cid, text in candidates[top_k:]]
    return scored + leftover


def _truncate_for_rerank(text: str, max_chars: int = 1500) -> str:
    """Cap text length sent to the cross-encoder. bge-reranker-v2-m3 has a
    512-token context window; 1500 chars ≈ 350-400 tokens which leaves room
    for the query."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars]

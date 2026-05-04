"""Patch ZZ — persistent cross-run memory.

When the user asks a question similar to a past /deep-ai-research run, the
orchestrator can inject a summary of the past run's findings into the
recency pass context, avoiding redundant research.

Index format: `.claude/scratch/cross_run_index.json` (gitignored) — flat list
of past run records:

    [
      {
        "run_id": "2026-05-04-201130-find-ways-to-increase-speed",
        "question": "Find ways to increase speed and find more sources faster.",
        "finished_at": "2026-05-04T21:40:00Z",
        "report_path": "reports/2026-05-04-201130-find-ways-to-increase-speed.md",
        "embedding": [0.123, -0.456, ...]  # 384-dim arctic-embed-s
      },
      ...
    ]

API:
- `index_run(run_id, question, report_path)` — embed question + append to index
- `find_similar(query, threshold=0.85, top_k=3)` — return matching past runs
- `extract_conclusion(report_path)` — read §1 Conclusion + first 200 chars

Uses the same `Snowflake/snowflake-arctic-embed-s` model as the corpus search,
so no new model dependency.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

log = logging.getLogger("corpus_server.cross_run_memory")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = PROJECT_ROOT / ".claude" / "scratch" / "cross_run_index.json"

# Cache the embedding model across calls. Reuses corpus_server.server's
# SentenceTransformer load when available, otherwise loads its own.
_model_cache: dict[str, Any] = {}


def _get_model() -> Any | None:
    if "model" in _model_cache:
        return _model_cache["model"]
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        log.warning("sentence-transformers not installed; cross-run memory disabled")
        _model_cache["model"] = None
        return None
    log.info("loading embedding model for cross-run memory")
    model = SentenceTransformer("Snowflake/snowflake-arctic-embed-s", device="cpu")
    _model_cache["model"] = model
    return model


def _embed(text: str) -> list[float] | None:
    model = _get_model()
    if model is None:
        return None
    vec = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
    return [float(x) for x in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity. Vectors are normalized at encode time, so this is dot product."""
    if not a or not b or len(a) != len(b):
        return 0.0
    return float(np.dot(np.asarray(a), np.asarray(b)))


def _load_index() -> list[dict[str, Any]]:
    if not INDEX_PATH.exists():
        return []
    try:
        loaded = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        log.warning("cross_run_index.json malformed; treating as empty")
        return []
    if not isinstance(loaded, list):
        return []
    return [r for r in loaded if isinstance(r, dict)]


def _save_index(records: list[dict[str, Any]]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = INDEX_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(records, indent=2), encoding="utf-8")
    tmp.replace(INDEX_PATH)


def index_run(run_id: str, question: str, report_path: str) -> bool:
    """Add a finished run to the cross-run index. Idempotent on run_id —
    re-indexing the same run_id replaces its entry. Returns True on success.
    """
    embedding = _embed(question)
    if embedding is None:
        log.info("skipping cross-run index (no embedding model available)")
        return False

    records = _load_index()
    # Drop any prior entry for this run_id (idempotency).
    records = [r for r in records if r.get("run_id") != run_id]
    records.append({
        "run_id": run_id,
        "question": question,
        "finished_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "report_path": report_path,
        "embedding": embedding,
    })
    _save_index(records)
    log.info("indexed %s into cross-run memory (%d total runs)", run_id, len(records))
    return True


def find_similar(
    query: str, *, threshold: float = 0.85, top_k: int = 3
) -> list[dict[str, Any]]:
    """Return past-run records whose question embedding has cosine ≥ threshold
    to the query embedding. Sorted by similarity descending. Top-k cap.

    Each returned record adds a `similarity` field. Excludes the embedding
    field from the return so callers can JSON-dump it cheaply.
    """
    query_emb = _embed(query)
    if query_emb is None:
        return []

    records = _load_index()
    scored: list[dict[str, Any]] = []
    for r in records:
        emb = r.get("embedding")
        if not emb:
            continue
        sim = _cosine(query_emb, emb)
        if sim >= threshold:
            scored.append({
                "run_id": r.get("run_id"),
                "question": r.get("question"),
                "finished_at": r.get("finished_at"),
                "report_path": r.get("report_path"),
                "similarity": round(sim, 3),
            })
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


def extract_conclusion(report_path: str, max_chars: int = 1200) -> str:
    """Pull §1 Conclusion section from a past report. Falls back to the first
    paragraph if §1 isn't found. Returns empty string on read failure."""
    full_path = PROJECT_ROOT / report_path
    if not full_path.exists():
        return ""
    try:
        text = full_path.read_text(encoding="utf-8")
    except OSError:
        return ""

    # Match either "## 1. Conclusion" or "## §1 Conclusion" or "# 1. Conclusion".
    m = re.search(
        r"(?:^|\n)#{1,3}\s*(?:§|\d+\.?\s*)?\s*(?:Conclusion|Recommendation|Bottom\s+line)\b",
        text,
        re.IGNORECASE,
    )
    if not m:
        # Fall back to first 1.2K characters of body (post-frontmatter).
        body = text.split("---", 2)[-1] if text.startswith("---") else text
        return body.strip()[:max_chars]

    start = m.start()
    # Stop at next ## section or 1.2K chars, whichever comes first.
    end_match = re.search(r"\n#{1,3}\s+", text[start + 2:])
    end = (start + 2 + end_match.start()) if end_match else len(text)
    section = text[start:end].strip()
    return section[:max_chars]


def main() -> None:
    """CLI for backfilling the index from existing reports/."""
    import argparse
    parser = argparse.ArgumentParser(description="Cross-run memory CLI")
    parser.add_argument("--backfill", action="store_true",
                        help="Index all reports/*.md as past runs")
    parser.add_argument("--list", action="store_true", help="List indexed runs")
    parser.add_argument("--query", help="Find similar past runs to this query")
    parser.add_argument("--threshold", type=float, default=0.85)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if args.backfill:
        reports_dir = PROJECT_ROOT / "reports"
        if not reports_dir.exists():
            log.error("no reports/ directory")
            return
        n = 0
        for path in sorted(reports_dir.glob("*.md")):
            # Try to extract the question from the first markdown heading.
            text = path.read_text(encoding="utf-8")
            heading_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            question = heading_match.group(1).strip() if heading_match else path.stem
            run_id = path.stem
            ok = index_run(run_id, question, str(path.relative_to(PROJECT_ROOT)))
            if ok:
                n += 1
        log.info("backfilled %d reports", n)

    if args.list:
        for r in _load_index():
            print(f"{r['run_id']}: {r['question'][:80]}")

    if args.query:
        matches = find_similar(args.query, threshold=args.threshold)
        if not matches:
            print(f"no past runs ≥ {args.threshold} similar")
            return
        for m in matches:
            print(f"  sim={m['similarity']}  {m['run_id']}  → {m['question'][:80]}")


if __name__ == "__main__":
    main()

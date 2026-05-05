"""Patch AAA — embedding model migration.

⚠ DEFERRED under the current compute envelope.
   Don't run this without an explicit decision to accept the latency cost.
   (See ~/.claude/projects/.../memory/feedback_no_gpu_no_api.md.)

Switches the corpus from one embedding model to another, re-embedding every
chunk against the new model. Original migration target was arctic-embed-s
(384-dim, 33M) → Qwen3-Embedding-0.6B (1024-dim, 610M, MTEB-R 61.82). The
+9% retrieval quality lift is real but the 5-10× per-query CPU latency
makes interactive `/deep-ai-research` runs visibly slower; the project's
compute envelope (CPU-light models in the hot path or Claude subscription
elsewhere) doesn't tolerate that under normal use. Skeleton kept for the
case where the constraint changes.

Procedure:
  1. Backs up the sqlite DB to `<sqlite_path>.<timestamp>.bak` so a failed
     migration can be rolled back.
  2. Drops the existing `embeddings` virtual table (which is dim-locked at
     create-time by sqlite-vec).
  3. Updates EMBED_DIM by editing config/embedding.yaml in-place — this is
     a destructive write to a config file; backed up separately.
  4. Recreates `embeddings` at the new dim.
  5. Re-embeds every chunk via the new model.
  6. Updates pin_versions("embed_model") to the new model id.

Cost: 2-4h on CPU for ~8K chunks @ Qwen3-0.6B; ~30-45min on a CUDA-enabled
torch install (RTX 5080 or similar). The user's `--confirm` is required
because this is a destructive, long-running operation.

Usage:
    # See what would change without doing it:
    uv run python -m ingest.migrate_embedding --to Qwen/Qwen3-Embedding-0.6B --dry-run

    # Run for real (requires explicit --confirm):
    uv run python -m ingest.migrate_embedding \\
        --to Qwen/Qwen3-Embedding-0.6B --dim 1024 --confirm

Recovery:
    If the migration fails or you want to revert:
        cp corpus/_index.sqlite.<timestamp>.bak corpus/_index.sqlite
        # Edit config/embedding.yaml back to the prior (model, dim) values.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

log = logging.getLogger("ingest.migrate_embedding")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_paths() -> dict[str, str]:
    data = yaml.safe_load((PROJECT_ROOT / "config" / "paths.yaml").read_text(encoding="utf-8"))
    return dict(data) if isinstance(data, dict) else {}


def _read_current_config() -> dict[str, object]:
    cfg = PROJECT_ROOT / "config" / "embedding.yaml"
    if not cfg.exists():
        return {"model": "Snowflake/snowflake-arctic-embed-s", "dim": 384, "device": "auto"}
    data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    return dict(data) if isinstance(data, dict) else {}


def _write_config(model: str, dim: int, device: str) -> Path:
    cfg = PROJECT_ROOT / "config" / "embedding.yaml"
    backup = cfg.with_suffix(f".{int(time.time())}.bak")
    if cfg.exists():
        shutil.copy2(cfg, backup)
    cfg.write_text(
        "# Patch AAA — embedding model configuration. Updated by "
        "`ingest.migrate_embedding`.\n"
        f"model: {model}\n"
        f"dim: {dim}\n"
        f"device: {device}\n",
        encoding="utf-8",
    )
    return backup


def _backup_db(db_path: Path) -> Path:
    """Atomic-ish backup of the sqlite file. WAL files are also copied if
    present so a partially-applied migration can be reverted cleanly."""
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup = db_path.with_suffix(f".{timestamp}.bak")
    shutil.copy2(db_path, backup)
    for suffix in ("-wal", "-shm"):
        wal = db_path.with_name(db_path.name + suffix)
        if wal.exists():
            shutil.copy2(wal, backup.with_name(backup.name + suffix))
    return backup


def _re_embed(model_id: str, dim: int, device: str, batch_size: int = 32) -> tuple[int, int]:
    """Drop & recreate `embeddings` at `dim`, then re-embed all chunks.
    Returns (chunks_total, chunks_embedded)."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise SystemExit(
            "sentence-transformers not installed. Run: uv sync --extra embed"
        ) from None

    paths = _load_paths()
    db_path = (PROJECT_ROOT / paths["sqlite_path"]).resolve()

    # Patch AAA — must use a connection that knows the new EMBED_DIM. Reload
    # the module so its module-level EMBED_DIM picks up the freshly-written
    # config/embedding.yaml value.
    import importlib

    from ingest import _index as idx_mod
    importlib.reload(idx_mod)
    if idx_mod.EMBED_DIM != dim:
        raise SystemExit(
            f"config write didn't take effect: ingest._index.EMBED_DIM is "
            f"{idx_mod.EMBED_DIM}, expected {dim}. Aborting before any "
            "destructive operations."
        )

    conn = idx_mod.connect(db_path)

    # Drop and recreate the vec0 table at the new dim. NOTE: vec0 stores
    # dim in the table definition, so we MUST drop+recreate, not ALTER.
    log.info("dropping existing embeddings table")
    conn.execute("DROP TABLE IF EXISTS embeddings")
    conn.commit()
    conn.execute(idx_mod.EMBEDDINGS_DDL)
    conn.commit()

    # Load model.
    if device == "auto":
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"
    log.info("loading model %s on %s", model_id, device)
    model = SentenceTransformer(model_id, device=device)

    # Iterate chunks in batches.
    rows = conn.execute("SELECT chunk_id, text FROM chunks ORDER BY chunk_id").fetchall()
    total = len(rows)
    log.info("re-embedding %d chunks (batch_size=%d)", total, batch_size)
    embedded = 0
    t0 = time.time()
    for i in range(0, total, batch_size):
        batch = rows[i : i + batch_size]
        texts = [r["text"] for r in batch]
        vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        for r, v in zip(batch, vecs, strict=True):
            conn.execute(
                "INSERT OR REPLACE INTO embeddings(chunk_id, embedding) VALUES (?, ?)",
                (r["chunk_id"], list(float(x) for x in v)),
            )
        embedded += len(batch)
        if (i // batch_size) % 10 == 0:
            rate = embedded / max(time.time() - t0, 0.001)
            log.info("progress: %d / %d (%.1f chunks/sec)", embedded, total, rate)
        conn.commit()

    # Update pinned model.
    conn.execute(
        "INSERT OR REPLACE INTO pin_versions(name, value) VALUES (?, ?)",
        ("embed_model", model_id),
    )
    conn.commit()
    conn.close()
    return total, embedded


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--to", required=True, help="Target HF model id (e.g. Qwen/Qwen3-Embedding-0.6B)")
    p.add_argument("--dim", type=int, required=True, help="Target embedding dim (e.g. 1024 for Qwen3)")
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--dry-run", action="store_true", help="Print plan only; don't touch anything")
    p.add_argument(
        "--confirm",
        action="store_true",
        help="Required to actually run the migration (safety gate).",
    )
    p.add_argument("-v", "--verbose", action="count", default=0)
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose >= 2 else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    paths = _load_paths()
    db_path = (PROJECT_ROOT / paths["sqlite_path"]).resolve()
    current = _read_current_config()

    log.info("=== embedding migration plan ===")
    log.info("  current model: %s (dim=%s)", current.get("model"), current.get("dim"))
    log.info("  target  model: %s (dim=%d, device=%s)", args.to, args.dim, args.device)
    log.info("  sqlite db:     %s", db_path)
    if args.dry_run:
        log.info("(dry-run; nothing written)")
        return 0

    if not args.confirm:
        log.error(
            "--confirm not given. This will DROP the embeddings table and "
            "re-embed all chunks (~2-4h CPU on 8K chunks). Re-run with "
            "--confirm to proceed."
        )
        return 2

    backup = _backup_db(db_path)
    log.info("sqlite backup written to %s", backup)
    cfg_backup = _write_config(args.to, args.dim, args.device)
    log.info("config backup written to %s", cfg_backup)

    try:
        total, embedded = _re_embed(args.to, args.dim, args.device, batch_size=args.batch_size)
    except Exception as e:
        log.error("migration failed: %s", e)
        log.error(
            "RECOVERY: cp %s %s  &&  cp %s %s",
            backup, db_path, cfg_backup, PROJECT_ROOT / "config" / "embedding.yaml",
        )
        return 3

    log.info("migration complete: %d / %d chunks embedded", embedded, total)
    log.info("config/embedding.yaml updated to model=%s dim=%d", args.to, args.dim)
    return 0


if __name__ == "__main__":
    sys.exit(main())

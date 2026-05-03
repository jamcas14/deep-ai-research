# NOTES

Append-only running log. What was built, what's deferred, what surprised. Resume in fresh session by reading this + PLAN.md.

Monthly rotation: previous month moves to `notes/archive/NOTES-YYYY-MM.md`.

---

## 2026-05-03 — Project bootstrap

**Built:**
- `PLAN.md` — full architecture, post 4-pass analysis. Authoritative.
- `CLAUDE.md` — trimmed to ~80 lines; points to PLAN.md.
- `pyproject.toml` — uv-managed; min Python 3.10; deps: feedparser, httpx, pydantic, pyyaml, python-frontmatter, beautifulsoup4, dateutil, click, pysqlite3-binary, sqlite-vec, numpy, praw.
- `.gitignore`, `.env.example`, `Makefile`, `README.md`.
- `config/{paths,decay,sources,authorities}.yaml`. `authorities.yaml` moved from project root to `config/`.
- `ingest/` skeleton: `__init__.py`, `canonicalize.py` (URL canonicalization + source_id + content_hash), `frontmatter.py` (pydantic schema), `run.py` (runner with flock, --adapter, --dry-run, --since).
- `ingest/adapters/` skeleton: `_base.py` (RawSource + Adapter Protocol), `_rss.py` (generic RSSAdapter via feedparser + httpx + bs4).
- 4 Tier-1 newsletter adapters: `ainews.py`, `import_ai.py`, `tldr_ai.py`, `last_week_ai.py`. AINews built first per its compensation role for missing Twitter.
- `ops/verify-sqlite.sh` — checks pysqlite3-binary path works (system sqlite is 3.37.2 on this Pop!_OS, below sqlite-vec's required 3.45.x).

**Archived (Postgres-era, no longer authoritative):**
- `docs/ranking-formula.md`, `docs/authority-rules.md`, `docs/schema.md`, `docs/idempotency-and-drift.md`, `docs/prompt-injection-defense.md`, `docs/build-plan.md`, `docs/ingestion-tiers.md`, `docs/benchmarks.md`, `docs/mcp-tools.md` — moved to `docs/_archive/`.

**Surprises:**
- System sqlite on Pop!_OS 22.04 is 3.37.2; sqlite-vec needs 3.45+. Solved by adding `pysqlite3-binary` to deps; bypasses system sqlite entirely.
- Native Claude Code subagents are **sequential**, not parallel. Verified via claude-code-guide. Plan recovered: sequential dispatch is fine for personal use; revisit Agent Teams later if speed becomes painful.
- `Task` tool renamed to `Agent` in v2.1.63. Both names alias.
- Skills (`.claude/skills/`) is the recommended pattern in 2026, replacing `.claude/commands/`.
- `snowflake-arctic-embed-s` (Apache-2.0, BEIR 51.98) is a marginally-better drop-in for `bge-small-en-v1.5` (MIT, 51.68) at the same 33M-param 384-dim envelope. Switched.

**Built (continued, same session):**
- `Makefile` with help, install, verify-sqlite, ainews, ingest, lint, test, backup targets.
- `README.md` minimal, points at PLAN.md.
- Smoke-tested `uv sync`: 685 markdown files written across 4 adapters on first run; idempotent re-run produces 685 with no changes.
- AINews ingestion is **fully working**. Files dated up to 2026-05-01 (one day pre-current). Frontmatter validated by pydantic. Stable source_ids via `sha256(canonical_url)[:16]`.
- 25 unit tests passing (canonicalize, frontmatter round-trip, chunker invariants).
- Step 2 scaffold: `ingest/_index.py` (sqlite schema with vec0 virtual table for embeddings, engagements, pin_versions, run_costs, adapter_health), `ingest/chunk.py` (versioned chunker — v1 paragraph-aware), `ingest/embed.py` (snowflake-arctic-embed-s interface; lazy import of sentence-transformers from `--extra embed`), `ingest/embed_pending.py` (CLI). sqlite-vec v0.1.9 loaded successfully via pysqlite3-binary 3.51.1.
- Step 4 scaffold: `.claude/skills/deep-research/SKILL.md` + 6 agent files (`orchestrator`, `researcher`, `contrarian`, `verifier`, `critic`, `synthesizer`). System prompts substantive; they call out the structural fixes (forced recency pass, contrarian as first-class, verifier discipline against fabrication).

**Deferred to next session:**
- `uv sync --extra embed` and run `make ainews && uv run python -m ingest.embed_pending`. ~3GB PyTorch download, then ~1–6 CPU-hours to embed the existing 685 docs. Don't auto-trigger; user opt-in.
- **Step 3 is next**: authority polling. `ingest/poll_authorities.py` for GitHub stars/events, Reddit/HN, OpenAlex citations. Backfill engagements for the 24 seed authorities against the existing corpus.
- **Step 5**: eval framework. `evals/run_all.py` invokes `claude -p "/deep-research <query>"` per case, captures the run trace from `.claude/scratch/<run-id>/`, judges behaviorally.
- **Try the loop**: with corpus + agents in place, can manually run `claude` then `/deep-research <topic>` to see the loop fire even before embeddings. Researcher will fall back to Glob+Grep on markdown which works fine for small corpus.

**To know for fresh session:**
- The four mechanisms (authority boost, time decay, contrarian subagent, forced recency pass) are the entire moat. Keep them in mind for any retrieval-layer change.
- Twitter is **deferred indefinitely**. AINews + Reddit + HN are the proxies.
- The Karpathy-wiki regression eval will not pass until either Twitter ingestion lands OR the authority graph produces a Karpathy retweet via some other channel. Expected.

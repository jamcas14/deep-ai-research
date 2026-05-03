# deep-ai-research (dair)

A personal deep-research tool whose subject domain is AI/ML. Fixes the recency and authority/niche-signal failures of existing tools (Claude Research, Perplexity, OpenAI Deep Research). Runs entirely under your $200 Claude Max subscription; everything else is free.

## Quick start

```bash
# 1. Install deps (uv handles Python venv + lockfile).
uv sync

# 2. Verify sqlite-vec ABI compat (we ship pysqlite3-binary so this should pass).
bash ops/verify-sqlite.sh

# 3. Copy .env.example → .env and fill in tokens (all free).
cp .env.example .env
$EDITOR .env

# 4. Run a smoke ingestion against AINews.
uv run python -m ingest.run --adapter ainews --verbose

# 5. After Step 4 ships, you'll do this for actual research:
claude
/deep-research What memory systems should I look at for an LLM agent?
```

## Architecture

See [`PLAN.md`](PLAN.md) for the full plan, or [`CLAUDE.md`](CLAUDE.md) for the orientation.

## Status

- [x] Step 0 — Reconcile docs (CLAUDE.md trimmed; obsolete docs archived to `docs/_archive/`)
- [ ] Step 1 — pyproject + config + 4 newsletter adapters (in progress)
- [ ] Step 2 — Embedding sidecar
- [ ] Step 3 — Authority graph + engagement tagging
- [ ] Step 4 — Skill + orchestrator + researcher subagent
- [ ] Step 5 — Eval skeleton + 5 seed cases
- [ ] Step 6 — Specialist subagents + forced passes
- [ ] Step 7 — Lab blogs + Reddit + HN + HF Daily Papers
- [ ] Step 8 — Benchmarks subsystem
- [ ] Step 9 — Promoted arXiv pipeline
- [ ] Step 10 — Podcast transcripts
- [ ] Step 11 — Eval growth + weekly cadence

Build order details in [`PLAN.md` § build order](PLAN.md#build-order).

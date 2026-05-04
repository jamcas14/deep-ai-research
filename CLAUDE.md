# deep-ai-research

A personal deep-research tool whose subject domain is AI/ML. Runs entirely inside Claude Code under the $200 Max plan. **Markdown-first corpus + curated authority graph + structural fixes for the SEO bias of existing tools.**

## Why this exists

Claude Research, Perplexity, OpenAI Deep Research, and similar tools fail in two reproducible ways for AI/ML:

1. **Recency** — recommends old versions because ranking favors more-linked content. (DeepSeek v3.2 → v4 case.)
2. **Authority/niche signal** — misses niche-but-correct answers (Karpathy's LLM wiki) because there's no concept of *who I personally trust*.

The system fixes both via a continuously-ingested local corpus + a hand-curated authority graph + a research loop with a **forced contrarian subagent** and a **forced recency pass**. Everything runs locally and free.

## Architecture in one paragraph

The `/deep-ai-research` skill in `.claude/skills/deep-ai-research/` IS the orchestrator (Patch J 2026-05-04 — it runs in main-conversation context where `Agent` dispatch actually works). Six specialist subagents in `.claude/agents/`: `researcher`, `contrarian`, `verifier`, `fit-verifier`, `structure-verifier`, `critic`, `synthesizer` (seven if you count synthesizer running twice as draft + final). Dispatched in stages — parallel where independent (researchers + contrarian; citation + fit + structure verifiers), sequential where dependent (draft → verify → critic → final). Markdown corpus in `./corpus/` (gitignored). Tiny sqlite sidecar (`corpus/_index.sqlite`) holds engagement edges + embeddings via sqlite-vec brute-force `vec0`. Ingestion via Python adapters under `ingest/adapters/`, scheduled by systemd-timer. Live web via Claude Code's built-in `WebSearch` / `WebFetch` (no Brave, no SearXNG). Embeddings via `snowflake-arctic-embed-s` (33M params, 384-dim, Apache-2.0). Hybrid retrieval: ripgrep BM25 + vector cosine, RRF k=60, no score normalization.

## How you actually use it

```
cd ~/code/projects/claude-deep-research-ai-domain
claude
/deep-ai-research What memory systems should I look at for an LLM-based agent?
```

The skill (acting as orchestrator) runs a strict clarification gate, classifies the query, plans 3-5 sub-questions (4-5 typical for multi-axis recommendation queries; 5-6 reserved for genuine triple-axis complexity — bounded coverage per honesty contract §9, Patch X calibration), runs the forced recency pass, dispatches researchers (≤8 retrieval calls each) + contrarian (≤5 calls) in parallel, the synthesizer writes a draft on Sonnet, citation+fit+structure verifiers run in parallel (citation samples 12 most-load-bearing citations), the critic flags top 10 issues, the synthesizer rewrites the final on Sonnet (Opus only on re-dispatch). Token target ~600-800K, ~25 min wall-time, ≤30% of 5h Max window. Final report has §1 Conclusion (recommendation + reasoning + 2-4 runner-ups with dismissal reasons) + §2 Confidence panel (corpus/web sourcing metric + plan-usage metric) + §3 Findings opening with Comparison matrix + §4 Alternatives + §5 Open questions classified + §6 Citations. Saved to `reports/YYYY-MM-DD-slug.md`.

In the background, systemd-timer fires `python -m ingest.run` every 15 min. Adapters poll RSS / APIs, write markdown files to `corpus/`, update sqlite. You don't see this happening.

## The four mechanisms that fix the failure modes

1. **Authority-engagement boost in retrieval** — `authorities.yaml` is the moat. Content tagged with engagement from authority-graph members gets up to a 4× ranking multiplier.
2. **Per-content-type time decay** — half-lives in `config/decay.yaml`. Tweets 7d, blogs 60d, papers 365d, etc.
3. **Forced contrarian subagent** — fires on recommendation queries with the explicit job *"find the answer the lead agent will miss."* Structural answer to SEO bias.
4. **Forced recency pass** — every research run includes a `corpus.recent(topic, hours=168)` sweep regardless of query phrasing.

## Key files

- [`PLAN.md`](PLAN.md) — full architecture, build order, decision log. **Source of truth.**
- [`config/authorities.yaml`](config/authorities.yaml) — the moat: hand-curated authority graph.
- [`config/sources.yaml`](config/sources.yaml) — adapter registry.
- [`config/decay.yaml`](config/decay.yaml) — per-content-type half-lives.
- [`config/paths.yaml`](config/paths.yaml) — corpus/scratch/sqlite locations.
- [`evals/cases.yaml`](evals/cases.yaml) — regression cases including the DeepSeek-v4 and Karpathy-wiki seeds.
- `NOTES.md` — running log: what was built, what's deferred, what surprised. Append per build step.
- `docs/_archive/` — earlier (Postgres-era) docs; preserved for historical record. Don't reference for current architecture.

## Working style

- Ask before non-obvious *architectural* decisions. Pick reasonable defaults for routine choices and document in code or `NOTES.md`.
- After each build step, append to `NOTES.md`: what was built / what's deferred / what surprised / what to know for fresh session.
- Tools: `uv` for Python deps, `ruff` + `mypy` + `pytest` via pre-commit, `systemd-timer` (not Docker) for ingestion supervision.
- Tests for retrieval-layer specifically — authority weighting, time decay, dedup, entity resolution. Other code: light tests fine.
- Confirm schema and Docker setup with me before writing ingestion workers. ← *(Note: there's no Docker. systemd-timer + Python venv. Schema is already in `PLAN.md` § sqlite schema — confirm before changing.)*

## Models

- Lead orchestrator + research subagents: **Sonnet 4.6**
- Final synthesis on hard queries (conditional): **Opus 4.7**
- Eval judge: **Opus 4.7**
- Embeddings: **`snowflake-arctic-embed-s`** (local CPU)
- Podcast transcription: **faster-whisper** with `medium` model

## What NOT to build (in v1)

Web UI. Multi-user. Mobile. Email/push notifications. Cost dashboards beyond per-run ledger. Twitter/X (deferred indefinitely). Postgres / pgvector (rejected — markdown corpus is correct). LangChain (rejected — native Claude Code primitives). Brave / SearXNG (rejected — Claude Code's WebSearch).

## Cost

$0 beyond the existing $200 Claude Max subscription. Optional: ~$0.10–1/mo Anthropic API if you want background Haiku summarization at ingestion time (`.env`'s `ANTHROPIC_API_KEY`); fully optional, raw content works too.

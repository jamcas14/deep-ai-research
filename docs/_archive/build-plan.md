# Build plan

The numbered, validate-each-layer sequence. Don't skip ahead. Each step exists because the previous step must work first.

## Step 1 — Foundation

Postgres + pgvector container, schema scaffold, `corpus` module skeleton, Alembic, embedding model pinned, `config.toml` baseline.

**Done when:**
- `docker compose up` brings Postgres + pgvector cleanly.
- `alembic upgrade head` runs from empty.
- `python -m corpus.search "anything"` returns `[]` without error.
- `python -m corpus.ingest <fixture>` round-trips a known record.

**Confirm with user before continuing:** schema and Docker setup. (CLAUDE.md instruction.)

## Step 2 — Eval skeleton + 5 seed cases

`evals` module with `run_all`, scoring rubrics per category, history storage. Five hand-written cases including the DeepSeek v3.2→v4 (recency) and Karpathy-wiki (authority) regression seeds. **They will fail at this point.** That is the point — we now have an objective signal of progress.

**Done when:**
- `python -m evals run_all` runs 5 cases and writes a report.
- Failure messages are informative ("corpus contains 0 sources matching `DeepSeek v4`").
- Eval cases are in `evals/cases.yaml`, version-controlled.

## Step 3 — Tier 1 ingestion

`ingestion` module with the shared rate-limit budget, worker supervision, and adapters for arXiv, HuggingFace, GitHub, lab blogs.

**Done when:**
- Each adapter writes rows into `sources` + `summaries` + `details`.
- `health()` reports last-success times per adapter.
- "What did HuggingFace get this week" returns real (non-empty) results.
- Re-running ingestion does not duplicate rows (idempotency).

## Step 4 — Authority module + retrieval integration

`authority` module: YAML loader, engagement recorder, weight scorer. Wire `score_for(source_id)` into `corpus.search`'s ranking. Commit to the formula in `docs/ranking-formula.md` (already done; this step exercises it).

**Done when:**
- `authorities.yaml` loads cleanly; deletions soft-delete.
- Tier 1 adapters call `record_engagement` for the engagements they can detect.
- `corpus.search` results visibly differ when authorities are toggled.
- The Karpathy-case eval *partially* passes — partial credit accepted; full pass blocked on Twitter ingestion (Step 9).
- Unit tests for the ranking invariants in `docs/ranking-formula.md` § "Test invariants" all pass.

## Step 5 — Orchestration

`orchestration` module: the corpus MCP server, Claude Code subagents in `.claude/agents/`, and the forced passes (verification, recency, counter-position, critique).

**Done when:**
- `python -m orchestration.research "..."` runs end-to-end.
- A real query — "what's the latest version of DeepSeek?" — returns a cited answer.
- The verification pass catches a deliberately fabricated citation.
- The recency pass fires automatically on every research run.
- The counter-position pass fires on "should I use X" queries.

## Step 6 — Live web MCPs + per-run cache + injection fencing

Brave + Firecrawl MCPs wired in. The per-run live-fetch cache deduplicates within a run. Prompt-injection fencing applied at every model boundary per `docs/prompt-injection-defense.md`.

**Done when:**
- A query that exhausts corpus escalates to Brave.
- Firecrawl fetches by URL when the agent decides to follow a link.
- The cache evicts at end-of-run.
- The injection-defense unit tests pass.

## Step 7 — Tier 2 ingestion

Newsletter RSS with 1-yr backfill. Reddit (PRAW). HN (Algolia). OpenReview.

**Done when:**
- All four adapters healthy.
- Newsletter backfill complete; corpus contains historical issues.
- Reddit/HN posts surface in retrieval.

## Step 8 — Benchmarks subsystem

Independent module. Per-benchmark adapters; snapshot history; staleness alerts.

**Done when:**
- LMArena, Artificial Analysis, OpenRouter, LiveBench, GPQA Diamond, HLE, SWE-bench Verified, Aider Polyglot all have working adapters.
- Adding a new benchmark is config-only.
- The "How does Claude rank" eval passes.

## Step 9 — Twitter ingestion (Tier 3)

Apify (or equivalent) with documented Nitter/RSS-bridge swap-out path. Build LAST because it's fragile.

**Done when:**
- Authority-graph engagements (RT, quote, reply) are recorded.
- The Karpathy-wiki regression eval passes.
- Recency + authority + counter-position evals all pass.

## Step 10 — Long tail

Podcast transcripts (Whisper). Weekly "what did I miss" digest. Monthly source-discovery pass.

**Done when:**
- Tracked podcasts are transcribed and ingested.
- Weekly digest fires on schedule.
- Source-discovery surfaces candidate authorities for review.

## Pause points

The CLAUDE.md instruction is to confirm schema and Docker setup before writing ingestion workers. Translated to this plan:

- **Confirm before Step 3** (Tier 1 ingestion is the first ingestion-worker step).
- **Confirm before Step 9** (Twitter ingestion has unique fragility risk).

Other steps proceed without explicit confirmation as long as evals are improving.

## Stop conditions

Don't proceed past a step if:
- The step's "done when" is partially met. Finish before moving on.
- An eval that previously passed now fails. Investigate before moving on.
- A scheduled job has been failing for >24h. Fix before piling on new ingestion sources.

These are not arbitrary; they're the signal that something upstream is actually broken.

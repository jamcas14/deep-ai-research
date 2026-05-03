# Benchmarks subsystem

Separate from general ingestion. Benchmarks have different cadences, different shapes (snapshots vs summaries), and different retrieval patterns (current + history vs hybrid+authority). Authority weighting is meaningless on LMArena ELO.

## Tracked benchmarks

| benchmark | cadence | source preference |
|---|---|---|
| LMArena | daily | underlying GitHub data > rendered HTML |
| Artificial Analysis | on model-release events + weekly | endpoint JSON if available |
| OpenRouter rankings | weekly | API |
| LiveBench | weekly | underlying CSV/JSON |
| SLOPbench | on update | repo / API |
| RefusalBench | on update | repo / API |
| GPQA Diamond | on paper-level updates | leaderboard JSON |
| HLE (Humanity's Last Exam) | on update | leaderboard JSON |
| SWE-bench Verified | weekly | leaderboard JSON |
| Aider Polyglot | weekly | repo data |
| HF leaderboards | weekly | HF datasets API |

## Scrape strategy

Order of preference per benchmark:
1. **Underlying JSON / dataset.** Check DevTools → Network for the data endpoint before touching HTML. LMArena publishes data to GitHub; Artificial Analysis exposes endpoints; HF leaderboards are HF datasets.
2. **Public API.** OpenRouter, HF.
3. **Firecrawl fallback.** Only for rendered-only sites.

Per-benchmark scrape strategy lives in `src/benchmarks/scrapers/<name>.py`. Each scraper returns a list of `Snapshot` records.

## Snapshot history

Every scrape is a timestamped snapshot. Append-only. Never overwrite.

```sql
INSERT INTO snapshots (benchmark_name, model, score, metric_type, snapshot_at, metadata)
VALUES (...);
```

Enables queries like:
- "How did Claude rank on LMArena this week?" → `current("lmarena", "claude-opus-4-7")`
- "How did GPT-5 trend on Artificial Analysis over the past quarter?" → `history("artificial_analysis", "gpt-5", since="-90 days")`
- "Show me the top 10 on SWE-bench right now" → `top("swebench_verified", 10)`

## Schema normalization

Different benchmarks use different metric names: `elo`, `accuracy`, `pct_correct`, `pass@1`, etc. The `snapshots.metric_type` column carries this. Cross-benchmark comparisons use the metric_type to know what's comparable.

Adding a benchmark is **config-only** — `src/benchmarks/configs/<name>.toml` plus a scraper file. No schema change.

## Staleness alerts

Per-benchmark `expected_max_silence` config. If `now() - max(snapshot_at) > expected_max_silence`, a daily alert fires:

- Benchmark may be dead (alert: investigate).
- Scraper may be broken (alert: check scraper logs).

Alerts go to `NOTES.md` and the daily digest. We don't page; this is a single-user system.

## Retrieval integration

Benchmark queries don't go through `corpus.search`. They have their own entry points:

- `benchmarks.current(benchmark, model) -> Score`
- `benchmarks.history(benchmark, model, since) -> [Snapshot]`
- `benchmarks.top(benchmark, n=10, snapshot_at=None) -> [Score]`
- `benchmarks.compare(benchmark, models, snapshot_at=None) -> [Score]`

When a research query is benchmark-related, the lead orchestrator agent calls `benchmarks.*` directly, not `corpus.search`. The MCP server exposes both.

## Why not "just put benchmarks in `corpus`"

Considered and rejected:

1. **Different ranking model.** Authority weighting is meaningless on LMArena ELO. Forcing it through `corpus.search` requires special-casing benchmark hits — that special case bleeds across the corpus module.
2. **Different temporal model.** Most-recent-wins for benchmarks; per-content-type half-life for everything else. Two temporal models in one ranker is one too many.
3. **Different shape.** A benchmark snapshot is not a "source" with an author and a summary; it's a structured row with a model, score, and timestamp.

Splitting them keeps both modules deep (each does its one thing thoroughly) and avoids the temporal-decomposition trap of "everything is a source."

## Adding a benchmark

1. Add config: `src/benchmarks/configs/<name>.toml` with cadence, source URL, metric_type, expected_max_silence.
2. Add scraper: `src/benchmarks/scrapers/<name>.py` implementing `scrape() -> [Snapshot]`.
3. Run: `python -m benchmarks snapshot <name>` to verify.
4. Wire into the supervisor: it auto-discovers via the configs directory.
5. Add an eval case if the benchmark answers a class of question we want guaranteed.

No schema migration. No MCP tool change. No retrieval-layer change.

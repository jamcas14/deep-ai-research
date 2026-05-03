# Ingestion tiers

Per-source persistence strategy and tier ordering. Different sources have different shapes; one strategy does not fit all.

## Persistence categories

### Persist everything, indefinitely

| source | rationale |
|---|---|
| **X / Twitter** | Historical posts unrecoverable; ingest once, store forever. Single biggest fragility risk: official API unworkable at our volume; scraping (Apify/Nitter) breaks 2–4 times/year. Build with swap-out path. **Without Twitter, the Karpathy-wiki failure persists.** |
| **Newsletters** | Backfill ~1 yr archives where accessible (Latent Space, Interconnects, The Batch, Import AI, AI News by Smol AI, etc.). Ongoing RSS poll. |
| **Lab blogs** | ~30 blogs. Mirror entirely. Anthropic, OpenAI, DeepMind, DeepSeek, Mistral, Meta AI, plus smaller labs. |
| **Podcast transcripts** | Latent Space, Dwarkesh, MLST, No Priors, Cognitive Revolution. Whisper-transcribe, persist. |
| **Benchmark snapshots** | Historical sequence IS the value. Persist every snapshot timestamped. |
| **Reddit** | r/LocalLLaMA, r/MachineLearning. PRAW (free). Persist new posts. |
| **Hacker News** | Algolia API (free). AI-keyword-filtered firehose persisted. |

### Persist selectively (signal threshold)

| source | strategy |
|---|---|
| **arXiv** | ~70K cs.LG papers/year alone — too large to mirror. Ingest title + abstract + author + arXiv ID + categories for everything in tracked categories (cs.LG, cs.CL, cs.AI, cs.CV, stat.ML). Persist *full paper* only when threshold hit: cited by authority graph, GitHub repo with >100 stars, mentioned in tracked newsletter, or manually flagged. Live arXiv MCP for ad-hoc deep search. |
| **HuggingFace** | Persist new-model events, authority engagement, Daily Papers feed. Live HF MCP for ad-hoc model lookups. |
| **GitHub** | Persist authority-graph commits/stars, watched-org releases, weekly trending snapshots. Live GitHub MCP for ad-hoc repo queries. |
| **OpenReview** | Persist accepted papers from major conferences (NeurIPS, ICML, ICLR, COLM, ACL) and tracked workshops. Workshop papers are leading indicators. |

### Don't persist (live-query only)

| source | rationale |
|---|---|
| General web search results (Brave) | Too volatile. |
| Firecrawl page fetches | Cached only within a single research run. |

### Decision rule

Persist when historical sequence has value, when re-fetch is impossible/expensive, or when authority weighting needs to apply. Live-query when the source has a good API and persistence offers no advantage.

## Tier ordering (build sequence)

### Tier 1 — first (free APIs, low fragility)

- arXiv RSS (cs.LG, cs.CL, cs.AI, cs.CV, stat.ML), 15-min poll, signal-thresholded persistence.
- HuggingFace API (new models, Daily Papers), 5–15 min poll.
- GitHub API (watched orgs, authority-graph activity, trending), 15 min for releases / hourly for trending.
- Lab blog RSS (~30 blogs), 30-min poll.

### Tier 2 — after Tier 1 working

- Newsletter RSS with 1-yr backfill (one-shot historical job + ongoing poll).
- Reddit (PRAW). r/LocalLLaMA, r/MachineLearning.
- Hacker News (Algolia). AI-keyword filter.
- OpenReview (accepted papers from tracked conferences/workshops).

### Tier 3 — highest value, highest fragility

- X / Twitter via Apify (or equivalent). Build LAST because (a) breaks regularly and (b) you need everything else to confirm corpus + retrieval works before adding fragile dependencies.

### Tier 4 — slow signal, expensive

- Podcast transcripts (Whisper). Compute-heavy.

## Adapter contract

All adapters implement a single protocol:

```python
class SourceAdapter(Protocol):
    name: str
    poll_interval_seconds: int

    def iter_new(self, since: datetime) -> Iterable[RawSource]: ...
    def detect_engagements(self, raw: RawSource) -> Iterable[Engagement]: ...
    def supports_full_text(self) -> bool: ...
```

`iter_new` yields raw source records; the ingestion module handles canonicalization, dedup, summarization, embedding, and write. `detect_engagements` extracts authority engagements per `docs/authority-rules.md`.

Adapters do **not** call the database directly. They yield records; the ingestion module owns DB writes. This is the deep/shallow split: adapters are thin (just "how do I get records out of source X"); ingestion is thick (idempotency, retry, rate-limit, summarization, embedding, engagement-recording).

## Shared rate-limit budget

A single rate-limit broker, configured per-source-host:

```toml
[rate_limits]
"api.github.com" = { requests_per_hour = 5000, burst = 50 }
"export.arxiv.org" = { min_seconds_between = 3.0 }
"huggingface.co" = { requests_per_minute = 60 }
"www.reddit.com" = { requests_per_minute = 60 }
"hn.algolia.com" = { requests_per_minute = 100 }
```

Adapters acquire from the broker before each request. Backoff is exponential on 429/5xx with jitter. The broker is a singleton in the ingestion module; adapters do not invent their own limiters.

## Worker supervision

Single Docker Compose service `worker` running a Python supervisor that owns all adapter instances. `restart: always` policy. Each adapter's last-success time is reported via `health()`. A daily staleness alert fires if any adapter has been silent longer than `2 * poll_interval_seconds`.

Why one process, not one per adapter:
- Shared rate-limit broker is in-process; cross-process would require a queue.
- Easier to debug (one log stream).
- One user, one host — process-level isolation is overkill.

If memory or compute pressure becomes an issue, the cleanest split is by tier: separate worker processes for Tier 1, 2, 3, 4. Don't shard by individual adapter.

## Backfill jobs

Backfill is the same `ingest()` code path as ongoing polling, just with a different iterator. CLI:

```
python -m ingestion backfill <adapter> --since=2024-01-01
```

Backfill runs respect the same rate-limit broker — no special bypass. Long backfills (1-yr newsletter) run for hours; that's fine, idempotent, and resumable on restart.

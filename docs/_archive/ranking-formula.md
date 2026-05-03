# Ranking formula

The composite score that decides what `corpus.search` returns. This is the moat's actual mechanism — without it written down, retrieval changes are vibes-driven and regressions are invisible. Treat this file as load-bearing.

## Pipeline

```
candidates = top_K_bm25(query, K=50) ∪ top_K_vector(query, K=50)         # union, dedup by source_id
final(d) = rrf(d) * authority_boost(d) * recency_decay(d)                # for each candidate
```

Return the top N (default 20) by `final(d)`. Then run entity-level dedup (see "Dedup" below) and trim to the requested limit.

## Components

### 1. RRF (Reciprocal Rank Fusion)

```
rrf(d) = 1 / (k + bm25_rank(d)) + 1 / (k + vec_rank(d))      # k = 60
```

`bm25_rank(d)` is the 1-indexed rank of `d` in the BM25 result list, or `K+1` if absent. Same for `vec_rank`. `k = 60` is the canonical constant from the original RRF paper; keeps the formula stable as we tune K.

**Why RRF over weighted sum:** BM25 and cosine similarity are on incompatible scales (unbounded vs [0,1]); a weighted sum requires score normalization that is brittle across queries. RRF only uses ranks, so it composes cleanly. We can revisit if evals show the rank-ordinal information loss matters.

### 2. Authority boost

```
authority_boost(d) = min(4.0, 1 + Σ_{(a, kind) ∈ engagements(d)} authority_weight(a) * kind_weight(kind))
```

`authority_weight(a)` is from `authorities.yaml` — typically `[0.5, 1.0]` per authority. `kind_weight(kind)` is from `docs/authority-rules.md` per source-type (e.g., RT = 0.8, star = 0.5). The `min(4.0, ...)` cap prevents a single mega-popular tweet from drowning the rest of the score.

**Why multiplicative, not additive on the RRF score:** authority is a *trust* signal, not a relevance signal. Multiplying preserves ordering within unauthorized content and lifts authorized content as a coherent group, rather than letting a Karpathy retweet of an irrelevant link beat a perfect-relevance hit.

**Why a hard cap (4.0), not a sigmoid:** the failure mode we are protecting against is "Karpathy retweeted X" beating "high-quality SEO blog from yesterday." The cap is enough headroom for that and not so much that 30 authority engagements buries everything else. Sigmoid is fine alternative if evals demand it; start simple.

**`authorities.yaml` is source of truth.** The DB caches it but rebuilds on every reload. If a YAML deletion happens, the cache rebuild drops it; engagements remain (audit trail) but `score_for(source_id)` returns 0 for that authority.

### 3. Recency decay

```
recency_decay(d) = exp(-ln(2) * age_days(d) / half_life(content_type(d)))
```

`half_life` is per-content-type from `config.toml`:

| content_type | half_life_days | rationale |
|---|---|---|
| tweet | 7 | conversation half-life on X is ~1 week |
| reddit_post / hn_post | 14 | discussion thread half-life |
| newsletter_issue | 60 | reading window for weekly newsletters |
| blog_post | 60 | most blogs are timely |
| lab_blog_architecture | 180 | architecture posts age slowly |
| arxiv_paper | 365 | canonical work persists for a year |
| podcast | 90 | stays useful through next episode cycle |
| benchmark_snapshot | special | most-recent-wins; older only on explicit history queries |

Benchmarks are NOT subject to the standard decay — they go through `benchmarks.history()` which has its own ordering.

**Why exponential, not linear:** matches the observed half-life behavior; keeps very fresh content ranked very high without a discontinuity.

### 4. Dedup (entity-level)

After the top-N is selected, group hits by entity (e.g., the "DeepSeek v4 release" entity). Keep one representative per entity (the highest-scoring), attach the others as `also_seen_in` metadata. Source diversity per entity is preserved (different authors), source redundancy (same news, 30 outlets) is collapsed.

The entity-resolution module lives inside `corpus`. See `docs/schema.md` § entities.

## Filters

`search(query, filters)` accepts:

- `since` / `until` — timestamp window (applied as a hard filter before scoring, not a soft boost)
- `source_types` — restrict to e.g. `["tweet", "arxiv_paper"]`
- `authors` — restrict to specific authors
- `min_authority_boost` — filter out hits with no authority engagement
- `entity_ids` — restrict to specific entities

Filters short-circuit candidate generation; don't fetch a million BM25 candidates and then discard most.

## Test invariants

These invariants must hold; they are unit tests, not production checks. If any breaks, ranking is broken.

1. **Authority lift.** Synthetic corpus: doc A and doc B with identical embeddings, identical timestamps, identical BM25 hits. A is engaged by an authority (weight 1.0, RT). `final(A) > final(B)`. Specifically `final(A) ≈ 1.8 * final(B)` (1 + 1.0 * 0.8 = 1.8).
2. **Recency dominance at equal authority.** Doc A is 1 day old, Doc B is 14 days old, same content_type=tweet. With no authority on either, `final(A) > final(B)`, and the ratio matches `exp(ln(2) * 13 / 7) ≈ 3.6`.
3. **Cap.** A doc with 50 authority engagements has `authority_boost == 4.0`, not 50.
4. **Filter respect.** `since` removes older docs entirely, doesn't just down-rank them.
5. **Entity collapse.** 10 sources covering the DeepSeek v4 release surface as 1 result with 9 in `also_seen_in`, not 10 separate results.
6. **Stability under reload.** Reloading `authorities.yaml` does not change the score of unaffected docs.

## Tunables

In `config.toml` under `[ranking]`:

```toml
[ranking]
candidate_k = 50
rrf_k = 60
authority_boost_cap = 4.0
default_top_n = 20

[ranking.half_lives_days]
tweet = 7
reddit_post = 14
hn_post = 14
newsletter_issue = 60
blog_post = 60
lab_blog_architecture = 180
arxiv_paper = 365
podcast = 90
```

Anything else (the formula shape, RRF vs weighted sum, multiplicative vs additive composition) is a code change, not a tunable. If you change those, document why in `NOTES.md` and re-run the eval set.

## What NOT to add to the ranking

- A "freshness override" that puts anything < 24h at the top. Use `recent()` for that — it's a separate retrieval mode, not a ranking quirk.
- Source-quality scores beyond authority (e.g., domain reputation). The authority graph is the model.
- Personalization beyond the authority graph. Single user; the graph IS the personalization.
- LLM reranking on top of this. Maybe later, gated by an eval improvement; not v1.

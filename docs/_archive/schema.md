# Schema

Postgres + pgvector. Single database. Tables described here are the public contract of `corpus`; column-level detail in the migration files is the source of truth, this doc is the explanation of *why* each table exists and what invariants hold.

## Tables

### `sources`

The atomic unit. Every URL, post, paper, tweet, video, podcast episode is one row.

| column | type | notes |
|---|---|---|
| id | TEXT PK | `sha256(canonical_url)`, deterministic |
| canonical_url | TEXT NOT NULL | normalized URL (lowercased host, no tracking params, trailing slash stripped) |
| source_type | TEXT NOT NULL | enum: `tweet`, `arxiv_paper`, `github_repo`, `github_release`, `lab_blog`, `newsletter_issue`, `reddit_post`, `hn_post`, `podcast_episode`, `benchmark_snapshot` |
| author | TEXT | free text; nullable (some sources have no author) |
| author_handle | TEXT | platform handle when applicable, for engagement linking |
| published_at | TIMESTAMPTZ NOT NULL | original publication time |
| ingested_at | TIMESTAMPTZ NOT NULL DEFAULT now() | when *we* saw it |
| content_hash | TEXT NOT NULL | `sha256(full_content)` — drives revision detection |
| revision | INTEGER NOT NULL DEFAULT 1 | bumps when content_hash changes; see `docs/idempotency-and-drift.md` |
| parent_id | TEXT | non-null for revisions ≥ 2; points at first-seen revision |
| metadata | JSONB | source-type-specific (e.g., RT count, citation count) |

Indexes:
- `(source_type, published_at DESC)` — drives recency queries
- `(author_handle)` partial WHERE not null — drives `find_by_authority`
- `(canonical_url)` unique
- GIN on `metadata`

### `summaries`

Short summary per source. Loaded into context first; full text fetched on demand.

| column | type | notes |
|---|---|---|
| source_id | TEXT PK FK→sources.id | one summary per source |
| text | TEXT NOT NULL | 150–250 tokens, written by Haiku summarizer |
| embedding | vector(1024) NOT NULL | pgvector, embedding model from config |
| tsv | TSVECTOR | generated column from `text`, English config |
| summarized_at | TIMESTAMPTZ NOT NULL DEFAULT now() | for re-summarization tracking |

Indexes:
- HNSW on `embedding` (`m=16, ef_construction=64`)
- GIN on `tsv` for FTS / BM25-equivalent

### `details`

Full content. Separate table because details can be large and we don't want them in every query.

| column | type | notes |
|---|---|---|
| source_id | TEXT PK FK→sources.id |
| content | TEXT NOT NULL | full extracted text |
| content_format | TEXT NOT NULL | `plain`, `markdown`, `html`, `pdf_text` |
| stored_at | TIMESTAMPTZ NOT NULL DEFAULT now() |

No FTS or embeddings on `details` — those live in `summaries`. Detail is fetched only when `corpus.fetch_detail(id)` is called.

### `entities`

Deduped concepts/releases/papers — what 30 sources cluster under.

| column | type | notes |
|---|---|---|
| id | UUID PK |
| name | TEXT NOT NULL | e.g., "DeepSeek v4 release" |
| kind | TEXT NOT NULL | `release`, `paper`, `concept`, `incident`, `person` |
| canonical_embedding | vector(1024) | for nearest-neighbor entity matching at ingestion |
| metadata | JSONB | release_date, version, etc. |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() |

### `entity_sources`

Many-to-many: which sources belong to which entity.

| column | type | notes |
|---|---|---|
| entity_id | UUID FK→entities.id |
| source_id | TEXT FK→sources.id |
| confidence | REAL | [0,1], from clustering step |
| PRIMARY KEY | (entity_id, source_id) |

### `authorities`

Cache of `authorities.yaml`. Source of truth is the YAML file; this table is rebuilt from it.

| column | type | notes |
|---|---|---|
| id | UUID PK | stable per name; doesn't churn on YAML reload |
| name | TEXT NOT NULL | display name |
| handles | JSONB NOT NULL | `{"twitter": "karpathy", "github": "karpathy", ...}` |
| weight | REAL NOT NULL | from YAML, [0,1] |
| tier | TEXT NOT NULL | `canonical`, `trusted`, `signal` |
| notes | TEXT | freeform, from YAML |
| created_at | TIMESTAMPTZ NOT NULL |
| deleted_at | TIMESTAMPTZ | soft-delete on YAML removal |

Indexes:
- GIN on `handles` (key-existence queries)
- Partial on `(deleted_at IS NULL)` for the active set

### `engagements`

Many-to-many: which authority engaged with which source, and how.

| column | type | notes |
|---|---|---|
| id | BIGSERIAL PK |
| authority_id | UUID FK→authorities.id |
| source_id | TEXT FK→sources.id |
| kind | TEXT NOT NULL | per `docs/authority-rules.md` |
| recorded_at | TIMESTAMPTZ NOT NULL DEFAULT now() |
| metadata | JSONB | e.g., `{"original_tweet_id": "..."}` for RT |

Constraints:
- UNIQUE `(authority_id, source_id, kind)` — idempotent

Indexes:
- `(source_id)` — drives `score_for`
- `(authority_id, recorded_at DESC)` — drives `engagement_history`

### `snapshots`

Benchmark history. Separate from `sources` because shape and retrieval pattern are different.

| column | type | notes |
|---|---|---|
| id | BIGSERIAL PK |
| benchmark_name | TEXT NOT NULL | `lmarena`, `artificial_analysis`, `swebench_verified`, ... |
| model | TEXT NOT NULL | normalized model identifier |
| score | DOUBLE PRECISION NOT NULL |
| metric_type | TEXT NOT NULL | `elo`, `accuracy`, `pct_correct`, ... |
| snapshot_at | TIMESTAMPTZ NOT NULL |
| metadata | JSONB | per-benchmark extra fields (CI, sample size, etc.) |

Indexes:
- `(benchmark_name, model, snapshot_at DESC)` — drives `current(model, benchmark)` and history queries

### `queries_log`

Every research query and its retrieved sources. Becomes eval seed data.

| column | type | notes |
|---|---|---|
| id | UUID PK |
| query_text | TEXT NOT NULL |
| ran_at | TIMESTAMPTZ NOT NULL DEFAULT now() |
| retrieved | JSONB NOT NULL | `[{source_id, score, rank}, ...]` |
| report_md | TEXT | the synthesized answer |
| cost_estimate_usd | DOUBLE PRECISION | per-run cost cap ledger |
| metadata | JSONB | classification, options |

## Embedding model

Pinned in `config.toml`. Default: `BAAI/bge-large-en-v1.5` (1024 dims, open). Alternative: `text-embedding-3-large` (3072 dims, OpenAI) — if so, the `vector(1024)` columns become `vector(3072)` and a migration drops/rebuilds the HNSW index.

**Don't change after first commit.** Re-embedding the corpus is expensive; not changing it is not a hardship.

## Migrations

Alembic. Layout:

```
alembic/
  env.py
  script.py.mako
  versions/
    0001_initial_schema.py
    0002_<...>.py
```

Rules:

1. **No backwards-incompatible changes without a versioned migration.** No "just edit the DB by hand."
2. **HNSW index rebuilds are expensive.** Avoid changing embedding dims. If unavoidable, schedule for off-hours and document the runtime in `NOTES.md`.
3. **`pgvector` extension installation goes in `0001_initial_schema.py`.** `CREATE EXTENSION IF NOT EXISTS vector;` first thing.
4. **Idempotent re-ingestion is a hard guarantee.** Migrations must not break it (preserve `id` derivation, preserve `revision`/`parent_id` if those columns are touched).
5. **Schema docs (this file) update in the same commit as the migration.** No drift.

## Invariants

These are facts a future maintainer can rely on:

- `sources.id` is deterministic from `canonical_url`. Two ingestions of the same URL produce the same id.
- `revision = 1` for first-seen content. Subsequent revisions get `revision >= 2` and `parent_id = first_revision_id`.
- Every `summaries` row has exactly one `sources` row; same for `details`.
- `engagements` is unique on `(authority_id, source_id, kind)`. Re-ingesting a tweet does not duplicate the RT-engagement row.
- `authorities` rows are never hard-deleted by application code. Only the YAML reload sets `deleted_at`.
- `snapshots` is append-only. We never overwrite a snapshot.
- `queries_log` is append-only. The cost ledger uses it.

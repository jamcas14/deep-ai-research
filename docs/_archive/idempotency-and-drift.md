# Idempotency and content drift

Re-running ingestion against a source the system already has must never duplicate. But content does change: tweets get edited, arXiv papers get a v2, blogs get silently amended, repos get force-pushed. This file pins the policy.

## Stable IDs

```
source.id = sha256(canonical_url)
```

Canonical URL means:
- Lowercased host.
- Tracking params stripped (`utm_*`, `ref=`, `fbclid`, `gclid`, etc.).
- Trailing slash removed except on root.
- Twitter URLs normalized to `https://x.com/{handle}/status/{tweet_id}` regardless of `twitter.com`/`x.com`/mobile-prefix variants.
- arXiv URLs normalized to `https://arxiv.org/abs/{paper_id}` (no version in the canonical form; version goes in metadata).
- GitHub URLs use the default branch's blob ref or the canonical commit hash, whichever is appropriate for the source_type.

Canonicalization is implemented in `src/corpus/_canonical.py`. Adding a new source-type means adding a canonicalizer there. Don't sprinkle URL fixups across adapters.

## Content hash

```
source.content_hash = sha256(normalized_full_content)
```

`normalized_full_content` strips ephemera that would falsely flag a revision: trailing whitespace, edit-counters that some sites embed, view-count badges, "Last edited 2m ago" strings.

The normalizer is per-source-type; if it's not obvious what to strip, don't strip it — false revisions are recoverable, false non-revisions are silent corruption.

## Re-ingestion decision tree

When ingestion sees a URL:

```
id = sha256(canonical_url(url))
existing = sources WHERE id = $id ORDER BY revision DESC LIMIT 1

if existing is None:
    INSERT new row, revision=1, parent_id=NULL
    Embed + summarize
    return

if existing.content_hash == current_content_hash:
    # No change. Update ingested_at on the existing row.
    UPDATE sources SET ingested_at = now() WHERE id = $id AND revision = existing.revision
    return  # idempotent: no new row, no re-embedding, no re-summarization

# Content changed.
INSERT new row with:
  - id = sha256(canonical_url + ":r" + str(existing.revision + 1))
  - revision = existing.revision + 1
  - parent_id = existing.id (or existing.parent_id if existing already has one)
  - canonical_url = same
  - content_hash = new hash
Embed + summarize the new revision.
```

The first revision keeps the bare-canonical-URL ID. Subsequent revisions get suffixed IDs so we can hold both in the DB and link them by `parent_id`.

## What `corpus.search` returns

By default: only the latest revision per `(canonical_url)`. This is the common case — the user wants "the current state of this source," not its history.

`corpus.search(filters={"include_revisions": True})` returns all revisions. Used by:

- `evals` cases that test revision behavior.
- Manual debugging: "show me how this tweet changed."

`corpus.fetch_detail(id)` always returns the specific revision's content — never auto-redirects to "latest." That breaks audit trail.

## Source-type-specific notes

### Tweets / X

- Edits create revision 2+. The original revision is preserved.
- Deleted tweets: we don't auto-delete. The row stays; metadata records `observed_deleted_at`. (Useful for "did Karpathy delete this?")
- Replies are separate sources; threads are reconstructed at retrieval time.

### arXiv papers

- v1, v2, v3 are revisions of the same `id` (canonical URL excludes version).
- Each revision gets its own `details` row with the version-specific text.
- `metadata.version_history = ["v1", "v2"]` accumulates.

### Blogs / newsletters

- Silent edits trigger a revision. We log the diff in `metadata.diff_summary` so the user can see what changed.
- Deleted posts: revision row inserted with `observed_deleted_at` and a snapshot of the last-known content.

### GitHub

- For repo-level sources (README, top-level metadata): rev on default-branch HEAD change.
- For releases: revision means the release was edited (rare). New releases are new sources.
- For commits: each commit is its own source; commits don't revise.

### Reddit / HN

- Edits revise. Score changes don't.
- Deleted/removed posts: row stays; metadata records the state.

## Re-summarization policy

Summary is regenerated on any new revision. Embedding is regenerated alongside (same model). Engagements pointing at the previous revision keep pointing at the previous revision — they were observed at that content, and the lineage is preserved by `parent_id`. New engagements observed against the new revision attach to the new revision.

## Backfill semantics

On a backfill of N years of newsletter archives, every issue is a fresh `sources` row, revision=1. Backfill is not a different code path — it's the same `ingest()` function. The only difference is the data source iterates over historical RSS, not just-published.

`ingested_at` is set to `now()`, not the historical publication time. `published_at` carries the original timestamp. Time decay uses `published_at`.

## Tests

Required unit tests in `src/corpus/tests/test_idempotency.py`:

1. Same canonical URL twice in a row → one row, ingested_at updates.
2. Same URL, content changed → revision=2 row inserted, parent_id set, both rows queryable.
3. URL with tracking params and URL without → identical id.
4. arXiv v1 then v2 → revisions, both have details.
5. `corpus.fetch_detail(rev1_id)` returns rev1 content even after rev2 exists.
6. `corpus.search` returns latest revision only by default.

If any of these breaks, idempotency is broken. Block the merge.

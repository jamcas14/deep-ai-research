# Authority rules

How "Karpathy retweeted X" becomes data the ranking can use. The `authority` module owns this file conceptually; ingestion adapters call `authority.record_engagement(authority_id, source_id, kind)` per the rules below.

## Authority weight

Each entry in `authorities.yaml` has a `weight ∈ [0.0, 1.0]`. Tiers:

| tier | weight | examples |
|---|---|---|
| canonical | 1.0 | core researchers / lab leads with sustained track record |
| trusted | 0.7 | strong contributors, narrower domains |
| signal | 0.5 | reliable but lower-volume |

Weights are the user's call; revisit quarterly (one of the scheduled jobs).

## Engagement kinds and weights

`kind_weight(kind)` is fixed in code (not authority-by-authority — too much config). When a kind is below the threshold (currently 0), no engagement is recorded.

### Tweets / X

| kind | kind_weight | recorded? |
|---|---|---|
| authored | 1.0 | yes |
| retweet | 0.8 | yes |
| quote | 0.7 | yes |
| reply | 0.4 | yes (replies signal active engagement) |
| like | 0.0 | NO — too noisy, reading patterns vary, mass-like users exist |

A self-RT counts as authored (deduped: one engagement per (authority, source)).

### GitHub

| kind | kind_weight | recorded? |
|---|---|---|
| commit_author | 1.0 | yes (author of any commit on default branch) |
| star | 0.5 | yes |
| fork | 0.4 | yes |
| watch | 0.0 | NO — watch is for notifications, not endorsement |
| issue_open | 0.3 | yes (opening an issue signals engagement) |
| pr_author | 0.8 | yes |
| review | 0.6 | yes (substantive review, not just a +1) |

For commit_author on the default branch only — feature branches are noisy.

### arXiv

| kind | kind_weight | recorded? |
|---|---|---|
| author | 1.0 | yes (paper author) |
| cited_by_tracked | 0.6 | yes (paper cited by an authority's paper) |

Citation extraction is on title-level only initially; full-text citation parsing is Tier-4 work.

### Newsletter / blog

| kind | kind_weight | recorded? |
|---|---|---|
| author | 1.0 | yes |
| mentioned_with_link | 0.5 | yes |
| mentioned_without_link | 0.0 | NO — too easy to false-positive on name collisions |

Author detection: prefer structured byline; fall back to "by NAME" pattern only when blog is in the trusted-format list (Substack, Ghost, etc.).

### Reddit / HN

| kind | kind_weight | recorded? |
|---|---|---|
| post_author | 1.0 | yes |
| comment_author_top_level | 0.4 | yes (top-level comments only) |

We do not record upvotes or favorites — too low-signal.

### Podcasts

| kind | kind_weight | recorded? |
|---|---|---|
| host | 0.7 | yes (per episode) |
| guest | 1.0 | yes (per episode) |

## Reload semantics

`authority.reload_from_yaml(path)` is called:

1. At process start.
2. By a scheduled job (every 6 h is fine — YAML changes are infrequent).
3. By an explicit `corpus reload-authorities` CLI command for after manual edits.

**Race conditions:** the reload runs in a single Postgres transaction. Insertions, updates, soft-deletes (set `deleted_at`) all happen atomically. Concurrent ingestion writers calling `record_engagement` against an authority whose row is being replaced see the old row until commit. Engagements pointing at soft-deleted authorities still get recorded; they just contribute 0 to `authority_boost`.

**Deletion semantics:** removing an authority from YAML soft-deletes the DB row (`deleted_at = now()`). Engagements remain for audit. `score_for(source_id)` filters on `deleted_at IS NULL`.

**Add-back semantics:** a re-added authority resumes scoring; historical engagements that pointed at the soft-deleted row pop back into effect. (We don't re-derive engagements on add-back unless the user runs `corpus rebuild-engagements <authority>`, which is a separate job.)

## When to add an authority

The user's `authorities.yaml` is hand-curated. Suggested filters:

- Sustained AI/ML technical output (not just commentary).
- At least one of: paper authorship, frontier lab affiliation, OSS maintainership of a tool you'd use, depth-of-thought on X consistently signaled by the rest of the graph.
- Avoid: pure influencers, hype accounts, lab-PR accounts (use `lab_org` engagements instead — separate concept, lower weight).

Aim for 50–200 entries. More than 200 dilutes the signal.

## What NOT to do

- **Don't authority-weight orgs.** Anthropic-the-account retweeting something is PR. Anthropic researchers retweeting it is signal. Track *people*.
- **Don't infer authority transitively.** If A retweets B, B is not now an authority. The graph is hand-curated for a reason.
- **Don't track follower count.** Useless as a quality signal in this domain.
- **Don't use the like signal even with high weight.** Likes are bookmarks, attention markers, social maintenance, "interesting will read later." None of those means endorsement.

## Tunables

`kind_weight(kind)` lives in code (`src/authority/rules.py`) not config — these are decisions, not tunables. If you change them, re-run evals. Authority-level `weight` is per-entry in `authorities.yaml`.

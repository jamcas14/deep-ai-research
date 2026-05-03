# Distribution: making this usable for people who don't want API keys

## The user's question (paraphrased)

> Most people don't want to insert their own Reddit API key (and others). Can
> they download the corpus directly from somewhere I update — i.e., the API
> keys + ingestion stay private (mine), and the public path is "clone, get a
> recent corpus, run /deep-ai-research"?

## Short answer

**Yes for the codebase + index. Risky for the corpus content itself.** Here's
why and what to do instead.

## The legal constraint

The corpus contains content from third parties:

| source family | redistribution policy | risk if you publish full text |
|---|---|---|
| Newsletters (Smol AI, Import AI, TLDR AI, ...) | most explicitly prohibit republication | DMCA / terms-violation risk |
| Reddit posts/comments | Reddit Data API ToS specifically restricts redistribution; 2023+ enforced | account ban + legal complaint risk |
| Hacker News stories (Algolia mirror) | the *stories* link to others' content; comments are CC0 | comments OK, story body not yours to republish |
| Lab blogs (Anthropic, OpenAI, DeepMind, ...) | publication-dependent; some CC, most "all rights reserved" | reputation + complaint risk |
| Podcast transcripts | Whisper output; the underlying audio is rarely CC | high — you've effectively republished a copyrighted talk |
| arXiv abstracts | open license (mostly CC) | low |
| arXiv full PDFs | depends per paper | mixed |

**Bottom line**: republishing the full markdown corpus violates terms of most
sources we ingest. Even with summaries, "your" summaries of someone else's
content are derivative works under most jurisdictions.

This isn't theoretical — Reddit specifically litigated against API-data
republishers in 2023-24 and the chilling effect held.

## What you CAN safely distribute

The following are all yours / public-domain / clearly safe:

1. **The codebase** — already public on GitHub. ✓
2. **`config/authorities.yaml`** — public handles (Karpathy's Twitter handle isn't
   copyrighted). ✓
3. **`config/sources.yaml`, `decay.yaml`, `paths.yaml`** — your config. ✓
4. **`evals/cases.yaml`** — your eval rubrics. ✓
5. **Pre-built embedding index** *minus the chunk text* — embeddings are a
   derived, transformative representation; courts have generally treated
   them as fair-use research artifacts (cf. Authors Guild v. Google).
6. **Engagement edges** (`engagements` table) — public GitHub stars, citations,
   mentions. Public facts. ✓
7. **Benchmark snapshots** — published leaderboard data. ✓
8. **The URLs of ingested items** — links are public information. ✓

## What you CAN'T safely redistribute

- The **chunk text** in the `chunks` table (it's the actual content)
- The **markdown body** in `corpus/*.md` files
- Podcast transcripts
- Newsletter article bodies

## The practical solution: "thin distribution"

A distribution where the public path is:

```
git clone github.com/jamcas14/deep-ai-research
cd deep-ai-research
uv sync --extra embed
make bootstrap-public        # downloads pre-built index from a release artifact
claude
/deep-ai-research What's the latest from DeepSeek?
```

**What `make bootstrap-public` downloads** (from a periodically-published GitHub
Release):

- `bootstrap.sqlite` — embeddings + frontmatter + engagements + URLs
   (≈30 MB). **Excludes** the `chunks.text` column.
- `frontmatter-only.tar.gz` — the YAML frontmatter of every corpus item, as
   small standalone files. URLs + dates + tags + mentioned_authorities.
   No bodies.

**What's missing from the bootstrap**: the chunk text itself.

**How retrieval still works**:

- `corpus_search` returns ranked hits with frontmatter + URLs but **empty
  snippets** for chunks that aren't locally cached.
- When the orchestrator wants the body of a hit (or the synthesizer / verifier
  wants to read content), it calls `corpus_fetch_detail(source_id)` which
  *first* checks `corpus/<type>/<slug>.md` locally, *then* falls back to
  `WebFetch(url)` to live-fetch the original source.
- WebFetch happens at query time, billed against the user's own Claude Code
  Max plan. The user implicitly has the right to read the URL — they're a
  human (well, their agent) following a link.

This avoids the redistribution problem entirely. We're shipping a *map* (URLs,
embeddings, engagements) not a *book* (full text).

## Implementation sketch (deferred until v2)

A `make publish-bootstrap` target on your private side that:

1. Connects to your `corpus/_index.sqlite`.
2. Exports a copy with `chunks.text` stripped.
3. Tar-balls the markdown frontmatter (`grep -lP '^---' corpus/**/*.md` →
   strip body via `awk` BEGIN/END on `---`).
4. Uploads as a GitHub Release artifact, e.g., `bootstrap-2026-05-03.tar.gz`.

A `make bootstrap-public` target on the public side that:

1. Downloads the latest release artifact via `gh release download`.
2. Extracts to `corpus/`.
3. Runs `python -m ingest.embed_pending --skip-text-only` to use the imported
   embeddings without re-computing.

## What to tell users in the public README

> This is a personal AI/ML deep-research tool. To run it against the live
> internet:
>
> 1. Clone the repo, `uv sync --extra embed`.
> 2. `make bootstrap-public` (downloads an embeddings index + URL map; ~30 MB).
> 3. `claude` → `/deep-ai-research <question>`.
>
> The orchestrator will retrieve URLs from the local index and live-fetch
> their content via Claude Code's WebSearch/WebFetch (covered by your Max
> plan). No third-party API keys needed.
>
> If you want your own continuously-updated corpus instead of the snapshot,
> see `docs/self-hosting.md` for the API setup (~free; ~30 min).

## Trade-offs

- **Live-fetch latency**: WebFetch adds a few seconds per source the
  orchestrator decides to read. Acceptable for the personal-research-tool
  use case where queries take 2-5 min anyway.
- **Stale URLs**: if a newsletter URL goes dead, you fall back to WebSearch
  for the topic. The system already does this.
- **Bootstrap freshness**: published as often as the user (you) chooses to
  run `make publish-bootstrap`. Weekly is reasonable.
- **License clarity**: the README of the public repo should explicitly state
  "Bootstrap contains derived embeddings + URL maps; no third-party content
  is republished. Live content fetching at query time is your responsibility."

## What this means for the existing v1

Nothing today. The user's own private corpus is fine — `corpus/` is gitignored
and they're using their own Claude Code session to query it. The distribution
question only matters if/when they actually publish a release artifact.

When they get there, the v2 bootstrap mechanism above is the path. Until then,
the public repo (already at github.com/jamcas14/deep-ai-research) is just the
codebase, which is fully fine to share.

## Recommendation

For the user (you):

1. **Ship as-is for now.** The public repo is the codebase. People who clone
   it ingest their own corpus from public APIs (no special creds needed for
   most of it — only Reddit + GitHub PAT, both free 5-min signups).
2. **Defer the bootstrap distribution to a v2 milestone**, after you've used
   the system yourself for a few weeks and confirmed the moat works.
3. **In the public README, clearly mark which adapters need credentials**
   (currently just GitHub PAT for authority polling and Reddit OAuth) and
   make all of them gracefully no-op if creds are missing — which they
   already do.

For the bootstrap path specifically: it's a real ~1-day implementation. The
hardest part is the legal review, not the code. If you decide to ship a
public bootstrap, get a lawyer to look at the embeddings-only stance.

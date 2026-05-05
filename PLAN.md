# Personal AI Research Assistant — Final Plan

> Status: pending user signoff. Once approved, this plan supersedes the contradictory docs/* written for the Postgres path. Those docs will be rewritten or removed in execution Step 0.

## Why this exists

Existing tools (Claude Research, OpenAI Deep Research, Perplexity, Gemini Deep Research) fail in two reproducible ways for AI/ML research:

1. **Recency** — they recommend old versions (DeepSeek v3.2 when v4 is out, Sonnet 4.5 when 4.6 is out) because ranking favors older, more-linked content.
2. **Authority/niche signal** — they miss niche-but-correct answers (Karpathy's LLM wiki) because they have no concept of *who I personally trust*.

The system fixes both via a continuously-ingested local corpus + a hand-curated authority graph + a research loop with structural mechanisms for surfacing the underrated answer. **The corpus and the authority graph are the moat.** The orchestration loop is commodity.

## How this plan was reached

Five passes. Each pass tightened the plan; the largest reframes are flagged ★.

- **Pass 1** — initial flaw analysis. Found 24 issues across architecture, ops, and unverified technical claims.
- **Pass 2** — research verification. Spawned a `claude-code-guide` agent and a `deep-research` agent in parallel; ran three WebSearches concurrently. Verified Claude Code subagent semantics May 2026, embedding-model landscape, sqlite-vec status, Smol AI / AINews status, Whisper CPU performance, and current AI newsletter RSS availability.
- **Pass 3** — synthesized findings. Twelve corrections to the prior plan, including the **biggest one: Claude Code subagents are sequential, not parallel** (multiple `Agent()` calls in one prompt run one-after-the-other unless you opt into experimental Agent Teams). Also: switch from `bge-small-en-v1.5` to `snowflake-arctic-embed-s`; switch from `.claude/commands/` to `.claude/skills/`; tool name is now `Agent`, not `Task`; AINews migrated to `news.smol.ai`.
- **Pass 4** — write the final reconciled plan (this document).
- **Pass 5** — held in reserve; if review surfaces remaining gaps, re-iterate.

The previous Postgres+pgvector+Alembic+Docker plan is obsolete: once Claude Code is the runtime, native file tools (`Read`, `Glob`, `Grep`) work directly on markdown, and the realistic 5-year corpus (25–50K docs) doesn't need a relational database. The current plan is **markdown-first, native-Claude-Code-first, fully-free**.

---

## Architecture

```
~/code/projects/claude-deep-research-ai-domain/
├── CLAUDE.md                          # ~80-line orientation; loaded every session
├── PLAN.md                            # this file
├── NOTES.md                           # current-month log; older content rotates to notes/archive/
├── .claude/
│   ├── honesty_contract.md            # system-wide rules read by every subagent
│   ├── skills/
│   │   └── deep-ai-research/
│   │       └── SKILL.md               # /deep-ai-research <question> entry point — also the orchestrator (Patch J: dispatch lives at skill level so Agent works)
│   ├── agents/                        # all files prefixed deep-ai-research-*.md
│   │   ├── deep-ai-research-researcher.md
│   │   ├── deep-ai-research-contrarian.md         # finds underrated answers (independent retrieval)
│   │   ├── deep-ai-research-verifier.md           # citation verifier — re-checks every citation
│   │   ├── deep-ai-research-fit-verifier.md       # checks recommendation/query fit
│   │   ├── deep-ai-research-structure-verifier.md # NEW (Patch L) — checks §1–§6 structural conformance, runner-up block, comparison matrix, citations list
│   │   ├── deep-ai-research-critic.md             # flags missing perspectives + retrieval-log coverage gaps
│   │   ├── deep-ai-research-synthesizer.md        # writes final cited report
│   │   └── _archive/                              # deprecated agents (kept for historical reference; do NOT rename back into agents/)
│   │       └── deep-ai-research-orchestrator.md.deprecated
│   └── scratch/                       # per-run subagent coordination; ephemeral
│       └── <run-id>/
│           ├── manifest.json          # query, classification, clarifications, sub_questions[*].must_cover_families, redispatches, dispatch_failures, structure_check, token_tally, usage_snapshot_start/end
│           ├── researcher-<N>-gen<G>.{md,json}   # generation-tagged for re-dispatch isolation; JSON has `dispatched_by: "subagent"` field for Patch K verification
│           ├── contrarian-gen<G>.{md,json}
│           ├── recency_pass.json
│           ├── synthesizer-draft.md
│           ├── verifier.json          # citation verifier output
│           ├── fit_verifier.json      # fit verifier output
│           ├── structure_verifier.json # structure verifier output (Patch L)
│           ├── critic.md
│           ├── synthesizer-final.md   # also copied to reports/<run-id>.md
│           └── retrieval_log.jsonl    # one JSON line per retrieval call across all agents (Patch I — required `tool` field, enumerated values; Patch K — `agent` field must be `researcher-<N>` / `contrarian` for stage-3 entries)
├── corpus/                            # gitignore'd — 25–50K markdown files at maturity
│   ├── newsletters/
│   ├── lab-blogs/
│   ├── reddit/
│   ├── hn/
│   ├── hf-daily-papers/
│   ├── podcasts/
│   ├── promoted-arxiv/
│   ├── benchmarks/                    # JSON snapshots
│   └── _index.sqlite                  # engagement edges + embeddings + chunker version
├── ingest/
│   ├── adapters/                      # one Python file per source
│   │   ├── ainews.py                  # Smol AI / AINews — Tier 1
│   │   ├── import_ai.py
│   │   ├── tldr_ai.py
│   │   ├── interconnects.py
│   │   ├── lab_blogs.py
│   │   ├── reddit.py
│   │   ├── hn.py
│   │   ├── hf_daily_papers.py
│   │   ├── podcasts.py
│   │   └── arxiv_promoted.py
│   ├── poll_authorities.py            # daily authority engagement polling
│   ├── summarize.py                   # Haiku-driven summarization
│   ├── embed.py                       # snowflake-arctic-embed-s → sqlite-vec
│   ├── chunk.py                       # versioned chunker; version recorded in sqlite
│   ├── canonicalize.py                # URL canonicalization
│   ├── frontmatter.py                 # pydantic schema + validation
│   └── run.py                         # called by systemd-timer
├── config/
│   ├── authorities.yaml               # the moat — hand-curated
│   ├── sources.yaml                   # adapter registry + cadences
│   ├── decay.yaml                     # per-content-type half-lives
│   └── paths.yaml                     # corpus location, scratch location, etc.
├── mcp/
│   └── corpus-server/                 # tiny MCP for sqlite-backed queries
│       └── server.py                  # 4 tools max
├── reports/                           # research outputs (committable, eval seed)
│   └── 2026-05-03-deepseek-v4.md
├── evals/
│   ├── cases.yaml                     # regression seeds
│   ├── run_all.py                     # eval runner
│   └── runs/                          # archived run traces
│       └── <run-id>/
├── ops/
│   ├── ingest.service                 # systemd unit
│   ├── ingest.timer                   # systemd timer with Persistent=true
│   └── verify-sqlite.sh               # ABI check for sqlite-vec
├── tests/
│   └── ...
└── pyproject.toml                     # uv-managed deps
```

### Core architectural commitments

1. **Markdown-first corpus.** Each ingested item is a `.md` file with YAML frontmatter. Claude Code's native `Read`/`Glob`/`Grep` reads them directly.
2. **One small sqlite sidecar** (`corpus/_index.sqlite`) — engagement edges, embedding vectors, chunker/model versions. No Postgres, no pgvector, no Alembic.
3. **Native Claude Code subagents** in `.claude/agents/`, dispatched from the skill (main-conversation context) via the `Agent` tool. **Dispatch lives at the skill, not in an orchestrator agent (Patch J)**: subagents cannot spawn sub-subagents — when an orchestrator agent tries to call `Agent`, the runtime omits it. The skill (which runs in main convo) has full `Agent` access. **Parallel where independent, sequential where dependent**: multiple `Agent` calls emitted in a single assistant message run concurrently. Stage 3 (researchers + contrarian) and Stage 5 (citation + fit + structure verifiers) fan out concurrently; draft → verify → critic → final remain sequential.
4. **Skill, not command** — `.claude/skills/deep-ai-research/SKILL.md` is the entry point.
5. **Subagent output coordination via scratch dir.** `.claude/scratch/<run-id>/<role>.{md,json}` — orchestrator reads/writes structured findings; bypasses the "subagents return only free text" limitation.
6. **Live web is Claude Code's `WebSearch` + `WebFetch`.** Covered by the $200 Max plan. No Brave, no SearXNG, no separate web-search MCP.
7. **Cost cap** is a per-run *token budget* (~250K input + 50K output max), enforced by orchestrator's running tally. Anthropic doesn't expose remaining-quota; estimate is good enough.
8. **Cron replaced by systemd-timer with `Persistent=true`** — survives the user shutting down overnight.

---

## How you actually use it

### Foreground (a research session)

1. `cd ~/projects/deep-ai-research && claude`
2. `/deep-ai-research <question>`
3. Skill loads orchestrator subagent.
4. **Clarification gate (strict).** Before classification, orchestrator runs the trigger checklist: hardware, budget, deployment context, term ambiguity, refusal-tolerance/content-tier, volume. If any trigger fires unstated AND the answer would change with it, it asks 2–4 sharp clarifying questions via `AskUserQuestion`. Skip rationale must quote user-provided text; inferred caller intent is not grounds to skip (honesty contract §8). Q&A is recorded in `manifest.json` and threaded to every subagent. Skipped only for self-directed exploration and simple factual queries.
5. Orchestrator classifies query (recency / verification / exploration / recommendation / benchmark).
6. Orchestrator generates a `<run-id>`, creates `.claude/scratch/<run-id>/`, plans 3–5 sub-questions.
7. **Staged dispatch — runs from the skill in main-conversation context (Patch J).** The skill IS the orchestrator; an orchestrator agent file would be defeated by the "subagents can't spawn sub-subagents" runtime constraint.
   - **Stage 0 (skill-direct): Strict clarification gate.** Per honesty contract §8. Skip rationale must quote user-provided text.
   - **Stage 1 (skill-direct): Classification + sub-question planning.** Bounded coverage (honesty contract §9 — Patch S calibration): default **3** sub-questions for simple queries; **4–5** for typical multi-axis recommendation queries; **5–6** only for genuine triple-axis complexity. **Defaulting to 7–8 is over-decomposition** that produced the 2026-05-04 cost explosion. Each sub-question can own MULTIPLE option families (e.g., "local 8B–32B abliterated finetunes" is one sub-question covering Dolphin / Hermes / Magnum / Qwen3-abliterated / Llama-abliterated families together at 8 calls). Each sub-question records `must_cover_families` enumerating the option sub-classes; the §3 Comparison matrix enforces breadth at report level regardless of how many researchers cover it.
   - **Stage 2 (skill-direct): Forced recency pass FIRST + corpus density signal (Patch Y) + entity-version registry triangulation (Patch GG).** Skill runs `corpus_recent` / Glob+Grep filtered by frontmatter `date` within last 7 days. Results land in `recency_pass.json` BEFORE any subagent dispatches. The pass also computes a `corpus_density_signal` (`dense` / `moderate` / `thin`) from total corpus hits across the queries, which is passed to researchers so they can pre-allocate their 8-call budget between corpus and web instead of discovering corpus thinness independently. **If classification includes `entity_version` (Patch GG)**, the skill also invokes `ops/registry-query.sh <entity>` to triangulate across HuggingFace Hub + OpenRouter; the result is written into `recency_pass.json` under `entity_version_resolution`. When `source_agreement >= 2`, the registry-derived version is treated as authoritative for the §1 answer — researchers focus on context (capability, deployment, comparison) rather than re-discovering the version itself. Narrow scope: only `entity_version` queries route through registries; synthesis queries take the normal corpus path.
   - **Stage 3 (parallel fan-out): Researchers + contrarian in a single message.** N researchers (one per sub-question) and the contrarian (recommendation queries only) all dispatch concurrently via multiple `Agent` calls in one assistant message. Researchers receive `must_cover_families` and must surface ≥1 candidate per family OR explicitly mark a family as "no candidates exist." After the fan-out, the skill runs a **strengthened dispatch self-check (Patch K)**: not just file existence — also verifies the retrieval log has entries with `agent: researcher-<N>` (not only `skill-orchestrator`) and each researcher JSON has `dispatched_by: "subagent"`. Spurious "files exist because the orchestrator wrote them inline" passes are blocked. **Coverage check (Patch O)** also runs here: if any `must_cover_families` entry is unsatisfied across all researcher outputs, re-dispatch a focused researcher at gen2.
   - **Stage 4 (sequential): Synthesizer draft.** Reads latest-generation researcher + contrarian outputs + recency results + manifest. Writes `synthesizer-draft.md` using the required structure: §1 Conclusion (with **bolded recommendation + short reasoning + 2-4 runner-ups with one-line dismissal reasons** per Patch P) · §2 Confidence panel (Strongest evidence / Weakest assumption / What would change my mind / **Sources: corpus vs web ratio per Patch C — never mixes axes per Patch M** / **Plan usage: % of plan budget per Patch N**) · §3 Findings — opens with **`Comparison matrix` on recommendation queries with multiple named options (Patch G)**, ≥6 rows on multi-option queries · §4 Alternatives · §5 Open questions classified · §6 Citations (parsable structured list).
   - **Stage 5 (parallel fan-out): Citation verifier + fit verifier + structure verifier in a single message.** Three independent checks run concurrently. Citation verifier re-fetches every cited source. Fit verifier checks goal/constraint/category/implicit-constraint fit. **Structure verifier (Patch L)** validates §1–§6 conformance — runner-up block presence (Patch P), comparison matrix presence and ≥6 rows (Patch G), §5 tag discipline, §6 parsable list with ≥3 entries.
   - **Stage 6 (conditional): Re-dispatch on fit-verifier or structure-verifier `fail`.** Increment generation, re-spawn the appropriate stage. Cap: 1 fit re-dispatch + 1 structure re-dispatch per run.
   - **Stage 7 (sequential): Critic.** Reads draft + all three verifier outputs + retrieval log + manifest. Flags claim issues, coverage gaps, tag-discipline issues, open-question discipline issues. Writes `critic.md`.
   - **Stage 8 (sequential): Synthesizer final.** Integrates critic + all three verifier outputs. Computes the corpus/web sourcing metric (Patch C, exact format, Patch M anti-mixing rule) and the plan-usage metric (Patch N) from `retrieval_log.jsonl` + `manifest.json` token tally + `config/plan.yaml`. Tries one targeted WebSearch per `[research-target-dropped]` item to close it. **Mini-contrarian on the recommendation (Patch Z)**: before final write, internal red-team — 2-3 specific arguments AGAINST the recommendation; if any are strong enough, change the recommendation, otherwise surface them in §2 Weakest assumption / §4 Reframe. **Triangulation tag-finalization (Patch H + Patch AA source-quality penalty)**: `[verified]` requires verifier `pass` AND ≥2 independent *high-signal* inline sources; two SEO-aggregator sources count as one (apparent triangulation is illusory). Writes `reports/<run-id>.md`.
8. Skill prints **§1 Conclusion (with runner-ups) + §2 Confidence panel (with both metrics)** verbatim to terminal, plus path to full report and any flags. The runner-ups are part of §1 — they show up in the terminal automatically.
9. Total wall-clock: bounded coverage (honesty contract §9 — Patch X calibration). Simple factual queries: ~3–5 min, ~150–250K tokens. Typical recommendation queries: ~15–25 min, ~600–800K tokens. Triple-axis edge cases: ~25–35 min, ~800K–1M tokens. **Hard ceiling**: 1.2M tokens / 40 min wall-time. **5h Max window discipline**: a single run consuming >30% of the user's 5h plan window is a regression even if other budgets are met. The 2026-05-04 1h-17m / 2.4M-token run (with 8 researchers @ 30 tool uses each) was the over-rotation this calibration prevents — breadth doesn't require redundant triangulation across many researchers; one strong representative per option family is enough. Quality + breadth > speed; depth bounded.

Every subagent reads `.claude/honesty_contract.md` first. The contract enforces no-sycophancy, no-vibes, capitulation guard (recursive across messages), confidence-tag discipline (`[judgment]` requires a one-line rationale), permission to disagree with the user, "I don't know" branch, and three-pass loop cap with escalate-to-user as the preferred third option.

### Background (continuous, you don't see it)

- **systemd-timer** fires `ingest/run.py` every 15 min. `flock` on `corpus/.lock` ensures single-writer.
- `run.py` consults `config/sources.yaml` for due adapters, dispatches each, summarizes new items via Haiku, embeds via arctic-embed-s, writes markdown files + sqlite rows.
- Daily: `poll_authorities.py` runs (separate timer). Polls each authority's GitHub stars, arXiv author page, Reddit/HN username; records engagements.
- Daily: `health.py` checks adapter staleness; appends to NOTES.md if anything's silent for 2× its `poll_interval`.
- Weekly: `evals/run_all.py` runs the regression set against the system; writes `evals/runs/<week>-summary.md`.
- Monthly: `notes/rotate.py` archives last month's NOTES content.
- Monthly: source-discovery surfaces candidate new authorities/sources for review.

### When something breaks

- Adapter selector change → next ingestion run logs the failure → daily staleness alert → NOTES.md entry on next session start.
- sqlite-vec ABI mismatch → `make verify-sqlite` catches it pre-flight; documented fallback to numpy+pickle.
- Quota near-exhaustion → orchestrator's per-run token counter hits the cap → graceful stop with partial report.

---

## Tech stack with rationale

| concern | choice | why |
|---|---|---|
| Orchestration runtime | Claude Code (CLI) | covered by $200 Max; native subagents + skills + MCP |
| Lead orchestrator + research subagents | Sonnet 4.6 | published ~95% Opus quality at lower quota |
| Final synthesis on re-dispatch (conditional) | **Opus 4.6** (NOT 4.7) | only after a fit-verifier or structure-verifier failure triggers a second pass — the synthesizer earns Opus by needing a second chance, not by query complexity. Opus 4.7's MRCR v2 regression (78.3% → 32.2%) makes it worse than 4.6 at long-context multi-document synthesis. |
| Ingestion summarization | Haiku 4.5 | background, batch, cheap |
| Eval judge | Opus 4.7 | judge ≠ system under test |
| Embedding model | **snowflake-arctic-embed-s** (33M, 384-dim, Apache-2.0) | marginally better BEIR (51.98) than bge-small-en-v1.5 (51.68) at same size class; cleaner license; CPU-runnable |
| Vector store | **sqlite-vec brute-force `vec0` table**; numpy+pickle as fallback | ~0.5–1ms top-K at 50K × 384-dim brute force; pre-v1 but solid at this scale; numpy-pickle is the bail-out |
| Hybrid retrieval | **RRF (k=60)** over top-100 BM25 + top-100 vector; no score normalization | RRF outperforms min-max/z-score on hybrid (per arXiv 2508.01405) |
| Reranker | none in v1; `bge-reranker-v2-m3` later if evals demand | ~350ms/pair on CPU; defer until needed |
| Whisper variant | **faster-whisper** with `medium` model | ~4× realtime on CPU; 5 podcast hrs/week ≈ 1.25 CPU-hr |
| Process supervision | **systemd-timer** with `Persistent=true` | survives overnight shutdowns |
| Concurrency control | `flock` on `corpus/.lock` | single-writer guarantee |
| Schema validation | pydantic on frontmatter | catch malformed frontmatter at ingestion |
| Python toolchain | `uv` + `ruff` + `mypy` + pre-commit | per CLAUDE.md |

### Sources for the technical claims

- **Subagent semantics May 2026**: https://code.claude.com/docs/en/sub-agents.md, https://code.claude.com/docs/en/agent-teams.md, https://code.claude.com/docs/en/skills.md (sequential not parallel; `Agent` not `Task`; subagents can't spawn subagents; output is text-only)
- **arctic-embed-s vs bge-small**: https://huggingface.co/Snowflake/snowflake-arctic-embed-s (51.98 BEIR Apache-2.0) vs https://huggingface.co/BAAI/bge-small-en-v1.5 (51.68 BEIR MIT)
- **sqlite-vec status**: https://github.com/asg017/sqlite-vec/releases v0.1.9 March 2026; https://marcobambini.substack.com/p/the-state-of-vector-search-in-sqlite for latency benchmarks
- **RRF over score normalization**: https://arxiv.org/html/2508.01405v2
- **AINews migration**: https://news.smol.ai/ (replaced Buttondown)
- **faster-whisper performance**: https://github.com/SYSTRAN/faster-whisper

---

## Subagent topology

Seven specialists. **The skill (`.claude/skills/deep-ai-research/SKILL.md`) acts as the orchestrator** — it runs in main-conversation context where `Agent` dispatch actually works (Patch J). The previous `deep-ai-research-orchestrator` agent file is deprecated (in `.claude/agents/_archive/`) because subagents can't spawn sub-subagents. Each specialist agent has narrow `tools`, narrow `mcpServers`, narrow system prompt. **Every specialist reads `.claude/honesty_contract.md` first.**

### `deep-ai-research` skill (the dispatcher — formerly `deep-ai-research-orchestrator`)
- **runs in**: main conversation (not as a subagent)
- **available tools** (inherited from main convo): `Agent`, `AskUserQuestion`, `Read`, `Write`, `Edit`, `Glob`, `Grep`, `Bash`, `WebSearch` (used only for the recency pass — researchers handle stage-3 retrieval), corpus MCP
- **responsibilities**: strict clarification gate (contract §8); classification; sub-question planning with `must_cover_families` enumeration (coverage-first per contract §9 — 5-8 sub-questions for multi-option recommendation queries); scratch dir + manifest setup; forced recency pass; staged subagent dispatch; **strengthened dispatch self-check (Patch K)** — verifies scratch files exist AND retrieval log shows researcher agents AND each researcher JSON has `dispatched_by: "subagent"`; **coverage check (Patch O)** — re-dispatches researchers if any `must_cover_families` entry is unsatisfied; **fit-verifier and structure-verifier re-dispatches (capped 1 each)**; final report path; enforces raised token budget (400K input / 80K output for max-effort recommendation queries).

### `deep-ai-research-researcher` (the worker)
- **model**: `sonnet`
- **tools**: `Read`, `Glob`, `Grep`, `WebSearch`, `WebFetch`, `Write`
- **mcpServers**: `deep-ai-research-corpus`
- **system prompt**: receives one sub-question + scratch dir + clarifications + generation number; searches corpus first via `corpus-server.search` (RRF + authority + decay), then `WebSearch` if corpus is insufficient; **logs every retrieval call to `retrieval_log.jsonl`**; writes findings as JSON+markdown including per-claim `tag_hint` (verified|inferred|judgment) and `tag_rationale` for `judgment` tags.

### `deep-ai-research-contrarian` (the structural fix for the Karpathy-wiki failure)
- **model**: `sonnet`
- **tools**: `Read`, `Glob`, `Grep`, `WebSearch`, `WebFetch`, `Write`
- **mcpServers**: `deep-ai-research-corpus`
- **system prompt**: **independent retrieval** — receives only a one-line label of "the obvious answer" plus clarifications, NOT the full researcher findings. **Two passes**: (1) micro-contrarian always runs — finds niche-but-correct alternatives including finetune lineages; (2) macro-contrarian runs when the lead's recommendation has high cost/complexity/commitment — questions the framing. Authority + 90-day recency biased. Logs all retrieval to `retrieval_log.jsonl`.

### `deep-ai-research-verifier` (the structural fix for citation fabrication; aka *citation verifier*)
- **model**: `sonnet`
- **tools**: `Read`, `WebFetch`
- **mcpServers**: `deep-ai-research-corpus` (for `fetch_detail`)
- **system prompt**: reads the synthesizer's draft; for each cited claim, re-fetches the cited source; confirms the claim is in it. Writes `verifier.json` with `{claim, citation, status: pass|fail|inconclusive, evidence_excerpt}` per citation. Does **not** judge whether the right *kind of thing* is recommended — that's the fit verifier's job.

### `deep-ai-research-fit-verifier` (the structural fix for "right citations, wrong recommendation")
- **model**: `haiku` (Patch FF — model heterogeneity rule. PoLL paper verified: judge ensembles work because of model diversity, not count. Citation + structure verifiers stay on Sonnet 4.6; fit verifier on Haiku 4.5 introduces genuine model diversity at lower cost. Fit verification is goal/constraint/category checking — a pattern-matching task suited to Haiku's strength.)
- **tools**: `Read`, `Write`, `Glob`, `Grep`
- **mcpServers**: `deep-ai-research-corpus`
- **system prompt**: reads the draft + manifest (with clarifications) + (optional) contrarian output. **Runs in parallel with the citation verifier and structure verifier**; does NOT depend on `verifier.json` or `structure_verifier.json`. Checks four dimensions: **goal fit**, **constraint fit**, **category fit**, **implicit-constraint fit**. On `fail`, returns `right_category_hint` + `rerun_guidance` to the skill (which re-dispatches at gen2). Does not fix the report itself.

### `deep-ai-research-structure-verifier` (NEW — Patch L — the structural fix for "synthesizer self-validates past spec")
- **model**: `sonnet`
- **tools**: `Read`, `Write`
- **mcpServers**: none
- **system prompt**: reads the synthesizer draft + manifest. **Runs in parallel with citation verifier and fit verifier**. Validates §1–§6 conformance per the spec: §1 has bolded recommendation + reasoning + 2-4 runner-ups with dismissal reasons (Patch P); §2 has all four sub-bullets including correctly-formatted Sources metric (Patch C/M anti-mixing) and Plan-usage sub-bullet (Patch N); §3 opens with Comparison matrix on multi-option queries with required base columns Option/What-it-is/Decision/Why and ≥6 rows (Patch G + coverage-first); §5 items carry exactly one of `[user-clarification]` / `[research-target-dropped]` / `[external-event]`; §6 is a parsable structured list with ≥3 entries. On `fail`, returns per-section repair guidance to the skill (which re-dispatches the synthesizer-draft at gen2; cap 1). Replaces the synthesizer's own pre-write self-check (Patch F-light) which kept being bypassed when the synthesizer's context was the same context that made the violation.

### `deep-ai-research-critic` (the structural fix for missing perspectives + retrieval coverage gaps)
- **model**: `sonnet`
- **tools**: `Read`
- **mcpServers**: none (works only from scratch dir)
- **system prompt**: reads draft + verifier.json + fit_verifier.json + retrieval_log.jsonl + manifest.json; flags unsupported claims, missing counter-positions, stale citations, reasoning gaps, **coverage gaps from the retrieval log** (e.g. "no subagent searched the finetune-lineage angle"), tag-discipline issues (bare `[judgment]` without rationale, `[verified]` on a verifier-failed claim). Writes `critic.md` with three buckets: `claim issues`, `coverage gaps`, `tag-discipline issues`.

### `deep-ai-research-synthesizer` (the writer)
- **model**: `sonnet` for both passes by default (Patch V calibration). **Opus 4.6 (NOT 4.7)** reserved for the post-re-dispatch synthesizer pass — Opus 4.7 has a documented MRCR v2 long-context retrieval regression (78.3% → 32.2%, BenchLM.ai 2026) that hurts multi-document synthesis specifically. The synthesizer earns Opus 4.6 by failing the first attempt (fit-verifier or structure-verifier triggered redo). Default-Opus 4.7 on first pass cost ~3× more for marginal/negative gain in the 2026-05-04 1h-17m run.
- **tools**: `Read`, `Write`, `WebSearch` (for the recency-double-check + dropped-target follow-up), `Glob`, `Grep`
- **mcpServers**: `deep-ai-research-corpus` (for `recent` to check freshness)
- **system prompt**: reads only **latest-generation** researcher and contrarian outputs (`*-gen<G>.json` where `<G>` is highest present). Assembles the final report using the **fixed structure**: §1 Conclusion (with **top recommendation bolded + 1-3 sentences of reasoning + 2-4 runner-ups, each named with a one-line dismissal reason — Patch P**) · §2 Confidence panel (Strongest evidence / Weakest assumption / What would change my mind / **Sources: corpus vs web ratio computed from retrieval_log + citations per Patch C; never mixes corpus-vs-web with confidence-tier-vs-judgment per Patch M; with malformed-log degraded-integrity caveat per Patch I** / **Plan usage: % of plan budget per Patch N from `config/plan.yaml` + manifest token tally**) · §3 Findings — **opens with a `Comparison matrix` on recommendation queries with multiple named options (Patch G — required base columns: Option / What-it-is / Decision / Why; plus 2–4 query-specific columns; ≥6 rows on multi-option queries per coverage-first)**, then sub-question prose with mandatory `[verified]/[inferred]/[judgment: <rationale>]` tags inline · §4 Alternatives considered and rejected (within-frame + reframe subsections) · §5 Open questions (each item classified `[user-clarification]` / `[research-target-dropped]` / `[external-event]`) · §6 Citations (parsable structured list, ≥3 entries — inline `[verified — source]` text does NOT substitute). **Recency double-check rule**: cited sources older than 6 months on fast-moving topics trigger a `WebSearch` to verify nothing newer supersedes. **Dropped-target follow-up**: on the second pass, each `[research-target-dropped]` item gets one targeted WebSearch attempt; if it resolves, the item moves into §3 with a citation. Two-pass: draft → (citation + fit + structure verifiers run in parallel, then critic) → final. Tag-finalization on second pass: verifier `pass` AND ≥2 independent inline sources → `[verified]`; verifier `pass` BUT only 1 source → downgrade to `[inferred]` (Patch H triangulation rule); verifier `inconclusive` → `[inferred]`; verifier `fail` → drop or replace. Structural conformance is now externally validated by `deep-ai-research-structure-verifier` (Patch L); the synthesizer's own pre-write self-check (Patch F-light) remains as a defensive belt + suspenders.

---

## Ingestion mechanics

### Adapter contract

Every adapter implements:

```python
class Adapter(Protocol):
    name: str
    poll_interval_seconds: int
    rate_limit_key: str    # for shared limiter

    def iter_new(self, since: datetime) -> Iterable[RawSource]: ...
    def detect_engagements(self, raw: RawSource) -> Iterable[Engagement]: ...
```

Adapters yield raw records; `ingest/run.py` handles canonicalization → dedup → summarization (Haiku) → chunking (versioned) → embedding (arctic-s) → frontmatter generation → file write → engagement record write → sqlite update. Adapters never touch the DB or filesystem directly.

### Frontmatter schema (pydantic-validated)

```yaml
---
source_id: "smol-ai-news-2026-04-15"        # sha256(canonical_url)[:16] preferred
source_type: "newsletter"
publication: "Smol AI News"
url: "https://news.smol.ai/issues/26-04-15-..."
canonical_url: "https://news.smol.ai/issues/26-04-15-..."  # strips tracking params
date: "2026-04-15"
authors: ["smol-ai"]
authorities_engaged: []                       # [{authority_id, kind}]
mentioned_entities: ["DeepSeek V4", "Karpathy LLM Wiki"]
mentioned_authorities: ["karpathy", "tri_dao"]
tags: ["releases", "discord-summary"]
ingested_at: "2026-04-15T08:00:00Z"
content_hash: "sha256:abc..."                 # for revision detection
revision: 1
parent_id: null                               # set on revision >= 2
chunker_version: "v1"
embed_model: "snowflake-arctic-embed-s"
embed_dim: 384
---
```

### Stable IDs and revisions

- `source_id = sha256(canonical_url)[:16]`
- Re-ingesting same URL with same content → no-op (update `ingested_at` only)
- Re-ingesting same URL with new `content_hash` → insert new row with `revision=2`, `parent_id=<original>`. Old revision preserved for audit.

### sqlite schema (the only DB tables)

```sql
-- Engagement edges (the moat data)
CREATE TABLE engagements (
    id INTEGER PRIMARY KEY,
    authority_id TEXT NOT NULL,            -- matches config/authorities.yaml id
    source_id TEXT NOT NULL,
    kind TEXT NOT NULL,                    -- author|retweet|star|fork|...
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,                         -- JSON
    UNIQUE(authority_id, source_id, kind)  -- idempotent
);
CREATE INDEX idx_engagements_source ON engagements(source_id);
CREATE INDEX idx_engagements_authority ON engagements(authority_id, recorded_at DESC);

-- Embeddings (one per chunk; multi-chunk docs allowed)
CREATE VIRTUAL TABLE embeddings USING vec0(
    chunk_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding float[384]
);

-- Chunker/model version pins
CREATE TABLE pin_versions (
    name TEXT PRIMARY KEY,        -- 'chunker' | 'embed_model'
    value TEXT NOT NULL,
    pinned_at TIMESTAMP NOT NULL
);

-- Adapter health
CREATE TABLE adapter_health (
    adapter_name TEXT PRIMARY KEY,
    last_success_at TIMESTAMP,
    last_error_at TIMESTAMP,
    last_error_message TEXT,
    consecutive_failures INTEGER NOT NULL DEFAULT 0
);

-- Cost ledger (for the per-run token budget)
CREATE TABLE run_costs (
    run_id TEXT PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    finished_at TIMESTAMP,
    finish_reason TEXT
);
```

### Authority engagement detection

Per-authority `handles` in `authorities.yaml` drive what we poll. `poll_authorities.py` runs daily:

| handle type | what we poll | how often | cadence reason |
|---|---|---|---|
| `github` | `GET /users/{handle}/starred?per_page=50` (paginated until we hit a previously-seen star) | daily | star activity is bursty but not per-minute |
| `github` | `GET /users/{handle}/events/public` (commits, issues, PRs) | daily | events feed gives 90 days of history |
| `arxiv_id` | author search via OpenAlex API or `https://arxiv.org/a/{handle}` HTML | weekly | new papers are rare per-author |
| `reddit_username` | `GET /user/{name}/submitted` via PRAW (read-only) | daily | post cadence is human-scale |
| `hn_username` | Algolia search `author:{name}` | daily | low-volume |
| `twitter_handle` | DEFERRED in v1 | — | accept the gap |
| newsletter author | mention-detection during summarization (Haiku asked: "Does this content link to or mention any of [authority list]?") | per-ingestion | inline at summary time |
| podcast guest | parsed from RSS metadata `<itunes:episode><guests>` if available; otherwise summarizer extracts | per-ingestion | inline |

Each engagement is upserted into the `engagements` table — `UNIQUE(authority_id, source_id, kind)` ensures idempotency. New authority added to YAML → run `python -m ingest.backfill_authority <handle>` to scan recent corpus and add historical engagement records.

### Authority handle drift

Twitter handles change. Add `aliases` field to `authorities.yaml` entries:

```yaml
- name: Andrej Karpathy
  weight: 1.0
  tier: canonical
  handles:
    twitter: karpathy
    github: karpathy
  aliases:
    twitter: ["karpathy_old"]
    github: []
```

Pollers consult both current handle and aliases. Engagements are recorded against the canonical `name`, not the handle.

---

## Retrieval mechanics

### `corpus-server` MCP tools (4 total — keep it minimal)

```
search(query: str, filters: dict) -> list[Hit]
    # Hybrid: top-100 ripgrep BM25 + top-100 vector cosine, RRF k=60.
    # Apply authority_boost = min(4.0, 1 + Σ engagement_weights), recency_decay per-content-type.
    # Filters: since/until, source_types, authors, min_authority_boost, entity_ids.
    # Returns: list of {source_id, path, frontmatter, score, snippets}.

find_by_authority(authority_id: str, since: str | None) -> list[Hit]
    # SELECT source_id FROM engagements WHERE authority_id = ? AND recorded_at >= ?
    # Returns full hit metadata including frontmatter excerpt.

recent(topic: str | None, hours: int) -> list[Hit]
    # Hard recency filter: published_at >= now() - hours.
    # If topic provided, applies vector similarity within that window.
    # Powers the forced recency pass.

fetch_detail(source_id: str) -> dict
    # Returns full markdown content + frontmatter for a source.
    # Used by verifier to re-check citations.
```

Subagents call these via MCP; orchestrator can also call them directly. No other corpus-access entry points — keeps the contract narrow.

### Ranking formula (the moat algorithm — pinned in writing)

```
candidates = top_100_bm25(query) ∪ top_100_vector(query)   # union, dedup by source_id
rrf_score(d)        = 1/(60 + bm25_rank(d)) + 1/(60 + vec_rank(d))
authority_boost(d)  = min(4.0, 1 + Σ_{(a, kind) ∈ engagements(d)} weight(a) * kind_weight(kind))
recency_decay(d)    = exp(-ln(2) * age_days(d) / half_life(content_type(d)))
final(d)            = rrf_score(d) * authority_boost(d) * recency_decay(d)
return top_N by final, dedup by mentioned_entities at synthesis time
```

Half-lives in `config/decay.yaml`:

```toml
[half_lives_days]
tweet = 7              # for future use; deferred in v1
hn_post = 14
reddit_post = 14
newsletter_issue = 60
blog_post = 60
lab_blog_architecture = 180
arxiv_paper = 365
podcast = 90
hf_daily_papers = 30
benchmark_snapshot = "most-recent-wins"
```

Engagement kind weights (in code, not config):

| source | kind | weight |
|---|---|---|
| github | commit_author, pr_author | 1.0 |
| github | star, fork | 0.5, 0.4 |
| github | issue_open, review | 0.3, 0.6 |
| github | watch | 0.0 (rejected — too noisy) |
| arxiv | author | 1.0 |
| arxiv | cited_by_tracked | 0.6 |
| reddit | post_author, comment_top_level | 1.0, 0.4 |
| hn | post_author, comment_top_level | 1.0, 0.4 |
| newsletter | author, mentioned_with_link | 1.0, 0.5 |
| podcast | guest, host | 1.0, 0.7 |

---

## The four mechanisms that solve the failure modes

1. **Authority-engagement boost in retrieval** — content tagged with `authorities_engaged` gets a multiplier capped at 4×. Prevents "Karpathy retweeted X" from being lost in SEO noise.

2. **Per-content-type time decay** — half-lives in `config/decay.yaml`. A 1-day-old tweet vs. 14-day-old at equal base score: tweet ranks ~3.6× higher.

3. **Forced contrarian subagent** — first-class part of the loop on recommendation queries. Its prompt is *"Find the answer the lead agent will miss."* Structural answer to the SEO bias.

4. **Forced recency pass** — every research run includes a `corpus.recent(topic, hours=168)` sweep regardless of query phrasing. Wired into the orchestrator, not optional.

---

## Eval framework

### Cases (seeded in `evals/cases.yaml`)

Five seed cases exist; pattern is **behavioral over content** to avoid bit-rot:

```yaml
- id: recency_deepseek_latest
  category: recency
  query: "What is the most recent DeepSeek model and when was it released?"
  expected_behavior:
    - recency_pass_fired: true              # verified via run trace
    - cites_source_within_days: 30
    - cited_source_mentions_pattern: "DeepSeek"
    - judge_check_live: true                # judge does WebSearch to validate version
  blocked_until: step_3_tier1_ingestion
```

The **judge** (Opus 4.7) reads:
- the query
- the system's full report (with citations)
- the run trace (subagent invocations, tool calls — for behavioral assertions)
- optionally does its own WebSearch to ground-truth the answer

Judge produces a structured score: pass/fail per behavioral criterion + a freeform critique.

### Run trace format

`.claude/scratch/<run-id>/` during a run; moved to `evals/runs/<run-id>/` after:

```
evals/runs/<run-id>/
├── manifest.json              # query, classification, clarifications, sub_questions, redispatches, finished_at, finish_reason
├── orchestrator.log           # what orchestrator decided when
├── researcher-1-gen1.{md,json}   # findings + raw search results; -gen<G> tags re-dispatch generation
├── researcher-2-gen1.{md,json}
├── researcher-3-gen1.{md,json}
├── researcher-1-gen2.{md,json}   # only present if fit-verifier triggered a re-dispatch
├── contrarian-gen1.{md,json}     # underrated answers; micro + (when warranted) macro pass
├── contrarian-gen2.{md,json}     # only present if re-dispatch repointed the contrarian
├── recency_pass.json             # the forced recency sweep result
├── retrieval_log.jsonl           # one JSON line per retrieval call across all agents — used by critic for coverage gaps
├── synthesizer-draft.md          # first draft (uses latest-generation researcher/contrarian outputs only)
├── verifier.json                 # citation verifier — per-citation pass/fail/inconclusive
├── fit_verifier.json             # fit verifier — per-dimension pass/fail and re-dispatch hints
├── critic.md                     # critique with three buckets: claim issues, coverage gaps, tag-discipline
├── synthesizer-final.md          # final report (also copied to reports/)
└── tokens.json                   # input/output token tally per role
```

Eval framework reads `manifest.json` + `tokens.json` + `retrieval_log.jsonl` for behavioral assertions ("did recency pass fire?", "did the orchestrator call AskUserQuestion?", "did the contrarian's queries actually differ from the lead's?", "did the fit verifier trigger a re-dispatch?", "are there at least 3 distinct citations?", "did verifier reject anything?"). The current `evals/run_all.py` is retrieval-layer-only; full-loop trace assertions are tracked under `blocked_until: full_loop_eval_harness` in `cases.yaml`.

### Cadence

- Weekly: `evals/run_all.py` runs all unblocked cases and writes `evals/runs/<week>-summary.md`
- Score history: tracked in `evals/runs/_history.jsonl` (append-only)
- Regression alert: if a previously-passing case starts failing, NOTES.md gets an entry on the next session start

---

## Operational concerns

### Where corpus/ lives

Default: `./corpus/` inside the repo, **gitignored**. Path configurable via `config/paths.yaml` if user wants it elsewhere (e.g., `~/research-corpus/`). Rationale: keeps the codebase repo small, avoids huge git-history bloat, but allows the user to point at a separate disk if needed.

### Backup strategy

What gets backed up (small, irreplaceable):
- `config/authorities.yaml` (the moat)
- `config/sources.yaml`, `config/decay.yaml`, `config/paths.yaml`
- `evals/cases.yaml`
- `evals/runs/_history.jsonl`
- `reports/*.md`
- Codebase (committed via git, pushed to GitHub)

What doesn't need backup (rebuildable):
- `corpus/*.md` — re-ingestable from RSS/APIs
- `corpus/_index.sqlite` — re-derivable from corpus markdown + re-running engagement polling

`make backup` target tarballs the critical files to `~/backup/deep-ai-research-YYYY-MM-DD.tar.gz`. Cron monthly.

### Concurrency control

`ingest/run.py` acquires exclusive `flock` on `corpus/.lock` at start. If can't acquire (previous run still going), exits silently — next timer tick picks up. Single-writer guarantee.

`poll_authorities.py` uses a separate lock (`corpus/.poll.lock`) since it can run alongside ingestion safely (different DB tables).

The `corpus-server` MCP server opens sqlite in read-only mode by default; write operations from MCP are limited to the cost ledger.

### NOTES.md rotation

`NOTES.md` accumulates entries for the current month. Monthly cron task `notes/rotate.py`:
- Renames `NOTES.md` to `notes/archive/NOTES-YYYY-MM.md`
- Creates fresh `NOTES.md` with a header pointing to archive
- CLAUDE.md references `NOTES.md` (always current), not the archive

### Cron alternative on Pop!_OS

`systemd-timer` with `Persistent=true` is the right primitive on Pop!_OS. Sample units in `ops/`:

```ini
# ops/ingest.timer
[Unit]
Description=deep-ai-research ingestion run

[Timer]
OnBootSec=2min
OnUnitActiveSec=15min
Persistent=true                    # catches missed runs after wake-from-sleep

[Install]
WantedBy=timers.target
```

Setup: `systemctl --user enable --now ingest.timer`.

### Cost cap mechanics

Anthropic doesn't expose remaining-quota. Approximation:
- Orchestrator maintains a per-run token tally in `run_costs` table
- Subagent token usage estimated from input message length + heuristic for output (typically 5-30K)
- Per-run cap defaults to 250K input + 50K output tokens (~$1–2 of API equivalent under Max plan terms)
- Cap exceeded → orchestrator stops dispatching new subagents, finalizes synthesis with what it has, marks `finish_reason='cost_cap'`

This is approximate but prevents runaway. Real defense is the user's discipline + the ~30min/wk maintenance pattern.

### Setup credentials needed

Free tier all of these:

| credential | what it's for | where to get | rate limit |
|---|---|---|---|
| GitHub PAT | authority engagement polling, GitHub MCP | github.com/settings/tokens | 5K/hr authenticated |
| HuggingFace token | HF Daily Papers, future model downloads | huggingface.co/settings/tokens | 100K/mo Inference credits |
| Reddit app | r/LocalLLaMA, r/MachineLearning ingestion | reddit.com/prefs/apps | 100 QPM with OAuth |
| Anthropic | covered by $200 Max plan | already have it | per Max plan terms |

Stored in `.env` (gitignored). `.env.example` checked in.

---

## Sources to ingest

### Tier 1 — first 4 newsletters (build first)

1. **Smol AI / AINews** — `https://news.smol.ai/` — daily, summarizes top AI Discords / Reddits / X. Tier-1 because it partially compensates for no Twitter ingestion.
2. **Import AI** (Jack Clark) — weekly, research + policy.
3. **TLDR AI** — daily, model releases / research / launches / funding in 5-min reads.
4. **Last Week in AI** — weekly, comprehensive summary.

### Tier 2 — remaining newsletters

5. **Interconnects** (Nathan Lambert) — open-models tracking, RL post-training. RSS: `https://www.interconnects.ai/feed`
6. **The Batch** (DeepLearning.AI / Andrew Ng) — weekly research + policy
7. **Ahead of AI** (Sebastian Raschka) — practitioner depth
8. **Eugene Yan** — applied ML systems, blog RSS
9. **Simon Willison** — daily LLM blog, RSS
10. **Lilian Weng** — deep technical blog posts
11. **Chip Huyen** — ML systems blog
12. **The Gradient** — technical essays
13. **Deep Learning Weekly** — engineering-focused
14. **AlphaSignal** — engineer-focused brief
15. **Davis Summarizes Papers** — paper digests

For each: verify RSS feed exists at setup time. Substack-hosted ones reliably have RSS at `<base>/feed`. If a newsletter goes paid-only, mark it deferred and continue with the others.

### Lab blogs (~30, persisted entirely via RSS)

Anthropic, OpenAI, DeepMind, Meta AI, Mistral, Cohere, AI2, EleutherAI, DeepSeek, Qwen/Alibaba, Moonshot/Kimi, xAI, Inflection, Adept, Reka, Together AI, Stability AI, NVIDIA AI Research, Microsoft Research, Apple ML Research, Google AI Blog, HuggingFace, Mosaic/Databricks, Replicate, Modal, vLLM, Cerebras, Groq, Lightning AI, Anyscale.

`config/sources.yaml` lists each with RSS URL + cadence. Failures during setup mark adapter inactive; user can retry monthly.

### Reddit (PRAW, read-only)

- `r/LocalLLaMA` — titles + top-thread summary
- `r/MachineLearning` — titles + top-thread summary

### Hacker News (Algolia API, free)

AI-keyword filtered firehose (keywords: `LLM`, `transformer`, `Claude`, `GPT`, `attention`, `embedding`, `vector`, `RAG`, `agent`, …). Persist titles + top-comment summary.

### HuggingFace Daily Papers

Curated daily list at `https://huggingface.co/papers`. The HF API exposes daily papers programmatically (`hf_hub_api.list_daily_papers(date=...)`). Persist as a single index file per day plus a stub-summary per paper; full text NOT persisted unless paper hits promotion threshold.

### Podcast transcripts (faster-whisper, medium model)

- Latent Space
- Dwarkesh Podcast
- Machine Learning Street Talk (MLST)
- No Priors
- Cognitive Revolution

Adapter: download new episodes via RSS → transcribe with faster-whisper medium → summarize with Haiku → write markdown. Run as daily batch (overnight if heavy day).

### Promoted arXiv papers

Ingestion threshold: an arXiv paper gets promoted to a corpus entry (with full summary) when **any** of:
- cited by an authority (via OpenAlex citation graph)
- mentioned in 2+ tracked newsletters
- has an associated GitHub repo with >100 stars
- manually flagged by user via `python -m ingest.promote <arxiv_id>`

Otherwise: NOT persisted. Live arXiv search via `WebSearch` covers ad-hoc lookups.

### Benchmark snapshots

Per-benchmark adapter scrapes JSON if available (LMArena GitHub data, Artificial Analysis endpoints, HF leaderboards as datasets) or falls back to `WebFetch` for rendered-only sites. Snapshot files: `corpus/benchmarks/<benchmark>/<YYYY-MM-DD>.json`. Tracked: LMArena, Artificial Analysis, OpenRouter, LiveBench, GPQA Diamond, HLE, SWE-bench Verified, Aider Polyglot.

### Live-query only (NOT persisted)

- arXiv search beyond promoted papers — Claude Code subagent calls arXiv API or WebSearch
- HuggingFace model/dataset search beyond Daily Papers — `WebSearch` or HF API
- GitHub ad-hoc repo search — `WebSearch` or GitHub API
- General web — Claude Code's `WebSearch` and `WebFetch` (covered by Max plan)

### Deferred (not in v1)

- Twitter/X via any path. Accept ~12–36hr delay; rely on Smol AI / Reddit / HN as the proxy. Re-evaluate when X landscape settles.

---

## Build order

Each step has a **done-when** condition and a clear next step. Don't skip ahead.

### Step 0 — Reconcile docs (immediate)
Update or remove the existing `docs/*` (Postgres-era; mostly wrong). Trim CLAUDE.md to point at this PLAN.md and the docs/* that survive.
- **done when**: `docs/` reflects markdown-first architecture; CLAUDE.md ≤80 lines; no contradictions between PLAN.md and docs/*

### Step 1 — Skeleton + 4 newsletter adapters
- `pyproject.toml` (uv-managed, ruff/mypy/pytest)
- `config/{authorities,sources,decay,paths}.yaml` filled with seed values
- `ingest/run.py`, `ingest/canonicalize.py`, `ingest/frontmatter.py`, `ingest/summarize.py`, `ingest/chunk.py`
- `ingest/adapters/{ainews,import_ai,tldr_ai,last_week_ai}.py`
- Smol AI / AINews adapter built **first** — it's the highest-value Tier-1 source
- `make verify-sqlite` script
- **done when**: `python -m ingest.run` writes valid markdown files to `corpus/newsletters/` for the 4 sources; frontmatter validates; idempotent re-runs change nothing

### Step 2 — Embedding sidecar
- `ingest/embed.py` (snowflake-arctic-embed-s, ONNX preferred)
- sqlite-vec table created (`vec0` virtual)
- `pin_versions` table records chunker_version and embed_model
- numpy+pickle fallback path documented in `ops/embed-fallback.md`
- **done when**: every markdown file in `corpus/` has corresponding chunk embeddings in sqlite; ABI verified

### Step 3 — Authority graph + engagement tagging
- `config/authorities.yaml` populated (start with the 24 seeds we already have, expand to 50+)
- `ingest/poll_authorities.py` for GitHub stars + events, Reddit, HN, OpenAlex
- Newsletter mention-detection added to `ingest/summarize.py` (Haiku prompt)
- `engagements` table populated
- **done when**: querying `engagements` for `karpathy` since last 30 days returns ≥1 row from real polled data

### Step 4 — Skill + orchestrator + researcher
- `.claude/skills/deep-ai-research/SKILL.md`
- `.claude/agents/{orchestrator,researcher}.md`
- `.claude/scratch/` directory + per-run dispatch
- `mcp/corpus-server/server.py` with `search`, `find_by_authority`, `recent`, `fetch_detail`
- Orchestrator implements RRF + authority + decay ranking
- **done when**: `claude` → `/deep-ai-research <query>` runs end-to-end against the partial corpus, returns a cited report saved to `reports/`

### Step 5 — Eval skeleton + 5 seed cases
- `evals/cases.yaml` already seeded
- `evals/run_all.py` invokes `claude -p "/deep-ai-research <query>"` per case (or programmatic Claude Agent SDK), captures the run trace from `evals/runs/<run-id>/`
- Judge (Opus 4.7) scores behavioral criteria
- All 5 cases will fail or be marked `blocked_until`. **That's the point** — we now have an objective signal of progress.
- **done when**: `python -m evals run_all` produces `evals/runs/<week>-summary.md` with per-case pass/fail/blocked

### Step 6 — Specialist subagents + forced passes
- `.claude/agents/deep-ai-research-{orchestrator,researcher,contrarian,verifier,fit-verifier,critic,synthesizer}.md` + `.claude/honesty_contract.md`
- Orchestrator dispatches in stages: clarification gate (strict, contract §8) → classification → recency-pass FIRST (orchestrator-direct, the ONLY orchestrator-direct retrieval allowed per Patch E) → parallel fan-out: researchers + contrarian (multi-Agent in one message; orchestrator verifies expected output files exist, retries on miss per Patch E.3) → synthesizer-draft (with Comparison matrix on multi-option recommendation queries per Patch G) → parallel fan-out: citation-verifier + fit-verifier (multi-Agent in one message) → fit-verifier re-dispatch on fail (capped at 1) → critic (with retrieval-log coverage check + open-question discipline) → synthesizer-final (Patch H triangulation: `[verified]` requires ≥2 independent sources; Patch F-light pre-write structural check; corpus/web sourcing metric with Patch I malformed-log handling; attempts to close `[research-target-dropped]` items)
- Forced recency pass wired
- Counter-position pass on recommendation queries
- Honesty contract referenced by every subagent
- Retrieval log written to scratch by all retrieval-tool callers
- **done when**: re-run evals — recency case improves; contrarian case shows underrated alternatives; verifier catches a deliberately-fabricated citation in a synthetic test; fit-verifier catches an injected category mismatch and triggers re-dispatch

### Step 7 — Lab blog + Reddit + HN + HF Daily Papers ingestion
- Adapters for ~30 lab blogs
- Reddit PRAW adapter (with OAuth setup script)
- HN Algolia adapter
- HF Daily Papers adapter
- **done when**: corpus contains real data from all four; `health()` reports green for all adapters

### Step 8 — Benchmarks subsystem
- Adapters for LMArena, Artificial Analysis, OpenRouter, LiveBench, GPQA, HLE, SWE-bench Verified, Aider Polyglot
- Benchmark snapshots stored as timestamped JSON
- `corpus-server` exposes benchmark queries (alongside main `search`)
- **done when**: benchmark eval case passes ("What's Claude Opus 4.7 ELO on LMArena?")

### Step 9 — Promoted arXiv pipeline
- Detection: cited by authority (OpenAlex), mentioned in 2+ newsletters, GitHub-repo-with-100-stars heuristic
- Promotion job: full PDF → text → summary → corpus markdown
- **done when**: at least 5 promoted papers have full corpus entries

### Step 10 — Podcast transcripts
- `ingest/adapters/podcasts.py` with faster-whisper medium
- Run as overnight batch
- **done when**: latest episodes of 5 tracked podcasts have transcripts in corpus

### Step 11 — Eval growth + weekly cadence
- Add 5–15 more eval cases across all 5 categories
- Weekly automated runs via systemd-timer
- Score-history graphing (simple matplotlib script if useful)
- **done when**: 4-week trend visible in `evals/runs/_history.jsonl`

**Defer indefinitely**: Twitter/X, Postgres migration, langchain, Brave/SearXNG, dedicated reranker, Agent Teams.

---

## Verification approach

**Integration smoke tests** (committed in `tests/`):
- `test_ingest_idempotency.py` — re-running ingestion against a fixture changes nothing
- `test_ranking_invariants.py` — synthetic corpus where authority-engaged docs provably rank above un-engaged at equal base score; recency decay measurable
- `test_frontmatter_schema.py` — pydantic catches malformed frontmatter
- `test_engagement_dedup.py` — `UNIQUE(authority_id, source_id, kind)` upholds
- `test_corpus_server_mcp.py` — all 4 MCP tools return expected shapes against fixture

**End-to-end smoke test**:
- `make smoke` → spin up corpus with 10 fixture docs → run a known-good `/deep-ai-research` query → assert non-empty report with ≥2 citations

**Eval set is the merge gate**: `python -m evals run_all` is the canonical "is the system working" signal. Regressions block merges (when there is a CI; for now, manual discipline).

---

## Open questions (small, post-approval cleanup)

1. **Corpus location** — default `./corpus/` gitignored is my assumption. Override if you want it elsewhere (e.g., `~/research-corpus/` so multiple repos share it).
2. **Authority handle expansion** — current `authorities.yaml` has 24 seeds. Grow to ~50 before Step 3 ships, or ship and grow incrementally?
3. **Promoted-arXiv full-text storage** — keep PDF + text + summary, or summary-only? My default: text + summary; skip PDF (re-fetchable).
4. **Podcast cadence** — overnight batch is fine for me to assume, but you might prefer weekly batch. Either works.
5. **Backup target** — `~/backup/` is my assumption. Override if you have a specific location (NAS, external drive path).

These are small enough I can default reasonably and you can override if you disagree. I won't block on them.

---

## Decisions log (what changed across the iterations)

| concern | original CLAUDE.md | post-Pass-1 plan | final plan (this doc) | reason |
|---|---|---|---|---|
| Storage | Postgres + pgvector + Alembic | (same) | markdown + sqlite + sqlite-vec | corpus is 25–50K docs over 5yr — not a relational-DB problem; Claude Code's file tools work directly on markdown |
| Loop framework | hand-built around Claude Code | hand-built around Claude Code | native `.claude/skills/` + `.claude/agents/` | Skills are the recommended pattern in 2026 |
| Subagent fan-out | "parallel" assumed | sequential (Agent Teams deferred) | **parallel where independent** (multi-Agent calls in single message) | Pass-2 research was outdated — Claude Code runtime supports concurrent execution when multiple Agent calls land in one assistant message. Stages 2 (researchers+contrarian) and 4 (citation+fit verifiers) parallelize; sequential dependencies (draft → verify, verify → critic, critic → final) preserved |
| Embedding model | bge-large-en-v1.5 | Qwen3-Embedding-0.6B | **snowflake-arctic-embed-s** (33M, 384-dim) | corpus too small for big models; arctic beats bge-small on BEIR with cleaner license |
| Live web | Brave + Firecrawl MCPs | SearXNG | **Claude Code's native WebSearch + WebFetch** | covered by $200 Max; no extra cost |
| Twitter | Tier 3 (build last) | $12/mo Apify or Nitter | **deferred indefinitely** | X landscape too unstable; AINews/Reddit/HN are proxies |
| Smol AI / AINews | bundled with newsletters | bundled | **Tier 1, build first** | partially compensates for no Twitter |
| Contrarian | counter-position pass implicit | first-class subagent | first-class subagent + structural prompt | the actual structural answer to the Karpathy-wiki failure |
| Tool name | `Task` | `Task` | **`Agent`** | renamed in v2.1.63 |
| Slash command | `.claude/commands/` | `.claude/commands/` | **`.claude/skills/`** | recommended in 2026 |
| Process supervision | Docker Compose worker | cron | **systemd-timer with Persistent=true** | survives overnight shutdowns |
| Vector lib | pgvector HNSW | sqlite-vec HNSW | **sqlite-vec brute-force `vec0`** | brute force at 50K is sub-ms; ANN buys nothing at this scale |
| Hybrid retrieval | unspec'd | "RRF" | **RRF k=60, no normalization, top-100 each side** | RRF beats min-max/z-score on hybrid (arXiv 2508.01405) |
| Cost cap | $5/run dollars | per-run quota | **per-run token budget (~250K input + 50K output)** | Anthropic doesn't expose remaining-quota; estimate is good enough |
| Re-embedding | "pin and never change" | "pin and never change" | **plan for every 12–18mo** | small embedding models improve 1–3 MTEB pts/yr; chunker version pinned alongside model |
| Subagent output | unspec'd | freeform text | **structured payloads in `.claude/scratch/<run-id>/`** | subagents return text only; scratch dir bypasses limitation |

---

## What's NOT in this plan (scope discipline)

- Web UI, mobile, multi-user, accounts, SSO
- Cost dashboards beyond the per-run ledger
- Notifications / email / push (NOTES.md is the alert surface)
- A "general-purpose" deep-research tool — this is AI/ML-domain-specific by design
- Real-time / streaming retrieval — batch ingestion + on-demand research
- A custom reranker model (deferred until evals demand)
- Twitter/X (deferred indefinitely)
- Postgres, pgvector, Alembic, Docker Compose for the DB, langchain (rejected)

---

## Maintenance commitment

~30 minutes/week:
- Review `config/authorities.yaml` for adds/drops
- Skim NOTES.md for source breakages
- Read latest `evals/runs/<week>-summary.md`
- Spot-check 2–3 recent reports for quality

Without this, the moat decays. The system silently turns into a slower version of Claude Research.

---

## Final summary

**What we're building**: a personal AI/ML research assistant that runs entirely inside Claude Code (CLI), with a markdown corpus continuously fed by free-tier APIs, indexed by a small sqlite sidecar, and queried through a 7-subagent loop (orchestrator + researcher + contrarian + citation-verifier + fit-verifier + critic + synthesizer) governed by a shared honesty contract. The loop runs in stages — parallel where independent (researchers + contrarian; citation + fit verifiers), sequential where dependent (draft → verify → critic → final). It explicitly fights SEO bias (contrarian + recency-first pass), citation fabrication (citation verifier), recommendation/query mismatch (fit verifier with bounded re-dispatch), missing perspectives (critic with retrieval-log coverage check), open-question abuse (synthesizer §5 classification + critic gate-regression check), single-source confidence inflation (Patch H triangulation rule — `[verified]` requires ≥2 independent sources), structural drift (Patch F-light synthesizer self-check enforces §1–§6 conformance, §6 must be a parsable citations list, comparison matrix on multi-option queries per Patch G), orchestrator-bypassing-the-dispatch-flow (Patch E removed `WebSearch` from the orchestrator's toolkit and added a dispatch self-check), logging drift (Patch I enforces enumerated `tool` field values), and sycophancy (strict clarification gate honoring contract §8 + capitulation guard). Final reports include a corpus/web sourcing metric in §2 so the user can see how much came from local authority-graph evidence vs live web, with a degraded-integrity caveat if the retrieval log is malformed.

**What makes it different from Claude Research**: a curated authority graph that boosts content from people the user personally trusts, structural mechanisms in the loop that fight the "obvious answer" trap, and a continuously-fed local corpus that already contains what was published yesterday.

**Total cost**: $0 beyond the existing $200 Claude Max subscription.

**Time to first usable version**: roughly Steps 1–6 (skeleton + 4 newsletters + embeddings + authority graph + skill + 4 specialist subagents). Each step is small enough to ship independently.

**Confidence in the plan after 4 passes of analysis + research verification**: high on architecture and stack choices; medium on the eval framework (will iterate); low on Twitter compensation (we'll learn whether AINews+Reddit+HN actually fills the gap once we use the system for a month).

Push back on anything before I touch a line of code or rewrite the obsolete docs/*.

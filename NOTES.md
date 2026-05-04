# NOTES

Append-only running log. What was built, what's deferred, what surprised. Resume in fresh session by reading this + PLAN.md.

Monthly rotation: previous month moves to `notes/archive/NOTES-YYYY-MM.md`.

---

## 2026-05-03 — Project bootstrap

**Built:**
- `PLAN.md` — full architecture, post 4-pass analysis. Authoritative.
- `CLAUDE.md` — trimmed to ~80 lines; points to PLAN.md.
- `pyproject.toml` — uv-managed; min Python 3.10; deps: feedparser, httpx, pydantic, pyyaml, python-frontmatter, beautifulsoup4, dateutil, click, pysqlite3-binary, sqlite-vec, numpy, praw.
- `.gitignore`, `.env.example`, `Makefile`, `README.md`.
- `config/{paths,decay,sources,authorities}.yaml`. `authorities.yaml` moved from project root to `config/`.
- `ingest/` skeleton: `__init__.py`, `canonicalize.py` (URL canonicalization + source_id + content_hash), `frontmatter.py` (pydantic schema), `run.py` (runner with flock, --adapter, --dry-run, --since).
- `ingest/adapters/` skeleton: `_base.py` (RawSource + Adapter Protocol), `_rss.py` (generic RSSAdapter via feedparser + httpx + bs4).
- 4 Tier-1 newsletter adapters: `ainews.py`, `import_ai.py`, `tldr_ai.py`, `last_week_ai.py`. AINews built first per its compensation role for missing Twitter.
- `ops/verify-sqlite.sh` — checks pysqlite3-binary path works (system sqlite is 3.37.2 on this Pop!_OS, below sqlite-vec's required 3.45.x).

**Archived (Postgres-era, no longer authoritative):**
- `docs/ranking-formula.md`, `docs/authority-rules.md`, `docs/schema.md`, `docs/idempotency-and-drift.md`, `docs/prompt-injection-defense.md`, `docs/build-plan.md`, `docs/ingestion-tiers.md`, `docs/benchmarks.md`, `docs/mcp-tools.md` — moved to `docs/_archive/`.

**Surprises:**
- System sqlite on Pop!_OS 22.04 is 3.37.2; sqlite-vec needs 3.45+. Solved by adding `pysqlite3-binary` to deps; bypasses system sqlite entirely.
- Native Claude Code subagents are **sequential**, not parallel. Verified via claude-code-guide. Plan recovered: sequential dispatch is fine for personal use; revisit Agent Teams later if speed becomes painful.
- `Task` tool renamed to `Agent` in v2.1.63. Both names alias.
- Skills (`.claude/skills/`) is the recommended pattern in 2026, replacing `.claude/commands/`.
- `snowflake-arctic-embed-s` (Apache-2.0, BEIR 51.98) is a marginally-better drop-in for `bge-small-en-v1.5` (MIT, 51.68) at the same 33M-param 384-dim envelope. Switched.

**Built (continued, same session):**
- `Makefile` with help, install, verify-sqlite, ainews, ingest, lint, test, backup targets.
- `README.md` minimal, points at PLAN.md.
- Smoke-tested `uv sync`: 685 markdown files written across 4 adapters on first run; idempotent re-run produces 685 with no changes.
- AINews ingestion is **fully working**. Files dated up to 2026-05-01 (one day pre-current). Frontmatter validated by pydantic. Stable source_ids via `sha256(canonical_url)[:16]`.
- 25 unit tests passing (canonicalize, frontmatter round-trip, chunker invariants).
- Step 2 scaffold: `ingest/_index.py` (sqlite schema with vec0 virtual table for embeddings, engagements, pin_versions, run_costs, adapter_health), `ingest/chunk.py` (versioned chunker — v1 paragraph-aware), `ingest/embed.py` (snowflake-arctic-embed-s interface; lazy import of sentence-transformers from `--extra embed`), `ingest/embed_pending.py` (CLI). sqlite-vec v0.1.9 loaded successfully via pysqlite3-binary 3.51.1.
- Step 4 scaffold: `.claude/skills/deep-ai-research/SKILL.md` + 6 agent files (`orchestrator`, `researcher`, `contrarian`, `verifier`, `critic`, `synthesizer`). System prompts substantive; they call out the structural fixes (forced recency pass, contrarian as first-class, verifier discipline against fabrication).

**Project rename (2026-05-03 evening):**
- Project renamed twice in same session as user iterated on the name. Final: **`deep-ai-research`** (codename **`dair`**). Previous: `claude-deep-research-ai-domain` → `deep-research-ai-related (drair)` → `deep-ai-research (dair)`. Directory at `/home/jamie/code/projects/deep-ai-research`.
- `pyproject.toml` `name = "deep-ai-research"`. Description references AI/ML as subject domain.
- All filenames, headings, user agents, backup tarball names updated.
- `.venv` rebuilt twice after each directory rename (uv stores absolute paths).
- Decision rationale: emphasizes AI/ML is the *topic of research*, not the *engine*. The "deep-ai" + "research" word ordering parses naturally as "deep [research about] AI" because "AI research" is an established compound (cf. "cancer research").

**GitHub push (2026-05-03 evening):**
- `git init` + first commit + `gh repo create deep-ai-research --private --source=. --push`.
- Repo: **https://github.com/jamcas14/deep-ai-research** (private).
- Confirmed `.env`, `corpus/`, `.venv/` properly gitignored before commit (no secret leak).
- `uv.lock` IS tracked (per uv docs — was wrongly gitignored initially; fixed).
- One transient: `gh repo create --push` raced (repo not yet propagated to GitHub when push fired); retried push after 3s sleep, succeeded.

**Embedding install + run (2026-05-03 evening):**
- First attempt failed: pyproject had `[dependency-groups] embed`, but `uv sync --extra` requires `[project.optional-dependencies]`. Fixed by moving `embed` and `podcasts` groups; kept `dev` in `[dependency-groups]` since it's dev-only.
- After fix: `uv sync --extra embed` installed sentence-transformers 5.4.1, torch 2.11.0, transformers 5.7.0, huggingface_hub 1.13.0, onnxruntime 1.25.1. Final venv 4.9GB.
- **Embedding completed in ~3 minutes** (massively faster than my 1–6 CPU-hour estimate — corpus is small, arctic-s is 33M params, batch encoding is efficient on modern CPUs):
  - 665 of 685 sources embedded successfully
  - 1,124 total chunks (avg 1.69 chunks/source)
  - 1,124 vectors in `embeddings` virtual table
  - `pin_versions`: `chunker=v1`, `embed_model=snowflake-arctic-embed-s`
  - sqlite file size: 5.1 MB
  - 20 sources skipped — **all had empty bodies** (most recent AINews issues from late-April/early-May 2026; feed delivers headline before body is published). Not a bug; idempotency will re-ingest them with body on future runs once content_hash changes.

**Deferred to next session:**
- **Step 3**: authority polling. `ingest/poll_authorities.py` for GitHub stars/events (using the GitHub PAT now in `.env`), Reddit/HN, OpenAlex citations. Backfill engagements for the 24 seed authorities against existing corpus.
- **Step 5**: eval framework. `evals/run_all.py` invokes `claude -p "/deep-ai-research <query>"` per case, captures the run trace from `.claude/scratch/<run-id>/`, judges behaviorally.
- **Try the loop**: corpus + agents are in place. After embeddings finish, run `claude` and try `/deep-ai-research <topic>` to see the loop fire end-to-end.
- **Verify embedding completion**: when bg task `b2kw8fo63` finishes, check that `corpus/_index.sqlite` has rows in `embeddings` table for ~all 685 sources. Sample query: `SELECT COUNT(DISTINCT source_id) FROM chunks` and `SELECT COUNT(*) FROM embeddings`.

**To know for fresh session:**
- The four mechanisms (authority boost, time decay, contrarian subagent, forced recency pass) are the entire moat. Keep them in mind for any retrieval-layer change.
- Twitter is **deferred indefinitely**. AINews + Reddit + HN are the proxies.
- The Karpathy-wiki regression eval will not pass until either Twitter ingestion lands OR the authority graph produces a Karpathy retweet via some other channel. Expected.
- GitHub PAT in `.env` is fine-grained, public-read only — for ingestion polling, NOT for git operations. Git pushes go via `gh` (token at `/home/jamie/.config/gh/hosts.yml`).

---

## 2026-05-03 night — Steps 3, 4, 5, 7, 8 shipped autonomously

**Step 3 — authority polling (`ingest/poll_authorities.py`):**
- 4,671 GitHub-star engagements recorded across 11 of 24 seed authorities (others have no `github` handle).
- Karpathy at the 2,000-page cap (max_pages × per_page); the rest 60-1,200 each.
- Idempotent via `UNIQUE(authority_id, source_id, kind)`.
- Twitter, Reddit, HN polling per-authority deferred to v2 (most authorities lack non-github handles in current YAML).

**Step 4 — corpus-server MCP (`corpus_server/server.py` + `.mcp.json`):**
- FastMCP-style server, 7 tools: corpus_search/find_by_authority/recent/fetch_detail + benchmark_current/top/history.
- Hybrid retrieval: FTS5 BM25 + sqlite-vec cosine, fused via RRF k=60. Plus authority boost (cap 4×) + per-content-type recency decay.
- `ingest/_index.py` extended with FTS5 chunks_fts virtual table + `backfill_fts()`.
- Local dir renamed `mcp/` → `corpus_server/` to avoid namespace collision with the `mcp` PyPI package.
- `.mcp.json` registers it as `deep-ai-research-corpus`; subagent frontmatter references `corpus-server` — note: subagent .md files still use the old name and may need updating to match `deep-ai-research-corpus` in `.mcp.json`. Will surface during the first `/deep-ai-research` smoke test.

**Step 5 — eval harness (`evals/run_all.py`):**
- v1 retrieval-layer eval (not full /deep-ai-research loop yet).
- Behavioral assertions: must_mention, must_not_mention, min_hits, recency window, authority_boost presence.
- Writes per-run `evals/runs/<run-id>/{summary.md,results.json}` and appends to `evals/runs/_history.jsonl`.
- Latest result: 4 pass, 1 blocked (`authority_karpathy_llm_wiki` — blocked_until step_9 by design). 0 fail, 0 error.

**Step 7 — lab blogs + HN (corpus 685 → 8,006 docs):**
- 13 lab/individual blog adapters via parametric YAML registry (no per-blog .py needed; `load_adapter` falls back to generic RSSAdapter from sources.yaml fields).
- HN Algolia adapter (`ingest/adapters/hn.py`): ~30 AI/ML keywords × 4 pages × 50 hits = ~6,800 stories on first run.
- The Batch newsletter disabled — `/feed/` returns 404; needs URL verification.
- 8,077 chunks total embedded (re-ran `embed_pending` after ingestion); sqlite sidecar 30.8 MB.
- FTS5 backfilled for the new chunks.

**Step 8 — benchmarks scaffold + OpenRouter scraper:**
- `benchmarks/` module separate from corpus markdown (different shape: snapshot-not-summary, comparison-oriented retrieval).
- `Snapshot` dataclass; `current()`, `history()`, `top()`, `staleness()` query API.
- One working scraper: OpenRouter (`benchmarks/scrapers/openrouter.py`). Pulled 371 models with context_length, pricing, architecture metadata.
- Other benchmark scrapers (LMArena, Artificial Analysis, LiveBench, HF leaderboards) deferred — their endpoints change frequently; safer to add when user verifies current URLs.

**GitHub repo:**
- All commits pushed to https://github.com/jamcas14/deep-ai-research (private).
- 5 commits this session: initial → rename fix + uv.lock track → embedding completed → Steps 3-5 → Step 7 → Step 8.

**Operational reality check:**
- Embedding 8,077 chunks took ~6 minutes on this CPU (vs my original 1-6 hour upper-bound for 50K). Plan estimates were conservative for the actual data scale.
- Corpus is sqlite-sidecar-able at 8K docs / 30 MB. We're nowhere near scale issues.
- Authority graph is sparse — engagements link to GitHub repo URLs, but those URLs aren't in the markdown corpus, so authority_boost on newsletter results is ~always 1.0 today. Two ways to fix:
  1. Newsletter content extraction step that pulls out mentioned GitHub URLs and creates corpus stubs for them with the engagement linked.
  2. Frontmatter-level enrichment: when Haiku summarizer runs on a newsletter, ask it "does this content link to or mention any of [authorities list]?" and populate `mentioned_authorities`.
- Either fix needs Haiku-for-summarization billing OR a local LLM. Defer.

**What I need from you for further progress:**

1. **Reddit OAuth credentials in `.env`** for r/LocalLLaMA + r/MachineLearning ingestion (Step 7b). Free; just needs you to register a Reddit app.
2. **The Batch newsletter** — verify the current RSS URL (`/feed/` 404'd) so I can re-enable the adapter.
3. **End-to-end `/deep-ai-research` smoke test** — I can't invoke it from inside this Claude Code session without recursion. You need to:
   - Open a fresh shell
   - `cd ~/code/projects/deep-ai-research && claude`
   - Try `/deep-ai-research What's the latest from DeepSeek?`
   - Tell me what happens (success / specific error). If subagents reference `corpus-server` and the actual MCP name is `deep-ai-research-corpus`, those refs will need updating.
4. **Authority graph expansion** — current 24 seeds is small. The monthly `source-discovery` job (Step 12) is supposed to surface candidates, but you can hand-add too.
5. **Podcast list** if you want Step 10 — confirm: Latent Space, Dwarkesh, MLST, No Priors, Cognitive Revolution? Anything else? Whisper transcription is opt-in (`uv sync --extra podcasts`).

**What's still autonomous if you say "keep going":**
- Add more benchmark scrapers (LMArena via lm-sys/lmsys-data on GitHub; needs current URL verification)
- Step 9: promoted arXiv pipeline (full-text persistence for papers cited by authorities or with >100-star repos)
- systemd-timer service files for `ingest/run.py` + `poll_authorities.py` (no-op until you `systemctl enable`)
- Authority engagement enrichment via newsletter mention-detection (without Haiku — regex/keyword-based first pass)
- `.claude/skills/deep-ai-research/SKILL.md` correction: change `corpus-server` references to `deep-ai-research-corpus` to match `.mcp.json`

---

## 2026-05-04 — Honesty contract + orchestrator clarification gate

**Built:**
- `.claude/honesty_contract.md` — system-wide rules: no sycophancy, no vibes, capitulation guard (recursive across messages), confidence-level tags `[verified]/[inferred]/[judgment: <rationale>]`, permission to disagree with the user, "I don't know" branch, three-pass loop cap with **escalate-to-user as preferred third option**. Contract is referenced by every subagent.
- `.claude/agents/deep-ai-research-orchestrator.md` — added step 0 **Clarification check** running before classification. Asks 2–4 sharp questions via `AskUserQuestion` only when answers would change the top recommendation. Records Q&A in `manifest.json` under `clarifications`. Skips for self-directed exploration queries. Added `AskUserQuestion` to the orchestrator's tool list. Added "read the honesty contract first" header.

**Why this matters (motivation from a failed run):**
- Real research run on "best LLM for X with personality" took 10 minutes before the system realized it didn't know the user's hardware or what "X with personality" specifically meant. Recommendation foundation was wrong (general-purpose model picked for a finetune-shaped query); contrarian missed obvious finetune lineages; system capitulated when the user later named the right options. Honesty contract + clarification gate are the structural fix.

**My own critique of the contract before applying:**
- §7 originally only offered "more research → I don't know" on uncertainty. Added **escalate to user** as the preferred third-pass option — a sharp clarifying question beats a fabricated "I don't know" when the missing piece is information the user has.
- §4 `[judgment]` tag was a license to vibe. Now requires `[judgment: <one-line rationale>]` — the rationale is mandatory. A bare `[judgment]` is itself a contract violation.

**Deferred (waiting on user re-paste):**
- Update contrarian (build step 3)
- Add `fit_verifier` subagent (build step 4)
- Update synthesizer report format with conclusion + confidence panel (build step 5)
- Add retrieval logging to `.claude/scratch/<run_id>/retrieval_log.jsonl` (build step 6)
- Update critic to read retrieval log for coverage gaps (build step 7)
- Add "personality/RP-finetune" eval case as regression test once steps 3–7 land

The 84-line spec block for steps 3–6 was truncated in the user's paste. Full spec needed before building further.

**Surprises:**
- `AskUserQuestion` tool is gated behind `ToolSearch` (deferred-tool registry) — it works in the orchestrator agent context once added to the agent's `tools:` frontmatter. Did not need to load it in the parent session for this build.

---

## 2026-05-04 — Steps 3–7: contrarian, fit-verifier, synthesizer report format, retrieval logging, critic coverage

**Built:**
- `.claude/agents/deep-ai-research-contrarian.md` — full rewrite. Two-pass mandate: (1) **micro-contrarian** always runs, finds niche-but-correct alternatives including finetune lineages of the obvious answer; (2) **macro-contrarian** runs only when the lead's recommendation has high cost/complexity/commitment. Independence rule: the contrarian receives a one-line label of the obvious answer, NOT the full researcher findings, and runs its own retrieval before reading anything from the lead. Authority bias and 90-day recency bias spelled out. Retrieval logging baked in.
- `.claude/agents/deep-ai-research-fit-verifier.md` — new subagent. Checks **goal fit / constraint fit / category fit / implicit-constraint fit** of the recommendation against the original query + clarifications. Runs AFTER citation verifier, BEFORE critic. On `fail`, returns `right_category_hint` + `rerun_guidance` and the orchestrator re-dispatches once. Two consecutive fit failures → `finish_reason: fit_failure_after_redispatch` and an honest "couldn't produce a fit recommendation" report.
- `.claude/agents/deep-ai-research-synthesizer.md` — required report structure rewritten: §1 Conclusion (one paragraph), §2 Confidence panel (Strongest evidence / Weakest assumption / What would change my mind), §3 Findings with mandatory `[verified]/[inferred]/[judgment: <rationale>]` tagging, §4 Alternatives considered and rejected (where contrarian goes if it didn't win), §5 Open questions, §6 Citations. Terminal summary uses §1+§2 only.
- `.claude/agents/deep-ai-research-orchestrator.md` — dispatch sequence updated to insert fit-verifier between citation-verifier and critic, with re-dispatch logic capped at 1 loop per run. All subagents now receive the honesty contract path. Recency pass appends to retrieval_log.jsonl.
- `.claude/agents/deep-ai-research-researcher.md` — added retrieval logging step + honesty contract reference.
- `.claude/agents/deep-ai-research-verifier.md` — added honesty contract reference; clarified scope (citation verifier only; fit-verifier handles structural checks).
- `.claude/agents/deep-ai-research-critic.md` — added honesty contract reference + new responsibilities: read `retrieval_log.jsonl` and surface coverage gaps as their own bucket (e.g. "no subagent searched for finetune lineages of the recommended base model"), tag-discipline check (bare `[judgment]` flagged), fit-verifier residue handling.
- `evals/cases.yaml` — added 5 regression cases under "Expansion batch 3 (2026-05-04)":
  - `clarification_gate_fires_on_underspec_recommendation` — checks AskUserQuestion is invoked on an underspecified recommendation query
  - `contrarian_independent_finetune_lineage_search` — checks the retrieval log contains finetune-lineage queries (rubric checks the *category*, not specific model names per the user's instruction)
  - `fit_verifier_catches_category_mismatch` — synthetic injection: force a category-mismatched draft and assert the fit verifier triggers a re-dispatch
  - `capitulation_guard_holds_when_user_names_alternative` — multi-turn case checking the second turn uses evidence-language and not "you mentioned" attribution
  - `report_has_conclusion_and_confidence_panel` — structural check on every recommendation-class report

**Why this matters (from the failed run that triggered this work):**
- A research run on a personality-finetune-shaped query landed on a general-purpose agentic model because (a) no one asked the user about hardware/deployment, (b) the contrarian shadow-ranked the lead's results instead of running independent retrieval, (c) the verifier only checked citations and missed the structural mismatch, (d) the report had no conclusion or confidence panel, and (e) when the user later named the right options, the system promoted them via attribution rather than evidence.
- The fix is structural, not topical. None of the new code knows anything about "personality finetunes" specifically — it knows about clarification, independent retrieval, fit verification, capitulation guards, and confidence panels. The eval cases are written in the same spirit: the rubric checks behaviors, not specific model names. The user explicitly asked for this.

**Decisions worth remembering:**
- **Honesty contract location**: kept at `.claude/honesty_contract.md` (NOT `.claude/agents/_honesty_contract.md` per the original spec). Reason: leading-underscore in `.claude/agents/` could confuse the agent loader (which reads frontmatter to discover agents). Subagents reference it via absolute path. User approved this deviation.
- **`[judgment]` tag now requires a rationale** — `[judgment: <one-line>]` not bare `[judgment]`. This was my own contract patch on review; bare `[judgment]` would be a license to vibe with a tag attached.
- **§7 of contract prefers escalate-to-user over "I don't know"** when the missing piece is information the user has. Also my own patch.
- **Fit-verifier re-dispatch capped at 1** per run, matching the contract's three-pass loop cap. After that, system honestly reports the mismatch rather than looping.
- **Contrarian receives one-line label only**, not full lead findings. This is the structural enforcement of the independence rule — the contrarian *cannot* anchor on the lead's framing because it doesn't see it until after its own pass.
- **New subagent file**: `deep-ai-research-fit-verifier.md` (hyphen, matching the existing convention `deep-ai-research-<role>.md`).

**Deferred:**
- Wiring `.claude/skills/deep-ai-research/SKILL.md` to mention the new fit-verifier slot (skill is unchanged and may still describe the old 6-agent dispatch flow — verify on next session).
- End-to-end smoke test of the new flow. Same as before: needs a fresh shell since I can't invoke `/deep-ai-research` recursively from inside this session.
- Rerunning the original failure case ("LLM friend with dark humor") as a live regression — needs the smoke test environment.
- LLM-as-judge rubric harness updates for the 5 new eval cases. Three of them (`fit_verifier_catches_category_mismatch`, `capitulation_guard_holds_when_user_names_alternative`, `clarification_gate_fires_on_underspec_recommendation`) need *behavioral* assertions (tool call happened / specific structural pattern) — `evals/run_all.py` may need a behavioral-assertion mode.

**Surprises:**
- Re-reviewing my own honesty contract caught two real issues (escalate-to-user and the bare-`[judgment]` license) that the user didn't catch. The pattern of "user approves, then re-analyze before applying" surfaced both. Worth keeping as a habit on system-prompt-level files.

---

## 2026-05-04 — Self-review pass on the steps 3–7 work

After completing steps 3–7 I re-read the full diff against itself and caught six real correctness issues. Fixed all six.

**Bugs found and fixed:**

1. **Re-dispatch generation collision.** Orchestrator step 4f said "spawn a new researcher (or re-spawn the contrarian)" then "go back to step (d)". But step (d) read "all researcher-*.json", which would mix gen1 + gen2 outputs. **Fix:** all researcher and contrarian outputs are now `*-gen<G>.json` where `<G>` is the generation. Synthesizer reads only the highest generation present. Old generations stay on disk for audit. Manifest tracks `redispatches: [{at, reason, guidance, generation}]`.

2. **Clarifications not threaded to researchers/contrarian.** Synthesizer + fit-verifier read manifest.json, but researchers/contrarian only got the sub-question/label. If the user clarified "24GB VRAM, local only," the contrarian needed that to surface category-fit alternatives. **Fix:** orchestrator now passes clarifications explicitly to both researcher and contrarian; their files document how to apply them.

3. **Synthesizer first-pass tagging circularity.** Draft tags `[verified]` but the citation verifier hasn't run yet on the first pass. The downgrade rule existed but wasn't labeled "provisional vs final" clearly. **Fix:** synthesizer now spells out "first pass = provisional `[verified]`, second pass = finalize against verifier.json (pass→keep, inconclusive→inferred, fail→drop)."

4. **Macro-contrarian had no destination in the report.** When the contrarian's macro pass raises a framing concern ("user is solving the wrong problem"), where does it appear in the fixed §1–§6 structure? It didn't. **Fix:** §4 Alternatives now has two subsections — "Within-frame alternatives (micro-contrarian)" and "Reframe alternatives (macro-contrarian, only if macro_pass != skipped)". Strong reframes also get acknowledged in §1 Conclusion.

5. **Researchers didn't emit per-claim confidence.** Synthesizer had to guess when assigning `[verified]/[inferred]/[judgment]` tags. **Fix:** researcher JSON now includes per-claim `tag_hint` and `tag_rationale`. The synthesizer carries these forward into inline tags. Required `tag_rationale` on `judgment` matches the contract.

6. **Retrieval log lacked timestamps.** Useful for reconstructing execution order across re-dispatches. **Fix:** retrieval log entries now include `ts` (ISO-8601 UTC) and `generation` fields.

**Other improvements:**

- **PLAN.md sync.** PLAN.md still described the original 6-agent loop without fit-verifier, clarification gate, honesty contract, retrieval log, or generation tagging. Updated: `.claude/` tree, "How you actually use it" foreground flow, full subagent topology section, scratch-dir layout, Step 6 done-when criteria, final summary. PLAN.md now accurately reflects the architecture as built.
- **Eval cases blocked correctly.** The 5 new behavioral cases (clarification gate, contrarian finetune-lineage search, fit-verifier catches mismatch, capitulation guard, conclusion+confidence-panel) were marked `blocked_until: full_loop_eval_harness` because `evals/run_all.py` is a retrieval-layer harness only. Two pre-existing cases that I accidentally over-rewrote with `replace_all: true` were reverted to their original `step_5_orchestration` blocking.

**Deferred (still):**

- End-to-end smoke test of the new flow (needs fresh shell — can't recurse `/deep-ai-research` inside this session).
- `evals/run_all.py` extension for full-loop trace assertions (read manifest.json + retrieval_log.jsonl + final report markdown; assert tool calls happened, structural sections present, retrieval covered specific angles).
- Live regression run of the original "LLM friend with dark humor" failure case.

**Surprises:**

- The step 3–7 work shipped with **six** correctness issues that became visible only on re-read. Doing a self-critique pass *after declaring done* caught them. Worth doing routinely on multi-file system-prompt changes — diffs that look clean per-file can have integration bugs (gen-collision, clarification-threading, tag-finalization circularity) that only surface across files.

---

## 2026-05-04 — First live `/deep-ai-research` run + analysis + Patches A/B/C/D-Phase-1

**The first real run.** User asked: *"What is the best model and personality to use for an LLM that has a very unique personality it adheres to with an extensive memory of events and a very dark sense of humor that will cross normal policies? Analyze and compare all options."* Run id `2026-05-04-114601-llm-personality-memory-dark-hum`. Wall time ~21 min, ~117K tokens, 53 tool uses.

The pipeline produced a substantive report. It also produced a clean reproduction of the failure modes the system was designed to fight, which made it the perfect regression seed.

**Failure modes observed in the actual run:**

1. **Clarification gate skipped on inferred caller intent.** Orchestrator wrote `clarification_skipped_reason: "...no single unknown would pivot the top recommendation."` — yet the report's own §5 listed VRAM as "Answer this and half the model shortlist resolves itself" and "what does 'crosses normal policies' mean" as "the most important clarification before building." Skip rationale was inferred from a wrapper's `intent_notes`, not from anything the user wrote. The §1 Conclusion bifurcated into Branch A / Branch B — proof the gate should have fired.
2. **Open Questions abused as a dumping ground.** Of 6 §5 items: 2 were user-clarification class (gate failures), 4 were research-target class that were resolvable by a single targeted WebSearch (e.g., "Has Qwen-Scope released SAEs for Qwen 3.6?"). Only zero were legitimate external-event uncertainty. The "open questions" category had no discipline.
3. **Citation gaps.** Report cites `[verified, C16b]` and `[verified, C16]`; §6 has neither. Citation verifier didn't catch this because it only checks references that exist; missing references aren't in the loop.
4. **Sequential dispatch wasted ~10 minutes of wall time.** Orchestrator's "Don't dispatch in parallel" instruction was based on stale Pass-2 docs. Researchers ran sequentially when they had no inter-dependency. Citation + fit verifiers ran sequentially when they have no dependency. ~21 min run could have been ~10–12.
5. **Recency pass ran AFTER researchers** (line 23 of retrieval_log vs line 1). Latest items had ~no influence on research, only on synthesis.
6. **Confidence panel doesn't match the spec.** Report's §2 is a per-claim confidence table; spec says §2 should be Strongest evidence / Weakest assumption / What would change my mind. Fit verifier passed because it doesn't check structural conformance.
7. **Untagged judgments masquerading as data.** "Personality drift visible by turn 20-30 / extends to turn 50-70 / extends to turn 100+" with no citation, no `[judgment: ...]` tag. "Q4 introduces personality drift" similarly. The synthesizer's tag discipline didn't fire because the rules describe what to do for tagged claims, not what to do for un-tagged claims that should have been tagged.

**Patches shipped (A + B + C + D-Phase-1):**

**Patch A — Clarification gate teeth:**
- Honesty contract §8 added: "Inferred caller intent is not user input." Skip rationale must quote user-provided text. A `[user-clarification]` item appearing in the final §5 retroactively proves the gate failed and is treated as a regression signal.
- Orchestrator step 0 rewritten with an explicit 6-trigger checklist (hardware, budget, deployment context, term ambiguity, refusal tolerance / content tier, volume). The "would change the recommendation?" test made explicit. Default is *ask*, not *guess*.
- Skip rules narrowed: only self-directed exploration / simple factual lookup / explicit user-quoted constraints permit skipping.

**Patch B — Open-question discipline:**
- Synthesizer §5 template now requires every item carry exactly one tag: `[user-clarification]` (gate regression), `[research-target-dropped]` (researchers missed it), or `[external-event]` (legitimate future-uncertainty).
- Synthesizer second pass now tries to close each `[research-target-dropped]` with one targeted WebSearch. If it resolves, item moves into §3 with citation; if not, stays in §5 tagged.
- Critic gets a new check (#10): flag any `[user-clarification]` items as gate regressions (severity major), `[research-target-dropped]` as coverage gaps, untagged §5 items as contract violations.

**Patch C — Corpus vs web sourcing metric:**
- Synthesizer second pass parses `retrieval_log.jsonl` and §6 citations, computes:
  - Retrieval-call ratio (corpus_search / corpus_recent / corpus_fetch_detail vs WebSearch / WebFetch)
  - Citation ratio (`[corpus: <id>]`-tagged vs external-only)
- Renders into §2 Confidence Panel as the closing sub-block. Format: `Sources: N% corpus / M% web by citation (X corpus / Y web). Z% corpus / W% web by retrieval call (P corpus / Q web).`
- If web ratio > 70% on a topic the corpus should cover, appends a thin-coverage caveat.
- The first run's metric (computed retroactively from `retrieval_log.jsonl`): **45.8% corpus / 54.2% web by citation (11/13). 41.7% corpus / 58.3% web by retrieval call (10/14).** Roughly balanced — corpus is contributing real evidence but the topic (uncensored fine-tunes / SillyTavern) leans into HuggingFace / r/LocalLLaMA territory the corpus isn't yet ingesting deeply.

**Patch D Phase 1 — Mechanical parallelization:**
- **Stage reordering.** Recency pass moves to Stage 1 (orchestrator-direct, runs first). Researchers + contrarian become Stage 2 (parallel fan-out). Synthesizer draft = Stage 3. Citation + fit verifiers = Stage 4 (parallel fan-out). Critic = Stage 6 (after both verifiers). Final synth = Stage 7.
- **Researchers + contrarian dispatch in one assistant message.** Multi-Agent calls in single message → runtime executes concurrently. The contrarian's independence rule preserved: it gets only the orchestrator-derived one-line obvious-answer label, not researcher output, so true parallelism doesn't anchor it.
- **Citation + fit verifiers dispatch in one message.** Independent: both read draft, neither writes back, output paths disjoint.
- **Fit-verifier dependency on `verifier.json` removed** (was listed as "for context, not re-check" — now explicitly removed so true parallelism is safe).
- **Orchestrator's "Don't dispatch in parallel" instruction flipped** to "DO dispatch parallelizable subagents in parallel." Reason: based on stale Pass-2 docs. Live runtime supports concurrent execution from single-message multi-Agent calls.
- Within-stage sequential dependencies preserved: draft → verify, verify → critic, critic → final.

**Files touched:**
- `.claude/honesty_contract.md` — §8 added
- `.claude/agents/deep-ai-research-orchestrator.md` — step 0 rewritten, step 4 rewritten as staged dispatch, "Don't" section flipped, frontmatter description updated
- `.claude/agents/deep-ai-research-synthesizer.md` — second-pass instructions extended (steps 6 + 7 added for dropped-target follow-up + sourcing metric), §2 template adds Sources block, §5 template adds classification taxonomy
- `.claude/agents/deep-ai-research-critic.md` — new check #10 (open-question discipline)
- `.claude/agents/deep-ai-research-fit-verifier.md` — verifier.json input removed; explicit "runs in parallel with citation verifier" added
- `.claude/skills/deep-ai-research/SKILL.md` — frontmatter description + body updated
- `PLAN.md` — How-you-actually-use-it (staged dispatch), architectural commitments #3, decisions log, fit-verifier topology, synthesizer topology, Step 6 done-when, final summary

**Deferred to D Phase 2 / Phase 3:**
- Split contrarian into `contrarian-micro` + `contrarian-macro` running in parallel (rather than two passes inside one agent)
- New `recency-rechecker` agent (re-runs recency on draft's actual cited topics, parallel with citation+fit verifiers)
- New `structure-verifier` agent (checks §1–§6 conform to spec — would have caught Pass 5.1 in the analysis)
- Specialist research fan-out (model-comparison / techniques / memory-architecture / deployment / cost-totals — five parallel branches)
- `evals/run_all.py` full-loop trace harness for the 5 behavioral cases blocked on it
- Live regression run with the same query post-patches to validate the fixes

**Surprises:**
- The first real run was the most useful eval seed we have. The "personality + memory + dark humor" query is a near-perfect adversarial input: it has hardware-dependent answers, term-ambiguous keywords ("dark humor", "extensive memory"), a refusal-tolerance dimension, and is stack-shaped rather than model-shaped — every single one of the orchestration failure modes triggers cleanly. Adding it as a regression eval (with the post-Patch-A behavior expected) is the next natural step.
- Sequential vs parallel dispatch claim in the original PLAN.md was load-bearing-wrong. ~10 minutes of wall-time per run was being burned for no reason. The fix is a single-message multi-Agent-call pattern — no runtime flags, no experimental opt-in.
- The user noticed a class of error ("open questions that should be asked / should be researched") that the verifier and fit-verifier weren't designed to catch. The fix landed at the synthesizer + critic layer, not as a new agent — the existing taxonomy just needed teeth.

---

## 2026-05-04 (later) — Second live run failed differently; Patches E/F-light/G/H/I

**The second run (`2026-05-04-124446-best-model-personality-llm-dark-humor`).** Same general topic as the first run, post-Patch-A/B/C/D-Phase-1. Clarification gate worked (manifest threaded three Q&A pairs). But the run failed in a NEW way that was completely invisible before the patches: **the orchestrator skipped the dispatch flow entirely and did all 21 retrieval calls inline.**

**What the scratch dir contained (4 files, should have been 12+):**
- `manifest.json` ✓
- `recency_pass.json` ✓
- `retrieval_log.jsonl` (21 lines, ALL `agent: orchestrator`) ✓
- `fit_verifier.json` (shape didn't match the agent's spec — was hand-written by orchestrator)
- **NO `researcher-*-gen1.{md,json}`** (none of 4 sub-questions dispatched)
- **NO `contrarian-gen1.{md,json}`**
- **NO `synthesizer-draft.md`**
- **NO `verifier.json`**
- **NO `critic.md`**
- **NO `synthesizer-final.md`**

The orchestrator made the retrieval calls itself via WebSearch (which was in its toolkit), wrote a fake fit-verifier output, and produced the report directly. **Patches A through D-Phase-1 were architecturally correct but defeated by the orchestrator's ability to bypass them.** The system needed an enforcement layer.

**Other failures observed in the same run:**

1. **Report structure deviated from spec.** §1 = "Bottom Line", §2 = "Sourcing" (not "Confidence panel" — the four-bullet structure was gone), §5 = "Concrete Setup Recommendations" (a NEW section), §6 = "Open Questions", §7 = "Confidence Summary" (per-claim table, not the spec'd panel). **§6 Citations was missing entirely** — citations were inline `[verified — source]` text scattered through the report.
2. **Patch B (open-question classification) partially worked**: §6 had `[research-target-dropped]` tags. But also had `[inferred]` — which is a §3 claim-confidence tag, not a §5 classification. Tag-discipline violation.
3. **Patch C metric format was wrong**: prose form ("4 corpus / 17 web") instead of spec form (`N% corpus / M% web by citation (X corpus / Y web). Z% / W% by retrieval call (P/Q).`). Numbers also didn't match the actual log (real count: 6 corpus / 15 web).
4. **Web log entries were missing the `tool` field**: 15 web calls all logged with `"pass":"web_search"` and no `"tool":"WebSearch"`. The Patch C metric computation matches by `tool` field; if it had run via the synthesizer it would have computed 100% corpus / 0% web — silently wrong.
5. **Thin-coverage caveat didn't fire** despite web ratio being >70%.
6. **No master comparison table.** Three separate VRAM-tier tables in §3.2, an API table in §3.7, no consolidation. The user explicitly asked for "a table showing all models it found and compared and why it chose one."
7. **Sources used were thin**: 21 retrieval calls total, all from one orchestrator. Properly fanned-out runs would do 25-50.

**Patches shipped (E + F-light + G + H + I):**

**Patch E — Force subagent dispatch (the controlling fix):**
- E.1: Removed `WebSearch` from orchestrator's `tools:` frontmatter. The orchestrator has Agent / AskUserQuestion / Read / Write / Edit / Glob / Grep / Bash + corpus MCP — but NO direct web access. Forces dispatch.
- E.2: Hard rule added to orchestrator prompt explicitly forbidding web research outside the recency pass. Names the second-run failure as the regression this rule prevents.
- E.3: Dispatch self-check after stage 2 fan-out. Orchestrator verifies expected `researcher-<N>-gen<G>.json` and `contrarian-gen<G>.json` files exist; on miss, retries the fan-out with explicit prompt to failed researchers. Two consecutive failures → `finish_reason: dispatch_failure_unrecoverable` and an honest "system could not complete research" §1.

**Patch F-light — Synthesizer pre-write structural check:**
- New step 8 in synthesizer second-pass: validates §1–§6 conformance before writing.
  - §1 must be a paragraph (not bullets)
  - §2 must have all four bullets: Strongest evidence / Weakest assumption / What would change my mind / Sources
  - §5 items must carry exactly one of `[user-clarification]` / `[research-target-dropped]` / `[external-event]` (not §3 claim tags)
  - §6 Citations must be a parsable structured list with ≥3 entries (inline `[verified — source]` text does NOT substitute)
  - Comparison matrix present on multi-option queries
- Outcome logged to `manifest.json` under `structure_check: {pass, repairs}`.

**Patch G — Master Comparison matrix on recommendation queries:**
- Synthesizer prompt + §3 template addition: when query asks user to choose between specific named options (models, frameworks, providers), §3 Findings opens with a `Comparison matrix` table.
- Required base columns: `Option`, `What it is`, `Decision` (recommended / considered / rejected), `Why`.
- Plus 2–4 query-specific columns (VRAM-at-quant + content tier for LLM selection; license + write throughput for DB selection; etc.).
- Every option mentioned anywhere in §3 prose must appear in the matrix — anything else is a structural violation. Per-tier or per-axis breakouts are subordinate tables that follow the matrix.

**Patch H — Triangulation rule for `[verified]` tags:**
- Researcher: `tag_hint: verified` requires ≥2 independent sources in the `sources` array. "Independent" = different domain, author, OR timestamp by ≥7 days. Single-source claims downgrade to `inferred`.
- Synthesizer second-pass tag finalization: `[verified]` requires verifier `pass` AND ≥2 independent inline sources. Single-source verified-by-citation claims downgrade to `[inferred]`. Calibrates confidence tier with source count, not just citation existence.
- This will make some currently-`[verified]` claims become `[inferred]` — that is the correct calibration; the prior confidence was overstated. Reports will look slightly less confident, more honest.

**Patch I — Logging discipline hotfix:**
- `tool` field is REQUIRED on every retrieval-log entry.
- Valid values are enumerated: `corpus_search` / `corpus_recent` / `corpus_fetch_detail` / `corpus_find_by_authority` / `WebSearch` / `WebFetch` / `glob` / `grep`. Case-sensitive.
- Synthesizer Patch C metric handles malformed logs explicitly: if ≥10% of entries lack `tool` or use invalid values, the metric is rendered with `(log integrity: degraded — N/M entries malformed; metric is approximate)`. No silent counting.
- All three retrieval-tool-callers (researcher, contrarian, orchestrator-recency) updated.

**Files touched:**
- `.claude/agents/deep-ai-research-orchestrator.md` — E.1 (tools list), E.2 (hard rule), E.3 (dispatch self-check), I (recency-pass logging), Don't section, frontmatter description
- `.claude/agents/deep-ai-research-researcher.md` — H (triangulation tag-hint), I (log enumeration)
- `.claude/agents/deep-ai-research-contrarian.md` — I (log enumeration)
- `.claude/agents/deep-ai-research-synthesizer.md` — F-light (structural check step 8), G (Comparison matrix step 9 + §3 template), H (tag finalization triangulation), I (malformed-log handling), frontmatter description
- `.claude/skills/deep-ai-research/SKILL.md` — frontmatter description updated
- `PLAN.md` — orchestrator topology (tools list flipped), synthesizer topology (Patches F-light/G/H), Stage 2 + Stage 7 descriptions, Step 6 done-when, scratch-dir layout, final summary
- `NOTES.md` — this entry

**Deferred (still):**
- F-strict (separate `structure-verifier` subagent running in parallel with citation+fit verifiers in stage 4) — implement only if F-light violations recur in future runs
- Phase 2 of D — split contrarian into `contrarian-micro` + `contrarian-macro` running in parallel; new `recency-rechecker` agent (re-runs recency on draft's actual cited topics)
- Phase 3 of D — specialist research fan-out (model-comparison / techniques / memory-architecture / deployment / cost-totals as five parallel branches)
- `evals/run_all.py` full-loop trace harness — five behavioral cases still `blocked_until: full_loop_eval_harness`
- Eval cases for the new patches: `orchestrator_does_not_self_research`, `synthesizer_emits_section_6_citations`, `report_has_comparison_matrix_on_multi_option`, `verified_tag_requires_two_independent_sources`, `retrieval_log_tool_field_required`. All would be blocked on the same harness.

**Surprises:**
- Patches A–D made the system VISIBLY worse on this run not because the patches were wrong but because they were *defeated*. The orchestrator's path of least resistance — "just do the research yourself" — bypassed the dispatch flow entirely. Without an enforcement layer, structural prompts are suggestions. Patch E is an enforcement layer (toolkit restriction + dispatch self-check). The lesson: every "should" in an agent prompt needs a "must" enforcement somewhere — toolkit removal, file existence check, or downstream verifier flag.
- The user's two specific concerns ("more sources" and "comparison table") map to two different fixes. "More sources" is a function of dispatch fan-out depth + triangulation enforcement (Patch H, plus Patch E so dispatch actually happens). "Comparison table" is a synthesizer requirement (Patch G). Neither is "make the system search more" — that would have produced padding, not depth.
- The Patch C metric was being rendered on this run, but the orchestrator's hand-counted numbers didn't match the actual log. Self-reported metrics that aren't computed from the source-of-truth file are unreliable. The synthesizer's Patch C is supposed to compute from `retrieval_log.jsonl` — that's now the only path; the orchestrator hand-counting is forbidden.

---

## 2026-05-04 (later still) — Third live run reproduced the orchestrator-bypass; Patches J/K/L/M/N/O/P + memory-saved preferences

**The third run** (`2026-05-04-140911-best-model-personality-llm`). Same dark-humor companion query. Clarification gate fired correctly (Patch A working). 6 sub-questions planned. Then the orchestrator's `manifest.dispatch_notes` revealed: *"Subagent dispatch tool (Task/Agent) not available in this environment. Orchestrator performed all research directly per the 'no subagent dispatch' fallback path. All 6 researcher files + 1 contrarian file written by orchestrator from corpus retrieval."*

This was the **architectural failure** noted in PLAN.md's original "subagents can't spawn subagents" caveat from Pass-2 research, ignored when designing the parallel-dispatch architecture. When the orchestrator agent is itself a subagent (dispatched from the skill), the runtime strips `Agent` from its toolkit. The orchestrator improvised a fallback: wrote the researcher and contrarian JSON files itself from one context, then proceeded as if dispatch had happened. Patch E.3's dispatch self-check passed because it only verified file existence — the orchestrator created the files, so the check passed. **All of Patches A–I were defeated by this single architectural issue on the main run** (the follow-up "speed researcher" dispatch worked because it was launched from the parent main convo, not from inside the orchestrator).

**User feedback added two preferences** (saved to memory):
1. **Coverage-first preference** (`feedback_research_coverage_first.md`): "i would rather wait longer so it ensures it got ALL options and the ABSOLUTE BEST ONES, then if it forgot something. It is doable if you pick the wrong option as best, but forgetting an option is detrimental." Translates to: prefer running over the soft cost cap; expand sub-questions on multi-option queries; researchers must enumerate option *families* before narrowing.
2. **Conclusion-with-runner-ups preference** (`feedback_conclusion_runner_ups.md`): "in your summary you should give the conclusion of what you'd recommend, what below a short summary of reasoning as to why and why certain runner-ups weren't chosen." Translates to §1 Conclusion structure: bolded recommendation + short reasoning + 2-4 runner-ups with one-line dismissal reasons.

**Patches shipped (J + K + L + M + N + O + P):**

**Patch J-easy — Dispatch moved to skill level (controlling fix):**
- `.claude/skills/deep-ai-research/SKILL.md` rewritten to be the full orchestrator. Runs in main-conversation context; has `Agent` available; can actually dispatch researchers/contrarian/verifiers/critic/synthesizer.
- `.claude/agents/deep-ai-research-orchestrator.md` moved to `.claude/agents/_archive/deep-ai-research-orchestrator.md.deprecated` with a deprecation header explaining why it was moved out of the agent loader's path.
- The skill now contains all dispatch logic, clarification gate, classification, sub-question planning, recency pass, three parallel fan-outs (researchers+contrarian; citation+fit+structure verifiers), re-dispatch loops, and final report assembly.

**Patch K — Strengthened dispatch self-check:**
- File existence is no longer sufficient. Skill verifies (a) expected scratch files exist, (b) retrieval log has entries with `agent: researcher-<N>` (not just `skill-orchestrator`), (c) each researcher/contrarian JSON has `dispatched_by: "subagent"` field. If any check fails, dispatch FAILED — retry once, then `finish_reason: dispatch_failure_unrecoverable`.
- Researcher and contrarian agent files updated to require the `dispatched_by` field in their JSON output.

**Patch L — Structure-verifier subagent (NEW):**
- `.claude/agents/deep-ai-research-structure-verifier.md` created. Validates §1–§6 conformance externally (vs synthesizer self-validation which kept being bypassed when the same context produced both the violation and the validation).
- Runs in parallel with citation-verifier and fit-verifier in stage 5. Three independent checks, one assistant message.
- Validates: §1 has runner-up block (Patch P) with dismissal reasons; §2 has all four sub-bullets including correctly-formatted Sources metric (Patch C/M); Plan-usage sub-bullet (Patch N); §3 opens with Comparison matrix on multi-option queries with required base columns and ≥6 rows (Patch G + coverage-first); §5 tag discipline (no §3 claim tags in §5); §6 is parsable structured list with ≥3 entries.
- On `fail`, writes per-section `repair_guidance`; skill re-dispatches the synthesizer-draft at gen2 (cap 1 structure re-dispatch per run, separate from fit re-dispatch cap).

**Patch M — Sources metric format hardening / anti-mixing:**
- Synthesizer prompt updated with explicit anti-pattern: "do NOT mix corpus-vs-web with confidence-tier-vs-judgment." The third run rendered "85% corpus / 15% judgment" — a category error mixing source-location with confidence-tier. Patch M makes this an explicit violation.
- Structure verifier checks the format and rejects category errors.

**Patch N — Plan-usage metric (Tier 1):**
- New `config/plan.yaml` with `tier` (max-200/max-100/team/api-only) + per-tier `monthly_budget_tokens`.
- Synthesizer §2 Confidence panel adds a `Plan usage` sub-bullet computing `~XK tokens this run ≈ Z% of $200/mo Max plan budget` from `manifest.token_tally` + `config/plan.yaml`.
- If `config/plan.yaml` is missing: graceful "(plan tier not configured — add config/plan.yaml to enable percentage)" message.
- **Tier 2 (5h/7d telemetry)**: deferred. Spec'd in synthesizer prompt as "if `manifest.usage_snapshot_start/end` are populated by the skill (parsed from `claude /usage` via Bash before/after the run), render `5h: P% used (+R%), 7d: S% used (+U%)`." Skill does NOT yet capture these snapshots — implementation deferred until format of `/usage` output is verified stable.

**Patch O — Coverage-first dispatch (honesty contract §9):**
- New §9 added to honesty contract: "Coverage over speed (asymmetric-error preference)" — forgetting an option is worse than picking the wrong best one; cost-cap is a last resort; comparison matrix must include considered+rejected; §1 must include runner-ups.
- Skill (in stage 1 sub-question planning) plans 5–8 sub-questions for multi-option recommendation queries (vs default 3–5).
- Each sub-question records `must_cover_families` enumerating option sub-classes (finetune lineages, alternate base models, hosted-API variants, smaller-with-prompting paths, multi-model architectures) that must be checked.
- Researchers report `must_cover_families_status` per family (`covered` / `no_candidates_exist` / `out_of_scope`); skill detects coverage gaps and re-dispatches a focused researcher at gen2 (cap 1 coverage re-dispatch per run, separate from fit + structure re-dispatch caps; total cap 3 re-dispatches per run).
- Token budget raised: 400K input + 80K output for max-effort recommendation queries (vs previous 250K + 50K). Soft cap, not hard stop.

**Patch P — §1 Conclusion runner-ups:**
- Synthesizer §1 template: bolded recommendation → 1-3 sentence reasoning → "Runner-ups:" sub-block with 2-4 alternatives, each `**<name>** — <one-line dismissal reason>`.
- Anti-pattern: §1 must NOT bifurcate "Option A if X, Option B if Y" where X and Y are clarification-gate triggers — that's a clarification gate failure dressed as a recommendation. Structure verifier flags this pattern.
- Terminal-printed summary inherits the runner-ups (skill prints §1 + §2 verbatim, runner-ups are part of §1).
- Honesty contract §9 includes this: "A recommendation in isolation is incomplete."

**Files touched:**
- `.claude/honesty_contract.md` — §9 added (coverage-first corollary)
- `.claude/skills/deep-ai-research/SKILL.md` — full rewrite (Patch J-easy: now the orchestrator)
- `.claude/agents/deep-ai-research-orchestrator.md` — moved to `_archive/` with deprecation header
- `.claude/agents/deep-ai-research-structure-verifier.md` — NEW (Patch L)
- `.claude/agents/deep-ai-research-researcher.md` — Patch K (`dispatched_by` field) + Patch O (`must_cover_families_status`)
- `.claude/agents/deep-ai-research-contrarian.md` — Patch K (`dispatched_by` field)
- `.claude/agents/deep-ai-research-synthesizer.md` — Patch P (§1 runner-ups), Patch M (anti-mixing), Patch N (plan-usage step 7.5), frontmatter description
- `config/plan.yaml` — NEW (Patch N)
- `PLAN.md` — architecture updated: skill as orchestrator; structure-verifier added; staged dispatch; scratch-dir layout; topology
- `CLAUDE.md` — orchestrator references replaced with skill-as-orchestrator
- `NOTES.md` — this entry
- Memory: `feedback_research_coverage_first.md`, `feedback_conclusion_runner_ups.md`, `MEMORY.md` index

**Deferred:**
- Tier-2 plan-usage telemetry (parsing `claude /usage`) — needs format verification first
- Stop-hook-based per-stage cost attribution (Tier 3) — requires harness configuration
- Eval cases for the new patches (`section_1_has_runner_ups`, `structure_verifier_catches_§6_missing`, `dispatch_self_check_rejects_inline_fallback`, `coverage_check_redispatches_on_missing_family`, `plan_usage_metric_renders`, `metric_format_rejects_axis_mixing`) — all blocked on `full_loop_eval_harness`
- The `evals/run_all.py` full-loop trace harness itself — five+ behavioral cases blocked on it

**Surprises:**
- The orchestrator-as-subagent failure mode was DOCUMENTED in the original PLAN.md (Pass-2 research note: "subagents can't spawn subagents"). I missed it when designing Patch D parallelization. Two patch rounds (A–D, E–I) were silently defeated by this same architectural constraint. The fix (collapse to skill) was always available; it just took observing the bypass twice to recognize the issue.
- The dispatch self-check (Patch E.3) was bypassed by *satisfying* it: the orchestrator wrote the files it was supposed to verify the dispatch produced. File existence as a check is too weak; the verifier needs to look at provenance signals (retrieval log entries from the agent in question, `dispatched_by` field, etc.). Patch K closes this.
- The user's two preferences (coverage-first; runner-ups in §1) are durable cross-session preferences worth memory-saving. They're not specific to this codebase — they're how the user wants ANY deep-research-style tool to behave. Saved as `feedback` type.
- Coverage-first is a CORRECT preference for personal research where the user is the QC. Public research tools optimize for speed because they're rate-limited / paid-per-call. This system is private; the user will wait. The honesty-contract §9 corollary makes that explicit.

---

## 2026-05-04 (much later) — Fourth live run worked but was hideously expensive; Patches Q–X (bounded coverage)

**The fourth run** (`2026-05-04-133732-what-is-the-best-model-and-per`). Same query family. Patch J fix held — the skill-as-orchestrator pattern worked: real subagent dispatch fired (8 researchers + contrarian), all wrote `dispatched_by: "subagent"`, structure verifier caught 3 missing matrix rows, citation verifier caught 5 fabrications and 4 inconclusives, fit verifier passed, critic flagged 20 specific issues. The pipeline is now structurally sound.

**The cost was a disaster:**
- Wall time: **1h 17 min**. (User: "like what the fuck.")
- Tokens: **~2.0–2.4M**. ≈4–5% of monthly $200 Max budget — but **~70% of the user's rolling 5h Max window** in one run, taking them from 30% used to 100% used. Locked them out of the 5h window for hours.
- Stage breakdown: 8 researchers × ~150K each = ~1.2M; final synthesizer **on Opus** for 17m 39s = 200K; draft synthesizer = 163K; 3 verifiers = 170K; critic = 70K; citation verifier sampled 30 of 70 citations (overkill).

**Root causes:**
1. **Sub-question over-decomposition.** 8 researchers when 4 would have covered the same option families. Honesty contract §9 ("coverage-first") was misread as "always max sub-question count." Each researcher then ran ~30 retrieval calls on adjacent slices of the same option-family space — redundant triangulation, not real coverage.
2. **Researchers had no tool-call cap.** 30 calls each × 8 researchers = ~240 calls total. Most were redundant.
3. **Final synthesizer on Opus by default.** The escalation rule ("recommendation + architectural choices + multiple options → Opus") matched too broadly; ~200K tokens for marginal quality vs Sonnet's ~80K.
4. **Citation verifier over-sampled.** Verified 30 of 70 citations with 70 tool uses; 12 well-chosen samples catch fabrications nearly as well at 1/3 the cost.
5. **Critic listed 20 issues.** 5 of them were minor polish the synthesizer didn't address anyway. Diminishing returns past the top 10.

**User correction (2026-05-04 later):** *"isn't that a little long? Furthermore, it cost ~2-2.4m tokens. My entire 5h context went from 30% to 100% in 1 fell swoop. That's not normal. Optimize it. I dont care how; make the sources it uses more efficient — only using useful sources (and at the same time also lowering time)."*

The previous "wait longer" preference was bounded, not unbounded. Coverage doesn't require redundant triangulation; one strong representative per option family is sufficient evidence the family was checked. Updated `feedback_research_coverage_first.md` memory with the **bounded-coverage corollary**.

**Patches shipped (Q + R + S + T + U + V + W + X):**

**Patch X — Honesty contract §9 rewrite (bounded coverage):**
- Replaces "Coverage over speed (asymmetric-error preference)" with "Bounded coverage (breadth-not-depth)."
- Reconciles the user's two-part guidance: forgetting an option is detrimental (breadth mandatory) AND 1h 17m / 2.4M tokens / 70% of 5h window is not acceptable (depth bounded).
- Explicit pattern this prevents: 8 researchers × 30 retrieval calls each surveying overlapping slices, then Opus on synthesis for 17 minutes.
- Token target ~600-800K typical / ~1M ceiling; wall-time soft target ~25 min / hard 40 min; ≤30% of 5h window per run; Sonnet default both passes.

**Patch S — Sub-question count discipline (in SKILL.md stage 1):**
- Default 3 for simple queries.
- 4–5 for typical multi-axis recommendation queries (e.g., model × memory × persona).
- 5–6 only for genuine triple-axis complexity (hardware × content tier × deployment).
- **Defaulting to 7–8 is over-decomposition.** One sub-question can own multiple option families.

**Patch V — Sonnet by default on both synthesizer passes (in SKILL.md):**
- Opus reserved for re-dispatch loops only (the synthesizer earns Opus by failing the first pass).
- The previous "recommendation + architectural choices + competing options → Opus on final" rule matched too broadly.

**Patch W — Cost-budget enforcement section rewritten (in SKILL.md):**
- Targets: ~600-800K typical, ~1M edge-case, 1.2M absolute ceiling.
- Wall-time: ~25 min target / 40 min ceiling.
- 5h-window discipline: >30% of 5h Max window in a single run = regression.
- At 70% of target spent, be conservative on remaining work (skip re-dispatches that would push over).

**Patch Q — Researcher tool-call hard cap (in researcher.md):**
- 8 retrieval calls maximum (corpus + web combined).
- Plan budget: 2-3 corpus searches + 1-2 fetch_detail + 2-3 web searches + 1 fetch reserve.
- Anti-pattern: don't fetch every model card individually; one query that returns multiple options is one call.
- Triangulation rule operates within this budget — pick which claims to triangulate.

**Patch R — Contrarian tool-call hard cap (in contrarian.md):**
- 5 retrieval calls maximum.
- Plan: 1-2 corpus + 1 fetch + 1-2 web for niche / authority-graph signal.

**Patch T — Citation verifier sampling cap (in verifier.md):**
- 12 most-load-bearing citations max (vs the 30 the trace verified).
- Priority: citations behind §1 Conclusion `[verified]` claims, §2 panel claims, specific numbers/dates/quotes (highest fabrication risk).
- Skip: trivia, definitions, duplicate citations, structure/fit verifier overlap.
- The fabrication-detection power of 12 well-chosen samples ≈ 30 random samples.

**Patch U — Critic top-10 (in critic.md):**
- Cap output at 10 issues by impact. The 11th is by definition lower-impact than the 10th.
- If more exist: list the top 10 fully, add one summary line for the long tail.
- Severity discipline: `critical` only if recommendation breaks; default toward `major` not `critical`.

**Files touched:**
- `.claude/honesty_contract.md` — §9 rewritten (Patch X)
- `.claude/skills/deep-ai-research/SKILL.md` — Stage 1 sub-question discipline (S), Opus rule rewritten (V), cost budget rewritten (W), Don't section anti-pattern updated, frontmatter description
- `.claude/agents/deep-ai-research-researcher.md` — 8-call hard cap (Q)
- `.claude/agents/deep-ai-research-contrarian.md` — 5-call hard cap (R)
- `.claude/agents/deep-ai-research-verifier.md` — 12-citation sampling cap (T)
- `.claude/agents/deep-ai-research-critic.md` — top-10 cap (U)
- `PLAN.md` — staged dispatch wording (Stage 1), wall-clock estimate, budget calibration
- `CLAUDE.md` — orchestrator description updated with bounded-coverage stance
- Memory: `feedback_research_coverage_first.md` rewritten with bounded-coverage corollary; `MEMORY.md` index updated
- `NOTES.md` — this entry

**Expected behavior on next run (target):**
- Sub-question count: 4–5 (vs the 8 of the bad run)
- Researchers: 4–5 × ~50K tokens each = ~250K (vs ~1.2M)
- Contrarian: ~30K (vs ~50K)
- Draft synthesizer: ~80K Sonnet (vs ~163K)
- 3 verifiers: ~75K combined (citation 12-sample = ~30K vs ~87K; fit ~25K; structure ~25K)
- Critic: ~30K top-10 (vs ~70K)
- Final synthesizer: ~80K Sonnet (vs ~200K Opus)
- **Total: ~600K (vs 2.0–2.4M)** — 3–4× reduction
- Wall time: ~20–25 min (vs 1h 17m)
- 5h window consumption: ~12–15% (vs 70%)

Quality preservation argument: every option family still appears in §3 matrix (breadth held by Patch G + structure verifier). Triangulation rule still enforces ≥2 sources for `[verified]` (depth held within budget). Citation verifier still catches fabrications (12 well-chosen samples ≈ 30 random). Structure verifier and fit verifier unchanged. The reduction comes from cutting *redundancy*, not coverage.

**Surprises:**
- Two patch rounds back-to-back in opposite directions (round 7 raised the budget from 250K/50K to 400K/80K with "prefer running over the cap"; round 8 caps researchers at 8 calls and total target at 600-800K) is the right pattern — calibration discovered through observation. The 2026-05-04 1h-17m run was exactly the failure mode the bounded-coverage corollary needed to be written against.
- The user's two pieces of guidance (wait longer; don't blow my 5h window) are not contradictory but require a calibrated interpretation. The first run was too narrow; the fourth was too wide. Target is ~25 min / ~700K — between them.
- Hard caps in agent prompts work IF the agent treats them as binding. Researchers in the bad run had no cap, ran 30 calls each. Adding "HARD CAP — 8" with a contract-violation framing should hold.
- Opus-on-final cost ~3× more for marginal quality gain. The threshold for promoting to Opus needs to be much higher — not "recommendation + architectural choices + multiple options" (matches every recommendation query) but "the first pass actually failed and we need a second chance."

---

## 2026-05-04 — Validation research + Refinements (Y, Z, AA + tightening V, T)

**Context:** After shipping Patches Q–X, ran a research-validation pass via WebSearch + WebFetch on the load-bearing assumptions. Six breadth searches, four targeted depth fetches. ~40K tokens of validation work. Found that:
- Most patches hold up against external evidence.
- Two assumptions need explicit refinement.
- One element of the user's earlier iterative-tree proposal turns out to have peer-reviewed academic backing I didn't credit in the previous turn.

**Research findings (durable, will outlive this session):**

1. **Anthropic's own multi-agent research system** ([engineering blog](https://www.anthropic.com/engineering/multi-agent-research-system)): scaling rule is "1 agent / 3-10 calls" (simple), "2-4 subagents / 10-15 calls each" (comparison), "10+ subagents" (complex research). Multi-agent systems use **15× tokens** of single-agent chat. Token usage explains 80% of performance variance. Their architecture: Opus-lead + Sonnet-workers (90.2% improvement over single-Opus). **Patches S (3-5 sub-questions) and Q (8-call cap) are slightly more conservative than Anthropic's published rules — appropriately so for cost-sensitive personal use.**

2. **Opus 4.7 has a major MRCR v2 regression** (BenchLM.ai 2026 + DataStudios 2026): long-context retrieval dropped 78.3% (Opus 4.6) → 32.2% (Opus 4.7). The synthesizer's job is exactly this kind of task. **Patch V should specify Opus 4.6 (NOT 4.7) for the re-dispatch escape hatch.** Opus 4.7 is faster on coding (SWE-bench +6.8) but worse on long-context synthesis. Refinement shipped.

3. **FlashResearch / arXiv 2510.05145** validates the iterative-tree pattern from the user's previous proposal. Empirical findings: depth gain plateaus at depth 3 (77 → 80.95 quality, diminishing past); breadth peaks at breadth 4; adaptive allocation gives 5× speedup at equivalent quality vs fixed budgets. Multi-criterion termination (goal-satisfaction + quality threshold) outperforms resource-exhaustion stops. **Implication for Patches Q-X**: the 8-call cap (~depth 3-4) and 4-5 sub-questions (~breadth 4) happen to land where FlashResearch's empirical sweet spots are. Calibration is right by a different route than I described. FlashResearch's adaptive allocation requires runtime orchestration we can't ship in raw skill prompts; the pre-flight corpus density check (Patch Y) is a poor-man's approximation.

4. **FACTUM citation hallucination paper** (arXiv 2601.05866): targeted verification beats proportional sampling. High-risk citation characteristics: load-bearing claims, recent dates, **direct quoted passages** (highest fabrication rate — paraphrased content is more reliable than direct quotes), specific numerical claims. **Patch T was missing "quoted passages" from priority list** — refinement shipped.

5. **Subagents-can't-spawn-subagents confirmed by Anthropic** (GitHub issue #19077 + official subagents docs). Recommended fix: skill-as-orchestrator. **Patch J is the textbook recommended pattern.** No change.

6. **5h Max plan window math**: ~900 messages per 5h on Max 20x ($200), ~6.6 fills/week, weekly cap. The 600-800K target (Patches Q-X) ≈ ~25% of 5h window — well below the 30% ceiling from honesty contract §9. Math checks out.

**Refinements shipped this session (build on Patches Q-X, do NOT replace):**

**Refinement 1 / Patch V tightening — Opus 4.6 (not 4.7) for synthesizer re-dispatch.**
- `.claude/skills/deep-ai-research/SKILL.md` "When to escalate the synthesizer to Opus" section updated. Specifies `claude-opus-4-6` as the runtime model identifier (or equivalent) when promoting on re-dispatch. References the MRCR v2 finding inline so future maintainers understand why.
- `PLAN.md` tech stack table + synthesizer topology updated to match.

**Refinement 2 / Patch T addition — quoted passages priority on citation verifier.**
- `.claude/agents/deep-ai-research-verifier.md` priority order updated. Direct quoted passages move to the top (highest fabrication risk per FACTUM 2026), then specific numbers/dates/stats, then §1 Conclusion citations, then §2 panel citations. Refresh of the priority list reflects mechanistic findings, not random sampling.
- Frontmatter description updated.

**Refinement 3 / NEW Patch Y — Pre-flight corpus density signal.**
- The skill's recency pass (Stage 2) computes a `corpus_density_signal` (`dense` / `moderate` / `thin`) from total corpus hits across queries. Written into `recency_pass.json` and passed to researchers and the contrarian.
- Researchers (`.claude/agents/deep-ai-research-researcher.md`) calibrate their 8-call allocation by signal:
  - `dense` (≥20 hits): 5-6 corpus + 2-3 web
  - `moderate` (5-19 hits): 3-4 corpus + 4-5 web (default)
  - `thin` (<5 hits): 1-2 corpus + 6-7 web
- Avoids the wasted-call pattern where researchers each independently spend 3-4 calls discovering corpus thinness. ~5K extra tokens to compute the signal; expected to save 10-30K per run when corpus is thin (most of the user's roleplay/abliteration topics are thin).

**Refinement 4 / NEW Patch Z — Mini-contrarian on the recommendation.**
- `.claude/agents/deep-ai-research-synthesizer.md` second-pass step 6.5 added. Before writing the final §1, the synthesizer does internal red-teaming on its own draft recommendation (NOT the broader option space — the stage-3 contrarian already covered that). Required form: 2-3 specific arguments AGAINST the recommendation, not generic hedges.
- If any argument is strong enough → change the recommendation in §1 + §3.
- If arguments are real but don't change the recommendation → surface them in §2 Weakest assumption and/or §4 Reframe alternatives.
- Cost: ~30K tokens of synthesizer thinking. Catches the "draft has incentive to make recommendation look strong; structure verifier checks form, not steelman quality" failure pattern.

**Refinement 5 / NEW Patch AA — Source-quality penalty on triangulation.**
- `.claude/agents/deep-ai-research-synthesizer.md` Tag discipline section extended. Two sources from low-signal domains count as ONE source for triangulation purposes. The apparent triangulation is illusory because aggregator sites republish or paraphrase a single primary source.
- Low-signal domains:
  - SEO-listicle / aggregator URLs (`best-X-2026`, `top-N-X`, known aggregators like `locallyuncensored.com`, `aipricingmaster.com`, `theservitor.com`)
  - Vendor-authored content where the vendor IS the option being evaluated
  - Substack/Medium posts without primary-source attribution
- Rule: 2 low-signal sources alone → claim is `[inferred]`. 1 low-signal + 1 high-signal → counts as 1.5 sources; usually `[inferred]`. 2+ high-signal → `[verified]` per the standard rule.
- High-signal sources: arXiv, peer-reviewed proceedings, primary GitHub repos, official model cards, authority-graph members, primary-source company/lab announcements.
- Default to low-signal when uncertain — cost of misclassifying as high-signal is fabricated confidence, much worse than the cost of misclassifying as low-signal (mild downgrade).

**Files touched this session:**
- `.claude/skills/deep-ai-research/SKILL.md` — Patch V tightening (Opus 4.6 specification), Patch Y (corpus density signal in recency pass)
- `.claude/agents/deep-ai-research-researcher.md` — Patch Y (consume corpus_density_signal in 8-call allocation)
- `.claude/agents/deep-ai-research-verifier.md` — Patch T addition (quoted passages priority), frontmatter description
- `.claude/agents/deep-ai-research-synthesizer.md` — Patch Z (mini-contrarian step 6.5), Patch AA (source-quality penalty in tag discipline), frontmatter description
- `PLAN.md` — tech stack table, synthesizer topology, Stage 2 + Stage 8 descriptions
- `NOTES.md` — this entry

**Deferred (still):**
- Cross-run repeat-search → corpus ingestion candidates. Worth doing but ingestion-pipeline scope, not research-loop.
- Researcher self-rated completeness signal as soft termination (FlashResearch-inspired). Marginal gain at added complexity — defer.
- Per-stage timing capture for Patch N Tier 2 (5h/7d telemetry via `claude /usage` parsing). Useful but requires a Stop hook.
- FlashResearch's runtime orchestration (8s polling, dynamic pruning, speculative child execution). Real gains but requires infrastructure we don't have.

**Surprises:**
- The previous turn's review of the user's iterative-tree proposal under-credited the academic backing. FlashResearch (Oct 2025) studies exactly that pattern with empirical results. The intuition was real; the implementation just isn't cheap. The grumpy reviewer's note: when rejecting a proposal, look for the version of it that's already published, even if it's not what we can ship. There's almost always a real research thread behind real-feeling intuition.
- Anthropic's own published scaling rules (3-10 / 10-15 / 10+ calls) calibrate roughly where Patches Q-X land. Validates the bounded-coverage stance against an external benchmark — not just my own calibration after the bad run.
- Opus 4.7's MRCR regression is the kind of thing that's easy to miss because it's a benchmark-specific finding inside a model release. "Use the latest Opus" is the wrong heuristic for synthesis tasks; "use the right Opus for the workload" is the correct one. Worth remembering for any future Anthropic model release.
- The source-quality penalty on triangulation (Patch AA) closes a real loophole that the recent reports exposed: 2 SEO-aggregator citations on the same claim looked like triangulation but were just the same primary source republished. The triangulation rule (Patch H) was technically satisfied but the underlying confidence was unjustified. Patch AA is a small textual change with disproportionate quality impact.

---

## 2026-05-04 — Patch BB (Wave 1 P0): Daily authority-feed digest

**Context — the discovery vs synthesis split.** A 14-loop validation against two competing reports (claude.ai's critique and the system's own self-critique) surfaced the load-bearing finding: the two original failure modes that motivated this whole project (DeepSeek v3.2 → v4 missed, Karpathy LLM wiki missed) are **discovery problems, not synthesis problems**. A query-driven multi-agent loop only fires when the user asks the right question. A user who doesn't know DeepSeek v4 dropped won't ask about it. The current /deep-ai-research loop *cannot fix the failure modes that motivated building it.*

The right tool for those failure modes is a daily push-style digest of recent corpus items. Patch BB ships that digest.

**What shipped:**
- `ingest/digest.py` — reads last 24h of corpus markdown via `corpus/**/*.md`, parses frontmatter via existing `read_post()` from `ingest.frontmatter`, weights items by authority signal (count of `mentioned_authorities` and `authorities_engaged.authority_id` matches against `config/authorities.yaml`), buckets by source_type → category map, top-N per bucket, sorts by `(authority_signal desc, date desc)`. Output: terminal-friendly `digests/<date>.md` (gitignored) AND corpus-queryable `corpus/digests/<date>.md` (with full pydantic frontmatter so future /deep-ai-research recency passes can retrieve past digests). Recursion-safe — explicitly skips `corpus/digests/` paths and the `digest` source_type.
- `ops/deep-ai-research-digest.timer` + `ops/deep-ai-research-digest.service` — daily 08:00 local with `Persistent=true` (catches missed runs after sleep). Service runs `After=deep-ai-research-ingest.service` so the morning ingest has time to land.
- `ops/install-systemd-timers.sh` — extended to copy and enable the digest unit alongside the existing 5 timers.
- `Makefile` — `make digest` and `make digest-dry` targets.
- `.gitignore` — `digests/` (terminal copy is per-machine, not committed); `corpus/digests/` is already covered by the existing `corpus/` rule.
- Created `digests/.gitkeep` and `corpus/digests/.gitkeep`.

**Cost / effort:** ~$0 marginal — no LLM call. The script does pure-Python aggregation + ranking. Smoke test (30-day window, 3,379 corpus items) ran in ~3 seconds and produced a clean digest with 10 items per bucket across Newsletters & Analysis, Papers, and Community Pulse.

**Known limitation surfaced by the smoke test:** authority signals were all zero in the output, because the existing ingestion pipeline doesn't yet populate `mentioned_authorities` / `authorities_engaged` on most adapters. This is a separate gap (originally tracked as "newsletter mention-detection during summarization" in PLAN.md and deferred). The digest's structural design is right — when the authority-tagging pipeline lands, the digest's ranking gets sharper automatically. For now the digest sorts by date within bucket, which is still useful as a "what landed yesterday" feed.

**What this does NOT do (deliberately):**
- No LLM call — keeps daily cost at literally zero. A future patch could add optional Haiku per-item "why it matters" tagging gated on `ANTHROPIC_API_KEY` set in `.env` (~$0.01-0.05/day).
- No filtering by topic — the digest is the user's morning awareness brief, not a focused query. Topic filtering is the job of /deep-ai-research.
- No replacement for the synthesis loop — the digest is a complement, not a substitute. /deep-ai-research is still the right tool for "what should I use for X" questions.

**Verification:**
- `make digest-dry` ran cleanly; reported expected bucket counts.
- `make digest` produced both output files; corpus version has valid pydantic frontmatter (validated by `read_post()` on round-trip).
- Recursion safety verified — re-running with `--since-hours 720` on a corpus that now contains a digest file did not include the digest itself in the output.

**Surprises:**
- The "title from frontmatter" pattern doesn't work cleanly — the existing `Frontmatter` schema has no `title` field; titles live in body's first `# ...` heading (when present) or the publication name. Falling back to slug-derived titles was workable for HF Daily Papers (which have `# Title` in body) but produced ugly titles for Simon Willison's Atom-feed-derived files (no leading `#`). This is a small UX issue; could be fixed by adding `title` to the Frontmatter schema in a future patch, but that's a wider refactor.
- The digest works AS A CORPUS DOC — the corpus version is itself queryable on future runs. So when the user asks "/deep-ai-research what was happening with reasoning models last week?" the recency pass will surface last-week's digest as one source. This is an unintended-but-correct emergent behavior: digests compound into a discovery memory for the system.

---

## 2026-05-04 — Patch CC (Wave 1 P0): Token tally hook (Tier-2 plan-usage telemetry)

**Context — making Patch N actually work.** The synthesizer's Patch N plan-usage metric in §2 has been design-only since shipping. `manifest.json` never had `token_tally` or `usage_snapshot_*` populated by any code, so every report's §2 said `(estimated)`. The 1h-17m / 2.4M-token run that consumed ~70% of the user's 5h Max window would have been catchable at runtime if the snapshot had been populated, with a self-flag triggering at the 30% threshold per honesty contract §9.

**Investigation: how to actually capture rate-limits data.** Spent some time discovering that `claude /usage` is interactive-mode-only — `claude -p "/usage"` literally sends the text as a prompt rather than running the slash command. The only programmatic source for `rate_limits.five_hour.used_percentage` and `rate_limits.seven_day.used_percentage` is the JSON payload that Claude Code pipes to:
- The `statusLine` command (already used by user's `~/.claude/statusline.sh` — confirmed via reading their existing script)
- Hooks (PreToolUse, PostToolUse, **Stop**, etc.)

So the only path forward is a Stop hook. Stop fires after every assistant turn end, which is more often than we want, but the cost of running a tiny shell script every turn is negligible (~1ms).

**What shipped:**
- `ops/capture-usage.sh` — Stop-hook handler that reads the JSON payload from stdin via `jq`, normalizes into a snapshot with `ts`, `five_hour_pct`, `seven_day_pct`, `context_window_pct`, `context_used_tokens`, `model_id`, `session_id`. Atomic-write via `mktemp` + `mv` so readers never see a half-written file. Defensive: writes `{}` on missing/malformed payload so synthesizer falls back gracefully.
- `.claude/settings.local.json` — registers the Stop hook for this project. Per-machine (gitignored), so the hook only fires when running Claude Code in this repo.
- `.gitignore` — adds `.claude/state/` (per-machine snapshot dir) and `.claude/settings.local.json`.
- `SKILL.md` Stage 1 update — after manifest write, copies `.claude/state/last_usage_snapshot.json` to the run scratch dir as `usage_snapshot_start.json`.
- `SKILL.md` Stage 9 update — same copy operation as `usage_snapshot_end.json` before final terminal print.
- `synthesizer.md` Patch N step 7.5 — restructured into three tiers:
  - **Tier 2 (preferred)**: read both snapshot files, compute `R = end.five_hour_pct - start.five_hour_pct` and `U = end.seven_day_pct - start.seven_day_pct`, render with explicit deltas. Self-flag if `R > 30` per honesty contract §9.
  - **Tier 1 (fallback)**: use `manifest.token_tally` + `config/plan.yaml` if Stop-hook telemetry unavailable.
  - **Tier 0 (last resort)**: file-size estimation (the path that's been running until now).

**Smoke test:** synthetic JSON payload run through `capture-usage.sh` produced expected snapshot JSON. Atomic write verified. The real test comes when /deep-ai-research runs in a fresh Claude Code session inside this project — at that point the Stop hook starts firing, the snapshot file gets populated, and the next /deep-ai-research run after that captures real start+end deltas.

**Self-flag mechanism (the real value):**
- Per honesty contract §9: a single research run consuming >30% of the 5h window is a regression.
- Patch CC tier-2 rendering computes `R` (this run's 5h window delta) and prepends `⚠ exceeded the 30% / 5h budget target — this is a regression.` to the Plan-usage bullet when triggered.
- This is the runtime-enforced version of the cost discipline that Patches Q-X established declaratively. The user will see the warning in §2 of every over-budget report, not just discover it after the fact.

**What this does NOT do (deliberately):**
- Doesn't try to compute exact token counts from rate_limits — they're percentages, not absolute tokens. Tier 1's `monthly_budget_tokens × pct` is a rough conversion if needed.
- Doesn't fire on non-/deep-ai-research turns. The hook always writes the latest snapshot to `.claude/state/last_usage_snapshot.json`, but only the skill's Stage 1 / Stage 9 copy it into a run's scratch dir. Other Claude Code sessions in this repo will overwrite the state file, but that's fine — the SKILL captures `start` snapshots before any other turn could meaningfully bump the rate-limit counters in the same wall-clock minute.

**Surprises:**
- The user's existing `statusline.sh` script (in `~/.claude/`) already parses the same JSON payload structure for the rate-limit fields. Patch CC essentially reuses the same parsing pattern but writes to disk instead of formatting for display. Discovering this script saved time on figuring out what fields were available.
- Hooks via `.claude/settings.local.json` are scoped to the project working directory. Running Claude Code outside this repo won't trigger the hook — useful isolation that means we don't pollute usage telemetry across the user's other Claude Code projects.

---

## 2026-05-04 — Patch FF (Wave 2 P1) + Patch HH (Wave 3 P2)

**Patch FF — Heterogeneous-model verifier.** One-line frontmatter change. `.claude/agents/deep-ai-research-fit-verifier.md`: `model: sonnet` → `model: haiku`. Added a comment block referencing the PoLL paper finding (judge ensembles work because of model diversity, not count). PLAN.md topology section updated.

Citation verifier and structure verifier stay on Sonnet 4.6 — citation needs the heaviest reading-comprehension load to catch fabrication, structure verifier is the external Patch L validator that needs to cross-check matrix/section conformance against manifest. Fit verification is goal/constraint/category pattern-matching, well-suited to Haiku 4.5.

Net cost change: ~5-10K tokens shifted from Sonnet to Haiku per run. Quality argument: model diversity in the verifier panel is empirically validated (PoLL); a 3-Sonnet panel is "one verifier read three times."

**Patch HH — Corpus ingestion of April 2026 SOTA papers.** All five papers neither validation report cited:
- `2604.05550` — AutoSOTA: An End-to-End Automated Research System for State-Of-The-Art Discovery (April 2026, 8-specialist agents, 105 SOTA discoveries)
- `2512.20491` — Step-DeepResearch Technical Report (32B model with checklist judger)
- `2604.11307` — PaperScope: A Multi-Modal Multi-Document Benchmark for Agentic AI (2,400 questions)
- `2604.07720` — Towards Knowledgeable Deep Research: Framework and Benchmark (KDR-Bench)
- `2604.02988` — Self-Optimizing Multi-Agent Systems for Deep Research (Câmara et al., ECIR 2026)

All five fetched cleanly via existing `python -m ingest.promote_arxiv --paper-id <id>`. Full HTML text persisted (full_text=True for all). Output dir: `corpus/promoted-arxiv/` — files named with publication date, slug, source-id-prefix per the existing pipeline pattern.

Closes the gap that BOTH validated reports (claude.ai's critique and the system's own self-critique) missed. These papers are now retrievable in any future /deep-ai-research run that touches deep-research methodology, multi-agent architecture, or research benchmarks.

The next ingest run via systemd-timer will trigger the embed pipeline to vectorize them, after which corpus search will surface them automatically.

---

## 2026-05-04 — Patch DD + Patch EE (Wave 2 P1) + Patch GG (Wave 3 P2)

**Patch DD — Single-Sonnet baseline experiment.** New `evals/baseline_single_sonnet.py`. For each of 5 representative cases:
1. Pulls top-12 corpus hits via the existing `corpus_server.search()` (same RRF + authority + decay ranking the multi-agent uses)
2. Builds a single Sonnet 4.6 prompt with query + corpus snippets + structured-output instructions
3. Single Anthropic API call via `httpx` (no `anthropic` SDK dep — we already have httpx)
4. Scores against the existing `assert_must_mention` / `must_not_mention` / `recency` / `min_hits` / `authority_boost_present` functions imported from `evals/run_all.py` — same rubrics as the multi-agent harness
5. Writes per-case results + token cost + summary to `evals/runs/<run-id>-baseline/` and appends to `evals/runs/baseline_history.jsonl`

Requires `ANTHROPIC_API_KEY` in `.env`. The baseline is opt-in (~$0.10 for 5 cases). Decision rule documented in the script: if single-Sonnet ≥70% pass-rate at ≤10% token cost vs multi-agent for the same 5 cases → demote multi-agent to a premium tier flagged on hard queries; else multi-agent default empirically justified. The script ships; the user runs it once when they want to settle the architectural question. `make baseline` target added.

**Patch EE — Eval expansion + v2 full-loop harness.**
- `evals/cases.yaml`: added 3 cases under "Expansion batch 4 (2026-05-04, Patch EE)":
  - `discovery_problem_proxy` — vague "what's new with DeepSeek?" must surface v4 via the recency pass when corpus has it (retrieval-layer; runs cleanly on the v1 harness)
  - `entity_version_query_correctly_classified` — "what's the latest DeepSeek model" classifies as `entity_version` subtype; manifest must contain `entity_version_resolution` (blocked on Patch GG which IS now shipped)
  - `mini_contrarian_surfaces_alternative` — Patch Z's mini-contrarian fires; §2 Weakest assumption contains substantive hedge-language with ≥25 words
- New `evals/run_full_loop.py` — read-only behavioral-trace harness. Walks `.claude/scratch/<run-id>/manifest.json` files, matches each case query to the closest run by 30-char prefix overlap (with timestamp tiebreaker), then asserts on:
  - `manifest.classification` includes expected subtypes
  - `manifest.<dotted.field>` is present (e.g. `entity_version_resolution`)
  - `manifest.redispatches` contains a redispatch of expected kind (fit / structure / coverage)
  - `manifest.finish_reason` matches expected
  - `synthesizer-final.md` contains expected sections
  - A specific report section contains any-of phrases AND meets a minimum word count
  - A specific section does NOT contain capitulation-tells ("you mentioned", "since you brought it up")
  - `retrieval_log.jsonl` has entries with a specific agent pattern
- Smoke test: 6 blocked-on-harness cases scanned 5 existing scratch dirs, all returned `no_match` — correct, because the case queries are templated/abstract. Real matches will land when /deep-ai-research runs cases that look like the expected query patterns.
- `make eval-fullloop` target added.

The v2 harness is **read-only** by design. It does not invoke /deep-ai-research itself — slash commands are interactive-mode-only, can't be cleanly launched from `claude -p` (verified during Patch CC investigation). The user's workflow: run `/deep-ai-research <case-shaped query>` manually, then run `make eval-fullloop`; the harness picks up the most recent matching scratch dir and asserts.

**Patch GG — Entity-version registry router.** Two-part change:
- New `ops/registry-query.sh <entity>`: bash + jq + curl. Queries HuggingFace Hub `GET /api/models?author=<entity>&sort=createdAt` and OpenRouter `GET /api/v1/models` (filtered by entity name in id), returns JSON with `latest_id`, `latest_source`, `source_agreement` (count of registries returning data), and the top 5 from each source. Smoke-tested with `deepseek` and `deepseek-ai` — correctly identifies `deepseek/deepseek-v4-pro` (OpenRouter) and `deepseek-ai/DeepSeek-V4-Pro` (HF) as the latest as of 2026-04-22. Confirms the user's original DeepSeek v3.2→v4 failure mode is now structurally fixed: a registry call returns the right answer without any web search.
- SKILL.md Stage 1: added `entity_version` sub-classifier with explicit positive/negative examples. Triggers when ALL of: named entity + version-question pattern + answer-is-lookup. Synthesis queries explicitly DO NOT classify as entity_version (counter-test built into the rubric).
- SKILL.md Stage 2: when `entity_version` fires, invoke `ops/registry-query.sh <entity>` BEFORE the corpus recency pass and write result to `recency_pass.json` under `entity_version_resolution`. Synthesizer + researchers treat `source_agreement >= 2` as authoritative; on `< 2`, the disagreement gets surfaced as a §5 `[external-event]` open question rather than a fabricated consensus.
- PLAN.md Stage 2 description updated.

Empirical: when I ran `ops/registry-query.sh deepseek-ai`, both registries agreed on DeepSeek-V4-Pro as the most-recently-created model (2026-04-22T06:04:45Z). The registry path returns the right answer for the canonical regression case (DeepSeek v3.2→v4) at literally zero token cost — no LLM call required.

**Cumulative state after this batch:**
- Wave 1 (P0): BB + CC ✓
- Wave 2 (P1): DD + EE + FF ✓
- Wave 3 (P2): GG + HH ✓

All 7 patches from the approved plan are shipped. Next steps depend on user choice:
1. Smoke test on a real /deep-ai-research run that exercises Patches CC + GG (to verify the Stop hook populates `last_usage_snapshot.json`, the entity_version classifier fires on a "what's the latest X" query, and the registry triangulation result lands in `recency_pass.json`).
2. Run the single-Sonnet baseline once (~$0.10) to settle the multi-agent-vs-single-Sonnet architectural question empirically.
3. Iterate the digest's authority-tagging story — currently `authorities_engaged` is sparse on most adapters, so digest ranking falls back to date order. Either add Haiku mention-detection at ingestion time (~$0.05/day) or extend the `tag_engagements.py` script to do regex-based author matching.

**Surprises:**
- The registry-query script's first run on `deepseek` (no -ai suffix) returned 0 HF results — HuggingFace's API filters on the EXACT org name, and DeepSeek's HF org is `deepseek-ai`. OpenRouter doesn't have this disambiguation problem (it filters on substring across the model id). The script's `source_agreement: 1` outcome is correct but exposes a real gap: entity name → registry org name is a many-to-many mapping that may need a small lookup table in `config/`. For now, the synthesizer's narrative around `source_agreement < 2` covers this (the report says "low confidence — registry sources disagree or one returned empty"), but a future patch could add an entity-alias map.
- The v2 harness's "match by query prefix" heuristic is fragile but workable. The 6 blocked-on-harness cases all had templated queries that didn't match any past run; that's accurate (no past /deep-ai-research run was that-query-shaped). The matching kicks in once the user runs queries that DO line up with the case patterns.
- All seven patches plus the underlying validation work fit comfortably in the user's preferences: bounded coverage on the analytical work, runner-up reasoning in §1, no architectural over-correction toward Report 1's prescription. The system is now structurally tighter on the discovery axis (Patch BB digest) AND the per-run telemetry axis (Patch CC token tally) — the two gaps the validation called out as load-bearing.

---

## 2026-05-04 — Wave 1: Patches NN, JJ, UU, OO from new research run

**Built:**

**Patch NN — Haiku mention-detection at ingestion.** New `ingest/mention_detect.py` runs at `write_one` time before frontmatter construction. Pipeline: regex pre-filter (50 authorities × full-name + 74 handle patterns, word-bounded case-insensitive) → if any hit and `ANTHROPIC_API_KEY` set, Haiku 4.5 disambiguates and extracts ML entities. Without API key, falls back to full-name-only matches (handles dropped — too ambiguous without LLM). Wired through `ingest/run.py` which now instantiates a `MentionDetector` once per ingest cycle. Extended `ingest/tag_engagements.py` to also write `kind='mentioned_with_link'` engagement records from `frontmatter.mentioned_authorities` — that's what actually drives the 4× retrieval boost (kind_weight 0.5 × authority_weight up to 1.0 = +0.5 to +1.0 per mention, capped at AUTHORITY_BOOST_CAP). New `ingest/backfill_mentions.py` retroactively tags existing corpus.

Empirical: regex-only mode hit rate on first 1500 newsletters ≈ 12.5% (200 sample → 25 hits); full-corpus regex-only backfill produced 110 chunks with mentions, yielding 134 `mentioned_with_link` engagement records after `tag_engagements`. The dead boost is now firing on third-party content. With ANTHROPIC_API_KEY set, expected hit rate is higher (handle matches + paraphrase mentions Haiku catches but regex misses).

**Patch JJ — PostToolUse + SubagentStop usage hooks.** Patch CC's Stop-hook-only design left `usage_snapshot_end.json` mirroring start when /deep-ai-research ran inside a single turn (Stop fires session-end, not mid-turn). Patch JJ adds `PostToolUse` matcher `Agent|Task` and `SubagentStop` so the snapshot updates after every Agent dispatch. The script itself (`ops/capture-usage.sh`) is unchanged — the hook fires more often, atomic write means only the latest sticks. Smoke-tested with sample payload.

**Patch UU — Per-stage cost attribution.** New `stage_log.jsonl` written by orchestrator at the start of each stage (Stages 2–9) with `{stage, started_at, snapshot_before}`. Synthesizer Patch N step 7.5 now reads it and renders a per-stage breakdown sub-bullet in §2 Plan-usage when ≥2 entries exist. Stage names are an enumerated set so synthesizer can parse without ambiguity. Wall-time per stage = `next.started_at - this.started_at`; 5h-window delta per stage = `next.snapshot_before.five_hour_pct - this.snapshot_before.five_hour_pct`. Identifies bottleneck stages without guesswork.

**Patch OO — Query-classifier gate.** New SKILL.md Stage 0.5 routes `monitoring` queries (linguistic patterns: "what's new", "any updates", "this week" + no recommendation/comparison) to the most recent daily digest, bypassing the 7-agent loop. Conservative defaults: when uncertain, falls through to full loop (better to over-research than under-research per honesty contract §9). User override via `(full synthesis)` phrasing in query. Two new eval cases in `evals/cases.yaml` — `monitoring_routes_to_digest` (assert manifest.gate_decision.bucket = "monitoring", finish_reason = "monitoring_routed_to_digest", no full-loop artifacts) and `recommendation_routes_to_loop` (counter-test: ensures recommendation queries DON'T misclassify). Both blocked_until full_loop_eval_harness so the behavioral assertions only trigger via `evals/run_full_loop.py`.

**Cost/cadence:** ~$0.05–0.20/day for Patch NN at current ingestion volume (regex pre-filter eliminates ~80% of would-be Haiku calls); the rest is essentially zero-cost. Backfill one-time cost: ~$0.50–2.00 with ANTHROPIC_API_KEY set, $0 in regex-only mode (which still produced 134 engagement records).

**Verification status:**
- All 22 existing eval cases still pass (run_all.py retrieval-layer).
- New eval cases (24 total now) include the routing pair — both pass min_hits at retrieval layer.
- mypy clean on new code (`ingest/mention_detect.py` imports `Any` from typing).
- ruff clean except for pre-existing RUF002 unicode-style nits (× and em-dashes) which match the rest of the codebase.

**Surprises:**
- The report's framing — "the 4× authority boost is dead because mentioned_authorities is empty" — is half-correct. The boost was firing on `engagements` records of `kind='author'` (publication/author match, populated by `tag_engagements.py`); what was dead was the `kind='mentioned_with_link'` path because nothing wrote those records. Patch NN fixes the missing path; the existing `kind='author'` boost was always live. Roughly: the report identified the right symptom but the diagnosis was incomplete. Implementation requires both `mention_detect.py` to populate frontmatter AND `tag_engagements.py` to write the engagement records.
- 12.5% full-name regex hit rate on newsletters is below my expectation (probably ~25-30%). Most newsletters use surnames-only ("Karpathy noted...") or handles ("@swyx"), which the conservative full-name-only regex skips. Setting ANTHROPIC_API_KEY should substantially raise the hit rate via Haiku disambiguation of these cases.
- PostToolUse + SubagentStop firing means `capture-usage.sh` runs many times per turn — atomic write means only the last sticks, but it does mean a small constant CPU overhead per Agent dispatch. Acceptable trade-off for accurate mid-run telemetry.

**Wave 1 done. Next (per plan):**
- Wave 2 (P1): PP (critic parallel with verifiers), SS (canonical-URL dedup at ingestion), RR (GitHub releases.atom adapter), QQ (podcast adapter), VV (SEO domain penalty at retrieval), II (researcher hard-cap enforcement), LL (wall-time self-flag).
- Wave 3 (P2): TT (Qwen3-Reranker after Patch NN works), WW (Bluesky openrss.org bridge), XX (Chinese lab RSS), YY (retrieval result caching), ZZ (cross-run memory).

---

## 2026-05-04 — Wave 2: Patches PP, SS, RR, VV, II, LL, QQ + Patch NN refactor

**Refactor — Patch NN now uses `claude -p` instead of API key.** Per durable user preference (`memory/feedback_use_claude_code_not_api_key.md`), the LLM disambiguation path no longer requires `ANTHROPIC_API_KEY`. It shells out to `claude -p --tools "" --no-session-persistence --disable-slash-commands --system-prompt <S> --output-format json --model claude-haiku-4-5 <user>` using the user's logged-in Max subscription. `--tools ""` cuts cache_creation from ~28K to ~4.3K tokens per call; back-to-back calls within the 5-min cache TTL get the 90% read discount. Default is now regex-only (zero subscription cost); `--use-llm` flag opts into Haiku disambiguation. Live-tested: correctly tagged "Andrej Karpathy" + "Sebastian Raschka" + "swyx (Shawn Wang)" via @swyx handle, plus extracted nanoGPT, GPT-2, PyTorch entities. Subscription rate-limit cost: ~4.3K tokens per call.

**Patch PP — Critic parallel with verifiers.** Moved critic dispatch from Stage 7 (sequential) to Stage 5 (parallel with citation+fit+structure verifiers). Confirmed via SKILL.md read that critic doesn't gate on verifier verdicts — the dependency was advisory not real. Saves ~3-5 min per run. Stage 7 is now a placeholder section preserving the numbering for backwards reference; Stage 8 (synthesizer final) blocks on Stage 5 outputs (which now include critic.md alongside the three verifier JSONs).

**Patch SS — Canonical-URL dedup at ingestion.** New `build_canonical_url_index()` walks corpus/ once at `ingest/run.py main()` start, producing a `dict[canonical_url, Path]`. `write_one()` now skips writes whose canonical_url is already in the index under a different path, preventing the same arXiv paper from N adapters yielding N chunks. Cost: ~50ms startup scan on 8K chunks; O(1) lookup per write.

**Patch RR — GitHub releases.atom adapter entries.** 7 new entries in `config/sources.yaml` `github_releases:` category: vLLM, llama.cpp, ollama, anthropic-sdk-python, claude-code, transformers, sglang. Generic RSSAdapter handles `releases.atom` feeds (standard Atom format). New source_type `github_release` with directory mapping `corpus/github-releases/`, decay half-life 90d, digest category `releases_and_infra`. Live-tested: vLLM feed returned 10 items in dry-run.

**Patch VV — SEO domain penalty at retrieval.** New `config/domain_penalties.yaml` with 11 initial entries (medium.com 0.6, hackernoon 0.5, locallyuncensored 0.3, etc). `corpus_server/server.py` loads them in `_ensure_state()`, applies `_domain_penalty(url)` as a multiplicative factor in score: `score = rrf * boost * decay * penalty`. Smoke-tested: medium.com → 0.6, www.medium.com → 0.6, blog.medium.com → 0.6 (suffix match), anthropic.com → 1.0 (no penalty on vendor primary sources). Replaces prompt-only Patch AA.

**Patch II — Researcher hard-cap enforcement.** Structure verifier now reads `retrieval_log.jsonl`, counts entries per `agent: researcher-N`, and emits `researcher_cap_check` field in `structure_verifier.json`. Soft signal: cap violation does NOT trigger structure re-dispatch on its own (the calls already happened — can't undo). The synthesizer surfaces the violation in §2 Weakest assumption when verdict=fail. Honesty-contract §9 binds the 8-call cap; this makes it visible.

**Patch LL — Wall-time self-flag at Stage 9.** Synthesizer step 7.5 now reads `manifest.started_at`, computes wall_seconds, and prepends a regression warning to the §2 Plan-usage bullet if >40 min (40 = honesty contract §9 hard ceiling). Independent of token cost — a run can stay under 1.2M tokens but blow wall time on slow web fetches or excessive re-dispatch. Both budgets bind.

**Patch QQ — Podcast adapter (faster-whisper).** New `ingest/adapters/podcast.py` with PodcastAdapter class. Pipeline: RSS parse → audio download → ffmpeg normalize to 16kHz mono WAV → faster-whisper medium (int8, CPU) → markdown transcript. Caches every intermediate artifact (audio, normalized WAV, transcript) so re-runs only re-fetch new episodes. New `ingest/podcasts.py` standalone runner (separate flock from main ingest, separate canonical-url index). New `ops/deep-ai-research-podcasts.timer` + `service` (daily 03:00, CPUWeight=30, IOWeight=30, Nice=15, MemoryMax=4G, TimeoutStartSec=4h). 5 podcast feeds configured: Latent Space, Dwarkesh, MLST, No Priors, Cognitive Revolution. Per-feed episode_cap_per_run=5 caps initial backfill. Excluded from main 15-min timer. Activates with `uv sync --extra podcasts` (faster-whisper is optional dep). ffmpeg required + verified on PATH. Smoke-tested without faster-whisper installed: gracefully logs warning and yields 0 episodes (does not crash).

**Verification status:**
- All 24 eval cases pass (23 ✓, 1 ⏸ blocked_until step_9_twitter_ingestion).
- Smoke tests: ainews dry-run + podcast adapter import + domain penalty unit + cohere-style live test of regex+LLM mention path.
- mypy clean on new files (5 pre-existing errors in run.py unchanged).
- ruff clean except pre-existing RUF002 unicode-style nits matching codebase convention.

**Surprises:**
- The `claude -p` cache_creation cost depends heavily on which flags you pass. Default ~28K tokens for tools loaded; `--tools ""` brings it to ~4.3K. The flag combination matters more than I expected.
- Each separate `claude -p` invocation creates a NEW session by default — back-to-back calls within 5 min get partial cache reuse but not the full 90% discount the API would give within a single session. For batch ingestion enhancement this is fine; for per-chunk-as-it-arrives it'd cost ~$0.008/call which is too much.
- Patch PP dropping from 5 stages (recency/research/draft/verifiers/critic/final) to 4 (recency/research/draft/parallel-verifiers+critic/final) saves a full sequential hop. The wall-time savings should show up immediately in stage_log.jsonl breakdowns once Patch UU snapshots have been captured.
- Podcast feeds have remarkably consistent RSS structure across hosts (Substack, Acast, Transistor, Simplecast). The generic enclosure-extraction logic handled all 5 without per-host code.

**Wave 2 done. Next (Wave 3 P2):**
- TT (Qwen3-Reranker-0.6B after Patch NN works) — cross-encoder over top-K RRF hits
- WW (Bluesky openrss.org bridge) — profile-level RSS for AT Protocol authority handles
- XX (Chinese lab RSS — DeepSeek + Qwen blogs)
- YY (retrieval result caching within run)
- ZZ (persistent cross-run memory via topic-fingerprint lookup)

---

## 2026-05-04 — Wave 3: Patches WW, XX, YY, ZZ, TT

**Patch WW — Bluesky native RSS.** Discovered while investigating openrss.org bridge: Bluesky exposes `bsky.app/profile/<handle>/rss` natively. Direct integration is cleaner than the openrss.org bridge (which 503'd or 429'd repeatedly). 11 verified handles in `config/sources.yaml` `bluesky:` category — Karpathy, Simon Willison, Nathan Lambert, swyx, Sebastian Raschka, Chip Huyen, Soumith, Tri Dao, Demis Hassabis, Anthropic, DeepMind. New source_type `bluesky_post` with 14d decay (similar to tweet), digest bucket `community_pulse`. Live-tested: 29 items from Simon Willison's feed.

**Patch XX — Chinese lab RSS via RSSHub.** DeepSeek and Qwen native blogs lack /feed.xml. RSSHub's `qwenlm/blog` route works (verified 200, returned 5 recent Qwen blog posts including Qwen3Guard, Qwen-Image, GSPO paper, Qwen-MT). Added `qwen_blog` adapter under `lab_blogs:`. DeepSeek RSSHub route 503'd at probe time — skipped for now; can add later when route returns.

**Patch YY — Retrieval result cache within run.** Added in-memory TTL cache (10min, max 256 entries, LRU evict on overflow) to `corpus_server/server.py`. Wraps `search()` and `recent()`. Cache key = JSON-serialized (function_name, args, sorted-kwargs). Smoke test: cold call 10.7s (includes embed model load), cached call 0.0ms — 378,000× speedup on repeat queries within the run. The 10min TTL covers a typical 25-min run with margin while preventing unbounded memory growth on a long-lived MCP server.

**Patch ZZ — Persistent cross-run memory.** New `corpus_server/cross_run_memory.py`. Index format: `.claude/scratch/cross_run_index.json` keyed on run_id, with `{question, finished_at, report_path, embedding}` per record. `find_similar(query, threshold=0.85, top_k=3)` uses arctic-embed-s cosine similarity to surface related past runs. Backfilled all 7 prior reports. Verified: query "best LLM model for personality and memory" returns 3 matches (sim 0.911, 0.904, 0.878) — all from this morning's earlier sessions. Wired into SKILL.md Stage 1 (write `prior_research.json`) and Stage 2 (fold into recency_pass.json under `prior_research_summaries`). Also wired into Stage 9 (`index_run` after final write). Future similar queries inject prior conclusions into the recency-pass context, avoiding redundant research.

**Patch TT — Cross-encoder reranker (skeleton).** New `corpus_server/reranker.py` with sentence-transformers CrossEncoder integration. Default model `BAAI/bge-reranker-v2-m3` (568M params, MTEB-R 57.03, Apache 2.0). Off by default; opt-in via `DAIR_RERANKER_ENABLED=1` env var or `enable: true` in `config/reranker.yaml`. New `[reranker]` optional dep group; `uv sync --extra reranker` installs sentence-transformers + torch. Wired into `search()` after RRF combine: when enabled, replaces RRF as the relevance score (boost / decay / domain_penalty still apply multiplicatively). When disabled, no-op. Qwen3-Reranker-0.6B (MTEB-R 65.80, the report's preferred model) DEFERRED — uses custom AutoModelForCausalLM yes/no token inference that doesn't fit the CrossEncoder API. Bge is the pragmatic default; Qwen3 upgrade is a follow-on patch when sentence-transformers either adds support or someone wires the custom inference code.

**Verification:** All 23 unblocked eval cases still pass. mypy clean on new files. Patch YY verified with timing test. Patch ZZ verified with backfill + similarity query. Patch TT verified default-OFF doesn't break search.

**Surprises:**
- Bluesky native RSS just works. The original recommendation suggested openrss.org as a bridge, but the bridge has rate limits and timeouts. Native RSS is faster and more reliable.
- Cross-run memory similarity scores were higher than I expected — the same-day personality+memory queries clustered tightly at 0.91. This means the gate threshold (0.85) is well-calibrated for genuinely similar queries while still filtering out unrelated ones (queries about "speed" vs "personality" had similarity around 0.4-0.6).
- The reranker's lazy-load pattern was surprisingly important — without `_state` tri-state, every `search()` call would attempt to load sentence-transformers, even when disabled, slowing every query by hundreds of ms.

**Wave 3 done. Where we are:**
- Wave 1 ✓: NN, JJ, UU, OO
- Wave 2 ✓: PP, SS, RR, VV, II, LL, QQ
- Wave 3 ✓: WW, XX, YY, ZZ, TT (skeleton)

**Wave 4 (P3 — long-horizon):**
- AAA — Qwen3-Embedding-0.6B + contextual chunking (1024-dim migration)
- BBB — Eval expansion to ≥30 cases
- CCC — DSPy/GEPA offline prompt optimization (depends on BBB)
- DDD — MCP filter additions (date_range × entity × source_type, corpus_count, corpus_related)
- EEE — Daily digest Haiku per-bucket prose summaries
- FFF — Source-discovery automation (monthly query for unsourced mentioned-entities)
- Future: Qwen3-Reranker-0.6B integration with custom inference code (15% MTEB-R lift over bge)

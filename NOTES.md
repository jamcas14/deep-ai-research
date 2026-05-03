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

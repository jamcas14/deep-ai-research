# System-level improvements and flaws — 10 loops

> Independent system-level audit, distinct from `2026-05-05-quality-review.md` (which targeted the report). This file targets the system itself: code, contract, agents, configs, retrieval strategy, evals, compute envelope, and architectural alternatives. Each loop progressively deeper, with extensive web research in middle-to-late loops.

## Headline preview (full meta-conclusion in §10)

The system is **architecturally sound but operationally over-patched**. 33+ named patches in 72 hours have produced a 330-line orchestrator skill on a 178-line honesty contract running 7 agents over a 25-Python-file ingestion pipeline. The four moat mechanisms (authority graph, time decay, forced contrarian, forced recency pass) are genuinely novel and right. But the patch-on-patch evolution has created **internal documentation drift, untested orchestration paths, and an evaluation framework that exists but doesn't run**.

The five highest-leverage system improvements are:
1. Stop adding patches; do a consolidation refactor (Patches → fewer, larger, named modules)
2. The eval framework needs to actually run — automatically — on every commit touching `.claude/`
3. The verifier needs teeth (HEAD checks, arithmetic, exact-quote matching — see prior review's Patch MMM)
4. Replace single-shot researcher dispatch with iterative refinement (Self-RAG / FLARE pattern)
5. The corpus's strength (longitudinal) and the web's strength (current-spec) need explicit query-class routing — not "same fan-out for every query"

Full per-loop detail below.

---

## Loop 1 — Repo inventory + top-level architecture audit

**Method:** Walk repo. Read PLAN.md, NOTES.md, CLAUDE.md, SKILL.md, honesty_contract.md, all configs. Cross-check documented architecture vs filesystem reality. Identify documentation drift and abandoned components.

### What's there

| Component | Status |
|---|---|
| `PLAN.md` (874 lines) | Full architecture; **partially stale** (see drift table) |
| `NOTES.md` (1012 lines) | Append-only log; 33+ named patches over 2026-05-03 → 2026-05-05 |
| `CLAUDE.md` (72 lines) | Top-level orientation; **stale on synthesizer Opus version** |
| `.claude/honesty_contract.md` (178 lines) | 9 sections; binding on every subagent |
| `.claude/skills/deep-ai-research/SKILL.md` (330 lines) | Orchestrator (Patch J — lives here, not in agent) |
| `.claude/agents/` | 7 agents (researcher, contrarian, critic, synthesizer, verifier, fit-verifier, structure-verifier) |
| `corpus_server/` | MCP server + reranker + cross-run memory (3 Python files) |
| `ingest/` | 25 Python files: 5 adapter classes, embedding, chunking, frontmatter, canonicalization, source discovery, podcasts, arxiv promotion, authority polling, mention detection, run visualization |
| `config/` | 8 YAMLs: authorities, sources, decay, paths, plan, embedding, reranker, domain_penalties |
| `ops/` | 5 systemd-timers (ingest, embed, digest, podcasts, poll-authorities, promote-arxiv, tag-engagements) + install scripts + registry-query |
| `evals/` | 3 Python runners (`run_all.py`, `run_full_loop.py`, `baseline_single_sonnet.py`) + `cases.yaml` + `runs/` archive |
| `tests/` | 3 unit-test files (canonicalize, chunk, frontmatter) |
| `benchmarks/` | OpenRouter/AA scraper |
| `corpus_server/cross_run_memory.py` | Patch ZZ — synthesizer-only cross-run drift detection |
| `digests/` | Daily digest output (Patch BB) |
| `reports/` | 8 reports as of 2026-05-05; the eval seed |
| `analysis/` | New (created today); contains the report-quality review and this file |
| `NEXT_TASK.md` | Hand-off instructions for the current session |
| `docs/_archive/` | Historical Postgres-era docs; preserved per CLAUDE.md |

### Documentation drift — five specific gaps

1. **PLAN.md line 99 says `mcp/corpus-server/`** — actual location is `corpus_server/` at repo root. The path was refactored but PLAN.md not updated.
2. **CLAUDE.md says "Final synthesis on hard queries (conditional): Opus 4.7"** — PLAN.md and SKILL.md (per Patch V) explicitly say **Opus 4.6, NOT 4.7** because of the MRCR v2 regression (78.3% → 32.2% on long-context). CLAUDE.md is stale on a load-bearing model-selection rule.
3. **PLAN.md scratch-dir layout** does not list `usage_snapshot_start.json`, `usage_snapshot_end.json`, `stage_log.jsonl`, `prior_research.json` — all introduced by patches CC, JJ, UU, ZZ. PLAN.md is the "source of truth" but reflects the system as of ~Patch P; everything Patch Q→HHH has grown atop without updating PLAN.md.
4. **CLAUDE.md says `mcp/corpus-server/` for the MCP server** — same drift as #1.
5. **README.md** is "minimal, points at PLAN.md" per NOTES.md — but PLAN.md is itself stale. The first-time-reader path is through stale docs.

### Patch density signal

NOTES.md narrates `Patch A → HHH` plus continued letters (CCC, DDD, EEE, FFF, BBB, AAA) over **3 calendar days** (May 3-5, 2026). Counting unique patch identifiers from NOTES.md's section headers and recent commits:

```
Wave 0:   A B C D E F G H I J K L M N O P     (~16 patches, 2026-05-04)
Wave 1:   Q R S T U V W X                     (~8 patches, 2026-05-04)
Wave 2:   Y Z AA BB CC DD EE FF GG HH         (~10 patches, 2026-05-04)
Wave 3:   II JJ KK LL MM NN OO PP QQ RR SS UU VV WW XX YY ZZ TT
                                              (~18 patches, 2026-05-04)
Wave 4:   AAA BBB CCC DDD EEE FFF GGG HHH     (~8 patches, 2026-05-05)
```

That's approximately **60 named patch identifiers** depending on how you count. **Some patches are documented but explicitly deferred** (per recent commit "Lock AAA + TT skeletons as documented-deferred per compute envelope"). The system **does not have a single source of truth for which patches are live, deferred, or rolled back**.

### What's missing from the architecture

| Missing component | Status |
|---|---|
| Pre-commit hooks for the agent prompts | None — agents are markdown, no syntax/lint check |
| Schema for `manifest.json` | None — contract is implicit; partial documentation in PLAN.md |
| Patch index (which patches live vs deferred) | None |
| Test suite for orchestration | None — only ingest unit tests |
| CI integration | None — repo has no `.github/workflows/` |
| `register-user-mcp.sh` execution evidence | Script exists but unclear if used |
| Twitter/X adapter | "Deferred indefinitely" per CLAUDE.md |
| Letta/Mem0/Graphiti for cross-session continuity (the system's own memory, not the user's) | Not built; relies on `cross_run_memory.py` keyword similarity only |

### Loop 1 verdict

The system is **substantial** (50+ files, 3,000+ LOC, 1,500+ doc lines, 33+ named patches in 3 days) and **architecturally sensible** (markdown-first, native CC primitives, sqlite-vec, no Postgres/Docker bloat). The four moat mechanisms (authority graph, time decay, contrarian, recency pass) are concrete and right.

But: **the patch-on-patch growth has outpaced the documentation refactor cycle**. PLAN.md reflects ~Patch P state; the live system is at ~Patch HHH state. The user will read stale instructions on first contact.

**Loop 1 patch candidates:**
- Add a `PATCHES.md` table: patch ID, status (live/deferred/rolled-back), one-line rationale, files touched
- Refactor PLAN.md sections to reflect post-Wave-4 reality (or accept PLAN.md is now historical and rely on SKILL.md as source-of-truth)
- README.md should describe the moat in two paragraphs, not point at a stale plan

---

## Loop 2 — Honesty contract internal-consistency audit

**Method:** Read every section of `.claude/honesty_contract.md`. Check internal consistency. Cross-reference against the failure modes that occurred in the 2026-05-05 review. Identify gaps and loopholes.

### Contract structure

9 sections + enforcement clause. 178 lines. Read by every subagent at start of task.

| § | Title | Binding constraint |
|---|---|---|
| 1 | No sycophancy | Don't soften conclusions; correct user premises |
| 2 | No vibes-based decisions | Every claim needs evidence or `[judgment]` tag |
| 3 | Capitulation guard | User suggestions are input, not authority; recursive |
| 4 | Confidence levels | `[verified]` / `[inferred]` / `[judgment]` definitions |
| 5 | Permission to disagree with the user | Hold the line on evidence |
| 6 | The "I don't know" branch | Mixed evidence is valid output |
| 7 | Loop on hesitation, but cap the loop | 3 passes max, then commit |
| 8 | Inferred caller intent is not user input | Skip rationale must quote user text |
| 9 | Bounded coverage | Token + wall-time + sub-question budgets |
| Enforcement | "Critic flags violations; eval harness records over time" | No automated mechanism beyond critic prompt |

### Finding 2.1 — Internal contradictions / unresolved interactions

**Contradiction A — §4 vs Patch H definition of `[verified]`:**

§4 (verbatim): "`[verified]` — claim has a cited source you (or another subagent) re-fetched"

This is a **mechanical** definition (re-fetched = exists). The synthesizer prompt's Patch H says "`[verified]` requires verifier `pass` AND ≥2 independent inline sources" — a **substantive** definition (≥2 independent sources). **The contract definition is *weaker* than the patch definition.** When they conflict, which authority wins? The contract claims "binds you absolutely"; the synthesizer prompt is operationally what runs. **No resolution.** The 2026-05-05 review's Loop 3 found 5 of 6 `[verified]` tags pass §4 (re-fetched source exists) but fail Patch H (single source or sources not independent). **Both passes are technically correct under different rules.**

**Tension B — §6 vs §9 on missing options:**

§6 says "I don't know" is valid output. §9 says forgetting an option family is detrimental — every family must appear in §3 matrix. When a family genuinely has no evidence, the resolution is "row exists with `[judgment]` tag and 'no evidence retrieved'". **The contract doesn't explicitly state this resolution.** The 2026-05-05 report does it (DarkIdol/NeuralDaredevil/Wayfarer line 118: "[judgment: absence of search evidence after multiple passes]"), but the practice is ad hoc, not contracted.

**Tension C — §7 vs §9 on time budget:**

§7 says three passes max. §9 says ~25 min target / 40 min ceiling. **Three passes can easily exceed 40 minutes** — and the 2026-05-05 run took 87 minutes. **The contract doesn't reconcile depth-passes with clock-minutes.** A run can comply with §7 (≤3 passes) and violate §9 (>40 min) simultaneously, which is exactly what happened.

**Unresolved D — Cross-run memory vs §3 capitulation:**

§3 says user input is not authority. Patch ZZ injects prior-run conclusions to the synthesizer for drift detection. **Are prior runs (a) the user's input (since they ran the query) or (b) the system's authority (since the system produced them)?** The Patch ZZ revision treats it as drift-detection-only — synthesizer-only artifact, no researcher injection. OK in practice, but §3 doesn't speak to this case. If a future patch decides to feed prior conclusions to researchers (the original Patch ZZ design before the 2026-05-05 revision), §3 doesn't have a clear rule against it.

### Finding 2.2 — Gaps the prior review surfaced that the contract does NOT address

The 2026-05-05 quality review found 6 high-severity issues in the report. Map each to whether the honesty contract has a clause that should have caught it:

| Issue | Loop | Contract clause that should catch it | Actually covered? |
|---|---|---|---|
| §1 cites src30/src31 for claim that src22 supports | 2.1 | "[verified] = re-fetched cited source contains claim" | **NO** — §4 only requires re-fetch, not contain |
| `[verified]` tag attached to mechanism papers for behavioral implication | 3, 4 | Mechanism vs behavior split | **NO** — §4 is one-tag-fits-all |
| Report mis-identifies what PRISM measures | 5 | Source-claim measurement match | **NO** — no clause |
| W_E claim contradicts cited source | 4 | Cited source contains claim | **NO** — same as above |
| abliteration.ai $5/M arithmetic error | 8 | Arithmetic verification on cited rates | **NO** — no clause |
| Willison verbatim quote not in src22 | 8 | Quote-to-source matching | **NO** — §4 doesn't specify |
| 5 prior runs produced 5 different recommendations | 7 | Inter-run drift / consistency | **NO** — §9 is intra-run only |

**Six of seven failure modes from the prior review are NOT covered by any honesty-contract clause.** The contract is binding on principle but silent on most of the specific failure modes the system actually exhibits. Patches A-HHH have been adding *operational* fixes (synthesizer prompt rules, verifier checks) but the *normative authority* (the contract) has not been updated since at least Patch P.

### Finding 2.3 — Enforcement mechanism is weak

The contract's "Contract enforcement" section says: "The critic subagent reads the final report against this contract. Any violation flagged here is a regression. The eval harness records violations over time."

In practice:
1. **The critic is one of four parallel agents in Stage 5** (per Patch PP). It runs on the **draft**, before the final synthesizer pass. The final report (post Stage 8 synthesizer-final) is **not** re-checked against the contract.
2. **The eval harness records violations over time** — but Loop 8 of this audit will show whether evals actually run. Spoiler: there's evidence they don't run on every commit / regularly.
3. **No automated contract-clause-by-clause check exists.** Structure verifier checks §1-§6 conformance; citation verifier checks citations; fit verifier checks recommendation fit; **no agent checks contract-clause compliance**.

The contract is a **document, not a control surface**. Enforcement is by reading.

### Finding 2.4 — Definition gaps that cause downstream confusion

**"Independent sources" (§4 / Patch H):** undefined. Are src21 (the original Anthropic prompt repo) + src22 (Simon Willison's analysis of src21) independent? The 2026-05-05 review's Loop 3 V6 found this borderline. **Definition needed:** two sources are independent if neither cites or analyzes the other within the relevant scope.

**"Re-fetched" (§4):** undefined. Does WebFetch count? Does grep through corpus count? Does HEAD-only count? **Definition needed:** re-fetched means ≥1 successful HTTP 2xx body fetch returning content the verifier can match against the citation.

**"Source quality" (Patch AA):** undefined. SEO aggregators count as 1; what about academic preprints, model cards, vendor docs, blog posts, social-media threads? **Hierarchy needed.**

**"Major claim" (§4):** "Tag each major claim." What's major? In the 2026-05-05 report, almost every paragraph has a tag — but some tags are clearly load-bearing (the headline recommendation) and some are decorative (a side-note about Whisper VRAM). **Definition needed** or remove the word "major" and tag everything that *could* be cited.

### Finding 2.5 — Missing clauses

Six clauses the contract doesn't have but should:

1. **§10 — Citation-graph integrity:** "Every `[srcN]` reference attaches to the source whose body actually contains the claim. Mis-attribution is a §10 violation."
2. **§11 — Mechanism-vs-behavior tag split:** "When a claim is a behavioral implication of a cited mechanism source (rather than directly stated), use `[inferred from mechanism — srcN]`, not `[verified]`."
3. **§12 — Inter-run consistency:** "When prior runs on similar queries exist, surface convergence / divergence in §2. Inter-run drift IS the confidence metric for repeat queries."
4. **§13 — Empirical resolution paths:** "When the recommendation rests on a calculated budget the user can falsify in <60 seconds, surface the falsification command in §1 or §5."
5. **§14 — Source quality hierarchy:** "Primary papers > implementation code > vendor docs > technical blogs > SEO aggregators. Two SEO sources count as one. Two papers do not collapse." (Calibrate Patch AA precisely.)
6. **§15 — Enforcement is automated, not just narrative:** "A `contract-verifier` subagent runs in parallel with structure-verifier, fit-verifier, citation-verifier, and critic. It checks each contract clause against the draft and produces a `contract_check.json` artifact. Hard violations gate Stage 8."

### Loop 2 verdict

The contract is **substantively right but operationally under-specified**. It binds principles but not mechanisms; it covers within-run discipline but not citation-graph integrity, inter-run drift, or empirical-verification suggestions. **Six high-severity failure modes in the 2026-05-05 report exist precisely in the contract's gaps.** A contract revision (adding §10-§15 above) would close most of those gaps; an automated contract-verifier agent would close the enforcement gap.

The current architecture is "contract as guidance + critic reads contract" — the critic is one of four parallel Stage 5 agents and operates on the draft. **The system has no agent whose explicit job is "verify contract clause-by-clause on the final report."** Adding one is a Wave-5+ candidate.

---

## Loop 3 — Agent prompt architecture deep-read

**Method:** Read every agent prompt. Map their tool inventory, inputs, outputs, dependencies. Find redundancy, inconsistency, and unguarded handoffs. Verify that each agent's claimed inputs match what the orchestrator (SKILL.md) actually dispatches.

### Agent inventory and sizes

| Agent | Lines | Tools | Effort (Patch HHH) | Stage |
|---|---|---|---|---|
| researcher | 182 | Read, Glob, Grep, WebSearch, WebFetch, Write | medium | 3 (parallel) |
| contrarian | 216 | Read, Glob, Grep, WebSearch, WebFetch, Write | high | 3 (parallel) |
| synthesizer | **627** | Read, Write, WebSearch, Glob, Grep | high | 4, 8 |
| verifier (citation) | 92 | Read, WebFetch | low | 5 (parallel) |
| fit-verifier | 178 | Read, Write, Glob, Grep | low | 5 (parallel) |
| structure-verifier | 168 | Read, Write | low | 5 (parallel) |
| critic | 153 | **Read only** | medium | 5 (parallel — Patch PP) |

### Finding 3.1 — Tool inventory bugs (two agents claim to write files but lack Write tool)

**Citation verifier** prompt says: "Write `verifier.json`: `{...JSON schema...}`". But its frontmatter is `tools: Read, WebFetch`. **No Write tool.** It cannot write to disk.

**Critic** prompt says: "Output: `.claude/scratch/<run-id>/critic.md`" and provides a full markdown template. But its frontmatter is `tools: Read`. **No Write tool.** It cannot write to disk either.

**Two interpretations:**
1. **Bug:** the orchestrator dispatches these agents and they fail silently to write outputs; downstream consumers (synthesizer at Stage 8) read non-existent files and degrade.
2. **Implicit pattern:** the orchestrator captures the agent's free-text reply (the agent returns the JSON or markdown as its message) and writes the file itself; the prompt's "Output: file.md" is misleading shorthand for "produce content in this format which the orchestrator persists."

If interpretation (2) is correct, the prompts should say: "Return the following JSON structure / markdown template as your reply text. The orchestrator will persist it." Currently the language reads as imperative-write.

If interpretation (1) is the actual behavior, **two of seven agents are silently broken**. The fix is one-line per agent: add `Write` to tools.

This is exactly the kind of issue a test would catch in <5 seconds. **There is no test for agent dispatch + output file presence.** (Tied to Loop 8 below.)

### Finding 3.2 — Critic agent expects Stage 5 inputs that may not exist yet

Critic prompt (lines 27-29):
> Inputs:
> - Path to the verified synthesizer draft (`synthesizer-draft.md`)
> - Path to the citation verifier results (`verifier.json`)
> - Path to the fit verifier results (`fit_verifier.json`)
> - ...

But SKILL.md Stage 5 (Patch PP) says:
> "All four are independent: each reads the draft, **none reads another's output**, output paths are disjoint."

**Direct contradiction.** SKILL.md says critic does NOT read verifier outputs (because they're produced concurrently). Critic prompt says it DOES read them.

Two race-y consequences:
- If Patch PP is correctly implemented and `verifier.json` / `fit_verifier.json` haven't been written when critic starts, critic's Read calls will fail or return stale content.
- The critic prompt section 3 says "The verifier already flagged these in `verifier.json`. Surface them again..." — this ENTIRE section is invalid under Patch PP.
- The critic prompt section 9 says "If `fit_verifier.json` listed any `uncertain_flags_for_critic`..." — also invalid under Patch PP.

**Real impact:** The critic in the 2026-05-05 run either (a) read empty/stale verifier outputs and missed claim issues, or (b) actually waited for the verifier outputs (defeating Patch PP's parallelism). Either way, the agent prompt and the orchestrator are out of sync.

### Finding 3.3 — Citation verifier mentions reading other verifier outputs (also Patch PP violation)

Citation verifier prompt (line 50):
> "Skip: ... Citations that the structure verifier or fit verifier already flagged (those re-runs duplicate effort)."

This **explicitly tells the citation verifier to read the structure-verifier and fit-verifier outputs**. Same Patch PP violation: those run concurrently in Stage 5.

The citation verifier might still pass mechanically (reading non-existent files = no skip), but the prompt is misleading.

### Finding 3.4 — Citation verifier sampling is documented as 12 — but the prior review found 3-of-7 different cut

Citation verifier prompt explicitly lists priority order:
1. Every `[verified]` claim in §1 Conclusion
2. Every direct quoted passage (FACTUM 2026 finding)
3. Every citation flagged for a specific number, date, or statistic
4. Every `[verified]` claim in §2 strongest/weakest
5. Fill remaining with §3 recommended-row claims

The 2026-05-05 review's Loop 8 sampled 7 *different* citations and found 3 fails (43% rate). The prior review's verifier sampled 12 with 3 fails (25% rate). **Combined: at least 6 fails of 19 sampled (32%) on the same draft.** The verifier's 12-citation sample missed the 3 issues the prior review's different cut found:
- src22 (Willison verbatim quote — *should* have been priority #2 under "every direct quoted passage")
- src35 (abliteration.ai pricing — should have been priority #3 under "specific number")
- src36 (Grok docs URL still 404 — no priority bucket covers "URL existence")

**The src22 miss is structurally diagnostic.** It SHOULD have been in the verifier's top 12 because:
- It's a direct quoted passage (priority 2)
- It supports a `[verified]` claim in §3 SQ3 (priority 5)

**Why was it missed?** Possible reasons:
1. Verifier sampled the §1 Conclusion citations (priority 1) and was capped before reaching priority 2.
2. Verifier checked the source existed but didn't string-match the quote.
3. Verifier was operating under wrong priority order due to prompt drift.

The prompt says "12 well-chosen samples" with "FACTUM finding: direct quotes have higher fabrication rates." If src22 was in the top-12, the verifier should have caught it. **Either the priority logic isn't being followed, or 12 is too few.** Patch MMM in the prior review's Loop 10 addresses this with HEAD checks, arithmetic checks, and exact-source-quote matching — those would have caught all 3 missed.

### Finding 3.5 — Synthesizer prompt is 627 lines (4× the next-largest)

The synthesizer prompt is a bloated container of every patch the system has accumulated. By rough count:
- Patches A-Z, AA-ZZ, BBB-HHH all appear in synthesizer prompt either directly or through cross-references
- ~25-30 distinct rules / sub-procedures, each labeled by patch ID
- Two passes (draft + final) interleaved with stage-specific rules

**Cognitive impact:** The agent must process 627 lines of context-specific rules before doing actual work. Token cost per dispatch: ~3-4K tokens just on the prompt. Per pass × 2 passes × 1+ run/day = 6-8K tokens daily on synthesizer prompt overhead alone — plus the model has to *attend* to all of it.

**Refactor candidates:**
1. Extract patch implementations into a `synthesizer-rules.md` referenced by the prompt
2. Move "draft pass" rules and "final pass" rules into separate agent files (`synthesizer-draft.md` + `synthesizer-final.md`)
3. Cap prompt at 200 lines; longer prompts go through external lookup

The 2026-05-05 run's 47-minute synthesizer_final stage isn't unrelated to this — the model is parsing a long, dense, partially-redundant prompt before doing 90% of the work that matters.

### Finding 3.6 — No agent prompt explicitly handles "claim trace" annotations (Patch III prerequisite)

The prior review's proposed Patch III requires the synthesizer to emit `<!-- claim-trace srcN: "exact quoted passage" -->` annotations and the verifier to consume them. **None of the current agent prompts contain anything about claim-trace annotations.** This is expected (Patch III isn't shipped yet) but flags the synthesizer's current approach: claims are attached to `[srcN]` tags with no machine-readable bridge to the source's text. The verifier's job is harder than it should be because the bridge is implicit.

### Finding 3.7 — Inconsistent honesty-contract path

Every agent's prompt says `/home/jamie/code/projects/deep-ai-research/.claude/honesty_contract.md`. But the actual project root is `/home/jamie/projects/deep-ai-research/` (no `code/`). **All seven agent prompts have a stale path.** This won't break — when the agent reads the file, the path is invalid; the agent silently proceeds without contract internalization, OR the orchestrator passes the correct path inline (Stage 3 dispatch passes the absolute path).

Per SKILL.md Stage 3:
> "The absolute path to the honesty contract: `/home/jamie/code/projects/deep-ai-research/.claude/honesty_contract.md`"

**SKILL.md has the same stale path.** The system has been operating with broken contract-load instructions, and either (a) the contract is loaded by another mechanism (not visible in dispatch), or (b) the contract has not been loaded at all in dispatched subagents — they're reading nothing.

If (b): every subagent has been operating without the contract internalized. The honesty discipline observed in the 2026-05-05 report's tag distribution and self-flagging is a result of the *prompts themselves* (which reproduce contract rules inline) more than the *contract being read*. The contract is binding in name; in practice the agent prompts duplicate the contract's rules locally.

This is recoverable (correct the path everywhere; one-line fix per file) but tells a story: **the contract has been a redundant artifact, and removing it would not change agent behavior** because every agent prompt has its rules baked in.

### Finding 3.8 — No agent owns "drift detection across runs"

Patch ZZ (cross-run memory) is described in SKILL.md as a synthesizer-only artifact: synthesizer reads `prior_research.json` and renders a `Cross-run continuity` sub-bullet in §2.

But: the synthesizer prompt's §2 specification doesn't mention this sub-bullet. The structure-verifier's §2 check requires four sub-bullets (Strongest evidence / Weakest assumption / What would change my mind / Sources / Plan usage — actually five if you count Plan usage). **No mention of "Cross-run continuity" as an expected sub-bullet.**

So when the cross-run memory file exists with prior matches, the synthesizer is supposed to emit the sub-bullet, but the structure-verifier doesn't check it, and the synthesizer's prompt doesn't either describe the sub-bullet's format. Patch ZZ is **half-implemented**: index exists, retrieval mechanism exists, no agent specifies the rendering.

### Finding 3.9 — Researcher and contrarian are similar in size and overlap on tool inventory

Researcher (182 lines) and contrarian (216 lines) have nearly identical tool inventories (Read, Glob, Grep, WebSearch, WebFetch, Write) and nearly identical structural roles (run a sub-question with retrieval, write findings to scratch). The contrarian has explicit "find the answer the lead agent will miss" framing.

Question: **Is the contrarian a structurally distinct agent, or a researcher with a different prompt?** Looking at the prompts:
- Researcher: structured around "must_cover_families" — the lead's predetermined option list
- Contrarian: structured around "the obvious answer label" → search differently → produce micro/macro contrarian sections
- Both have similar 8-call vs 5-call retrieval caps (researcher 8, contrarian 5)
- Both write to `<role>-gen<G>.json`

**Refactor opportunity:** consolidate into one researcher template with a `mode: standard|contrarian|deep_dive` parameter. Reduce two prompts to one + mode-specific instructions.

This is *not urgent* — the current separation works. But Loop 10's v2 proposal could include it.

### Loop 3 verdict

| # | Severity | Issue |
|---|---|---|
| 3.1 | **High** | Two agents (citation verifier + critic) lack Write tool but claim to write files |
| 3.2 | **High** | Critic prompt expects verifier outputs that don't exist under Patch PP parallelism |
| 3.3 | Medium | Citation verifier prompt also references concurrent-stage outputs |
| 3.4 | High | Citation verifier missed quoted-passage fabrication that should have been priority-2 sample |
| 3.5 | Medium | Synthesizer prompt is 627 lines — bloated, expensive per dispatch |
| 3.6 | Low | No claim-trace annotation pattern in any agent (prerequisite for Patch III) |
| 3.7 | **High (silent)** | All 7 agents reference a stale honesty-contract path; contract may be effectively unloaded |
| 3.8 | Medium | Patch ZZ cross-run-continuity sub-bullet is undocumented in synthesizer + structure-verifier |
| 3.9 | Low | Researcher and contrarian could consolidate |

**Three high-severity items: 3.1, 3.2, 3.7.** Each is one-line-fix (add Write tool / fix path) but currently silently impacts every run. **The contract-path issue is particularly concerning — the system's honesty foundation may be operationally bypassed.**

The agent architecture is **organizationally sensible** (seven specialized roles, parallel where possible, clear handoffs in PLAN.md / SKILL.md) but **operationally inconsistent** (prompts reference inputs that don't exist, tools missing from frontmatter, paths wrong). **The patch-on-patch growth has not been accompanied by agent-prompt-consistency refactors.**

---

## Loop 4 — Authority graph + sources + decay audit

**Method:** Read all 8 config YAMLs. Audit completeness of authorities. Audit source coverage against the 2026-05-05 query's 9% corpus / 91% web ratio. Critique decay calibrations. Domain penalties.

### authorities.yaml — 50 entries, mostly canonical

**Tier distribution:**
- canonical (1.0): 26
- trusted (0.7): 21
- signal (0.5): 3
- **Total: 50** (the file says "aim for 50-200")

**Coverage assessment by category:**

| Category | Coverage | Notable gaps |
|---|---|---|
| Frontier-lab leads | Good | All major CEOs/research leads present (Hassabis, Amodei, Brockman, Murati) |
| Deep-learning OG | Good for Hinton/LeCun; **missing Yoshua Bengio** (3rd Turing co-recipient), **missing Andrew Ng**, **missing Fei-Fei Li**, **missing Geoffrey Hinton** is there |
| Architecture / systems | Good (Tri Dao, Albert Gu, Noam Shazeer, Alec Radford) |
| Interpretability / mech-interp | **WEAK** — missing Chris Olah (Anthropic), Neel Nanda (DeepMind), Trenton Bricken / Adam Jermyn (Anthropic interp). The interp community has a strong authority graph the system doesn't capture. |
| Alignment / safety | Sam Bowman, Jack Clark, Dario Amodei, John Schulman present. **Missing Jan Leike**, **missing Paul Christiano**, **missing Ajeya Cotra**, **missing Jacob Steinhardt**, **missing Buck Shlegeris** |
| Open-weight / community | **WEAK** — missing Eric Hartford (Cognitive Computations / Dolphin finetunes), missing TheBloke (retired but legacy), missing huihui-ai (HuggingFace abliteration leader), missing mlabonne (the abliteration tutorial author cited in 2026-05-05 report). **The community-finetune authors who matter for Tier-T queries are absent**, which directly explains the corpus's thinness on Tier-T model recommendations. |
| Open-source frameworks | Harrison Chase (LangChain), Jerry Liu (LlamaIndex) present. Missing Patrick von Platen (HF transformers), Lewis Tunstall (HF), Omar Sanseviero (HF), Sebastian Raschka (Lightning + ed.) |
| Educators / commentators | Karpathy, Riley Goodside, Ethan Mollick, swyx, Dwarkesh present. Missing **Sebastian Raschka** (Ahead of AI newsletter is a major signal source, but Raschka himself isn't tagged authority), missing **François Chollet** (ARC challenge — major in 2026), missing **Jeremy Howard** (fast.ai), missing **Simon Willison** (his blog is cited heavily in 2026-05-05 report — but he's not tagged authority) |
| Safety researchers external | **Missing Stuart Russell, Eliezer Yudkowsky, Connor Leahy, Helen Toner** |

**The biggest gap:** community open-weight authors. The 2026-05-05 query was about huihui-ai/Qwen3-14B-abliterated; the system uses the very citations (mlabonne blog, huihui model cards) that authority-tagging the relevant authors would surface from corpus-first instead of web-first.

**Specific recommended additions** (priority order based on 2026-05-05 query patterns):

1. mlabonne (huggingface.co/mlabonne) — abliteration tutorial author
2. huihui-ai (huggingface.co/huihui-ai) — abliterated finetune publisher
3. EVA-UNIT-01 (huggingface.co/EVA-UNIT-01)
4. anthracite-org / TheDrummer
5. Eric Hartford (Cognitive Computations / Dolphin)
6. Sebastian Raschka (Ahead of AI)
7. Simon Willison (simonwillison.net)
8. François Chollet (ARC challenge — high-signal in 2026)
9. Chris Olah, Neel Nanda (interp)
10. Yoshua Bengio, Andrew Ng (canonical-tier educators)

### sources.yaml — 52 sources, but missing structural feeds

**Categories:**
- newsletters: 4 (ainews, import_ai, tldr_ai, last_week_ai)
- lab_blogs: ~20 (Anthropic, OpenAI, DeepMind, Meta, Mistral, Cohere, etc.)
- reddit: present
- hn: present
- hf_daily_papers: present (papers but NOT model cards)
- podcasts: Patch QQ (faster-whisper transcription)
- benchmarks: empty `[]` ← still Step 8 placeholder
- github_releases: present
- bluesky: Patch WW

**Missing from sources.yaml** that explain the 2026-05-05 corpus weakness on Tier-T:

1. **HuggingFace authority-author adapter** — the model cards for huihui, mlabonne, EVA-UNIT-01, anthracite-org, etc. are the source of truth. None ingested. The corpus has paper releases (`hf_daily_papers`) but not author pages or model-card updates. **This is the single biggest gap.**

2. **Anthropic Research Blog** — `anthropic.com/research` (separate from `anthropic.com/news` which is in sources.yaml). The Research Blog is where alignment + interp work lands.

3. **Hugging Face Blog** (`huggingface.co/blog`) — has the mlabonne abliteration post + many ecosystem posts. Not in sources.yaml.

4. **The Gradient** (`thegradient.pub`) — listed as commented-out TBD.

5. **Ahead of AI** (`magazine.sebastianraschka.com`) — listed as commented-out TBD.

6. **Simon Willison's blog** (`simonwillison.net/atom/everything/`) — listed as commented-out TBD. And the 2026-05-05 report cites it directly (src22), demonstrating this is a high-signal feed that should be ingested.

7. **Eugene Yan** (`eugeneyan.com/rss`) — TBD.

8. **Interconnects** (`interconnects.ai/feed`) — TBD.

9. **LessWrong / AI Alignment Forum** — alignment community discussions.

10. **Distill / Transformer Circuits Thread** — interpretability publications.

The TBD comments suggest these were planned but deferred. **Many high-signal feeds are documented-but-not-shipped** — same pattern as the deferred patches.

**Twitter/X is "deferred indefinitely" per CLAUDE.md.** Authoritarian decision driving the corpus gap on AI/ML where Twitter-equivalent is essentially the discussion layer. **The Bluesky adapter (Patch WW) is a partial substitute**, but only for users who migrated from X. Many AI researchers are still primarily on X.

### decay.yaml — 11 content types, two recent additions, calibration issues

```yaml
tweet: 7
reddit_post: 14
hn_post: 14
newsletter_issue: 60
blog_post: 60
lab_blog_architecture: 180  ← Patch RR
arxiv_paper: 365
podcast_episode: 90
hf_daily_papers: 30
github_release: 90  ← Patch RR
bluesky_post: 14    ← Patch WW
```

**Calibration concerns:**

1. **`blog_post: 60` is too short for foundational posts.** A blog post explaining mechanism (e.g., the Anthropic interpretability blog circa 2024) is still relevant 2 years later. The 60-day half-life means by month 6 it has weight ≈ 0.06, effectively dropped.

   **Patch RR partly addresses this with `lab_blog_architecture: 180`** — but the carve-out is for *lab blogs only* and only for *architecture* posts. A non-lab architecture post (e.g., grimjim's projected-abliteration blog) still gets the 60-day half-life.

   **Better:** add a `tag: evergreen` mechanism in frontmatter that overrides decay. Posts the user manually tags `evergreen` decay slowly regardless of source type.

2. **`hn_post: 14`** is reasonable for the HN homepage, but HN Show / HN Ask threads are sometimes referenced for years. Single half-life across all HN posts may be too aggressive.

3. **`tweet: 7`** — Twitter ingestion deferred, so this is unused. Should be marked deprecated or removed until ingestion ships.

4. **`hf_daily_papers: 30`** — papers themselves don't decay in 30 days. The half-life here represents *the daily-papers-feed prominence*, which is correct (a paper that was on Daily Papers a month ago is no longer the recency signal). But the corpus stores the underlying paper, which probably shouldn't decay at all per Patch RR's logic. **Mismatch between the feed-importance signal and the paper-permanence signal.**

5. **`github_release: 90`** (Patch RR) — frameworks evolve fast. A 90-day half-life means a llama.cpp release from 6 months ago has weight 0.06. For framework recommendations, this is right; for *historical* discussion of when feature X was introduced, this is too aggressive.

**Missing content types:**
- `hf_model_card` — would need its own half-life (model cards update rarely; abliterated finetunes once-per-base-model release)
- `paper_review` — peer reviews and critiques of papers
- `release_notes` — sometimes distinct from `github_release`

### domain_penalties.yaml — Patch VV addition; reasonable

10 penalty entries. Largely SEO-aggregator suppression. Reasonable hierarchy:
- 0.7 → mild (mixed-signal mainstream tech blogs)
- 0.5 → moderate (general aggregators)
- 0.3 → strong (SEO listicle farms)
- 0.1 → near-suppression (link-spam)

**Calibration assessment:**
- `medium.com: 0.6` — defensible but harsh. Some medium posts are research-grade.
- `dev.to: 0.6` — same as medium; src34 in 2026-05-05 report (juandastic) was a dev.to post, *not* SEO listicle but legit benchmark blog. **The blanket 0.6 might suppress legit signal.**
- `hackernoon: 0.5` — mostly SEO; defensible.
- `locallyuncensored.com: 0.3` — surfaces in Tier-T query class; correct strong discount.
- `superannotate.com / encord.com: 0.4` — vendor blogs with marketing tilt; correct.

**Missing from penalties:**
- `freeCodeCamp.org` — content-mill output increasingly
- `kdnuggets.com` — partly SEO-recycled content
- `analyticsindiamag.com` — heavy SEO content for AI topics
- `marktechpost.com` — high-volume AI news with SEO patterns; cited in prior runs (R3 src: web-hermes4-marktechpost) without penalty

### plan.yaml — token budget approximation

`max-200: 50_000_000` (50M tokens / month for $200 Max plan).

**Reality check:** Per the 2026-05-05 review's Loop 9, telemetry is broken — `usage_snapshot_start` / `usage_snapshot_end` are null. The plan.yaml token budget is therefore comparing an unknown numerator to a known denominator. **The plan-usage metric in §2 confidence panel is currently uncomputable for actual runs.** Patch CC + JJ tried to fix this; not yet operational on the 2026-05-05 run.

50M tokens / 30 days = ~1.67M tokens/day allowance. The 2026-05-05 run used ~600K-1M+ tokens (estimated). **One run/day fits the daily-average budget; 2-3 runs/day would deplete it.** Loop 9 (compute envelope) below validates this more rigorously.

### Loop 4 verdict

| # | Severity | Issue |
|---|---|---|
| 4.1 | **High** | Open-weight community authority gap — mlabonne, huihui-ai, EVA-UNIT-01, anthracite-org missing from authorities.yaml |
| 4.2 | High | HuggingFace model-card / author-page adapter missing; explains 9% corpus / 91% web ratio for Tier-T queries |
| 4.3 | Medium | Many high-signal feeds documented-but-deferred (Simon Willison, Ahead of AI, Interconnects, The Gradient) |
| 4.4 | Medium | Decay model is per-content-type; should support per-source / tag-based override (`evergreen` flag) |
| 4.5 | Low-Medium | Domain penalties may suppress legit signal (dev.to blanket 0.6 caught a legit benchmark post) |
| 4.6 | Low | Twitter/X deferred indefinitely; Bluesky partial substitute; AI/ML discussion layer is structurally absent |

**The 9% corpus / 91% web ratio in the 2026-05-05 report is direct evidence of these gaps.** The corpus is well-suited to longitudinal AI/ML *trends and discussion* and structurally weak on *current open-weight model specs*. Adding the HF authority-author adapter (and 5-10 community authors to authorities.yaml) would close ~50% of the gap for Tier-T queries.

---

## Loop 5 — Retrieval strategy critique with web research

**Method:** Read corpus_server retrieval implementation. Web-search current (2025-2026) literature on hybrid retrieval, RRF fusion, FLARE/Self-RAG/CRAG/A-RAG, HyDE, late interaction. Compare the system's RRF k=60 + BM25 + vector approach against the state-of-the-art for agent-driven research.

### Current retrieval architecture

Per `corpus_server/server.py`:
- **Hybrid:** FTS5 keyword (BM25-like) + sqlite-vec semantic
- **Fusion:** RRF k=60 over top-100 from each retriever
- **Score modifications:**
  - Authority-engagement boost (cap 4.0×)
  - Per-content-type recency decay (`config/decay.yaml`)
  - Per-domain penalty multiplier (Patch VV — `config/domain_penalties.yaml`)
- **Reranker:** **none** in v1; `bge-reranker-v2-m3` deferred ("if evals demand")
- **Top-N:** 20 by default, 100 candidates

### Single-shot vs iterative retrieval

The corpus server is **single-shot retrieve-then-generate**. Each researcher's 8 retrieval calls are independent; the orchestrator dispatches researcher → researcher reads results → researcher writes findings. No iterative refinement loop. **The 2025-2026 frontier has moved past this.**

### Finding 5.1 — RRF k=60 is reasonable but not optimal in 2026

Per [Andrey Chauzov's hybrid-retrieval blog (2025)](https://avchauzov.github.io/blog/2025/hybrid-retrieval-rrf-rank-fusion/):
- RRF outperforms min-max / z-score normalization on most hybrid setups
- **But** "convex combination methods outperform RRF on all tested datasets in terms of NDCG, and tuning for RRF is less sample efficient and less robust to domain shift"

The system chose RRF for **simplicity and zero tuning** — defensible for personal use. But on AI/ML query distribution, **the per-query optimal weight between BM25 and vector likely varies** (BM25 better for entity-name queries like "DeepSeek V4"; vector better for conceptual queries like "memory architecture for agents"). RRF's parameter-free fusion gives up that adaptation.

**Improvement candidate:** add a query-type classifier to weight BM25/vector dynamically. Entity queries → BM25-heavy; conceptual queries → vector-heavy; unclear → RRF as fallback.

### Finding 5.2 — No reranker is a *real* gap, not a defer-able one

Per the TREC iKAT 2025 challenge result quoted in the search above: "two parallel query rewrites generated candidate lists fused with RRF, **and then reranked by a cross-encoder**. Fusing before reranking yielded optimal results, with nDCG@10 improving from 0.4218 (no fusion) to 0.4425."

The "RRF + cross-encoder" combination is **the consensus 2026 production pattern**. The system has RRF; it does not have the cross-encoder. **The "defer until evals demand" framing is mistaken** — the eval framework (Loop 8 below) doesn't actually run, so the demand signal can't fire. The reranker is being deferred indefinitely by accident.

**Improvement candidate:** ship `bge-reranker-v2-m3` (already named in PLAN.md) on top-20 candidates. ~350ms per pair on CPU per PLAN.md → ~7 sec for top-20. Acceptable on background dispatch; trades 7 seconds for substantial precision gain.

### Finding 5.3 — System is on the wrong side of the agentic-RAG transition

The frontier has moved to **iterative, agentic retrieval** in 2025-2026:

| Pattern | What it does | Status in this system |
|---|---|---|
| **Self-RAG** ([2310.11511](https://arxiv.org/abs/2310.11511)) | Model emits "retrieval needed?" / "is this evidence relevant?" tokens; iterates | Not present |
| **CRAG** (Corrective RAG) | Detects irrelevant retrieval, reformulates query, retries | Not present |
| **FLARE** ([2305.06983](https://arxiv.org/abs/2305.06983)) | Triggers retrieval mid-generation when token confidence drops | Not present |
| **A-RAG** ([2602.03442](https://arxiv.org/abs/2602.03442)) | Hierarchical retrieval interfaces (keyword / semantic / chunk-read) exposed as tools | **Closest to present** — corpus MCP exposes 4 tools |
| **HyDE** ([Haystack](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde)) | Generate hypothetical doc with LLM, embed, retrieve nearest real docs | Not present |
| **Adaptive RAG** | Query-class-conditional routing (no retrieval / single retrieval / multi-step retrieval) | Not present |

The current system is **closest to A-RAG** (hierarchical retrieval tools exposed via MCP) but is missing the **adaptive trigger and self-critique** layers. A researcher subagent today does 8 retrieval calls in a single pass; if the first 3 calls return junk, calls 4-8 don't recover by *changing strategy* — they continue down the original retrieval direction.

**Improvement candidate (largest single leverage point):** make the researcher subagent agentic-retrieval-aware. Specifically:
1. After each retrieval call, the researcher emits a self-evaluation: "is this evidence relevant? sufficient? do I need to reformulate?"
2. If self-eval says "irrelevant", reformulate the query (HyDE-style or rewrite-prompt) and re-retrieve
3. If "sufficient", stop early — don't burn the remaining 8-call budget
4. Cap iterations at 8 calls total (current cap remains the upper bound)

This is **fundamentally what the system needs for the 9%/91% corpus/web problem**: when the corpus is thin, the researcher should *recognize* thinness on call 1 and pivot to web-heavy strategy on call 2 — not after burning 4 corpus calls discovering thinness.

### Finding 5.4 — HyDE for query expansion is a free win

Per [Zilliz HyDE blog](https://zilliz.com/learn/improve-rag-and-information-retrieval-with-hyde-hypothetical-document-embeddings) and 2025 benchmarks:
- HyDE bridges the semantic gap between short queries and longer documents
- 2025 results: HyDE + answer-context retrieval improved Helpfulness +20% vs standard RAG; HyPE (HyDE variant) +42pp precision, +45pp recall on some datasets
- Latency cost: 25-60% increase on small LLMs — **manageable**, given researchers already invoke LLMs

For this system specifically: when a researcher receives a sub-question like "memory frameworks for agents", standard retrieval embeds the *question*. HyDE would embed the *expected answer document* — much closer to actual indexed content. Per the search, HyDE gives 20%+ helpfulness lift on similar query patterns.

**Improvement candidate:** add HyDE to the corpus MCP. New tool: `corpus_search_hyde(query, hypothetical_doc)` where the synthesizer generates the hypothetical doc inline before retrieval.

### Finding 5.5 — Query-rewriting for entity disambiguation is missing

The 2026-05-05 run had a Mistral-Small-3.1-24B Imatrix Q3 model-identity collapse (Loop 2.3 of prior review): two different models (DavidAU's MAX-NEO-Imatrix vs BeaverAI's Fallen) got conflated under one name. **A query rewriter could have caught this** by:
1. Detecting that "Mistral-Small-3.1-24B Imatrix Q3" is an under-specified entity
2. Issuing two distinct queries (one per author) instead of one collapsed query
3. Surfacing both as separate matrix rows

Modern agentic-RAG systems (A-RAG, MELT) include explicit query-rewriting steps. The system has none. The closest analog is the entity_version path (Patch GG) which does `ops/registry-query.sh` for HF Hub + OpenRouter — but that's only for entity-version queries, not for entity disambiguation generally.

### Finding 5.6 — Late interaction (ColBERT v2) is missing

The system uses **bi-encoder** retrieval (snowflake-arctic-embed-s). ColBERT v2 (late interaction) is consensus-better for AI/ML technical retrieval as of 2024-2025 because it preserves token-level similarity rather than collapsing to a single vector. The trade-off:
- Bi-encoder: 1 vector per doc; fast retrieval; weaker semantic precision
- ColBERT: per-token vectors; slower; stronger precision

For 25-50K markdown docs (the corpus's stated maturity target), ColBERT v2 is feasible on CPU with `colbert-ai` or `RAGatouille`. Memory cost: ~2-4× the embedding storage, but still well under 1GB at 50K docs.

**Improvement candidate (lower priority than 5.3):** evaluate ColBERT v2 vs current bi-encoder on the eval set. If precision lift > 10% at the cost of 2× memory, switch.

### Finding 5.7 — Reranker would catch the SEO-aggregator domain leakage

`config/domain_penalties.yaml` is a **retrieval-time** score multiplier — applied to the candidate before fusion. It pushes SEO content down but doesn't prevent it from entering the candidate pool.

A cross-encoder reranker is **post-fusion** semantic scoring — it would catch high-BM25-keyword-match SEO listicles that nonetheless are weak signal because their *content* doesn't actually answer the query. Domain penalty + reranker combine well; either alone has gaps.

### Finding 5.8 — The corpus's MCP is small (4 tools); A-RAG suggests more granular tools

A-RAG exposes `keyword_search`, `semantic_search`, `chunk_read` as separate tools. The current MCP exposes (per PLAN.md "4 tools max"):
- `corpus_search` (hybrid)
- `corpus_recent` (recency-filtered)
- `corpus_fetch_detail` (read full source)
- `corpus_find_by_authority` (authority-graph filtered)

These are *task-oriented* (what the researcher wants to do) rather than *retrieval-mechanism* (which retriever to use). A-RAG's argument: exposing both axes lets the agent learn when to use which retriever. **Defensible system design choice; not strictly worse, just different ergonomics.**

### Loop 5 verdict

| # | Severity | Issue |
|---|---|---|
| 5.1 | Low | RRF k=60 is reasonable; convex combinations slightly better at cost of tuning |
| 5.2 | **High** | No cross-encoder reranker; deferred-pending-eval but eval framework doesn't fire |
| 5.3 | **High** | Single-shot retrieval; missing iterative/agentic patterns (Self-RAG, CRAG) — biggest leverage |
| 5.4 | Medium | HyDE query expansion would close ~20% of the precision gap |
| 5.5 | Medium | No query rewriting for entity disambiguation; explains some prior-review failures |
| 5.6 | Low | Bi-encoder vs ColBERT v2 — defer until corpus reaches 25K+ docs |
| 5.7 | Medium | Domain penalty alone misses SEO content with high keyword match |
| 5.8 | Low | MCP tool ergonomics (task-oriented) is fine; A-RAG's mechanism-oriented split is alternative |

**Top three improvements:**
1. **Ship the cross-encoder reranker** (`bge-reranker-v2-m3`) — already named in PLAN.md, ~7 seconds latency for top-20
2. **Add iterative retrieval to the researcher** — self-critique + reformulation; biggest leverage on the 9%/91% corpus/web ratio problem and on the over-decomposition cost
3. **Add HyDE-style query expansion** — particularly for sub-questions phrased as questions vs document descriptions

Sources:
- [A-RAG: Scaling Agentic Retrieval-Augmented Generation](https://arxiv.org/abs/2602.03442)
- [Agentic RAG Survey](https://arxiv.org/html/2501.09136v4)
- [SoK: Agentic Retrieval-Augmented Generation](https://arxiv.org/html/2603.07379v1)
- [FLARE: Active Retrieval Augmented Generation](https://arxiv.org/abs/2305.06983)
- [HyDE — Haystack docs](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde)
- [RRF hybrid retrieval — Andrey Chauzov 2025](https://avchauzov.github.io/blog/2025/hybrid-retrieval-rrf-rank-fusion/)
- [Glaforge — Advanced RAG RRF in Hybrid Search 2026](https://glaforge.dev/posts/2026/02/10/advanced-rag-understanding-reciprocal-rank-fusion-in-hybrid-search/)

---

## Loop 6 — Comparison to commercial deep-research products

**Method:** Web-research what Perplexity Pro, Claude Research, OpenAI Deep Research, Gemini Deep Research, exa.ai, STORM (Stanford) do in 2026. Identify where this system has a structural edge, where it's behind, and where the gap is closeable.

### Commercial landscape — 2026 state

| Tool | Runtime | Report shape | Notable feature | Reported citation accuracy |
|---|---|---|---|---|
| Perplexity Pro Sonar Deep Research | <3 min typical | Short, encyclopedic briefing | Pay-as-you-go API ($2/$8 per M tokens) | 78-94% (DRBench range) |
| OpenAI Deep Research | 15-25 min | Longest reports; deepest reasoning | 26.6% on Humanity's Last Exam at launch | 78-94% (DRBench range) |
| Claude Research | 5-45 min | Long-form synthesis | Sonnet 4.5 / Opus 4.5; 200K (1M beta) context | 78-94% (DRBench range) |
| Gemini Deep Research | Variable | Workspace-integrated | Best for Google Docs / Drive corpora | 78-94% (DRBench range) |
| Exa Deep (March 2026) | Faster, cheaper | Structured outputs, field-level grounding | Multiple parallel search agents | Not benchmarked |
| STORM (Stanford OSS) | ~15 min | Wikipedia-style outline | Multi-perspective query synthesis; open-source | Not benchmarked |
| **deep-ai-research (this system)** | **87 min** (last run) | §1-§6 structured, recommendation-focused | Authority graph + forced contrarian + recency + corpus | **~84% on the audit** (16% issues across combined samples) |

### Finding 6.1 — This system is 5-30× slower than commercial alternatives

Perplexity Sonar: <3 min. OpenAI Deep Research: 15-25 min. Claude Research: 5-45 min. **This system: 87 min on the 2026-05-05 run, or 25 min target with 40 min ceiling per §9.**

Even the §9 *target* (25 min) is comparable to OpenAI Deep Research's typical runtime; the *actual* wall time is at the upper end of Claude Research's range. **The system is operationally slow and not compensated by a clear quality edge** that the commercial benchmarks would surface. The 2026-05-05 report was "outcome-correct" per the prior review but contained 6 high-severity citation issues — comparable failure rate to commercial tools.

The slowness is not coming from doing more research; it's coming from synthesizer overhead (47 min of synthesizer_final stage alone, per Loop 9 prior review). **Per minute of user wait, the system is producing less output than commercial alternatives.**

### Finding 6.2 — The four moat mechanisms ARE structurally novel

Comparing the four advertised mechanisms vs commercial systems:

| Mechanism | Perplexity | OpenAI DR | Claude Research | Gemini DR | exa Deep | STORM | This system |
|---|---|---|---|---|---|---|---|
| Hand-curated authority graph | No | No | No | No | No | No | **Yes** |
| Per-content-type time decay | Search recency only | Search recency only | Search recency only | Search recency only | Search recency only | No | **Yes** |
| Forced contrarian subagent | No | No | No | No | No | Multi-perspective (closest analog) | **Yes** |
| Forced recency pass | Default-yes (search-first) | Default-yes (search-first) | Default-yes (search-first) | Default-yes | Default-yes | No | **Yes (explicit)** |

**The authority graph is the genuinely unique mechanism.** The other three are present in some form in commercial tools, but the explicit "forced contrarian agent finds the answer the lead missed" is a structural novelty. STORM's multi-perspective queries are the closest analog but operate differently (synthesizing diverse expert views rather than red-teaming the lead's recommendation).

**The recency pass is novel as an *explicit* stage** — commercial tools get it implicitly through search-first design. Making it explicit means the system can guarantee it fires (per honesty contract); commercial tools rely on the search engine's freshness without architectural guarantee.

### Finding 6.3 — Citation reliability is in the typical commercial range

Per [Citation Hallucination Benchmarks 2026](https://arxiv.org/html/2604.03173) and DRBench:
- DRBench citation accuracy across systems: **78-94%**
- Even RAG-enabled systems fabricate **3-13% of citation URLs**
- GhostCite (40 domains, 375K citations, 13 LLMs): **14-95% hallucination range**
- Citation accuracy is "the worst-performing task family across the frontier" — average 12.4% hallucination rate even with extended thinking
- ICLR 2026: 50 papers with hallucinations missed by 3-5 peer reviewers
- 10× increase from 2024 (0.28% of papers with fabricated refs) to 2025 (2.59%)

**This system's audited rate (~16% issues across 19 sampled citations in the 2026-05-05 report) is at the *worse* end of typical commercial performance** but well within the industry range. The system is *not exceptional* on citation reliability — same problem-class as the rest of the field, with the same root cause (LLM hallucination of plausible-sounding sources).

**However:** the system has structural mechanisms (citation verifier, structure verifier, fit verifier) that commercial tools lack. The infrastructure exists; the verifier currently has blind spots (Loop 8 prior review). **Patch MMM (HEAD checks, arithmetic verification, exact-quote matching) would push this to ~5-8% issue rate — at the better end of commercial.** This is the highest-leverage single improvement.

### Finding 6.4 — The system has a real edge on persistent local corpus

None of the commercial tools have a *persistent local corpus that grows over time*. They all do session-time web search. This system's corpus:
- Continuously ingests AI/ML feeds via systemd-timer
- Embeds with snowflake-arctic-embed-s
- Authority-tags engagement edges
- Applies per-content-type decay
- Survives across sessions (gitignored but on disk)

**For repeat queries on overlapping topics, the corpus accumulates evidence over weeks**. Commercial tools start fresh each query. **The drift-detection problem in Loop 7 of the prior review is partially explained by this** — the system's corpus has been growing while the user's query was repeated 5 times in 24 hours, so each run had marginally different available evidence. Commercial tools wouldn't have this problem (each starts fresh) but also lack the cumulative-evidence advantage.

The corpus is more valuable than the moat-summary captures. **For longitudinal queries** ("how has the open-weight model landscape evolved?", "trace the progression of mechanistic interpretability work") the system has a structural advantage commercial tools cannot easily replicate.

### Finding 6.5 — Honesty contract is a documented normative discipline that commercial tools lack

No commercial deep-research tool has published an explicit normative contract binding its agents. Perplexity, OpenAI DR, Claude Research, Gemini DR all have *system prompts* (some leaked, some not) but not *contracts* with §1-§9 structure that subagents read at start-of-task.

**The honesty contract is a structural advantage in principle.** In practice, Loop 2 found it has consistency gaps and an enforcement mechanism that's narrative not automated. **Closing those gaps would make the contract advertise-able** as a competitive differentiator — "the only deep-research tool with auditable normative compliance per task."

### Finding 6.6 — STORM's multi-perspective approach is convergent with the contrarian

[STORM (Stanford)](https://medium.com/@cognidownunder/stanford-storm-revolutionizing-ai-powered-knowledge-curation-35ce51996c19) simulates a panel of expert interviewers asking questions from different perspectives, then synthesizes into a Wikipedia-style article. **This is structurally similar to the forced contrarian + multi-researcher fan-out** but:
- STORM's perspectives are **prescribed** (e.g., "domain expert", "novice", "skeptic") at simulation time
- This system's contrarian is **adversarial** ("find the answer the lead missed")
- STORM produces consensus-shaped articles; this system produces recommendation-shaped reports

**The ideas are compatible.** A future Wave-5+ improvement: instead of one contrarian subagent, dispatch *3 perspective-tagged researchers* (skeptic / open-source-maximalist / cost-pragmatist) on recommendation queries. STORM-style perspective diversity vs current single-contrarian. **Trade-off: more researchers → more wall-time / token cost**, possibly worse for §9 budget compliance.

### Finding 6.7 — Pay-as-you-go API for the user could close the speed gap

Perplexity Sonar Deep Research is available as a **pay-as-you-go API** at $2/$8 per million tokens. A single run consuming ~600K tokens costs ~$3-5. **This is substantially cheaper than the user's $200/mo Max plan amortized at 30 runs/month ($6.67/run).**

For a user willing to pay marginally per query, hitting Perplexity Sonar in <3 min is a *reasonable substitute* for ~30-50% of queries. The system's edge — corpus, authority graph, contrarian — only matters when those are decisive for the answer. For **monitoring queries** (Patch OO routing) that already skip the full loop, Perplexity API would be even faster.

**Improvement candidate:** add a "fast-path API" route for queries that don't need the full loop's structural fixes. Trades $0 → $3-5 for 87 min → 3 min. The user can opt in.

### Finding 6.8 — The system is best-positioned for *AI/ML-specific* queries; commercial tools are domain-general

OpenAI DR and Claude Research are domain-general. Their authority graphs (implicitly: Google search ranking) don't favor AI/ML niche signal. **This system's authorities.yaml advantage is purely on AI/ML topics** — for "what's the best abliterated finetune for Tier-T humor" the corpus + authority graph are decisively better than commercial tools (which would surface SEO listicles).

But this advantage **only materializes when the corpus has the relevant content**. The 2026-05-05 query's 9% corpus / 91% web ratio shows the corpus *didn't* have it. Per Loop 4 above, the HF authority-author adapter would close this. **The system's competitive advantage on AI/ML is real but currently dormant for several sub-domains.**

### Loop 6 verdict — where this system stands vs the market

| Dimension | This system | Best commercial | Gap direction |
|---|---|---|---|
| Speed | 87 min (target 25 min) | <3 min (Perplexity) | **Behind by 5-30×** |
| Citation reliability | ~84% (audit) | 78-94% (range) | **Roughly typical** |
| Reasoning depth (long-form synthesis) | Strong | OpenAI DR strongest | Comparable |
| Hand-curated authority signal | **Unique** | None have this | **Ahead** |
| Persistent local corpus | **Unique** | None have this | **Ahead** |
| Forced contrarian / red-team | Unique (in this form) | STORM has multi-perspective | **Ahead, marginally** |
| Honesty contract / normative discipline | **Unique** (documented) | None have this | **Ahead** |
| Iterative / agentic retrieval | None | Most have it | **Behind** |
| Cross-encoder reranker | None | Most have it | **Behind** |
| Eval running automatically | No (Loop 8) | Most have internal evals | **Behind** |
| Cost transparency to user | Patch N (broken — Loop 9) | Perplexity has clear pricing | **Behind** |
| Specific to AI/ML | **Yes** | All domain-general | **Ahead** when corpus is rich |

**Net competitive position:** **structural novelty on the right axes (authority + corpus + contrarian + contract), operational deficits on speed + citation reliability + automation.** The edge cases the system is built for (AI/ML, longitudinal, authority-aware) genuinely beat commercial tools when the corpus is well-stocked. The general case loses to commercial tools on speed and verification.

Sources:
- [Deep Research Tools Compared 2026 — Glasp](https://glasp.co/articles/deep-research-tools-compared)
- [Best AI Deep Research Tools 2026 — Awesome Agents](https://awesomeagents.ai/tools/best-ai-deep-research-tools-2026/)
- [Stanford STORM](https://medium.com/@cognidownunder/stanford-storm-revolutionizing-ai-powered-knowledge-curation-35ce51996c19)
- [Exa Deep](https://exa.ai/blog/exa-deep)
- [Detecting and Correcting Reference Hallucinations in Commercial LLMs and Deep Research Agents (arXiv 2604.03173)](https://arxiv.org/html/2604.03173)
- [ReportBench: Evaluating Deep Research Agents](https://arxiv.org/html/2508.15804v1)

---

## Loop 7 — Recent academic research on agentic research systems

**Method:** Web-search 2025-2026 academic literature on multi-agent reflection, process reward models, rubric-based evaluation, agent benchmarks. Map findings against this system's current architecture. Identify which patterns this system can adopt at low cost.

### Patterns in the 2025-2026 frontier

#### Multi-Agent Reflexion (MAR) — December 2025

[arXiv 2512.20845](https://arxiv.org/abs/2512.20845) — "Multi-Agent Reflexion solves the problem of single-agent degeneration by having multiple agents reflect on shared failures from different perspectives, consistently outperforming both GPT-3.5 baseline and single-agent Reflexion on HotPotQA and HumanEval-Python benchmarks."

**Mapping to this system:**
- Current: single contrarian + single critic; both run once
- MAR pattern: 2-3 agents *reflect on shared failures* iteratively, building a memory of past mistakes
- Gap: the system has the *agents* (researcher × N, contrarian, critic) but not the *iteration*. The fit-verifier and structure-verifier re-dispatch loops are 1-shot per run. **The system does not learn from prior failures within a run** beyond responding to specific verifier verdicts.
- **Low-cost adoption:** add a "lessons" file the synthesizer maintains across runs — failed-claim → root-cause mapping. Wave-5+ candidate.

#### Process Reward Models (PRMs) — accelerating in 2025-2026

PRMs score *each intermediate step* of a reasoning chain, not just the final output. **This system scores only final outputs (citation verifier, fit verifier, structure verifier all judge the draft).** No agent scores the *intermediate decisions* (which sub-questions to plan, which sources to retrieve, when to stop iterating).

**Mapping:** The retrieval log (`retrieval_log.jsonl`) records *what* each agent retrieved but not *whether each retrieval was good*. A PRM-style verifier could score each retrieval as "useful for the final claim" / "wasted call" / "should-have-reformulated". **This is what the agentic-retrieval improvement in Loop 5 (Self-RAG / CRAG) implicitly does — it's the same idea applied to retrieval rather than reasoning steps.**

#### Rubric-based evaluation with auditable evidence — 2026 standard

Per [Adnan Masood, Medium 2026](https://medium.com/@adnanmasood/rubric-based-evals-llm-as-a-judge-methodologies-and-empirical-validation-in-domain-context-71936b989e80): "Rubrics operationalize quality criteria into specific traits such as factual accuracy, completeness, safety, tone, instruction-following, citation quality, escalation correctness, or tool-use quality. The EU AI Act, NIST AI RMF, and ISO/IEC 42001 now demand 'Technical Documentation' that provides auditable evidence of accuracy and safety."

**Mapping:** the system's §1-§6 report structure is an *informal* rubric. The structure-verifier checks structural conformance. **There is no formal rubric-based eval that scores the report on dimensions like "factual accuracy", "completeness vs scope", "citation quality"**. The eval framework (`evals/`) exists but Loop 8 below will show it doesn't run automatically.

**Improvement candidate:** convert §1-§6 + Patch H (verified ≥2 sources) + Patch AA (SEO penalty) + Patch C (sourcing axis) + Patch G (matrix coverage) into a formal rubric the eval judge can score. Each report gets a numeric rubric score; trends tracked over time.

#### Recursive rubric decomposition — 2026 finding

"Recent 2026 work argues that recursive rubric decomposition materially improves both judgment quality and reward modeling for open-ended tasks."

**Mapping:** if a high-level rubric trait is "citation quality", recursive decomposition splits it into:
- Citation graph integrity (every `[srcN]` in body has matching §6 entry)
- Source-claim match (cited source contains the claim)
- Triangulation (`[verified]` requires ≥2 independent sources)
- Source quality hierarchy (paper > implementation > docs > blog > aggregator)
- Quote fidelity (verbatim quotes match source verbatim)

The structure-verifier checks (1) and parts of (2). Citation verifier checks (2). The synthesizer's Patch H prompt enforces (3). Patch AA enforces (4). **Nothing checks (5)** — and that's exactly the src22 Willison-quote fabrication failure mode in the prior review's Loop 8.

**Adoption: low-cost.** The decomposition already exists implicitly in the patches; making it explicit + scored gives observability without changing behavior.

#### Chain-of-thought in LLM-as-judge — 10-15% reliability lift

"Chain-of-thought in LLM as a judge means prompting the judge model to explain its reasoning step-by-step before giving a final score, which improves reliability by 10-15% and provides debuggable reasoning trails."

**Mapping:** the eval judge in this system is Opus 4.7. Whether it uses chain-of-thought in scoring is unclear from the eval code (Loop 8 below). **Easy fix:** instruct the eval judge to first emit "criteria assessment" (one sentence per rubric trait), then score. Free 10-15% reliability lift.

#### Evaluator-LLM blind spots — 2026 critical finding

"Evaluator LLMs often fail to detect quality drops when targeted perturbations degrade factuality, instruction following, long form coherence, or reasoning."

**Mapping:** if the system's eval judge is similarly blind, the eval signal could be misleading. Wave-5+ candidate: **adversarial eval cases** that perturb known-good reports in specific ways (swap a citation, invert a numeric claim, drop a runner-up) and check whether the eval judge detects the perturbation. If the judge passes the perturbed report, the judge is unreliable for that perturbation type.

#### Multi-Agent Evolve (MAE) — October 2025

Proposer + Solver + Judge with reinforcement learning; 4.54% average improvement across benchmarks without human curation.

**Mapping:** this is **far beyond the system's personal-use scope.** RL fine-tuning is not feasible on $200 Max plan. **Don't pursue.** Mention as "what scaled-up systems are doing" but not Wave-5 candidate.

#### LATS (Language Agent Tree Search) — 2024-2025

Monte Carlo tree search + reflection. **Overkill for personal use.** This system's per-run wall time is already too long; adding tree-search retrieval would balloon it.

### Specific patterns this system DOES have but underutilizes

**Multi-perspective dispatch:** the system has a contrarian and N researchers. Each has a distinct sub-question. **But all researchers receive the SAME `must_cover_families` constraint** — meaning their searches are still constrained to a predetermined option space. **STORM-style perspective tagging would be a free addition:** instead of "researcher-1 covers SQ1", run "skeptic-perspective researcher" + "open-source-maximalist researcher" + "cost-pragmatist researcher" with overlapping option spaces.

**Honesty-contract-driven discipline:** the contract is a *normative* rubric the agents internalize. **Most academic agent literature doesn't have an explicit normative document** — it's all in agent prompts. The contract approach is closer to ConstraintNet / rule-based agents than to free-form agentic dispatch. **Defensible novelty.**

### Patterns this system CAN'T easily adopt (compute budget)

- Process Reward Models (PRMs) at retrieval-step level: requires training or fine-tuning a step-scorer
- RL-based self-improvement (MAE-style): infeasible without API budget
- LATS tree search: would push wall-time well past §9 ceiling
- Distillation / teacher-student loops: requires custom training infra

### Patterns this system CAN adopt at low cost

| Pattern | Cost | Expected lift |
|---|---|---|
| Rubric-based eval with chain-of-thought judge | Update eval prompt | 10-15% reliability lift |
| Recursive rubric decomposition | Refactor existing patches into explicit rubric | Improves observability + judgment quality |
| Adversarial eval cases | Add 10-20 perturbed reports to eval suite | Catches blind spots in eval judge |
| Cross-run "lessons" / failed-claim memory | Append-only file the synthesizer reads | Reduces repeat failures |
| Multi-perspective researcher tagging | Adjust dispatch parameters | Better coverage breadth |

### Loop 7 verdict

The system is **conceptually adjacent to the 2025-2026 frontier** (multi-agent dispatch + reflection + verification). The structural skeleton (researcher / contrarian / critic / verifier) is *similar* to MAR, but the iteration loop (failure-reflection-retry) is missing. **The biggest gap from current academic best practice is iteration**: the system runs each agent once per stage; modern agentic systems iterate within a stage based on self-evaluation.

The eval framework (Loop 8 below) is the load-bearing piece for adopting any of these. **Without an eval that runs and scores reports against a rubric, every "improvement" is unmeasured** — and the patches accumulate without quality signal.

Sources:
- [Multi-Agent Reflexion (MAR) — arXiv 2512.20845](https://arxiv.org/abs/2512.20845)
- [Awesome Agent Papers GitHub](https://github.com/luo-junyu/Awesome-Agent-Papers)
- [Survey on Evaluation of LLM-based Agents — arXiv 2503.16416](https://arxiv.org/html/2503.16416v2)
- [Rubric-Based Evals & LLM-as-Judge 2026 — Adnan Masood, Medium](https://medium.com/@adnanmasood/rubric-based-evals-llm-as-a-judge-methodologies-and-empirical-validation-in-domain-context-71936b989e80)
- [How to Correctly Report LLM-as-a-Judge Evaluations — arXiv 2511.21140](https://arxiv.org/pdf/2511.21140)
- [Judge Reliability Harness — arXiv 2603.05399](https://arxiv.org/html/2603.05399v1)
- [AI Agent Reflection and Self-Evaluation Patterns — Zylos](https://zylos.ai/research/2026-03-06-ai-agent-reflection-self-evaluation-patterns)

---

## Loop 8 — Eval framework analysis

**Method:** Read `evals/cases.yaml` (620 lines, 30 cases), `evals/run_all.py` (359 lines, retrieval-layer harness), `evals/run_full_loop.py` (437 lines, run-trace harness), `evals/baseline_single_sonnet.py` (339 lines, gating experiment). Read `evals/runs/_history.jsonl` (28 runs of history). Determine: does the eval framework run regularly? Is it actually testing the failure modes the system exhibits? Is it scoring report quality?

### Eval framework inventory

| File | Lines | Purpose | Status |
|---|---|---|---|
| `cases.yaml` | 620 | 30 regression cases across 7 categories | Maintained, expanding |
| `run_all.py` | 359 | v1: retrieval-layer assertions via `corpus_server.search()` | **Has run 28 times** |
| `run_full_loop.py` | 437 | v2: read-only assertions over scratch-dir artifacts | Has run a few times |
| `baseline_single_sonnet.py` | 339 | Patch DD: single-Sonnet vs multi-agent gating experiment | **Unclear whether run** |
| `runs/_history.jsonl` | 28 entries | Append-only run log | Last entry: **2026-05-04** (no run since then) |

### Finding 8.1 — Eval framework EXISTS and HAS RUN; just not after 2026-05-04

The history shows 28 eval runs over 2026-05-03 → 2026-05-04. **Most recent run: 2026-05-04T211406Z, 23 pass / 0 fail / 1 blocked.** Then nothing.

The 2026-05-05 system run that produced the report under review **was not followed by an eval check**. There's no commit-triggered eval, no daily cron, no GitHub Actions — the user manually invokes `python -m evals.run_all`. **The eval framework is a manual diagnostic, not a continuous-integration safety net.** Patches NN-HHH (Waves 1-4) shipped without eval verification post-2026-05-04.

The blocker: no `.github/workflows/` directory, no CI integration, no scheduled job for the eval. The systemd-timers cover ingestion (`ingest`, `embed`, `digest`, `podcasts`, `poll-authorities`, `promote-arxiv`, `tag-engagements`) but not evals.

### Finding 8.2 — The full-loop assertions were converted to retrieval-layer proxies

Cases that originally required full-loop dispatch (clarification gate, contrarian independence, fit verifier catches mismatch, capitulation guard, mini-contrarian surfaces alternative) were `blocked_until: full_loop_eval_harness`.

The full-loop harness was built (`run_full_loop.py`, 437 lines, v2 per Patch EE). On 2026-05-04T184252Z it ran with `0 pass / 6 no_match` — the full-loop harness was **non-functional at that snapshot**.

Then Patch BBB (2026-05-05 Wave 4) **converted these full-loop cases to retrieval-layer proxies** in `cases.yaml` (e.g., `mention_detection_populates_authorities`, `mentioned_with_link_engagement_records`, `cross_run_memory_finds_personality_query`). The full-loop dispatch path was abandoned in favor of cheaper retrieval-layer signals.

**Consequence:** the eval is now testing **whether retrieval-time signals correlate with intended behaviors** rather than **whether the actual behaviors fire**. For example, `mini_contrarian_surfaces_alternative` originally checked the synthesizer's mini-contrarian (Patch Z) by reading `synthesizer-final.md` for §2 Weakest assumption with hedge-language + ≥25 words. The Patch BBB version (per cases.yaml) tests something else — likely indirect.

This is **proxy testing**, not behavioral testing. The system is asserting via correlation rather than direct observation.

### Finding 8.3 — No LLM-as-judge in any eval code

Searching all eval Python files for `Opus` / `judge` / `llm_as_judge` returns **zero matches**.

`cases.yaml` describes rubrics ("LLM-as-judge with a rubric") and references the Opus 4.7 eval judge in PLAN.md / CLAUDE.md. **But no code invokes Opus or any judge model.** The eval framework is purely behavioral assertion (substring match, regex, structural check) against retrieval results or run artifacts.

This means the eval has zero capability to:
- Detect citation fabrication that *looks plausible* (because it's not asking a judge to verify the claim is in the source)
- Score report quality dimensions like "completeness vs scope", "factual accuracy", "reasoning soundness"
- Catch the failure modes the prior review's Loop 8 found (Willison fabricated quote, abliteration.ai arithmetic error, src36 404)

**The eval framework in its current state cannot detect the high-severity failure modes in the 2026-05-05 report.** Loop 7 found that 2025-2026 academic best practice uses LLM-as-judge with chain-of-thought + recursive rubric decomposition. The system has neither.

### Finding 8.4 — `baseline_single_sonnet.py` is the load-bearing unrun experiment

Patch DD (Report 2's "load-bearing unrun experiment"): test whether a single Sonnet 4.6 call with corpus snippets + WebSearch matches multi-agent quality. Decision rule:
- ≥70% quality at ≤10% cost → multi-agent demoted to premium
- <70% quality → multi-agent default justified

**Status: the file exists; no entry for it in `_history.jsonl`. The experiment has not been run.**

This is a profound finding. **The entire multi-agent architecture (with its 87-min wall time, 33 patches, 7 specialized agents) is empirically unjustified.** Until the single-Sonnet baseline runs, the system cannot answer:
- "Are we adding value over the simpler alternative?"
- "Is the patches-on-patches investment paying off?"
- "Is the user's $200 Max plan compute actually well-spent on multi-agent?"

The Patch DD comment block honestly says "until this runs, the multi-agent /deep-ai-research default is unproven against the simplest alternative." **It hasn't run.** This is the system's largest operational risk.

### Finding 8.5 — Eval cases test for moat mechanisms but not for high-severity failure modes from the prior review

Cross-mapping the 30 eval cases against the 6 high-severity failure modes from the 2026-05-05 review:

| Failure mode | Eval case that catches it? |
|---|---|
| §1 citation misattribution (src30/src31 vs src22) | **No** — no case checks claim→citation traceability |
| `[verified]` tag on mechanism papers for behavioral implication | **No** — `report_has_conclusion_and_confidence_panel` checks structure, not tag discipline |
| PRISM scope-stretch (paper measures different thing than claim) | **No** — no source-claim measurement check |
| W_E claim contradicts cited source | **No** — same |
| abliteration.ai $5/M arithmetic error | **No** — `verification_fabricated_citation` doesn't check arithmetic |
| Willison verbatim quote not in src22 | **No** — closest is `verification_fabricated_citation` but it injects a fake URL, not a fake quote |
| Inter-run drift across 5 prior runs | **No** — `cross_run_memory_finds_personality_query` checks index lookup, not drift surfacing |

**Zero of six high-severity failure modes from the prior review have an eval case that would have caught them.** This is the pure consequence of Finding 8.3 (no LLM-as-judge): structural and behavioral signals at retrieval-time can't catch synthesis-time fabrications.

### Finding 8.6 — `authority_karpathy_llm_wiki` has been blocked since day 1

The canonical regression case for the entire system's authority-graph mechanism (the Karpathy LLM wiki failure that motivated the project) is `blocked_until: step_9_twitter_ingestion`. Twitter ingestion is "deferred indefinitely" per CLAUDE.md.

**The system's flagship motivating example has never been validated end-to-end.** Karpathy's wiki may show up via Bluesky ingestion (Patch WW) but the case still uses `blocked_until: step_9_twitter_ingestion`. **Update needed:** route the case through the Bluesky path (since Karpathy posts on both) or accept that the canonical regression is permanently un-checkable in v1.

### Finding 8.7 — The eval cadence is wrong for a fast-iterating system

Patches NN-HHH shipped over 2026-05-04 → 2026-05-05 (~33 patches in 2 days). **The eval ran 0 times during this period after 2026-05-04T211406Z.** Each patch could individually have introduced a regression, but the compound effect is invisible.

In a system iterating at this rate, the right cadence is **eval on every commit touching `.claude/`**, not "manually when remembered". A pre-commit hook or GitHub Action would catch regressions immediately.

### Loop 8 verdict — the eval is real but operationally inert

| # | Severity | Issue |
|---|---|---|
| 8.1 | **High** | No automated cadence; eval is manual; not run after 2026-05-05 patches |
| 8.2 | High | Full-loop cases converted to retrieval-layer proxies; behavioral truth not tested |
| 8.3 | **Critical** | No LLM-as-judge; cannot catch synthesis-time failure modes |
| 8.4 | **Critical** | `baseline_single_sonnet.py` unrun; multi-agent architecture empirically unjustified |
| 8.5 | High | Zero of 6 high-severity failure modes from prior review have an eval that catches them |
| 8.6 | Medium | Flagship Karpathy case permanently blocked on deferred Twitter ingestion |
| 8.7 | Medium | Eval cadence wrong for the patch-velocity of the system |

**The eval framework is the load-bearing piece for the entire patches-as-improvements approach.** Without it firing automatically, the system has been accumulating 33 patches over 3 days with no quality signal. Patches NN-HHH are unverified.

Two highest-leverage fixes:
1. **Run `baseline_single_sonnet.py`.** Get the empirical answer on whether multi-agent is justified. This is the single biggest unanswered question about the entire system.
2. **Add LLM-as-judge to the eval framework.** Use Opus 4.7 (or 4.6) with chain-of-thought + rubric to score report quality. Run on every commit to `.claude/` via GitHub Actions or pre-commit. Without this, the eval can't detect the failure modes that actually occur.

---

## Loop 9 — Cost / compute envelope reality check

**Method:** Compute actual token + wall-time + 5h-window burn for the system at stated rates. Web-research current 2026 Max-200 plan limits. Cross-check against the runs that actually happened. Identify whether the §9 budget is realistic or aspirational.

### Stated budgets (sources)

| Source | Budget claim |
|---|---|
| `PLAN.md` line 124 | **"~250K input + 50K output max" per run, enforced by token tally** |
| `SKILL.md` "Cost budget enforcement" | **"~600-800K total tokens, ~25 min wall time"** typical |
| `SKILL.md` ceiling | **"1.2M tokens"** hard ceiling (≥1.2M = §9 regression) |
| `config/plan.yaml` | **50M tokens/month** estimated for Max-200 |
| Honesty contract §9 | **30% of 5h Max window** = single-run regression threshold |
| 2026-05-04 over-rotation | 2.4M tokens / 1h 17min — explicit reference example for what NOT to do |
| 2026-05-05 reviewed run | ~600-800K tokens estimated / 87 min wall time (telemetry null) |

### Finding 9.1 — Internal budget inconsistency: PLAN.md says 250K input; SKILL.md says 600-800K total

**PLAN.md line 124:** "Cost cap is a per-run *token budget* (~250K input + 50K output max), enforced by orchestrator's running tally."

**SKILL.md:** "Typical recommendation query: ~600-800K total tokens" with hard ceiling 1.2M.

These differ by ~3-5×. PLAN.md reflects the **original** budget design (when the system was simpler). SKILL.md reflects the **post-patches** reality (after Patch Q-X bounded coverage calibration following the 2026-05-04 over-rotation).

**Net:** the actual per-run budget has expanded ~5× from the original design. The patches are not budget-neutral; they are budget-expanding.

### Finding 9.2 — The §9 "30% of 5h Max window" rule is ambiguous

Per Anthropic's 2026 Max plan documentation (per [TokenMix 2026 limits guide](https://tokenmix.ai/blog/complete-claude-limits-guide-2026-tokens-uploads-5-hour)):
- "Max 20x" ($200/mo) provides "at least 900 messages per 5 hours under short, less compute-intensive use"
- "Not a hard quota for Opus, long chats, attachments, or tool-heavy work"
- Weekly caps exist across-all-models AND specifically-for-Sonnet
- Token allocation per 5h window is **not published** in numeric form by Anthropic

The system's `plan.yaml` estimates "50M tokens/month" — divides to ~1.67M tokens/day. Across ~6 rolling 5h windows/day, that's ~280K tokens per 5h window. **30% of 280K = 84K tokens.** A single research run regularly consumes 600-800K tokens (per SKILL.md). **The system's own typical run violates the §9 30% rule by ~7-10×.**

Either:
- The §9 rule is unrealistically tight for actual usage
- The 5h window cap is much higher than the average implies
- The 30% rule references a different denominator than I'm computing

The contract phrasing "30% of the user's 5h plan window" is *implicitly* about burst-window allocation, not amortized daily share. Anthropic's actual 5h burst cap could be 2-5× the daily-amortized share. Without empirical telemetry (which Loop 9 of the prior review found is broken), the system can't compute this.

### Finding 9.3 — The 2026-05-04 over-rotation (2.4M tokens, 1h 17min) was a singular incident

NOTES.md narrates this run as the calibration target for Patches Q-X (bounded coverage). The user's verbatim feedback is in honesty contract §9: *"1h 17 minutes — like what the fuck. ~2-2.4M tokens. My entire 5h context went from 30% to 100%. That's not normal. Optimize it."*

This means a 2.4M-token run consumes **~70% of the 5h window** (going from 30% → 100% = 70% delta). Reverse-engineering: 2.4M / 0.70 = 3.43M tokens of 5h window capacity → ~3.4M tokens / 5h window for Max-200. That's substantially higher than my naive ~280K calculation.

**Recalibration:** if 5h window holds ~3.4M tokens:
- §9 30% rule = ~1M tokens per run (consistent with 1.2M hard ceiling per SKILL.md)
- Typical run (600-800K) = 18-24% of 5h window — *under* the 30% rule
- 2026-05-05 run (~600-800K) = same range — under the rule

The actual user-perceived budget per 5h window is **~3.4M tokens** (back-derived from the 2026-05-04 incident). The system's §9 rule is calibrated correctly *to that figure*. **My naive 280K-per-window estimate was wrong by 12×.**

So the system's budgets are roughly:
- 5h window: ~3.4M tokens
- Daily (6 windows): ~20M tokens (uncapped per-day, but weekly cap interferes)
- Weekly (7 days): unclear; lower than 7 × daily

### Finding 9.4 — Run cadence reality check

At 600-800K tokens per typical run + 1.2M ceiling, the 5h-window math is:
- **One typical run: ~22% of 5h window.** Sustainable; user has buffer for other Claude Code work.
- **Two typical runs back-to-back: ~44% of 5h window.** Sustainable but tightening.
- **Three typical runs in 5h: ~66% — approaching ceiling.**
- **One ceiling-run + one typical: 35%+ 22% = 57%.** Edge.
- **The 2026-05-05 87-min run that consumed ~600-800K tokens fits comfortably in the budget.**

The user's 5-prior-runs-in-24h pattern is sustainable on the budget. The 2026-05-04 2.4M-token run was the explicit over-rotation that triggered Patches Q-X.

### Finding 9.5 — Synthesizer is the disproportionate cost driver

Per the 2026-05-05 stage breakdown:
- recency_pass: 112s (2%)
- research_fanout: 1059s (20%)
- synthesizer_draft: 721s (14%)
- verifiers: 381s (7%)
- **synthesizer_final: 2814s (54%)** ← disproportionate

If wall-time correlates with token cost (rough proxy), synthesizer_final is 54% of compute. Patch HHH set synthesizer to `effort: high` (down from `max`), expected to shave 20-30%. **Even after Patch HHH, synthesizer_final dominates the budget.**

Wave-5+ candidate: **decompose synthesizer's two passes into smaller agents**. The current synthesizer does:
1. Read 4-6 researcher outputs + contrarian + recency + manifest
2. Write 6-section structured report
3. Read 3-4 verifier outputs + critic
4. Try targeted WebSearches for dropped targets
5. Mini-contrarian on recommendation
6. Repair citations + tag fixes
7. Re-write report
8. Compute corpus/web ratio + plan-usage metric

This is many tasks in two passes. Splitting into:
- `synthesizer-draft` (steps 1-2)
- `synthesizer-repair` (steps 3, 6)
- `synthesizer-finalize` (steps 4, 5, 7, 8)

…would let each agent run with smaller context. Trade: 3 agents × overhead vs current 2 with disproportionate work.

### Finding 9.6 — Telemetry is broken; the system can't measure its own budget

Per 2026-05-05 review Loop 9:
- `usage_snapshot_start` / `usage_snapshot_end` were null
- Token tally not in manifest
- "Rough estimate from researcher file sizes (~100KB combined): ~600-800K tokens input"
- "Token regression (≥1.2M honesty contract §9 ceiling) cannot be ruled out"

Patches CC + JJ + UU were supposed to fix telemetry. They didn't fire on the 2026-05-05 run. **The system's compute envelope is currently uncomputable for the runs that matter.** Every "we're within budget" claim in §2 is approximate.

### Finding 9.7 — $200/mo plan vs actual usage value

Naive cost analysis:
- $200/mo / 30 days = ~$6.67/day
- One run/day at ~700K tokens (Sonnet 4.6 blended ~$5-8/M) = ~$4-6 per run
- Plan is ~$2-3 surplus per day = barely covers system overhead

Comparison to commercial alternatives at API rates (Loop 6):
- Perplexity Sonar Deep Research: $2/$8 per M = ~$5 per 700K-token run
- OpenAI Deep Research: subscription-only, no per-run pricing exposed
- Claude API direct (Sonnet 4.6): ~$5 per 700K-token run

**At per-run cost equivalence, the system competes well — $5/run for personal-use deep research is cheap.** The $200 Max subscription buys ~30-40 runs/month at typical complexity. **At the user's stated 5-runs-of-same-query-in-24h pattern, that's 1/6 of the monthly capacity in one day.**

### Finding 9.8 — The system has no soft-fail mode

Per `evals/run_full_loop.py` and the orchestrator: when the system hits a hard error (telemetry null, dispatch failure, citation verifier finding fabrications), it doesn't gracefully degrade — it either:
- Continues with degraded telemetry (the 2026-05-05 case)
- Hits `finish_reason: "fit_failure_after_redispatch"` and emits a final report explaining failure (the §6 case)
- Fails silently (the §3.7 contract-path-stale case)

What's missing: **a "best effort with confidence discount" mode.** When the system detects it's running over budget or with broken telemetry, it should produce a shorter report flagged as "fast-path: lower confidence" rather than continue grinding. The §9 cost-cap text mentions this:

> "If 80% spent and you haven't reached Stage 8, finalize with what's gathered and mark `finish_reason: 'cost_cap'` honestly."

But this rule depends on the orchestrator knowing it's at 80% — which requires telemetry — which is broken. **Circular dependency.**

### Loop 9 verdict

| # | Severity | Issue |
|---|---|---|
| 9.1 | Medium | PLAN.md and SKILL.md disagree on budget by 5×; PLAN.md is stale |
| 9.2 | Medium | §9 30% rule has ambiguous denominator; back-derives to ~3.4M token 5h window |
| 9.3 | n/a | 2026-05-04 over-rotation calibrates the actual 5h window capacity |
| 9.4 | n/a | Typical runs (600-800K) are sustainable at ~1 run/day on $200 Max |
| 9.5 | High | Synthesizer_final is 54% of wall time; Patch HHH partial fix; deeper decomposition needed |
| 9.6 | **High** | Telemetry broken — system can't measure own budget; circular dependency on cost-cap |
| 9.7 | Low | Per-run cost ($5) is competitive with API alternatives; $200/mo is appropriate scale |
| 9.8 | Medium | No soft-fail mode; system either succeeds or hard-fails |

**The compute envelope is functional but opaque.** The system regularly approaches its own ceilings without knowing whether it has crossed them, because telemetry is broken. Patches CC+JJ+UU were the fix; they didn't operate on 2026-05-05. **Without working telemetry, the §9 budget is normative-only, not enforced.**

The single-Sonnet baseline (Loop 8 Finding 8.4) gating experiment is the cost-side complement: if single-Sonnet hits 70% quality at 10% cost, the multi-agent system's $5/run is **5× the necessary cost** for 30% extra quality. **Until that experiment runs, the multi-agent's cost premium over single-Sonnet is unjustified.**

Sources:
- [Claude Limits 2026 — TokenMix](https://tokenmix.ai/blog/complete-claude-limits-guide-2026-tokens-uploads-5-hour)
- [Claude Code Pricing 2026 — NxCode](https://www.nxcode.io/resources/news/claude-code-pricing-2026-free-api-costs-max-plan)
- [Claude Code Rate Limits — Sitepoint](https://www.sitepoint.com/claude-code-rate-limits-explained/)

---

## Loop 10 — v2 architectural rebuild proposal

**Method:** Synthesize all findings from L2-1 through L2-9 plus the prior 10-loop quality review into a coherent "what would v2 look like if I started today" proposal. Specific structural changes tied to specific failures observed. This is the longest loop — synthesis of all 19 prior loops across both review files.

### v2 vision in three sentences

**v1 was right about the moat (authority graph + corpus + contrarian + recency) and wrong about the orchestration (patches accumulating without consolidation).** v2 keeps the moat untouched and rebuilds the orchestration around three principles: **consolidation** (patches → named subsystems), **iteration** (single-shot retrieval → agentic Self-RAG), and **enforcement** (narrative contract → automated checks). The eval framework moves from manual diagnostic to load-bearing CI gate, gating any change to `.claude/`.

### What stays the same (the moat is correct)

| Component | Status | Why preserve |
|---|---|---|
| Markdown-first corpus | Keep | Right choice over Postgres; sqlite-vec performs well at 25-50K docs |
| Authority graph (`authorities.yaml`) | **Expand by 10-15 entries** | Genuinely unique competitive advantage |
| Per-content-type time decay | Keep | Right approach; needs `tag: evergreen` override (Loop 4) |
| Forced contrarian subagent | Keep | Structurally novel vs commercial tools |
| Forced recency pass | Keep | Explicit-stage approach beats implicit search-first |
| systemd-timer ingestion | Keep | Operational, survives reboots |
| Native Claude Code primitives (no LangChain/Postgres/Brave) | Keep | Removes dependency surface |
| Honesty contract as normative document | **Keep but enforce** | Conceptually right; needs automated checking |
| Embedding model (snowflake-arctic-embed-s) | Keep | Marginally best in class for size |

### v2 changes — top 8 with rationale

#### Change 1: Patch consolidation refactor — eliminate the alphabet

**Problem:** 33+ named patches (A-Z, AA-ZZ, BBB-HHH, plus deferred AAA/TT) over 3 days. PLAN.md is stale at ~Patch P. SKILL.md at 330 lines is the de-facto source of truth. **Patch IDs leak into every config, prompt, and code comment** — a future maintainer cannot reconstruct system behavior without reading NOTES.md cover-to-cover.

**v2 fix:** consolidate patches into 7-10 named subsystems. Each subsystem owns a contiguous responsibility:

```
subsystems/
├── recency/       (recency pass, daily digest, monitoring routing)
├── coverage/      (must_cover_families, comparison matrix, sub-question budget)
├── verification/  (citation, fit, structure verifiers, claim-traceback)
├── traceability/  (manifest, retrieval log, stage log, telemetry)
├── synthesis/     (draft/repair/finalize agents, mini-contrarian)
├── retrieval/     (RRF + reranker + HyDE + iterative agentic)
├── authority/     (authority graph, mention detection, engagement scoring)
└── contract/      (honesty contract + automated enforcement)
```

Each subsystem has a single doc (`subsystems/<name>.md`) replacing the equivalent NOTES.md sections. Patches IDs deprecated; subsystem-level changes go in subsystem doc.

**Migration cost:** medium. ~2 days work. Most patch behaviors map 1:1 to subsystems.

**Validation:** PLAN.md becomes a 200-line index pointing at subsystems. NOTES.md becomes a generic build log. CLAUDE.md is updated to current state.

#### Change 2: Iterative agentic retrieval (Self-RAG / CRAG pattern)

**Problem:** Researchers do 8 retrieval calls per pass. If first 3 calls return junk, calls 4-8 don't recover by changing strategy. Per Loop 5, this is the biggest single leverage point.

**v2 fix:** within the existing 8-call cap, the researcher iterates:
1. Retrieval call N
2. Self-eval: "Is this evidence relevant? Sufficient? Should I reformulate?"
3. If irrelevant → reformulate query (HyDE-style: write a hypothetical doc, embed, retrieve nearest)
4. If sufficient → stop early, save remaining budget
5. Cap: 8 calls total (unchanged)

Implementation: extend researcher prompt with self-eval template after each retrieval. Add `corpus_search_hyde(query, hypothetical_doc)` MCP tool.

**Why now:** the 2026 frontier (per Loop 5) has moved here; this system is on the wrong side of that transition. **For 9%/91% corpus/web problem specifically, iteration lets the researcher recognize corpus-thinness on call 1 and pivot to web on call 2** — instead of burning 4 corpus calls discovering thinness.

**Migration cost:** medium. Researcher prompt grows ~50 lines. New MCP tool ~80 lines.

#### Change 3: Cross-encoder reranker (already specified in PLAN.md, never built)

**Problem:** Loop 5 found "RRF + cross-encoder" is the consensus 2026 production pattern. The system has RRF, no reranker. Deferred-pending-eval, but eval doesn't run.

**v2 fix:** ship `bge-reranker-v2-m3` on top-20 candidates. Per PLAN.md: ~350ms/pair on CPU, ~7s for top-20 — acceptable on background dispatch.

**Migration cost:** low. ~150 lines of code in `corpus_server/reranker.py` (already exists per Loop 1 inventory; unclear if active).

**Validation:** add eval case `reranker_promotes_high_relevance_over_high_keyword_match` — inject a SEO listicle that BM25-matches well but is low-relevance; verify reranker drops it.

#### Change 4: Claim-traceback annotations + automated enforcement

**Problem:** Prior review's Loop 8 found 3 of 7 sampled citations had issues including a fabricated quoted passage. Loop 3 of this audit found `[verified]` tags violate Patch H 5-of-6 times because the contract definition is mechanical, not substantive.

**v2 fix:** synthesizer emits machine-readable `<!-- claim-trace src22: "exact quoted passage from source" -->` annotations after each `[verified]` / `[inferred — srcN]` tag. Verifier consumes annotations:
- Re-fetches each cited URL (HEAD check + body fetch)
- Whitespace-normalizes both texts
- Performs exact-substring match against fetched body
- PASS on match; FAIL with diff on miss

Structure-verifier lints: any `[verified]` tag without `claim-trace` annotation = STRUCTURE FAIL.

This is **Patch III** from the prior review, made structural.

**Migration cost:** medium. Synthesizer prompt update; verifier loop update; structure-verifier lint addition. ~200 lines total.

**Validation:** the 2026-05-05 report's three citation issues (Willison fabricated quote, abliteration.ai $5/M arithmetic, src36 404) all become detectable. Re-run with v2 changes; all three caught.

#### Change 5: LLM-as-judge eval framework with rubric + GitHub Actions

**Problem:** Loop 8 found the eval framework has no judge model. The flagship `baseline_single_sonnet.py` gating experiment has never run. No CI; eval is manual.

**v2 fix:**
1. Add `evals/judge.py` — invokes Opus 4.6 (Patch V — not 4.7 due to MRCR regression) with chain-of-thought prompting + recursive rubric decomposition over §1-§6 + Patch H/AA/C/G specifications. Returns numeric scores per rubric trait.
2. Add `.github/workflows/eval.yml` — runs `python -m evals.run_all` and `python -m evals.judge` on every PR touching `.claude/`. Posts rubric scores as PR comment.
3. **Run `baseline_single_sonnet.py` once now** — get the empirical answer on whether multi-agent is justified.
4. Add adversarial cases that perturb known-good reports in specific ways (swap citation, invert numeric claim, drop runner-up). Verify judge catches each perturbation.

**Migration cost:** medium-high. ~400 lines (judge + adversarial cases + CI). Plus Anthropic API key for the judge ($0.01-0.05 per eval run).

**Validation:** adversarial cases catch synthetic perturbations. Real reports get rubric scores tracked over time. Patches that regress quality fail CI.

#### Change 6: HF authority-author adapter + 10 community authorities

**Problem:** Loop 4 found the 9% corpus / 91% web ratio for Tier-T queries is explained by the HF model-card / author-page gap. The community open-weight authors who matter (mlabonne, huihui-ai, EVA-UNIT-01, anthracite-org, BeaverAI, DavidAU, Sao10K, TheDrummer, bartowski) are missing from authorities.yaml AND no adapter ingests their HF pages.

**v2 fix:**
1. Add `ingest/adapters/hf_authority_authors.py` — for each author tagged `hf_authority: yes` in authorities.yaml, fetch their HF profile + recent model uploads + model card text. Daily polling.
2. Add 10-15 entries to authorities.yaml (canonical: mlabonne, huihui-ai, EVA-UNIT-01, anthracite-org, BeaverAI, DavidAU, Sao10K, TheDrummer; trusted: Eric Hartford, bartowski, Sebastian Raschka; signal: grimjim, 5-10 more).
3. Add 5 high-signal feeds from the deferred TBD list: Simon Willison, Sebastian Raschka, Eugene Yan, Interconnects, The Gradient.

**Migration cost:** medium. ~250 lines for the HF adapter. Authorities edits are config-only.

**Validation:** rerun the 2026-05-05 query. Corpus/web ratio shifts from 9%/91% toward 30%/70% as model-card data starts coming from corpus.

#### Change 7: Synthesizer decomposition (3 smaller agents replace 1 large)

**Problem:** Loop 9 found synthesizer_final is 54% of wall time. Loop 3 found synthesizer prompt is 627 lines (4× next-largest). Patch HHH (effort: high) shaves 20-30% but dominance persists.

**v2 fix:** split into:
- `synthesizer-draft` (current first pass) — reads researcher + contrarian + recency + manifest, writes draft. ~150-line prompt.
- `synthesizer-repair` (new) — reads draft + verifier outputs + critic, repairs citations + addresses issues. ~120-line prompt.
- `synthesizer-finalize` (current second-pass tail) — runs mini-contrarian, computes metrics, writes final. ~100-line prompt.

Three agents, each smaller context, each with one job. Total prompt budget: ~370 lines (down from 627). Plus, draft → repair → finalize can pipeline differently (repair doesn't need to wait for synthesizer to re-read everything).

**Migration cost:** high. ~3 days work. Risk of regressions during refactor; need eval coverage to catch them — which is Change 5's prerequisite.

#### Change 8: Operational fixes (one-line each, fix immediately)

These are bugs found in this audit; ship before v2:

| Fix | File | Severity | One-line description |
|---|---|---|---|
| Add `Write` tool to citation verifier | `.claude/agents/deep-ai-research-verifier.md` | High | Currently can't write `verifier.json` (Loop 3.1) |
| Add `Write` tool to critic | `.claude/agents/deep-ai-research-critic.md` | High | Currently can't write `critic.md` (Loop 3.1) |
| Fix honesty-contract path in all agents + SKILL.md | 8 files | **High (silent)** | All references to `/code/projects/` are wrong; correct path is `/projects/` (Loop 3.7) |
| Update critic prompt to not expect verifier outputs | `.claude/agents/deep-ai-research-critic.md` | High | Patch PP moved critic to parallel-with-verifiers; prompt still expects sequential inputs (Loop 3.2) |
| Update CLAUDE.md synthesizer Opus version | `CLAUDE.md` | Medium | Says Opus 4.7; PLAN.md and SKILL.md say 4.6 (Patch V) (Loop 1) |
| Add `Cross-run continuity` sub-bullet spec to synthesizer + structure-verifier | `synthesizer.md`, `structure-verifier.md` | Medium | Patch ZZ half-implemented (Loop 3.8) |

### Non-changes (proposed but rejected)

- **Multi-Agent Evolve (RL)**: too complex for personal-use scope (Loop 7).
- **LATS tree search**: would push wall-time past §9 ceiling (Loop 7).
- **ColBERT v2**: defer until corpus exceeds 25K docs (Loop 5.6).
- **Replacement of researcher + contrarian with single mode-parameterized agent**: cost > benefit (Loop 3.9).
- **Replace honesty contract with code**: contract is human-readable normative document; programmatic equivalent loses the readability (Loop 2). Keep contract; add automated enforcement layer.

### Migration path

| Phase | Duration | Changes | Risk |
|---|---|---|---|
| 0 (immediate) | <1 day | All Change 8 ops fixes | Low; single-line edits |
| 1 | ~3 days | Change 5 (eval framework + CI) — load-bearing for everything else | Medium; needs API key + judge prompt iteration |
| 2 | ~2 days | Change 6 (HF authority adapter + authorities additions) | Low; additive |
| 3 | ~2 days | Change 1 (patch consolidation refactor) | Medium; documentation work |
| 4 | ~3 days | Change 4 (claim-traceback annotations) | Medium; needs eval coverage from Phase 1 |
| 5 | ~3 days | Change 7 (synthesizer decomposition) | High; biggest behavior change |
| 6 | ~2 days | Change 2 (iterative retrieval) + Change 3 (reranker) | Medium; well-specified |

Total: ~16 days work in stages. Gate Phase N+1 on Phase N's eval scores not regressing.

### Cost estimate of v2 vs v1

| Dimension | v1 | v2 | Delta |
|---|---|---|---|
| Wall time per typical run | 87 min (last run) | ~30-40 min (synthesizer decomp + iteration savings) | **-50%** |
| Tokens per run | 600-800K | 700-900K (slightly higher; reranker + iteration adds calls) | +10-15% |
| Citation issue rate | ~16% | ~5-8% (claim-traceback + reranker) | **-50%** |
| Corpus/web ratio for Tier-T | 9%/91% | ~30%/70% (HF adapter) | Better balance |
| Eval automation | Manual | CI on every PR | **Categorical change** |
| Maintainability | 33 patches stacked | 8 named subsystems | **Categorical change** |
| Empirical justification | Single-Sonnet baseline never run | Run as Phase 1 gate | **Categorical change** |

### Final meta-conclusion across all 20 loops (10 prior review + 10 system audit)

**The system is conceptually right and operationally accreted.** v1 nailed the four moat mechanisms (authority graph, time decay, contrarian, recency pass) — that's genuinely novel and structurally distinct from commercial deep-research tools. v1 also accumulated 33 patches in 3 days because every observation became a new patch rather than feeding into a refactor.

The 2026-05-05 report under review is **outcome-correct** (huihui-ai/Qwen3-14B-abliterated is the right answer) but justified through a chain that contains:
- 2 citation misattributions in §1 (Loop 2 prior review)
- 5/6 `[verified]` tags failing Patch H (Loop 3)
- A direct contradiction with a cited source on W_E modification (Loop 4)
- A scope-stretched interpretation of PRISM (Loop 5)
- A 40% arithmetic error on abliteration.ai pricing that flips a recommendation (Loop 8)
- A Willison verbatim quote that doesn't exist in the cited source (Loop 8)

**Each of these is detectable by a verifier with teeth (Patch III + MMM from prior review).** The current verifier doesn't have those teeth because the contract definition of `[verified]` is mechanical, not substantive (Loop 2 of this audit).

**Each of these would be caught by an eval framework that runs.** The eval framework exists, has 30 cases, has run 28 times — but stopped after 2026-05-04, has no LLM-as-judge, and the gating experiment (`baseline_single_sonnet.py`) has never run (Loop 8).

**The single highest-leverage v2 change is Phase 1 of the migration: ship the eval framework with judge + CI.** Everything else is gated on having a feedback signal. Without it, the system has been adding 33 patches over 3 days with no quality regression detection. Some of those patches probably *added* failure modes — but the system can't tell.

**The next single highest-leverage change is iterative retrieval** (Change 2). The 9%/91% corpus/web ratio + the cost-of-burning-budget-on-thin-corpus problem both resolve when the researcher can recognize thinness on call 1 instead of call 4.

**The system is genuinely competitive on its target axis** (AI/ML longitudinal authority-aware research) — but only when the corpus is well-stocked AND the synthesizer doesn't fabricate. Both conditions hold occasionally. v2 makes both conditions hold reliably.

**The `baseline_single_sonnet.py` experiment is the existential question** for the multi-agent architecture. If single-Sonnet matches at 10% cost, the system's $5/run premium is unjustified. The patches-on-patches investment is unjustified. **Run that experiment.**

Sources for this v2 proposal draw on Loops 1-9 of this audit + Loops 1-10 of the prior 2026-05-05 quality review. Combined evidence base: ~50 web fetches/searches across both files, 7 agents read, all 8 configs read, eval history examined, ingestion pipeline surveyed, NOTES.md / PLAN.md / CLAUDE.md / SKILL.md / honesty contract read in full.
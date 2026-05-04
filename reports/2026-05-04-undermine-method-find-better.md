# Is the deep-ai-research methodology defensible, or is there a provably better approach?

> Generated 2026-05-04. Run id: 2026-05-04-165705-undermine-method-find-better.

---

## 1. Conclusion

**The most important finding is a category error: the two original failure modes that motivated building this system (missed DeepSeek v4, missed Karpathy LLM wiki) are discovery failures, not synthesis failures — and the current architecture cannot fix them.** This system is query-driven: it only fires when you ask the right question. A user who doesn't know DeepSeek v4 dropped won't ask about it; they'll ask "should I use DeepSeek?" and get a confident answer citing v3.2. A daily authority-feed digest — a single Sonnet call over the `authorities.yaml` RSS feeds, ~50K tokens, ~$0 — would have caught both failure modes. It addresses the original motivation more directly than the current architecture at 0.1% of the token cost. Build the digest first.

**Short why.** For on-demand synthesis queries ("what memory system should I use for an LLM agent?" — the system's actual operating mode), the current multi-agent architecture is defensible. The honest framing is: no tested alternative is *provably* better under the binding constraints, not that it is *confirmed optimal* — that Pareto claim has never been tested against the simplest baseline. The multi-agent default is provisional pending one unrun experiment: a single-Sonnet-call baseline on evals/cases.yaml. If it achieves ≥70% quality at ≤10% token cost, the multi-agent path should become a premium tier for hard queries, not the default. That conditional is real, not a hedge. **Self-flag: this run is estimated at ~1.1-1.5M tokens (~2-3% of $200/mo monthly budget, but likely 50%+ of the 5h Max window given the user-reported 2.4M token / 100% window use observed on the prior 5-researcher run at similar complexity). That is above the ≤30% target in honesty contract §9 and must be noted here, not buried.**

The mini-contrarian check found one place the discovery-reframe could be overstated: pure synthesis queries are unaffected by the discovery problem. The reframe applies to the two specific motivating cases, not to all uses of the system. For those uses, the current architecture is correctly designed.

**Runner-ups:**
- **DSPy/GEPA offline prompt optimization** — the most promising *synthesis* upgrade, but not proven on this system's failure modes; requires expanding evals/cases.yaml to ≥20 labeled cases before GEPA optimization is safe (overfitting risk with small eval set). [inferred — ECIR 2026 workshop result not directly retrieved; web-search-snippet only; arXiv 2507.19457 post-dates knowledge cutoff]
- **Single-Sonnet-call baseline** — unbeaten only because it has never been run against this system; if it achieves ≥70% quality at ≤10% token cost on evals/cases.yaml, multi-agent should become a premium tier rather than the default for all queries.
- **HippoRAG entity-KG retrieval layer** — NeurIPS 2024 peer-reviewed, up to 20% multi-hop recall gain on 2WikiMultiHopQA; constraint-incompatible unless a fully local entity extraction pipeline (small local model) is used to avoid $0 marginal cost violation.
- **Daily authority-feed digest** — not an alternative to synthesis but the correct tool for the two original failure modes; structurally better for proactive discovery than any query-driven system.

---

## 2. Confidence panel

- **Strongest evidence:** AutoResearchBench (arXiv 2604.25256, April 2026) — the best multi-agent systems including those that "largely conquered" BrowseComp achieve only 9.39% on domain-specific scientific literature discovery tasks. This is the clearest benchmark data supporting the reframe: BrowseComp scores measure a different task class than what this system needs to be good at. All architectures fail on the actual target task class. [src: src7, confirmed by corpus id bd21baf38f5a25cb and the AutoResearchBench abstract directly stating 9.39%]

- **Weakest assumption:** The claim that the current architecture is "at the Pareto frontier" under the binding constraints rests on never having run a single-Sonnet-call baseline on evals/cases.yaml. "Defensible" currently means "no published alternative proves it's better" rather than "confirmed optimal." These are not the same claim, and the distinction matters.

- **What would change my mind:** Either of two things: (a) running the single-Sonnet-call baseline on the existing evals/cases.yaml and finding it achieves ≥70% of multi-agent quality at ≤10% of token cost — this would flip multi-agent from default to premium tier; or (b) a published head-to-head ablation showing DSPy/GEPA applied to this system's researcher+synthesizer prompts achieves >10% quality gain on the recency+niche eval cases — this would upgrade GEPA from "recommended experiment" to "proven upgrade."

- **Sources:** 23% corpus / 77% web by citation (8 corpus / 27 web, 35 total citations). 41% corpus / 59% web by retrieval call (22 corpus / 32 web, 54 total calls including 1 synthesizer follow-up). Corpus coverage on benchmark leaderboards and recent lab blog posts is thin; treat web-derived numbers as more time-sensitive.

- **Plan usage:** ~900K-1.1M input + ~100K output tokens this run (estimated — no `token_tally` field in manifest.json). ~2-2.4% of $200/mo Max plan monthly budget (50M tokens). However the user-reported prior run data (~2.4M tokens consuming 30% to 100% of the 5h window) suggests this run class substantially exceeds the ≤30% 5h window target. Token tally monitoring gap: manifest.json has no `token_tally` field; budget enforcement currently relies on synthesizer self-estimation. This is a system architecture gap that should be patched with a real tally hook.

---

## 3. Findings

### Comparison matrix

All evaluated architecture families across sub-questions 1 and 5 (orchestration patterns and end-to-end alternatives). Retrieval families appear in the subordinate matrix at §3.3.

| Option | What it is | Evidence quality | Token cost vs chat | Constraint fit | Decision | Why |
|---|---|---|---|---|---|---|
| Supervisor-worker fan-out (current) | Parallel subagent dispatch from skill-as-orchestrator | Weak-self-reported (Anthropic internal eval, single source, breadth task designed for fan-out) | ~15x | Yes | recommended (synthesis) | Best available evidence for breadth-first queries; correct architecture for on-demand synthesis; pending single-Sonnet baseline |
| Daily authority-feed digest | Daily Sonnet call over RSS from authorities.yaml | N/A — structural argument, not a benchmark | ~0.1% of current | Yes | recommended (discovery) | Addresses both original failure modes at near-zero cost; query-driven synthesis cannot fix discovery failures |
| Single-Sonnet-call + tools | One model with tool access, no subagents | Weak (never benchmarked on this system) | ~1x | Yes | considered — baseline experiment needed | Never measured against this system; could achieve 70%+ quality at <5% token cost; experiment is gating |
| DSPy/GEPA offline optimization | Auto-optimizes existing prompts vs eval set | Medium (ICLR 2026 Oral; ECIR workshop not verified) | ~0 marginal (offline) | Yes — offline | considered — upgrade, not replacement | Constraint-compatible; closest to provable synthesis upgrade; requires ≥20 labeled eval cases first |
| ReAct-loop monolithic | Single loop, reasoning trace in context | Medium (BrowseComp baselines) | ~1x | Yes | rejected | 1.9% GPT-4o BrowseComp baseline vs 51.5% Deep Research; historically weaker than iterative-tool systems |
| Planner-executor | Separate planner + executor agent | Weak (no research-task benchmark) | ~2-3x | Yes | rejected | No isolated research-task benchmark; empirically thin |
| Hierarchical orchestrator-of-orchestrators | Multi-level orchestration | Weak | ~10x+ | No — token budget | rejected | Coordination error compounds; no research-task evidence; budget-incompatible |
| Multi-agent debate (MAD) | Multiple agents debating answer | Strong-negative (arXiv 2502.08788) | ~3-5x | No — token budget | rejected | 5 implementations, 9 benchmarks: fails to beat CoT or Self-Consistency at matched compute |
| Sakana Conductor | RL-trained 7B orchestrator | Medium (coding + science benchmarks) | Requires RL training | No — training infeasible | rejected | Needs RL training data; 83.9% LiveCodeBench, 87.5% GPQA but demonstrated on coding not research synthesis |
| AI21 Maestro | Offline Action Model + Pareto config search | Weak-self-reported (internal BrowseComp-Plus claim) | Requires offline training | No — proprietary AI21 infra | rejected | Constraint-incompatible; no Claude Code path; 95.18% BrowseComp-Plus is unverified self-report |
| hyperresearch (jordan-gibbs) | Claude Code deep research + persistent wiki vault | Weak (no methodology published) | ~1-2x | Yes — Claude Code | considered — coverage gap | Claude Code-native with persistent vault for cross-session compounding; no published eval; architecture surface not fully retrieved |
| LangGraph Deep Agents | Graph substrate with replay/checkpoint | Weak (operational, not quality gains) | ~1x | Partial | rejected | Operational advantages only; no research quality improvement evidence |
| OpenAI Deep Research | Iterative single-agent web research loop | Medium (BrowseComp 51.5% at launch) | ~10x | No — closed system | rejected | Architecture undisclosed; no Claude Code path; no authority/niche signal |
| Gemini Deep Research | Long-context + Google Search | Medium (BrowseComp 85.9% Gemini 3.1 Pro) | ~10x | No — closed system | rejected | Long-context competitive at 85.9% but same issue: no niche authority signal, no local corpus |
| Perplexity Deep Research | Fast citation-UI web research | Weak-marketing | Not in top BrowseComp | No | rejected | Speed-over-quality; no authority/curation; no architecture transparency |
| LATS tree search | MCTS over agent reasoning steps | Medium (92.7% HumanEval) | D×B LLM calls | No — wall-time | rejected | Wall-time arithmetic: depth × branching factor exceeds 25-min budget; no deep-research evidence |
| Reflexion (N>2 iterations) | Additional self-correction passes | Medium (already have single iteration) | ~2-3x per iteration | No — token budget | rejected | Current system already implements single-iteration Reflexion; additional iterations risk degeneration-of-thought |
| Test-time scaling / best-of-N | Run N completions, pick best | Medium (ICLR 2025 TTS paper) | ~N×base | No — N≥2 doubles cost | rejected | Saturation and inverse scaling at large N; constraint-incompatible at any N≥2 |

---

### §3.1 Orchestration patterns

**The Anthropic vs. Cognition "debate" is not a controlled experiment.** Anthropic's engineering blog (June 2025) reports 90.2% improvement over single-agent Claude Opus 4 on an internal research eval measuring parallelizable information gathering (finding board members across S&P 500 IT companies) [inferred — single self-reported source; internal eval not reproduced externally; task class designed to showcase fan-out]. Cognition's "Don't Build Multi-Agents" post (June 12 2025) argues from Devin product experience that context isolation causes conflicting decisions [inferred — engineering-experience-based, no published controlled eval numbers]. Neither provides a controlled head-to-head on the same benchmark with the same model. Both companies have structural incentives to frame their positions favorably [judgment: Anthropic sells multi-agent token usage; Cognition positions single-agent as more reliable for their coding product].

Token usage explains ~80% of BrowseComp performance variance per Anthropic's own analysis — meaning multi-agent wins primarily by spending more tokens, not by qualitatively better reasoning [inferred — second-order inference from single-source 80%-variance stat; the derived conclusion that "multi-agent wins by spending tokens, not better reasoning" follows structurally but is not directly stated in the source].

**Multi-agent debate (MAD) is empirically weak.** arXiv 2502.08788 tested 5 MAD implementations across 9 benchmarks and 4 foundation models. MAD reliably fails to outperform Chain-of-Thought or Self-Consistency at matched compute [inferred — single arXiv source; no independent replication in this retrieval pass]. The current system's "forced contrarian" pattern is structurally different from MAD: it is a single adversarial subagent run once, not debate rounds, which avoids the convergence-on-shared-error failure mode.

**Sakana Conductor** (7B RL-trained orchestrator) achieved 83.9% LiveCodeBench and 87.5% GPQA-Diamond, beating all workers in its pool [inferred — AINews 2026-04-27, corpus id: 64115e8c43fd6637]. Architecturally the most interesting alternative: RL-trained orchestration vs. prompt-based. Constraint-incompatible for this system.

**The "Last Harness You'll Ever Build"** (arXiv 2604.21003, April 2026) proposes a two-level meta-learning framework automating harness engineering. If this generalizes, it threatens the hand-tuned orchestration logic in the current system [inferred — corpus id: f048ff68a8ec5f98; not independently reproduced; the paper is very new].

**Token overhead is a real operational risk.** Agentic systems consume ~1000x more tokens than chat and have ~30x variance across runs on identical tasks; more spending does NOT monotonically improve accuracy [inferred — AINews 2026-04-27 citing SWE-bench study; measured on coding agents; the user-reported 1h17m / 2.4M token run in honesty contract §9 is direct evidence of this pattern in this specific system].

---

### §3.2 Verification and citation faithfulness

**Production fabrication rates are severe.** Tow Center (Columbia, March 2025, 200 queries across 8 AI search engines): >60% of all citations were inaccurate [inferred — NiemanLab report confirming ≥60% overall finding; the specific per-product subcategory breakdown was not confirmed in the verifier's source re-fetch and is dropped per the citation verifier's fail verdict]. Perplexity answered 37% of queries incorrectly. Gemini and Grok 3 produced more fabricated links than correct links [inferred — multiple sources confirm the overall ≥60% finding; per-product subcategory numbers are from the CJR primary source, partially confirmed].

**Post-rationalization is the deep problem.** arXiv 2412.18004 found up to 57% of citations lack faithfulness — models cite documents aligned with their prior parametric beliefs rather than documents they actually used to derive the claim [inferred — single arXiv source; the 57% finding is directly stated in the abstract]. Post-hoc verification can catch broken pointers and semantic mismatches but cannot detect post-rationalization because the cited document superficially supports the claim.

**FAMA (arXiv 2604.25135, April 2026) — coverage gap.** The recency pass flagged FAMA (Failure-Aware Meta-Agentic Framework, corpus id: d3cdbd6d80d8a825) as the highest-signal corpus item for verifier-loop alternatives. FAMA directly addresses the same problem this system's verifier/critic loop handles: structured failure detection within agentic pipelines. No researcher in this run fetched it. This is a concrete coverage gap: a directly relevant alternative to the current verification architecture was present in the corpus and not retrieved. Would resolve via one targeted WebFetch of corpus id d3cdbd6d80d8a825.

**Inline citation-grounded decoding does not provably dominate post-hoc verification.** Anthropic's Citations API (January 2025) guarantees valid document pointers but does not prevent post-rationalization [inferred — Anthropic Citations API docs + arXiv 2412.18004; no published head-to-head comparing inline vs. post-hoc on fabrication rates for long-form multi-source synthesis exists as of this writing].

**The detection difficulty problem.** FaithBench (arXiv 2505.04847) shows existing hallucination detectors achieve near-50% balanced accuracy on summarization — essentially coin-flip. The best detector (FaithJudge with o3-mini-high, few-shot) reaches 84% [inferred — arXiv 2505.04847]. This means the verifier subagent itself may fail to detect unfaithfulness in ~16-33% of checked citations, regardless of inline vs. post-hoc architecture.

**The current 12-sample design is defensible but arbitrary.** No published study evaluates optimal citation sample size for post-hoc verification. For a report with 20-40 citations, sampling 12 most-load-bearing achieves ~30-60% coverage [judgment: the criterion is right; the number 12 is a heuristic with no empirical validation].

**Verification families evaluated:**

| Family | What it does | Fabrication-rate evidence | Cost | Gap vs current | Decision |
|---|---|---|---|---|---|
| Post-hoc citation re-fetch (current, 12-sample) | Re-fetches + LLM-judges sampled citations after generation | Catches pointer errors + semantic mismatches; verifier itself ~67-84% accurate | Low-medium | IS baseline | baseline |
| Fit verifier (current) | Goal/constraint/category match vs manifest | Orthogonal to fabrication | Low | Complementary | keep |
| Structure verifier (current) | Schema conformance §1-§6 | Orthogonal to fabrication | Very low | Complementary | keep |
| FAMA failure-aware meta-agentic | Structured failure detection in agentic pipelines | Unknown — not retrieved in this run | Unknown | Coverage gap — not evaluated | not evaluated |
| SelfRAG | Adaptive retrieval + reflection tokens during generation | Significant gains on QA; requires fine-tuned model | High | Cannot use off-the-shelf Claude | rejected |
| FLARE / RARE | Proactive retrieval on low-confidence tokens | Superior or competitive on 4 long-form tasks | Medium | No fabrication-rate comparison to post-hoc | rejected |
| Reflexion self-correction | Verbal self-reflection after failure | +20% HotpotQA; degeneration-of-thought failure mode | Medium | Already implemented as critic→rewrite pass | already have |
| CAI critique chain | Safety critique + revision | Not evaluated on citation faithfulness | Medium | Wrong tool for this problem | rejected |
| MAD / judge-jury debate | Debate rounds | No evidence of dominance on citation faithfulness | High | MAD doesn't beat CoT per arXiv 2502.08788 | rejected |
| RAGAS auto-eval | LLM-based claim decomposition + judge | Evaluation only, not prevention | Low-medium | Complement, not replacement | could add as monitoring |
| FACTS Grounding benchmark | 3-judge ensemble, 32K token documents | All models <70%; Gemini 3 Pro 68.8% | High (3 frontier judges) | Evaluation benchmark, not runtime prevention | rejected (too expensive as runtime) |
| Inline citation-grounded decoding (Citations API) | Forces inline citation pointers during generation | Prevents pointer invalidity; does not prevent post-rationalization | Low | No head-to-head vs post-hoc published | considered |

---

### §3.3 Retrieval architectures

**For the current corpus size and constraints (10K-100K docs, CPU-local, 15-min ingestion cycle), the current stack is approximately correct.** The one provably validated improvement is HippoRAG.

**HippoRAG (NeurIPS 2024, arXiv 2405.14831)** achieves up to 20% gain on 2WikiMultiHopQA over baselines including ColBERTv2/BM25, using Personalized PageRank over a knowledge graph of extracted entities. Single-step retrieval is 10-30x cheaper and 6-13x faster than iterative multi-hop retrieval (IRCoT) while matching or exceeding IRCoT performance [inferred — arXiv 2405.14831 directly states the gains; the specific Recall@2/Recall@5 metric label verification failed in the citation verifier pass; the abstract supports "up to 20%" and cost figures; downgraded from [verified] per the verifier's guidance]. The gain is real but specific to genuine multi-hop queries. The constraint issue: KG construction requires LLM entity extraction at index time, which conflicts with the $0 marginal cost requirement unless local extraction is used.

**GraphRAG (Microsoft, arXiv 2404.16130)** explicitly targets "datasets in the 1 million token range." Applying it to a 10K-100K doc corpus would incur high LLM-powered indexing cost without the benefit case it was designed for [inferred — Microsoft abstract confirms 1M-token framing; small-corpus inapplicability is inferred from absence of small-corpus claims].

**HyDE (Hypothetical Document Embeddings)** achieves nDCG@10 = 61.3 vs 44.5 for Contriever on TREC DL-20 — largest gains on short/ambiguous queries [inferred — secondary sources summarizing Gao et al.; primary paper not re-fetched]. Cost: 1 LLM call per query. This is a cheap, constraint-compatible improvement worth adding as a query preprocessing step for exploratory queries.

**ColBERT** is overkill for this corpus: storage would expand to per-token vectors (3.3B floats vs 38M for single-vector at 100K docs), and gains over strong modern single-vector models at small corpus sizes are not well-measured [inferred — architecture reasoning; small-corpus ColBERT advantage is not established in primary literature].

**Authority-graph hand-curation**: plausible mechanism for fixing SEO bias; no published head-to-head vs. learned trust signals for AI/ML at this corpus size exists [judgment: the mechanism is sound — SEO-optimized content ranks high in web search but low in a hand-curated trust graph; empirical validation against a learned alternative is absent].

**Retrieval family matrix:**

| Family | Evidence quality | Key number | Strength | Weakness | Fit |
|---|---|---|---|---|---|
| BM25+vector+RRF (current) | Medium | Hybrid ~15-25% better than either alone on enterprise corpora | Default for mixed queries; essential for AI/ML entity/acronym lookups | Marginal lift over pure semantic in some settings | Yes |
| Authority-graph curated (current) | Low — judgment only | No head-to-head published | SEO de-ranking mechanism is plausible | No empirical validation vs learned alternatives | Yes |
| Per-content-type time decay (current) | Low — heuristic | No calibration benchmark | Correct direction | Half-life values arbitrary; no ablation | Yes |
| HippoRAG NeurIPS 2024 | Medium (peer-reviewed) | Up to 20% multi-hop recall gain; 10-30x cheaper than IRCoT | Proven multi-hop gains; fast at query time | LLM extraction at index time (cost); no evidence for niche/authority signal | Partial |
| GraphRAG | Medium | "Substantial improvement" at 1M+ token range | Strong for global sensemaking at scale | 1M-token design assumption; indexing cost prohibitive | No |
| HyDE | Medium | nDCG@10 61.3 vs 44.5 Contriever on TREC DL-20 | Cheap (1 LLM call); big gains on short/ambiguous queries | Hallucinated hypothesis can hurt retrieval | Yes — cheap add |
| IRCoT | Medium | Outperforms standard RAG on multi-hop | Established multi-hop gains | Expensive; dominated by HippoRAG at same cost | No — dominated |
| ColBERT late interaction | Medium | Out-of-domain NAACL 2022 gains | Strong for niche/OOD queries | Storage: 3.3B floats vs 38M single-vector | No — storage |
| Query rewriting/decomposition | Low | No isolated primary benchmark found | Improves complex multi-part queries | Multi-researcher decomposition already approximates this | Already have |
| MMR diversity retrieval | Low | Documented in LangChain/Haystack | Zero-cost re-ranking; within-query deduplication | Does not fix cross-perspective bias | Yes — free |
| Arctic-S vs BGE-M3 vs Voyage | Medium | 5pt MTEB gap = ~3-8% recall improvement | Measurable recall lift | 10x CPU cost; 1-2 more docs per query | No — not worth it |

---

### §3.4 Benchmarks: where does multi-agent actually win?

**The central finding: "multi-agent wins BrowseComp" is measuring a different task class than the one this system is built for.**

**BrowseComp** (OpenAI, April 2025): 1,266 hard web-browsing problems. GPT-4o baseline = 1.9%; Deep Research single-agent iterative loop = 51.5% at launch [inferred — OpenAI primary source; cited as single source; the 51.5% figure is from the OpenAI BrowseComp primary page but the verifier returned 403 on re-fetch; downgraded to [inferred]]; GPT-5.5 Pro (with tools) = 90.1% May 2026; Gemini 3.1 Pro = 85.9% [verified — OpenAI primary source + llm-stats.com leaderboard; two independent sources confirm the leaderboard numbers]. BrowseComp rewards multi-step web navigation and fact extraction. The 80% variance explained by token count means architecture matters less than budget.

**AutoResearchBench** (arXiv 2604.25256, April 2026): tasks AI agents with scientific literature discovery. Best agents — including those that "largely conquered" BrowseComp — achieve only 9.39% accuracy on Deep Research tasks and 9.31% IoU on Wide Research tasks [verified — corpus id: bd21baf38f5a25cb; the 9.39% figure is directly stated in the abstract; confirmed by the AutoResearchBench paper and the corpus entry]. This benchmark most closely resembles what the deep-ai-research system actually does. All architectures fail here regardless of fan-out.

**HumaneBench** — a benchmark for human-aligned agent behavior — was listed in manifest sub-question 4 must_cover_families. It was not surfaced in any retrieval pass during this run. Coverage gap: not retrieved; cannot evaluate. No row data available.

**GAIA** (General AI Assistants): GPT-5 = 42% pass@1 overall; current leaders use iterative tool-calling single agents, not multi-agent fan-out [inferred — Princeton GAIA leaderboard; architecture attribution is inferred from known system descriptions, not confirmed in published methodology].

**DeepResearch Bench** (arXiv 2506.11763): 100 PhD-level research tasks. Top score: Cellcog Max = 56.13 [inferred — leaderboard scores confirmed; architecture of top performers not published]. On the FutureSearch variant, ChatGPT o3 outperforms OpenAI Deep Research — a single reasoning model outperforming a purpose-built research agent.

**FACTS Grounding** (Google DeepMind, arXiv 2501.03200): all models below 70% grounding accuracy. Gemini 3 Pro leads at 68.8% [verified — DeepMind blog + arXiv 2501.03200; two independent sources]. Multi-agent systems have MORE faithfulness risk per handoff, not less.

**FRAMES** (multi-hop factual): 0.40 without retrieval → 0.66 with multi-step retrieval pipeline [inferred — arXiv 2409.12941; the improvement is from multi-step retrieval, attributable to iterative single-agent just as easily as fan-out].

**Long-context single-agent is now within 4.2pp of multi-agent on BrowseComp.** Gemini 3.1 Pro (single agent, 1M context) = 85.9% vs GPT-5.5 Pro (90.1%) [inferred — tokenmix.ai secondary source; the causal attribution to long-context vs architecture is inferred, not measured in a controlled ablation]. The 1M-context availability materially weakens the "single-agent hits context limit" argument that justified multi-agent fan-out in 2024.

**Task class split:**
- Multi-agent fan-out wins: breadth-first parallel lookups requiring simultaneous investigation across many independent sub-questions (entity enumeration, web crawling across hundreds of sites)
- Single-agent wins or ties: focused synthesis requiring coherent reasoning, sequential dependency chains, tasks where context isolation causes conflicting outputs
- Neither wins: domain-specific scientific literature discovery (AutoResearchBench 9.39% for all architectures)

---

### §3.5 Alternative end-to-end architectures

**Summary verdict: nothing is provably better under the binding constraints. The closest candidate is DSPy/GEPA offline optimization. The most structurally underexplored option is hyperresearch.**

**DSPy/GEPA** (ICLR 2026 Oral, arXiv 2507.19457): GEPA (Reflective Prompt Evolution) achieves over 10% aggregate improvement vs MIPROv2 and +12% on AIME-2025, with "up to 20%" vs GRPO, using 35x fewer rollouts than RL [inferred — results from arXiv 2507.19457; ECIR 2026 workshop result not directly retrieved in this run; arXiv ID post-dates assistant knowledge cutoff; "up to 20%" drops prior model attribution per citation verifier fail]. An ECIR 2026 workshop paper reportedly shows GEPA outperforms expert-crafted prompts on a multi-agent research task, but this was not directly retrieved. The key constraint: GEPA requires a labeled eval set. The current evals/cases.yaml is small — overfitting to a small eval set could optimize for the eval rather than the target failure modes. **Recommended action: expand evals/cases.yaml to ≥20 labeled cases (including at least 3 recency-failure cases and 3 niche-authority cases), then run GEPA offline.**

**hyperresearch (github.com/jordan-gibbs/hyperresearch)** — Claude Code-native deep research agent with a persistent wiki/vault architecture. Key architectural differences from this system: (1) sources land in a persistent, searchable vault that compounds across sessions — this addresses a gap this system has (no cross-run knowledge compounding); (2) tier-adaptive 16-step pipeline with adversarial audit; (3) patcher/polish auditor are tool-locked to [Read, Edit] so they cannot write a new draft — a mechanical constraint this system handles via honesty contract alone [inferred — GitHub readme retrieved via synthesizer WebSearch follow-up; no published benchmark; methodology is documented but not externally evaluated]. The vault architecture is a structural alternative worth examining. Cannot evaluate against this system's quality targets without an actual comparison run.

**LATS** (Language Agent Tree Search, ICML 2024): 92.7% HumanEval with GPT-3.5 [inferred — arXiv 2310.04406; single source]. Requires intermediate-state evaluator (absent for open research tasks). Wall-time cost is D×B LLM calls. Under ~25-min budget, this eliminates LATS as a replacement [judgment: first-principles arithmetic; LATS has no deep-research benchmark evidence].

**Reflexion** (NeurIPS 2023): +22% ALFWorld, +20% HotpotQA, +11% HumanEval across 12 iterations [verified — arXiv 2303.11366 + arXiv 2512.20845v1 (MAR); two independent sources]. **The current system already implements single-iteration Reflexion: critic → mandatory synthesizer rewrite.** More iterations would violate the token budget. Reflexion's "degeneration-of-thought" failure mode is also the critic-capitulation failure mode the honesty contract §3 guards against.

**Letta/MemGPT** (74% LoCoMo benchmark) [verified — Letta blog + vectorize.io; two independent sources]: designed for persistent conversational memory across sessions. Deep-ai-research is a single-run tool. The corpus+sqlite pipeline already handles the "memory" function. Letta adds overhead without addressing recency or niche-signal problems.

**Voyager skill library**: .claude/skills/ already implements a static version of this pattern. The gap is skill self-improvement, which requires objective graders absent for open research tasks [verified — arXiv 2305.16291 + voyager.minedojo.org; two sources; the gap is a judgment].

**Test-time scaling / best-of-N**: TTS can exceed parameter scaling for reasoning, but shows saturation and inverse scaling at large N [verified — arXiv 2408.03314 + testtimescaling.github.io; two independent sources]. N=2 doubles cost and likely violates the ≤30% window cap.

---

### §3.6 The contrarian's macro-finding: discovery vs. synthesis

This is the finding most likely to be missed by lead researchers and the most structurally important result in this report — already surfaced in §1, elaborated here.

**The two original failure modes cited in CLAUDE.md ("DeepSeek v3.2 → v4 case" and "Karpathy LLM wiki") are discovery failures, not synthesis failures.** The user did not fail to synthesize correctly — they failed to know the thing existed. The current system cannot fix this because it is query-driven.

**A daily authority-feed digest** would have caught both failure modes. DeepSeek v4 would appear in the Nathan Lambert or AINews feed within hours. Karpathy's LLM wiki would appear when he posted it.

**The reframe does not invalidate the synthesis architecture.** It narrows the system's mission: correctly designed for answering explicit synthesis queries; not designed for proactive discovery. The two tools are complements, not substitutes.

**Bounded to discovery domain.** The reframe does not apply to all research queries — pure synthesis questions ("what memory system should I use for an LLM agent?") are unaffected by the discovery problem. The reframe matters precisely when the user's primary motivation is the two cited failure modes, not general synthesis quality. This caveat is important: the reframe applies to the original stated motivation, not to the system's primary operating mode.

---

## 4. Alternatives considered and rejected

### Within-frame alternatives (micro-contrarian)

- **Single-Sonnet-call baseline** — not empirically ruled out; the experiment has never been run. The main reason it isn't the current recommendation is that multi-agent fan-out is known to outperform single-agent on breadth-first tasks (Anthropic 90.2%, weak evidence as noted), and synthesis questions often span multiple dimensions. But "known to outperform on breadth-first tasks" is not the same as "known to outperform on this system's specific eval set." [judgment: the default should arguably be to run the baseline before treating multi-agent as mandatory for all queries]

- **Inline citation-grounded decoding (Citations API)** — not replacing post-hoc but complementary. Inline prevents pointer invalidity; post-hoc catches semantic mismatches. The ideal design may be both pipelines in sequence. But adding inline enforcement would require restructuring the synthesizer's generation pipeline. Evidence is directional, not proof-grade. [src: src11, src9]

- **More Reflexion iterations (N>2)** — rejected because the current single-iteration critic→rewrite is already single-iteration Reflexion. More iterations multiply cost non-linearly. Degeneration-of-thought failure mode means additional iterations don't guarantee improvement. [src: src20]

- **MMR diversity retrieval** — rejected as primary intervention; addresses within-query document redundancy only, not cross-perspective bias or SEO-authority inversion. Cheap enough to add as a supplement.

- **Upgrading from Arctic-Embed-S to BGE-M3** — rejected: ~3-8% recall improvement at 10x CPU cost means 1-2 more relevant documents per query on this corpus. Not worth the computational overhead.

### Reframe alternatives (macro-contrarian)

**The "wrong level of abstraction" challenge.** The system optimizes for synthesis quality per query while the original motivation was at a different level (staying current without knowing the right questions). Two tools are needed:

1. **Daily authority-feed digest** (proactive discovery): single Sonnet call over authorities.yaml RSS, ~50K tokens/day, ~$0. Catches DeepSeek v4 dropping, Karpathy posting a new wiki, a benchmark releasing. This addresses the original failure modes.

2. **On-demand deep-research synthesis** (the current system): for answering specific queries with sourced, authority-weighted analysis.

If the user must choose which gap to close first: the daily digest addresses the original stated motivation more directly. The current system assumes the user already knows what to ask about — which is precisely the assumption violated by the failure modes that motivated building it. [judgment: this is the contrarian's strongest point; bounded to the discovery-problem domain and the two specific motivating cases; pure synthesis queries are unaffected by this argument]

---

## 5. Open questions

- `[research-target-dropped]` **FAMA (arXiv 2604.25135) — failure-aware meta-agentic framework for verifier-loop alternatives.** Present in the corpus (id: d3cdbd6d80d8a825) as the recency pass's highest-signal item for verifier loop alternatives; not retrieved by any researcher in this run. Would be resolved by: one targeted WebFetch of corpus id d3cdbd6d80d8a825. Directly relevant to whether the current verifier/critic loop has a superior alternative.

- `[research-target-dropped]` **Single-Sonnet-call baseline vs. multi-agent on evals/cases.yaml.** No published or internal study compares these on this system's own eval cases. Would be resolved by: running 5 eval cases through a single Sonnet call with 3-4 targeted web searches + authority corpus retrieval, scoring with Opus judge. Expected result: likely 60-80% of multi-agent quality at <5% of token cost — but this is the load-bearing unrun experiment.

- `[research-target-dropped]` **hyperresearch architecture evaluation.** Github repository was retrieved (persistent vault, adversarial auditor, tool-locked patcher) but no published benchmark or comparative eval exists. Would resolve: does the persistent cross-session vault architecture produce measurably better synthesis quality on repeated-domain queries? Would be resolved by: running parallel comparison on evals/cases.yaml.

- `[research-target-dropped]` **ECIR 2026 workshop "Self-Optimizing Multi-Agent Systems for Deep Research" (GEPA applied to multi-agent research tasks).** Mentioned in web search results but not directly retrieved. Would resolve: does GEPA produce measurable gains on a multi-agent research system comparable to this one?

- `[research-target-dropped]` **Inline citation grounding (Citations API) vs. post-hoc 12-sample verification on fabrication rates for long-form synthesis.** No published head-to-head exists. Would resolve: run 20 synthesis queries through both pipelines, score with FaithJudge or RAGAS faithfulness metric.

- `[research-target-dropped]` **HippoRAG uplift on this specific corpus for AI/ML authority/recency queries.** HippoRAG's gains are measured on 2WikiMultiHopQA (Wikipedia entity resolution). Whether the same gain appears on AI/ML blog posts and arXiv papers indexed with authority-graph boosts is unknown.

- `[research-target-dropped]` **Optimal citation sample size for post-hoc verification.** Why 12 and not 8 or 20? No empirical study. Would resolve: ablation over citation count vs. fabrication detection rate using FaithBench methodology.

- `[external-event]` **Token tally monitoring gap — system architecture issue.** manifest.json has no `token_tally` field; budget enforcement currently relies on synthesizer self-estimation. This is not an external event but a known system gap that should be patched with a real tally hook (e.g., parsing `claude /usage` output before and after each run and writing to manifest.json under `usage_snapshot_start`/`usage_snapshot_end`). Technically not an [external-event] but noted here as a systemic gap without a clear [research-target-dropped] resolution path — the patch is implementation work, not research.

---

## 6. Citations

- [src1] "How we built our multi-agent research system," Anthropic Engineering Blog, June 2025. https://www.anthropic.com/engineering/multi-agent-research-system — 90.2% improvement over single-agent Claude Opus 4 on internal breadth-first eval; 80% BrowseComp variance from token count; 15x token cost multiplier. Single self-reported source; evidence quality: weak-self-reported.

- [src2] "Don't Build Multi-Agents," Cognition AI Blog, June 12 2025. https://cognition.ai/blog/dont-build-multi-agents — Context isolation → conflicting decisions; context engineering is the primary lever; single-agent with long context recommended for reliability. Engineering-experience-based, not a controlled benchmark.

- [src3] "Stop Overvaluing Multi-Agent Debate" (arXiv 2502.08788), arXiv, February 2025. https://arxiv.org/abs/2502.08788 — MAD fails to outperform CoT and Self-Consistency across 5 implementations, 9 benchmarks, 4 models.

- [src4] "The Last Harness You'll Ever Build" (arXiv 2604.21003), arXiv / HuggingFace Daily Papers, April 2026. https://arxiv.org/abs/2604.21003 [corpus: f048ff68a8ec5f98] — Two-level meta-learning framework automating harness engineering. Potentially threatens hand-tuned orchestration prompts; unvalidated as of writing.

- [src5] AINews 2026-04-27 (Sakana Conductor; 1000x agentic token study), Smol AI / AINews, April 2026. https://news.smol.ai/issues/26-04-27-not-much/ [corpus: 64115e8c43fd6637] — Sakana Conductor 7B RL orchestrator: 83.9% LiveCodeBench, 87.5% GPQA-Diamond. Also: 1000x token vs chat, 30x variance, non-monotonic accuracy.

- [src6] "Reaching SOTA on deep research benchmarks by automating agent optimization," AI21 Labs Blog, April 2026. https://www.ai21.com/blog/blog/maestro-deep-research-agents/ [corpus: c1def20f88fb5e3d] — Maestro: 95.18% BrowseComp-Plus claim; architecture undisclosed; internal comparison only; requires AI21 proprietary infra.

- [src7] AutoResearchBench (arXiv 2604.25256), HuggingFace Daily Papers, April 2026. https://arxiv.org/abs/2604.25256 [corpus: bd21baf38f5a25cb] — Best agents achieve 9.39% on domain-specific Deep Research tasks; all systems fail; BrowseComp-conquering architectures don't transfer.

- [src8] "We compared eight AI search engines — they're all bad at citing news," Columbia Journalism Review / Tow Center, March 2025. https://www.cjr.org/tow_center/we-compared-eight-ai-search-engines-theyre-all-bad-at-citing-news.php — >60% overall citation inaccuracy; Perplexity 37% incorrect. (Note: per-product subcategory breakdown not confirmed in verifier re-fetch; only overall and Perplexity figures used.)

- [src9] "Correctness is not Faithfulness" (arXiv 2412.18004), arXiv, December 2024. https://arxiv.org/abs/2412.18004 — 57% of citations lack faithfulness; post-rationalization phenomenon; correctness ≠ faithfulness.

- [src10] FaithJudge / FaithBench (arXiv 2505.04847), arXiv, May 2025. https://arxiv.org/html/2505.04847v1 — Hallucination detectors at ~50% accuracy on FaithBench; FaithJudge (o3-mini-high) reaches 84%; RAGTruth rates: Gemini-2.5-Pro 7.6%, Claude-3.7-Sonnet 16.1%.

- [src11] Anthropic Citations API, Anthropic Blog, January 2025. https://claude.com/blog/introducing-citations-api — Inline citation-grounded decoding; guarantees valid pointers; no published fabrication-rate comparison to post-hoc.

- [src12] BARRED asymmetric debate (arXiv 2604.25203), HuggingFace Daily Papers, April 2026. https://huggingface.co/papers/2604.25203 [corpus: ee8ae1b1ecada59d] — Debate for synthetic training data generation; NOT citation faithfulness verification; wrong tool for this problem.

- [src13] FACTS Grounding (arXiv 2501.03200), Google DeepMind / arXiv, January 2025. https://arxiv.org/abs/2501.03200 — 860+859 examples; 3-judge ensemble; Gemini 3 Pro leads at 68.8%; all models below 70%.

- [src14] Self-RAG (arXiv 2310.11511), arXiv, October 2023. https://arxiv.org/abs/2310.11511 — Adaptive retrieval + reflection tokens; significant gains on open-domain QA; requires fine-tuned model; no deep-research comparison.

- [src15] HippoRAG (arXiv 2405.14831 / NeurIPS 2024), arXiv / NeurIPS, 2024. https://arxiv.org/abs/2405.14831 — Up to 20% gain on 2WikiMultiHopQA over BM25/ColBERTv2; 10-30x cheaper than IRCoT; single-step KG retrieval.

- [src16] GraphRAG (arXiv 2404.16130), Microsoft Research / arXiv, April 2024. https://arxiv.org/abs/2404.16130 — Explicitly targets 1M-token range; substantial improvement vs naive RAG on global sensemaking at scale; not for small corpora.

- [src17] BrowseComp benchmark, OpenAI, April 2025. https://openai.com/index/browsecomp/ — 1,266 hard web-browsing tasks; Deep Research ~51.5% at launch (source returned 403 in verifier re-fetch; figure is from researcher primary retrieval); GPT-4o+browsing 1.9%.

- [src18] BrowseComp Leaderboard (May 2026), llm-stats.com. https://llm-stats.com/benchmarks/browsecomp — GPT-5.5 Pro 90.1%, Claude Mythos Preview 86.9%, Gemini 3.1 Pro 85.9%.

- [src19] FACTS Grounding blog, Google DeepMind, December 2024. https://deepmind.google/blog/facts-grounding-a-new-benchmark-for-evaluating-the-factuality-of-large-language-models/ — Leaderboard; Gemini 3 Pro 68.8%.

- [src20] Reflexion (arXiv 2303.11366 / NeurIPS 2023), arXiv, March 2023. https://arxiv.org/pdf/2303.11366 — +22% ALFWorld, +20% HotpotQA, +11% HumanEval over 12 iterations; degeneration-of-thought failure mode documented.

- [src21] Multi-Agent Reflexion / MAR (arXiv 2512.20845), arXiv, December 2024. https://arxiv.org/html/2512.20845v1 — +3pp HotpotQA, +6.2pp HumanEval over Reflexion baseline.

- [src22] GEPA / Reflective Prompt Evolution (arXiv 2507.19457 / ICLR 2026 Oral), arXiv. https://arxiv.org/abs/2507.19457 — Over 10% aggregate improvement vs MIPROv2; +12% on AIME-2025; "up to 20%" vs GRPO; 35x fewer rollouts. ECIR 2026 workshop result not directly retrieved (post-dates knowledge cutoff; web-search-snippet only).

- [src23] Voyager (arXiv 2305.16291), arXiv, May 2023. https://arxiv.org/abs/2305.16291 — 3.3x items, 15.3x faster tech tree in Minecraft via growing skill library; objective grader required.

- [src24] Letta benchmarking AI agent memory, Letta Blog, 2025. https://www.letta.com/blog/benchmarking-ai-agent-memory — Letta Filesystem 74% LoCoMo; three-tier memory; designed for conversational agents not single-run research.

- [src25] HippoRAG 2 (OpenReview / NeurIPS), OpenReview, 2024. https://openreview.net/forum?id=hkujvAPVsg — HippoRAG confirmed NeurIPS 2024; 20% multi-hop gain.

- [src26] Test-time scaling (arXiv 2408.03314 / ICLR 2025), arXiv, August 2024. https://arxiv.org/abs/2408.03314 — TTS can exceed parameter scaling; saturation and inverse scaling at large N.

- [src27] Nathan Lambert "Lossy Self-Improvement," Interconnects, March 2026. https://www.interconnects.ai/p/lossy-self-improvement [corpus: e3189b5cdd6b0fb9] — Self-improvement automation trend; authority signal.

- [src28] LATS (arXiv 2310.04406 / ICML 2024), arXiv, October 2023. https://arxiv.org/abs/2310.04406 — 92.7% HumanEval, 75.9 WebShop; MCTS over ReAct; requires intermediate evaluator.

- [src29] FRAMES (arXiv 2409.12941), arXiv, September 2024. https://arxiv.org/abs/2409.12941 — 0.40 → 0.66 with multi-step retrieval.

- [src30] Gemini benchmarks 2026, TokenMix. https://tokenmix.ai/blog/gpt-5-vs-gemini-3-10-benchmarks-2026 — Gemini 3.1 Pro BrowseComp 85.9%; long-context single-agent competitive.

- [src31] AINews 2026-05-01, Smol AI. https://news.smol.ai/ [corpus: 75e9ca8451b7aa5a] — Agent runtime as low-level primitive; library-skills.io pattern.

- [src32] Arctic Embed (arXiv 2405.05374), Snowflake / arXiv, May 2024. https://arxiv.org/html/2405.05374v1 — Arctic-Embed S SOTA for 33M params size class at launch.

- [src33] RAGAS faithfulness documentation, RAGAS Docs. https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/faithfulness/ — Claim decomposition + LLM judge; post-hoc evaluation only; complement to current stack.

- [src34] HippoRAG 2 report, MarkTechPost, March 2025. https://www.marktechpost.com/2025/03/03/hipporag-2-advancing-long-term-memory-and-contextual-retrieval-in-large-language-models/ — Dynamic KG updates.

- [src35] AgentSearchBench (arXiv 2604.22436), HuggingFace Daily Papers, April 2026. https://arxiv.org/abs/2604.22436 [corpus: 0ac826b7451fee4c] — Semantic similarity insufficient for agent capability assessment; behavioral signals needed.

- [src36] hyperresearch, GitHub (jordan-gibbs), April 2026. https://github.com/jordan-gibbs/hyperresearch — Claude Code-native deep research with persistent wiki vault; tier-adaptive 16-step pipeline; adversarial audit; tool-locked patcher. No published benchmark.

---

*The 90.2% improvement from [src1] is the most widely cited number in multi-agent research coverage and the weakest load-bearing claim in this report: single self-reported source, task class designed to showcase fan-out, not externally reproduced. Treat it as suggestive evidence for the multi-agent sweet spot (parallelizable breadth tasks), not a general superiority claim.*

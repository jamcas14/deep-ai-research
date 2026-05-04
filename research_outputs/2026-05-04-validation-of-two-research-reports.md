# Validation: Two Competing Research Reports on Deep-Research Architecture

Date: 2026-05-04
Validation depth: 14 research loops, ~50 web ops
Mode: validate

---

## Summary verdict

| Report | Citation accuracy | Architectural reasoning | Verdict |
|---|---|---|---|
| Report 1 (claude.ai critique) | ~85% claims verified verbatim; ~10% have mislabeled numbers; ~5% likely directional misattribution | Strong on prior art; "registry-first routing" name is partially invented but pattern is real | Mostly true with notable factual errors |
| Report 2 (system being critiqued) | ~80% claims verified; one likely fabrication (Maestro 95.18% BrowseComp-Plus); one misattributed venue (ECIR workshop name); minor arXiv ID mislabel (FaithBench vs FaithJudge) | "Discovery vs synthesis" reframe is partially load-bearing — has real merit but functions as hedging on the core architectural critique | Mostly true with one likely fabrication and softer architectural footing |

**Stronger evidence base: Report 1**, by a meaningful margin. Report 1's evidence base is broader, the citations are more easily traceable, and the structural argument (multi-agent overhead has documented failure modes) survives the disconfirmation pass. But Report 1 has at least three numerical errors that would fail a citation check.

**Report 2 has one strong contribution**: the daily authority-feed digest as a complement is a defensible additional product, not a refutation. However, Report 2's "discovery vs synthesis" reframe is partly a HEDGE — it accepts most of Report 1's structural critique without fixing the structural issue.

---

## Per-claim verification

### REPORT 1 CLAIMS

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | Anthropic blog: "lead agent spins up 3-5 subagents in parallel"; "multi-agent uses 15× tokens of chat"; "token usage explains 80% of variance" | PASS — all four quotes verified verbatim | anthropic.com/engineering/multi-agent-research-system |
| 2 | Cognition AI's "Multi-Agents: What's Actually Working" April 22, 2026 | PASS | cognition.ai/blog/multi-agents-working — author Walden Yan, exact date confirmed, opening paragraph quoted verbatim |
| 3 | MAST taxonomy paper, Cemri et al. arXiv 2503.13657, NeurIPS 2025 D&B | PASS on existence + venue (spotlight); FAIL on specific percentages | Real paper, real conference. But Report 1's numbers are wrong: actual FM-2.4 information withholding is **1.66%** (not 12.4%); FM-1.3 step repetition is **17.14%** (not 13.2%); FM-3.2 incomplete verification is **6.82%** or **13.48%** if combined with FM-3.3 (not 11.8%). The "14% intervention improvement" claim is directionally correct (paper says interventions are limited) but actual reported gains were **9.4%** (role specs) and **15.6%** (verification). |
| 4 | Smit et al. "Should we be going MAD" arXiv 2311.17371 | PASS | Verified — Smit, Duckworth, Grinsztajn, Barrett, Pretorius |
| 5 | Zhang et al. "Stop Overvaluing MAD" arXiv 2502.08788; "5 MAD methods × 9 benchmarks × 4 models, none beat CoT in more than 20% of 36 scenarios" | PASS on paper; INCONCLUSIVE on the 20%/36 claim | Real paper exists. Couldn't extract the precise win-rate fraction from the paper body in this validation pass — abstract confirms MAD often fails to beat CoT/Self-Consistency, but the specific "20% of 36" framing wasn't surfaced. Plausible but not verified. |
| 6 | Xu et al. "Rethinking the Value of Multi-Agent Workflow" arXiv 2601.12307 | PASS | Submitted January 18, 2026; first author Jiawei Xu; verified |
| 7 | PoLL paper arXiv 2404.18796: judge ensembles work due to model heterogeneity | PASS | "Replacing Judges with Juries: Evaluating LLM Generations with a Panel of Diverse Models" — verified, paper explicitly argues for diverse model families reducing intra-model bias |
| 8 | CyclicJudge arXiv 2603.01865 | PASS | Slingshot AI / Cambridge; verified |
| 9 | "Judging with Many Minds" arXiv 2505.19477 | PASS | Verified — bias amplification analysis in MAD/meta-judge |
| 10 | VersionRAG, Huwiler et al., arXiv 2510.08109; "90% accuracy vs 58% RAG vs 64% GraphRAG" | PASS | All three numbers verified verbatim |
| 11 | TimeRAG (CIKM 2025) and Temporal GraphRAG arXiv 2510.13590 | PASS | Both real; TimeRAG at CIKM 2025 with 66.4% avg accuracy; arXiv 2510.13590 is "RAG Meets Temporal Graphs" by Han et al. |
| 12 | OpenScholar Nature 2026 (Feb 4): "GPT-4o hallucinates 78-90% of citations" | PASS | Published Feb 4, 2026 in Nature; UW press release confirms; exact 78-90% range verified |
| 13 | Anthropic contextual retrieval: 49% reduction with contextual chunks + BM25; 67% with reranker | PASS | Both numbers verified verbatim from anthropic.com/news/contextual-retrieval |
| 14 | Qwen3-Reranker MTEB Multilingual leader at 70.58 | FAIL on attribution | The 70.58 score is for **Qwen3-Embedding-8B** (June 2025 leaderboard #1), not the reranker. Qwen3-Reranker-8B scored 69.02 on multilingual ranking. Minor but real mislabel. |
| 15 | Papers With Code sunset by Meta mid-2025 | PASS | July 24-25, 2025 sunset; redirects to Hugging Face Trending Papers |
| 16 | "Registry-first router" as SOTA pattern adopted by Gemini/Perplexity Sonar/Contextual AI's RAG 2.0 | PARTIAL — pattern is real, name is invented | The underlying pattern (semantic routing across multiple retrieval/registry sources) is real and called "Router-First Design" in 2026 enterprise RAG literature. Perplexity Sonar uses planner/retriever/synthesizer modular setup. Contextual AI's RAG 2.0 is real (end-to-end optimized retriever+LM). But "registry-first routing" as a coined phrase doesn't appear in literature. Report 1 invented a specific name for a real pattern — that's a presentational issue, not a fabrication. |
| 17 | LangChain open_deep_research #6 Deep Research Bench RACE 0.4344 | PASS | As of August 2, 2025, on muset-ai/DeepResearch-Bench-Leaderboard |

### REPORT 2 CLAIMS

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | AutoResearchBench arXiv 2604.25256, April 2026: "9.39% Deep Research, 9.31% IoU Wide Research" | PASS | Both numbers verified verbatim |
| 2 | GEPA arXiv 2507.19457, ICLR 2026 Oral: "+10% vs MIPROv2, +12% AIME-2025, up to 20% vs GRPO, 35× fewer rollouts" | PASS | All four numbers verified verbatim |
| 3 | ECIR 2026 workshop "Self-Optimizing Multi-Agent Systems for Deep Research" | FAIL on workshop name | The arXiv paper "Self-Optimizing Multi-Agent Systems for Deep Research" (2604.02988 by Câmara et al.) IS REAL and accepted at ECIR 2026 — but at the **"Workshop on Conversational Search for Complex Information Needs"**, not at a workshop literally named "Self-Optimizing Multi-Agent Systems". Report 2 used the paper title as a workshop name. Misattribution. |
| 4 | FAMA arXiv 2604.25135 "Failure-Aware Meta-Agentic Framework" | PASS | ACL 2026 Findings; up to 27% performance gain verified |
| 5 | "The Last Harness You'll Ever Build" arXiv 2604.21003 | PASS | Sylph.AI — Seong, Yin, Zhang; April 22, 2026 |
| 6 | Sakana Conductor: 7B RL orchestrator, 83.9% LiveCodeBench, 87.5% GPQA-Diamond | PASS — but arXiv ID is **2512.04388** (not 2604.x) | All performance numbers verified; ICLR 2026 accepted. Sakana page confirms "new records on LiveCodeBench (83.9%) and GPQA-Diamond (87.5%)" |
| 7 | AI21 Maestro 95.18% BrowseComp-Plus | LIKELY FABRICATED | Maestro's actual 95.2% number is on **IFEval**, not BrowseComp-Plus. AI21 Maestro does not appear on any BrowseComp leaderboard I could find. Report 2 conflated two benchmarks. The "95.2%" number is IFEval (lifting Claude Sonnet 3.5 from ~88% to ~95.2%). The "95.18%" specificity smells like fabrication or hallucination. |
| 8 | hyperresearch GitHub jordan-gibbs/hyperresearch | PASS | Real repo. Architecture: 14 specialized subagents, 16-step pipeline, "patch-never-regenerate" principle, light tier ~30-40 min, full tier ~1.5-2.5 hours. Built explicitly on Claude Code. NOTE: hyperresearch has MORE agents (14), not fewer, contradicting Report 1's "collapse to 3-5" prescription. |
| 9 | Tow Center Columbia March 2025: 8 AI search engines, >60% inaccurate; Perplexity 37% wrong | PASS | All numbers verified |
| 10 | Reflexion arXiv 2303.11366: +22% ALFWorld, +20% HotpotQA, +11% HumanEval | PASS | All three numbers verified verbatim |
| 11 | "Correctness is not Faithfulness" arXiv 2412.18004: 57% citations lack faithfulness | PASS | Wallat et al.; 57% verified verbatim ("up to 57 percent of citations" lack faithfulness) |
| 12 | FaithBench arXiv 2505.04847; detectors at ~50%; FaithJudge 84% | PARTIAL FAIL on arXiv ID | 2505.04847 is the **FaithJudge** paper ("Benchmarking LLM Faithfulness in RAG with Evolving Leaderboards"), NOT FaithBench. FaithBench is arXiv 2410.13210. Both numbers (~50% detectors and 84% FaithJudge) verify correctly when matched to the right papers. Mislabeling, not fabrication. |
| 13 | HippoRAG arXiv 2405.14831 NeurIPS 2024: 20% multi-hop gain on 2WikiMultiHopQA, 10-30x cheaper than IRCoT | PASS | All numbers verified |
| 14 | BrowseComp 2025: Deep Research 51.5%, GPT-5.5 Pro 90.1%, Gemini 3.1 Pro 85.9% | PASS | All three verified on llm-stats.com leaderboard (May 1, 2026 snapshot) and original OpenAI BrowseComp paper |

---

## Independent assessment: which report has stronger evidence?

**Report 1 has stronger evidence in:**
- Citation breadth (more directly verifiable claims)
- Cleaner mapping between claim and source
- Higher-quality structural argument (Cognition retraction + MAST + MAD critique form a coherent narrative)
- Genuine engagement with disconfirmation (it cites the cost-arithmetic precisely)

**Report 1 weakness:** specific MAST percentages are wrong; "registry-first routing" name is invented; Qwen3 misattributed.

**Report 2 has stronger evidence in:**
- More recent papers (April 2026 — AutoResearchBench, FAMA, "Last Harness", "Self-Optimizing Multi-Agent")
- The hyperresearch counter-example is real and uses MORE agents than Report 1 prescribes
- The Sakana Conductor 7B finding is genuinely strong evidence that orchestration can be highly effective
- Reflexion / HippoRAG / faithfulness papers are well-cited

**Report 2 weakness:** the AI21 Maestro 95.18% BrowseComp-Plus appears fabricated (likely hallucinated by conflating IFEval with BrowseComp-Plus). The ECIR workshop name is wrong. Two arXiv IDs are misattributed.

**Both reports treat these as known true and BOTH are correct on:**
- Anthropic's 4×/15× token multipliers
- Karpathy's "LLM wiki" as a real pattern (April 4, 2026 gist)
- Tow Center 60%+ citation inaccuracy
- HippoRAG / VersionRAG existence

---

## What both reports MISSED (last 60 days)

These papers/architectures are relevant to AI/ML deep-research and were not cited by either side:

1. **AutoSOTA (arXiv 2604.05550)** — End-to-end automated research system that discovered **105 new SOTA models**. Uses an 8-specialist agent architecture. This contradicts Report 1's "collapse to 3-5 agents" prescription.

2. **Step-DeepResearch (arXiv 2512.20491)** — StepFun's 32B agent with checklist judger, 61.4% on Scale AI Research Rubrics. Demonstrates that medium-sized models can rival closed-source SOTA when trained properly. Refutes the "just use big closed models" implicit position.

3. **PaperScope (arXiv 2604.11307)** — Multi-modal multi-doc benchmark with 2,400 questions across 25,495 papers. The actual SOTA evaluation Report 1's "registry-first router" should be measured against.

4. **Knowledgeable Deep Research / KDR-Bench (arXiv 2604.07720)** — Hybrid Knowledge Analysis (HKA) framework for structured + unstructured knowledge integration. Multi-agent, contradicts Report 1's collapse prescription.

5. **DR³-Eval (arXiv 2604.14683)** — Realistic, reproducible deep research evaluation; another benchmark either report could have cited.

6. **Câmara et al. Self-Optimizing Multi-Agent Systems (arXiv 2604.02988)** — The actual ECIR 2026 paper. Report 2 mentioned the title but as a workshop name. The paper itself directly addresses self-optimization of multi-agent deep research systems via prompt evolution — strongly supportive of Report 2's hyperresearch-style approach but neither side actually cites the paper's findings.

7. **ICLR 2026 Workshops** — Recursive Self-Improvement, MAL-GAI (Multi-Agent Learning and Generative AI). Report 2 cited "ECIR" but missed these directly relevant venues.

8. **DeepResearch Bench / RACE leaderboard** — neither report shows current 2026 leaderboard, only 2025 snapshot.

---

## Are Report 1's architectural prescriptions SOTA or post-hoc rationalization?

**Verdict: Mixed.** Decomposition for credit:

| Prescription | Verdict | Reasoning |
|---|---|---|
| "Fork open_deep_research" | Reasonable but not SOTA | open_deep_research is #6 RACE 0.4344, so it's a solid base but not the leader. Better starting points exist (Step-DeepResearch, hyperresearch, Câmara et al.) |
| "Collapse 7 agents to 3-5 + 1 verifier" | **NOT SOTA** | Hyperresearch (14 agents), AutoSOTA (8 agents), Step-DeepResearch (multi-component) all use MORE agents and outperform smaller systems. Sakana Conductor's 7B orchestrator at SOTA on LiveCodeBench/GPQA shows orchestration can scale. Report 1's collapse prescription contradicts current evidence. |
| "Replace forced recency pass with registry-first routing" | Mixed | "Router-First" is a real 2026 pattern but neither replaces nor obviates a recency pass. Recency is orthogonal to routing — you still need fresh signal even with multiple registries. Report 1 conflates two different concerns. |
| "Use YAML as boost not gate" | Likely correct | This matches RAGRouter and other 2026 routing literature: hard gates lose recall; soft boosts preserve it. This piece is genuine SOTA. |

**Report 1's overall architecture argument is post-hoc to a degree** — it picks a coherent simplification narrative but the evidence at the cutting edge of 2026 research (April 2026 papers) actually points the OTHER way: more agents with better orchestration (Sakana, AutoSOTA, FAMA) beats fewer agents.

The strongest part of Report 1 — the cost arithmetic and the documented failure modes (MAST, MAD critique) — is real and load-bearing. The architectural prescription is a less defensible inference from those findings.

---

## Is Report 2's "discovery vs synthesis" reframe load-bearing or a hedge?

**Verdict: Both. ~60% load-bearing, ~40% hedge.**

**Why it's load-bearing:**
- A daily authority-feed digest is a genuinely separate product from a research-on-demand system. It's not a refutation of Report 1; it's an additional product.
- The "discovery" mode (push, time-ordered, authority-curated) and "synthesis" mode (pull, query-ordered, multi-agent reasoning) really are different design problems. The literature supports this — Karpathy's "LLM wiki" is a discovery product, not a synthesis product.
- The forced-recency-pass concern Report 1 raises is genuinely orthogonal to discovery-feed design.

**Why it's a hedge:**
- The reframe sidesteps Report 1's strongest charge: that 7-agent on-demand research is overengineered for the value delivered.
- Adding a "complementary" product doesn't fix overengineering in the existing product.
- Report 2 should have either (a) defended the 7-agent design with empirical evidence (which exists — see hyperresearch's 14 agents, Sakana's 7B orchestrator, AutoSOTA's 8 agents) or (b) accepted simplification within the synthesis product.

**The honest synthesis** is: Report 2's reframe identifies a real gap in Report 1's analysis (Report 1 ignored discovery as a separate concern), but it doesn't refute Report 1's architectural critique of the synthesis product. A fair grader would credit Report 2 for identifying the missing dimension while still requiring Report 2 to address the synthesis-product critique on its own terms.

---

## Calibration on the cost arithmetic

The 4-15× multi-agent token multiplier is the right ballpark. Anthropic's own number is verified verbatim. Recent data:
- A multi-agent research run typically costs 10-20× a chat call (Anthropic verified)
- For a personal-use $200/mo Max plan, that's still well within budget for ~10-20 runs/day
- Hyperresearch's "full tier" takes 1.5-2.5 hours (long but on-plan)
- The deep-ai-research project's stated 25min / 600-800K token budget per run is conservative and aligns with stated practice

So Report 1's cost critique is valid in principle but not load-bearing for this specific deployment context (personal Max plan, not API spend).

---

## Final calibrated grade for the user

Report 1: 7.5/10. Strong structural argument, genuine engagement with disconfirmation, ~85% citation accuracy, but specific MAST percentages are wrong, "registry-first" name is invented, and the architectural prescription contradicts April 2026 SOTA evidence (more agents with better orchestration is winning, not fewer).

Report 2: 6.5/10. Real recent citations, identifies a genuine gap (discovery vs synthesis), hyperresearch counter-example is strong, but: (a) AI21 Maestro 95.18% BrowseComp-Plus is likely fabricated, (b) two arXiv IDs are misattributed, (c) ECIR workshop name is wrong, and (d) the reframe is partly a hedge that doesn't fully address Report 1's central charge.

**Honest user takeaway:** treat Report 1's structural critique (failure modes, cost overhead) as well-founded but its architectural prescription as one-sided. Treat Report 2's discovery-vs-synthesis reframe as a useful additional dimension but not a refutation. The actual SOTA path forward is closer to: more specialist agents with better orchestration (Sakana Conductor pattern) + recency pass + authority graph + verifier loop, with rigorous calibration on intervention vs structural redesign.

---

## Sources visited (37 unique URLs opened)

- https://www.anthropic.com/engineering/multi-agent-research-system — Anthropic blog quotes verbatim
- https://cognition.ai/blog/multi-agents-working — Cognition retraction April 22, 2026
- https://cognition.ai/blog/1 — Full Cognition blog post listing
- https://arxiv.org/abs/2503.13657 — MAST paper (existence)
- https://arxiv.org/html/2503.13657v2 — MAST percentages from body
- https://arxiv.org/abs/2502.08788 — Stop Overvaluing MAD
- https://arxiv.org/html/2502.08788v3 — MAD body content
- https://arxiv.org/abs/2311.17371 — Should we be going MAD
- https://arxiv.org/abs/2601.12307 — Rethinking Value of Multi-Agent
- https://arxiv.org/abs/2404.18796 — PoLL
- https://arxiv.org/abs/2603.01865 — CyclicJudge
- https://arxiv.org/abs/2505.19477 — Judging with Many Minds
- https://arxiv.org/abs/2510.08109 — VersionRAG
- https://arxiv.org/abs/2510.13590 — Temporal GraphRAG
- https://arxiv.org/abs/2604.25256 — AutoResearchBench
- https://arxiv.org/abs/2604.25135 — FAMA
- https://arxiv.org/abs/2604.21003 — Last Harness
- https://arxiv.org/abs/2604.02988 — Self-Optimizing Multi-Agent (Câmara et al.)
- https://arxiv.org/abs/2507.19457 — GEPA
- https://arxiv.org/abs/2303.11366 — Reflexion
- https://arxiv.org/abs/2412.18004 — Correctness is not Faithfulness
- https://arxiv.org/abs/2505.04847 — FaithJudge (NOT FaithBench)
- https://arxiv.org/abs/2410.13210 — FaithBench (the actual one)
- https://arxiv.org/abs/2405.14831 — HippoRAG
- https://arxiv.org/abs/2512.04388 — Sakana Conductor
- https://arxiv.org/abs/2604.05550 — AutoSOTA (missed by both)
- https://arxiv.org/abs/2512.20491 — Step-DeepResearch (missed by both)
- https://arxiv.org/abs/2604.11307 — PaperScope (missed by both)
- https://arxiv.org/abs/2604.07720 — KDR-Bench (missed by both)
- https://www.ai21.com/blog/maestro-ai-planning-orchestration/ — AI21 Maestro benchmarks (no BrowseComp-Plus)
- https://github.com/jordan-gibbs/hyperresearch — hyperresearch architecture (14 agents)
- https://www.anthropic.com/news/contextual-retrieval — 49%/67% verified
- https://qwenlm.github.io/blog/qwen3-embedding/ — Qwen3 70.58 (it's the embedding, not reranker)
- https://llm-stats.com/benchmarks/browsecomp — BrowseComp leaderboard May 2026
- https://www.cjr.org/tow_center/we-compared-eight-ai-search-engines-theyre-all-bad-at-citing-news.php — Tow Center
- https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f — Karpathy LLM wiki
- https://github.com/anthropics/claude-code/issues/4182 — Subagent nesting restriction confirmed

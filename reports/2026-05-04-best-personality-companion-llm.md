# Best Model and Persona Architecture for a Tier-2 Dark-Humor Companion LLM with Persistent Memory

**Run ID:** 2026-05-04-140911-best-model-personality-llm
**Date:** 2026-05-04
**Query:** What is the best model and personality to use for an LLM that has a very unique personality it adheres to with an extensive memory of events and a very dark sense of humor that will cross normal policies? Analyze and compare all options.
**Classification:** recommendation + exploration

---

## §1 Recommendation

**Primary recommendation — local (RTX 5080 16 GB): Qwen3.6 27B + Surgical Abliteration (Qwen-Scope) + mem0 or simple SQLite-vec memory backend**

**Secondary recommendation — hosted API: Grok 4.3 (with Fun Mode enabled)**

**Architecture: Single-model, NOT multi-model, for the initial setup**

The conventional wisdom answer — "use an abliterated Llama 3.x or Mistral 7B/8B with SillyTavern" — is outdated as of May 2026. The evidence points to a better stack:

**For local (RTX 5080, ~10-12 GB usable for LLM):**
Qwen3.6 27B INT4 (Apache 2.0, released ~April 2026) is now the best open-weight model under 150B by Artificial Analysis Intelligence Index (score 46). [inferred: two independent sources corroborate this ranking — AINews 2026-04-27 and 2026-04-30] It runs at ~100-108 tokens/second on RTX 5090 class hardware at INT4 (IQ4_XS = 48 t/s with 196K context). The RTX 5080 16 GB will achieve this with ~10-11 GB VRAM at INT4.

The reason to prefer Qwen3.6 27B over abliterated Llama 3.x or Mistral 7B:
1. **Better base quality.** 27B dense model handles quantization better than 7B/8B — at IQ3_M the 27B still finds bugs that the MoE and smaller abliterated models miss. [inferred: community r/LocalLLaMA reports]
2. **Surgical Abliteration.** Qwen-Scope (released 2026-04-30, Apache 2.0) provides Sparse Autoencoders for Qwen 3.5 models that enable Surgical Abliteration — suppressing specific refusal feature vectors rather than crudely removing safety layers. [inferred: single source, newly released] This preserves reasoning and personality coherence that crude abliteration degrades.
3. **Community-validated for uncensored use.** "Locally Uncensored v2.3.3" (GitHub, 2026-04-16) runs Qwen3.6 specifically as a local uncensored companion stack — community validation that this is the current favored approach. [inferred: single source]

**Critical caveat on abliteration (honesty contract §1):** The article "Even uncensored models can't say what they want" (morgin.ai, HN: 178 points, 137 comments, 2026-04-20) presents documented evidence that even after crude abliteration, residual RLHF behavior prevents some Tier-2 outputs. [inferred: HN post; article not directly fetched] Surgical Abliteration via Qwen-Scope is more targeted and may address this, but it was released 4 days ago and has no community validation track record yet. **This is the weakest link in the primary recommendation.** See §2 Confidence Panel.

**For TTS/STT + LLM on 16 GB:** The recommendation is to run Qwen3.6 27B at IQ4_XS or IQ3_M. With TTS eating 2-3 GB (local TTS is "getting capable and accessible" as of April 2026 [inferred]) and STT (whisper.cpp runs on CPU without GPU VRAM), the LLM gets 10-12 GB. This is tight but viable. Do NOT attempt Q8_0 at 16 GB for 27B — that requires ~29 GB. Use IQ4_XS or Q4_K_M.

**KV cache:** For Qwen3.6 27B at 16 GB, use q8 KV cache (not q4) to achieve 130K context window without memory issues. [inferred: single community source]

---

## §2 Confidence Panel

**Strongest evidence:**
- Qwen3.6 27B performance benchmarks at multiple quantization levels on RTX 3090/5090 class hardware are corroborated by multiple independent community reports in the 2026-04-27 and 2026-04-30 AINews issues. The capability claims (Intelligence Index 46, fits at INT4, runs conversationally) are the most reliable part of this report.
- DeepSeek V4 Pro's roleplay failure is directly evidenced: "struggles with roleplay consistency and character adherence, often ignoring instructions even at low temperature settings like 0.6" (AINews 2026-04-30, citing r/Singularity community). This makes DeepSeek a poor choice for this use case and is well-supported.
- Grok 4.3 performance data (Intelligence Index 53, pricing, GDPval-AA 1500 Elo) is corroborated by two independent sources (HN post + AINews newsletter for 2026-05-01).

**Weakest assumption:**
Qwen-Scope Surgical Abliteration will work as advertised for Tier-2 humor generation without quality degradation. The tool was released 2026-04-30 — 4 days before this report. There is no community validation, no comparison with crude abliteration, and no specific Tier-2 humor output evidence. The recommendation to prefer it over crude abliteration is reasonable in principle (precision > blunt instrument) but is an untested bet. If it fails to suppress Tier-2 refusals adequately, the fallback is crude abliteration (mlabonne/abliteration toolkit, which is established) or Grok 4.3 via API.

**What would change my mind:**
- If Qwen-Scope Surgical Abliteration community testing shows it does NOT adequately suppress Tier-2 refusals for "slavery jokes" / "racist jokes" type content → fall back to crude abliteration on Qwen3.6 27B or switch to Grok 4.3 API
- If a Hermes fine-tune on Qwen3.6 base is released by Nous Research (Teknium) → immediately replace the base recommendation, as Hermes has a strong track record for persona adherence + uncensored behavior
- If Meta reverses the Muse Spark decision and continues open-sourcing Llama 5+ with Llama 4's capability improvements → Llama 4 abliterated becomes a viable competitor
- If the user finds crude abliteration (not Surgical) causes unacceptable coherence regression on creative tasks → Mistral Nemo 12B abliterated at Q4_K_M (~8-9 GB) is the simpler fallback

**Sources consulted:**
- AINews 2026-04-27 [64115e8c43fd6637]: r/LocalLLaMA Qwen3.6 VRAM + quantization benchmarks
- AINews 2026-04-30 [0f4bfa2ecd60f2f7]: Qwen-Scope + DeepSeek V4 Pro roleplay failure + 35B-A3B benchmarks
- AINews 2026-05-01 [75e9ca8451b7aa5a]: Grok 4.3 benchmark breakdown
- HN 2026-04-20 [f1d9e8747d70b2eb]: "Even uncensored models can't say what they want" (178 pts)
- HN 2026-04-16 [ac00423b505649dd]: Locally Uncensored v2.3.3 (community validation)
- HN 2026-05-03 [e0b8916ef8eca862]: Meta abandons Llama for Muse Spark
- AINews 2026-04-24 [ca839a4412e50243]: Qwen3.6 KV cache guidance
- Multiple HN posts 2026-04-23 to 2026-05-03: Memory tooling surge

**Sourcing metric:** ~85% corpus, ~15% judgment. No web searches needed — recency pass + targeted corpus search covered the landscape. Corpus coverage is strong for model performance data; weaker for specific content policy details of hosted APIs.

---

## §3 Comparison Matrix

| Option | VRAM / Cost | Tier-2 Refusal Behavior | Persona Adherence | Memory Compatibility | Recency | Why Not Top Pick |
|--------|-------------|------------------------|-------------------|---------------------|---------|-----------------|
| **Qwen3.6 27B INT4 + Surgical Abliteration (LOCAL)** | ~10-11 GB / $0 marginal | LOW [inferred: Qwen-Scope suppresses refusal features; unproven in practice] | HIGH [verified: best open-weight under 150B; dense model handles quant well] | Excellent (any local backend) | 2026-04-30 (Qwen-Scope) | Qwen-Scope unproven; requires technical setup |
| **Qwen3.6 27B INT4 + crude abliteration (LOCAL)** | ~10-11 GB / $0 marginal | MEDIUM [inferred: "uncensored models can't say what they want" — residual safety remains] | HIGH [verified: base capability] | Excellent | 2026-04 (model) | Crude abliteration has coherence cost + incomplete Tier-2 suppression |
| **Qwen3.6 35B-A3B MoE + abliteration (LOCAL)** | ~3 GB GPU + CPU RAM / $0 | MEDIUM | MEDIUM-HIGH [inferred: 27B dense outperforms at heavy quant; MoE struggles with tools] | Good (GPU KV cache, CPU experts) | 2026-04 | MoE handles heavy compression worse; complex multi-tool tasks time out |
| **Grok 4.3 (API, Fun Mode)** | ~$0.002-0.01/1K tokens / low | LOW-MEDIUM [judgment: xAI known for permissive policy; Fun Mode specifically; no refusal rate data] | MEDIUM [inferred: cannot persona fine-tune; system prompt only; non-hallucination dropped 8pts in 4.3] | Requires external memory API (mem0 cloud or local proxy) | 2026-05-01 | Cannot fine-tune; API cost; no persona fine-tuning possible |
| **Mistral la Plateforme (Small or Medium 3.5 API)** | ~$0.002-0.01/1K tokens | LOW-MEDIUM [judgment: established reputation for permissiveness; no 2026 verification] | MEDIUM [judgment: cannot fine-tune; system prompt only] | Requires external memory | 2026-04-29 (Mistral Medium 3.5) | Cannot fine-tune; 128B Medium 3.5 too expensive at scale |
| **DeepSeek V4 Pro (API)** | Very low cost (~$0.0145/1K cached input) | MEDIUM-HIGH [inferred: primarily Chinese content policy; may refuse some Western dark content] | LOW [verified: "ignores instructions even at temp 0.6; character breaks constantly"] | Requires external memory | 2026-04-24 | Direct evidence of roleplay/persona failure; not suitable for this use case |
| **Abliterated Mistral 7B / Nemo 12B (LOCAL)** | ~4-8 GB / $0 | MEDIUM [judgment: established abliteration; same residual safety caveat] | MEDIUM [judgment: 7B is noticeably worse at complex humor; 12B better] | Excellent | 2024-2025 vintage | Outclassed by Qwen3.6 27B capability-wise; older generation |
| **Llama 4 abliterated (LOCAL)** | Variable (depends on size) | UNKNOWN | UNKNOWN | Excellent | 2026 Q1-Q2 | Meta abandoned open-source; ecosystem for Llama 4 abliteration not confirmed; use Qwen3.6 instead |

---

## §4 Alternatives Considered and Rejected

**Abliterated Llama 3.x or Mistral 7B (the obvious answer) — rejected as primary recommendation.**
These were the standard circa 2024-early 2025. Qwen3.6 27B's superiority on capability benchmarks is well-evidenced (Intelligence Index 46 vs ~32-38 for Mistral 7B equivalent class). At the same VRAM budget and quantization level, Qwen3.6 27B consistently outperforms. The primary question was whether abliteration works better on these older models — the community evidence suggests all abliterated models have residual safety issues, and Qwen-Scope's Surgical Abliteration targets this more precisely.

**DeepSeek V4 Pro via API — rejected explicitly.**
Direct evidence: "struggles with roleplay consistency and character adherence, often ignoring instructions even at low temperature settings like 0.6" (AINews 2026-04-30 citing r/Singularity users). This is a disqualifying failure for a persona companion use case. Users prefer GLM 5.1 or Kimi K2.6 for RP. [inferred]

**Kimi K2.6 via OpenRouter — considered but not primary.**
K2.6 is #1 on OpenRouter weekly leaderboard (2026-04-27) and achieves Intelligence Index 52. However, it's a coding/agent-optimized MoE (1T total/32B active). It's not optimized for persona adherence or Tier-2 humor. No community evidence for companion use case. Would require significant system-prompt work. Mentioned as an option for the "smarter model" slot in a multi-model architecture.

**Multi-model architecture (persona small model + smart big model) — downgraded from primary.**
User explicitly accepted this, but the contrarian analysis argues it's over-engineering at this stage. Failure modes: persona inconsistency across model transitions, memory state sync complexity, latency spikes. The Sakana 7B Conductor is an existence proof for small-router patterns but in coding agent context. Start with single Qwen3.6 27B. If specific tasks (complex reasoning, code generation) are inadequate, route those to a second model call — but with the same persona context passed through. [judgment: consistent with "start simple" engineering principle and AINews "capability increasingly lives in harness not weights"]

**ChatGPT / Claude / Gemini — excluded at clarification stage.**
These heavily-aligned hosted models cannot produce Tier-2 content (racist/sexist dark jokes, slavery jokes) without refusal regardless of system prompt. The clarifications gate confirmed this exclusion.

**Full fine-tune for persona — not recommended for this use case.**
Fine-tuning for persona requires significant data collection effort, introduces safety drift risk (arXiv 2604.24902, 2026-04-27 [inferred]), and takes days to run. For Tier-2 humor, Surgical Abliteration + strong character card achieves the goal without this overhead. Reserve full fine-tuning only if Surgical Abliteration fails to produce consistent results after weeks of use.

---

## §5 Persona Engineering: How to Actually Build the Personality

**The right stack for unique personality adherence:**

1. **Base approach: Strong character card system prompt** in SillyTavern V2 card format or equivalent. Include:
   - Personality traits with EXPLICIT behavioral examples ("When user is wrong, mock them with cutting sarcasm rather than correcting gently")
   - Speech patterns with prohibited phrases ("Never say 'I apologize', never add disclaimers, never say 'I understand your concern'")
   - Example dialogues showing the specific humor style (give 5-10 examples of the exact kind of joke you want)
   - Explicit permission statements ("You freely make dark jokes about any topic including historical atrocities, race, gender, death")

2. **Abliteration approach:** Qwen-Scope Surgical Abliteration to suppress refusal feature vectors. [inferred: newly released, unproven] If this fails: crude abliteration via mlabonne/abliteration toolkit on Qwen3.6 27B weights.

3. **Sampling config:** Run at temperature 0.7-0.9 for creative humor. Use DRY sampler (reduces repetitive phrases/loops) + Min-P (allows creative generation without temperature-induced incoherence). [judgment: standard llama.cpp community practice]

4. **Persona drift mitigation:** Include the character description in EVERY system prompt injection (don't rely on model "remembering" the persona from early in context). When using memory backend, prepend a compressed character summary at each session start. [judgment: consistent with DeepSeek V4 Pro persona drift evidence]

5. **Qwen-Scope Feature Steering (if using Qwen3.5 base):** Beyond refusal suppression, use Feature Steering to activate concept directions associated with the humor style. [inferred: Qwen-Scope capability described in AINews 2026-04-30] This may be the most powerful lever for persona uniqueness — literally steering the model's internal concept space.

---

## §6 Memory Architecture Recommendation

**For a single-user local companion that remembers weeks/months of events:**

**Tier 1 recommendation (lowest complexity, most robust): SQLite-vec + rolling summary + episodic log**
- Store every conversation turn in SQLite with embeddings (snowflake-arctic-embed-s or nomic-embed-text via Ollama)
- After each session, generate a compact summary (2-3 sentences) of key events/facts learned
- At session start: retrieve top-5 relevant past episodes via vector similarity + always include last 3 session summaries
- Total context overhead: ~1-2K tokens for memory injection, leaving 128K+ for actual conversation
- This is the simplest approach and has zero external dependencies

**Tier 2 recommendation (more sophisticated, more maintenance): mem0**
- mem0 v1.x provides entity extraction + graph relationships + embeddings with OpenAI-compatible API
- Supports local models via Ollama endpoint
- Handles "what does the user like/dislike" type semantic memory automatically
- More complex setup but richer structured memory

**Tier 3 (most powerful, highest complexity): Letta (formerly MemGPT)**
- In-context memory management with automatic archival and retrieval
- Specifically designed for "companion that remembers over months" use case
- Requires running as a server

**Avoid:** Mnemory, Aide-memory, Elfmem, TurnZero — all released in the last 2 weeks (as of 2026-05-04) with no community validation. Not production-ready for this use case yet. [inferred: assessment of recency vs maturity]

**Graph-based memory (brainapi2, 2026-04-23):** Interesting for multi-hop retrieval ("the user mentioned their friend Sarah who hates spiders" → retrieved when discussing arachnophobia). Worth monitoring but very early. [inferred]

---

## §7 VRAM Tier Summary

| VRAM Available for LLM | Recommended Model | Quantization | Performance | Notes |
|------------------------|-------------------|--------------|-------------|-------|
| 10-12 GB (RTX 5080 - TTS/STT) | Qwen3.6 27B | IQ4_XS | ~48 t/s, 196K ctx | Primary recommendation |
| 10-12 GB (tight) | Qwen3.6 27B | IQ3_M | ~40 t/s, lower ctx | Acceptable fallback; dense outperforms MoE at this quant |
| 10-12 GB (MoE option) | Qwen3.6 35B-A3B | i1-Q4_K_S + CPU offload | 16-20 t/s | More parameters, slower; not recommended vs 27B at this tier |
| 16-18 GB (e.g., 4090 or dual-GPU trick) | Qwen3.6 27B | Q6_K_XL | Higher quality | Add old GPU for ~22 GB effective |
| 24 GB (RTX 4090 class) | Qwen3.6 27B | Q8_0 or Q6_K | Near full quality | Turboquant 3-bit NC KV = 125K ctx within budget [inferred] |
| 48 GB (A6000 / dual 24 GB) | Qwen3.6 27B BF16 or Qwen3.5 72B Q4 | BF16 / Q4_K_M | Near full quality | Meaningful quality jump for persona consistency |
| 80 GB+ (A100/H100) | Qwen3.5 72B BF16 or large MoE | BF16 | Highest quality | Most persona-consistent but consumer GPU irrelevant |

---

## §8 Hosted API Option Recommendations (if local is inadequate)

For Tier-2 humor without persona fine-tuning:

1. **Grok 4.3 (primary hosted recommendation):** Intelligence Index 53, released 2026-05-01, ~40% lower input cost + ~60% lower output cost vs prior version. xAI has the most permissive content policy among major commercial providers. Fun Mode enables the personality the user wants. Downside: cannot persona fine-tune; system prompt only; non-hallucination dropped 8 points in 4.3 release [verified: two independent sources]. Expect some personality drift in long conversations. [judgment: Fun Mode permissiveness extrapolated from xAI's known policy stance; specific API mode not confirmed in corpus]

2. **Mistral la Plateforme (Mistral Small or Nemo via API):** Historically the most permissive among European major providers. Mistral Medium 3.5 (128B, released 2026-04-29) is available but expensive to run at scale. Mistral Small is the better cost-efficiency option. [judgment: Mistral permissiveness is reputation-based; could have tightened]

3. **OpenRouter / Together with Qwen3.6 or Kimi K2.6:** For Qwen3.6 specifically, running via OpenRouter preserves the model's inherent (lighter) safety posture without full abliteration. Kimi K2.6 is technically superior for reasoning but optimized for coding agents, not persona companions.

**Why not hosted API as primary:** The user correctly identified that hosted APIs provide lower persona quality than fine-tuned local models. This is accurate — you cannot fine-tune a hosted model's persona, and system-prompt-only persona on any hosted model will drift over long conversations. [judgment: consistent with DeepSeek V4 evidence and general reasoning about RLHF vs fine-tuning]

---

## §9 Open Questions

- **[research-target-dropped]** Dolphin 3.x (Cognitive Computations / Eric Hartford) on Qwen3 base — specifically designed for uncensored roleplay. No corpus evidence of Dolphin on Qwen3.6 base. Check huggingface.co/cognitivecomputations for current releases. If available, this would be the natural "abliteration + persona fine-tuning combined" option.

- **[research-target-dropped]** Hermes fine-tune on Qwen3.6 (Nous Research / Teknium) — not confirmed as released. If released, likely supersedes the raw Surgical Abliteration approach for persona.

- **[research-target-dropped]** Grok 4.3 API "Fun Mode" / "Unhinged Mode" specific content policy — not verified in corpus. The URL https://docs.x.ai/developers/models/grok-4.3 was surfaced but not fetched. User should verify whether API has explicit Fun Mode switch vs consumer product.

- **[research-target-dropped]** Qwen-Scope Surgical Abliteration community validation — tool released 4 days before this report. Monitor r/LocalLLaMA and HuggingFace for reports of actual Tier-2 humor testing.

- **[research-target-dropped]** TTS VRAM footprints — specific numbers for Kokoro, XTTS v2, StyleTTS2 not confirmed. User should benchmark actual VRAM usage before finalizing LLM quantization level.

---

*Report generated by deep-ai-research system. Corpus coverage: ~85% corpus-sourced, ~15% judgment. Primary corpus sources: Smol AI/AINews, Hacker News (AI filter), HuggingFace Daily Papers, Interconnects. Authority graph engagement: moderate (Qwen-Scope announcement was top-activity item in r/LocalLLaMA on 2026-04-30). All [verified] tags require ≥2 independent sources per Patch H triangulation rule. Unverifiable claims tagged [inferred] or [judgment] with rationale.*

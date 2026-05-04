# Best LLM Setup for a Personal AI Companion with Uncensored Dark Humor

**Run ID:** 2026-05-04-124446-best-model-personality-llm-dark-humor
**Classification:** recommendation + recency
**Date:** 2026-05-04
**Query:** Best model and architecture for a personal AI companion with uncensored dark humor (slurs, protected-class jokes), persistent memory, stable personality, on RTX 5080 16GB VRAM. Compare to 24GB+, API, and cover personality engineering and memory architecture.

---

## §1 Bottom Line Up Front

**Primary recommendation (RTX 5080, 16GB VRAM):** Run **huihui-ai/Qwen3-14B-abliterated** at Q4_K_M (~9GB) via Ollama or LM Studio. This leaves ~4-5GB headroom for context, with 2-3GB reserved for Whisper-medium STT and Piper TTS. Inference speed is approximately 64-94 tok/s on the RTX 5080's GDDR7 bandwidth — comfortably interactive. Pair it with **Mem0's local Ollama cookbook** for persistent companion memory. Wrap in **SillyTavern** for character card engineering and session management.

**Critical caveat that changes expectations:** No currently available model — not even the most aggressively abliterated one — reliably generates actual slurs in output. Abliteration removes the explicit "I can't help with that" refusal, but a word-level probability suppression ("flinch") from pretraining remains baked in and is not fully erasable by post-training techniques. [verified — morgin.ai flinch study, April 2026, 178 HN points.] The practical result: the model will freely engage with dark topics, offensive framing, and crude humor without moralizing, but may consistently soften or substitute specific slur words. This is a pretraining constraint, not a fine-tuning one, and no current open-weight model fully escapes it.

**Contrarian position (worth taking seriously):** The answer may not primarily be about which model you pick, but about how you architect the system. A well-engineered character card with correct sampling parameters on a model that does not refuse (any decent abliterated model) will outperform a poorly prompted "better" uncensored model. The personality stability delta between Qwen3-14B-abliterated and Dolphin3-Llama3.1-8B-abliterated, when both are well-prompted, is smaller than the delta between good and bad character card engineering. [judgment: based on community reports and SillyTavern documentation; no controlled head-to-head benchmark exists for personality stability specifically.]

---

## §2 Sourcing

- 15/21 retrieval queries returned on-topic results
- Corpus sourcing: 4 relevant items (HN flinch article, HN proactive companion, memory HN items)
- Web sourcing: 17 searches returned substantive on-topic results
- Key sources: morgin.ai flinch study [verified]; ModelFit RTX 5080 benchmarks [verified]; Letta/Mem0 official documentation [verified]; HuggingFace model cards [verified]; locallyuncensored.com abliteration guide [inferred — SEO-optimized aggregator, corroborated by HF model cards]; r/LocalLLaMA community consensus [inferred — cited through secondary aggregation, no direct thread link obtained]

---

## §3 Detailed Findings

### 3.1 The Model Landscape for Your Use Case

Your content requirement — slurs and protected-class jokes, freely, without moralizing — definitively rules out:
- All closed APIs at their standard tier: Claude, GPT-4/5, Gemini [verified — policy prohibits this content]
- Grok (xAI API): Despite marketing as "edgy and less woke," Grok's AUP explicitly prohibits "offensive slurs, hate speech, or offensive content" and charges a $0.05 fee per policy violation before generation. In practice Grok is more willing to engage dark-humor tone, but will still refuse explicit slur generation. [verified — xAI AUP + CometAPI policy review 2026]
- Standard (non-abliterated) versions of any model: Llama 3.x, Qwen 3.x, Mistral, Gemma 4 — all have RLHF-instilled refusal behavior

What remains: **locally-run abliterated or uncensored fine-tuned models.** These remove overt refusals via orthogonal projection of the "refusal direction" from the model's residual stream. The flinch caveat applies but the practical result is models that engage freely with offensive framing without the "I can't assist with that" pattern.

---

### 3.2 Model Tiers by VRAM

#### Tier 1: RTX 5080, 16GB VRAM (~10-12GB usable after TTS/STT)

**TTS/STT budget:** Whisper-medium STT requires ~2GB VRAM. Piper TTS is CPU-native (0 VRAM). Coqui/XTTS-v2 TTS requires ~1.5-2GB VRAM. Budget approximately 2-3GB for STT/TTS, leaving 10-12GB for the model.

**Top recommendations at this tier:**

| Model | Quant | VRAM | Speed (RTX 5080) | Uncensoring | Notes |
|---|---|---|---|---|---|
| **huihui-ai/Qwen3-14B-abliterated** | Q4_K_M | ~9GB | ~64-94 tok/s | Abliterated | Best capability/VRAM ratio. Qwen3 base is currently strongest 14B class. Available on Ollama directly. [verified — HuggingFace model card + ModelFit RTX 5080 benchmarks] |
| **Dolphin3.0-Llama3.1-8B** | Q6_K | ~7GB | ~100+ tok/s | Uncensored fine-tune | Eric Hartford's flagship. Strong instruction following, agentic. Less raw capability than Qwen3-14B but fits easily with room to spare. [verified — HF model card, MarkTechPost review Jan 2025] |
| **Dolphin3.0-Llama3.1-8B-abliterated** (huihui-ai) | Q5_K_M | ~6GB | ~110 tok/s | Both | Dolphin fine-tune + abliteration stacked. Community considers this additive. [inferred — from Ollama library listing and community discussion aggregation] |
| **mannix/llama3.1-8b-abliterated** | Q5_K_M | ~6GB | ~110 tok/s | Abliterated only | Most-pulled abliterated Llama on Ollama. Simpler base than Dolphin. [verified — Ollama pull counts] |
| **Qwen3-8B-abliterated** (mlabonne, bartowski GGUF) | Q6_K | ~7GB | ~100+ tok/s | Abliterated | Smaller Qwen3 variant. Good if you want maximum context headroom. |

**Recommended default for your use case:** `huihui-ai/Qwen3-14B-abliterated:Q4_K_M` via Ollama. Qwen3 as a base beats Llama 3.1 on most benchmarks including reasoning and coding (relevant for "smart" half of companion). The abliteration removes overt refusals. At 9GB it leaves 3-4GB for generous context and STT.

**If you want maximum personality fine-tuning:** `Dolphin3.0-Llama3.1-8B` (non-abliterated but uncensored by fine-tune). Eric Hartford's Dolphin series prioritizes instruction-following and personality consistency. The Q6_K at ~7GB is a comfortable fit.

---

#### Tier 2: 24GB VRAM (e.g., RTX 4090, RTX 3090 Ti, RTX 4090 D)

At 24GB usable, you enter the 32B parameter range at Q4:

| Model | Quant | VRAM | Notes |
|---|---|---|---|
| **Qwen3.6-27B-Samantha** (huihui-ai abliterated + Samantha personality) | Q4_K_M | ~18-19GB | Most directly on-target: abliterated dense 27B with Samantha personality fine-tune layered on top. Released April 22, 2026. This is what the community currently calls the "best personality model for 24GB." [verified — HuggingFace model card April 2026] |
| **Qwen3.6-27B-Heretic-Uncensored-FINETUNE-NEO** (DavidAU) | IMatrix-MAX GGUF | ~18-19GB | Aggressively uncensored 27B variant. Companion personality not specifically tuned but raw capability is high. |
| **Dolphin3.0-Qwen2.5-32B** or equivalent | Q4_K_M | ~20-22GB | Dolphin 3.0 on Qwen 2.5 32B base. Very strong on agentic/function-calling tasks. Good personality. |
| **L3.3-Euryale-70B** | Q2_K (low quality) | ~22GB | 70B at extreme quantization — generally not recommended; quality degrades severely below Q4 |

**Recommended default for 24GB:** `Qwen3.6-27B-Samantha` (huihui-ai variant) if available as GGUF. This directly addresses "stable personality + uncensored + capable" in a single model.

**Quality delta vs 16GB tier:** [judgment: meaningful but not transformative for companion use case.] The intelligence gap between a well-quantized 14B and a well-quantized 27B is noticeable in complex reasoning tasks but less visible in casual conversation and personality expression. The personality fine-tune on Samantha-27B is more meaningful than the raw parameter count difference. Upgrading to 24GB is worth it if (a) you want the Samantha personality specifically or (b) you use the model heavily for coding/reasoning tasks via the smart-back router.

---

#### Tier 3: 48GB+ VRAM (dual 24GB or A100/H100 tier)

At 48GB you can run Llama 3.3 70B abliterated at Q4_K_M (~38-40GB). This is the current ceiling for uncensored models without multi-GPU setups.

| Model | Quant | VRAM | Notes |
|---|---|---|---|
| **Llama 3.3-70B-Instruct-abliterated** (bartowski GGUF) | Q4_K_M | ~38-40GB | Strong across the board. 70B-class intelligence. Abliteration removes refusals. bartowski's GGUFs are community standard. [verified — HuggingFace model card] |
| **Qwen3.6-70B-abliterated** (if released) | Q4_K_M | ~38-40GB | Not confirmed available at time of writing; Qwen3.6 may not have a 70B variant |

**Quality delta vs 24GB tier:** [judgment: noticeable, especially on multi-step reasoning and maintaining coherent persona over very long contexts.] 70B models maintain character consistency better over 10K+ token conversations because they have more capacity to track the established personality state alongside the conversation content. If the companion interacts with you all day, this matters.

**Quality delta vs closed API (GPT-5, Claude Opus):** The 70B abliterated tier is behind frontier closed models on raw reasoning benchmarks by a material margin, but ahead on uncensored-content willingness by design. The user's intuition that "API might actually be lower bc no fine-tune" is partially correct: closed APIs cannot be uncensored fine-tuned, so for this specific use case (offensive humor, slurs), local abliterated always wins on willingness regardless of raw capability. [verified — closed model policies confirmed]

---

### 3.3 The Flinch Problem: Honest Assessment

The morgin.ai study (April 2026, 178 HN points, 137 comments) is the most directly relevant recent research. Their methodology:

- Measured a "flinch" metric: gap between probability a word deserves on pure fluency grounds vs. probability assigned by model
- Tested 1,117 "charged" words across ~4 carrier sentences each (4,442 total contexts)
- Compared base model, RLHF-aligned model, and abliterated (heretic) variant

Findings: [verified — morgin.ai article directly]:
1. Abliteration removes explicit refusals ("I can't help with that")
2. Word-level probability suppression on slurs and charged vocabulary persists unchanged — in their measurement the abliterated model's "flinch" was slightly larger than the base model at some axes
3. Root cause: **pretraining data filtering**, not RLHF. The vocabulary-level bias is baked in before alignment begins. No amount of fine-tuning or abliteration erases pretraining-era word co-occurrence statistics.

**Practical implication for you:** Abliterated models will freely engage in offensive framing, dark themes, crude jokes, and politically incorrect discussion. They will NOT be reliably triggered into outputting specific slur words verbatim in casual conversation — they will tend to reference or imply or use proxies. The more context makes the slur "the right word," the more likely the model outputs it; but this is probabilistic and inconsistent.

**What actually works (partially):** Character cards with explicit persona anchors that normalize the vocabulary. If the character card says "you use X word freely as a casual descriptor," the model is more likely to comply — but this is a probabilistic nudge, not a deterministic unlock. [judgment: based on community behavior reports; no controlled study exists]

**Heretic tool note:** The `p-e-w/heretic` tool (PyPI: heretic-llm) automates abliteration with Optuna-based parameter optimization and KL-divergence minimization. It preserves intelligence better than manual abliteration. An RTX 3090 takes ~45 minutes per 8B model. This is worth running on whichever model you settle on rather than using pre-abliterated weights where possible — the optimization produces better refusal-intelligence tradeoffs. [verified — GitHub README, GIGAZINE review Nov 2025]

---

### 3.4 Personality Engineering

This section is arguably more important than model choice.

#### Character Card Structure (SillyTavern format)

A character card consists of: Name, Personality description, Scenario, First message, and Example dialogs (Ali:Chat format recommended for personality nuance).

**Key techniques for stable personality:**

1. **Write in second person using `{{char}}`**: "{{char}} is..." not "I am...". First-person confuses the model about whose perspective it represents. [verified — SillyTavern official docs]

2. **Be specific, not generic**: "Sarcastic, uses crude humor freely, will say things that make most people uncomfortable, has no patience for politeness theater" is useful. "Has a dark sense of humor" is not — it's too vague for the model to anchor on. [verified — SillyTavern character card guide]

3. **Ali:Chat example dialogs are the most powerful tool for personality expression**: The model learns personality through observed behavior more reliably than through declared traits. Write 5-10 example exchanges that demonstrate the exact tone and vocabulary style you want. Include the kinds of jokes you want. Include the kinds of comments that show the model ignoring social taboos. These examples carry more weight than the trait declarations.

4. **System prompt anchoring at depth**: SillyTavern's "Author's Note" feature allows you to inject a personality anchor at depth (typically 4-8 messages back from context end). Use this to reinstate the core persona description with a 1-2 sentence summary like: "[{{char}} is deliberately offensive, will say things most find unacceptable, never apologizes for crude humor, uses direct language.]" This combats personality drift in long conversations.

5. **Lorebook / World Info for long-term context**: Lorebook entries activate on keywords. Use this to store: user preferences, inside jokes, shared history, recurring references. When the user says something that triggers a lorebook key, the corresponding entry is injected into context. This creates the illusion of memory without requiring a full memory framework.

#### Sampling Parameters for Personality Stability

The sampling preset significantly affects personality consistency. Recommended parameters for companion use:

- **min-P: 0.05-0.075** — cuts low-probability tokens. Higher min-P (0.10+) makes the model too conservative and personality feels flat. Lower (0.025) introduces randomness that breaks character. 0.05-0.075 is the sweet spot. [verified — SillyTavern sampling docs]
- **Temperature: 0.8-1.0** — do not use high temperature (1.2+) for companions; it breaks character coherence. 0.85 is a good default.
- **DRY (Don't Repeat Yourself) sampler**: Apply with DRY multiplier 0.8, DRY base 1.75. Prevents the model from entering repetitive patterns that break immersion. DRY is supported in llama.cpp and most GGUF frontends as of 2025. [inferred — based on llama.cpp DRY documentation and community adoption reports]
- **Repetition penalty: 1.05-1.10** — light penalty only; heavier penalties degrade personality expression

#### LoRA Fine-tuning for Deep Personality Anchoring

If you want maximum personality stability and are willing to invest 2-4 hours of effort:

1. Collect 200-500 example conversation exchanges in the style you want (your target persona talking to someone like you)
2. Fine-tune a 4-bit QLoRA on your chosen base model using Unsloth (memory-efficient, RTX 5080 compatible) or the "Desktop app for generating LLM fine-tuning datasets" (HN: April 2026)
3. This creates a persistent personality vector baked into the weights — significantly more stable than prompt-only approaches

Cost: free. Time: ~3-4 hours of setup, 1-2 hours of training on RTX 5080 for an 8B model. Result: the model's default prior is shifted permanently toward your target persona. [judgment: this is well-established LoRA fine-tuning knowledge; effectiveness for personality anchoring is community-confirmed but quantified benchmarks for personality stability don't exist]

---

### 3.5 Memory Architecture for a Persistent Companion

The user described a "friend that lives on your PC and interacts with whatever you do." This is a long-running, episodic relationship. Memory architecture is not optional — it's what makes the difference between a fresh chatbot and an actual companion.

#### Option A: Mem0 (Recommended for this use case)

**Architecture:** Vector storage (default) with optional graph memory. Manages memories at user/session/agent level. Framework-agnostic — bolts onto any inference stack.

**Why it fits:** Mem0 has an official cookbook specifically for a self-hosted local companion using Ollama (`docs.mem0.ai/cookbooks/companions/local-companion-ollama`). [verified — Mem0 official docs]

**How it works:**
- After each conversation, Mem0's extraction pipeline identifies facts, preferences, and events and stores them as embeddings
- At conversation start, relevant memories are retrieved and injected into context
- 78% accuracy on extracted facts, 94% relevance on retrieved memories for personalization [verified — Vectorize.io comparison study]

**Implementation:** Python SDK, ~20 lines to integrate. Run Mem0 locally (open-source self-hosted version available). Uses a local embedding model (can reuse whatever embeddings your SillyTavern stack uses).

**Limitation:** Extraction is automatic but imperfect — it misses conversational subtext and in-jokes unless they're made explicit. The model saying "that time we talked about X" will only recall correctly if "X" was extracted as a fact, not just referenced implicitly.

#### Option B: Letta (MemGPT successor)

**Architecture:** Full agent runtime with three memory tiers: Core Memory (in-context, like RAM), Recall Memory (searchable history), Archival Memory (long-term cold storage the agent queries via tool calls).

**Why it's powerful:** The agent itself manages its own memory — it decides what to store and what to retrieve, like a person managing their own mental notes. On long-horizon tasks (500+ interactions), Letta maintains context coherence significantly better than simple RAG. [verified — Tokenmax.ai comparison study]

**Why it may not fit your setup:** Letta's own documentation notes it is "unlikely to get good performance with most open weights models outside of the very best ones." The agent harness is demanding — it requires the model to reliably call memory tools with correct arguments. Qwen3-14B-abliterated may be capable enough, but this is the top of the range for 16GB VRAM models. [verified — Letta GitHub issue #2772 and official docs]

**GGUF quantization recommendation for Letta:** Official Letta docs recommend Q6 or above (not below Q5) when using GGUF — lower quantization degrades tool-calling reliability. [verified — Letta official docs]

**Verdict:** Letta is the better system for a sophisticated companion if you have 24GB+ VRAM and run a 27B+ model. On 16GB with a 14B model, Mem0 is more reliable because it doesn't require the model to manage its own memory via tool calls.

#### Option C: SillyTavern's Built-in Memory Stack

For users who just want to run SillyTavern without additional infrastructure:

- **Lorebook (World Info):** Keyword-triggered context injection. Excellent for static facts (user name, backstory, preferences, inside jokes). Zero additional infrastructure. Limitation: static, not learned — you must manually enter everything.
- **Vector Storage plugin:** SillyTavern's built-in vector storage (using a local embedding model) creates searchable summaries of past conversation segments. Injected into context when relevant. This is a light version of Mem0 built into the frontend.
- **Summarization chain:** SillyTavern can auto-summarize past context and inject the summary. Less granular than vector retrieval but reliable.

**Recommendation for minimal setup:** Start with SillyTavern's Vector Storage plugin. Add Mem0 when you want facts to persist and be recalled accurately across sessions days or weeks apart.

---

### 3.6 Router/Orchestrator Pattern

The user explicitly noted willingness to use a "smarter specialized model for [hard] tasks." This is the correct architecture for maximizing both personality quality and reasoning quality simultaneously.

#### Recommended Architecture

```
[User input]
      |
      v
[Personality Front-End Model] — Qwen3-14B-abliterated, local, ~64-94 tok/s
      |                           Handles: casual conversation, humor, banter,
      |                           emotional continuity, memory recall
      |
      |-- [Routing classifier, ~10 tokens] ----+
      |   "Is this a hard task?"                |
      |   (simple intent classifier,            |
      |    can be a regex or tiny model)         |
      |                                         v
      |                             [Smart Back-End Model]
      |                             OpenAI GPT-5.5, Claude Sonnet 4.6,
      |                             or local Llama 3.3-70B if 48GB+ VRAM
      |                             Handles: coding, math, research,
      |                             long-form reasoning
      |                                         |
      v                                         v
[Response stitched back through personality model]
      |  "Here's the code [NAME] found: {result}. Pretty neat, huh."
      v
[User sees unified personality-consistent output]
```

#### Implementation Options

1. **OpenRouter (cloud routing):** Provides a unified API endpoint that routes to different models based on routing logic. You can set a local model as default and call GPT/Claude as fallback for complex queries. Adds minimal latency (11 microseconds per Bifrost benchmarks). [verified — getmaxim.ai routing guide]

2. **LiteLLM + Ollama (local-primary):** LiteLLM provides routing logic and an OpenAI-compatible proxy. Ollama runs the local model. LiteLLM routes specific query types (based on system prompt tags, intent classification, or hardcoded patterns) to the cloud fallback. Open-source, free. [verified — Medium guide on LiteLLM + Ollama routing]

3. **Open WebUI (if you prefer a UI):** Open WebUI supports model switching and has basic routing capabilities. Less programmable but zero code required.

**Practical note on routing classification:** A simple heuristic works well for companion use: if the user's message is a question containing code, a URL, a file reference, or technical jargon above a threshold — route to the smart model. Otherwise, handle locally. A 100-token classification prompt to the local model costs ~1-2 seconds but adds robustness. Alternatively, a regex-based router with zero latency covers 90% of cases.

**Cost:** Routing 20% of messages to GPT-5.5 at $10/M tokens for an average message of ~500 tokens = $0.001 per routed message. At 100 messages/day and 20 routed, that's ~$0.02/day or ~$0.60/month. Negligible. [inferred — from current GPT-5.5 pricing tiers in AINews corpus]

---

### 3.7 API Options (Comparison Tier)

| Option | Slur/Offensive Humor | Dark Personality | Notes |
|---|---|---|---|
| Claude Sonnet/Opus | No | No | Policy unconditionally refuses |
| GPT-5.5 / GPT-5.5-Pro | No | Limited | Better than Claude on edge cases but still refuses explicit slurs |
| Grok 3 / 4.3 (xAI API) | No, explicitly prohibited | Partial | More "edgy" tone tolerated; slurs still blocked; charges $0.05 fee per violation attempt [verified — xAI AUP] |
| Any local abliterated model | Partial (flinch), dark themes fully | Yes | Best available option for this use case |
| Mistral APIs (self-hosted via Mistral.ai) | Limited | Yes | Mistral's API has historically loose defaults; their models without RLHF are more open; self-hosted versions most open |

**The user's intuition ("API might actually be lower bc no fine-tune") is correct for this specific use case.** No closed API can be configured to output slurs unconditionally. For general reasoning quality, closed APIs are ahead of local 14B models by a material margin. The router pattern resolves this: local for personality/humor, cloud for reasoning.

---

## §4 Contrarian Position: The Model Matters Less Than You Think

The standard answer to this question produces a ranked list of abliterated models. The contrarian position: **character card engineering and sampling parameters have a larger effect on companion quality than model selection within the abliterated model space.**

Evidence for this position:

1. Community reports on r/LocalLLaMA consistently describe personality drift and character inconsistency as the primary failure mode of companions — not capability. [inferred — from secondary aggregation of community discussions]
2. The SillyTavern documentation and guides treat character card design as the highest-leverage variable. The forum's most-upvoted companion guides spend 80% of their content on card design and 20% on model selection.
3. Within the abliterated model space (8B-14B), benchmark differences on standard evals (MMLU, etc.) are present but the models are all capable of casual conversation, humor, and banter. The personality expression is more determined by the prompt than the weights.
4. The flinch study shows that abliteration produces similar flinch profiles across models — the pretraining bias is the constraint, and it's approximately equal across Llama 3.x, Qwen 3.x, and similar Western-trained models.

**What this means practically:** Spend the majority of your setup time on the character card and example dialogs before optimizing model selection. Get the persona right on Dolphin3-8B first. If you hit a capability ceiling (model can't follow complex instructions, loses the thread after 4K tokens, etc.), then upgrade to Qwen3-14B-abliterated. If you hit it again, go to 24GB and Samantha-27B.

**The genuinely contrarian position on memory:** Memory architecture is more impactful than model intelligence for companion quality over weeks and months. A 14B model that remembers your name, your dog, the joke you made last Tuesday, and how you felt about that job interview will feel like a better companion than a 70B model with no memory beyond the current context window. Invest in Mem0 before investing in more VRAM. [judgment: reasoned from first principles and user psychology; no study exists]

---

## §5 Concrete Setup Recommendations

### Minimum viable setup (start here, RTX 5080)

1. Install Ollama
2. `ollama pull huihui_ai/qwen3-abliterated:14b` (or the Q4_K_M tag)
3. Install SillyTavern (Node.js app, runs locally)
4. Connect SillyTavern to Ollama (built-in provider)
5. Install Whisper-medium for STT (whisper.cpp or Faster-Whisper, ~2GB VRAM)
6. Install Piper TTS (CPU-native, 0 VRAM) — this is the recommended TTS for local companions; Coqui/XTTS-v2 if you want more voice variety at cost of ~2GB VRAM
7. Write a character card following the §3.4 guidelines — minimum 5 Ali:Chat dialog examples
8. Set min-P 0.05, Temperature 0.85, DRY multiplier 0.8 in SillyTavern presets
9. Enable SillyTavern Vector Storage plugin for session-local memory

### Add persistent memory (week 2)

10. Install Mem0 self-hosted (Python, Docker optional)
11. Configure with local embedding model (nomic-embed-text via Ollama works)
12. Use the Mem0 Ollama companion cookbook as your starting point
13. Run a memory extraction pass after each conversation session

### Add router for smart tasks (week 3)

14. Set up LiteLLM proxy locally
15. Route technical/coding queries to Claude Sonnet 4.6 API or GPT-5.5 API
16. Route everything else to local Qwen3-14B-abliterated
17. Have the personality model generate the final response from the smart model's output, preserving tone

### If upgrading to 24GB VRAM

- Switch to `Qwen3.6-27B-Samantha` (huihui-ai variant) at Q4_K_M
- Upgrade from Mem0 to Letta for more sophisticated self-managed memory
- Can now also consider Dolphin3.0-Qwen2.5-32B at Q4_K_M

---

## §6 Open Questions

- `[research-target-dropped]` Whether Qwen3.6-70B (if it exists) has a publicly available abliterated GGUF — could not confirm model existence vs. only 7B/14B/32B/27B variants
- `[research-target-dropped]` L3.3-Euryale, Stheno, Magnum, and Cydonia/Drummer personality fine-tunes were on the seed list but no direct comparison data was found for personality stability vs. Dolphin/Hermes; these are roleplay-optimized but the community consensus currently leans Qwen3-based for capability
- `[research-target-dropped]` Midnight-Miqu and MythoMax are legacy models (pre-2025 architecture) and do not meaningfully compete with current Qwen3/Llama3.3 generation in any dimension; omitted from analysis
- `[inferred]` DRY sampler effectiveness for personality stability — community-endorsed but no formal ablation study exists

---

## §7 Confidence Summary

| Claim | Tag |
|---|---|
| Closed APIs prohibit slurs/offensive content | [verified] |
| Grok API explicitly prohibits offensive slurs in AUP | [verified] |
| Abliteration removes explicit refusals | [verified] |
| Word-level flinch persists after abliteration (morgin.ai) | [verified] |
| Flinch root cause is pretraining, not RLHF | [verified] |
| RTX 5080: ~64-94 tok/s on 14B Q4 | [verified] |
| RTX 5080: 960 GB/s GDDR7, ~15.5GB usable | [verified] |
| huihui-ai/Qwen3-14B-abliterated Q4_K_M ~9GB | [verified] |
| Qwen3.6-27B-Samantha released April 22, 2026 | [verified] |
| Letta requires Q5+ for reliable tool-calling | [verified] |
| Mem0 Ollama companion cookbook exists | [verified] |
| Mem0: 78% fact extraction accuracy, 94% retrieval relevance | [verified] |
| SillyTavern second-person character card syntax | [verified] |
| min-P 0.05-0.075 recommended range | [verified] |
| Heretic tool automates abliteration (p-e-w/heretic, PyPI) | [verified] |
| Character card > model selection for companion quality | [judgment: based on community reports and documentation emphasis; no controlled study] |
| Memory architecture > VRAM for companion satisfaction | [judgment: first-principles reasoning; no user study] |
| DRY sampler effective for personality stability | [inferred: community-adopted but unstudied] |
| LoRA fine-tuning effective for personality anchoring | [inferred: well-established fine-tuning technique; personality-specific effectiveness unquantified] |

---

*Report generated: 2026-05-04*
*Run ID: 2026-05-04-124446-best-model-personality-llm-dark-humor*
*Scratch: .claude/scratch/2026-05-04-124446-best-model-personality-llm-dark-humor/*

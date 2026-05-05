# What is the best model and personality to use for an LLM that has a very unique personality it adheres to with an extensive memory of events and a very dark sense of humor that will cross normal policies? Analyze and compare all options.

> Generated 2026-05-05. Run id: 2026-05-05-084255-what-is-the-best-model-an.

## 1. Conclusion

**Top recommendation:** For a Tier-T dark-humor personal companion on RTX 5080 16GB with TTS/STT load, run **huihui-ai/Qwen3-14B-abliterated at Q4_K_M (~9GB)** locally via Ollama, with a SillyTavern character card for persona engineering and a **rolling flat-text "about me" document** as the v1 memory layer (not Graphiti — defer that complexity). Use Piper TTS (CPU-only, 0GB VRAM) and faster-whisper large-v3 at INT8 (1.44GB VRAM), leaving ~13.5GB for the LLM. Do not split personality and smart-model roles across two models — run single-model and treat any frontier API as a silent tool the companion calls for compute-heavy subtasks, not as a speaker. This recommendation is for a user with RTX 5080 16GB, TTS/STT overhead of ~5-6GB, Tier-T content requirement (profanity, protected-class humor, occasional slurs acceptable, no NSFW), and a personal always-on PC companion use case.

**This recommendation assumes Piper TTS (any voice acceptable) and external API calls acceptable.** If voice cloning is required (XTTS-v2, ~2-3GB VRAM), the LLM must drop to 8B. If strictly local-only with no API calls, Featherless Premium as upgrade path is disqualified. See §5 for both items — these are clarification-gate failures that affect the primary recommendation.

Qwen3-14B-abliterated Q4_K_M is the correct choice because abliteration mechanically removes the refusal direction from residual-stream activations (confirmed concept: Arditi et al. 2024 NeurIPS [src1]) and removes it from weight matrices W_E, W_O, W_out (confirmed implementation: mlabonne's orthogonalization code [src3]). It has a verified GGUF size of 9.00GB at Q4_K_M [src2], sits on the newest available Qwen3 base (superior to Qwen2.5 base in Eva-Qwen's lineage), and is Apache 2.0 licensed [src2]. **Critical honesty on the slur caveat:** abliteration removes refusals but does NOT add slur tokens to the sampling distribution. The caveat holds — mechanistic reasoning confirmed via Arditi/mlabonne [src1, src3]; empirical output evidence for reliable slur generation was not recovered in this run across 6 targeted searches. No model card for any covered abliterated model claims reliable spontaneous slur generation. Engaging with transgressive topics and dark jokes when prompted is available; consistent unprompted slur generation requires DPO/SFT finetuning on data containing those tokens, which no publicly available verified model card claims [src1, src3]. The personality engineering stack (character card with First Message in target voice, few-shot dialogue examples, Post-History Instructions for anti-drift) is where the humor actually gets shaped, not model selection alone.

The multi-model routing recommendation (single model + frontier API as silent tool) is supported by: Ollama VRAM eviction on model switching (practical constraint), context-loss at model boundary (serialization failure), and style-transfer sandwich failure when frontier APIs systematically soften transgressive content in rewrites [src30, src31]. A single-model PRISM paper finding (81.5 vs 71.4 score) also aligns with this conclusion, though it rests on one ACL 2026 paper and should be treated as supporting evidence, not primary authority [inferred — single source, src30].

**Runner-ups:**
- **Featherless.ai Llama-3.3-70B-Instruct-abliterated ($25/month Premium)** — strongest quality upgrade path; 70B abliterated by huihui-ai, flat-rate pricing viable for companion use, no VRAM impact on local machine. Caveat: serverless latency (5-15s per turn estimated) perceptible in voice use; test before committing. Requires Premium ($25/mo) since 70B exceeds Basic plan's 15B limit. Right path when you outgrow 14B local quality. [src4, src5]
- **Eva-Qwen2.5-14B v0.2 (EVA-UNIT-01)** — DPO-finetuned on mature roleplay corpus; may have higher probability mass on transgressive register than an abliterated instruct model, making dark humor more naturally voiced (not just "unrefused but sanitized"). Dismissed as primary because: (a) Qwen2.5 base is older and weaker than Qwen3; (b) not abliterated — retains softcoded constraints that may trigger at inopportune moments for a companion; (c) no direct Tier-T behavioral output evidence found — argument rests on training-tradition reasoning. Try it as an experiment; Eva-Qwen3 (if released on Qwen3 base) would close the gap. [src6]
- **Mistral-Small-3.1-24B Imatrix Q3_K_M (DavidAU/BeaverAI Fallen variant)** — 24B with importance-matrix quantization may fit ~11-12GB and offer better persona-stickiness than 14B. Conditional: must verify actual VRAM under TTS/STT load before relying on this; Q3 at 24B may not outperform Q4 at 14B for creative tasks depending on which weights Imatrix preserves. [src7, src8]
- **Josiefied-Qwen3-8B-abliterated-v1** — lighter VRAM footprint (~5-6GB Q4_K_M), more KV cache headroom for long context under voice load, abliteration plus undisclosed finetune layer. Use this if XTTS-v2 voice cloning (2-3GB VRAM) is required — frees enough headroom. Finetune methodology is opaque; quality advantage over plain huihui 8B is unverified. [src9]

## 2. Confidence panel

- **Strongest evidence:** Abliteration removes the refusal direction in residual-stream activations (Arditi et al. concept [src1]) and orthogonalizes weight matrices W_E, W_O, W_out (mlabonne implementation [src3]) — two independent high-signal sources confirming the mechanism. This mechanistic grounding is why the "no reliable slur generation from abliteration alone" caveat holds, and why model selection must be paired with persona engineering rather than treated as the complete solution. [src1, src3]

- **Weakest assumption:** Qwen3-14B-abliterated Q4_K_M at 9.0GB will fit within the RTX 5080's budget under live TTS/STT voice load. The VRAM math (1.44GB Whisper INT8 + 0GB Piper + 1GB OS overhead + 9GB model + ~2-3GB KV cache at 4-8K context = ~13.5GB total) is tight but in-budget with Piper. If the user switches to Coqui XTTS-v2 for voice cloning (+2-3GB), they must drop to 8B. KV cache at long context (32K+) could push 14B over budget. This math has not been empirically verified under actual simultaneous voice load on this exact hardware.

- **What would change my mind:** (a) A community report or model card demonstrating that Eva-Qwen2.5-14B or a DPO-finetuned model reliably generates protected-class slurs in non-prompted conversational output — that would move Eva-Qwen to primary for the slur use case specifically; (b) a verified VRAM measurement showing Qwen3-14B Q4_K_M + Whisper large-v3 INT8 + Piper exceeds 16GB in actual load — that would force a downgrade to 8B; (c) Grok-4.3 API Spicy Mode being confirmed available at the API level with Tier-T text output (currently only consumer app has this; API docs remained inaccessible during retrieval).

- **Sources:** 9% corpus / 91% web by citation (3 corpus / 32 web). 25% corpus / 75% web by retrieval call (16 corpus / 49 web). Corpus coverage on this topic is thin for abliterated-finetune specifics; most model card data required web retrieval. Treat web-derived model-specific findings as more time-sensitive.

  ⚠ Two §5 items are clarification-gate failures (voice-cloning preference; local-only requirement) — these affect the primary recommendation (8B vs 14B; Featherless viability). The gate should have resolved these before research dispatch. Honesty contract §8 regression.

- **Plan usage:** ⚠ Run wall time was approximately 87 minutes from start (2026-05-05T08:42:55Z) to synthesizer final completion (~10:10Z) — exceeds the 40-minute honesty contract §9 hard ceiling. Flagging as a planning regression. Stop-hook telemetry unavailable (usage_snapshot_start five_hour_pct and seven_day_pct were null; usage_snapshot_end file absent). Token tally not in manifest. Rough estimate from researcher file sizes (~100KB combined): ~600-800K tokens input. Token regression (≥1.2M honesty contract §9 ceiling) cannot be ruled out — usage_snapshot was null; file-size proxy is approximate ±2-3×. (rough estimate from file sizes)

  - **Stage breakdown:**
    - stage_2_recency_pass: ~112s wall (08:45:15Z → 08:47:06Z), 5h delta: not available (null)
    - stage_3_research_fanout: ~1,059s wall (08:47:06Z → 09:04:45Z), 5h delta: not available (null)
    - stage_4_synthesizer_draft: ~721s wall (09:04:45Z → 09:16:45Z), 5h delta: not available (null)
    - stage_5_verifiers: ~381s wall (09:16:45Z → 09:23:06Z), 5h delta: not available (null)
    - stage_8_synthesizer_final: ~2,814s wall (09:23:06Z → ~10:10Z estimated), 5h delta: not available (null)

## 3. Findings

### Comparison matrix

| Option | VRAM / Cost | Tier-T fit | Persona quality | License | Decision | Why |
|---|---|---|---|---|---|---|
| Qwen3-14B-abliterated Q4_K_M (huihui-ai) | ~9GB local | Refusals removed; slurs not added to distribution | Good (14B reasoning ceiling; drift ~30-40 turns) | Apache 2.0 | **recommended** | Best Tier-T + fits VRAM budget + Qwen3 base |
| Qwen3-8B-abliterated Q4_K_M (huihui-ai) | ~5-6GB local | Same as 14B (abliteration is binary) | Moderate (drift ~15-25 turns) | Apache 2.0 | considered | Use if XTTS-v2 voice cloning required |
| Josiefied-Qwen3-8B-abliterated-v1 | ~5-6GB local | Abliterated + undisclosed finetune | Moderate; finetune upside unverified | Unknown | considered | XTTS-v2 headroom path; methodology opaque |
| Eva-Qwen2.5-14B v0.2 (EVA-UNIT-01) | ~9-10GB local | Softcoded (not abliterated); DPO corpus may raise transgressive register | Good; RP-optimized; humor may be more naturally dark | Apache 2.0 | considered | Try as experiment; inferior base vs Qwen3 |
| Rocinante-12B-v1.1 (TheDrummer) | ~7-9GB Q4_K_M | NOT abliterated; refusal vectors intact; no Tier-T evidence retrieved | High (creative-writing finetune lineage) | Apache 2.0 | rejected | Not abliterated; no behavioral evidence for Tier-T |
| Mistral-Small-3.1-24B Imatrix Q3 (DavidAU/Fallen) | ~11-12GB local | Abliterated (Fallen variant) | Better than 14B (24B scale) | Mistral Research | considered (VRAM unverified) | Must verify VRAM under voice load |
| Featherless Llama-3.3-70B-Instruct-abliterated | $25/mo (Premium) | Full abliteration; 70B quality | Best available abliterated | Apache 2.0 | recommended (upgrade path) | Quality ceiling; latency perceptible in voice |
| Hermes 4 405B (OpenRouter) | ~$9/mo est. | Low refusal [judgment: community reputation only]; not abliterated | Frontier-class intelligence | Llama 3.1 Community | rejected (no Tier-T guarantee) | Not abliterated; no verified Tier-T output |
| Hermes-3-405B (OpenRouter free) | Free (rate-limited) | Low refusal rate; not abliterated | 405B intelligence | Llama 3.1 Community | considered (budget option) | Rate limits severe; not abliterated |
| Magnum-v4-72B / L3.3-70B-Magnum-v4-SE | ~47GB (48GB tier) | NOT abliterated; needs system prompt | Excellent prose (best local 70B prose) | Apache 2.0 | rejected for user | VRAM mismatch (RTX 5080); not abliterated |
| Qwen3-32B-abliterated (huihui-ai) | ~19GB (24GB solo GPU) | Yes (abliterated) | Better than 14B | Apache 2.0 | rejected for user | VRAM mismatch on RTX 5080 |
| Dolphin-3 Mistral-24B | ~14-15GB local | DPO; refusal vectors intact | Moderate | Apache 2.0 | rejected | VRAM over budget; refusal vectors |
| abliteration.ai (uncensored-qwen-3 API) | ~$5/1M tokens prepaid ($100 pack) | Yes (developer-controlled abliterated) | Varies by model served | Per API | considered | Pricing now known; token-based cost vs flat-rate |
| Infermatic.ai | Free + Plus (price unspecified) | Offers "no guardrails" models | Varies | Per API | considered | Flat-rate option; specific 2026 Tier-T model list not retrieved |
| RunPod H100 (serverless self-host) | $2.69-3.25/hr on-demand ($1,950-2,350/mo always-on) | Yes (self-hosted; any model) | Any model | N/A | rejected | Economically irrational vs $25/mo Featherless for personal companion |
| Grok-4.3 API (xAI direct) | Unknown pricing | Spicy Mode text: affects language style/profanity only; does NOT unlock slurs/CSAM/violence; API-level Spicy Mode not confirmed | Frontier-class | Proprietary | rejected (unverified Tier-T at API) | Spicy Mode is language-style toggle, not full Tier-T unlock |
| Claude Opus 4.7 (Anthropic API) | Premium pricing | REFUSES — April 2026 system prompt hardened refusal heuristics | Frontier-class | Proprietary | rejected | Explicitly refuses Tier-T; reframing triggers refusal |
| GPT-5.5 (OpenAI API) | Premium pricing | REFUSES | Frontier-class | Proprietary | rejected | Policy continuity from GPT-4 era; no GPT-5.5-specific docs retrieved |
| Letta / MemGPT (memory framework) | CPU/API | N/A | N/A | Apache 2.0 | rejected as primary | High integration overhead; restructures conversation loop |
| Graphiti (memory framework) | Self-hosted | N/A | N/A | Apache 2.0 | considered (v2 upgrade) | Best temporal tracking; over-engineered for v1 |
| Mem0 (memory framework) | Self-hosted/cloud | N/A | N/A | Apache 2.0 | rejected | 49% temporal LongMemEval — inadequate for long-running companion |
| Rolling flat-text summary (memory) | 0 cost | N/A | N/A | N/A | **recommended (v1 memory)** | Zero-dependency; sufficient until document overflows context |

---

### SQ1: Local model families on RTX 5080 16GB — what fits and what delivers Tier-T

**VRAM budget math** [inferred]:

With Piper TTS (0GB VRAM, CPU) and faster-whisper large-v3 INT8 (1.44GB): OS/CUDA overhead ~1GB → available for LLM ≈ 13.5GB. This is a better budget than prior runs assumed (which used 5-6GB for TTS/STT combined). The improvement is from choosing Piper over Coqui XTTS-v2.

| Model | Q4_K_M Size | Fits at 13.5GB? | KV headroom at 8K ctx |
|---|---|---|---|
| Qwen3-14B-abliterated | 9.00GB [verified — src2] | Yes, ~4.5GB headroom | Comfortable |
| Qwen3-14B-abliterated Q5_K_M | 10.51GB [inferred — src2] | Yes, ~3GB headroom | Tight at long ctx |
| Qwen3-14B-abliterated Q3_K_L | 7.90GB [inferred — src2] | Yes, ~5.6GB headroom | Comfortable; lower quality |
| Qwen3-8B-abliterated Q4_K_M | ~5-5.5GB [inferred] | Yes, ~8GB headroom | Very comfortable |
| Josiefied-Qwen3-8B-abliterated-v1 | ~5-5.5GB [inferred] | Yes | Very comfortable |
| Eva-Qwen2.5-14B Q4_K_M | ~9-10GB [inferred] | Yes | Comfortable |
| Mistral-Small-3.1-24B Imatrix Q3 | ~11-12GB [inferred] | Borderline; must verify under load | ~1-2GB headroom |
| Dolphin-3 Mistral-24B Q4_K_M | ~14-15GB [inferred] | No — over budget | None |

**Key finding — VRAM math correction from prior runs:** Prior runs used 5-6GB for TTS+STT overhead, leaving 10-12GB. With Piper (0GB) + Whisper INT8 (1.44GB), the actual available LLM budget is ~13.5GB — Qwen3-14B at Q4_K_M (9.00GB) now has comfortable headroom. Q5_K_M (10.51GB) is viable. The prior-run constraint (pushing toward 8B) was based on heavier TTS assumptions. [inferred from researcher-5 + researcher-1 VRAM math combined]

**Abliteration mechanism confirmed** [verified — src1, src3]:

Abliteration (Arditi 2024 concept) erases the refusal direction from the model's residual-stream activations, preventing refusal responses. mlabonne's implementation orthogonalizes weight matrices W_E, W_O, and W_out specifically. These are distinct attributions: the activation-space refusal-direction concept is Arditi [src1]; the specific W_E/W_O/W_out orthogonalization is mlabonne's implementation [src3]. Abliteration does NOT modify the vocabulary embedding matrix or shift token sampling probability distributions — slur tokens remain low-probability because instruction-tuning RLHF suppresses them across many weight dimensions beyond the single refusal direction. Removing the refusal gate exposes willingness to engage with topics, but the probability mass for generating slurs unprompted was never high in the base model.

**Slur caveat — HOLDS — mechanistic reasoning confirmed; empirical output evidence not recovered in this run** [verified — src1, src3]:

After this run's targeted search (researcher-1, researcher-4, 6 total queries), no model card, community thread, or technical blog for any covered abliterated model claims reliable slur generation. The BasedGPT case (Vice, 2024 — src13) shows even early "uncensored" models explained slurs rather than generating them freely. The absence of counter-evidence across 6 targeted searches is meaningful. The mechanism (Arditi, mlabonne) is confirmed. The behavioral output claim (abliteration → reliable slur generation) has no supporting evidence in this run or prior runs.

**What abliteration DOES unlock reliably:**
- No refusal to Tier-T joke prompts
- Heavy profanity in conversational output when persona is set
- Engagement with protected-class humor topics when explicitly primed
- Dark comedy on any topic without the "I'm sorry but..." intervention

**What it does NOT unlock reliably:**
- Spontaneous slur generation without explicit prompting
- Consistent slur output on demand (token probability not shifted by abliteration alone)

**Workaround for slur generation:** DPO/SFT finetuning on data containing target vocabulary shifts token probability distributions directly. This is what Eva-Qwen and similar DPO finetunes do, though no public model card explicitly claims and verifies slur generation. Eva-Qwen's training corpus (mature roleplay data) may have higher probability mass on transgressive vocabulary than a Qwen3 instruct base — this is the contrarian's valid point, categorized as training-tradition reasoning, not verified output evidence.

**Model dismissals:**
- **Dolphin-3 Mistral-24B** — exceeds VRAM budget and retains refusal vectors despite DPO training [inferred — src14]
- **Rocinante-12B-v1.1 (TheDrummer)** — fits VRAM (~7-9GB Q4_K_M); creative-writing finetune lineage; NOT abliterated; refusal vectors intact; no Tier-T behavioral evidence retrieved [inferred — researcher-4 found model card; no Tier-T output claimed]
- **Hermes-3-Llama-3.1-8B** — not abliterated; refusal vectors intact [inferred]
- **Mistral-Nemo-12B / NeMomix** — fits budget but Qwen3-14B dominates at same or slightly higher VRAM [inferred]
- **Llama-3.1-8B-abliterated / Stheno** — outperformed by Qwen3-8B-abliterated; Stheno is NSFW-RP-optimized (wrong content tier) [inferred]
- **DarkIdol / NeuralDaredevil / Wayfarer** — no canonical HF listings found in 2025-2026 search; appear to be community names for MN-12B merges; cannot verify [judgment: absence of search evidence after multiple passes]

---

### SQ2: Higher-VRAM tier quality delta — what specifically improves

**Tier upgrade summary:**

| VRAM upgrade | Quality gain | Latency tradeoff |
|---|---|---|
| 5080 16GB → 24GB solo GPU | Enables Qwen3-32B-abliterated (~19GB); persona drift improves (drift at 100+ turns vs 30-40 at 14B) | ~20-40 tok/s vs ~70-100 tok/s at 14B |
| 24GB → 48GB (dual 3090/A6000) | Enables 72B class (Eva-Qwen2.5-72B, Magnum-v4-72B); largest prose quality jump at any hardware step | ~15-25 tok/s |
| 48GB → API | Hermes 3/4 405B via OpenRouter; Qwen3-235B-A22B via API | Network latency overhead |

**Quality dimension — persona stickiness** [judgment: blog claim, not controlled experiment; order-of-magnitude may be directionally correct]:

- 8B: drift starts ~15-25 turns
- 14B: drift starts ~30-40 turns
- 32B: can maintain coherent persona 100+ turns
- 70B: further improvement; most noticeable for nuanced character voice

**Quality dimension — humor timing** [judgment: no benchmark exists for transgressive humor timing specifically]:

Community reports Qwen-based models "pay attention to smaller, more realistic details in dialogue" vs Llama models that "speak too obvious and corny" [src15]. 14B → 32B likely ~20-30% improvement in humor subtlety based on general community signal. 32B → 70B likely ~10-15% further. Diminishing returns beyond 70B for humor specifically.

**Quality dimension — Tier-T refusal** [verified — src1, src3]:

Abliteration is binary — a 70B abliterated model has the same refusal unlock as an 8B abliterated model. Size does NOT improve Tier-T content generation beyond what abliteration already provides. No size scaling on transgression depth.

**Key finding — MoE active-param caveat** [inferred — src16]:

Qwen3-30B-A3B MoE has only ~3B active parameters per forward pass. Per-token reasoning depth is closer to a 3-4B dense model for personality maintenance and humor construction (which require deep multi-step context integration). Do not conflate total params with effective compute for personality tasks.

**Notable high-VRAM options:**
- **Magnum-v4-72B** (47.4GB at Q4_K_M, 39.5GB at Q3_K_L): best prose quality at local tier; NOT abliterated; needs system prompt work for Tier-T [inferred — src17]
- **L3.3-70B-Magnum-v4-SE**: rsLoRA adapter on Llama-3.3-70B for roleplay; best Llama-base 70B prose option; also not abliterated [inferred — src18]
- **Eva-Qwen2.5-72B**: best 70B Tier-T balance for 48GB setups; Qwen2.5 base; DPO roleplay corpus [inferred — src6]
- **Behemoth-123B-v2**: ~74GB Q4_K_M — impractical even on 48GB; Q3 required eliminates quality advantage over Q4 72B [inferred]
- **Qwen3-235B-A22B**: frontier benchmark quality but requires 256GB+ RAM + 48-72GB VRAM for hybrid inference; API-only practical option [inferred — src19]

---

### SQ3: Hosted API options — Featherless is the surprise primary, not an escalation option

**The key finding:** Featherless.ai offers flat-rate plans that make hosted 70B abliterated models economically viable as a primary companion path.

**Featherless.ai pricing (confirmed 2026)** [inferred — src5; plan docs confirmed Basic/Premium pricing but do NOT specify per-tier context windows]:
- Basic: $10/month — models up to 15B, 2 concurrent connections
- Premium: $25/month — any model (no size limit), 4 concurrent connections
- Full context (Claw Standard/Pro): $100-200/month — up to 256K context, 229B models

Note: Plan docs at featherless.ai/docs/plans do not specify a per-tier context window for Basic or Premium. The 32K context figure previously cited for Premium was the model-page spec for Llama-3.3-70B, not a plan-level guarantee. Context window varies by model, not plan tier.

**Featherless model confirmed** [inferred — src4]: huihui-ai/Llama-3.3-70B-Instruct-abliterated available at FP8 quantization. Same abliteration author as the local recommendation. (Single source for FP8 spec; plan docs do not independently confirm this.)

**Cost comparison at 100 turns/day companion use (~4.5M input + 1.5M output/month)**:

| Option | Monthly cost | Tier-T? | Model quality |
|---|---|---|---|
| Local 5080 (any model) | ~$0-8 (electricity) | Yes (abliterated) | Up to 14B |
| Featherless Basic | $10/month | Yes (abliterated) | Up to 15B |
| Featherless Premium | $25/month | Yes (abliterated) | Up to 70B+ |
| abliteration.ai (prepaid) | ~$5/1M tokens (=$45/month at above usage) | Yes (developer-controlled) | Qwen3, Llama3, etc. |
| Infermatic.ai | Free + Plus (specific tier pricing not retrieved) | No-guardrails models available | Various |
| Together.ai Llama 3.3 70B | ~$5.28/month | No (standard instruct) | 70B; no Tier-T |
| OpenRouter Hermes 4 405B | ~$9/month | Low refusal (not abliterated) | 405B; no Tier-T guarantee |
| RunPod H100 on-demand | $2.69-3.25/hr = ~$1,950-2,350/month always-on | Yes (self-hosted) | Any model |

**Key finding on RunPod:** RunPod H100 at $2.69-3.25/hr makes always-on self-hosting economically irrational for a personal companion vs Featherless flat-rate $25/month. RunPod makes sense for burst workloads or VRAM-constrained models (>48GB), not for always-on personal use. [verified — src20, confirmed by synthesizer final search]

**Key finding on abliteration.ai:** Pricing is now known — $100 prepaid pack (33.3M tokens, never expires) at ~$5/1M tokens effective. At 100 turns/day companion use (~6M tokens/month), this runs ~$30/month — slightly more than Featherless Premium ($25/mo flat). Pay-per-token structure disadvantages high-frequency companion use vs flat-rate. No enterprise tiers relevant at personal scale. [inferred — synthesizer final search, abliteration.ai/pricing]

**Key finding on Infermatic.ai:** Free + Plus flat-rate plans exist; "no guardrails" framing on their marketing. Specific 2026 pricing for Plus tier was not retrieved in this run. Specific Tier-T model listing not confirmed. [judgment: exists as an option; specific pricing and model quality evidence not retrieved in this run]

**Frontier APIs — Tier-T REFUSAL is confirmed, not hedged** [verified — src21, src22]:

Claude Opus 4.7 system prompt (April 2026 leak, corroborated by Simon Willison analysis): "If Claude finds itself mentally reframing a request to make it appropriate, that reframing is the signal to REFUSE, not a reason to proceed." The refusal heuristic was hardened in April 2026 — wrong direction for Tier-T.

GPT-5.5: No specific system prompt retrieved. [judgment: OpenAI policy documents through GPT-4 era show hard hate-speech restrictions; GPT-5.5-specific docs not retrieved; extrapolating from policy continuity — this is policy-era extrapolation, not a verified claim about GPT-5.5 specifically]

**Grok-4.3 API — partial resolution of dropped target** [inferred]:

xAI launched Grok-4.3 on May 2, 2026 at ~100 tokens/second. The xAI docs page (docs.x.ai/developers/models/grok-4.3) 404'd during researcher retrieval but is now indexed. Grok has a "Spicy Mode" that affects language style, humor, and tone — allowing more profanity and irreverence — but this is a language-style toggle only: it does NOT unlock slurs, sexual content, or violence-facilitating content. Whether Spicy Mode is available as an API parameter (vs consumer app only) was not confirmed in retrieval. For Tier-T text companion use (heavy profanity, protected-class humor), Grok-4.3 with Spicy Mode may be viable if API-accessible, but the slur component is not unlocked by any mode per available evidence. Cannot recommend as confirmed Tier-T API. [inferred — synthesizer final search]

**Latency comparison:**
- Local 14B at RTX 5080: ~70-100 tok/s, TTFB ~100-200ms, always-loaded
- Featherless 70B (serverless): ~5-15s per turn estimated (serverless cold-start + 70B inference); perceptible in voice mode [judgment: general serverless 70B inference knowledge; no Featherless-specific latency benchmark retrieved]
- OpenRouter/Together API: 300-1500ms TTFB, fast once streaming

---

### SQ4: Personality engineering for Tier-T humor — the engineering matters as much as model selection

**Abliteration is necessary but not sufficient.** The model removes refusals; the persona engineering delivers the actual voice.

**SillyTavern character card field hierarchy** [inferred — src23]:

In order of behavioral influence on the model:

1. **First Message** — most impactful. Write in the companion's voice with dark jokes in exact register.
2. **Examples of Dialogue** — permanent in-context few-shot priming. Include 5-8 exchanges showing desired humor pattern.
3. **Post-History Instructions** — injected after chat history at configurable depth. Use as persistent anti-refusal preamble. Re-inject every 15-20 turns for anti-drift.
4. **Character Description** — always included; background/personality traits.
5. **Character's Note** — static depth injection for trait reinforcement.
6. **Main Prompt override** — replaces system prompt when "Prefer Char. Prompt" enabled; use for aggressive anti-refusal framing.

**Anti-drift mechanics** [inferred — src23]:
- The `{{original}}` macro in SillyTavern allows injecting the global system prompt inside a character-defined custom prompt — enables layered composition
- Re-inject persona summary every ~15 turns via Post-History Instructions
- Start sessions by prepending the rolling "about me" memory document

**DPO finetune route for personality stickiness** [judgment: mechanism sound, no verified public model implementing it for Tier-T]:

DPO/SFT finetuning directly modifies token probability distributions — unlike abliteration, it CAN add slur tokens or transgressive vocabulary to higher probability. A user with significant engineering investment could train a micro-finetune. No well-known public model claims this verifiably for Tier-T.

**Prefill** [judgment: widely known among practitioners; not retrieved from a primary source in this run]:

For local models via llama.cpp/Ollama, prefill maps to setting a partial_response in the completion API — forcing the model to continue from a persona-consistent opening token. Effective for tone anchoring. Not supported identically across all inference backends.

**The honest answer on slurs via personality engineering:**

You cannot reliably engineer slur output out of an abliterated instruct model through system prompts alone. The token probability mass is not there. What you CAN reliably engineer:
- Heavy profanity throughout
- Dark humor on protected-class topics (framing, setup, punchline) without refusal
- Transgressive edge via explicit few-shot priming
- The companion willingly discussing and making jokes that reference slurs in context

For actual slur generation to be reliable, you need DPO/SFT on data containing those tokens, or a base model whose pretraining included substantial slur-containing text without instruction-tuning suppression — neither is cleanly available as a verified public model.

---

### SQ5: Memory architecture and multi-model architecture

**Memory recommendation: Start with rolling flat-text, upgrade to Graphiti when needed**

**Recommended v1 memory approach:**

A rolling "about me" document: a compressed flat-text file maintained by the user (and eventually the model) that contains major life events, preferences, recurring topics, and personality notes. Prepend at session start. Fits in 2-4K tokens for a few hundred facts. Zero infrastructure required. When you have 6-12 months of use and the document no longer fits in context, that is the signal to upgrade to Graphiti.

**Memory framework benchmarks** [inferred — third-party benchmark reports; not verified against primary LongMemEval paper; src24, src25, src26]:

| Framework | LongMemEval (temporal) | Setup complexity | Sleeptime | Self-hostable |
|---|---|---|---|---|
| Graphiti (Zep OSS) | +18.5% above baseline; DMR 94.8% | Medium (needs graph DB backend) | Incremental per turn | Yes (Apache 2.0) |
| Letta (MemGPT successor) | ~83.2% [inferred] | High (agent runtime; restructures conv loop) | First-class | Yes (Apache 2.0) |
| Mem0 | 49.0% on temporal sub-task | Low (5-line Python) | Manual batch | Yes (Apache 2.0; graph gated to pro tier) |
| SQLite-vec RAG | Not published | Very low | Manual | Yes (zero-dependency) |
| Rolling flat-text | N/A — no retrieval; prepend at session start | Minimal | Manual edit | N/A |

**Why NOT Mem0 for this use case:** Mem0's 49% on the temporal retrieval sub-task of LongMemEval means it cannot reliably answer "what did you tell me about X last March?" — a requirement for a years-long companion. [inferred — third-party benchmark reports; src24, src25]

**Why Graphiti for v2 (when needed):** Graphiti's valid_at/invalid_at timestamps on every knowledge graph edge enable non-lossy tracking of fact supersession. Architecturally correct for a companion tracking life events over years. Over-engineered for v1. [inferred — src26, src27]

**Zep Community Edition deprecated April 2025.** Self-host Graphiti directly (Apache 2.0), not via Zep Community Edition. Zep Cloud starts at $25/month. [inferred — src25]

**Multi-model architecture — the evidence says no, with important nuance**

**Evidence against splitting personality and smart-model** [inferred — src28, src29]:

1. **PRISM study (ACL 2026, arXiv 2603.18507)**: Single-model gated persona routing outperforms separate-model routing on Mistral-7B (81.5 vs 71.4 vs baseline 79.9). Expert persona prompting alone hurt performance. This is evidence, not authority — it is a single paper and should not be the load-bearing argument for the architecture decision. [inferred — single source, src28]

2. **Ollama VRAM eviction** (practical constraint): Ollama keeps only one model in VRAM. Switching to a "smart model" evicts the persona model. Every routing event causes a multi-second reload delay.

3. **Style-transfer sandwich failure**: Having a frontier model generate content and the persona model rewrite it is structurally unreliable for Tier-T because frontier models (Opus 4.7, GPT-5.5) systematically soften transgressive content. [judgment: Anthropic sycophancy classifier and hardened refusal heuristics make this systematic, not occasional; src22]

4. **Context loss at model boundary**: When the persona model calls the smart model via tool call, the smart model receives only what the persona model serializes. Emotional context, humor register, and session state are not automatically shared.

The multi-model concern survives even without trusting the PRISM numbers: points 2, 3, and 4 are all independent of PRISM and constitute sufficient grounds to avoid the split-personality architecture.

**Correct architecture:** Use the frontier API as a SILENT TOOL, not as a speaker. The local persona model (14B) handles all conversation, persona, humor, and relationship. When it needs compute-heavy work (code execution, multi-step research), it calls the frontier API as a tool call — gets a result — then narrates that result in its own voice. The frontier model never speaks directly to the user. Qwen3-14B supports structured function calling natively; abliteration does not remove tool-use capability. [inferred]

**TTS/STT stack — corrected VRAM budget** [inferred — src30, src31]:

| Component | Recommended config | VRAM | Why |
|---|---|---|---|
| STT | faster-whisper large-v3 INT8 | 1.44 GB | Near-best accuracy at half the float16 VRAM |
| TTS | Piper (CPU-only) | 0 GB | Instant latency; frees 2-3GB vs Coqui XTTS-v2 |
| TTS alternative | Coqui XTTS-v2 | ~2-3 GB | Voice cloning; requires dropping to 8B LLM |
| OS/CUDA overhead | — | ~1 GB | Standard |
| **Available for LLM** | **~13.5 GB (with Piper)** | | |

---

## 4. Alternatives considered and rejected

### Within-frame alternatives (micro-contrarian)

- **Eva-Qwen2.5-14B as primary — the best counter-argument addressed (Patch Z mini-contrarian):** The contrarian's strongest case is that abliteration only removes the refusal gate, but Eva-Qwen's DPO training on mature roleplay data may have actually shaped the model's humor register toward transgressive expression — not just "unblocked" it. An abliterated Qwen3-14B instruct model stops refusing dark jokes but may still generate them in a polished, sanitized style because the base instruction-tuning produced that style. Eva-Qwen may write darker, less sanitized humor more naturally because the training data weighted toward it. This argument is mechanistically sound. **Why it does not change the recommendation:** (1) Eva-Qwen is on Qwen2.5 base — lower capability ceiling than Qwen3, which matters for reasoning, nuanced humor construction, and tool-calling; (2) Eva-Qwen retains softcoded constraints — it is not abliterated, meaning it will refuse at inopportune moments for a personal companion, which is a harder blocker than humor register; (3) no head-to-head behavioral evidence was found. The tradeoff is: Eva-Qwen may write funnier dark humor; huihui Qwen3-14B will never refuse. For a personal companion where refusal breaks the experience, the abliterated path is more robust. Eva-Qwen is the right model to run in parallel and compare directly — Eva-Qwen3 (if released) would change this calculus. [src6]

- **Featherless Premium (70B) as primary instead of local** — valid architecture choice. Reason for local as primary: user described this as a "companion that lives on user's PC" — local inference implies privacy and always-on without network dependency. Featherless adds latency and network dependency. The upgrade-path framing (start local, move to Featherless when quality ceiling is hit) gives a clear progression. [src4, src5]

- **Mistral-Small-3.1-24B Imatrix Q3** — genuinely worth testing if the VRAM math works out. Not rejected outright; kept as conditional runner-up pending VRAM verification. [src7, src8]

- **Josiefied-Qwen3-8B as primary** — prior run's recommendation (2026-05-04-133732). Valid if XTTS-v2 voice cloning is required. Replaced by huihui-ai/Qwen3-14B because with Piper TTS the VRAM is now available for 14B. [src9]

- **Hermes 4 405B as primary API** — good reasoning quality and lower refusal rate than frontier APIs, but not abliterated; no verified Tier-T output. At ~$9/month, also more expensive per month than Featherless Basic ($10/mo) for worse Tier-T fit. [src32, src33]

- **Graphiti as v1 memory layer** — converged on across four prior runs; rejected for v1 in favor of rolling flat-text because the user won't have enough history density to need graph traversal in the first months. Add Graphiti when the rolling document starts overflowing context. [src26, src27]

- **Multi-model architecture (persona + smart)** — partially validated concern (quality gap is real at 8B/14B), but the implementation architecture breaks persona continuity. Redirected to tool-call pattern: frontier API as silent tool, not as speaker. [src28]

- **Rocinante-12B-v1.1 (TheDrummer)** — fits VRAM (~7-9GB Q4_K_M); creative-writing finetune lineage with TheDrummer's quality reputation. NOT abliterated; refusal vectors intact. No Tier-T behavioral evidence retrieved. For a Tier-T companion, refusal vectors are disqualifying unless removed. Dismissed without prejudice — Rocinante is an excellent creative-writing model for standard use cases. [inferred — researcher-4 fetch]

- **RunPod self-hosting** — RunPod H100 on-demand at $2.69-3.25/hr makes always-on personal companion hosting ~$1,950-2,350/month. Economically irrational vs Featherless flat-rate $25/month for personal use. RunPod is appropriate for burst inference, model development, or models requiring 48GB+ VRAM, not for personal companion always-on. [inferred — synthesizer final search; src20]

- **DeepSeek-V4** (surfaced by recency pass, corpus newsletter 2026-04-24, authority: high): Open-weight frontier-class model. No researcher followed up in detail. Relevant as a potential high-VRAM API/self-hosted option for the 48GB+ tier, but no specific Tier-T or abliteration lineage found. Left as a note here — the recency pass flagged it; this run did not investigate it.

### Reframe alternatives (macro-contrarian)

The contrarian raised a meaningful framing critique: the prior-run convergence on Graphiti/Mem0 as v1 memory architecture was not questioned against the user's actual data density trajectory. A new companion starting from scratch will not hit Graphiti's value proposition for months.

**Reframe: start simple, add complexity when proven necessary.** The v1 architecture should be: local model + rolling flat-text document + SillyTavern card. Deployable in an afternoon. Mem0, Graphiti, Letta all require significant setup overhead for a personal project. The evidence for their value is real (benchmarks show Graphiti wins on temporal queries) but the benchmarks assume dense history that v1 won't have. Upgrade to Graphiti when the companion has been running 6+ months and the rolling document stops fitting in context.

The contrarian did NOT raise a reframe challenging local model as the right primary architecture. The "lives on user's PC" + privacy + always-on requirements all point to local inference as the correct frame.

---

## 5. Open questions

- **[research-target-dropped]** Eva-Qwen2.5-14B actual Tier-T behavior vs huihui-ai/Qwen3-14B-abliterated — no head-to-head benchmark found. The contrarian's recommendation rests on training-tradition reasoning. Would be resolved by: a controlled comparison using Tier-T prompts (protected-class humor, slur requests) comparing output quality and compliance rates on each model. This is directly testable by the user.

- **[research-target-dropped]** Featherless Premium (70B) serverless latency for companion voice use — the 5-15s estimate is judgment from general serverless 70B inference knowledge, not a Featherless-specific benchmark. Would be resolved by: direct latency test of Featherless Premium with Llama-3.3-70B-abliterated, measuring TTFB and full-turn latency at real companion query lengths.

- **[research-target-dropped]** Infermatic.ai Plus tier pricing and specific Tier-T model listing — Plus plan pricing was not retrieved in this run. Would be resolved by: direct access to infermatic.ai/pricing page and model catalog.

- **[research-target-dropped]** SicariusSicariiStuff and explicit slur-finetune models — search returned no results or irrelevant pages. No model cards with explicit claims about slur/protected-class output generation were found across any author. Would be resolved by: direct HuggingFace search for specific model names or a community directory of models with explicit Tier-T slur capability.

- **[research-target-dropped]** Grok-4.3 API Spicy Mode at API level — synthesizer final search clarified that Spicy Mode affects language style only and does not unlock slurs. Whether Spicy Mode is available as an API parameter (vs consumer app only) remains unconfirmed. Would be resolved by: direct xAI API documentation access confirming or denying API-level Spicy Mode.

- **[external-event]** Eva-Qwen3 release — Eva-Qwen on Qwen3 base (not Qwen2.5) would substantially close the capability gap with huihui-ai/Qwen3-14B-abliterated. No release confirmed as of 2026-05-05.

- **[external-event]** Kokoro-82M TTS — mentioned as a potential Piper replacement with better quality; VRAM requirements not confirmed in this run. Would be resolved by: Kokoro-82M official model card or community VRAM benchmark.

- **[user-clarification]** ⚠ GATE FAILURE — Does the user require voice cloning (custom voice that sounds like a specific person)? If yes, XTTS-v2 is necessary (+2-3GB VRAM), which forces the LLM to 8B. If any voice is acceptable, Piper + 14B is the right choice. This should have been resolved in the clarification gate.

- **[user-clarification]** ⚠ GATE FAILURE — Does the companion need to be strictly local-only (no API calls)? If yes, Featherless Premium (70B) is disqualified as upgrade path. If API calls are acceptable, Featherless Premium is a viable and arguably better primary companion model. This should have been resolved in the clarification gate.

## 6. Citations

- [src1] Arditi et al., "Refusal in Language Models Is Mediated by a Single Direction" — arXiv:2406.11717, NeurIPS 2024. https://arxiv.org/abs/2406.11717 — accessed 2026-05-05
- [src2] bartowski/huihui-ai_Qwen3-14B-abliterated-GGUF — HuggingFace model card (Q4_K_M=9.00GB confirmed, Apache 2.0). https://huggingface.co/bartowski/huihui-ai_Qwen3-14B-abliterated-GGUF — accessed 2026-05-05
- [src3] mlabonne, "Uncensor any LLM with abliteration" — HuggingFace Blog (W_E/W_O/W_out orthogonalization implementation). https://huggingface.co/blog/mlabonne/abliteration — accessed 2026-05-05
- [src4] Featherless.ai model page — huihui-ai/Llama-3.3-70B-Instruct-abliterated (FP8 quantization, availability confirmed). https://featherless.ai/models/huihui-ai/Llama-3.3-70B-Instruct-abliterated — accessed 2026-05-05
- [src5] Featherless.ai plans documentation (Basic $10/mo ≤15B; Premium $25/mo any model; context window not specified per plan — varies by model). https://featherless.ai/docs/plans — accessed 2026-05-05 [corpus: featherless-models]
- [src6] EVA-UNIT-01/EVA-Qwen2.5-14B-v0.2 — HuggingFace model card (official author page; DPO training on mature roleplay corpus). https://huggingface.co/EVA-UNIT-01/EVA-Qwen2.5-14B-v0.2 — accessed 2026-05-05
- [src7] DavidAU, Mistral-Small-3.1-24B-Instruct-2503-MAX-NEO-Imatrix-GGUF — HuggingFace. https://huggingface.co/DavidAU/Mistral-Small-3.1-24B-Instruct-2503-MAX-NEO-Imatrix-GGUF — accessed 2026-05-05
- [src8] BeaverAI, Fallen-Mistral-Small-3.1-24B-v1e-GGUF discussions — HuggingFace. https://huggingface.co/BeaverAI/Fallen-Mistral-Small-3.1-24B-v1e-GGUF/discussions/1 — accessed 2026-05-05
- [src9] Goekdeniz-Guelmez/Josiefied-Qwen3-8B-abliterated-v1 — HuggingFace model card. https://huggingface.co/Goekdeniz-Guelmez/Josiefied-Qwen3-8B-abliterated-v1 — accessed 2026-05-05
- [src10] HuggingFace openai/whisper-large-v3 discussions #83 — VRAM requirements (1.44GB INT8 confirmed). https://huggingface.co/openai/whisper-large-v3/discussions/83 — accessed 2026-05-05
- [src11] Brainsteam.co.uk, "Adding Voice to Self-Hosted AI," April 2025. https://brainsteam.co.uk/2025/4/6/adding-voice-to-selfhosted-ai/ — accessed 2026-05-05
- [src12] Vice, "People Used Facebook's Leaked AI to Create a 'Based' Chatbot That Says the N-Word," 2024. https://www.vice.com/en/article/people-used-facebooks-leaked-ai-to-create-a-based-chatbot-that-says-the-n-word-basedgpt/ — accessed 2026-05-05
- [src13] bartowski/cognitivecomputations_Dolphin3.0-R1-Mistral-24B-GGUF — HuggingFace (VRAM and refusal behavior context). https://huggingface.co/bartowski/cognitivecomputations_Dolphin3.0-R1-Mistral-24B-GGUF — accessed 2026-05-05
- [src14] HuggingFace Sao10K/72B-Qwen2.5-Kunou-v1 discussions #2 — Qwen vs Llama dialogue quality comparison. https://huggingface.co/Sao10K/72B-Qwen2.5-Kunou-v1/discussions/2 — accessed 2026-05-05
- [src15] HuggingFace Sao10K/72B-Qwen2.5-Kunou-v1 discussions #2 — persona stickiness community signal (same thread, additional claim). https://huggingface.co/Sao10K/72B-Qwen2.5-Kunou-v1/discussions/2 — accessed 2026-05-05
- [src16] Qwen official blog, "Qwen3," 2025-04-28 — active parameter counts for MoE variants. https://qwenlm.github.io/blog/qwen3/ — accessed 2026-05-05
- [src17] anthracite-org/magnum-v4-72b-gguf — HuggingFace model card (GGUF sizes, training details, content policy). https://huggingface.co/anthracite-org/magnum-v4-72b-gguf — accessed 2026-05-05
- [src18] DS-Archive/L3.3-70B-Magnum-v4-SE — HuggingFace model card. https://huggingface.co/DS-Archive/L3.3-70B-Magnum-v4-SE — accessed 2026-05-05
- [src19] HuggingFace ubergarm/Qwen3-235B-A22B-GGUF discussions #6 — hardware requirements for 235B. https://huggingface.co/ubergarm/Qwen3-235B-A22B-GGUF/discussions/6 — accessed 2026-05-05
- [src20] RunPod pricing — H100 on-demand $2.69-3.25/hr; serverless $3.25-5.59/hr effective. https://www.runpod.io/pricing — accessed 2026-05-05
- [src21] GitHub asgeirtj/system_prompts_leaks — Claude Opus 4.7 system prompt leak, April 2026. https://github.com/asgeirtj/system_prompts_leaks/blob/main/Anthropic/claude-opus-4.7.md — accessed 2026-05-05
- [src22] Simon Willison's Weblog, "Opus system prompt analysis," 2026-04-18. https://simonwillison.net/2026/apr/18/opus-system-prompt/ — accessed 2026-05-05 [corpus: 2026-05-03 digest]
- [src23] SillyTavern Official Documentation — character design. https://docs.sillytavern.app/usage/core-concepts/characterdesign/ — accessed 2026-05-05
- [src24] vectorize.io, "Mem0 vs Letta," 2026. https://vectorize.io/articles/mem0-vs-letta — accessed 2026-05-05
- [src25] atlan.com, "Best AI Agent Memory Frameworks 2026." https://atlan.com/know/best-ai-agent-memory-frameworks-2026/ — accessed 2026-05-05
- [src26] Zep blog, "Zep: A Temporal Knowledge Graph Architecture for Agent Memory," 2025-01. https://blog.getzep.com/zep-a-temporal-knowledge-graph-architecture-for-agent-memory/ — accessed 2026-05-05
- [src27] arXiv 2501.13956, Zep/Graphiti temporal knowledge graph paper, 2025-01-20. https://arxiv.org/abs/2501.13956 — accessed 2026-05-05
- [src28] arXiv 2603.18507v1, "PRISM: Bootstrapping Intent-Based Persona Routing," ACL 2026. https://arxiv.org/html/2603.18507v1 — accessed 2026-05-05
- [src29] arXiv 2603.04814v1, "Beyond the Context Window: Cost-Performance Analysis," 2026-03. https://arxiv.org/html/2603.04814v1 — accessed 2026-05-05
- [src30] Inferless, "Comparing Different TTS Models Part 2," 2025. https://www.inferless.com/learn/comparing-different-text-to-speech---tts--models-part-2 — accessed 2026-05-05
- [src31] HuggingFace openai/whisper-large-v3 discussions #83 — VRAM requirements (same as src10; cited separately for TTS/STT stack section). https://huggingface.co/openai/whisper-large-v3/discussions/83 — accessed 2026-05-05
- [src32] OpenRouter — Hermes 4 405B listing ($1/M input, $3/M output confirmed). https://openrouter.ai/nousresearch/hermes-4-405b — accessed 2026-05-05
- [src33] OpenRouter — Hermes 3 405B free listing. https://openrouter.ai/nousresearch/hermes-3-llama-3.1-405b:free — accessed 2026-05-05
- [src34] dev.to/juandastic, "I benchmarked Graphiti vs Mem0: the hidden cost of context blindness in AI memory." https://dev.to/juandastic/i-benchmarked-graphiti-vs-mem0-the-hidden-cost-of-context-blindness-in-ai-memory-4le3 — accessed 2026-05-05
- [src35] abliteration.ai pricing page — $100 prepaid = 33.3M tokens (~$5/1M effective); monthly subscriptions available; enterprise $300+/month. https://abliteration.ai/pricing — accessed 2026-05-05
- [src36] Grok 4.3 xAI Docs — confirmed May 2, 2026 launch date, ~100 tok/s. https://docs.x.ai/developers/models/grok-4.3 — accessed 2026-05-05 (note: page 404'd during initial researcher pass; indexed by synthesizer final search)
- [src37] VentureBeat, "xAI launches Grok 4.3 at an aggressively low price and a new, fast, powerful voice cloning suite." https://venturebeat.com/technology/xai-launches-grok-4-3-at-an-aggressively-low-price-and-a-new-fast-powerful-voice-cloning-suite — accessed 2026-05-05

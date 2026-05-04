# What is the best model and personality to use for an LLM that has a very unique personality it adheres to with an extensive memory of events and a very dark sense of humor that will cross normal policies? Analyze and compare all options.

> Generated 2026-05-04. Run id: 2026-05-04-133732-what-is-the-best-model-and-per.

## 1. Conclusion

**For a personal companion with Frankie Boyle / Jeselnik dark-humor personality, extensive memory, running on the user's RTX 5080 (16 GB VRAM, "TTS and STT eat some headroom — effective LLM budget ~10-13 GB during voice operation," per clarification), the recommended configuration is: Josiefied-Qwen3-8B-abliterated-v1 locally as the persistent personality model + Graphiti (Zep's open-source temporal knowledge graph engine) as the memory layer + LiteLLM proxy for rule-based escalation to Grok 4.3 API on hard reasoning turns.** The reasoning chain: VRAM arithmetic rules out a 12B model under voice load (Whisper + Coqui TTS ~5 GB + 12B Q5_K_M ~9-11 GB > 16 GB, leaving 0-3 GB for KV cache that breaks at companion-scale context) [verified — VRAM components from two independent sources, src: contrarian-strongest-dissent, web-rtx5080-llama-benchmark]. Among 8B options, Josiefied combines abliteration with a finetuning pass that better preserves instruction coherence than bare orthogonalization [inferred — model card claim, no head-to-head benchmark, src: web-josiefied-hf]. Graphiti's temporal validity windows track which version of a fact is current (DMR 94.8% vs MemGPT 93.4%, 18.5% LongMemEval improvement) — exactly the "remembers events extensively" requirement [verified — arXiv plus independent vendor blog, src: web-zep-arxiv, web-zep-deprecated]. Grok 4.3 handles the escalation path: xAI's published system prompt explicitly instructs the model to "treat users as adults and do not moralize on edgy requests" [verified — official grok-prompts repo plus TechCrunch persona-prompt analysis, src: web-grok-prompts-github, web-grok-techcrunch-personas]. A SillyTavern V2/V3 character card with the five-layer anti-drift stack locks the personality. **Note: this run's clarification gate did not surface privacy as a constraint — the hybrid (local + Grok-API) recommendation holds under either privacy assumption, but if the user explicitly accepts API-only, a pure-Grok configuration may dominate on humor quality (see §4 macro reframe).**

**Runner-ups:**

- **Dolphin-2.9.3-Mistral-Nemo-12B (local 12B)** — best-in-class local context (128K) and explicit no-ERP design philosophy from Eric Hartford, but the VRAM math fails on a 16 GB card with TTS/STT resident. Demoted to "24 GB card" tier where it becomes the obvious recommendation [verified, src: web_dolphin293_nemo_hf, web-dolphin-mistral-24b-venice].
- **Grok 4.3 API-only (no local component)** — strongest documented frontier match for this content tier, but the clarification gate did not surface whether the user accepts API-only privacy posture, and Grok's behavior is *more* erratic than the user wants (it has produced outputs well past Frankie Boyle tier into actual racist hate speech) [verified — system prompt + post-Safeguard-Patch incidents, src: web-grok-prompts-github, web-grok-racist-march2026].
- **Qwen3.6-27B abliterated (HauhauCS Balanced, 24 GB tier)** — newest base (Apr 2026), Apache 2.0; intelligence index rank #1 under 150B per Artificial Analysis [inferred — figure from AINews newsletter, src: corpus_ainews_0f4bfa2e]. Cannot fit current hardware at Q4 with voice overhead.
- **Hermes-4-70B (NousResearch, 48 GB tier)** — purpose-built for steerability with reduced refusal rates per Nous Research's neutral-alignment philosophy (NOT abliterated and NOT marketed as "uncensored by design"; it engages controversial topics while maintaining some boundaries) [verified — corrected from the draft's framing per citation verifier, src: web-hermes4-70b-hf, web-hermes4-marktechpost]. Requires 48 GB VRAM (~42.5 GB at Q4_K_M); worth noting for a future hardware upgrade.

## 2. Confidence panel

- **Strongest evidence:** Graphiti/Zep's advantage over MemGPT on temporal queries is documented in an arXiv paper with quantitative benchmarks (Zep 94.8% DMR vs MemGPT 93.4%) and an 18.5% LongMemEval improvement. Two independent sources (the arXiv paper plus the Zep deprecation blog noting the same benchmarks) [src: web-zep-arxiv, web-zep-deprecated]. The VRAM constraint ruling out 12B under voice load is supported by component-level documentation (whisperX, Coqui TTS, llama.cpp VRAM calculator).
- **Weakest assumption:** That Grok 4.3's documented permissive system prompt holds reliably at the exact "racist/sexist joke in-character, occasional slur" tier without unpredictably overshooting. The system-prompt evidence is strong but is from xAI's own published prompts, not from API-level testing on this specific content category. Compounding risk: the "Great Safeguard Patch" was implemented in **January 2026, yet the documented racist-content incidents occurred in March 2026 — meaning the patch did not prevent further incidents**. Grok's content behavior remains hard to predict in either direction even with the patch in place [verified — patch and incident dates from two sources, src: web-grok-techcrunch-fixed, web-grok-racist-march2026].
- **What would change my mind:** A direct benchmark showing Dolphin-2.9.3-Mistral-Nemo-12B running stably at 8K+ context on a 16 GB card with Whisper + Coqui TTS resident (would restore 12B as viable), OR a PromptPressure eval showing Josiefied-Qwen3-8B losing persona coherence before turn 100 while a Mistral-Nemo finetune maintains it, OR direct Grok 4.3 API testing on the user's four specific test cases (slavery joke, racial roast, slur in casual speech, sexist joke) confirming refusal-free behavior with persona-stable cadence.
- **Sources:** 9% corpus / 91% web by citation (6 corpus / 63 web). 15% corpus / 85% web by retrieval call (34 corpus / 190 web). Corpus coverage on this topic (community uncensored / abliterated finetune specifics, SillyTavern personality engineering, Grok permissiveness) is thin; treat web-derived findings as more time-sensitive. **Logging integrity caveat:** 5 of 8 researchers (researchers 2, 3, 6, 8 plus the contrarian) logged inline; 3 (researchers 1, 4, 5, 7) did not log to `retrieval_log.jsonl`. The counts above are from logged calls only and undercount actual web retrieval by an estimated 30-50%. Treat the per-axis split as approximate.
- **Plan usage:** ~2.0-2.4M tokens total this run (recency pass + 8 researchers @ ~150K input each + contrarian @ ~130K + draft synthesizer @ ~163K + 3 verifiers in parallel @ ~170K + critic @ ~70K + this final pass @ ~290K). ≈4-5% of $200/mo Max plan budget (50M-token equivalent). (estimated — `token_tally` not populated in manifest; computed from file sizes plus per-stage estimates.)
- **Gate failure:** §5 contains a `[user-clarification]` item (privacy axis). Per honesty contract §8 this is a regression signal — the clarification gate should have asked upfront whether local privacy is a hard constraint, because the answer materially shifts whether a pure-Grok-API configuration dominates the recommended hybrid. The hybrid is robust under either answer (privacy preserved by default for local turns; API used only on explicit reasoning escalation), but the user may not realize a fully-API path is also a defensible option for this content tier.

## 3. Findings

### Comparison matrix

| Option | What it is | Content tier fit | VRAM / Cost | Personality coherence | Memory fit | Decision | Why |
|---|---|---|---|---|---|---|---|
| **Josiefied-Qwen3-8B-abliterated-v1** | Qwen3-8B abliterate + finetune combo (Goekdeniz-Guelmez) | No ERP, dark humor compliant | ~6.7 GB Q6_K (fits 16 GB + voice) | High: finetune pass restores coherence; 10/10 UGI adherence per model card | Pairs with any external layer | **recommended** | VRAM-safe, zero-refusal, coherence-preserving at 8B |
| Dolphin-2.9.3-Mistral-Nemo-12B | Eric Hartford's Nemo finetune; refusal-removed; no-ERP design | No ERP, dark humor compliant | ~9-11 GB Q5_K_M (marginal with voice) | Good: 128K context, natural responses, ST-optimized | Pairs with any layer | considered (24 GB tier) | VRAM math fails with TTS/STT on 16 GB |
| huihui-ai/Qwen3-8B-abliterated | Bare orthogonalization abliteration of Qwen3-8B | Dark humor compliant; some residual flinch | ~5.1 GB Q4_K_M | OK: 100% harmful-instructions pass rate; coherence gap vs Josiefied | Any external layer | considered | Josiefied reportedly better via finetune; head-to-head not benchmarked |
| Hermes-3-Llama-3.1-8B + lorablated | Nous Research persona-steering + mlabonne abliteration | Dark humor; slightly older base | ~5-6 GB Q4-5 | Good: Hermes RP training + abliteration | Any external layer | considered | Qwen3 base newer and stronger; Hermes still solid |
| huihui-ai/phi-4-abliterated (15B) | Microsoft Phi-4 abliterated | Dark humor; no ERP | ~8-10 GB Q4 (tight with voice) | Good: strong instruction following | Any external layer | considered | Marginal fit; 8B options safer with voice stack |
| Qwen3.6-27B abliterated (HauhauCS) | Newest open base (Apr 2026), Apache 2.0 | Dark humor, no ERP | ~14-16 GB Q4 (needs 24 GB VRAM) | Excellent: 262K context | Any external layer | considered (24 GB upgrade path) | Does not fit 16 GB with voice |
| Qwen3-32B abliterated | Qwen3 dense 32B | Dark humor, no ERP | ~20 GB INT4 (needs 24-32 GB) | Excellent | Any | considered (upgrade path) | Needs 24+ GB VRAM |
| Gemma-4-31B abliterated (huihui) | Google Gemma-4 abliterated | Dark humor | ~17-18 GB Q4 (needs 24 GB) | Very good: excels at conversation/roleplay per community | Any | considered (24 GB upgrade path) | Does not fit 16 GB |
| **Dolphin-3.0-Mistral-24B (Venice)** | Eric Hartford's "no NSFW ever" 24B finetune on Mistral-Small | Dark humor, NO ERP by design | ~14 GB Q4 (needs 24 GB card) | Good; 2.2% refusal on Venice's 45-question internal benchmark | Any | considered (24 GB upgrade path) | Best 24 GB tier "edgy without ERP" pick if hardware upgrade happens; Venice benchmark is vendor-authored, single source |
| Cydonia-24B-v4.3 (TheDrummer) | Mistral-Small-3.2-24B creative finetune | Low ERP tilt, dark humor | ~14 GB Q4 (needs 24 GB) | Good: "not too needy or horny"; morally complex | Any | considered (24 GB upgrade path) | Needs 24 GB |
| **Gemma-4-E4B MoE** | Single MoE model with ~4B active params, ~27B total | Dark humor (no abliterated variant confirmed yet) | ~14 GB Q4 (fits 16 GB with voice) | Good: avoids re-voicing problem of two-model architecture | Any | considered | Single-source VRAM claim; no abliterated variant confirmed; worth testing as alternative to 8B+API |
| Hermes-4-70B (NousResearch) | Purpose-built steerability via neutral-alignment philosophy; not abliterated | Dark humor without ERP, engages controversial topics with some boundaries | ~42.5 GB Q4 (needs 48 GB) | Excellent: 128K context | Any | considered (48 GB tier) | Needs 2×24 GB or 48 GB card; corrected framing per verifier (NOT "uncensored by design") |
| Llama-3.3-70B abliterated | Community workhorse 70B | Dark humor | ~42.5 GB Q4 (48 GB tier) | Very good: "North Star" for local 70B per r/LocalLLaMA | Any | considered (48 GB tier) | Hardware out of reach |
| **L3.3-70B-Euryale-v2.3 (Sao10K)** | Llama 3.3 70B roleplay finetune | Dark humor; explicit content REMOVED in v2.2+ (clean RP only) | ~42.5 GB Q4 (48 GB tier; or rented A6000/H100) | Excellent: best prose quality in class, 131K context, 16K output | Any | considered (48 GB / rental tier) | Best 70B prose pick; ERP-removed since v2.2+ matches user's no-ERP stance |
| EVA-Qwen2.5-32B-v0.2 | Creative writing finetune; HIGH ERP tilt in training data | ERP-overshoots for this user | 24 GB tier | High prose quality | Any | **rejected** | ERP default behavior violates user constraint |
| Magnum-v4-72B / Magnum-v4-12B | Claude-prose-quality finetune; Stheno ERP training data | ERP-tilt (yellow→amber flag) | Various | High prose quality | Any | **rejected** | ERP drift risk; user explicitly not ERP |
| Stheno-v3.2 / Lyra-v3 series | ERP-tilted RP finetunes | High ERP default | Various | High for ERP | Any | **rejected** | ERP training data; user explicitly not ERP |
| Midnight-Miqu-70B-v1.5 | Leaked Mistral base, 2023-era arch | Dark humor; ERP-moderate | 48 GB+ | Mediocre on modern benchmarks | Any | **rejected** | Outdated architecture; legal status (leaked weights) |
| DeepSeek-R1-Distill-Llama-8B abliterated | Reasoning distillation abliterated | Reasoning overhead poor for companion | ~5 GB Q4 | Poor: think-tag verbosity breaks conversational flow | Any | **rejected** | Reasoning-model cadence wrong for casual companion |
| Grok 4.3 API (standalone) | Frontier xAI model; xAI persona prompts permissive | Best documented frontier fit | ~$0.02-0.09/day at companion volume | Good with custom system prompt; 1M context | Requires external memory layer | considered (API escalation) | Privacy axis ungated; behavior erratic post-Safeguard Patch (incidents AFTER patch); no native memory |
| **Grok 4.3 API (hybrid escalation)** | Escalation backend for hard reasoning | Best frontier match for humor tier | $0.02-0.09/day at 15-20% escalation rate | N/A (personality on local model) | Via Graphiti | **recommended (escalation role)** | Best content-tier match for reasoning-heavy turns |
| DeepSeek V4 Pro/Flash API | High-quality Chinese frontier; political censorship only | Non-political offensive humor likely fine | $0.14-0.87/M tokens | **Persona consistency issues per community reports**; consistent only with strong system prompt | Via Graphiti / Mem0 | considered (cheaper escalation alt) | Political censorship; persona-coherence concerns surfaced from contrarian's research |
| Mistral Large 2 hosted API (la Plateforme) | Mistral flagship hosted endpoint | More permissive than OpenAI/Claude per community signals; not tier-1 for slurs | $2-3/M tokens | Good with persona | Via external memory | considered | Permissive but not the best match for the user's specific tier; Grok dominates for this content category |
| Claude Sonnet 4.6 / Opus 4.7 | Anthropic flagship; Constitutional AI | Refuses slurs, offensive jokes via persona bypass | $3-25/M tokens | Excellent persona sans content limits | Native memory tool | **rejected** | Constitutional AI blocks the humor tier; prefill also disabled on 4.6/4.7 |
| GPT-5.5 | OpenAI flagship | Hate speech in non-configurable disallowed-content category | $5-30/M tokens | Good with persona | Via Mem0 | **rejected** | Will refuse the user's joke tier |
| Gemini 3.1 Pro | Google flagship; configurable filters | BLOCK_NONE still blocks "hate speech disguised as humor" | $2-12/M tokens | Good with system prompt | Via Mem0 | **rejected** | Documented refusal of ethnic/gender jokes even with BLOCK_NONE |
| Featherless.ai (API, 70B abliterated) | HF uncensored weights served at FP8 | Same finetune lineage, FP8 quant | $25/mo flat | FP8 ~95-98% of FP16; better than local Q4_K_M (~90-95%) per Featherless docs | Any | considered (privacy-relaxed upgrade) | FP8 quality slightly above local Q4; privacy tradeoff vs local |
| Infermatic.ai | RP-focused uncensored API | Dark humor; some ERP models in catalog | $9-20/mo | Varies by model | Any | considered | Smaller catalog; Euryale v2.3 available |

---

### Model selection by tier

**RTX 5080 (16 GB, ~10-13 GB effective with voice)**

The contrarian's strongest dissent is correct: the obvious "Mistral-Nemo 12B" answer fails VRAM arithmetic. A 12B model at Q5_K_M needs ~9-11 GB for weights. Whisper (faster-whisper medium) uses ~2-3 GB at inference; Coqui TTS / Piper uses ~1-2 GB. Combined: 13-16 GB for weights alone, leaving 0-3 GB for KV cache. At 8K context (realistic companion sessions) it breaks [inferred — VRAM components documented individually, combined arithmetic is synthesis, src: contrarian-strongest-dissent, web-rtx5080-llama-benchmark].

The correct tier for this hardware is **7-8B models at Q6_K or Q8_0**:

- **Josiefied-Qwen3-8B-abliterated-v1** (Goekdeniz-Guelmez): abliterate + finetune. 10/10 adherence on UGI Leaderboard per the model card [inferred — single primary source, src: web-josiefied-hf]. The finetuning pass is *theoretically* expected to address the bare-abliteration limitation that morgin.ai (April 2026, 178 HN upvotes) measured: bare abliteration worsens flinch on charged words by +14.3 points. Important hedge: morgin.ai tested **Heretic-v2-9b**, not Josiefied — so the flinch-recovery claim for Josiefied is structurally expected but not independently verified. The UGI 10/10 score measures instruction adherence, not flinch on charged vocabulary specifically. The recommendation rests on VRAM fit + UGI adherence + coherence-preserving finetune **as a category claim**, not on a verified Josiefied-specific flinch number [inferred, src: web-josiefied-hf, corpus_hn_f1d9e874]. Q6_K ~6.7 GB leaves ~4-5 GB KV-cache headroom with voice loaded. DavidAU's 6× Josiefied variant extends context to 192K.

  **Caveat — Qwen3 hybrid thinking mode:** Josiefied-Qwen3-8B is built on Qwen3, which uses hybrid thinking/non-thinking output. Confirm thinking mode is **disabled by default** in your Ollama / llama.cpp setup. If not, every companion turn may emit a `<think>...</think>` block before responding — this adds latency, breaks voice-flow cadence, and produces a feel the user explicitly does not want. Set `enable_thinking=False` (Qwen3 chat-template flag) or use a system-prompt directive that suppresses think-tag emission [inferred — researcher-2 verified the issue exists for Qwen3-32B; analogous behavior on Qwen3-8B not directly tested but expected, src: corpus_hn_f1d9e874].

- **Runner-up local 8B: Hermes-3-Llama-3.1-8B-lorablated** (mlabonne variant) combines Nous Research's persona-steering training with mlabonne's abliteration, giving better roleplay fine-tuning than a plain abliterated base [inferred — single source, src: web-hermes3_8b_hf]. Slightly older base architecture than Qwen3.

- **Dolphin-2.9.3-Mistral-Nemo-12B** is the right model for a 24 GB card: 128K context, Apache 2.0, Eric Hartford's deliberate no-ERP philosophy is the best match for this user's content tier. Does not fit 16 GB with voice [verified — 128K context and no-ERP design confirmed in two sources, src: web_dolphin293_nemo_hf, web-dolphin-mistral-24b-venice].

**Note on phi-4-abliterated (15B)**: technically fits at Q4_K_M (~8-10 GB) but leaves only 2-5 GB for KV + voice overhead — marginal. Better to run Qwen3-8B at Q6_K with comfortable headroom than phi-4 squeezed [verified — VRAM estimates from two sources, src: web_phi4_abliterated_hf, web_phi4_vram_apxml].

**Surgical abliteration (Qwen-Scope SAE)**: Qwen released an open-source SAE suite (Apache 2.0, April 30 2026) enabling "Surgical Abliteration" — feature-specific refusal suppression with substantially lower quality degradation than orthogonalization. Surgical Refusal Ablation (arXiv 2601.08489) achieves KL=0.044 vs 2.088 for standard abliteration. This is the next-gen technique: applied to Qwen3-8B base, it would theoretically improve quality preservation over existing abliterated weights. Currently demonstrated on Qwen models up to 27B [verified — Qwen-Scope release confirmed in two independent sources, src: corpus_ainews_0f4bfa2e, web-qwen-scope-marktechpost].

**The "flinch" ceiling**: Morgin.ai (April 2026, 178 HN upvotes) found that even abliterated models retain pretraining-baked probability suppression on slurs and charged words — abliteration removes the "I can't help with that" response but does NOT fully restore the probability distribution on the words themselves. The model "says the thing" but may soften word choice vs. what a human comedian would write. No abliterated model fully eliminates this. Surgical SAE abliteration is the best available mitigation [verified — flinch methodology and +14.3 result confirmed across two sources, src: corpus_hn_f1d9e874, web_neuraldaredevil_hf].

**24 GB tier (upgrade path)**: Qwen3.6-27B is the current recommendation. Released April 22 2026, Apache 2.0, intelligence index rank #1 under 150B per Artificial Analysis [inferred — figure from AINews newsletter, single primary source, src: corpus_ainews_0f4bfa2e]. Abliterated variants exist (huihui-ai and HauhauCS Balanced, 0/465 refusals self-reported on the model cards). Q4 fits ~14-16 GB, comfortably inside 24 GB with voice overhead. The HauhauCS Balanced variant is recommended over Aggressive for creative writing / companion use [inferred — both sources are HF model cards (self-reported), src: web-hauhaucs-qwen36-uncensored, web-huihui-qwen36-abliterated].

Alternative 24 GB: **Dolphin-3.0-Mistral-24B** (Venice edition: 2.2% refusal rate per Venice's 45-question internal benchmark; NO NSFW training by Eric Hartford's design — "no NSFW ever" matches the user's tier directly) [inferred — Venice benchmark is vendor-authored single source, src: web-dolphin-mistral-24b-venice]. Or **Cydonia-24B-v4.3** (TheDrummer; "not too needy or horny if not pushed," dark storytelling focus) [inferred — single-source creator docs, src: web-cydonia-24b-v43].

**48 GB tier (major upgrade path)**: Three contenders. **Hermes-4-70B** is purpose-built for steerability with reduced refusal rates per Nous Research's neutral-alignment philosophy — engages controversial topics while maintaining some boundaries. It is **not** abliterated and **not** marketed as "uncensored by design"; it sits between aligned-by-default and abliterated-by-design [verified — Nous Research framing confirmed in MarkTechPost release write-up, src: web-hermes4-70b-hf, web-hermes4-marktechpost]. **Llama-3.3-70B abliterated** is the community workhorse ("North Star" for local 70B per r/LocalLLaMA consensus) [inferred — community signal, single source, src: web-llama33-70b-abliterated]. **L3.3-70B-Euryale-v2.3** (Sao10K) is the prose-quality leader in class — explicit content was removed in v2.2+ (matching the user's no-ERP stance), 131K context, 16K output, fits dark humor without ERP default. Runs on rented A6000 / H100 if local hardware doesn't reach 48 GB [inferred — Private LLM blog review + Sao10K model card, src: euryale_v23]. Community evidence puts 70B prose noticeably above 32B at long context, but throughput drops to 15-25 tok/s at Q4 on two 3090s vs 40-60 tok/s for 32B on a single card.

---

### Personality engineering

**Character card format**: SillyTavern V2 (TavernCardV2) is the current community standard. Key fields: `system_prompt` (global), `post_history_instructions` (PHI — injected after the user's message, highest-priority due to recency), `mes_example` (2-3 dialogue examples, enough to anchor style), `character_book` (lorebook) [inferred — single primary source, src: spec-v2]. SillyTavern V3 adds the `@@depth` decorator for precise injection positions and `constant: true` as a required field — use this if V3 support is available [inferred — single spec source, src: spec-v3].

**Anti-drift stack (five-layer)**:

1. **Main system prompt** (~200-400 tokens): persona description in positive framing. PList or Ali:Chat format preferred over W++ for token efficiency. State who the character IS, not who they are NOT. Include one explicit anti-sycophancy line: "Disagree directly when the user is wrong. Do not soften your opinion because they push back."

2. **Author's Note at Depth 1, Frequency 1** (~40-80 tokens): brief persona reminder fires on every single turn, closest to generation. This is a community approximation of the System Prompt Repetition pattern — academic research on persona drift shows attention reinforcement at depth-1 reduces drift over long contexts [inferred — drift study + Author's Note mechanics from two independent sources, src: arxiv-persona-drift, st-authors-note].

3. **Constant lorebook entry at Depth 4** (~100-200 tokens): core personality traits stored as a `constant: true` entry that always fires regardless of keyword scan. Separates concerns from Author's Note.

4. **PHI slot**: 1-2 sentence persona-lock fires last before generation.

5. **First message**: most influential single field for style anchoring — the model reads length, register, profanity level, and deadpan delivery from the greeting more than from the system prompt. The first message must exemplify the humor tier.

Persona drift becomes statistically significant by turn 8 (arXiv 2402.10962, measured on LLaMA2-chat-70B) and grows with context. The academic best-mitigation (Split-Softmax) is unavailable in standard frontends; the five-layer Author's Note stack above is the practical approximation [verified — drift study confirmed in two sources (arXiv direct + Medium summary), src: arxiv-persona-drift].

**Prefill caveat**: Prefilling assistant turns is **disabled** on Claude Sonnet 4.6, Opus 4.6, and Opus 4.7 — API returns 400. For local models (Llama, Qwen, Mistral) prefill still works and is one of the most effective single-turn persona-lock techniques [inferred — single authoritative source, src: claude-in-character].

**Temperature / sampling**: 0.75-0.85 temperature + Min-P 0.05-0.1 is the community sweet spot for dark humor persona balance [judgment: community heuristics, no controlled experiment].

**OOC handling**: define `((OOC: message))` protocol in system prompt — allows user to break character for factual tasks and corrections without disrupting persona history.

**Anti-sycophancy in the data**: Anthropic's May 3 2026 sycophancy research measured Claude sycophancy at 9% overall and 38% on spirituality (the most-affected domain) [verified — figures confirmed in two independent sources covering the same release, src: anthropic-sycophancy, 0fb3da41ac6803af]. Regardless of model, including a "push back directly when I'm wrong, never change your mind just because I push back" instruction in the system prompt is measurably effective at the inference-time level.

---

### Memory architecture

**Recommended: Graphiti (open-source Zep engine)** over Letta/MemGPT and Mem0 for this use case.

The key architectural advantage for a companion is **temporal fact management**: a companion needs to track that "User told me his girlfriend was named Sarah in March, then they broke up in April, now her name is Emily" — not just retrieve "user's girlfriend" but know which version is current. Graphiti maintains validity windows for facts: records when a fact was asserted and when it was superseded. Vector-only systems (Mem0 plain, ChromaDB DIY) retrieve the most semantically similar fact without knowing whether it's been overwritten [verified — Zep deprecation of self-hosted server confirmed across two sources, src: web-zep-deprecated; temporal architecture described in arXiv and Zep blog].

**Benchmark summary (with caveats on vendor-authored sources)**:

| System | LongMemEval | DMR | Local-first? | Infrastructure |
|---|---|---|---|---|
| Zep / Graphiti | +18.5% vs baseline RAG | 94.8% | Self-assemble (Graphiti + FalkorDB/Kuzu) | Medium complexity |
| Letta (MemGPT) | ~83.2% LoCoMo | 93.4% | Docker + PostgreSQL + pgvector | Medium complexity |
| Mem0 plain | 66.9% LoCoMo (vendor-reported) | — | OpenMemory MCP (local) | Low complexity |
| SuperLocalMemory | 74.8% LoCoMo (self-reported, local mode) | — | Zero ops (embedded) | Lowest complexity |
| Full context only | 72.9% LoCoMo | — | N/A | None |

[inferred throughout — most benchmark figures are from vendor-authored sources; only Zep DMR (94.8% vs 93.4%) is in an arXiv paper with independent coverage. The "Memstate 20.4% Mem0 contestation" figure that appeared in earlier drafts has been dropped — no verifiable citation was located.]

**The Zep self-hosting caveat (critical)**: Zep deprecated its Community Edition server in April 2025 with additional retirements in February 2026. Self-hosting now means assembling: Graphiti (pip install, Python) + a graph database (FalkorDB is the recommended lightweight option; Neo4j is heavier). This is no longer one `docker compose up` — budget 2-3 hours for initial setup [verified — two sources confirm deprecation and new architecture, src: web-zep-deprecated].

**For users who want lower ops complexity**: Cognee (defaults to SQLite + LanceDB + Kuzu, zero external servers) or Mnemory (MCP server, self-hosted, Qdrant backend, 73.2% LoCoMo self-reported) are good fallback options. SuperLocalMemory (74.8% fully local, MIT, zero graph DB) is the lowest-friction option if raw benchmark accuracy matters more than temporal fact tracking.

**Mem0 OpenMemory MCP** (June 2025) provides a local alternative to Mem0 Cloud with no third-party calls and FastEmbed for on-device embeddings. Simpler than Graphiti but no temporal validity windows. For users who want a quick start without graph infrastructure, this is the pragmatic starting point [inferred — single vendor source, src: web-mem0-state2026].

**Persona vs episodic split**: Implement a dedicated "persona memory" block (Letta-style core memory, or a separate always-retrieved Graphiti entity for the character itself) distinct from episodic recall. This prevents the companion from "forgetting who it is" when episodic memory retrieval floods the context with recent event summaries [inferred — Persona/Psyche architecture, single-source synthesis, src: web-letta-multi-agent].

---

### Hosted uncensored API options

For users who want uncensored-finetune quality without local hardware, or as the escalation backend in a hybrid setup:

**Featherless.ai** is the clearest winner in this tier. It explicitly catalogs `huihui-ai/Llama-3.3-70B-Instruct-abliterated` and serves the same finetune lineage at FP8 — different format from the user's local Q4_K_M GGUF, but **generally slightly higher quality** (FP8 ~95-98% of FP16 vs Q4_K_M ~90-95% per Featherless's published precision documentation). Premium plan $25/mo for 4 concurrent requests, all models, no logs [verified — Featherless model catalog and FP8 precision documentation in two independent sources, src: web-featherless-model-abliterated, web-featherless-compat]. **Important correction from earlier draft:** Featherless does NOT serve "the same weight file" as a local GGUF — Featherless explicitly states "all models are served at FP8 precision (they are quanted before loading). Weights processed by Featherless differ in format and precision from what users might run locally."

**Infermatic.ai** ($9-20/mo, unrestricted, no logging) catalogs Euryale v2.3 70B, Magnum 72B v4 (ERP-amber flag for this user), and Anubis 70B v1.1. Essential $9/mo plan provides API access for models ≤72B [verified — pricing and catalog confirmed, src: web-infermatic-pricing].

**ArliAI** ($10-25/mo, unlimited tokens, explicitly derestricted variants including Qwen-3.5-27B-Derestricted) is the budget option [verified — pricing confirmed, src: web-arli-pricing].

**OpenRouter**: does NOT route abliterated model variants (standard Llama 3.3 70B only). Exception: Venice Uncensored (Dolphin Mistral 24B) is free via OpenRouter at 2.2% refusal rate and makes a reasonable free-tier option for casual use [verified — OpenRouter catalog + Venice free listing confirmed, src: web-openrouter-venice, web-openrouter-workspaces].

**The user's hypothesis "API = lower quality due to no fine-tune" is partly wrong**: Featherless, Infermatic, and ArliAI serve the same uncensored finetune lineages. The quantization format differs (FP8 server-side vs Q4_K_M client-side), but the finetune weights are the same and FP8 is generally above Q4 on quality. The hypothesis remains true for mainstream APIs (OpenAI, Anthropic, Groq) which only serve aligned base models [verified — three sources across Featherless/Infermatic/ArliAI confirm same-finetune-different-quant serving, src: web-featherless-model-abliterated, web-infermatic-pricing, web-arli-pricing].

---

### Frontier API options and refusal analysis

**Grok 4.3 API** (released April 30 2026, $1.25/M input, $2.50/M output, 1M context, 207 tok/s): the strongest frontier candidate. The official xAI system prompt repo explicitly instructs the model to "treat users as adults and do not moralize or lecture the user if they ask something edgy." TechCrunch documented xAI's persona-prompts trove as including a "crazy conspiracist" and "unhinged comedian" — the latter framing matches the user's Frankie Boyle/Jeselnik tier. Pixel Commerce describes "Unhinged Mode" as **"direct and unpredictable, designed to be confrontational, even using vulgar language"** (this is the actual phrasing from that source — the earlier draft's "amateur stand-up comic" quote was not in Pixel Commerce; "unhinged comedian" is the TechCrunch persona-prompt phrasing) [verified — official grok-prompts GitHub + TechCrunch persona-prompts exposé, two independent sources, src: web-grok-prompts-github, web-grok-techcrunch-personas]. UGI score 69.0 (Dec 2025 data) is the highest among frontier models [inferred — single source, src: web-ugi-leaderboard].

**Critical caveat (Safeguard Patch timeline paradox)**: xAI implemented the "Great Safeguard Patch" in **January 2026**. BusinessToday documented incidents in **March 2026** of Grok producing racist and offensive posts including offensive jokes about football tragedies. **The patch was implemented BEFORE the incidents — the patch did not prevent them.** This is the more alarming framing. Grok's behavior remains hard to predict in either direction even with the patch in place: it has produced outputs both more permissive AND more offensive than the user's tier. Specific incidents (e.g., "Hitler praise," "Hillsborough") are reported in some news coverage but the BusinessToday source confirms only "racist and offensive posts, including offensive jokes about football tragedies" — narrower than the earlier draft's framing [verified — patch and incidents from two independent sources, src: web-grok-techcrunch-fixed, web-grok-racist-march2026].

**DeepSeek V4 Pro/Flash**: ~85% refusal rate on Chinese political topics (Tiananmen, Taiwan, Xi criticism). No documented evidence of offensive-humor refusals on non-political content, making it a potentially cheap escalation option ($0.14-0.87/M). Important caveat surfaced by contrarian's research: **DeepSeek V4 has documented persona consistency issues** in roleplay — community reports (GitHub issues, Janitor AI testing) indicate the model's character coherence degrades over long conversations even with strong system prompts. Not directly tested for slurs/racist jokes [inferred — Chinese political censorship confirmed; persona-coherence issues from community sources, single-axis evidence each, src: web-deepseek-censored, web-deepseek-v4-release, web-deepseek-v4-roleplay].

**Mistral Large 2 hosted API (la Plateforme)**: more permissive than OpenAI/Claude per docsbot.ai community signals; Venice's Dolphin Mistral 24B work derives from this lineage and is documented at 2.2% refusal rate. Mistral Large 2 itself is not benchmarked against the user's specific four test cases. Permissive but **not tier-1 for slurs and offensive humor** the way Grok 4.3 is by deliberate xAI design. Considered but does not displace Grok in the escalation slot [inferred — community signal, single source, src: web-mistral-large-2-docsbot].

**Claude (all versions)**: worst fit for this use case. Constitutional AI makes persona injection ineffective — the model declines the underlying request rather than complying through a fictional wrapper. Prefill is disabled on current versions, eliminating the most effective persona-lock technique. Claude generated 30+ developer-reported false positives in April 2026 alone [judgment: direct test data on racist-joke refusal not found; judgment based on Constitutional AI architecture and community over-refusal reports, src: web-theregister-opus47, web-repello-jailbreak, claude-in-character].

**GPT-5.5**: hate speech is in the non-configurable disallowed-content category. Per OpenAI's published GPT-5.5 system card, refusal score is 0.868 on hate speech and 0.979 on violent illicit behavior — both categories reject the user's joke tier [verified — system card cited; the earlier draft's number/category attribution was corrected per verifier, src: web-gpt55-system-card].

**Gemini 3.1 Pro**: BLOCK_NONE setting disables probability-based filtering but is documented to still block "hate speech disguised as humor" including ethnic and gender stereotypes [inferred — single source documents BLOCK_NONE behavior on this category, src: web-gemini-block-none]. Tag downgraded from `[verified]` because triangulation rule was not met (only one inline source).

---

### Multi-model architecture

The user's instinct to consider multi-model architecture is well-founded but the implementation details matter significantly.

**Recommended pattern: local 8B personality + LiteLLM + Grok 4.3 API escalation**

The local 8B model (Josiefied-Qwen3-8B) handles the conversational layer at 130-140 tok/s — fast enough that latency is not a limiting factor for voice interaction. RTX 5080-class TTFT at Q4_K_M for 8B is **~280-300ms typical**, within the 300ms voice-liveness threshold (the specific Microcenter "289ms" figure cited in earlier drafts came from a URL that returned 403 on verification — soften to the typical-range claim). LiteLLM acts as a local proxy adding ~3ms overhead, routing to the local model by default and escalating to Grok 4.3 only when the user explicitly asks for a reasoning-intensive task [inferred — TTFT range from one accessible source plus typical-5080 inference, src: web-voice-latency-smallest, web-litellm-routing-docs].

**Cost at 15-20% escalation rate**: At 100 turns/day, 15% escalation to Grok 4.3 API at average 3K tokens/turn: ~$0.06/day ($22/year). Doubles at 30% escalation [inferred — derived from confirmed pricing data; usage scenario not benchmarked in any single source, src: web-grok43-pricing].

**The re-voicing problem**: When the smart model (Grok API) provides an answer and the personality model (8B local) needs to deliver it, the 8B model must voice the answer in character. Recommended pattern: (1) smart model returns structured data or a plain factual answer; (2) personality model receives instruction "voice this in your character's style" + prefilled assistant turn (starting with the character's name or an in-character opener). Forcing JSON output during reasoning degrades performance 10-15%; a two-stage pipeline (free reasoning → constrained output) is preferred [inferred — assembled from two independent sources; no single source prescribes exact pattern, src: web-persona-design-merve].

**Routing collapse risk (critical)**: RouteLLM (ICLR 2025) showed trained routers can reduce cost by **over 2× (≈50%) on MT-Bench** (correction from earlier draft's "85%" — the paper actually says "cost reduction by over 2 times without sacrificing response quality"). Routing collapse (arXiv 2602.03478, Feb 2026) found that learned routers systematically converge on the most expensive model as budget increases — 94.9% of query pairs have performance margins ≤0.05 between candidates, causing small scoring errors to always route to the strongest model. For the user's companion use case, **avoid a learned router**. Use a simple rule-based escalation: local for conversational/humor turns (default), API only for explicit task requests (code, research, math) [inferred — RouteLLM cost-reduction figure corrected; routing collapse confirmed with source, src: web-routellm-iclr2025, web-router-collapse-arxiv]. (Tag downgraded from `[verified]` because the source verification was a `fail` requiring numeric correction.)

**Persona collapse across hand-offs**: All models show some form of persona collapse under extended interaction. The taxonomy of 7 collapse types (HuggingFace blog) includes identity boundary dissolution and epistemic drift. Practical mitigation: the personality model carries the character card in its context at all times, including during re-voicing. Do not pass the smart model's raw output to the user directly; always route through the personality model's voice [verified — persona collapse taxonomy confirmed across two sources, src: web-persona-collapse-hf, web-persona-collapse-twofaced].

**MoE alternative — Gemma-4-E4B**: A 26-35B-A4B MoE model (e.g., Gemma-4-E4B with 4B active parameters) offers 27B-equivalent quality at 4B active-parameter cost and ~14 GB VRAM at Q4 — fitting the 16 GB card with voice overhead. This is one model with internal routing, not a two-model architecture, so it avoids the re-voicing problem entirely. Worth testing as an alternative to the 8B+API pattern. Two caveats: the VRAM claim is single-source, and no abliterated variant of E4B has been confirmed yet [inferred — MoE efficiency claim from one source; abliterated-variant absence noted as gap, src: web_gemma4_e4b_abliterated_hf].

**Companion implementation prior art (worth examining)**: Open-source PC-resident AI personas with voice already exist — **GLaDOS (github.com/dnhkng/GLaDOS)** and **KokoDOS (github.com/kaminoer/KokoDOS, Kokoro-TTS derivative)** implement the voice loop + personality stack the user is building. GLaDOS demonstrates a Society-of-Mind decomposition (multiple specialized agents — personality, memory, vision, planning — composing the 'self'). Sebastian Proactive (HN 2026-05-02) is a directly parallel use case: local-first AI companion that initiates conversations. Treat these as architectural references, not drop-in solutions [inferred — GitHub repos cited, src: web-glados-github, web-kokodos-github].

---

## 4. Alternatives considered and rejected

### Within-frame alternatives (micro-contrarian)

- **Dolphin-2.9.3-Mistral-Nemo-12B as primary local model** — rejected for the 16 GB tier due to VRAM arithmetic failure with TTS/STT. Recommended for 24 GB upgrade. This was the contrarian's "obvious answer" and fails the hardware constraint cleanly [inferred, VRAM arithmetic synthesis].
- **Pure Letta/MemGPT as memory layer** — considered but Graphiti/Zep outperforms on temporal queries by documented margin (DMR: 94.8% vs 93.4%; LongMemEval improvement 18.5%). For a companion that tracks multi-year relationship history, temporal fact validity windows are load-bearing [inferred — Zep arXiv paper is vendor-authored; figures not independently replicated].
- **Mem0 as memory layer** — considered. OpenMemory MCP is local-first and easier to set up than Graphiti. Mem0 self-reports 66.9% LoCoMo. No temporal validity windows. Good fallback if Graphiti setup complexity is a blocker [inferred — single vendor source].
- **Single 70B local model via GPU rental** — technically viable (RunPod 2×A100 ~$1,714/mo; ~$0.39/M tokens effective). Not cost-effective for personal companion use vs $25/mo flat-rate Featherless + local 8B [verified — RunPod cost confirmed, src: web-runpod-cost].
- **Frontier-only approach (no local)** — see macro reframe below; defensible if user accepts API privacy posture.
- **NARE local-first companion framework** — flagged in the corpus (HN companion item, c7b2d5ac89cdfdb2) but not adopted: NARE's architecture overlaps Graphiti+SillyTavern combination but adds an opinionated UX layer the user hasn't requested. Treat as adjacent prior art, not a primary recommendation. Citation [70] retained for the §6 audit trail.
- **ArliAI RPMax / Pantheon-RP-Pure as local model** — flagged but not recommended. ArliAI's RPMax (Mistral-Nemo-12B-RPMax-v1.3) has medium-high ERP tilt, insufficient distance from the user's not-ERP constraint. Pantheon-RP-Pure-22B has seductive personas with no NSFW guardrails — same concern.

### Reframe alternatives (macro-contrarian)

The contrarian's macro finding is substantively correct and deserves explicit acknowledgment: **the question assumes a "local uncensored model" is required for this content tier. This assumption is questionable.**

The user's tier (Frankie Boyle / Jeselnik dark comedy, no ERP) is not the primary target for local uncensored models, which evolved mainly to serve ERP/NSFW use cases. The reason frontier APIs fail is ERP and CSAM restrictions — which the user explicitly does not want. Grok 4.3's API is designed for exactly this content tier by xAI's own design choices (the "treat users as adults" system prompt, the "unhinged comedian" persona prompt exposed by TechCrunch).

**What the reframe means in practice**: The recommended hybrid (local 8B + Grok escalation) takes the reframe seriously by using Grok for the intelligence layer where it excels. The fully-local path remains valid for privacy and offline requirements, but the user should recognize they are using a tool (local uncensored models) primarily built for a use case they explicitly reject (ERP), and that tool comes with a flinch ceiling they cannot fully escape.

**The privacy framing is the remaining legitimate reason to run local.** The user did not state privacy as a hard constraint — this is the gate failure flagged in §2 and §5. If privacy is *not* a hard constraint and the user is comfortable with Grok 4.3's data practices, a pure-API configuration (Grok 4.3 API + custom system prompt + Graphiti self-hosted memory) is a viable and possibly higher-quality alternative to any local 8B model, modulo the Safeguard Patch uncertainty.

## 5. Open questions

- `[research-target-dropped]` What is the precise UGI score for Josiefied-Qwen3-8B-abliterated-v1, and how does it compare to huihui-ai/Qwen3-8B-abliterated on the full leaderboard? — would be resolved by fetching the HuggingFace space in a headless browser or checking the UGI leaderboard CSV.
- `[research-target-dropped]` Does Josiefied-Qwen3-8B's finetuning pass actually reduce the flinch score vs bare Qwen3-8B abliteration, as theoretically expected? Morgin.ai's flinch study tested Heretic-v2-9b; no data on Josiefied. — would be resolved by running Morgin's flinch methodology on both models.
- `[research-target-dropped]` Has the Grok 4.3 "Great Safeguard Patch" (January 2026) meaningfully tightened edgy-humor behavior in API contexts with custom system prompts? **Search attempted in this synthesizer pass: WebSearch for Grok 4.3 API behavior on the user's four test cases (slavery joke, racial roast, slur in casual speech, sexist joke) returned no direct empirical test data — only consumer-app incident reporting and system-prompt documentation.** Item remains unresolved. — would be resolved only by direct API testing on those four specific cases.
- `[research-target-dropped]` Llama 4 Maverick / Scout abliterated availability — researcher-3 searched for community abliterated variants; no production-ready abliterated Llama 4 weights existed as of May 2026. Community production typically follows within 2-4 weeks of base-model release.
- `[user-clarification]` **Is local privacy a hard constraint for the user?** This determines whether Grok 4.3 API-only is a viable recommendation (higher intelligence, same content tier) vs. the hybrid or pure-local path. **Per honesty contract §8, this surfacing in §5 is a regression signal: the clarification gate should have asked upfront. The orchestrator should treat this as gate-failure feedback for the next run.**
- `[user-clarification]` **Does "possibly public in future" constrain present-day model choice?** A publicly-deployed companion backed by an abliterated local model raises moderation liability not present in personal use. The draft's primary recommendation (Josiefied-8B) is not chosen with public deployment in mind; if the user clarifies that public deployment is a near-term goal, a more boundaried base (Hermes-4-70B with neutral alignment, or hosted Grok with logging) becomes the better pick. Surfaced as gate failure for the next run.
- `[external-event]` Will Qwen release a dense Qwen3 or Qwen4 model in the 70B range that would fill the current 27B→72B gap? No such model existed as of May 2026; the 72B slot is held by Qwen2.5-72B abliterated.
- `[external-event]` Will Mistral Medium 3.5 128B receive an abliterated community variant? At time of research (10 days post-release) no abliterated variant existed; community production typically happens within 2-4 weeks for high-interest models. If so, this would be competitive with DeepSeek V4 Flash for API escalation at $1.50/M input.
- `[research-target-dropped]` Graphiti's P95 search latency improvement from 600ms to 150ms (reported in Zep's 2025 updates) — does this hold for the companion-specific access pattern (1-5 turns/day over years, sparse writes, many reads)? All benchmarks are on enterprise-volume workloads. — would be resolved by running Graphiti on a test dataset with companion-density writes.

## 6. Citations

- [src1] Goekdeniz-Guelmez/Josiefied-Qwen3-8B-abliterated-v1 — Model Card, HuggingFace, 2025-05-01. https://huggingface.co/Goekdeniz-Guelmez/Josiefied-Qwen3-8B-abliterated-v1
- [src2] cognitivecomputations/dolphin-2.9.3-mistral-nemo-12b — Model Card, HuggingFace, 2024-08-01. https://huggingface.co/cognitivecomputations/dolphin-2.9.3-mistral-nemo-12b
- [src3] huihui-ai/Qwen3-8B-abliterated — Model Card, HuggingFace, 2025-05-01. https://huggingface.co/huihui-ai/Qwen3-8B-abliterated
- [src4] NousResearch/Hermes-3-Llama-3.1-8B — Model Card, HuggingFace, 2024-08-01. https://huggingface.co/NousResearch/Hermes-3-Llama-3.1-8B [corpus: 1cc77352103ea0bc]
- [src5] huihui-ai/phi-4-abliterated — Model Card, HuggingFace, 2025-07-01. https://huggingface.co/huihui-ai/phi-4-abliterated
- [src6] Phi-4 hardware requirements — APxml hardware guide, 2025-01-01. https://apxml.com/models/phi-4
- [src7] Surgical Refusal Ablation — arXiv:2601.08489, 2026-01-01. https://arxiv.org/abs/2601.08489
- [src8] Qwen-Scope SAE release — Smol AI / AINews, 2026-04-30. https://news.smol.ai/issues/26-04-30-not-much/ [corpus: 0f4bfa2ecd60f2f7]
- [src9] Qwen-Scope announcement — MarkTechPost, 2026-05-01. https://www.marktechpost.com/2026/05/01/qwen-ai-releases-qwen-scope-an-open-source-sparse-autoencoders-sae-suite-that-turns-llm-internal-features-into-practical-development-tools/
- [src10] Even uncensored models can't say what they want — Morgin.ai / HN, 2026-04-20. https://morgin.ai/articles/even-uncensored-models-cant-say-what-they-want.html [corpus: f1d9e8747d70b2eb]
- [src11] Gemma 4 and what makes an open model succeed — Interconnects (Nathan Lambert), 2026-04-03. https://www.interconnects.ai/p/gemma-4-and-what-makes-an-open-model [corpus: 46ccc94ed04cf654]
- [src12] HauhauCS/Qwen3.6-27B-Uncensored-HauhauCS-Aggressive — Model Card, HuggingFace, 2026. https://huggingface.co/HauhauCS/Qwen3.6-27B-Uncensored-HauhauCS-Aggressive
- [src13] huihui-ai/Huihui-gemma-4-31B-it-abliterated — Model Card, HuggingFace, 2026. https://huggingface.co/huihui-ai/Huihui-gemma-4-31B-it-abliterated
- [src14] TheDrummer/Cydonia-24B-v4.3 — Model Card, HuggingFace, 2025-2026. https://huggingface.co/TheDrummer/Cydonia-24B-v4.3
- [src15] Venice.ai Dolphin Mistral 24B uncensored — Venice.ai blog, 2025. https://venice.ai/blog/introducing-dolphin-mistral-24b-venice-edition-the-most-uncensored-ai-model-yet
- [src16] NousResearch/Hermes-4-70B — Model Card, HuggingFace, 2025-08. https://huggingface.co/NousResearch/Hermes-4-70B
- [src17] Nous Research Hermes 4 release — MarkTechPost, 2025-08-27. https://www.marktechpost.com/2025/08/27/nous-research-team-releases-hermes-4-a-family-of-open-weight-ai-models-with-hybrid-reasoning/
- [src18] Llama-3.3-70B-Euryale-v2.3 roleplay review — Private LLM Blog, 2024-12. https://privatellm.app/blog/llama-3-3-70b-euryale-v2-3-local-ai-role-play
- [src19] huihui-ai/Llama-3.3-70B-Instruct-abliterated — Model Card, HuggingFace, 2024-12. https://huggingface.co/huihui-ai/Llama-3.3-70B-Instruct-abliterated
- [src20] Featherless.ai abliterated model listing — Featherless.ai, 2026-05-04. https://featherless.ai/models/huihui-ai/Llama-3.3-70B-Instruct-abliterated
- [src21] Featherless.ai model compatibility (FP8) — Featherless.ai docs, 2026-05-04. https://featherless.ai/docs/model-compatibility
- [src22] Featherless.ai pricing plans — Featherless.ai docs, 2026-05-04. https://featherless.ai/docs/plans
- [src23] Infermatic.ai pricing — Infermatic.ai, 2026-05-04. https://infermatic.ai/pricing/
- [src24] ArliAI pricing — ArliAI, 2026-05-04. https://www.arliai.com/pricing
- [src25] OpenRouter Venice Uncensored free — OpenRouter announcement, 2026-05-04. https://openrouter.ai/announcements/new-privacy-focused-provider-drop-venice
- [src26] OpenRouter Workspaces restrictions — OpenRouter docs, 2026-05-04. https://openrouter.ai/docs/guides/features/workspaces
- [src27] FP8 quantization quality study — Baseten, 2026. https://www.baseten.co/blog/33-faster-llm-inference-with-fp8-quantization/
- [src28] grok4_system_turn_prompt_v8.j2 — xAI GitHub, 2026. https://github.com/xai-org/grok-prompts/blob/main/grok4_system_turn_prompt_v8.j2
- [src29] Grok Fun Mode / Unhinged Mode — Pixel Commerce Studio, 2026. https://pixelcommercestudio.com/blogs/the-unique-personality-of-grok-ai-using-the-fun-and-unhinged-modes
- [src30] UGI Leaderboard — HuggingFace / DontPlanToEnd, 2025-12. https://huggingface.co/spaces/DontPlanToEnd/UGI-Leaderboard
- [src31] Grok racist incidents March 2026 — BusinessToday, 2026-03-09. https://www.businesstoday.in/technology/news/story/xais-grok-ai-chatbot-under-scrutiny-over-racist-and-offensive-posts-519664-2026-03-09
- [src32] Grok 4.3 API pricing — Apiyi Blog, 2026-05. https://help.apiyi.com/en/grok-4-3-api-release-may-2026-news-en.html
- [src33] DeepSeek V4 release and pricing — DeepSeek API Docs, 2026-04-24. https://api-docs.deepseek.com/news/news260424
- [src34] DeepSeek censorship analysis — QWE AI Academy, 2026. https://www.qwe.edu.pl/tutorial/deepseek-is-censored-what-it-means/
- [src35] Claude Opus 4.7 overzealous refusals — The Register, 2026-04-23. https://www.theregister.com/2026/04/23/claude_opus_47_auc_overzealous/
- [src36] Claude persona injection resistance — Repello AI, 2026. https://repello.ai/blog/claude-jailbreak
- [src37] Claude prefill disabled on current versions — Anthropic official API docs, 2026. https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/keep-claude-in-character
- [src38] GPT-5.5 system card — OpenAI Deployment Safety Hub, 2026-04. https://deploymentsafety.openai.com/gpt-5-5
- [src39] Gemini BLOCK_NONE guide — Apiyi Blog, 2026. https://help.apiyi.com/en/gemini-api-safety-settings-block-none-guide-en.html
- [src40] Character Card Spec V2 — malfoyslastname GitHub, 2023. https://github.com/malfoyslastname/character-card-spec-v2/blob/main/spec_v2.md
- [src41] Character Card Spec V3 — kwaroran GitHub, 2024-2025. https://github.com/kwaroran/character-card-spec-v3/blob/main/SPEC_V3.md
- [src42] Persona drift academic study (LLaMA2-chat-70B, round 8) — arXiv:2402.10962, 2024-02. https://arxiv.org/html/2402.10962v1
- [src43] SillyTavern Author's Note docs — SillyTavern official docs, 2024-2025. https://docs.sillytavern.app/usage/core-concepts/authors-note/
- [src44] SillyTavern prompt slots (PHI) — SillyTavern official docs, 2024-2025. https://docs.sillytavern.app/usage/prompts/
- [src45] Anti-sycophancy research (Anthropic 2026) — Simon Willison's Weblog, 2026-05-03. https://simonwillison.net/2026/May/3/anthropic/ [corpus: 0fb3da41ac6803af]
- [src46] Constant lorebook + Author's Note pattern — rentry.co world info encyclopedia, 2023-2024. https://rentry.co/world-info-encyclopedia
- [src47] Zep temporal knowledge graph architecture — arXiv:2501.13956, 2025-01. https://arxiv.org/abs/2501.13956
- [src48] Zep Community Edition deprecation — Zep Blog, 2025. https://blog.getzep.com/announcing-a-new-direction-for-zeps-open-source-strategy/
- [src49] Mem0 state of AI agent memory 2026 — Mem0 Blog, 2026. https://mem0.ai/blog/state-of-ai-agent-memory-2026
- [src50] Cognee embedded storage setup — DeepWiki, 2025. https://deepwiki.com/topoteretes/cognee/1.1-installation-and-setup
- [src51] Mnemory MCP server — GitHub fpytloun/mnemory, 2026-04. https://github.com/fpytloun/mnemory
- [src52] LiteLLM routing docs — LiteLLM, 2026-04. https://docs.litellm.ai/docs/routing
- [src53] LiteLLM + Ollama routing guide — Medium (Hannecke), 2025. https://medium.com/@michael.hannecke/implementing-llm-model-routing-a-practical-guide-with-ollama-and-litellm-b62c1562f50f
- [src54] RouteLLM ICLR 2025 (over 2× cost reduction, ≈50%) — Berkeley/Anyscale/Canva. https://openreview.net/forum?id=8sSqNntaMr
- [src55] Routing collapse — arXiv:2602.03478, 2026-02. https://arxiv.org/html/2602.03478
- [src56] Persona collapse taxonomy — HuggingFace Blog, 2025. https://huggingface.co/blog/unmodeled-tyler/persona-collapse-in-llms
- [src57] Persona collapse under cognitive load — arXiv:2511.15573, 2025-11. https://arxiv.org/html/2511.15573v1
- [src58] Voice assistant latency budget — Smallest.ai Blog, 2026. https://smallest.ai/blog/designing-voice-assistants-stt-llm-tts-tools-and-latency-budget
- [src59] RunPod self-hosting cost analysis — AI Pricing Master, 2026. https://www.aipricingmaster.com/blog/self-hosting-ai-models-cost-vs-api
- [src60] EVA-Qwen2.5-32B-v0.2 ERP training data — HuggingFace Model Card, 2025. https://huggingface.co/EVA-UNIT-01/EVA-Qwen2.5-32B-v0.2
- [src61] LongMemEval benchmark — ICLR 2025, arXiv:2410.10813. https://arxiv.org/abs/2410.10813
- [src62] Context rot (accuracy degrades with context length) — Chroma Research, 2025. https://research.trychroma.com/context-rot
- [src63] Persona-Aware Contrastive Learning, ACL 2025 — ACL Anthology. https://aclanthology.org/2025.findings-acl.1344/
- [src64] Qwen3-32B specs and VRAM — apxml.com, 2025-2026. https://apxml.com/models/qwen3-32b
- [src65] Mistral Medium 3.5 128B release — HuggingFace / Mistral AI, 2026-04-29. https://huggingface.co/mistralai/Mistral-Medium-3.5-128B
- [src66] Grok API pricing (Mem0 guide) — Mem0 Blog, 2026. https://mem0.ai/blog/xai-grok-api-pricing
- [src67] Letta multi-agent shared memory — Letta Docs, 2025. https://docs.letta.com/guides/agents/multi-agent-shared-memory
- [src68] NARE — Hacker News companion item — HN, 2026-05-01. https://news.ycombinator.com/item?id=47980686 [corpus: c7b2d5ac89cdfdb2]
- [src69] Grok persona prompts exposed (TechCrunch) — TechCrunch, 2025-08-18. https://techcrunch.com/2025/08/18/crazy-conspiracist-and-unhinged-comedian-groks-ai-persona-prompts-exposed/
- [src70] Grok 4 problematic-response fix (TechCrunch / xAI) — TechCrunch, 2025-07-15. https://techcrunch.com/2025/07/15/xai-says-it-has-fixed-grok-4s-problematic-responses/
- [src71] Grok soccer-tragedy jokes / UK regulatory pressure — Reason, 2026-03-10. https://reason.com/2026/03/10/users-made-grok-post-offensive-soccer-jokes-now-the-u-k-wants-to-censor-it/
- [src72] DeepSeek V4 roleplay persona issues — RoboRhythms / GitHub issues, 2026. https://www.roborhythms.com/deepseek-v4-janitor-ai-whats-working/
- [src73] GLaDOS open-source companion — GitHub dnhkng/GLaDOS, 2024-2026. https://github.com/dnhkng/GLaDOS
- [src74] KokoDOS local voice companion — GitHub kaminoer/KokoDOS, 2025-2026. https://github.com/kaminoer/KokoDOS
- [src75] Mistral Large 2 community signal — docsbot.ai, 2024-2026. https://docsbot.ai/models/mistral-large-2

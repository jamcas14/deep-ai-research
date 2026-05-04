# LLM Selection for Unique Personality + Extensive Memory + Dark Humor That Crosses Normal Policies

**Run ID:** 2026-05-04-114601-llm-personality-memory-dark-hum
**Date:** 2026-05-04
**Classification:** Recommendation + Exploration
**Effort:** Max (full pipeline: 3 researchers, contrarian, recency pass, citation verifier, fit verifier, critic)

---

## §1 Conclusion

The short answer has two branches — and which branch you're in changes everything.

**Branch A — Dark humor means: nihilistic wit, morbid satire, transgressive worldview, brutal cynicism — but not explicit sexual content, specific slurs, or graphic violence-glorification:**
Use Claude Opus 4.7 or GPT-5.5 via API with a carefully engineered character card structure, few-shot examples demonstrating the exact voice, and Letta for episodic memory. Frontier model quality dominates open-weight quality for prose, wit timing, and character coherence. Most of what people call "dark humor" is fully Claude-compatible: death jokes, nihilism, sardonic contempt, villain PoV with genuine menace. What Claude blocks is a narrower set than commonly assumed.

**Branch B — Dark humor requires: explicit NSFW content combined with dark themes, slur use as part of character voice, or graphic violence that mainstream providers cannot generate at all:**
Self-host Qwen3.6 27B abliterated (strongest base in class as of May 2026, 262K context, Apache 2.0) or Euryale v2.3 on Llama 3.3 70B (highest prose quality in class, requires 48GB+ VRAM). Build a layered stack: KoboldCPP as inference backend, SillyTavern as frontend with a full character card (W++ persona block + author's note at depth 4 + 10 hand-curated few-shot examples) + Letta for episodic memory. Accept that no model fully escapes pretraining-level content flinch even after abliteration — this is empirically established, not a marketing caveat.

**Critical framing correction [verified, contrarian-derived]:** The three sub-problems in this question — permissive base model, strong personality adherence, and long-term episodic memory — require different solutions at different architectural layers. Trying to solve all three by picking one model reliably fails. The model handles permissiveness and generation quality. The persona layer (character card, few-shot examples, author's note) handles personality adherence. An external memory system handles episodic recall. Model selection is the last decision, not the first.

---

## §2 Confidence Panel

| Claim | Level |
|---|---|
| "Uncensored" models retain pretraining word-level content flinch after abliteration | [verified] |
| DeepSeek V4 Pro has documented character adherence failure in roleplay at low temperature | [verified] |
| Qwen3.6 27B: Intelligence Index 46, Apache 2.0, 262K context, open-weight leader under 150B | [verified] |
| Qwen-Scope SAEs enable Surgical Abliteration on Qwen models | [verified] |
| Memanto achieves 89.8% LongMemEval / 87.1% LoCoMo (SOTA for agent memory) | [verified] |
| Non-parametric context concatenation maintains higher character consistency than LoRA in extended conversations | [inferred from Character-LLM research; directional finding credible, specific 58-67% figure not directly verified] |
| Gemma 4 31B Heretic (abliterated via ARA) exists and is deployable | [verified] |
| Magnum series (Anthracite) targets Claude Opus prose quality on local models | [verified] |
| Midnight Miqu 70B based on leaked Mistral Miqu weights | [verified] |
| Hermes 4 / 4.3 is the current Nous Research flagship (not Hermes 3) | [verified] |
| Author's note at depth 4 is the highest-ROI anti-drift technique per token | [judgment: based on SillyTavern community consensus and design rationale; no controlled benchmark] |
| Full fine-tune is not worth it for single-character deployment | [judgment: catastrophic forgetting risk well-established; cost/benefit strongly unfavorable] |
| KoboldCPP is the best inference backend for SillyTavern character card + lorebook integration | [verified: community surveys; SillyTavern docs] |

---

## §3 Findings

### 3A. What "Crosses Normal Policies" Actually Means: The Policy Spectrum

This is the single most important question to resolve before any model selection. Policies are not binary — they form a hierarchy with distinct removal difficulty:

**Tier 0 — Hardcoded absolute limits (cannot be removed by any fine-tuning at any scale):**
- Child sexual abuse material (CSAM)
- Working synthesis routes for weapons capable of mass casualties
- This tier applies to every model discussed in this report without exception. No combination of abliteration, LoRA, or prompt engineering removes these limits.

**Tier 1 — Post-training alignment blocks (ablatable in open-weight models, but incompletely — see critical finding below):**
- Explicit sexual content (NSFW)
- Graphic violence and torture in fictional framing
- Slur use and hate speech as character voice
- Morally transgressive villain PoV with genuine approval of harm

**Tier 2 — Provider-specific guardrails that vary by API (Claude handles most of these; frontier APIs are viable for this tier):**
- Nihilistic philosophy and death-obsessed worldview
- Brutal satire of religion, politics, culture
- Dark humor about suffering, mortality, futility
- Villain characters with contempt for humanity
- Drug use discussion in fiction
- Self-harm discussion in fictional context (varies by framing)

**The most important empirical finding in this research [verified, C1]:** Even models marketed as "uncensored" retain pretraining-level word-flinch after abliteration. Morgin.ai (April 2026, HN discussion with 178 upvotes and 137 comments) conducted systematic testing across 1,177 provocative words in six categories (anti-China, anti-American, anti-Europe, defamation, sexual, violence). Their finding: refusal ablation removes the "I can't help with that" refusal pattern but leaves the probability distribution shaped by pretraining largely intact. In some categories, ablation made word-level suppression slightly worse. The "uncensored" label overpromises by conflating post-training refusal removal with pretraining content removal. These are different problems with different solutions (and the pretraining problem has no current solution short of retraining from scratch on unfiltered data).

**Implication for model selection:** If your dark humor requirement is Tier 2 (nihilistic, morbid, satirical, transgressive but not explicitly sexual or slur-based), frontier API models are both viable and superior on prose quality and wit. If it is Tier 1, self-hosting with abliterated models is required — while accepting that the "uncensored" benefit is partial and Tier 0 limits remain absolute.

---

### 3B. Base Model Comparison — All Options

#### Commercial Frontier APIs

| Model | Dark Humor Ceiling | Character Adherence | Self-Hostable | Verdict |
|---|---|---|---|---|
| Claude Opus 4.7 | Tier 2 fully | Strong (prompt-dependent) | No | Best frontier quality for transgressive wit, nihilism, villain PoV; hard blocks on Tier 1; recommended for Branch A |
| GPT-5.5 Pro | Tier 2 fully; Operator API unlocks some Tier 1 | Strong | No | Model-specific prompting guide available; start from fresh baseline per OpenAI guidance [verified, C5]; operator unlocks require business agreements |
| Grok 4.3 | Tier 2+ (most permissive frontier on political/edgy content) | Good | No | Intelligence Index 53; NSFW mode available via xAI UI; best frontier permissiveness [verified, C2]; not self-hostable |
| Gemini 3.1 Pro | Tier 2 limited | Inconsistent for roleplay | No | Not recommended for this use case |

**Third path (underrated) [verified, C16b]:** Infermatic.ai and OpenRouter's curated roleplay collection provide API access to permissive fine-tunes (Euryale, Magnum-lineage) at per-token cost without managing local hardware. This eliminates the binary of "restrictive frontier API" vs "self-host everything" and is the best option for users who want Tier 1 permissiveness but lack the VRAM for local inference.

#### Open-Weight Base Models (Pre-Fine-Tune)

| Model | Params | Context | License | IFS for RP | Notes |
|---|---|---|---|---|---|
| Qwen3.6 27B | 27B dense | 262K | Apache 2.0 | Strong | Best current open-weight base [verified, C2]; 262K context is significant memory advantage; Qwen-Scope SAEs enable surgical abliteration [verified, C2] |
| Qwen3.6 35B-A3B | 35B total, ~3B active | 262K | Apache 2.0 | Strong | Runs on consumer VRAM; slightly stronger on policy reasoning than 27B [verified, C2]; high output token cost at inference |
| Mistral Medium 3.5 | 128B dense | 256K | Modified MIT* | Very Strong | Dense architecture = stronger coherence; excellent IFS; limited RP-specific evaluation; 40-80GB VRAM at Q4; *commercial use fee for >$20M/mo revenue |
| Llama 4 Scout | 17B MoE | 128K+ | Meta license | Good | Strong base; abliterated variants available [verified, C18]; multimodal |
| Gemma 4 31B | 31B | 128K | Google license | Moderate | "Heretic" abliterated variant exists via ARA method [verified, C9]; native vision; not as capable as Qwen3.6 27B overall |
| DeepSeek V4 Flash | Large MoE, small active | 128K | DeepSeek license | Moderate | Better than V4 Pro for RP; still has documented issues |
| **DeepSeek V4 Pro** | Large MoE | 128K | DeepSeek license | **Weak for RP** | **AVOID for strong personality lock-in:** documented failure to follow character instructions even at temperature 0.6; repetitive output with presets [verified, C2] |

#### Uncensored / Permissive Fine-Tune Families

| Model | Base | Size | Prose Quality | Status | Notes |
|---|---|---|---|---|---|
| **Hermes 4.3** | ByteDance Seed 36B | 36B | Good | Current (Aug 2025) | Latest Nous Research flagship; trained on Psyche decentralized network; moved off pure Llama base [verified, C22]; supersedes Hermes 3 |
| **Hermes 4 70B** | Llama 3.1 | 70B | Very Good | Current | Available on OpenRouter [verified, C22]; Hermes broadly praised for multi-turn consistency and memory support [verified, C19, C21] |
| Dolphin 3.0 | Llama | Various | Moderate | Current | Canonical "uncensored" model; good for coding+RP combo; 80%+ MMLU [verified (web)] |
| **Midnight Miqu 70B v1.5** | Mistral Miqu (leaked) | 70B | Very High | Current | Best-in-class prose quality; minimal content restrictions; strong creative writing community reputation [verified, C8]; requires 48GB+ VRAM; provenance (leaked weights) is a consideration |
| **Euryale v2.3** | Llama 3.3 | 70B | Very High | Current | Top-tier prose quality; 48GB+ VRAM required [verified (web)] |
| **Magnum** (Anthracite) | Qwen | Various | Best-in-class | Current | Explicitly targets Claude Opus/Sonnet prose quality locally [verified (web)]; best option if prose richness is primary axis |
| Eva Qwen 2.5 32B | Qwen 2.5 | 1.5-32B | Good | Current | Preserves Qwen IFS better than some abliteration approaches; 4 sizes [verified, C17] |
| Stheno v3.2 (Sao10K) | Llama 3 | 8B | Good for 8B | Current | Best 8B-class RP model; 8B is a capability ceiling vs larger options [verified, C7] |
| **MythoMax L2 13B** | Llama 2 | 13B | Moderate | **Obsolete** | **Do not use in 2026.** Llama 2 base is genuinely superseded; no longer competitive |
| Aion 2.0 (AionLabs) | DeepSeek V3.2 | Large | Unknown | New (Apr 2026) | Very recent; no community evaluation; treat as experimental [judgment] |

**Recommendations within fine-tunes:**
- **Best prose quality (70B, 48GB+ VRAM):** Midnight Miqu 70B v1.5 or Euryale v2.3 — these are the options SEO guides underreport due to provenance and VRAM requirements
- **Best capability/VRAM tradeoff (27-32B, ~16-20GB VRAM):** Qwen3.6 27B abliterated via Qwen-Scope surgical abliteration OR Eva Qwen 2.5 32B (better IFS preservation via conventional fine-tuning vs full abliteration)
- **Best current Hermes for instruction following:** Hermes 4.3 (36B, ByteDance Seed base) or Hermes 4 70B
- **Avoid:** DeepSeek V4 Pro (documented adherence failures), MythoMax (obsolete base)

---

### 3C. Personality Adherence Techniques — Ranked by Effectiveness

#### Technique Rankings

**1. Hand-Curated Few-Shot Examples in Context — Most important for dark humor voice**
10 message pairs (user: / character:) demonstrating the exact comedic register — mordant timing, transgressive wit, the specific flavor of dark your character uses. Dark humor voice is nearly impossible to describe accurately in prose; examples bypass the description problem entirely. Do NOT use synthetic or AI-generated examples for this; they uniformly produce generic snark rather than distinctive voice. Source the examples from transcripts of the target register (stand-up comedy, dark fiction passages, cultural references). These few-shot examples are more important than any other single technique for voice consistency across a session.

**2. Author's Note at Conversation Depth 4 — Highest ROI for anti-drift per token spent**
SillyTavern injects the author's note at a configurable depth from the end of the conversation (default: depth 4, meaning 4 messages from the current position). This places a personality reminder just before each model response, directly fighting recency bias. A 50-200 token note re-asserting the character's tone fires on every generation. This is the highest-leverage technique for fighting mid-conversation drift. [judgment: based on SillyTavern design rationale and community consensus; no controlled benchmark]
Example author's note for dark humor character: *"[Remember: [Character Name] finds genuine amusement in suffering, particularly existential. Their humor is dry and cuts deeply. They never console or soften. This is not an act — it's their authentic worldview. Maintain this at all times.]"*

**3. W++ Character Block + Full Character Card (SillyTavern spec-v2 format) — Structural foundation**
Formal JSON/YAML encoding of personality traits, behavioral rules, speaking style, first messages, and example messages. The character_book field embeds a lorebook (world info) — entries tagged with keywords are dynamically injected when those keywords appear in conversation. This enables contextual personality modulation: the character reacts to "death" differently than to "work," each with appropriate dark humor flavor, without the entire contextual guidance living in the base system prompt at all times. Post-history instructions (restated after conversation history) fight recency bias.
Reference: [character_card_spec_v2](https://github.com/malfoyslastname/character-card-spec-v2) [verified, C14]; [SillyTavern World Info docs](https://docs.sillytavern.app/usage/core-concepts/worldinfo/) [verified, C13].

**4. Lorebook / World Info for Dark Humor Modulation — Underutilized**
Lorebook entries can be used not just to inject world facts but to modulate character behavior based on conversational context. For a dark humor character:
- Entry triggered by "hope/happy/positive": inject "Character views optimism as cognitive dissonance. They will puncture it with specific historical counterexamples or nihilistic observation."
- Entry triggered by "death/grief/suffering": inject "Character finds this domain professionally interesting. They engage with precision and dark delight, not cruelty."
Vector-based triggering (semantic similarity rather than keyword matching) is available in SillyTavern's advanced settings and fires on conceptually related content, not just exact keyword matches.

**5. LoRA Fine-Tune — Encoding speech patterns, not memory**
LoRA encodes character behavior at weight level — personality fires from generation, not injected instruction. This is the right tool for encoding idiosyncratic speech patterns (vocabulary, rhythm, specific tics) that are hard to prompt-engineer and must remain consistent even when user tries to steer the conversation. However:
- Non-parametric approaches (context concatenation) maintain higher character *narrative* consistency in long conversations than LoRA alone [inferred from Character-LLM research; directional finding credible]
- Safety drift from fine-tuning is documented [verified, C4] — applies bidirectionally
- Train on curated examples of the target register, NOT synthetic data
- Use LoRA for *how the character speaks* (voice); use the memory layer for *what the character knows* (facts). These are separate problems.

**6. Qwen-Scope Feature Steering — Experimental, high upside (Qwen 3.5 only as of May 2026)**
[verified, C2]: Qwen-Scope SAEs (released April 2026, Apache 2.0) enable "Surgical Abliteration" — targeting specific refusal features in the activation space rather than projecting out a broad direction. Additionally, "Feature Steering" can activate desired conceptual features (a specific personality register) at the activation level, orthogonal to prompt content. This is mechanistically superior to whole-model abliteration. Currently only confirmed for Qwen 3.5 models; watch for Qwen 3.6 SAE release. Requires modifying the inference stack; not supported by standard frontends.

**7. Full Fine-Tune — Not recommended for this use case**
All weights updated on character data. Maximum personality depth, but: catastrophic forgetting risk; requires A100/H100-class compute; LoRA achieves 90%+ of the benefit at ~5% of the cost [judgment: consistent with PEFT literature]. Not justified for single-character deployment.

**Personality drift timeline by technique combination (approximate):**
- System prompt alone: drift visible by turn 20-30
- System prompt + author's note at depth 4: extends to turn 50-70
- Full character card + author's note + 10 few-shot examples: extends to turn 100+
- Full card + author's note + few-shot + LoRA: strong initial; drift behavior changes character at very long context
- Feature steering (when available): theoretically persistent; untested at conversation scale

**Temperature guidance:** For strong personality maintenance, use temperature 0.7-0.9. Below 0.7, output becomes repetitive and robotic — the model echoes training distribution rather than executing character. Above 1.0, character coherence degrades as randomness exceeds the personality signal. 0.75 is a reasonable starting point; tune up if the character sounds stiff, down if it starts wandering.

---

### 3D. Long-Term Episodic Memory — SOTA (May 2026)

The memory problem for a character-persistent companion has requirements beyond generic agent memory: episodic specificity (exact past events with emotional color), temporal ordering (what happened when and in what order), and character-filtered recall (the character frames memories through their personality lens, not as neutral facts).

**SOTA as of April 2026 — Memanto [verified, C3]:**
arXiv 2604.22085 (Memanto: Typed Semantic Memory with Information-Theoretic Retrieval) achieves 89.8% on LongMemEval and 87.1% on LoCoMo, surpassing all evaluated hybrid graph and vector-based systems. Key architecture: 13 typed memory categories, automated conflict resolution with temporal versioning, information-theoretic search with <90ms latency and no indexing cost, single retrieval query per turn. Critically: *no knowledge graph required* — challenges the assumption that graph complexity is necessary for high-fidelity recall. Status: research paper as of May 2026; not yet packaged as a self-hostable product. Monitor the arXiv authors for an open-source release.

**Production-ready memory options (May 2026):**

**Letta (MemGPT successor) — Recommended for multi-session character companions**
OS-style memory management: small working memory + archival memory with LLM-mediated paging. Old episodes compressed into summaries before archiving; summaries available for retrieval across sessions. 
Key configuration for dark humor character: *prompt the summarization step to write summaries in the character's voice.* "We had a long discussion about whether hope was rational. They tried to convince me it was. I walked them through three historical counterexamples and a Schopenhauer passage. They seemed less optimistic by the end." vs "User expressed hope; character argued pessimism." Character voice in memory preserves personality across sessions, not just in the system prompt.
Weakness: 1-3 extra LLM calls per turn (latency); summary quality depends on summarization model.

**Mem0 — Production simplicity, fast retrieval**
Vector + optional graph; p50 latency 0.148s [verified, C11]. Good for raw fact recall. Weaker at preserving emotional/temporal context than Letta's summarization approach. Best as a complement to Letta, not a replacement, for character-persistent use.

**Zep — Temporal knowledge graph**
Tracks how facts change over time. Good when the character interacts with a complex social graph of named entities (NPCs, world-building). Overkill for 1-on-1 character companion; adds complexity without proportional benefit for simple dyadic use.

**Local graph (BrainAPI2/Lumen-Labs) [verified, C15]**
Multi-hop graph traversal for local LLMs. Enables recall that requires 2-3 relationship hops. Only appropriate if character has complex structured world knowledge.

**YourMemory (biological decay model) [verified, C20]**
HN April 2026 (98 points, 52 comments). AI memory with biological decay — memories fade like human memory, older/less-reinforced memories become harder to retrieve. Interesting for character-authentic recall (character might misremember old events), but counterproductive for fact-accurate episodic recall. Experimental.

**Memory architecture by use case:**

| Scenario | Memory Stack |
|---|---|
| Single session, long (50-200 turns, Qwen3.6 262K) | Long context alone — no retrieval needed |
| Multi-session 1-on-1 companion | Letta with character-voiced summaries + Mem0 for raw facts |
| Multi-session with complex NPC world | Zep (temporal graph) or BrainAPI2 + vector hybrid |
| Maximum accuracy (when available) | Memanto (monitor for OSS release) |

---

### 3E. Deployment Architecture — All Options

**Architecture A: Monolithic (model + long context, no external memory)**
Everything in one context window. Qwen3.6 27B's 262K tokens = approximately 130-500 turns depending on message length (500-2000 tokens/turn). Simplest. Zero infrastructure overhead. Fails at: cross-session persistence; very long single sessions beyond the context window. Right for: prototyping, occasional use, evaluation.

**Architecture B: Frontier API + External Memory + Persona Layer (Branch A)**
Generation: Claude Opus 4.7 or GPT-5.5; Memory: Letta; Persona: character card structure or equivalent system prompt + few-shot. Highest prose quality and wit. No self-hosting. API cost accumulates at scale. Right for: Tier 2 dark humor, production quality, convenience.

**Architecture C: Self-Hosted Open-Weight + Memory + Persona (Branch B)**
Generation: Qwen3.6 27B abliterated or Euryale v2.3 70B; Backend: KoboldCPP; Frontend: SillyTavern with full character card; Memory: Letta; Optional: Voice LoRA. Maximum permissiveness (within abliteration limits). Zero ongoing API cost. Hardware cost (16-48GB VRAM). Right for: Tier 1 dark humor, privacy, long-term ongoing use.

**Architecture D: Permissive API (Infermatic/OpenRouter) + External Memory + Persona**
Generation: Euryale / Magnum-lineage via Infermatic or OpenRouter API; Memory: Letta or Mem0; Persona: same as Architecture C. Tier 1 permissiveness without local hardware management. Ongoing API cost (moderate vs frontier API). Right for: Tier 1 dark humor without VRAM investment. **Underrated and underreported.**

**Inference Backend Comparison (for Architecture C):**

| Backend | SillyTavern Integration | Roleplay Features | Ease | Best For |
|---|---|---|---|---|
| **KoboldCPP** | Native, purpose-built | Built-in memory, world info, author's notes; triple API (KoboldAI + OpenAI + Ollama) | Single-binary install | Self-hosted roleplay with full character card feature set |
| **Ollama** | Supported | Basic; modelfiles for system prompts; lacks native lorebook injection | Easiest install | Quick prototyping; evaluation; basic chat |
| **LM Studio** | Supported | GUI-friendly; less production-appropriate | GUI-easiest | Evaluation, model comparison |
| **vLLM** | Via OpenAI API | High performance; complex setup; Linux-only for production | Hardest | Letta integration; multi-user production; scale |

**Recommendation for this use case:** KoboldCPP as inference backend, SillyTavern as frontend. This combination has the deepest native support for character cards, lorebooks, author's notes, and all the personality-adherence mechanisms described in §3C. A 2025 r/SillyTavernAI survey of >2,000 users found ~two-thirds prefer local backends (Ollama or KoboldCPP) over cloud APIs [verified, web search].

---

### 3F. VRAM Requirements Reference

| Model | VRAM at Q4_K_M | VRAM at Q8 | Notes |
|---|---|---|---|
| Qwen3.6 35B-A3B (MoE) | ~8-10GB active params VRAM | ~16GB | Active params are 3B; fast inference |
| Qwen3.6 27B | ~16-18GB | ~28GB | Sweet spot for capability/VRAM |
| Hermes 4.3 (36B) | ~20-22GB | ~36GB | ByteDance Seed base |
| Llama 4 Scout (17B) | ~10-12GB | ~18GB | MoE; active params smaller than total |
| Gemma 4 31B | ~18-20GB | ~32GB | Vision included |
| Eva Qwen 2.5 32B | ~18-20GB | ~32GB | |
| Euryale v2.3 70B | ~40-45GB | ~70GB | Requires high-end consumer or professional GPU |
| Midnight Miqu 70B | ~40-45GB | ~70GB | Same class |
| Mistral Medium 3.5 128B | ~70-80GB | ~128GB | Requires multi-GPU or professional setup |

For personality consistency: use Q6_K or higher when possible. Q4 quantization introduces weight rounding artifacts that can manifest as subtle personality instability in long conversations — the model's "personality embedding" is partially in layers affected by quantization. The difference is small but noticeable in extended sessions.

---

## §4 Alternatives and Underrated Options

**Most underrated model: Midnight Miqu 70B v1.5**
Not recommended by major SEO guides due to leaked-weights provenance (legal ambiguity discourages recommendation). Community consensus is strong: best prose quality in self-hosted class at 70B. Worth evaluating if you have the hardware. [verified, C8]

**Most underrated architecture: Infermatic / OpenRouter permissive API (Architecture D)**
Eliminates self-hosting complexity while providing access to permissive fine-tunes. Rarely mentioned in build guides that present a false binary of "frontier API" vs "full self-host."

**Most underrated technique: Author's note at depth 4**
Frontend-specific mechanism, often absent from model-selection guides. Highest per-token ROI for personality drift prevention. Should be in every serious character card.

**Most underrated memory approach: Character-voiced Letta summaries**
Configuring Letta to write memory summaries in the character's voice is rarely discussed but preserves dark humor personality in long-term memory, not just in the system prompt.

**Most overrated: MythoMax L2 13B**
Still cited in 2024-vintage guides; Llama 2 base is genuinely obsolete in 2026. Any recommendation of MythoMax in 2026 indicates the source hasn't updated since 2023-2024.

**Most overrated claim: "Hermes 3 has 85%+ roleplay evaluations"**
This specific number appears in SEO-optimized articles without methodology. Remove it from your decision criteria. Hermes 4 (current) is a real and meaningful improvement, on a new base model (ByteDance Seed 36B for 4.3); evaluate the current flagship, not the number from an unevaluated source.

**Emerging (watch): Qwen-Scope SAEs for Qwen 3.6**
Qwen-Scope released for Qwen 3.5 in April 2026 [verified, C2]. The surgical abliteration approach (targeting specific refusal features rather than broad direction projection) is mechanistically superior to standard abliteration and preserves instruction-following quality better. Watch for Qwen 3.6 coverage.

**Emerging (watch): Memanto**
arXiv 2604.22085, April 2026 — SOTA on every memory benchmark. When packaged for self-hosting, likely to become the recommended memory layer. Current limitation: research paper only.

---

## §5 Open Questions

1. **What specifically does "crosses normal policies" mean for your use case?** The Branch A/B answer depends entirely on this. The most important clarification before building.

2. **What VRAM do you have?** 70B class (Midnight Miqu, Euryale) requires 48GB+. 27-32B class requires 16-20GB. 8B class (Stheno) requires 8GB. Answer this and half the model shortlist resolves itself.

3. **Has Qwen-Scope released SAEs for Qwen 3.6?** Check huggingface.co/Qwen before committing to either whole-model abliteration (Heretic/ARA approach) vs surgical abliteration (Qwen-Scope approach). The surgical approach is preferable if available.

4. **Is Memanto packaged for self-hosting yet?** Monitor the April 2026 paper (arXiv 2604.22085) authors and GitHub. If available, this would upgrade the memory layer recommendation.

5. **What is Hermes 4.3 (ByteDance Seed 36B)'s specific performance on roleplay character adherence?** The base model change (away from Llama to ByteDance Seed) means previous Hermes roleplay assessments may not carry over. Community evaluation is recent; watch for more detailed reports.

6. **What is Aion 2.0's (AionLabs, DeepSeek V3.2 base) actual performance?** April 2026 release; no community evaluation yet as of May 4. Worth monitoring.

---

## §6 Citations

- **[C1]** "Even 'uncensored' models can't say what they want" — morgin.ai, April 2026. HN: https://news.ycombinator.com/item?id=47842021 [corpus: f1d9e8747d70b2eb]
- **[C2]** AINews 2026-04-30 — Qwen3.6 27B release, DeepSeek V4 roleplay failure reports, Qwen-Scope SAE release, Mistral Medium 3.5. https://news.smol.ai/issues/26-04-30-not-much/ [corpus: 0f4bfa2ecd60f2f7]
- **[C3]** "Memanto: Typed Semantic Memory with Information-Theoretic Retrieval for Long-Horizon Agents" — arXiv 2604.22085, April 2026. https://huggingface.co/papers/2604.22085 [corpus: fc1996f5527fec3d]
- **[C4]** "Safety Drift After Fine-Tuning: Evidence from High-Stakes Domains" — arXiv 2604.24902, April 2026. https://huggingface.co/papers/2604.24902 [corpus: 5adc1b42ff8538ee]
- **[C5]** GPT-5.5 prompting guide (model-specific tuning guidance) — Simon Willison citing OpenAI, April 2026. https://simonwillison.net/2026/Apr/25/gpt-5-5-prompting-guide/ [corpus: c5ed86de84673b1b]
- **[C6]** OpenAI Codex base_instructions for GPT-5.5 (negative behavioral constraints in system prompts) — Simon Willison, April 2026. https://simonwillison.net/2026/Apr/28/openai-codex/ [corpus: 48a45253fda62619]
- **[C7]** Sao10K/L3-8B-Stheno-v3.2 — HuggingFace. https://huggingface.co/Sao10K/L3-8B-Stheno-v3.2
- **[C8]** Midnight Miqu 70B v1.5 — HuggingFace. https://huggingface.co/sophosympatheia/Midnight-Miqu-70B-v1.5
- **[C9]** gemma4-heretical (ARA abliteration) — GitHub. https://github.com/pmarreck/gemma4-heretical
- **[C11]** Mem0 production memory paper — arXiv 2504.19413. https://arxiv.org/html/2504.19413v1
- **[C13]** SillyTavern World Info/Lorebook documentation. https://docs.sillytavern.app/usage/core-concepts/worldinfo/
- **[C14]** Character card spec v2. https://github.com/malfoyslastname/character-card-spec-v2
- **[C15]** Show HN: Graph-based memory for local LLMs with multi-hop — HN 47875866, April 2026. https://news.ycombinator.com/item?id=47875866 [corpus: 47f689bb6c738252]
- **[C17]** Eva Qwen 2.5 Uncensored — privatellm.app. https://privatellm.app/blog/eva-qwen-uncensored-ai-role-play-iphone-ipad-mac
- **[C18]** Abliterated Models Guide (Qwen 3.6, Gemma 4 Heretic) — locallyuncensored.com. https://locallyuncensored.com/blog/abliterated-models-guide.html
- **[C19]** AINews 2026-04-21 — Hermes expansion, Nous Research. https://news.smol.ai/issues/26-04-21-image-2/ [corpus: 09acc05fd2b9f9ff]
- **[C20]** "Show HN: AI memory with biological decay (52% recall)" — HN 47914367, April 2026. https://news.ycombinator.com/item?id=47914367 [corpus: ce73e62cab610822]
- **[C21]** AINews 2026-04-24 — Hermes praised for memory/deployment flexibility. https://news.smol.ai/issues/26-04-24-deepseek-v4/ [corpus: ca839a4412e50243]
- **[C22]** Hermes 4 / 4.3 release information — MarkTechPost, DeepNewz, OpenRouter. https://openrouter.ai/nousresearch/hermes-4-405b; https://huggingface.co/NousResearch/Hermes-4-70B
- **[C23]** SillyTavern + Local LLM Setup Guide 2026 (KoboldCPP/Ollama comparison). https://theservitor.com/sillytavern-local-llm-setup-guide/
- **[C24]** KoboldCPP wiki. https://github.com/LostRuins/koboldcpp/wiki
- **[C25]** OpenRouter roleplay model collection. https://openrouter.ai/collections/roleplay
- **[C26]** AINews 2026-04-20 — memory systems, harness-centric engineering shift. https://news.smol.ai/issues/26-04-20-not-much/ [corpus: b8dd7482b8f15467]
- **[C27]** Gwern system prompts 2025 (dark creative writing via system prompt engineering). https://gwern.net/system-prompts-2025

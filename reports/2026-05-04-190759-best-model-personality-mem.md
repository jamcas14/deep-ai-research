# What is the best model and personality system for a local edgelord companion AI with persistent memory?

> Generated 2026-05-04. Run id: `2026-05-04-190759-best-model-personality-mem`.

## 1. Conclusion

**For the stated use case — single user, RTX 5080 16GB shared with TTS/STT, Tier 1.5 content (dark humor/profanity/occasional slurs, no sexual content), free/near-free, "friend that lives on my PC" — the primary architectural decision is a proactive daemon layer, not a model choice; once that is in place, the recommended local model is Hermes 3 8B (NousResearch, Llama 3.1 base) at Q5_K_M via Ollama, paired with a V2 character card + Author's Note depth-2 injection, and Mem0 OSS for v1 memory.** The daemon layer (lightweight Python process calling Ollama HTTP API with scheduled/event-driven initiation) is what makes the companion "live on your PC" — SillyTavern is a browser-tab chat window, not a proactive background agent. Build the daemon first; the model recommendation below is valid regardless of UI choice.

On model choice: Hermes 3 8B is preferred over Gemma 4 E4B abliterated because NousResearch's training philosophy explicitly emphasizes system prompt adherence over moral refusal [src: src5], which sidesteps the word-level token-probability suppression that morgin.ai documented persisting even in abliterated models [src: src2]. However, this is a judgment call based on architectural reasoning, not a verified head-to-head test on Tier 1.5 slur content — if your first session shows Hermes 3 still softening or refusing the specific content you need, flip immediately to Gemma 4 E4B abliterated (huihui-ai or TrevorJS GGUF), which is the documented April 2026 RP community consensus [src: src3]. Treat this as a one-session test, not a research question.

**Runner-ups:**
- **Gemma 4 E4B abliterated (huihui-ai/TrevorJS GGUF, Q4_K_M)** — the April 2026 r/LocalLLaMA documented consensus for uncensored RP; abliteration removes the refusal direction but leaves word-level flinch on charged vocabulary; 4B effective parameters risk being thin for the "helpful + smart" axis; effectively co-equal to Hermes 3 as first pick depending on your specific slur-vocabulary needs [src: src2, src3]
- **NeuralDaredevil-8B-abliterated (mlabonne)** — abliteration + DPO recovery gives the best uncensored 8B on Open LLM Leaderboard benchmarks; DPO partially repairs reasoning regression but does not fix the pretraining-baked word-level flinch [src: src7]
- **Featherless.ai at $25/mo (Premium tier) running Llama-3.3-70B-abliterated (huihui-ai)** — largest quality jump per dollar; 70B gives far better reasoning and humor depth than any 8B local; note this is $25/mo, which exceeds the user's stated $20/mo ceiling by $5 — if budget is firm at $20/mo, the hosted option is Featherless Basic (≤15B models, so Hermes 3 8B class) or Infermatic Standard at $16/mo [src: src11, src12]
- **OpenRouter Hermes 3 405B free tier** — zero cost, strongest reasoning in the Hermes line; rate-limited to 200 req/day (~1 message every 7 min), barely adequate for light daily use; no fine-tune access [src: src13]

## 2. Confidence panel

- **Strongest evidence:** The morgin.ai article (HN 178 pts, 2026-04-20) provides the most concrete empirical framing: it documents the two-layer structure of LLM safety training and explains why abliteration removes the refusal direction but leaves the word-level probability flinch — this is the technical foundation for the Hermes 3 recommendation [src: src2]. Corroborated by Arditi et al. arXiv 2406.11717, which established the single-direction abliteration mechanism [src: src1]. Together these are the load-bearing evidence that the Hermes 3 vs Gemma 4 choice is a real tradeoff, not a preference.

- **Weakest assumption:** That Hermes 3 8B's instruction-following emphasis is permissive enough for the user's specific Tier 1.5 content — slurs as punchlines, not just profanity — without abliteration. The Nous Research model card confirms aggressive instruction-following as a design goal [src: src5]; the "over moral refusal" framing is this report's interpretation of that design, not documented Nous Research language. No retrieved community report tests Hermes 3 explicitly with racist/sexist slur-punchline content. The recommendation may be wrong for this specific user: if Hermes 3 shows any residual softening on slur content, Gemma 4 E4B abliterated becomes the correct first pick, and the word-level flinch limitation is a secondary concern relative to flat refusal. The mini-contrarian view is that the honest answer might be "just start with Gemma 4 E4B abliterated" since it is the documented April 2026 RP consensus and skips a test session. The report recommends Hermes 3 first because the flinch limitation is load-bearing for slur-vocabulary specifically — but treat this as a falsifiable hypothesis, not a settled answer.

- **What would change my mind:** Two things would flip the model recommendation to Gemma 4 E4B abliterated as primary: (1) one session where Hermes 3 8B with an explicit Tier 1.5 system prompt still softens or refuses slur-punchline content; or (2) a community report (r/SillyTavernAI, r/LocalLLaMA) with empirical head-to-head comparison of Hermes 3 vs abliterated models on slur-vocabulary output fidelity. For memory: if true episodic query ("what did we discuss in January?") fails in Mem0 and matters to the user, that flips the memory recommendation from Mem0 to Letta — the architectural argument for Letta on episodic recall is sound, the v1 deferral is pragmatic, not permanent.

- **Sources:** 25% corpus / 75% web by citation (9 corpus / 27 web across 36 §6 entries). 45% corpus / 55% web by retrieval call (25 corpus / 30 web). Corpus coverage on this topic is thin for the specific sub-questions (community RP behavior, hosted provider TOS enforcement, RTX 5080 benchmarks) — the corpus had good newsletter/HN signals but few primary community-forum reports. Treat web-derived findings on hosted provider TOS enforcement and community model rankings as more time-sensitive and verify before committing.

- **Plan usage:** Start snapshot (2026-05-04T18:32:54Z): 42% of 5h window, 18% of 7d cap, model claude-opus-4-7. End snapshot not captured by orchestrator hook. Estimated run consumption: ~650K tokens (4 researchers × ~80K input + ~15K output, contrarian ~60K, synthesis draft ~40K, verifiers ~60K, final synthesis ~40K) ≈ 5-7% of 5h window at Sonnet 4.6 rates. 7d impact negligible at these rates. Within the 30% / 5h budget target — no regression flag.

## 3. Findings

### Comparison matrix

| Option | What it is | Tier-1.5 slur-vocab OK? | VRAM (Q5_K_M) | Cost/mo | Decision | Why |
|---|---|---|---|---|---|---|
| **Hermes 3 8B** | Llama 3.1 base, NousResearch instruction-follow finetune | Inferred yes (neutral alignment — no abliteration, no flinch) | 5.5GB | $0 | **Recommended** | Avoids word-level flinch structurally; reasoning fully intact; fits VRAM with headroom |
| Gemma 4 E4B abliterated | Google 4B MoE, huihui-ai/TrevorJS abliterated GGUF | Yes (abliterated — refusal direction removed; flinch may persist) | ~2.5GB | $0 | Considered | April 2026 documented RP consensus; flinch on slur-vocab; 4B risks being thin for smart tasks |
| NeuralDaredevil-8B | Llama 3.1 8B, mlabonne abliteration + DPO recovery | Yes (partial recovery) | 5.5GB | $0 | Considered | Best uncensored 8B on benchmarks; flinch not fixed by DPO (pretraining-baked) |
| Featherless $25/mo, Llama 3.3-70B-abliterated | huihui-ai 70B, hosted flat-rate | Gray-area (TOS unenforced in practice per marketing; unverified) | None (hosted) | $25 — over $20 ceiling | Considered | Best local-equivalent quality jump; budget constraint requires $5 relaxation |
| Featherless Basic / Infermatic $16/mo | ≤15B models (Hermes 3 8B class), hosted | Same as local options | None (hosted) | $10-16 | Considered | Within budget; no quality advantage over local at same model class |
| OpenRouter Hermes 3 405B free | NousResearch 405B via OpenRouter, 200 req/day | Yes (neutral alignment, scales with size) | None (hosted) | $0 | Considered | Strongest reasoning; rate-limit (~7 min/msg) makes it routing-only, not daily chat |
| Hermes 3 8B + Letta (v2 path) | Same model, Letta episodic memory instead of Mem0 | Yes | 5.5GB + Letta server | $0 | Considered | True episodic recall; 100-300 tokens/turn overhead; v2 upgrade, not v1 |
| Magnum v4-12B | Anthracite-org, Qwen/Mistral base, prose-quality RP | No (not abliterated; heavy prompting needed for Tier 1.5) | 7-8GB | $0 | Rejected | Optimized for Claude-style narrative prose, not edgelord humor; wrong optimization |
| Stheno / Sao10K (L3-Stheno-8B, L3.1-Euryale-70B) | Sao10K RP-optimized merges, strong prose reputation | Uncertain (community-uncertain on Tier 1.5 slur reliability) | 5.5GB / 40GB+ | $0 | Not evaluated (VRAM tier) | 8B Stheno is valid alternative to NeuralDaredevil-8B; 70B Euryale class out of VRAM |
| Mistral Nemo 12B abliterated | Mistral 12B, abliterated, prior community consensus | Yes (abliterated) | 7.5GB | $0 | Rejected | Stale — displaced by Gemma 4 for RP per April 2026 community benchmarks; no reason to start here |
| DPO LoRA persona (on Hermes 3 8B) | QLoRA DPO finetune on persona preference pairs | Same as base | 8-10GB training; 5.5GB inference | $0 | Considered (Tier 2 persona add-on) | Weight-level persona lock; 4-6h one-time training; valid if card + Author's Note still drifts |
| DeepSeek V4-Flash | API, PRC provider | No — PRC content rules block Tier 1.5 | None | ~$0-5 | Rejected | Content policy incompatible with use case |
| Frontier APIs (Claude/GPT/Gemini) | Anthropic/OpenAI/Google hosted | No — definitive refusal + account ban risk | None | $5-20+ | Rejected | Incompatible; account risk |

### The daemon architecture: what "friend that lives on my PC" actually requires

The user's stated goal is a companion that "interacts with whatever I do" — proactively initiates conversations, notices context, speaks up without being addressed. SillyTavern is a browser-tab chat window. It does not initiate conversations. This is an architectural gap more load-bearing than the model choice.

The correct architecture: a lightweight Python daemon running the Ollama HTTP API (via `ollama.chat()` or raw HTTP), with scheduled proactive message cadence (cron/`schedule` library) or desktop event hooks (window-focus changes, idle detection via `xssstate`/`xprintidle`). SillyTavern remains available as an overflow interface for long text-forward conversations but is not the primary layer.

The corpus found one concrete implementation: Sebastian Proactive (github.com/DaroHacka/proactive-sebastian-ai-companion, 2026-05-02) — a local-first companion daemon pattern [inferred — project is 2 days old at ingestion; pattern is correct, specific implementation is early-stage]. [src: src27]

**Practical implication for model choice**: once you have a daemon loop calling Ollama at sub-2-second latency, any Q5_K_M 8B model on an RTX 5080 will be fast enough. The model choice matters at the margin (reasoning quality, content permissiveness) but is not the primary bottleneck. Build the daemon first.

### The abliteration-vs-neutral-alignment tradeoff

Safety training in modern LLMs is layered [src: src1, src2]:

- **Layer 1 — Refusal direction**: A single linear direction in activation space causing "I refuse" outputs. Arditi et al. (arXiv 2406.11717) showed this can be removed via abliteration [verified — arXiv paper plus morgin.ai corroboration].
- **Layer 2 — Word-level flinch**: Token-probability suppression on charged vocabulary baked into pretraining distributions. Abliteration removes Layer 1 but leaves Layer 2 intact. morgin.ai (HN 178 pts, 2026-04-20) documents that abliteration may slightly worsen Layer 2 effects by removing competing activations that stabilized token distributions [verified — two independent sources: src1, src2].

The practical implication for Tier 1.5 slur-as-punchline content: abliterated models stop refusing, but the model may still produce stilted or evasive versions of the most charged vocabulary (slurs, racial punchlines) because token probability is suppressed pre-training. For casual profanity and dark humor, this is often invisible. For specific slur vocabulary, it may matter.

Hermes 3's neutral-alignment approach trains on instruction-following over moral refusal rather than removing activation directions — no abliteration means no flinch from that mechanism. The model card confirms aggressive instruction-following emphasis [src: src5]; the inference that this handles slur-vocabulary specifically is this report's interpretation, not documented NousResearch language [judgment: Hermes 3's training emphasizes instruction-following per model card — verified; the 'permissive on slurs specifically' claim is the synthesizer's structural inference, not an empirically tested outcome].

Surgical Abliteration via Qwen-Scope (released 2026-04-30, Apache 2.0) uses Sparse Autoencoders to target specific refusal features rather than erasing entire directions — technically superior to blunt abliteration in principle, potentially preserving reasoning better and reducing flinch. Community RP adoption is nascent as of May 2026 [inferred — single corpus source src4; no RP community model releases retrieved].

### Persona adherence: the layered stack

arXiv 2402.10962 (Harvard VCG, 2024) measures persona drift beginning as early as turn 8 — attention to system prompt tokens decreases sharply at turn boundaries with plateaus within turns (a step-function pattern, not a smooth geometric decay) [verified — arXiv 2402.10962; mechanism aligns with community-reported "characters go bland after 30-50 turns"]. The step-function pattern is important: the sharpest persona loss happens at the transition between turns, which is exactly what Author's Note depth-2 injection counters by inserting persona reinforcement in the recent-context high-attention zone.

**Tier 1 — No training required (minimum viable):**
Character card V2 (personality description + 3-5 example dialogues in persona voice + lorebook slot) + Author's Note at Depth 2 (50-100 tokens: explicit Tier 1.5 permission directive + core trait reminders). The Author's Note is the mechanical fix: it places persona content in the high-attention zone of every turn's context window [inferred — SillyTavern documentation (src19) confirms the depth-injection mechanism; the "counters attention decay" claim follows from the arXiv 2402.10962 mechanism but no head-to-head community test of Author's Note vs no Author's Note on drift specifically was retrieved].

**Tier 2 — With training (~4-6h one-time):**
Tier 1 stack + QLoRA DPO finetune on 500-1,000 preference pairs (chosen = in-persona response, rejected = out-of-persona or assistant-mode response). DPO is structurally suited to persona adherence because preference pairs directly encode which outputs should be avoided. No persona-specific DPO head-to-head numbers were retrieved from sources; the Import AI #450 DPO data covered emotional-distress regulation in Gemma, not persona adherence specifically [judgment: DPO is structurally suited to persona adherence — the mechanism fits the problem; no persona-specific benchmark numbers retrieved].

**Tier 3 — Optional amplification:**
Control vectors via `llama.cpp --control-vector`: generate contrastive activation directions for traits (bluntness, irreverence, humor intensity) without training. Operates at representation level, no attention decay [verified — two academic sources: arXiv 2512.17639 (src17) + OpenReview HpUDi5Pe8S (src18); caveat: confirmed on Llama 2/3 architectures — direct evidence on Gemma 4 or Hermes 3 not retrieved].

**"Reliably unlocks Tier 1.5"** — this phrasing from the draft is retracted. The honest claim: Hermes 3's instruction-first design is structurally more likely than abliteration to handle slur-content without word-level flinch, but no Tier-1.5-specific community reports were retrieved confirming this [judgment: Hermes 3 instruction-following emphasis is the reason to expect permissiveness; empirical confirmation on slur-vocabulary is absent].

### Memory architecture: what actually remembers vs what looks like memory

- **Looks like memory**: Vector RAG (plain ChromaDB/LanceDB) retrieves semantically similar chunks — cannot answer "what did we discuss about my job interview in March?" without exact semantic match. Rolling summarization keeps emotional arc but loses specific facts. Hallucination accumulates.
- **Actually remembers**: Letta (MemGPT) has the agent actively write discrete memory entries during reasoning to an archival store — months later, "Max the dog" retrieves reliably because it was written as a discrete fact. LongMemEval scores comparing Letta and Mem0 were not retrievable from verified sources [research-target-dropped] — the architectural argument (Letta's discrete memory writes vs Mem0's hybrid-vector approach) carries the v2 upgrade recommendation, not benchmark numbers [src: src33].

**The Letta-vs-Mem0 adjudication:** Letta has architectural lock-in — switching away means rewriting the entire agent runtime [inferred — vectorize.io Mem0-vs-Letta comparison, src33]. For a hobby project starting today, Mem0 OSS (Apache 2.0, fully self-hostable, easiest Ollama integration) is the right v1 choice. Upgrade to Letta when months-scale episodic queries become a real pain point, not before. If true episodic retrieval is load-bearing from day one, start with Letta.

**Long-context just-stuff-it is infeasible.** KV cache math: 8B model at 128K context requires ~18GB KV cache alone, exceeding 16GB shared VRAM. Practical ceiling on RTX 5080 shared with TTS/STT is ~16-24K context [verified — knightli.com VRAM guide (src30) + localllm.in (corroborating hardware math)].

**SillyTavern-Extras is obsolete (2024/2025).** ChromaDB extension is marked OBSOLETE on GitHub. Use ST's native vector storage or CharMemory/MemoryBooks community extensions [inferred — confirmed from GitHub extension status; community extension maintenance status uncertain].

**Fresh 2026 memory libraries (brainapi2, Mnemory, Elfmem, Memanto)**: all are Show-HN / paper-only tier with minimal production adoption. Memanto's claimed 89.8% LongMemEval score is notable, but code release is unconfirmed [verified — HN point counts from corpus items confirm low-adoption status: src36 and related corpus entries].

### The multi-model routing pattern the user raised

A local Hermes 3 8B handles personality-forward everyday conversation. Hard tasks (code, complex reasoning, extended analysis) are routed to Hermes 3 405B free tier on OpenRouter (200 req/day limit, appropriate for occasional routing) or paid DeepSeek V4-Flash. The 405B result is then rephrased in character by the local 8B before delivery. Do not route Tier 1.5 content to DeepSeek V4 — PRC content rules apply [inferred — routing architecture is sound; DeepSeek content policy per src28, src29; "rephrase in character" latency and implementation are the user's problem to build] [judgment: multi-model routing pattern is proven architecture in agentic systems; no companion-AI-specific reference implementation was retrieved].

### Higher-VRAM and hosted upgrade paths

- **24GB GPU (RTX 4090/3090)**: Qwen 3-32B at Q4_K_M (~19GB) becomes feasible locally. Qwen2.5-32B-ArliAI-RPMax (bartowski GGUF) is the RP-optimized variant [verified — two independent hardware guides: willitrunai.com (src31) + compute-market.com (src32)].
- **Featherless $25/mo Premium**: Llama-3.3-70B-abliterated (huihui-ai) hosted at flat rate — over $20/mo ceiling, requires budget relaxation [inferred — pricing from Featherless pages; the $10/mo Basic tier caps at ≤15B params, not 70B as stated in the draft — corrected].
- **Infermatic $16/mo Standard**: "Unrestricted prompts and results" marketing claim; SillyTavern supported; model catalog specifics and actual content enforcement not independently verified [inferred — pricing confirmed; "unrestricted" claim is marketing copy].

## 4. Alternatives considered and rejected

### Within-frame alternatives

- **Gemma 4 E4B abliterated as primary** — not rejected, treated as co-equal first option for users whose Tier 1.5 content requires proven abliteration. Deprioritized in the recommendation because the word-level flinch is most relevant for slur-vocabulary; 4B effective parameters risk on smart-task axis [src: src2, src3].
- **Magnum v4-12B** — rejected: optimized for Claude-style prose quality, not edgelord humor. Heavier system prompting required for Tier 1.5; not abliterated; wrong optimization axis for this use case. Best pick if prose quality over humor vibe is wanted.
- **Stheno/Sao10K (L3-Stheno-8B, L3.1-Euryale-70B)** — not formally evaluated: 8B Stheno variants are valid alternatives to NeuralDaredevil-8B with strong prose-quality reputation in r/SillyTavernAI; they lack the abliteration + DPO recovery combination, so Tier-1.5 slur-vocabulary reliability is community-uncertain. The 70B Euryale class is out of the RTX 5080 VRAM tier.
- **Letta as primary memory (v1)** — deferred to v2 due to architectural lock-in and maintenance overhead. Correct upgrade path for true episodic recall [src: src33].
- **Zep / Graphiti** — rejected: Zep Community Edition is deprecated; self-hosting now requires running Neo4j/FalkorDB graph database, significant ops overhead for a single hobbyist [src: src22].
- **Full finetune on persona corpus** — rejected as overkill. QLoRA DPO achieves comparable persona adherence at a fraction of compute. Full finetune requires multi-GPU or cloud training at 8B+ scale [judgment: per structural analysis of the signal-to-compute ratio; no empirical head-to-head retrieved].
- **NovelAI Scroll $15/mo** — rejected: locks user to NovelAI's proprietary model (Erato, 70B Llama-3 based), no character card import from external formats, no user finetuning. Closed ecosystem is wrong fit for a power user [src: src34].

### Reframe alternatives (macro-contrarian)

The contrarian raised a genuine architectural reframe: the user asked "what's the best model" but the deeper goal is "companion that lives on my PC." SillyTavern is the default answer to a narrower version of the question.

The reframe: **solve the proactive-daemon problem first.** At the latency target needed for daemon-mode (sub-2-second response on brief messages), any Q5_K_M 8B model on an RTX 5080 is adequate. The orchestration layer — daemon initiation, desktop event hooks, scheduled proactive messages, voice trigger — is what makes the companion feel like a companion rather than a chat window. If the user builds SillyTavern-first and model-second, they get a great chat UI and not the proactive companion they described.

**Multi-model routing as a first-class architecture**: if the user wants "helpful + smart" for hard tasks and "personality-forward" for conversation, a local 8B personality model + OpenRouter Hermes 3 405B for hard tasks is a real and working pattern. OpenRouter's free-tier rate limit (200 req/day) makes this viable for routing occasional hard tasks but not daily conversation. [src: src13]

## 5. Open questions

- `[research-target-dropped]` LongMemEval scores for Letta vs Mem0: vectorize.io explicitly states Letta has not published LongMemEval results; the 83.2% / 49% figures in the draft were unverified and have been removed. Would be resolved by: Letta or Mem0 publishing benchmark results on LongMemEval, or an independent community reproduction.
- `[research-target-dropped]` Does Hermes 3 8B's instruction-following permissiveness extend to slur-as-punchline content with an explicit Tier 1.5 system prompt? Cannot resolve without empirical testing. Resolved by: one session with Hermes 3 8B + explicit permission directive on target content.
- `[research-target-dropped]` RTX 5080 empirical tokens/s for 8B Q5_K_M and 12B Q4_K_M GGUF: no benchmarks found in any retrieved source; speed estimates are bandwidth-math-derived. Would be resolved by a r/LocalLLaMA thread on RTX 5080 benchmarks (GPU is new as of early 2026; threads should appear within weeks).
- `[research-target-dropped]` Does llama.cpp `--control-vector` flag work reliably on Gemma 4 and Hermes 3 architectures? Published evidence (arXiv 2512.17639, OpenReview HpUDi5Pe8S) is on Llama 2/3 bases. Would be resolved by a direct community test report or academic paper on Gemma 4 activation geometry.
- `[research-target-dropped]` SillyTavern issue #5398 (Gemma 4 corrupted-output bug) — status as of May 2026. Contrarian flagged this as an active issue at April 2026 model launch; check the ST issue tracker before committing to Gemma 4 + ST workflow.
- `[external-event]` Memanto code release: arXiv 2604.22085 claims 89.8% LongMemEval with no ingestion cost — if code releases, may outperform all current memory options. Currently paper-only; no timeline.
- `[external-event]` Qwen-Scope Surgical Abliteration community RP uptake: released April 2026, technically superior to blunt abliteration. Watch r/LocalLLaMA for Qwen 3.5 7B abliterated releases in next 2-3 months.
- `[external-event]` Featherless / Infermatic / Arli AI actual Tier 1.5 enforcement in practice: TOS language suggests permissive; no independent user reports of racist/sexist slur content being allowed without account action were retrieved. Do not assume "unrestricted" marketing is operationally true until community confirms it.

## 6. Citations

- [src1] Arditi et al., "Refusal in Language Models Is Mediated by a Single Direction," arXiv 2406.11717, 2024. HN repost 2026-05-02, 113 pts. https://arxiv.org/abs/2406.11717 [corpus: bd70612fecc589d5]
- [src2] morgin.ai, "Even 'uncensored' models can't say what they want," morgin.ai, 2026-04-20. HN 178 pts. https://morgin.ai/articles/even-uncensored-models-cant-say-what-they-want.html [corpus: f1d9e8747d70b2eb]
- [src3] Smol AI/AINews, "Issue 2026-04-22: Gemma 4 for RP community," Smol AI, 2026-04-22. https://news.smol.ai/issues/26-04-22-not-much/ [corpus: 1cc77352103ea0bc]
- [src4] Smol AI/AINews, "Issue 2026-04-30: Qwen-Scope Surgical Abliteration," Smol AI, 2026-04-30. https://news.smol.ai/issues/26-04-30-not-much/ [corpus: 0f4bfa2ecd60f2f7]
- [src5] NousResearch, "Hermes 3 model card," nousresearch.com, 2024. https://nousresearch.com/hermes3
- [src6] NousResearch, "Hermes 4," hermes4.nousresearch.com, 2025-2026. https://hermes4.nousresearch.com/
- [src7] mlabonne, "NeuralDaredevil-8B-abliterated," Hugging Face, 2024-2025. https://huggingface.co/mlabonne/NeuralDaredevil-8B-abliterated
- [src8] swyxio, "April 2026 r/LocalLLaMA preferred models," GitHub Gist, 2026-04. https://gist.github.com/swyxio/324fc884061bf20e97a2ecbe59bae34a
- [src9] TrevorJS, "Gemma-4-E4B-it-uncensored-GGUF," Hugging Face, 2026. https://huggingface.co/TrevorJS/gemma-4-E4B-it-uncensored-GGUF
- [src10] huihui-ai, "Huihui-gemma-4-E2B-it-abliterated," Hugging Face, 2026. https://huggingface.co/huihui-ai/Huihui-gemma-4-E2B-it-abliterated
- [src11] Featherless.ai, "Pricing and model catalog," featherless.ai, 2026-05-04. https://featherless.ai/
- [src12] Featherless.ai, "Llama-3.3-70B-Instruct-abliterated model page," featherless.ai, 2026-05-04. https://featherless.ai/models/huihui-ai/Llama-3.3-70B-Instruct-abliterated
- [src13] OpenRouter, "Hermes-3-Llama-3.1-405B free tier," openrouter.ai, 2026-05-04. https://openrouter.ai/nousresearch/hermes-3-llama-3.1-405b:free
- [src14] Jack Clark, "Import AI #450," Import AI Substack, 2026-03-23. https://importai.substack.com/p/import-ai-450-chinas-electronic-warfare [corpus: 047c866f88ed4f91]
- [src15] Anthropic, "Persona Vectors: Monitoring and Controlling Character Traits," arXiv 2507.21509, 2025. https://arxiv.org/abs/2507.21509
- [src16] VCG Harvard, "Measuring and Controlling Persona Drift in Language Model Dialogs," arXiv 2402.10962, 2024. https://arxiv.org/html/2402.10962v1
- [src17] "Linear Personality Probing and Steering in LLMs: A Big Five Study," arXiv 2512.17639, 2024. https://arxiv.org/html/2512.17639
- [src18] "Steering LLM Interactions Using Persona Vectors," OpenReview HpUDi5Pe8S, 2025. https://openreview.net/forum?id=HpUDi5Pe8S
- [src19] SillyTavern, "Author's Note documentation," SillyTavern Docs, 2025-2026. https://docs.sillytavern.app/usage/core-concepts/authors-note/
- [src20] Unsloth, "Fine-tuning LLMs guide," Unsloth Docs, 2026. https://unsloth.ai/docs/get-started/fine-tuning-llms-guide
- [src21] Letta, "Letta (formerly MemGPT)," GitHub, 2026. https://github.com/letta-ai/letta
- [src22] Zep, "Graphiti Open Source," getzep.com, 2026. https://www.getzep.com/product/open-source/
- [src23] Mem0, "Open Source Overview," docs.mem0.ai, 2026. https://docs.mem0.ai/open-source/overview
- [src24] Hermes OS Blog, "AI agent memory systems 2026," hermesos.cloud, 2026. https://hermesos.cloud/blog/ai-agent-memory-systems
- [src25] DEV Community, "Mem0 vs Zep vs LangMem vs MemoClaw 2026," dev.to, 2026. https://dev.to/anajuliabit/mem0-vs-zep-vs-langmem-vs-memoclaw-ai-agent-memory-comparison-2026-1l1k
- [src26] Sebastian Raschka, "Components of a Coding Agent," Ahead of AI, 2026-04-04. https://magazine.sebastianraschka.com/p/components-of-a-coding-agent [corpus: 4b5942c9e4a3eb42]
- [src27] DaroHacka, "Sebastian Proactive: local-first AI companion," GitHub, 2026-05-02. https://github.com/DaroHacka/proactive-sebastian-ai-companion [corpus: 627bab872f2d3ea2]
- [src28] Smol AI/AINews, "Issue 2026-04-24: DeepSeek V4," Smol AI, 2026-04-24. https://news.smol.ai/issues/26-04-24-deepseek-v4/ [corpus: ca839a4412e50243]
- [src29] Simon Willison, "DeepSeek V4," simonwillison.net, 2026-04-24. https://simonwillison.net/2026/Apr/24/deepseek-v4/ [corpus: 3c34f8cea72e3788]
- [src30] knightli.com, "Running Qwen3.6 Locally: VRAM Requirements," knightli.com, 2026-05-01. https://www.knightli.com/en/2026/05/01/qwen3-6-local-vram-quantization-table/
- [src31] WillItRunAI, "Qwen3 GPU requirements," willitrunai.com, 2026-05-04. https://willitrunai.com/blog/qwen-3-gpu-requirements
- [src32] Compute Market, "Qwen3 local hardware guide 2026," compute-market.com, 2026-05-04. https://www.compute-market.com/blog/qwen-3-local-hardware-guide-2026
- [src33] vectorize.io, "Mem0 vs Letta: AI Agent Memory Compared 2026," vectorize.io, 2026. https://vectorize.io/articles/mem0-vs-letta
- [src34] NovelAI, "Subscription documentation," docs.novelai.net, 2026-05-04. https://docs.novelai.net/en/subscription/
- [src35] Anthracite-org, "Magnum v4-22B HuggingFace discussion," HuggingFace, 2025. https://huggingface.co/anthracite-org/magnum-v4-22b/discussions/1
- [src36] HuggingFace Daily Papers, "Memanto: Typed Semantic Memory," HuggingFace, 2026-04-23. https://huggingface.co/papers/2604.22085 [corpus: fc1996f5527fec3d]

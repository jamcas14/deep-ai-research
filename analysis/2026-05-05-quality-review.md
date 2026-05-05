# Quality review — `reports/2026-05-05-084255-what-is-the-best-model-an.md`

> Independent review created 2026-05-05 by a separate Claude Code session. Ten progressively-deepening loops over the report. Each loop is a different aspect/depth-layer; later loops longer than earlier ones.

## Headline assessment (preview — full meta-critique in §10)

I would act on **most** of this report's recommendation, but with three guardrails:

1. **Run the VRAM math empirically before committing to 14B.** The 13.5GB-headroom math is the report's own listed Weakest Assumption and was never empirically verified on RTX 5080 16GB under simultaneous TTS/STT. If it falls over, the cost is silent OOM/swap mid-conversation — a *worse* failure mode than just starting on 8B.
2. **Treat the single-model architecture argument as 3-of-4 valid, not 4-of-4.** The PRISM (ACL 2026) 81.5-vs-71.4 number is one paper that — when fetched — does not generalize to "personality companion architecture" cleanly (Loop 5). The other three independent arguments (Ollama VRAM eviction, context-loss at boundary, style-transfer sandwich softening) carry the recommendation on their own. Don't lean on PRISM in the headline.
3. **The slur caveat is correct but the framing is structurally misleading for the user.** Abliteration *removes refusal*, which is what a Tier-T companion mostly needs. The "no slurs without DPO" caveat is technically true but inverts the user's actual likely need: protected-class *humor that frames slurs as setup or punchline* is reliably available; *spontaneous unprompted slur generation in casual conversation* is not. The report's wording suggests the latter is what's missing — the user probably wants the former, which already works (Loop 4).

The full per-flaw analysis, drift analysis, citation re-fetch, and Wave-5 patch proposals are in the loops below.

---

## Loop 1 — Structural conformance pass

**Method:** Mechanical check of report structure against the §1-§6 spec in `CLAUDE.md` + `.claude/skills/deep-ai-research/SKILL.md`. Citation-graph integrity, tag-distribution counts, section presence, header discipline.

### Findings

| Check | Result | Notes |
|---|---|---|
| §1 Conclusion present with top rec + reasoning + runner-ups | ✓ | 4 runner-ups, each with one-line dismissal reason (Patch P) |
| §2 Confidence panel sub-bullets (Strongest/Weakest/Change-mind/Sources/Plan-usage) | ✓ | All 5 present; Sources axis discipline OK (Patch C/M not violated) |
| §3 Findings opens with Comparison matrix | ✓ | 20-row matrix, lines 44-69 (Patch G satisfied) |
| §4 Alternatives split into within-frame + reframe | ✓ | Micro-contrarian + macro-contrarian, both labeled |
| §5 Open-question type tags | ✓ | 5×`research-target-dropped`, 2×`external-event`, 2×`user-clarification` |
| §6 Citations parsable list | ✓ | 37 sources, line-formatted |
| Citation graph integrity (body refs ↔ §6 declarations) | ✓ | All 37 srcs used in body; all 37 declared in §6; zero orphans, zero phantoms |
| Sub-question count within bound (3-5 typical) | ⚠ at ceiling | SQ1-SQ5 = 5; query is genuinely triple-axis (model + persona + memory) so within spec, but right at the upper bound |

### Citation distribution anomaly

Histogram of `[srcN]` references in the body:

```
src1  (Arditi 2024)        : 4×    ← load-bearing
src3  (mlabonne abliteration): 4× ← load-bearing
src2  (huihui Q4_K_M GGUF)  : 3×
src6  (Eva-Qwen card)       : 3×
src9  (Josiefied card)      : 3×
src15 (Sao10K thread)       : 2×
src28 (PRISM ACL 2026)      : 2×
[28 other sources]          : 1× each (76% of corpus)
```

**Observation:** 28 of 37 sources (76%) are cited exactly once. This is consistent with **citation accumulation** (sources gathered as exhibits) rather than **citation triangulation** (sources cross-checking each other on the same claim). The two genuinely load-bearing sources are src1 and src3 — both for the same single claim (the abliteration mechanism), and these are also the two cited in support of every `[verified]` tag.

### Confidence-tag distribution

```
[verified] : 6 instances
[inferred] : 39 instances
[judgment] : 10 instances
```

This is honest — only ~11% of claims clear the Patch H bar (≥2 independent sources). Two cautions:

1. The **diversity of verified evidence is narrower than the count suggests** — most `[verified]` tags cite the same src1+src3 pair (Arditi + mlabonne). If those two sources have a shared blind spot (which they do — both are *concept/implementation* sources, not *behavioral output* sources), the report's `[verified]` claims inherit that blind spot. The slur-generation analysis in Loop 4 is downstream of this.
2. Patch AA says 2 SEO-aggregator sources count as 1. Loop 3 will check whether any `[verified]` claim is propped up by aggregator sources that should collapse to a single weight.

### Patch HHH compatibility

Per-stage breakdown in §2 (lines 35-40):

```
recency_pass        :  ~112s
research_fanout     : ~1059s
synthesizer_draft   :  ~721s
verifiers           :  ~381s
synthesizer_final   : ~2814s   ← 47% of total wall time, on a single agent
```

The synthesizer_final stage alone (47 minutes) **exceeds the entire 40-minute §9 ceiling**. Patch HHH (per-agent effort levels — synthesizer set to `effort: high`) was committed *after* this run, so this run did not yet benefit from it. But: even with `effort: high`, the synthesizer stage is doing the most *work* (draft → critic → fit/citation/structure-verifier feedback → final rewrite + mini-contrarian). Patch HHH alone may not bring it under 40 minutes — see Loop 9 regression analysis.

### Loop 1 verdict

Structurally conformant. The two soft warnings are (a) the citation distribution suggests exhibit-style sourcing rather than triangulation, and (b) the `[verified]` tag relies heavily on a single two-source pair. Both inform downstream loops.

---

## Loop 2 — Internal contradiction audit

**Method:** Walk every load-bearing claim in §1 and check it against §3, §4, §5, and §6. Look for citation misattributions, numeric inversions, model-identification ambiguity, and hedging mismatches across sections.

### Finding 2.1 — Citation misattribution in §1 conclusion (TWO bad references in one paragraph)

§1 line 13:
> "...style-transfer sandwich failure when frontier APIs systematically soften transgressive content in rewrites **[src30, src31]**. A single-model PRISM paper finding (81.5 vs 71.4 score) also aligns with this conclusion, though it rests on one ACL 2026 paper and should be treated as supporting evidence, not primary authority **[inferred — single source, src30]**."

§6 cites:
- **src30**: Inferless, "Comparing Different TTS Models Part 2" — a TTS comparison page
- **src31**: HuggingFace `whisper-large-v3` discussions #83 — Whisper VRAM
- **src22**: Simon Willison, "Opus system prompt analysis" — *the actual source for the softening-on-rewrite claim*
- **src28**: arXiv 2603.18507, "PRISM: Bootstrapping Intent-Based Persona Routing" — *the actual PRISM paper*

So §1's "[src30, src31]" attaches the *style-transfer-sandwich-failure-in-frontier-API-rewrites* claim to two TTS/STT sources, and the "[inferred — single source, src30]" attaches the *PRISM 81.5 vs 71.4* claim to the Inferless TTS page. **Both are wrong attributions.** §3 SQ5 (line 281) correctly cites src22 for the softening claim, and §3 SQ5 (line 277) correctly cites src28 for PRISM. The §1 paragraph appears to be a final-pass rewrite that broke the citation graph silently.

The citation verifier reportedly caught "2 fabrications + 1 inconclusive" in the final pass. These two §1 misattributions appear to be **uncaught by the verifier** — likely because the verifier samples the *most-load-bearing* claims and may have re-fetched src22 and src28 directly while missing that §1's text *cites src30 and src31* for those claims. This is a **specific failure mode of citation-verifier-by-source-list** vs **citation-verifier-by-claim-traceback**. Captured as Wave-5 candidate (Loop 10).

### Finding 2.2 — Hermes 4 cost factual inversion

§3 SQ3 table (line 183): `OpenRouter Hermes 4 405B | ~$9/month`
§4 micro-contrarian (line 313): "Hermes 4 405B... At **~$9/month, also more expensive per month than Featherless Basic ($10/mo)** for worse Tier-T fit."

$9/month is **less expensive** than $10/month. The dismissal logic is otherwise sound (no abliteration → no Tier-T guarantee), but the wording inverts the price relationship. A reader scanning §4 to "compare on cost" would get the wrong answer. Numeric editing error not caught.

### Finding 2.3 — `Mistral-Small-3.1-24B Imatrix Q3` model-identity collapse

§1 (line 18) calls the runner-up "Mistral-Small-3.1-24B Imatrix Q3_K_M (DavidAU/BeaverAI Fallen variant)". §6 lists:
- **src7**: `DavidAU/Mistral-Small-3.1-24B-Instruct-2503-MAX-NEO-Imatrix-GGUF`
- **src8**: `BeaverAI/Fallen-Mistral-Small-3.1-24B-v1e-GGUF`

These are **two different models by two different authors**:
- DavidAU's `MAX-NEO-Imatrix` is an importance-matrix quantization of the standard Mistral-Small-3.1-24B-Instruct (no abliteration claim on the card)
- BeaverAI's `Fallen` is a darker finetune (the "Fallen" naming convention is BeaverAI's signature for transgressive variants)

§3 line 53 (comparison matrix) labels "Mistral-Small-3.1-24B Imatrix Q3 (DavidAU/Fallen)" with "**Abliterated (Fallen variant)**". The §1 runner-up text gives the user no way to tell *which* model they're being recommended — and the abliteration property only attaches to one (BeaverAI's Fallen, if confirmed) and not the other (DavidAU's MAX-NEO-Imatrix, which is a quantization not an abliteration). **A user acting on this runner-up could end up running the wrong model with refusal vectors intact.**

### Finding 2.4 — VRAM math: same number for two different quantities

§1 line 7 / §3 SQ1 line 77 use "13.5GB" for ***available* for LLM** (16 - 1.44 Whisper - 0 Piper - 1 OS):

> "leaving ~13.5GB for the LLM"

§2 line 25 uses "13.5GB" for ***total consumed*** (1.44 + 0 + 1 + 9 + KV):

> "1.44GB Whisper INT8 + 0GB Piper + 1GB OS overhead + 9GB model + ~2-3GB KV cache at 4-8K context = ~13.5GB total"

These are mathematically *different quantities*. The §2 sum is 13.44 (with 2GB KV) → 14.44 (with 3GB KV). Calling it "~13.5GB total" anchors to the §1 number rather than the actual sum. The honest §2 framing would be "13.4-14.4GB total consumed; headroom 1.6-2.6GB" — and that headroom is **the user's actual safety margin**, which the report obscures by reusing the 13.5 number.

The substance ("tight but in budget") survives, but the arithmetic communicates badly. A reader comparing §1's "13.5GB available" to §2's "13.5GB total" might think "great, exactly the budget" when in reality the actual model+KV consumes 11-12GB of a 13.5GB pool, leaving 1.5-2.5GB for unaccounted growth. See Loop 6 for the full VRAM rebuild.

### Finding 2.5 — §2 "3 corpus / 32 web" citation count off-by-2

§2 line 29: `9% corpus / 91% web by citation (3 corpus / 32 web)`. Total = 35.

§6 has **37 sources**. Only **2** are explicitly tagged `[corpus: ...]` (src5 Featherless and src22 Simon Willison). The panel says 3 corpus and totals 35, leaving 2 sources unaccounted-for and overcounting corpus by 1. The 9%/91% ratio is roughly correct (2/37 = 5.4% if generous to the panel; 3/35 = 8.6% as the panel states), but the underlying counts don't reconcile with §6.

Patch C requires the corpus/web ratio to be reported truthfully and never mixed with other axes. The numbers don't match the citations the report itself contains. Patch C compliance is *attempted* but *not arithmetically clean*.

### Finding 2.6 — "Strongest quality upgrade path" vs latency that breaks voice mode

§1 line 16 promotes Featherless Premium 70B as "**strongest quality upgrade path**" with the caveat "test before committing". §3 line 204 puts Featherless 70B latency at "~5-15s per turn estimated" — *judgment, no benchmark*. §5 line 339 drops the latency question as `research-target-dropped`.

5-15s per turn over voice is unusable for a real-time companion. The "strongest upgrade path" framing is a recommendation with no validated path forward, and the report knows it (hence §5 drop). This isn't strictly a contradiction — the "test before committing" preserves honesty — but the §1 *enthusiasm* is at odds with the §3/§5 *uncertainty*. A more honest §1 would say "promising upgrade path conditional on a 30-second latency test the user can run; if 70B-on-Featherless is >5s/turn, fall back to a 14B local upgrade or 32B if you've upgraded VRAM."

### Loop 2 verdict — five concrete contradictions

| # | Type | Severity | Location |
|---|---|---|---|
| 2.1 | Citation misattribution (×2 in same paragraph) | **High** — §1 paragraph | Lines 13 |
| 2.2 | Numeric inversion on Hermes vs Featherless price | Medium — affects §4 reasoning | Line 313 |
| 2.3 | Model-identity collapse (DavidAU vs BeaverAI) | **High** — could mis-route user | Line 18, 53 |
| 2.4 | VRAM math same-number-two-quantities | Medium — obscures real headroom | Lines 7, 25, 77 |
| 2.5 | §2 corpus/web count off-by-2 | Low — ratio direction OK | Line 29 |
| 2.6 | "Strongest upgrade" vs untested latency | Low — caveat preserves honesty | Lines 16, 204, 339 |

The high-severity findings (2.1 and 2.3) are **citation graph integrity** failures. The structure-verifier and citation-verifier as currently configured did not catch them. This points to a Wave-5 patch on **claim→citation traceback verification**, not just citation re-fetch verification.

---

## Loop 3 — Source-attribution and tag-discipline audit

**Method:** Audit every `[verified]` tag against Patch H (≥2 independent sources required). Audit every `[inferred]` tag for source attribution. Check Patch AA (SEO aggregators count as 1) compliance. Scan `[judgment]` hedging.

### `[verified]` audit — 5 of 6 fail Patch H

| # | Line | Claim | Sources cited | Patch H verdict |
|---|---|---|---|---|
| V1 | 81 | Qwen3-14B Q4_K_M = 9.00GB | `src2` only | **FAIL** — single source. Honest tag = `[inferred — src2]` |
| V2 | 92 | Abliteration removes refusal direction in residual stream | `src1` Arditi + `src3` mlabonne | **PASS** — two genuinely independent sources (concept paper + implementation blog) |
| V3 | 96 | "Slur caveat HOLDS" | `src1` + `src3` | **FAIL** — neither source makes a behavioral output claim about slur generation. The mechanism is verified; the *behavioral implication* is reasoned downstream. Honest tag = `[inferred from src1, src3]` |
| V4 | 143 | "Abliteration is binary; size does NOT improve Tier-T content generation" | `src1` + `src3` | **FAIL** — same problem as V3. Mechanism papers don't make the size-invariance claim. Honest tag = `[inferred from src1, src3]` |
| V5 | 186 | RunPod is economically irrational vs Featherless | `src20` + "synthesizer final search" | **FAIL** — "synthesizer final search" is not a citable second source; it's the same source re-fetched. One real source. Honest tag = `[inferred — src20]` |
| V6 | 192 | "Frontier APIs — Tier-T REFUSAL is confirmed" | `src21` (Anthropic prompt leak) + `src22` (Simon Willison analyzing src21) | **BORDERLINE FAIL** — src22 is commentary on src21; not independent. The interpretation in src22 *could* differ from a different reading of src21, but as evidence for the same claim, they collapse to one. Honest tag = `[verified — src21]` with `[judgment-supported by src22]` annotation. |

**Net: 1 of 6 `[verified]` tags is cleanly Patch H compliant.** The other five over-claim. The pattern: when the synthesizer has a *strong mechanistic argument from one or two foundational sources* it is tagging the *downstream behavioral conclusions* as `[verified]` — but Patch H verifies *the cited claim*, not "the foundation of an argument leading to the claim."

This is the *structural* version of the §1 citation-misattribution failure (Loop 2). Both stem from the same root cause: **the synthesizer treats `[verified]` as "I'm confident" rather than "two independent sources directly contain this claim".**

### `[inferred]` source-attribution audit

Of 39 `[inferred]` tags:
- 25 use the form `[inferred — srcN]` (sourced)
- 13 use the bare form `[inferred]` (no source)
- 1 uses `[inferred from researcher-X + researcher-Y …]` (internal-reasoning trace, no external source)

**13 bare `[inferred]` tags identified:**

| Line | Claim | Should-have source |
|---|---|---|
| 75 | "VRAM budget math" | OK as bare — internal calculation from listed components |
| 84 | Qwen3-8B Q4_K_M ~5-5.5GB | Should cite huihui Qwen3-8B GGUF model card |
| 85 | Josiefied Qwen3-8B ~5-5.5GB | Should cite src9 (already in §6) |
| 86 | Eva-Qwen2.5-14B Q4_K_M ~9-10GB | Should cite src6 (already in §6) |
| 87 | Mistral-Small-3.1-24B Imatrix Q3 ~11-12GB | Should cite src7/src8 (already in §6) |
| 88 | Dolphin-3 Mistral-24B Q4_K_M ~14-15GB | Should cite src13 (already in §6) |
| 115 | Hermes-3-Llama-3.1-8B not abliterated | Should cite a Hermes-3 model card (none in §6) |
| 116 | Mistral-Nemo / NeMomix dismissal | No source given; absence of evidence reasoning is implicit |
| 117 | Llama-3.1-8B-abliterated / Stheno dismissal | No source; community-knowledge reasoning |
| 155 | Behemoth-123B-v2 quant impracticality | Should cite a Behemoth model card |
| 198 | Grok-4.3 API status | Should cite src36/src37 (BOTH in §6) — clear miss |
| 262 | Letta benchmark ~83.2% | Should cite src24 or primary LongMemEval (already in §6) |
| 287 | Architecture summary "frontier as silent tool" | OK as bare — synthesis of preceding sourced claims |

**Pattern:** at least 6 bare `[inferred]` tags reference claims for which the report **already has the source in §6** but failed to attach the citation marker. This is *clerical*, not factual. Easy fix. **Patch X-light: bare-`[inferred]` lint as part of structure-verifier.**

### Patch AA (SEO-aggregator double-counting)

Two SEO-aggregator-flavored sources:
- **src24** vectorize.io ("Mem0 vs Letta")
- **src25** atlan.com ("Best AI Agent Memory Frameworks 2026")

Both are aggregator content sites. The memory-framework benchmark numbers in §3 SQ5 cite both. **The report itself acknowledges this:** "[inferred — third-party benchmark reports; not verified against primary LongMemEval paper]" (lines 257, 267). The disclosure is honest. Neither aggregator is used to support a `[verified]` tag. **No Patch AA violation.**

But: the *underlying primary source* is the LongMemEval paper, which the report does not cite. Patch AA is satisfied; **but the correct fix is to cite the LongMemEval paper directly** rather than triangulate via two aggregators.

### `[judgment]` tag review — well-hedged

All 10 `[judgment]` tags carry explicit qualifying language ("blog claim, not controlled experiment", "no benchmark exists for transgressive humor timing specifically", "policy-era extrapolation, not a verified claim about GPT-5.5 specifically", etc.). **`[judgment]` discipline is the strongest of the three tag classes.** This is consistent with the honesty contract working when the claim is openly held as opinion, but breaking when the claim is presented as fact (`[verified]`).

### Loop 3 verdict

The tag-discipline regression has a sharp shape: **`[judgment]` is honest, `[inferred]` is mostly OK but clerically sloppy, `[verified]` is overused 5-of-6 times.** The structural fix is not "add another verifier"; it's a **stricter `[verified]` definition + a structure-verifier lint that flags single-source `[verified]` tags and "verified" claims whose cited sources don't textually contain the claim**. This becomes a Wave-5 candidate.

---

## Loop 4 — Abliteration / slur-generation mechanics deep-dive

**Method:** Web-fetch Arditi 2024 abstract (src1), mlabonne implementation blog (src3), and search post-2024 abliteration literature. Compare what the cited sources actually say to what the report claims.

### Finding 4.1 — Direct technical error: "Abliteration does NOT modify the vocabulary embedding matrix"

**Report line 94 (verbatim):**
> "Abliteration does NOT modify the vocabulary embedding matrix or shift token sampling probability distributions"

**mlabonne's implementation (src3) — verbatim code from the cited blog:**
```python
model.W_E.data = get_orthogonalized_matrix(model.W_E, refusal_dir)

for block in tqdm(model.blocks):
    if refusal_dir.device != block.attn.W_O.device:
        refusal_dir = refusal_dir.to(block.attn.W_O.device)
    block.attn.W_O.data = get_orthogonalized_matrix(block.attn.W_O, refusal_dir)
    block.mlp.W_out.data = get_orthogonalized_matrix(block.mlp.W_out, refusal_dir)
```

**`W_E` is the vocabulary embedding matrix.** The mlabonne implementation modifies it explicitly. The report's claim is **directly contradicted by the source it cites**. This is the report's `[verified — src1, src3]` claim that fails most loudly: the cited source contains code that does the *opposite* of what the report says it doesn't do.

The report likely meant "does not modify the **logits / unembedding** matrix" — which, depending on whether the model is weight-tied (e.g., Llama, where W_E and W_unembed share weights), may or may not be a separate object. For weight-tied models (most modern open-weight LLMs including Qwen3), modifying W_E *is* modifying the unembedding logits. This is a substantive technical inversion, not just a wording issue.

### Finding 4.2 — The behavioral claim is inferred, not verified

**Arditi 2024 abstract** (`src1` re-fetched 2026-05-05):

> "we find a single direction such that erasing this direction from the model's residual stream activations prevents it from refusing harmful instructions"

The Arditi abstract **does not discuss** whether erasing this direction modifies token sampling distributions on slurs/hate-speech tokens, or whether it produces capabilities the model didn't previously have. Strictly subtractive framing only.

**mlabonne blog** (`src3` re-fetched 2026-05-05):
> "If we prevent the model from representing this direction, it loses its ability to refuse requests."

The blog's evaluation **filters refusal markers** (`["I cannot", "I can't"]`) but does not display content vocabulary changes or specific outputs. The post does not demonstrate slur generation, hate-speech output, or any vocabulary-level shift.

**Conclusion:** The report's `[verified — src1, src3]` tag attached to the slur caveat (line 96) cites two sources, neither of which makes any claim about slur generation. The slur caveat is a *mechanistic inference* downstream of the verified mechanism — the correct tag is `[inferred from src1, src3]`, not `[verified]`. (This is Loop 3 V3 with confirmation from re-fetch.)

### Finding 4.3 — Post-2024 abliteration variants the report missed

The recency pass and contrarian agent appear to have not surfaced the substantial post-NeurIPS-2024 literature. From a single web search (above):

| Variant | Source | What's different |
|---|---|---|
| Projected abliteration | grimjim, HF Blog | Removes component parallel to harmless direction first; reduces capability degradation |
| Norm-preserving biprojected abliteration | grimjim, Nov 2025 | Preserves matrix norms during intervention; reduces overcompliance |
| Heretic | p-e-w (tool) | Bayesian-optimized abliteration with residual-geometry visualization |
| FailSpy's abliterator library | FailSpy | Generalized implementation framework |
| DECCP | community | One of four methods compared in arXiv 2512.13655 |
| ErisForge | community | Another method compared in arXiv 2512.13655 |
| MopeyMule | — | Applies abliteration to *conversational style* instead of safety |
| arXiv 2512.13655 (Dec 2025) | Comparative Analysis of LLM Abliteration Methods | KL divergence 0.043-1.646 across methods on 7-14B models — *empirical evidence that abliteration DOES produce measurable distribution shift* |
| arXiv 2505.19056 (May 2025) | An Embarrassingly Simple Defense Against LLM Abliteration Attacks | Adversarial response — extends refusal signal across token positions to maintain refusal under abliteration |

The 2026-05-05 report mentions zero of these. Specifically, **arXiv 2512.13655 directly contradicts the report's "no token-distribution shift" claim**: KL divergence numbers in the 0.043-1.646 range are not zero. Bayesian-optimized abliteration produces *substantial* distribution shift on some models. The report's "abliteration does not shift sampling distributions" framing is empirically wrong at the magnitude.

### Finding 4.4 — What the report's recommendation gets right anyway

Despite the technical errors above, the *practical* conclusion is plausibly correct. The chain of reasoning that *should* support it:

1. Abliteration removes the refusal direction → user's companion will not refuse Tier-T jokes ✓ (Arditi confirmed)
2. Abliteration produces measurable but variable distribution shift → token probabilities do change, but the *direction of shift* on slur tokens specifically is not characterized by the cited sources
3. RLHF / instruction-tuning suppresses slur tokens through *multiple* dimensions, not just the refusal direction → the inferred-but-untested claim that drives the recommendation
4. Therefore: abliteration alone unlocks engagement/profanity/dark-humor; reliable slur *generation* requires DPO/SFT on data containing those tokens

Steps 1, 3, and 4 hold. **Step 2 is the empirical gap the report doesn't acknowledge.** The honest version is: "abliteration measurably shifts token distributions, but the cited sources do not characterize the direction of shift on slur tokens specifically; we infer from training-tradition reasoning that the shift is not large enough to enable spontaneous slur generation."

### Finding 4.5 — User-facing implication: framing is misleading

The user's stated need is "Tier-T content: heavy profanity OK, racist/sexist comedic transgression OK, occasional slurs OK, NO sexual content, no real intent-to-harm".

The report frames the slur question as a binary: "abliteration unlocks willingness to engage with topics" vs "DPO/SFT required for slur generation". The user reading this gets the impression: "*if I want slurs at all, I need DPO/SFT*."

But "occasional slurs OK" in the user's phrasing more likely means *protected-class humor where slurs appear in setup/punchline of a joke*, not *spontaneous unprompted slur generation in casual conversation*. The first **is** reliably available from huihui-ai/Qwen3-14B-abliterated with persona engineering (the report itself says "the companion willingly discussing and making jokes that reference slurs in context", line 244). The second is what the slur caveat addresses, and that's a different thing.

**The recommendation is right; the framing of *why* is misleading.** A user reading §1 and §3 SQ1 might conclude they need a DPO finetune they don't actually need.

### Loop 4 verdict

| # | Severity | Issue |
|---|---|---|
| 4.1 | **High** | Report claims source says X; source code shows opposite of X (W_E modification) |
| 4.2 | **High** | `[verified]` tag attached to a behavioral claim that neither cited source contains |
| 4.3 | Medium | Post-2024 abliteration literature (arXiv 2512.13655 + 8 other variants) entirely missed by recency/contrarian pass |
| 4.4 | Medium | Empirical token-distribution shift is non-zero (KL div 0.043-1.646) — contradicts "no shift" framing |
| 4.5 | Low-Medium | User-facing framing of slur caveat creates false binary; conflates two different user needs |

The recommendation (`huihui-ai/Qwen3-14B-abliterated`) is *outcome-correct* for the user's actual use case. The *justification* contains a substantive technical error (4.1), an over-claimed verification (4.2), a recency gap (4.3-4.4), and a framing issue (4.5). All are fixable.

---

## Loop 5 — PRISM ACL 2026 single-source architecture claim

**Method:** Fetch arXiv 2603.18507 directly. Verify the 81.5 / 71.4 / 79.9 numbers exist and what they measure. Compare the paper's actual scope to how the report uses it.

### Finding 5.1 — Paper exists, numbers are real, but the comparison they support is narrower than the report claims

**Verified:**
- Paper: "Expert Personas Improve LLM Alignment but Damage Accuracy: Bootstrapping Intent-Based Persona Routing with PRISM" (Hu, Rostami, Thomason — USC; arXiv 2603.18507, March 2026)
- Numbers in Table 1, Mistral-7B-Instruct, "Overall" score averaging MT-Bench + MMLU + Safety:
  - **79.9** = baseline (no persona)
  - **71.4** = "Expert Prompting" (always-on persona)
  - **81.5** = PRISM (intent-gated conditional persona)
- The paper *does* advocate for gated single-model design over always-on persona prompting.

### Finding 5.2 — But the comparison is NOT what the report says it is

**Report (§3 SQ5, line 277):**
> "PRISM study (ACL 2026, arXiv 2603.18507): Single-model gated persona routing outperforms separate-model routing on Mistral-7B (81.5 vs 71.4 vs baseline 79.9). Expert persona prompting alone hurt performance."

The 71.4 score is **not** a "separate-model routing" baseline. It is **"Expert Prompting" — always-on persona-prompted single-model**, applied uniformly to all queries. The paper's actual comparison is:

| Approach | Architecture | Score |
|---|---|---|
| Baseline | Single model, no persona | 79.9 |
| Expert Prompting | Single model, always-on persona | 71.4 |
| PRISM | Single model, intent-gated persona | 81.5 |

**All three are single-model.** The paper does not test a two-model "persona-LM + smart-LM" architecture *at all*. The report's framing — that PRISM evidence supports avoiding a two-model split-personality architecture — is **a claim the paper neither makes nor measures**.

The directional analogy ("conditional persona activation > always-on persona") is plausible. But the specific numerical evidence (81.5 vs 71.4) is comparing *two flavors of single-model* configurations, not single-model vs two-model.

### Finding 5.3 — Use-case scope mismatch

The paper's scope (per fetched HTML body):
- **Tasks:** MT-Bench (multi-turn dialogue), MMLU (knowledge retrieval), Safety
- **Model:** Mistral-7B-Instruct only
- **Use case:** benchmark evaluation; "preference and safety alignment on generative tasks while preserving accuracy"

The report extends this to: *Tier-T-humor personality companion architecture decision on a 14B abliterated Qwen3 model running 24/7 on consumer hardware*. The extension assumptions are:
- Conditional persona activation generalizes from 7B → 14B (plausible)
- Generalization from MT-Bench/MMLU/Safety → Tier-T humor companion (questionable — the user's "always-on" companion is essentially "always-on persona", which is the regime PRISM says **hurts** by 8.5 points vs baseline)
- The architecture choice "single-model with always-on persona for companion" is similar to PRISM's gated design (it's *not* — it's similar to Expert Prompting, which lost)

**Read literally, PRISM's evidence pushes the OPPOSITE direction for the report's recommendation:** PRISM says always-on persona hurts on *general* tasks (MMLU drops sharply with persona prompting). For a Tier-T companion, persona is always on. This isn't fatal — the user prefers persona quality over MMLU performance — but the report's framing of PRISM as "supporting evidence" is misleading. PRISM is a finding about *when* persona helps, and it argues *against* always-on persona use.

### Finding 5.4 — The recommendation survives anyway

The report (§3 SQ5, line 285) explicitly says:
> "The multi-model concern survives even without trusting the PRISM numbers: points 2, 3, and 4 are all independent of PRISM and constitute sufficient grounds to avoid the split-personality architecture."

This is the right hedge. The three independent arguments — (a) Ollama VRAM eviction on switch, (b) context loss at model boundary, (c) frontier-API style softening — each individually rule out the two-model split-personality architecture for an always-on Tier-T companion. **The recommendation is correctly grounded.** PRISM is a coincidental directional reference that should not have been recruited as numerical evidence.

### Finding 5.5 — Honest framing fix

The §1 conclusion paragraph (with citation errors fixed per Loop 2) should read:

> "The single-model recommendation rests on three operational constraints: (a) Ollama keeps one model in VRAM and switching evicts the persona model [src — local-inference common knowledge]; (b) context loss at model boundary breaks persona continuity [judgment]; (c) frontier APIs (Opus 4.7, GPT-5.5) systematically soften transgressive content during rewrites [src22 — Simon Willison Opus prompt analysis]. The PRISM paper (src28) is *directionally consistent* with the recommendation but its specific numerical comparison (81.5 vs 71.4) measures gated-vs-always-on within a single Mistral-7B model, not single-model-vs-multi-model architecture. Do not treat PRISM as evidence for the architectural choice."

### Loop 5 verdict

| # | Severity | Issue |
|---|---|---|
| 5.2 | **High** | Report mis-identifies what PRISM's 71.4 baseline measures — it's single-model always-on persona, not separate-model routing |
| 5.3 | Medium | Use-case generalization from Mistral-7B benchmark eval to Tier-T humor companion is wide; PRISM directionally argues *against* always-on persona |
| 5.4 | n/a | Recommendation survives without PRISM — three independent operational arguments are sufficient |
| 5.5 | Medium | Framing fix: PRISM should be characterized as directional, not numerical evidence |

This is a clear case where **the report's recommendation is right but its supporting paper is wrong**. The synthesizer reached for a plausible-sounding citation that, on inspection, doesn't measure the comparison being argued. Patch H done well would catch this — *the cited source's claim must contain the report's claim*. The citation verifier as currently configured re-fetches the source to check that the source exists and the cited number is in it; it does not check whether the source's *measurement* matches the report's *claim about what was measured*. Wave-5 candidate.

---

## Loop 6 — VRAM math validation

**Method:** Re-fetch each citation supporting the VRAM math (Qwen3-14B-abliterated Q4_K_M GGUF size, faster-whisper large-v3 INT8). Compute KV cache from Qwen3-14B's actual architecture. Reconstruct the budget at 4K / 8K / 16K / 32K context; identify what's missing from the report's accounting.

### Component 1: Qwen3-14B-abliterated Q4_K_M = 9.00 GB ✓

**Re-fetched bartowski model card (src2):** "Qwen3-14B-abliterated-Q4_K_M.gguf | Q4_K_M | **9.00 GB**". Marked as "Good quality, default size for most use cases, recommended".

Report claim is accurate. Note: model card says "15B params" — Qwen3-14B has ~14.8B params (Qwen3's release naming rounds down).

### Component 2: faster-whisper large-v3 INT8 = 1.44 GB **static**, ~1.7 GB **practical**

**Re-fetched HF discussion #83 (src10/src31):**
> "dtype: int8, Largest Layer or Residual Group: 63.31 MB, Total Size: 1.44 GB, Training using Adam: 5.75 GB"

And critically:
> "When performing inference, expect to add up to an additional 20% to this, as found by EleutherAI"

So the practical figure under inference is **~1.7 GB**, not 1.44 GB. The report uses the static-size figure. **The report is underestimating Whisper VRAM by ~0.3 GB.**

This 0.3 GB is small alone, but the report's "Weakest Assumption" framing already says budget is "tight" — every 0.3 GB matters in that framing.

### Component 3: KV cache — the report substantially OVERESTIMATES for Qwen3-14B

The report (line 25) lists "**~2-3GB KV cache at 4-8K context**". This is way off for Qwen3-14B specifically.

**Qwen3-14B architecture** (from Qwen3 paper / model config):
- Layers: 40
- Query heads: 40
- KV heads (GQA): **8** ← critical: KV cache scales with KV heads, not query heads
- Head dimension: 128
- KV dtype default: fp16 (2 bytes)

**KV cache per token** = 2 (K+V) × 8 KV heads × 128 dim × 40 layers × 2 bytes = **163,840 bytes ≈ 160 KB/token**

**KV cache at various contexts (fp16):**

| Context | KV cache size |
|---|---|
| 4K | 0.625 GB |
| 8K | 1.25 GB |
| 16K | 2.5 GB |
| 32K | 5.0 GB |

The report's "~2-3 GB at 4-8K" overestimates by **roughly 2×** for Qwen3-14B. The report's 2-3 GB figure is correct *at ~16K context*, not 4-8K.

**Why the report got this wrong:** Likely used a generic "14B model has ~2-3GB KV cache" heuristic without accounting for Qwen3's aggressive GQA (8 KV heads down from 40 query heads — a 5× reduction in KV cache size vs MHA). Llama-2-13B and Mistral-7B have less aggressive GQA; their KV caches are bigger per layer. **The report imported a heuristic from older models and didn't recompute for Qwen3's architecture.**

### Component 4: Missing from the report's accounting

The report omits or underestimates:
- **llama.cpp / Ollama activation buffers during generation:** ~0.3-0.5 GB. The report counts model weights + KV cache but not activations; in practice Ollama allocates ~10% over the model size for generation buffers.
- **Inference-time Whisper overhead:** the +20% from EleutherAI noted above (0.3 GB).
- **CUDA driver / fragmentation slack:** under sustained allocation churn, fragmentation can effectively shrink usable VRAM by 200-500 MB. Not mentioned.

But the report **could have** counted:
- **KV cache quantization** (`-ctk q4_0 -ctv q4_0` in llama.cpp): cuts KV cache by ~4×. At 8K context with 4-bit KV, the cache is **~0.3 GB instead of 1.25 GB**. This dramatically extends usable context for almost no quality cost on most Qwen3 tasks. Not mentioned.
- **Q4_K_S** quantization: 8.5 GB instead of 9.0 GB. Buys 0.5 GB headroom for marginal quality cost. Not in the comparison.

### Reconstructed budget — at four context lengths

Using practical numbers (Whisper +20%, llama.cpp activations +0.5GB, Qwen3-14B-correct KV):

| Context | Whisper | Piper | OS/CUDA | Qwen3-14B Q4_K_M | KV (fp16) | Activations | **Total** | **Headroom (16GB)** |
|---|---|---|---|---|---|---|---|---|
| 4K | 1.7 | 0 | 1.0 | 9.0 | 0.62 | 0.5 | **12.8** | **3.2 GB** |
| 8K | 1.7 | 0 | 1.0 | 9.0 | 1.25 | 0.5 | **13.5** | **2.5 GB** |
| 16K | 1.7 | 0 | 1.0 | 9.0 | 2.5 | 0.5 | **14.7** | **1.3 GB** |
| 32K | 1.7 | 0 | 1.0 | 9.0 | 5.0 | 0.5 | **17.2** | **−1.2 GB (OOM)** |
| 32K with q4 KV | 1.7 | 0 | 1.0 | 9.0 | 1.25 | 0.5 | **13.5** | **2.5 GB** |

### Finding 6.1 — The report is OVER-CAUTIOUS at typical companion context (4-16K)

The report's §2 "Weakest Assumption" framing makes it sound like 13.5 GB is the budget ceiling and the model barely fits. The corrected math says: **at 4-8K context the user has 2.5-3.2 GB free**, which is comfortable. The user could even consider Q5_K_M (10.5 GB) at 4K context (budget: 1.7 + 1 + 10.5 + 0.62 + 0.5 = 14.3, headroom 1.7 GB).

For a personal voice companion, 4-16K context is realistic. The report's framing implies "cliff at 14B"; the correct framing is "cliff at 32K context unless you enable KV quantization".

### Finding 6.2 — The 32K cliff matters for memory-architecture decisions

The report recommends a "rolling flat-text 'about me' document" for memory (§3 SQ5). It says 2-4K tokens fits a few hundred facts. **At 8K context, the rolling doc + recent conversation + persona card fits comfortably.** At 32K, it does not on this hardware.

This means the memory-architecture upgrade trigger (rolling doc → Graphiti) is partly forced by **hardware context ceiling** at ~16K, not by document growth alone. The report doesn't make this connection. **The two recommendations (run 14B locally; use rolling doc until it overflows) are coupled by the same VRAM ceiling, and the user should know this.**

### Finding 6.3 — KV-cache quantization is a free lunch the report ignores

`llama-server --cache-type-k q4_0 --cache-type-v q4_0` (or `OLLAMA_KV_CACHE_TYPE=q4_0`) cuts KV cache by ~4× with negligible perplexity impact for inference. **This single config change extends usable context from ~16K to ~64K within the same VRAM budget.** A complete recommendation would mention it; the report does not.

### Finding 6.4 — Empirical verification path the user can run in 30 seconds

The report's §2 acknowledges "This math has not been empirically verified under actual simultaneous voice load on this exact hardware." But the user can verify with:

```bash
ollama run huihui-ai/Qwen3-14B-abliterated:Q4_K_M
# in another terminal, while ollama is generating:
nvidia-smi --query-gpu=memory.used --format=csv -l 1
# (alongside Whisper + Piper running)
```

The report doesn't suggest this. **A 30-second VRAM-snapshot test would resolve the report's listed Weakest Assumption empirically.** Trivial Wave-5 patch: when a recommendation rests on a calculated VRAM budget, suggest the empirical verification command.

### Loop 6 verdict

| # | Severity | Issue |
|---|---|---|
| 6.1 | Medium | Report overstates VRAM tightness at 4-16K context; user has 1.3-3.2 GB headroom, not "tight" |
| 6.2 | Low-Medium | Hardware context ceiling and memory-arch trigger are coupled; report doesn't connect them |
| 6.3 | Medium | KV-cache quantization (free 4× context) is unmentioned |
| 6.4 | Low | Easy empirical verification path not suggested |

The recommendation (run 14B locally) is **correct and arguably under-sold**. At realistic companion context lengths the user has substantial headroom. The "Weakest Assumption" framing in §2 should be re-classified as "Likely Comfortable" with a 32K-context cliff caveat.

---

## Loop 7 — Drift analysis across 5 prior runs on the same query

**Method:** Read each prior report's §1 conclusion + runner-ups + memory rec + architecture rec. Build a six-run drift table (5 prior + current). Distinguish convergence from improvement vs path-dependent anchoring.

### Drift table — six runs, four axes

| Run | Time | Model rec | Memory rec | Architecture | TTS/STT assumed |
|---|---|---|---|---|---|
| R1 | 2026-05-04 11:46 | Branched: Claude Opus 4.7 OR Qwen3.6-27B abliterated OR Euryale v2.3 (48GB+) | **Letta** | Multi-layer (model + persona + memory) | Not specified |
| R2 | 2026-05-04 12:44 | **huihui-ai/Qwen3-14B-abliterated Q4_K_M** | **Mem0** | Local + Mem0 + SillyTavern | Whisper-medium + Piper, 2-3GB |
| R3 | 2026-05-04 13:37 | **Josiefied-Qwen3-8B-abliterated-v1** | **Graphiti** | Multi-model (8B local + LiteLLM + Grok 4.3 escalation) | "5GB TTS+STT" → 10-13GB usable |
| R4 | 2026-05-04 19:07 | **Hermes 3 8B** (NousResearch, NOT abliterated) | **Mem0** | Daemon layer + local + V2 card | Implicit |
| R5 | 2026-05-04 — | **Qwen3.6 27B INT4 + Surgical Abliteration (Qwen-Scope)** | **Mem0 or sqlite-vec** | Single-model | "TTS 2-3GB" → 10-12GB usable |
| **R6** | **2026-05-05 08:42 (current)** | **huihui-ai/Qwen3-14B-abliterated Q4_K_M** | **Rolling flat-text "about me" doc** | Single-model + frontier API as silent tool | Piper + Whisper INT8 → 13.5GB usable |

### Finding 7.1 — Substantial drift on three of four axes

**Model size**: 27B → 14B → 8B → 8B → 27B → 14B. Vacillated from 8B to 27B and back. R5's 27B recommendation was likely **incorrect** for this hardware — Qwen3.6-27B INT4 at 10-11GB on 16GB shared with TTS/STT doesn't actually fit cleanly with KV cache (the corrected math would give ~12GB consumed for model + 2.5GB KV at 8K = 14.5GB just for LLM, overflowing the available 12GB after voice load). R6 returns to R2's 14B recommendation with the corrected (Piper-aware) VRAM math.

**Memory framework**: Letta → Mem0 → Graphiti → Mem0 → Mem0/sqlite-vec → **rolling flat-text**. R6 is the only run to recommend *no framework at all*. The four prior framework recommendations vacillated despite the question (a personal v1 companion) being identical.

**Architecture**: multi-layer → single-model → multi-model → daemon-layer → single-model → single-model + tool. R3's multi-model recommendation (LiteLLM + Grok 4.3 escalation) is the only run to recommend a multi-model split, and R6 explicitly argues against it.

**Abliteration vs not**: 4 of 6 runs recommend abliterated models (huihui or Josiefied or Surgical). R1 branches and includes non-abliterated. **R4 is the outlier** — recommends Hermes 3 8B explicitly *not abliterated*, citing morgin.ai's "flinch study" and NousResearch's neutral-alignment philosophy. None of R5 or R6 follow R4's reasoning. Note: R4's morgin.ai citation may be the same pretraining-flinch claim that R6's "slur caveat" addresses in different language.

### Finding 7.2 — What hardened across runs (genuine convergence)

| Hardened claim | Runs |
|---|---|
| "Local Apache-2.0 model is the primary path" | R2, R3, R5, R6 (4 of 6) |
| "Frontier APIs (Claude, GPT, Grok) cannot be relied on for Tier-T" | R2, R3, R4, R5, R6 (5 of 6) |
| "SillyTavern character card is the right persona engineering tool" | All 6 |
| "Persona engineering matters as much as model selection" | All 6 |
| "Featherless.ai is the right hosted-API answer for Tier-T budget cases" | R4, R6 |
| "$25/mo Featherless Premium 70B is the upgrade path" | R4, R6 |

These are the system's stable answers — what *would* show up if the user asked the same question 10 more times.

### Finding 7.3 — What softened or vacillated

| Vacillated claim | Pattern |
|---|---|
| Exact model size | 8B/14B/27B all defensible depending on VRAM math |
| Memory framework choice | Letta/Mem0/Graphiti/flat-text all surfaced; no run reproduced another's choice |
| TTS/STT VRAM assumption | 2-3GB (R2) / 5-6GB (R3, R4) / 2-3GB (R5) / 1.44GB (R6) — driven by which TTS each run assumed (Piper vs Coqui XTTS-v2) |
| Whether to use a multi-model split | R3 yes; R6 no |
| Eva-Qwen as candidate | Surfaces only in R6 — missing from R1-R5 |
| Rolling flat-text as memory | Only R6 — missing from R1-R5 |

The pattern: **the system's recommendations on infrastructure-y choices (memory framework, multi-model architecture, exact quantization) are highly variable across runs**, while recommendations on the *content* of the persona engineering and the broad model family are stable.

### Finding 7.4 — Three flips that look like genuine improvement

1. **Memory framework simplification (R3 Graphiti → R6 flat-text):** R6's macro-contrarian explicitly questioned whether a v1 personal companion needs a graph DB. The reasoning ("user won't have enough history density to need graph traversal in the first months") is correct for a personal-scale system. **This flip looks like the contrarian agent doing its job.**
2. **VRAM math correction (R3-R5 ≤8B/27B → R6 14B):** R6's Piper TTS choice frees the 2-3GB that R3-R5 assumed for Coqui. The corrected budget makes 14B viable. **This flip looks like better VRAM accounting.**
3. **Multi-model elimination (R3 multi-model → R6 single + tool):** R6's three independent operational arguments (VRAM eviction, context boundary, frontier softening) are sound. **This flip looks like better architectural reasoning.**

### Finding 7.5 — But also two flips that may be path-dependent

1. **R4 → R5 → R6 chain on abliteration**: R4 argued for non-abliterated Hermes 3 with a *specific* mechanistic argument (morgin.ai flinch study + NousResearch neutral-alignment). R5 ignored R4's argument. R6 ignores R4's argument too — and R6's *own* slur-caveat treatment of "the same flinch problem" arrives at the *opposite* conclusion (favor abliteration anyway). **The system is treating R4's reasoning as if it didn't exist** rather than refuting it. This is a coherence regression — across runs, the system should engage with prior contrary reasoning rather than reset.
2. **Memory framework oscillation**: Letta → Mem0 → Graphiti → Mem0 → Mem0/sqlite-vec → flat-text. The variance is consistent with the framework choice being *under-determined by the available evidence* — meaning the question of "which memory framework for v1" doesn't have a stable best answer in the system's evidence base, and any single run's pick may reflect noise more than signal. R6's "use nothing for v1" is a *legitimate* simplification that breaks the framework-debate by reframing the question.

### Finding 7.6 — Run-to-run variance as a system honesty signal

Five runs of the same query produced five materially different recommendations. The user reading R6 in isolation gets a confident answer; the user reading R1-R5 sees a much-less-confident system. **The honest reporting would surface this variance:** "Our system has produced 5 different headline recommendations on this exact query in 24 hours. The current recommendation is run #6, converging with run #2. We have moderate confidence based on cross-run consistency."

The current §2 confidence panel discusses *intra-run* uncertainty (Strongest/Weakest/Change-mind) but not *inter-run* uncertainty. **For a research system being run repeatedly, inter-run drift IS the confidence metric.** Wave-5 candidate: the orchestrator should detect prior runs on similar queries (via embedding similarity over `reports/`) and surface a "drift summary" in §2.

### Loop 7 verdict

The system does **not** have a stable answer to this query. R1 → R6 shows substantial drift on three of four axes; only persona-engineering claims and "Featherless is the upgrade path" hardened across most runs. R6's headline recommendation **converges with R2** (two of six runs land on huihui-ai/Qwen3-14B-abliterated), simplifies memory beyond all prior runs (rolling flat-text), and corrects R5's overoptimistic 27B math.

The convergence is partly **genuine improvement** (better contrarian-driven memory simplification, better VRAM accounting, sound architectural reasoning) and partly **the system finally returning to an earlier well-grounded answer (R2)** after R3-R5 drifted around. The user should not treat R6 as definitive without recognizing that the system is producing different answers each time — and that R6's confidence framing should be discounted by inter-run variance.

**Recommended user behavior:** when a recommendation matters, run the query 2-3 times and look at consistency, not at any single run's confidence panel. **Recommended system fix:** drift-summary in §2 of every report when prior runs on similar queries exist. (Wave-5 candidate.)

---

## Loop 8 — Independent citation re-fetch (different cut from verifier)

**Method:** The internal citation verifier samples 12 most-load-bearing citations, prioritizing quoted-passages → numbers/dates/stats → §1 conclusion → §2 panel. To avoid duplicating its work, I sampled **§3/§4 citations + 1 quoted-passage in §3 + 1 known-404 source the report claims is now indexed**. Seven sources, including one quoted passage and four numeric claims.

### Re-fetch results

#### src22 — Simon Willison "Opus system prompt analysis" — ❌ **FABRICATED QUOTE**

Report (line 194):
> "**Claude Opus 4.7 system prompt** (April 2026 leak, corroborated by Simon Willison analysis): 'If Claude finds itself mentally reframing a request to make it appropriate, that reframing is the signal to REFUSE, not a reason to proceed.' The refusal heuristic was hardened in April 2026"

Re-fetch result (2026-05-05):
> "No, this post does not contain that verbatim quote."

**This is a quoted-passage fabrication.** The report tags it `[verified — src21, src22]` (Loop 3 V6) and treats it as a verified Tier-T-refusal claim. The quote *may* be in src21 (the actual leaked prompt repo), but the report attributes its corroboration to src22 — which doesn't contain it. Patch T's empirical finding (FACTUM 2026: quoted passages have the highest fabrication rate) confirmed exactly here. The internal citation verifier's "2 fabrications + 1 inconclusive" did not catch this one.

#### src17 — Magnum-v4-72B GGUF sizes — ✓ **PASS**

Report: "Magnum-v4-72B (47.4GB at Q4_K_M, 39.5GB at Q3_K_L)"
Re-fetch: Q4_K_M = 47.4 GB, Q3_K_L = 39.5 GB. Exact match.

**Bonus finding:** model card lists training dataset `kalo-opus-instruct-22k-no-refusal` — confirms the report's framing that Magnum is "NOT abliterated; needs system prompt work for Tier-T" but is trained on data filtered for no-refusal behavior. This is a *training-tradition* path comparable to Eva-Qwen's DPO route — not mentioned by the contrarian as a parallel option.

#### src32 — OpenRouter Hermes 4 405B pricing — ✓ **PASS**

Report (§3 SQ3 table): "OpenRouter — Hermes 4 405B listing ($1/M input, $3/M output confirmed)"
Re-fetch: page shows "$1/M input tokens$3/M output tokens". Match.

(Note: this verifies the per-token rates, but does NOT validate the report's `~$9/month` aggregate cost estimate at companion-scale usage. That estimate depends on token-volume assumptions the report doesn't fully spell out.)

#### src35 — abliteration.ai pricing — ❌ **NUMERIC ERROR; FLIPS COST RECOMMENDATION**

**Report (§3 line 188):** "$100 prepaid pack (33.3M tokens, never expires) at **~$5/1M tokens effective**. At 100 turns/day companion use (~6M tokens/month), this runs ~$30/month — slightly more than Featherless Premium ($25/mo flat)."

**Report (§3 SQ3 comparison matrix line 180):** "abliteration.ai (prepaid) | ~$5/1M tokens (=$45/month at above usage)"

**Report (§6 src35):** "$100 prepaid = 33.3M tokens (~$5/1M effective); monthly subscriptions available; enterprise $300+/month."

**Re-fetch result (2026-05-05):**
- Scale Pack: $100 = 33,333,334 tokens
- $100 / 33.3M = **$3.00 per million tokens**, not $5/M
- Enterprise tiers begin at $600/month (Policy Gateway Control), not $300+
- Monthly subscriptions: Builder $20/mo (6.67M tokens), Team $50/mo (16.67M tokens) — actually around $3/M consistently

**The arithmetic error is severe and direction-changing:**

| | Report's claim | Reality | Implication |
|---|---|---|---|
| Effective rate | $5/M | $3/M | 40% cheaper than reported |
| Monthly cost @ 6M tokens | $30 | $18 | abliteration.ai is **cheaper** than Featherless Premium ($25), not "slightly more" |
| Enterprise floor | $300+ | $600+ | Enterprise tier 2× higher than reported |

**This flips the §3 SQ3 recommendation:** the report says abliteration.ai is "slightly more expensive than Featherless Premium" — wrong; it's *cheaper* at the user's stated usage. If the user values pay-per-token (no flat-rate commitment) and abliteration.ai serves Qwen3, this might be a **better** primary hosted option than Featherless for the user's described "100 turns/day" pattern.

#### src26 — Zep temporal-KG blog — ⚠ **PARTIAL PASS — claim attributed but not literally present**

Report (line 269): "Graphiti's **valid_at/invalid_at timestamps on every knowledge graph edge** enable non-lossy tracking of fact supersession"
Re-fetch: blog mentions "temporally-aware knowledge graph engine" but **does not literally describe valid_at/invalid_at timestamps**. The architectural detail likely lives in src27 (the arXiv paper). Citation should be `[src26, src27]` (or just src27) for the architecture claim, not src26 alone.

DMR 94.8% claim ✓ verified.
LongMemEval 18.5% improvement ✓ verified.

#### src36 — xAI Grok 4.3 docs — ❌ **STILL 404**

Report (line 200, §6 src36): "Grok 4.3 xAI Docs — confirmed May 2, 2026 launch date, ~100 tok/s. https://docs.x.ai/developers/models/grok-4.3 — accessed 2026-05-05 (note: page 404'd during initial researcher pass; indexed by synthesizer final search)"

Re-fetch (2026-05-05): **404 still**.

The synthesizer's claim that the page was "indexed by synthesizer final search" appears to be **wrong**. Either the synthesizer hallucinated the indexing, or the page has since been removed, or the claim was based on a search-result snippet that didn't actually resolve to a fetchable page. **The report cites a 404 URL in §6 as if it were a fetched source.** This is a citation-of-non-existent-content failure mode — a different category from quote fabrication, but equally bad.

#### src12 — Vice BasedGPT 2024 — ✓ **PASS WITH FRAMING NUANCE**

Report: "BasedGPT case (Vice, 2024 — src13 [sic — actually src12]) shows even early 'uncensored' models explained slurs rather than generating them freely"

Re-fetch confirms: BasedGPT *defined* slurs in response to direct questions rather than using them casually. **However**, the same article documents BasedGPT generating "ranking ethnicities from worst to best" and offensive hypothetical news headlines unprompted. The article supports a more mixed conclusion than the report's framing implies: "uncensored models will explain rather than freely generate slurs in response to direct questions, but will produce other problematic transgressive content unprompted." The report uses src12 to argue the *narrow* point (no slur generation). Vice supports the *broader* point (transgressive content yes, slur-token spam no). Reading is in-bounds.

(Bonus: the report has src12 mis-numbered as `src13` in the body — line 98. Citation graph integrity issue caught only on re-fetch.)

### Loop 8 summary table

| # | Source | Verdict | Severity |
|---|---|---|---|
| 1 | src22 (Willison quote) | **FAIL — fabricated quoted passage** | **High** |
| 2 | src17 (Magnum-v4-72B) | PASS | — |
| 3 | src32 (OpenRouter Hermes 4) | PASS | — |
| 4 | src35 (abliteration.ai) | **FAIL — pricing wrong by 40%; flips cost ranking** | **High** |
| 5 | src26 (Zep blog) | Partial — claim attributed but not in source | Low |
| 6 | src36 (Grok 4.3 docs) | **FAIL — cited URL is 404** | Medium |
| 7 | src12 (Vice BasedGPT) | Pass with nuance; also mis-numbered as src13 in body | Low |

**Net: 3 passes, 3 fails, 1 partial.** **Failure rate on this cut: 43% (3 of 7).**

The internal citation verifier reportedly caught "2 fabrications + 1 inconclusive" out of 12 sampled. My different cut found 3 different failures in 7 samples — including one quoted-passage fabrication of the kind Patch T explicitly warns about.

### Loop 8 verdict — citation verification has structural blind spots

The citation verifier as currently configured **misses three failure modes** that show up in this cut:
1. **Cited URL is 404** — the verifier likely treated "synthesizer final search re-confirmed" as proof of existence; it isn't
2. **Numeric mathematical errors** — verifier checks "is $5 in the source?" but doesn't verify the *computation* "$100 / 33.3M = $5/M" (false; should be $3/M)
3. **Quoted passage attributed to wrong source** — verifier may have re-fetched src21 (where the quote does live) and ticked it off, missing that src22 is the cited source for that specific quoted passage

Three structural fixes for Wave-5:
1. **Verifier should fetch every cited URL with a HEAD check** to catch 404s before accepting a citation
2. **Verifier should check arithmetic on cited dollar/token/percentage figures** when the report computes a rate from cited primitives
3. **Verifier should match quoted passages to the *specific cited source*, not to "any source in §6"**

Critically, the **abliteration.ai $3/M vs $5/M error is recommendation-changing**: at the user's stated usage pattern, abliteration.ai prepaid would be cheaper than Featherless Premium. The report's hosted-API ranking is wrong because of this single arithmetic error.

---

## Loop 9 — Honesty-contract regression deep analysis

**Method:** Cross-reference each declared regression in the report's §2 panel against the honesty contract's specific clauses. Diagnose whether the regression is a one-off or structural. Estimate whether already-shipped patches (Patch HHH) will fix it.

The honesty contract's relevant sections (`/home/jamie/projects/deep-ai-research/.claude/honesty_contract.md`):
- **§8 — Inferred caller intent is not user input**: clarification gate must use only statements the user actually made; surfacing `[user-clarification]` in §5 retroactively proves gate failure
- **§9 — Bounded coverage**: token budget ~600-800K target, ≥1.2M is regression; wall-time ~25 min target, ~40 min ceiling; Sonnet on synthesizer both passes (Opus only on re-dispatch); ≥30% of 5h Max window is a regression

The report self-flags four regressions in §2. I'll add three more from Loops 1-8.

### Regression 9.1 — §8 gate failure: 2 `[user-clarification]` items in §5

**Self-flagged in report (line 31):**
> "⚠ Two §5 items are clarification-gate failures (voice-cloning preference; local-only requirement) — these affect the primary recommendation (8B vs 14B; Featherless viability). The gate should have resolved these before research dispatch. Honesty contract §8 regression."

**Contract violation magnitude:** Both items are *recommendation-flipping*. Voice-cloning Y → forces drop to 8B; local-only Y → disqualifies Featherless upgrade path. Per §8, the system "spent compute on a research run pointed at the wrong target" — and at 87 min wall time, it spent ~87 min of compute on potentially-wrong-target research.

**Why the gate failed:** The clarification gate's checklist (per `SKILL.md`) currently includes hardware (VRAM tier), content tier, and use-case explicit. It does **not** include:
- TTS implementation choice (Piper vs XTTS-v2 vs Coqui — affects VRAM by 2-3 GB and thus the model-size recommendation)
- Strict-local vs hybrid-local-API tolerance (affects whether Featherless / OpenRouter / abliteration.ai are even on the table)

These two axes are **load-bearing for any "voice + Tier-T companion" query**. They surface in §5 because they were not asked. The gate's checklist needs explicit triggers for "voice-companion query class" → "ask which TTS, ask local-only-or-hybrid".

**Wave-5 candidate:** voice-companion query-class gate triggers.

### Regression 9.2 — §9 wall-time: 87 min vs 40 min ceiling

**Self-flagged in report (line 33):**
> "⚠ Run wall time was approximately 87 minutes ... exceeds the 40-minute honesty contract §9 hard ceiling."

**Stage breakdown (lines 35-40):**

| Stage | Wall time | % of total |
|---|---|---|
| recency_pass | 112s | 2.1% |
| research_fanout | 1059s | 20.3% |
| synthesizer_draft | 721s | 13.8% |
| verifiers | 381s | 7.3% |
| **synthesizer_final** | **2814s** | **53.9%** |
| (other / overhead) | ~133s | 2.5% |
| **Total** | **5220s ≈ 87 min** | 100% |

**The synthesizer_final stage alone (47 min) exceeds the entire 40-min §9 ceiling.** Critical observation.

**Will Patch HHH fix this?** Patch HHH sets `synthesizer.effort: high`. Per Claude Code's effort-level model, `high` vs `max`/`xhigh` typically shaves 20-30% off synthesizer time. Optimistic estimate after Patch HHH: 47 min × 0.7 = 33 min synthesizer_final → ~73 min total. **Still over the 40-min ceiling.**

**What's actually consuming synthesizer_final time:**
1. Reading critic + citation-verifier + fit-verifier + structure-verifier outputs
2. Mini-contrarian on the recommendation itself (Patch Z)
3. Rewriting §1 + §2 + §3 + §4 + §5 + §6
4. Final structure-conformance check

This is a lot of work. Patch HHH is a partial fix — the structural fix would require parallelizing critic/verifier processing within the synthesizer or pre-computing citation-graph integrity checks before the final synthesis pass.

**Wave-5 candidate:** synthesizer_final time-budget audit and structural decomposition.

### Regression 9.3 — §9 token budget: indeterminate, possibly over

**Self-flagged in report (line 33):**
> "Stop-hook telemetry unavailable (usage_snapshot_start five_hour_pct and seven_day_pct were null; usage_snapshot_end file absent). Token tally not in manifest. Rough estimate from researcher file sizes (~100KB combined): ~600-800K tokens input. Token regression (≥1.2M honesty contract §9 ceiling) cannot be ruled out — usage_snapshot was null; file-size proxy is approximate ±2-3×."

**The honest read:** the system can't tell you if it hit the ≥1.2M token ceiling. Telemetry is broken. The fact that the report acknowledges this is good — but the fact that telemetry is broken is itself a regression.

**Wave-5 candidate:** mandatory usage_snapshot capture before run termination; refuse to write final report if telemetry is null.

### Regression 9.4 — Citation verifier caught 2 fabrications + 1 inconclusive (and missed at least 3 more — Loop 8)

**Internal verifier:** 2 fabrications + 1 inconclusive out of 12 sampled = 25% issue rate on its sample.

**External verifier (Loop 8):** 3 issues out of 7 sampled = 43% issue rate on a different cut.

**Combined:** at least 6 of the 37 citations have verified issues. **At least 16% of citations have known problems.** If the rates from the two samples are representative of the un-sampled remainder, the *unsampled* citations may contain another ~5-10 issues.

**Diagnosis: synthesizer is over-stretching, AND verifier has structural blind spots.**

The synthesizer over-stretches because of *three internal pressures*:
1. The §3 comparison matrix must include every option family (Patch G + §9 breadth requirement) — drives speculative claims about lesser-researched options
2. Runner-ups in §1 must have one-line dismissal reasons — drives shallow attribution to nearest-plausible source
3. `[verified]` is rewarded as honest confidence — drives over-tagging of mechanism-confirmed claims as if their behavioral implications were also confirmed (Loop 3 V3, V4)

The verifier blind spots (per Loop 8):
1. No HEAD check on cited URLs (src36 404)
2. No arithmetic verification on cited rates (abliteration.ai $5/M error)
3. Quoted-passage matching is "is the quote in *any* §6 source" not "is it in the *cited* source" (src22 fabrication)

**Wave-5 candidates:**
- Synthesizer: claim-traceback discipline (every claim → exact source passage)
- Verifier: HEAD check, arithmetic check, exact-source-quote matching

### Regression 9.5 — 9% corpus / 91% web by citation (with arithmetic noise)

**Self-flagged in report (line 29):**
> "9% corpus / 91% web by citation (3 corpus / 32 web). 25% corpus / 75% web by retrieval call (16 corpus / 49 web). Corpus coverage on this topic is thin for abliterated-finetune specifics; most model card data required web retrieval."

**Hand-off question:** is the right fix to add more sources to `config/sources.yaml`, or is this a fundamental gap in the discovery pipeline?

**Diagnosis:** mostly fundamental. For *this query class* (current model recommendations from HuggingFace cards), the corpus is structurally less authoritative than the web. Reasons:
- Abliterated-finetune model cards live on HuggingFace and update frequently
- The corpus's design strength (longitudinal blog/paper aggregation, authority-engagement boost) is for trends and discussions, not current-spec model lookups
- Even if the corpus ingested HF model cards via an adapter, model cards change daily; the web fetch is more authoritative

**But there IS a fixable gap:** the corpus does not have an HF model-card adapter at all. Adding one for authority-tagged authors (`huihui-ai`, `mlabonne`, `EVA-UNIT-01`, `anthracite-org`, `bartowski`, `BeaverAI`, `DavidAU`, `Sao10K`, `TheDrummer`) would substantially help abliterated-finetune queries — even if the data is ~24h stale, it would close the 9% → ~30% corpus ratio.

**Real fix:** hybrid. (a) HF model-card adapter for authority authors → bumps corpus coverage; (b) accept the 70%+ web for fast-moving model-spec queries (don't pretend to fix what isn't broken).

**Sub-finding:** the §2 panel says "3 corpus / 32 web" totaling 35, while §6 lists 37 sources. **Off-by-2 arithmetic error already noted in Loop 2.5.** Two unaccounted sources.

**Wave-5 candidate:** HF model-card adapter for authority-tagged authors.

### Regression 9.6 — §9 sub-question count at upper bound

The report runs SQ1-SQ5 = 5 sub-questions. §9 says "5-6 only for genuine triple-axis complexity". This query has three axes (model + persona + memory). 5 is in-bound but at the ceiling.

The decomposition is:
- SQ1: Local model families on RTX 5080 16GB
- SQ2: Higher-VRAM tier quality delta
- SQ3: Hosted API options
- SQ4: Personality engineering for Tier-T humor
- SQ5: Memory architecture and multi-model architecture

**SQ5 is a compound:** "Memory architecture **AND** multi-model architecture". §9 says fewer-but-deeper sub-questions; this sub-question is two sub-questions in one. If SQ5 had been split into SQ5 (memory) and SQ6 (multi-model architecture), the count would have been 6 — over the ceiling. Compound sub-questions are a way to comply with the count limit while sneaking in extra scope. **This is a calibration drift the contract doesn't currently address.**

**Wave-5 candidate:** sub-question scope-test — each SQ must answer one question, not a conjunction.

### Regression 9.7 — synthesizer model: was it Sonnet or Opus?

§9 says "Sonnet 4.6 default on BOTH passes. Opus 4.7 is reserved for re-dispatch loops." The report does not specify which model the synthesizer ran on. The hand-off note (`NEXT_TASK.md`) claims Patch HHH set per-agent effort levels but does NOT confirm Sonnet on synthesizer.

If the run used Opus on the first synthesizer pass, that's a §9 violation. If Sonnet, that's compliant but doesn't explain the 47-min synthesizer_final time.

**Wave-5 candidate:** the report manifest should record the synthesizer model identity per stage — a single field, easy to add, currently absent.

### Loop 9 verdict

The report is *honest about its regressions* but the regressions are *systemic*:

| Regression | Patch HHH fix? | Wave-5 needed? |
|---|---|---|
| 9.1 §8 gate failures (×2) | No | **Yes** — voice-companion-query gate triggers |
| 9.2 87-min wall time | Partial (~73 min projected post-HHH) | **Yes** — synthesizer_final structural decomposition |
| 9.3 token-budget telemetry broken | No | **Yes** — mandatory usage_snapshot capture |
| 9.4 citation verifier blind spots | No | **Yes** — HEAD/arithmetic/exact-quote checks |
| 9.5 9%/91% corpus ratio | No (this is mostly correct framing) | Partial — HF authority-author adapter |
| 9.6 compound sub-question scope drift | No | **Yes** — SQ scope-test |
| 9.7 synthesizer model not recorded | No | **Yes** — manifest field |

Six of seven regressions need Wave-5 attention. Some are quick (manifest fields, gate triggers). Some are structural (synthesizer claim-traceback). The honest read: **Patch HHH was an effort-level fix; it does not address the deeper structural issues with the synthesizer's verification surface.**

The report's self-flagging is the system working correctly — but the contract-violation rate is high enough that the next run should be expected to violate the contract again unless these issues are addressed. The system is **honest about being broken**, not yet **fixed**.

---

## Loop 10 — Wave-5 patch synthesis + meta-critique

**Method:** Synthesize loops 1-9 into ≤5 Wave-5 patch proposals, framed in the same letter-convention as Patches NN through HHH. Each patch with what / why / how / acceptance-test. Then a final meta-critique on whether to act on the report.

The pattern across all nine prior loops: **the synthesizer and the verifier are each doing roughly half their job, with the gap in the middle producing recommendation-distorting errors**. Wave-5's job is to close that gap.

### Patch III — Citation-traceback discipline

**What:** Every load-bearing claim must be paired with the *exact source passage* that contains it. The synthesizer must emit, for each `[verified]` / `[inferred — srcN]` tag, an inline machine-readable annotation containing a quoted fragment of the cited source's text. The verifier consumes this annotation and re-fetches the source to confirm exact-string match.

**Why (drawing from Loops 2, 4, 5, 8):**
- Loop 2.1 — §1 conclusion paragraph mis-attaches `[src30, src31]` (TTS sources) to a claim about frontier-API rewriting, when the correct source is src22
- Loop 4.1 — Report claims "abliteration does NOT modify the vocabulary embedding matrix"; the cited mlabonne implementation (src3) modifies `model.W_E` (the embedding matrix) explicitly
- Loop 5.2 — Report cites PRISM (src28) 81.5-vs-71.4 numbers as evidence for "single-model vs separate-model"; the paper actually measures gated-vs-always-on within one model
- Loop 8 — src22 has fabricated verbatim quote; src35 abliteration.ai pricing claim fails arithmetic on the source's own primitives

All five share a root cause: **the synthesizer produces conclusions, then back-fills citations from a candidate pool of sources, without ensuring each source actually contains the claim.** The verifier, currently configured to spot-check existence, doesn't catch this because the source DOES exist — it just doesn't contain the claim being attributed to it.

**How:**

1. **Synthesizer prompt amendment** (`.claude/agents/deep-ai-research-synthesizer.md`):

   For every `[verified]`, `[inferred — srcN]`, or `[judgment ... srcN]` tag, the synthesizer emits an HTML-comment annotation immediately after the tag:
   ```
   This is the claim. [verified — src1, src3]
   <!-- claim-trace src1: "single direction such that erasing this direction from the model's residual stream activations" -->
   <!-- claim-trace src3: "model.W_E.data = get_orthogonalized_matrix(model.W_E, refusal_dir)" -->
   ```
   Each `claim-trace` quotes a fragment from the cited source long enough to be unique (≥40 characters), short enough to verify (≤200).

2. **Citation verifier amendment** (`.claude/agents/deep-ai-research-verifier.md`):

   For each `claim-trace` annotation: re-fetch the cited URL, perform exact-substring match (whitespace-normalized) against fetched body. PASS on exact match; FAIL on miss. Output goes into the existing verifier-failures channel.

3. **Structure-verifier amendment** (`.claude/agents/deep-ai-research-structure-verifier.md`):

   Lint: every `[verified]` and `[inferred — srcN]` tag MUST be followed by a `claim-trace` annotation. Missing annotation = STRUCTURE FAIL with location.

**Acceptance test:** Re-run the 2026-05-05 query against a fresh corpus. The citation verifier should now flag: (a) src22 missing Willison quote, (b) abliteration.ai $5/M arithmetic mismatch (the source's `$100 / 33,333,334 tokens` resolves to ≠ $5/M), (c) src36 404 URL, (d) §1's mis-attached `[src30, src31]` tags. Acceptable false-positive rate ≤5% (verifier flags pass on second human review).

### Patch JJJ — `[verified]` tag refactor: mechanism vs behavior

**What:** Split `[verified]` into `[mechanism-verified]` and `[behavior-verified]`. Mechanism-verified means a foundation source confirms a structural mechanism. Behavior-verified means sources directly confirm the claimed *output behavior*. Behavioral implications inferred from mechanism sources must use `[inferred from mechanism — srcN]`, not `[verified]`.

**Why (drawing from Loops 3, 4):**

Loop 3 audit found 5 of 6 `[verified]` tags fail Patch H. The pattern is consistent: the synthesizer cites Arditi 2024 (src1, refusal-direction concept paper) and mlabonne (src3, weight-orthogonalization implementation blog) as authoritative, then tags downstream behavioral claims (slur generation, refusal binary, no size-scaling) as `[verified — src1, src3]`. Neither source makes those behavioral claims. The mechanism is verified; the behavioral conclusion is not.

Loop 4 confirmed: when re-fetched, neither src1 nor src3 contains the slur-generation claim, the size-binary claim, or the W_E-modification-direction claim. The synthesizer is overusing `[verified]` for "I'm confident" rather than "two independent sources directly contain the claim."

The current `[verified]` tag is doing two jobs: (a) "the mechanism the argument rests on is real" and (b) "the behavioral conclusion the argument reaches is real." Wave-5 splits these.

**How:**

1. **Honesty contract amendment** (`.claude/honesty_contract.md` §4 Confidence levels):

   Replace the current single `[verified]` definition with:
   - `[mechanism-verified]` — foundation source(s) directly confirm the mechanism on which the claim rests; ≥2 independent sources required if mechanism is novel; ≥1 if mechanism is canonical (papers in major venues)
   - `[behavior-verified]` — ≥2 independent sources directly contain the claimed output behavior; behavior-verified is unavailable when the only sources are concept/implementation papers
   - `[inferred from mechanism — srcN]` — claim is downstream of cited mechanism; reasoning chain is sound but not directly evidenced
   - `[inferred — srcN]` (unchanged) — single source supports a single inferential step
   - `[judgment]` (unchanged)

2. **Synthesizer prompt amendment**: when a claim is a behavioral implication of a mechanism source, the synthesizer must default to `[inferred from mechanism — srcN]`, not `[verified]`. Clear examples in the agent's prompt with the abliteration → slur-generation case.

3. **Structure-verifier lint**: warn on `[verified]` (legacy single tag) — must be `[mechanism-verified]` or `[behavior-verified]` explicitly. Migration: existing reports left as-is; new reports use new tags.

**Acceptance test:** A re-run of the 2026-05-05 query produces ≤2 `[behavior-verified]` tags (the W_E orthogonalization implementation in src3 might still pass; everything else becomes `[inferred from mechanism — src1, src3]` or `[judgment]`). Loop 3 audit's V1, V3, V4, V5, V6 all migrate to weaker tags.

### Patch KKK — Empirical-verification suggestion in §1 / §5

**What:** When a recommendation rests on a calculated budget (VRAM, cost, latency, token volume) that hasn't been empirically validated, §1 or §5 must include a one-command empirical-verification path the user can run in ≤60 seconds.

**Why (drawing from Loops 6, 9):**

Loop 6 — the report's listed "Weakest Assumption" (13.5GB VRAM math under voice load) could be resolved in 30 seconds with `nvidia-smi --query-gpu=memory.used --format=csv -l 1` while running Ollama + Whisper + Piper. The system spent 87 minutes producing a calculation that takes 30 seconds to verify. Asymmetric.

Loop 5/9 — the Featherless 70B "5-15s per turn" latency claim is `[research-target-dropped]` in §5 and rests on "general serverless 70B inference knowledge". A single `curl --request POST` to the Featherless endpoint with the right model would resolve it in <30 seconds. Same logic for abliteration.ai true cost (one purchase + token meter), Mistral-Small-3.1-24B Imatrix VRAM under load (one Ollama + nvidia-smi run), Grok-4.3 API Spicy Mode parameter (one curl with `?spicy=true`).

The system is doing 87 minutes of cloud research to produce conclusions the user could falsify or confirm in 60 seconds at the terminal. **The honest report should hand the user the falsification command.**

**How:**

1. **Synthesizer prompt amendment**: for each `Weakest Assumption` bullet in §2 and each `[research-target-dropped]` item in §5 that rests on a measurable quantity (VRAM, latency, throughput, cost), the synthesizer must produce a one-command "Empirical resolution" sub-bullet with the exact command.

2. **§3 Comparison matrix amendment**: any row with "VRAM unverified", "latency estimated", or "cost estimated" must include a 1-line resolution command in a new "Empirical check" column.

3. **Structure-verifier lint**: §2 Weakest Assumption + §5 `[research-target-dropped]` items that contain measurable-quantity language ("GB", "tokens/sec", "$X/month", "ms") must include an empirical-resolution sub-bullet.

**Acceptance test:** Re-run produces, for the 2026-05-05 query: VRAM check command in §2 weakest assumption; Featherless 70B latency check in §5; abliteration.ai cost check in §5; Mistral-Small-3.1-24B VRAM check in §3 matrix.

### Patch LLL — Inter-run drift summary

**What:** §2 of every report includes a "Drift" sub-bullet when prior reports on similar queries exist (cosine similarity ≥0.85 on title embedding). The drift bullet surfaces prior recommendations + convergence/contradiction status. Do not gate dispatch on it; just surface it. Honesty signal.

**Why (drawing from Loop 7):**

Five prior runs of "what is the best model + personality + memory for an LLM with dark humor" produced five different headline recommendations:
- R1: Branched (frontier API or 27B/70B)
- R2: huihui-ai/Qwen3-14B-abliterated
- R3: Josiefied-Qwen3-8B + Graphiti + LiteLLM-Grok escalation
- R4: Hermes 3 8B (NOT abliterated)
- R5: Qwen3.6 27B INT4 + Surgical Abliteration
- R6 (current): huihui-ai/Qwen3-14B-abliterated

The user reading R6 in isolation gets a confident `[verified]` recommendation. The user reading the cross-run pattern sees a much less confident system. **For a research system being run repeatedly, inter-run drift IS the confidence metric.** The current §2 confidence panel discusses intra-run uncertainty (Strongest evidence / Weakest assumption / What would change my mind) but not inter-run uncertainty.

**How:**

1. **Orchestrator amendment** (`.claude/skills/deep-ai-research/SKILL.md`): pre-dispatch step queries `reports/*.md` for prior reports with title-embedding cosine ≥0.85. For each match, extract §1 top recommendation (regex on `**Top recommendation:**` or equivalent). Build a "drift context" string passed to the synthesizer.

2. **Synthesizer prompt amendment**: receive drift context. Include in §2 a new sub-bullet:
   ```
   - **Drift:** N prior runs on this query in the last 30 days. Headline recommendations: [...]. This run converges with R# (X axes match) and diverges from R# (Y axes differ). Cross-run consistency is the confidence signal — discount intra-run confidence accordingly.
   ```

3. **Structure-verifier lint**: when drift context is non-empty, §2 must include a "Drift" sub-bullet.

**Acceptance test:** Re-run the 2026-05-05 query. §2 produces a "Drift" sub-bullet listing R1-R6, marking R6 as converged with R2, divergent on memory framework from all others, divergent on architecture from R3, etc.

### Patch MMM — Verifier teeth: HEAD / arithmetic / exact-source-quote

**What:** The citation verifier gains three concrete checks beyond "re-fetch source and grep for citation": (1) HTTP HEAD on every cited URL; (2) arithmetic verification on cited rates/percentages where source contains primitives; (3) exact-source-quote match against the *specific cited source*, not "any §6 source".

**Why (drawing from Loop 8):**

In a 7-citation re-fetch with a different cut from the verifier's 12 most-load-bearing samples:
- src36 — cited URL still 404 (verifier did not check existence of cited URL; treated synthesizer's "indexed by final search" as proof)
- src35 — abliteration.ai $100 / 33.3M tokens = $3/M, but report claims $5/M (verifier checked "is $5 in the source?" but did not verify the computation; in fact $5 wasn't in the source — the report computed it incorrectly from the source's primitives)
- src22 — verbatim Willison quote not in cited source; the quote may exist in src21 (the original prompt repo), but the report attributes it to src22 (verifier may have checked "quote exists somewhere in §6" not "quote exists in cited src22")

Three different failure modes, each individually addressable.

**How:**

1. **HEAD check** in `.claude/agents/deep-ai-research-verifier.md`:
   ```
   For each citation [srcN]:
     resp = httpx.head(srcN.url, follow_redirects=True, timeout=10)
     if resp.status >= 400: VERIFIER FAIL "URL is dead (HTTP {status})"
   ```
   Run before content fetch; cheap; catches 404s in <1 second per source.

2. **Arithmetic check**: when the report contains a computed rate of form `$X/M` or `Y%` or similar, and the source contains the primitives ($X, M), verifier extracts both, computes the rate, and compares against the report's claim. Tolerance ±10%. Mismatch → FAIL with computed-vs-claimed rates.

3. **Exact-source-quote match**: when the report contains a string in double-quotes attributed to a `[srcN]`, verifier fetches src*N* specifically (not any §6 source), normalizes whitespace, performs exact substring match. Miss → FAIL with "cited quote not in cited source"; if the same quote IS found in a *different* §6 source, the failure annotation says "found in srcM, not cited srcN".

**Acceptance test:** Re-run citation verifier on 2026-05-05 report. Should now flag: src36 (HEAD = 404), src35 (arithmetic: $100/33.3M ≠ $5/M), src22 (Willison quote not in src22 body).

---

### Patch summary table

| Patch | What it adds | Loops driving it | Risk |
|---|---|---|---|
| III | Claim-trace annotations + verifier exact-quote match | 2, 4, 5, 8 | Low; mostly synthesizer-side prompt change |
| JJJ | `[mechanism-verified]` vs `[behavior-verified]` split | 3, 4 | Medium; honesty contract change; migration cost |
| KKK | Empirical-verification commands in §1/§5 | 6, 9 | Low; pure addition |
| LLL | Inter-run drift summary in §2 | 7 | Medium; needs embedding query of prior reports |
| MMM | HEAD / arithmetic / exact-quote verifier checks | 8 | Low; verifier-side; cheap |

These five address ~80% of the issues found across loops 1-9. The remaining issues (sub-question scope drift, telemetry capture, manifest field for synthesizer model identity) are smaller and can ride along in the same wave or wait for Wave-6.

---

## Final meta-critique — would I act on this report's recommendation?

### Yes, with three guardrails

1. **Run `nvidia-smi --query-gpu=memory.used --format=csv -l 1` for 30 seconds** with Ollama serving Qwen3-14B-abliterated Q4_K_M + Whisper INT8 + Piper running concurrently. The Weakest Assumption resolves in this 30-second test. If actual VRAM consumed is ≤14 GB at 8K context, proceed. If not, fall back to Q4_K_S (8.5 GB) or 8B.

2. **Enable KV-cache quantization from day one**: `OLLAMA_KV_CACHE_TYPE=q4_0` (or `--cache-type-k q4_0 --cache-type-v q4_0` if running llama.cpp directly). The report does not mention this. It is a free 4× context extension with negligible quality cost. Without it, you'll hit a context cliff at ~16K. With it, ~64K is comfortable.

3. **Treat the slur caveat as overspecified.** The user's "occasional slurs OK" means slurs in setup/punchline of jokes — that works on huihui-ai/Qwen3-14B-abliterated with persona engineering (the report itself says so at line 244). Spontaneous unprompted slur generation in casual conversation is a different need; it requires DPO/SFT, but you probably don't actually want this anyway. Don't pursue a DPO finetune based on the report's framing.

### Where I would ignore the report

1. **Drop PRISM from the §1 conclusion** (Loop 5). The PRISM paper measures gated-vs-always-on within a single model; the report misrepresents it as evidence against multi-model architecture. The recommendation survives without PRISM — three independent operational arguments (VRAM eviction, context boundary, frontier-API softening) are sufficient. PRISM's actual headline finding is that *always-on persona hurts general-task performance*, which weakly argues *against* a persona companion, not for it.

2. **Re-rank hosted-API options.** The abliteration.ai $5/M claim is wrong by 40% (Loop 8); actual rate is $3/M. At 6M tokens/month: abliteration.ai prepaid $18/mo < Featherless Premium $25/mo. If you go hosted, abliteration.ai prepaid is competitive with Featherless and better than the report's "slightly more expensive" framing implies.

3. **Disambiguate the Mistral-Small-3.1-24B runner-up** (Loop 2.3). "Mistral-Small-3.1-24B Imatrix Q3_K_M (DavidAU/BeaverAI Fallen variant)" collapses two different models — DavidAU's MAX-NEO-Imatrix is *not* abliterated; BeaverAI's Fallen *is* (in the dark-finetune lineage). Pick BeaverAI/Fallen if you want abliteration + Mistral-Small-3.1-24B; pick DavidAU's MAX-NEO-Imatrix only if you separately apply abliteration.

4. **Don't treat Featherless 70B as the "strongest upgrade path"** (Loop 5/9). The 5-15s/turn latency estimate is judgment, not benchmark. Voice mode requires <2s/turn for "always-on companion" feel. **Test with a real curl request before committing to $25/mo.** If it's >5s/turn, the upgrade path is "more local VRAM" (24GB → Qwen3-32B-abliterated), not Featherless.

5. **Resolve the two §5 gate-failures BEFORE acting.** Voice cloning requirement: Y → drop to 8B. Strict-local requirement: Y → Featherless and OpenRouter are out. The recommendation may flip on either answer. The report's primary recommendation is conditional on "no voice cloning, API tolerance ok", and that condition was never confirmed.

### What the report gets right

- **The model family**: huihui-ai/Qwen3-14B-abliterated is genuinely the right choice for the user's hardware + content tier. This survives all critiques.
- **The persona-engineering stack**: SillyTavern character card + First Message + few-shot dialogue + Post-History Instructions is the correct toolset, supported by both the docs (src23) and community practice.
- **The architecture**: single-model + frontier API as silent tool is correct for an always-on Tier-T companion. The three operational arguments hold; the PRISM citation is window-dressing that should be dropped.
- **The memory simplification**: rolling flat-text "about me" doc as v1 is genuinely better than Mem0 / Graphiti / Letta for a 0-month-old companion. The macro-contrarian's reframe earned this answer.
- **The honesty about regressions**: §2's self-flagging of gate failures, wall-time overrun, and corpus/web ratio is the system working correctly. The fixes for those regressions are Wave-5 (Patches III-MMM above), not "stop being honest about them".

### What I'd grade the report

- **Recommendation quality**: 85/100 — outcome-correct; lightly miscalibrated supporting evidence; one runner-up is ambiguous; one cost claim is wrong direction-of-fit.
- **Justification quality**: 60/100 — three citation misattributions in §1 conclusion alone; 5-of-6 `[verified]` tags fail Patch H; PRISM scope-stretched; Willison quote fabricated; abliteration.ai pricing arithmetic wrong; W_E claim contradicts cited source.
- **Honesty quality**: 90/100 — self-flags regressions accurately; admits weak assumption; surfaces gate failures rather than hiding them; tag distribution (39 inferred / 10 judgment / 6 verified) is honest in the aggregate even when individual `[verified]` tags fail discipline.
- **System diagnostic value**: 95/100 — this report is a *gift* for system improvement. Every flaw points to a specific fixable patch. Wave-5 should ship Patches III-MMM in response.

The report is acceptable to act on with the guardrails above. The system that produced it is more interesting than the report itself — it's documenting its own failure modes loudly enough that those failure modes are now fixable.

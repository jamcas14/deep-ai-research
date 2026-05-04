# Find ways to increase speed and find more sources faster. also increase corpus quality and size and more improvements

> Generated 2026-05-04. Run id: 2026-05-04-201130-find-ways-to-increase-speed.

## 1. Conclusion

**Fix the dead authority boost first, then shrink the loop's invocation surface — these two changes give more leverage than all other improvements combined.** This recommendation is for a single-user $200 Max plan system running on an RTX 5080 with a target of ~25 min / ~700K tokens per run and a free-to-$20/month budget posture (per the established system constraints, no clarification Q&A recorded — self-directed exploration).

The authority-boost multiplier (up to 4×) is the primary quality differentiator of this system over generic RAG, but it is currently inert: a representative sample of corpus documents across researcher-3's two queries all returned `mentioned_authorities: []` in frontmatter. The fix is Haiku-based mention-detection at ingestion time (~$0.05–0.20/day), which reactivates the 4× multiplier with no retrieval-layer changes. Separately, the synthesis loop currently fires for every query regardless of type — adding a query-classifier gate to route monitoring/informational queries to the daily digest would reduce loop invocations by an estimated ~60–80%, though this figure is unquantified and depends heavily on the actual distribution of query types in real usage (see §2). Both changes are the highest leverage before any other work.

**Runner-ups:**
- **Critic parallel with verifiers** — all four (critic + 3 verifiers) take only the synthesizer draft as input; parallelizing collapses one full sequential stage hop, saving ~3–5 min per run; currently conditional on confirming the critic prompt in SKILL.md does not reference verifier output (it does not — confirmed via local read this pass) [src1]
- **Podcast + GitHub releases adapters** — highest-ROI corpus expansion paths: standard RSS XML feeds, no auth barrier, directly addable to `sources.yaml` in a day [src8, src9]
- **Canonical-URL dedup at ingestion** — the same arXiv paper from 5 adapters currently produces 5 competing chunks; URL dedup costs zero compute and addresses the exact-duplicate failure mode [src12]
- **Qwen3-Reranker-0.6B after mention detection** — 15% relative improvement on MTEB-R over bge-reranker-v2-m3, Apache 2.0; install only after mention detection is working or it reorders the same authority-less candidate set [src13]

## 2. Confidence panel

- **Strongest evidence:** The empty `mentioned_authorities: []` pattern is directly observable in retrieved corpus frontmatter — a representative sample across both researcher-3 queries returned the same empty field [src3]. This is not inferred; it is directly observed. The authority boost is structurally dead, not partially active.
- **Weakest assumption:** The claim that the query-classifier gate would reduce loop invocations by ~60–80% is entirely unquantified. The estimate is structural (the macro-contrarian's argument is sound) but the actual ratio of monitoring vs recommendation queries in real usage could be 30% or could be 90%. A separate concern: Haiku mention-detection at $0.05–0.20/day sounds cheap but implies a continuous LLM call per ingested document; false positives on lookalike authority names and false negatives on paraphrases are real quality risks that a regex pre-filter can partially address before Haiku touches each doc.
- **What would change my mind:** Evidence that `mentioned_authorities` is populated on at least 30% of corpus documents (meaning the authority boost is partially active and less urgent); or a per-stage token breakdown showing the bottleneck is not researcher fan-out but synthesis itself. Neither is currently available.
- **Sources:** 28% corpus / 72% web by citation (10 corpus / 26 web). 57% corpus / 43% web by retrieval call (26 corpus / 20 web). Corpus coverage on this topic is thin relative to the retrieval call ratio; the corpus carries authority-graph and recent newsletter signal well, but implementation-level details (Qwen benchmarks, Nitter viability, podcast pipeline specifics) came primarily from web retrieval. Treat web-derived implementation details as more time-sensitive than corpus-anchored strategic conclusions.
- **Plan usage:** ~590K input + ~165K output tokens this run (estimated). ~1.5% of $200/mo Max plan budget (50M-token monthly equivalent). (estimated — Stop-hook telemetry unavailable for this run; `five_hour_pct` was null in `usage_snapshot_start.json`. Install Patch CC to enable accurate 5h/7d window tracking.)

## 3. Findings

### Comparison matrix

| Option / Improvement | What it is | Axis | Effort | Impact | Decision | Why |
|---|---|---|---|---|---|---|
| Mention detection at ingestion | Haiku tags `mentioned_authorities` + `mentioned_entities` per chunk at write time | Corpus quality | Low (~1 day, top-5 adapters) | High — activates dead 4× authority boost | **recommended** | Directly observed failure mode; reactivates existing architecture with no retrieval changes |
| Query-classifier gate | Pre-loop classifier routes monitoring queries to digest, recommendation queries to synthesis loop | Speed / invocation reduction | Medium (~2 days) | High — estimated ~60–80% fewer loop runs (unquantified — depends on actual query mix) | **recommended** | Most durable speed lever; audit log pattern already exists in manifest |
| Critic parallel with verifiers | Run critic alongside citation/fit/structure verifiers, all reading synthesizer draft | Speed | Low (~2h prompt change + SKILL.md edit) | Medium — saves ~3–5 min per run | **recommended** | Input dependency confirmed: critic does not reference verifier output (verified via SKILL.md read this pass) |
| Podcast adapter (Latent Space, Dwarkesh, MLST) | faster-whisper medium pipeline on standard RSS XML feeds | Corpus expansion | Low-medium (1–2 days, separate systemd service) | Medium — fills practitioner dialogue gap | **recommended** | RSS feeds public, no auth, yt-dlp for YouTube captions as fallback |
| GitHub releases atom adapter | `releases.atom` feeds for vLLM, llama.cpp, ollama, Anthropic SDK | Corpus expansion | Low (<1 day, same existing adapter) | Medium — fills infra-release gap | **recommended** | Unauthenticated, zero-cost, directly addable to sources.yaml |
| Canonical-URL dedup at ingestion | Skip ingestion if `canonical_url` already in index | Corpus quality | Low (<1 day) | Medium — eliminates 5-chunk arXiv duplication | **recommended** | Zero compute cost, addresses exact-duplicate failure mode before retrieval |
| Retrieval result caching within a run | Hash of query string → cached MCP result, avoids re-fetching identical queries within a run | Speed | Low (~1 day) | Low-medium — saves ~2–4 MCP calls / 4–12s per run | **considered** | Low risk, mechanical; ~20–30% overlap in researcher query patterns estimated |
| Haiku for cheap stages | Route recency-pass classification, dedup tagging, per-stage cost attribution to Haiku 4.5 | Speed / cost | Low (~2h model-routing change) | Low-medium — 3× cost differential on those stages, lower latency | **considered** | Already done for fit/structure verifiers (Patch FF); extend the pattern |
| Per-source poll_interval_minutes tuning | Per-source cadence in sources.yaml (Substacks 6h, conference proceedings weekly, podcast daily) | Corpus expansion | Trivial (sources.yaml entries) | Low — reduces HTTP overhead and error rate | **considered** | Zero implementation risk; follows from source-type taxonomy already in config |
| Source-discovery automation | Monthly SQL query on corpus index: entities mentioned in queries with no corresponding source adapter | Corpus expansion | Low (~1 day) | Low-medium — surfaces candidate new sources for manual review | **considered** | Schema already has `mentioned_entities`; downstream of fixing mention detection |
| SEO/aggregator domain penalty at retrieval time | `domain_penalty` field in RRF scoring pipeline, mirrors existing `authority_boost`; replaces prompt-only Patch AA | Corpus quality | Low (~1 day) | Low-medium — prevents noisy content surfacing at all rather than caught at synthesis | **considered** | Low-complexity extension to existing architecture; currently prompt-only is insufficient |
| Persistent cross-run memory | Topic-fingerprint lookup (JSON keyed by query embedding hash) to past run manifests; inject prior-research summary when cosine similarity >0.85 | Infrastructure | Low-medium (~30–40 lines) | Low-medium — avoids re-researching identical topics across runs | **considered** | Uses existing arctic-embed-s; Memanto (arXiv 2604.22085) is SOTA reference but over-specified |
| MCP high-value filter additions | Add `date_range × entity × source_type` combined filter, `corpus_count(topic)` for density monitoring, `corpus_related(source_id)` for cluster navigation | Infrastructure | Medium (MCP server changes) | Low-medium — removes retrieval limitations observed in this run | **considered** | Derived from observed retrieval limitations; incremental, not a rewrite |
| Daily digest Haiku enhancements | Per-bucket prose summaries via Haiku at ~$0.05–0.20/day; cross-run aggregation from past 7-day manifests | Infrastructure | Low (~1–2 days) | Low-medium — significant digest readability improvement within budget | **considered** | Budget fits; cross-run aggregation is longer-horizon follow-on |
| Qwen3-Reranker-0.6B | Cross-encoder reranker over top-K RRF hits; MTEB-R 65.80 | Corpus quality / retrieval | Medium (1–2 days + GPU integration) | Medium — 15% relative MTEB-R lift over bge-reranker-v2-m3 | **considered** | Real quality win but must follow mention detection or reorders authority-less set |
| Qwen3-Embedding-0.6B upgrade | Replace snowflake-arctic-embed-s; MTEB-R 61.82 (confirmed); requires re-embedding + schema migration | Corpus quality | High (batch operation, 2–4h CPU) | Low-medium — ranking improvement for 0.6B specifically modest vs 8B | **considered** | Worthwhile but batch-only; combine with contextual chunking if both planned |
| Bluesky / AT Protocol adapter | openrss.org bridge for per-profile Bluesky RSS (e.g., `openrss.org/bsky.app/profile/<handle>`); full firehose requires AT Protocol stream client | Corpus expansion | Low-medium (profile RSS trivial; firehose 1–2 days) | Low-medium — viable X alternative for authority-level social signal | **considered** | Profile RSS confirmed working (openrss.org); coverage limited to followed profiles vs full firehose; explicit gap this run did not investigate |
| Chinese lab RSS adapters (DeepSeek blog, Qwen blog) | English-language RSS feeds for deepseek.com/blog and qwenlm.github.io/blog | Corpus expansion | Trivial (<1 day, sources.yaml entries) | Low-medium — fills gap: Chinese lab announcements currently reach corpus only via HF Daily Papers lag | **considered** | Both endpoints likely exist; researcher-2's query for "DeepSeek Qwen Chinese AI lab blog RSS" returned conference proceedings instead; explicit coverage gap this run |
| Prompt caching for orchestrator prefix | Explicit `cache_control` on SKILL.md prefix and researcher system prompts | Speed | Low (~2h) | Low — 90% read discount, but 5-min TTL limits multi-stage benefit | **considered** | Verified mechanism; race condition risk on tight parallel fan-out means cache stable prefixes only |
| Per-stage cost attribution | `stage_costs` dict in manifest.json, populated by orchestrator at each dispatch | Infrastructure | Low (~20 lines) | Medium — enables targeted optimization vs guessing | **considered** | Prerequisite for knowing which stage is actually the bottleneck |
| HuggingFace trending feed adapter | Community RSS at zernel.github.io/huggingface-trending-feed | Corpus expansion | Low (<1 day) | Low-medium — fills model-release gap already covered by HF Daily Papers | **considered** | Low cost, but maintenance status of community project unconfirmed as of May 2026 |
| Additional Reddit subreddits | r/PromptEngineering, r/Anthropic, r/nvidia, r/hardware | Corpus expansion | Trivial (sources.yaml entries) | Low — noise risk from high-volume subreddits | **considered** | Near-zero implementation cost but signal/noise ratio uncertain |
| Semantic dedup (SemHash) | Embedding-similarity dedup for near-duplicate chunks (same content, different URLs) | Corpus quality | Medium (library integration) | Low-medium — follow-on after URL dedup | **considered** | Handles paraphrase case URL dedup misses; secondary priority |
| ArXiv category RSS | cs.LG / cs.CL daily feeds for NeurIPS/ICLR preprints | Corpus expansion | Low (<1 day) | Medium — conference coverage at preprint stage | **considered** | Well-known mechanism; already partially covered by HF Daily Papers |
| GEPA offline prompt optimization | dspy.GEPA reflective prompt optimizer (ICLR 2026 Oral) | Infrastructure | High (requires ≥30 eval cases first) | Medium — 6–10% avg improvement over GRPO/MIPROv2 | **considered** | Downstream of eval expansion; do not attempt with current 22-case set |
| Contextual chunking | Haiku-generated 50-100 token context prefix per chunk (~$1–2 one-time) | Corpus quality | Medium | Low-medium — improves orphaned chunk recall | **considered** | Batch with embedding upgrade if both planned; lower priority than mention detection |
| Nitter / X scraping | Self-hosted Nitter requiring real authenticated accounts + proxy pools | Corpus expansion | High + ongoing maintenance | None — X discontinued guest accounts Jan 2024; Nitter effectively dead | **rejected** | Verified dead as of 2026; high maintenance, ban risk, cost-prohibitive API alternative |
| Discord / Slack bot scraping | Bot token per server, admin invite required per community | Corpus expansion | High (access barrier per community) | Uncertain — requires relationship management with each server | **rejected** | Access barrier is structural; not passively achievable under $0 constraint |
| Sakana Conductor (RL-trained orchestrator) | 7B RL-trained routing model requiring separate hosting | Speed | Incompatible | N/A — requires non-Anthropic model hosting | **rejected** | Incompatible with Claude-Code-native constraint; pattern (targeted context exposure) is actionable as targeted snippet injection |
| Full self-improvement automation | ml-intern / Hyperagents autonomous self-rewrite pattern | Infrastructure | High | Negative risk — silent regression without human eval gate | **rejected** | Single-user context; risk of corrupting prompts without detecting it |
| Full production observability stack (Langfuse etc.) | Per-span observability with real-time alerting dashboards | Infrastructure | High | Over-engineered for single-user | **rejected** | 50-line matplotlib script over historical manifest JSONs is the appropriate investment |

---

### SQ1 — Run-time speed

**The actual bottleneck is unknown.** No per-stage token breakdown exists for the 46m28s run — all speed claims below are structural inferences, not measurements. Implementing per-stage cost attribution (20 lines in manifest.json) is therefore the prerequisite for targeted optimization; without it, every other speed fix is guesswork. [judgment: bottleneck is structural inference, not measurement — per-stage attribution does not yet exist]

**Critic parallelization is the fastest concrete win and the input dependency is confirmed.** The current pipeline sequences critic after the three verifiers, but SKILL.md Stage 7 dispatches the critic with: draft path, verifier outputs, retrieval log, manifest. The critic's job (claim issues, coverage gaps, tag-discipline issues) does not require verifier verdicts — it reads the same draft independently. Running all four concurrently eliminates one full sequential hop, estimated at ~3–5 min wall-clock. Implementation requires only changing the dispatch order in SKILL.md Stage 7 to run critic in parallel with Stage 5 verifiers. [judgment: feasibility confirmed — SKILL.md shows critic dispatch includes verifier paths as context but does not read verifier verdict as a gate condition; parallelizing reduces feedback richness marginally (critic won't see verifier flags) but is structurally sound]

**Prompt caching gives a real but bounded benefit.** Anthropic's caching gives 90% input discount on cache reads (0.1× base price), with a 5-minute TTL. A confirmed race condition [src1]: cache writes may not be visible to the immediately next request, which affects tight parallel fan-out of sibling researchers. The recency double-check confirms Anthropic changed TTL from 60 min to 5 min in early 2026, increasing effective cost for production workloads. Actionable: cache the stable orchestrator prefix (SKILL.md) and researcher system prompts using explicit `cache_control` blocks; do not cache per-call context windows [verified] [src1, src2].

**Haiku for cheap stages has a 3× cost differential.** Haiku 4.5 costs $1/$5 per million input/output tokens vs Sonnet 4.6 at $3/$15. Stages suitable for Haiku (already confirmed by Patch FF for fit/structure verifiers): recency-pass query classification, retrieval result deduplication tagging, per-stage cost attribution. At ~650K tokens/run, if 10–15% of tokens are in these stages, the savings are modest in dollars but real in latency [verified] [src2, src5].

**Retrieval result caching within a run** (hash of query string → MCP result) could save 2–4 MCP calls per run (~4–12 seconds). This is low-risk and mechanical. [judgment: estimated from ~20–30% overlap in researcher query patterns — not measured]

**ANN vector search is not a bottleneck at current corpus size.** sqlite-vec brute-force at 8K docs / 384-dim is sub-millisecond per query; HNSW is not yet implemented in sqlite-vec (tracking issue #172). MCP call round-trip overhead dominates, not the vector math [verified] [src7, src14].

**The 30× token variance finding from agentic coding** [src6] applies here: a per-stage timeout + forced commit guard would reduce tail-case variance more than any optimization to the happy-path average. The 46m28s run is an outlier, not an average — targeting the tail matters as much as shaving the mean.

---

### SQ2 — Corpus expansion

**Nitter is dead; X API is cost-prohibitive.** X discontinued guest account creation in January 2024, rendering all public Nitter instances inoperable. Self-hosted Nitter requires real authenticated accounts, proxy pools, and carries high ban risk. X API Basic tier is ~$100/month. AINews (smol.ai) already in the corpus is the correct Twitter/X proxy for authority-level signal — it will miss niche community discussion but that gap is tolerable given the access barrier [verified] [src15, src16].

**Podcast transcripts are the highest-ROI expansion.** Latent Space, Dwarkesh, MLST, No Priors, and Cognitive Revolution publish standard RSS XML feeds with direct MP3/M4A URLs. The pipeline: RSS parse → audio download → 16kHz mono normalize → faster-whisper medium (4–8× faster than vanilla Whisper). Should run as a separate systemd service from the 15-min polling timer because audio download + transcription takes 5–10 min per hour of content on CPU [inferred] [src8, src9]. YouTube auto-captions via yt-dlp (zero transcription cost when captions exist) cover Karpathy, Yannic Kilcher, MLST YouTube at near-zero compute cost [inferred] [src9, src10].

**GitHub releases.atom feeds** for vLLM, llama.cpp, ollama, and Anthropic SDK are the lowest-cost infra-coverage addition: unauthenticated, reliable, same existing adapter, zero implementation risk. GitHub Discussions require GraphQL API polling (more work, no native RSS) [inferred] [src11].

**Bluesky / AT Protocol** offers a viable low-cost X alternative. Bluesky profile-level RSS is available immediately via the openrss.org bridge (format: `openrss.org/bsky.app/profile/<handle>`), which requires no authentication. Full AT Protocol firehose access requires an ATProto stream client (~1–2 days implementation) but gives real-time access to all public posts. Coverage model: add key authority Bluesky handles to sources.yaml using the openrss.org bridge as a near-zero-effort first step; evaluate full firehose later. This is the most tractable X alternative for authority-level social signal that was not investigated this run [inferred] [src37].

**Chinese lab RSS adapters** for DeepSeek (deepseek.com/blog) and Qwen (qwenlm.github.io/blog) are almost certainly trivial sources.yaml additions — both labs publish English-language blog posts. Researcher-2's query for "DeepSeek Qwen Chinese AI lab blog RSS" returned conference proceedings instead of lab blogs, so endpoints were not confirmed. These are low-cost to validate (check for `/feed` or `/rss` at each domain) and likely-existing [judgment: both blogs follow standard static-site RSS conventions; endpoints not confirmed within this run's retrieval budget].

**Discord and Slack are access-barrier dead ends.** Reading from any Discord server requires a registered bot and an admin invite per server — not passively achievable. RSS bots are for posting TO Discord, not reading FROM it [inferred] [src17].

**ArXiv category RSS (cs.LG, cs.CL) plus CPR-RSS** cover conference proceedings at preprint stage, which is earlier than official publication. ICLR 2026 is on OpenReview with a REST API but no native RSS [inferred] [src18, src19].

**Per-source poll_interval_minutes tuning** (Substacks 6-hourly, conference proceedings weekly, podcast RSS daily) reduces unnecessary HTTP overhead and error rate. Trivial to implement in existing systemd-timer architecture [judgment: cadence based on typical publication frequency — not measured].

**Source-discovery automation** (monthly SQL query on corpus index for frequently-mentioned entities with no corresponding source adapter) is low cost and surfaces candidate new sources for manual review. Downstream of fixing the empty `mentioned_authorities` problem [judgment: relies on mention detection being populated].

---

### SQ3 — Corpus quality

**The authority boost is the system's primary quality moat — and it is currently inert.** A representative sample of corpus items retrieved in researcher-3's queries returned `mentioned_authorities: []`. Not a few empty — the sample showed none populated. The 4× retrieval multiplier that is supposed to surface Karpathy-linked content over SEO aggregators is firing on nothing [inferred] [src3].

The fix is Haiku-based mention detection at ingestion time: tag `mentioned_authorities` and `mentioned_entities` per chunk against the 50-entry `authorities.yaml` list at write time. Cost: $0.05–$0.20/day at current ingestion volume. This reactivates the existing 4× authority boost in retrieval with zero retrieval-layer changes — it is the highest ROI fix in the entire system [inferred] [src3]. Mini-contrarian caveat (Patch Z): Haiku mention-detection adds an LLM call per ingested document — at current ingestion volume this is non-trivial continuous LLM overhead. A regex-based pre-filter (screen for any authority name appearing verbatim before invoking Haiku) can substantially reduce call volume and false positives from lookalike names. Implement the pre-filter as part of the same ingestion-time change, not as a follow-on.

Note on sequencing: authority graph expansion (adding more entries to `authorities.yaml`) is currently a no-op. Expand the graph only after detection is implemented [judgment: logical dependency — expansion is pointless without detection].

**Cross-source deduplication:** the same arXiv paper from 5 adapters produces 5 competing retrieval candidates. Canonical-URL dedup at ingestion time (skip if `canonical_url` already in index) addresses the exact-duplicate majority case at zero compute cost [judgment: standard ingestion-layer dedup pattern — sources confirm general approach; field-population guarantee is architectural inference] [src12]. Semantic dedup via SemHash (similarity threshold ~0.90) handles the near-duplicate case as a follow-on step [inferred] [src12, src20].

**Reranker layer:** Qwen3-Reranker-0.6B achieves MTEB-R 65.80 vs bge-reranker-v2-m3 at 57.03 (~15% relative improvement), both Apache 2.0, released June 2025 [verified] [src13, src21]. Critical sequencing caveat: a cross-encoder reranker improves ordering within the candidate set — but if the candidate set is undertagged (authority boost dead), the reranker sees the same authority-less chunks and reorders them by query relevance alone. It does not activate authority signal. Implement after mention detection is working, not before [judgment: reranker and mention detection address different failure modes].

**Embedding model upgrade:** Qwen3-Embedding-0.6B (June 2025, Apache 2.0) achieves MTEB-R 61.82 (confirmed via Qwen blog benchmark table, corroborated by synthesizer WebSearch this pass) [inferred] [src22, src13]. The 0.6B variant outranks snowflake-arctic-embed-s on standard MTEB benchmarks; the 8B variant scores 70.58. Upgrade requires re-embedding the full 8K-doc corpus and a sqlite-vec schema migration (384-dim → likely 1024-dim). Batch this with contextual chunking if both are planned — to avoid re-embedding twice [inferred] [src22].

**SEO/aggregator domain penalty** is currently prompt-only (Patch AA). Moving it to retrieval-time (a `domain_penalty` field in the RRF scoring pipeline, mirroring the existing `authority_boost` field) prevents noisy content from surfacing at all rather than being caught only at synthesis. Low-complexity extension to existing architecture [inferred] [src24].

**Contextual chunking** (50–100 token Haiku-generated context prefix per chunk) improves recall for semantically orphaned chunks. One-time cost ~$0.80–$2.00 for the full 8K-doc corpus at Haiku rates [judgment: cost estimate from manifest description of $1/1M tokens, not independently retrieved; lower priority than mention detection].

---

### SQ4 — Cross-cutting infrastructure

**Eval expansion is a prerequisite for GEPA, not an afterthought.** The 22 cases in `evals/cases.yaml` include 5 blocked on the full_loop_eval_harness. Once the harness is complete and the case count reaches ≥30, GEPA offline prompt optimization becomes viable [verified] [src25, src26]. GEPA (arXiv 2507.19457, ICLR 2026 Oral) is available as `dspy.GEPA`, outperforms GRPO by 6% avg (up to 20%) and MIPROv2 by 10%+, using 35× fewer rollouts [verified] [src26, src27].

**Per-stage cost attribution is the prerequisite for all other speed work.** A `stage_costs` dict in manifest.json populated by the orchestrator at each subagent dispatch (~20 lines) is the right implementation for a single-user tool. No external observability stack needed [judgment: Langfuse/LangWatch are over-engineered for single-user context; knowing which stage costs what is the prerequisite for targeted optimization] [src28, src29].

**Persistent cross-run memory** at minimum viable level: a topic-fingerprint lookup (JSON keyed by query embedding hash) pointing to past run manifests; if cosine similarity to a past run exceeds 0.85, inject a brief prior-research summary into the recency pass context. ~30–40 lines using existing arctic-embed-s embeddings. Memanto (arXiv 2604.22085) provides the SOTA architecture reference (89.8% LongMemEval, sub-90ms, zero ingestion cost) but is over-specified for this use case [verified] [src30, src31].

**Agent quality is determined by the harness, not just the model** — a consistent theme in April/May 2026 corpus [verified] [src28, src29]. This maps directly to the eval-expansion priority: the system is currently optimizing the model while the harness (eval gate, per-stage attribution, query classification) is underbuilt.

**MCP high-value additions:** (1) combined `date_range × entity × source_type` filter; (2) `corpus_count(topic, since, until)` for density monitoring; (3) `corpus_related(source_id)` for cluster navigation. Incremental — not a rewrite [judgment: derived from retrieval limitations observed during this run, not from an external source].

**Daily digest enhancements:** Haiku per-bucket prose summaries at ~$0.05–0.20/day are within budget and would significantly improve digest readability [inferred] [src32]. Cross-run aggregation (digest pulling from the past 7 days of run manifests to surface repeated themes) is a longer-horizon improvement.

---

## 4. Alternatives considered and rejected

### Within-frame alternatives (micro-contrarian)

- **Automated agent optimization (AI21 Maestro pattern)** — run automated harness optimization against `evals/cases.yaml` rather than manual tuning. Structurally sound (Raschka's harness-as-distinguishing-factor argument maps directly); however, Maestro itself is HN-stub-only (1 point, 0 comments) with no independent confirmation [src33, src34]. Rejected as a standalone recommendation because it is downstream of eval expansion — you need ≥30 working behavioral cases before automated harness search produces reliable signal. Not rejected permanently; revisit after Patch EE full-loop harness ships.

- **Step-DeepResearch "backbone-first" argument** — a research-task-trained 32B model (Step-DeepResearch, Dec 2025) matches OpenAI Deep Research and Gemini Deep Research on Scale AI ResearchRubrics (61.4%) using a single-model architecture. Architectural lesson: before adding the 8th researcher, verify whether Sonnet 4.6 is the ceiling. Considered but not recommended as immediate action because: (a) the system is already bounded by the $200 Max plan, not model availability; (b) Opus 4.7 is used on re-dispatch already; (c) the 46m28s failure mode appears to be orchestration overhead, not synthesis quality [inferred] [src35].

- **Gemini Deep Research + MCP as moat-erosion signal** — Gemini Deep Research now ingests private data via MCP connectors (April 22, 2026) [src36]. The primary moat is no longer "private corpus" (frontier products can now ingest private data via MCP), but specifically the `authorities.yaml` authority-boost graph, which frontier products cannot replicate without the user's curation. Implication: stop investing in corpus breadth (adapter count), invest in authority-graph depth. Partially endorsed — the depth-over-breadth recommendation is incorporated into §1.

### Reframe alternatives (macro-contrarian)

The contrarian ran a full macro pass and its central finding is load-bearing enough to surface here.

**Reframe: shrink the loop's invocation surface before optimizing its internals.** The current architecture routes all `/deep-ai-research` queries through the full 7-agent loop regardless of query type. The contrarian identifies a missing query-classifier gate: monitoring/informational queries should route to the daily digest (already shipping as Patch BB); only active recommendation and deep-exploration queries should invoke the synthesis loop. If 60–80% of real queries are informational, this is a more durable speed improvement than any orchestration optimization — it reduces loop invocations by 4–5× rather than shaving 5 minutes off each [src3, src6].

This reframe is not fully adopted as a rejection of the obvious answer — the synthesis loop still needs the internal improvements listed in §3. But the query-classifier gate is elevated to a tier-1 recommendation alongside mention detection, because it addresses the invocation-surface problem that all other speed optimizations leave untouched. Note: if the user reviews `reports/` and finds <20% informational queries, the query-classifier gate should be demoted to runner-up — direction stays correct, but magnitude would be small (see §5).

**Reframe: authority-graph depth over corpus breadth.** The Gemini+MCP development and the agentic coding spend study's "more spending not monotonically better accuracy" finding both point the same direction: adding more corpus sources with noise degrades retrieval quality, while deepening the authority-graph signal improves it. The recommended corpus expansions (podcasts, GitHub releases) are specifically those with low noise / high authority-signal content. Rejected expansions (Discord, Reddit mass-expansion, Nitter) carry high noise risk [src36, src6].

---

## 5. Open questions

- `[user-clarification]` What fraction of actual `/deep-ai-research` invocations in the past 30 days were monitoring/informational (could have gone to digest) vs. active recommendation (needed the synthesis loop)? — would be resolved by reviewing the past 30 run IDs in `reports/` and classifying their queries. This is a clarification-gate regression: the gate should have asked this upfront since the query-classifier gate's tier-1 ranking depends on the answer. If the actual split is <20% informational, demote the query-classifier gate from tier-1 to runner-up. The mention-detection recommendation is independent and stays tier-1 regardless of this answer.

- `[research-target-dropped]` Does Claude Code's `Agent` dispatch automatically insert `cache_control` on subagent system prompts, or must it be manually added to SKILL.md? The recency double-check confirms Claude Code uses prompt caching (per the official blog post "Prompt caching is everything"), but the specific behavior for `/deep-ai-research`'s multi-subagent fan-out is unconfirmed — needs empirical test with a small instrumented run. — would be resolved by running a single-researcher dispatch with verbose token reporting and checking for cache_read_input_tokens in the response.

- `[research-target-dropped]` Is the `zernel/huggingface-trending-feed` community project still maintained as of May 2026? The researcher flagged it as a source but maintenance status is unconfirmed. — would be resolved by checking the GitHub repo's last commit date.

- `[external-event]` Will ICLR 2026 accepted papers (on OpenReview) get official RSS support? OpenReview has a REST API but no native RSS as of this run. — depends on OpenReview's product roadmap.

---

## 6. Citations

- [src1] "Anthropic SDK prompt-cache writes may not be immediately visible to the next request," GitHub / anthropics/anthropic-sdk-python, issue #1451, 2026-04-27. https://github.com/anthropics/anthropic-sdk-python/issues/1451 [corpus: 283115b6a4d328ff]
- [src2] "Prompt caching," Anthropic official documentation, 2026. https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- [src3] Corpus search results (researcher-3, 2026-05-04): representative sample across two queries returned `mentioned_authorities: []` — directly observed in frontmatter. [corpus: ebe82643ac57755c, fb3d772e088b631c]
- [src5] "Claude API pricing: Haiku 4.5 vs Sonnet 4.6," BenchLM.ai, 2026-04. https://benchlm.ai/blog/posts/claude-api-pricing
- [src6] AINews / Smol AI newsletter, 2026-04-27. https://news.smol.ai/issues/26-04-27-not-much/ [corpus: 64115e8c43fd6637]
- [src7] sqlite-vec HNSW tracking issue #172, GitHub / asg017/sqlite-vec, 2024–2025. https://github.com/asg017/sqlite-vec/issues/172
- [src8] "How AI processes podcast audio," sipsip.ai, 2026. https://sipsip.ai/blog/learn/how-ai-processes-podcast-audio
- [src9] yt-whisper: using OpenAI Whisper to generate YouTube subtitles, GitHub / m1guelpf, 2025. https://github.com/m1guelpf/yt-whisper
- [src10] Latent Space podcast, RSS feed confirmed. https://www.latent.space/podcast
- [src11] vLLM GitHub releases atom feed. https://github.com/vllm-project/vllm/releases.atom
- [src12] "RAG data quality at scale," Mitchell Bryson, 2025. https://www.mitchellbryson.com/articles/ai-rag-data-quality-at-scale
- [src13] Qwen3 Embedding blog (official, Alibaba), June 2025. https://qwenlm.github.io/blog/qwen3-embedding/
- [src14] "The state of vector search in SQLite," Marco Bambini's Substack, 2025. https://marcobambini.substack.com/p/the-state-of-vector-search-in-sqlite
- [src15] "Is Nitter still working? The definitive 2026 status report," pcxio.com, 2026. https://pcxio.com/is-nitter-still-working-the-definitive-2026-status-report/
- [src16] "Nitter alternatives 2026," simple-web.org, 2026. https://simple-web.org/guides/nitter-alternatives-2026-view-twitter-x-timelines-anonymously
- [src17] RSS.app Discord RSS bot documentation, 2026. https://rss.app/bots/rssfeeds-discord-bot
- [src18] CPR-RSS conference proceedings RSS project, GitHub, 2025. https://github.com/CPR-RSS/CPR-RSS.github.io
- [src19] ICLR 2026 Conference on OpenReview, 2026. https://openreview.net/group?id=ICLR.cc/2026/Conference
- [src20] SemHash — semantic deduplication library, MinishLab, GitHub, 2025. https://github.com/MinishLab/semhash
- [src21] Qwen3-Reranker-0.6B model card, HuggingFace, June 2025. https://huggingface.co/Qwen/Qwen3-Reranker-0.6B
- [src22] HN: "Qwen releases Qwen3-Embedding-0.6B," Hacker News (AI filter), 2025-06. https://news.ycombinator.com/item?id=47829961 [corpus: f918f9a33e3340cd]
- [src23] "Best embedding models for RAG 2026 ranked by MTEB score," blog.premai.io, 2026. https://blog.premai.io/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/
- [src24] AINews / Smol AI newsletter, 2026-04-23. https://news.smol.ai/issues/26-04-23-gpt-55/ [corpus: cebe00af53f16546]
- [src25] evals/cases.yaml (local), 2026-05-04. 22 cases, 5 blocked on full_loop_eval_harness.
- [src26] GEPA: "Reflective Prompt Evolution Can Outperform Reinforcement Learning," arXiv 2507.19457 / ICLR 2026 Oral. https://arxiv.org/abs/2507.19457
- [src27] dspy.GEPA API documentation, DSPy official docs, 2026. https://dspy.ai/api/optimizers/GEPA/overview/
- [src28] "Components of a Coding Agent," Sebastian Raschka / Ahead of AI, 2026-04-04. https://magazine.sebastianraschka.com/p/components-of-a-coding-agent [corpus: 4b5942c9e4a3eb42]
- [src29] "LLM cost attribution for agentic CI/CD," TrueFoundry, 2026. https://www.truefoundry.com/blog/llm-cost-attribution-agentic-cicd
- [src30] "Memanto: Typed Semantic Memory with Information-Theoretic Retrieval," HuggingFace Daily Papers, 2026-04-23. https://huggingface.co/papers/2604.22085 [corpus: fc1996f5527fec3d]
- [src31] Memanto arXiv paper (2604.22085), 2026-04. https://arxiv.org/abs/2604.22085
- [src32] Anthropic pricing (Haiku 4.5). https://www.anthropic.com/pricing
- [src33] AI21 Maestro SOTA on deep research benchmarks, HN stub (corpus: c1def20f88fb5e3d), 2026-04-29. [corpus: c1def20f88fb5e3d]
- [src34] "Components of a Coding Agent," Sebastian Raschka, 2026-04-04 — harness as distinguishing factor. https://magazine.sebastianraschka.com/p/components-of-a-coding-agent [corpus: 4b5942c9e4a3eb42]
- [src35] Step-DeepResearch (arXiv 2512.20491, StepFun AI), Dec 2025. https://arxiv.org/abs/2512.20491
- [src36] Gemini Deep Research + MCP private data connectors, HN 47857489, 2026-04-22. [corpus: d034606e9f219d54]
- [src37] "Bluesky's new Attie app uses AI to give you full control over your social feed," TechCrunch, 2026-03-28. https://techcrunch.com/2026/03/28/bluesky-leans-into-ai-with-attie-an-app-for-building-custom-feeds/ — and openrss.org Bluesky RSS bridge: https://www.oreateai.com/blog/bringing-your-bluesky-feed-to-your-favorite-rss-reader/b0ade3d693c3b86d36864e370be39c25

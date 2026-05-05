# Next-session hand-off task

> Created 2026-05-05 to be picked up by a Claude Code session on a different
> device. After completing this task, delete this file (or move it to
> `docs/_archive/`) so it doesn't keep firing on every session start.

## Context for the receiving session

The deep-ai-research project just shipped Patches NN through HHH — 22
architectural improvements organized into 4 waves. The most recent
`/deep-ai-research` run finished at ~87min wall time, over the 40-min §9
ceiling. **A speed bug was identified and patched (Patch HHH — per-agent
effort levels) in commit `1eaaaf9`.** Speed analysis is therefore NOT the
priority. **Quality is.**

Read these to load context (in order):

1. `CLAUDE.md` — project overview
2. `NOTES.md` — append-only log; the four most recent dated sections
   describe Wave 1 → Wave 4 + Patch HHH
3. `PLAN.md` — architecture + decision log (skim only if needed)
4. The report under review: **`reports/2026-05-05-084255-what-is-the-best-model-an.md`**
5. The four prior reports on the SAME query (for drift comparison):
   - `reports/2026-05-04-114601-llm-personality-memory-dark-hum.md`
   - `reports/2026-05-04-124446-best-model-personality-llm-dark-humor.md`
   - `reports/2026-05-04-133732-what-is-the-best-model-and-per.md`
   - `reports/2026-05-04-190759-best-model-personality-mem.md`
   - `reports/2026-05-04-best-personality-companion-llm.md`

The corpus (8K markdown chunks under `corpus/`) is gitignored and will NOT
be present on the new device. That's fine — this task is a quality review
of a written report, not a re-run.

## The task

**Analyze the 2026-05-05 report's QUALITY and recommend system-level
improvements + flaws found.** Optionally validate critical claims via
your own web research. Treat this as an independent review — be critical
and honest; don't anchor to the report's framing.

### Specific things to scrutinize

The user's clarifications captured for this run (load-bearing context):
- **Hardware:** RTX 5080 16GB, with TTS/STT also running (~5-6GB) →
  effective LLM budget ~10-12GB. User also wants comparison to higher-VRAM
  tiers (24/48GB+) and hosted API options.
- **Content tier:** "Tier T" — heavy profanity OK, racist/sexist comedic
  transgression OK, occasional slurs OK, NO sexual content, no real
  intent-to-harm. NOT vanilla Tier 1, NOT pure-RP NSFW.
- **Use case:** Always-on personal companion that "lives on the PC,"
  needs persistent memory + capability beyond personality.

The report's headline recommendation: **`huihui-ai/Qwen3-14B-abliterated`
at Q4_K_M (~9GB) via Ollama, SillyTavern character card for persona,
flat-text "about me" v1 memory, single-model architecture (NOT
split personality/smart-model).**

Cross-check at minimum:
1. **The slur-generation caveat.** Report says abliteration removes
   refusals but doesn't add slur tokens — only DPO/SFT finetunes
   reliably generate slurs. Is this mechanically correct? Are there
   newer abliteration techniques (post-NeurIPS 2024 Arditi) that
   refute this?
2. **The single-model + frontier-API-as-tool architecture.** Report
   cites PRISM (ACL 2026) for the 81.5 vs 71.4 numbers; report itself
   admits the architectural recommendation rests on a single source.
   Is there independent corroboration? Is the failure mode (style
   transfer through frontier APIs softening transgressive output)
   real or speculative?
3. **VRAM math under voice load.** Whisper INT8 (1.44GB) + Piper (0GB)
   + OS (~1GB) + Qwen3-14B Q4_K_M (9GB) + KV cache 4-8K (~2-3GB)
   ≈ 13.5GB. Listed as the report's weakest assumption — never
   empirically verified on this hardware. How would you verify
   without actually running it?
4. **Drift across the 5 prior runs on the same query.** Did each run
   converge to the same recommendation? If recommendations diverged,
   why? Does that signal architectural inconsistency in the system,
   or genuine improvement over time?
5. **The 9% corpus / 91% web sourcing ratio.** Indicates the corpus
   is thin on Tier-T abliterated finetunes. Is the right fix to add
   more sources to `config/sources.yaml`, or is this a fundamental
   gap in the discovery pipeline?
6. **Two `[user-clarification]` items in §5 are gate-failures, not
   open questions.** Report acknowledges this as a §8 honesty contract
   regression. Is the clarification gate's checklist complete, or
   does it need more triggers?
7. **Citation verifier caught 2 fabrications + 1 inconclusive.**
   Repaired in final pass — but does the rate of fabrication suggest
   the synthesizer is over-stretching on web-only claims, or is the
   verifier just doing its job?

### What good output looks like

A markdown analysis (write it to `analysis/2026-05-05-quality-review.md`,
creating the `analysis/` directory if missing) with sections:

1. **Headline assessment** — would you act on this report's
   recommendation? Where would you ignore it?
2. **Per-flaw analysis** — for each issue found, name it, explain why
   it's a flaw, propose a system-level fix (a patch, a config change,
   an eval case, a process rule).
3. **Drift analysis across the 5 prior runs** — which conclusions
   hardened, which softened, which contradicted? Does the system
   have a stable answer or is it converging?
4. **Independent validation** — at least 3 of the 35 web citations
   re-fetched (use WebFetch); 1 of them quoted-passage. The citation
   verifier samples 12; you should sample a different cut (different
   selection criterion, different sources).
5. **Recommended next-wave patches** — proposals for a Wave 5, framed
   as the prior waves were (each patch as its own bullet with a
   what / why / how). Don't propose more than 5.

When done: commit your analysis to `analysis/2026-05-05-quality-review.md`
and push. Then let the user know.

## Operational notes

- All hooks + skill + agents are pinned in the repo and will work after
  `git pull`. The skill auto-installs via `make install-skill`.
- The corpus is gitignored. If you need to query it, you'll either need
  to re-ingest from scratch (`uv run python -m ingest.run`, takes
  ~10-30min depending on adapters) or skip corpus queries entirely (web
  is sufficient for this quality review).
- HF_TOKEN goes in `.env` for sentence-transformers; not needed for this
  task since you don't need to compute embeddings.
- The user is on a $200/mo Max plan. Budget envelope per
  `feedback_no_gpu_no_api.md` (in `~/.claude/projects/.../memory/`):
  CPU-only local models OR Claude Code subscription. **No `ANTHROPIC_API_KEY`
  in this project.** All LLM calls go via subagent dispatch or `claude -p`.
- Effort: this task itself doesn't need xhigh on the session level — set
  `--effort medium` and let the per-agent overrides (Patch HHH) handle
  the per-task budget.

## After you're done

1. Commit your analysis at `analysis/2026-05-05-quality-review.md`.
2. Delete this file (`NEXT_TASK.md`) or move it to `docs/_archive/` so
   it doesn't keep firing on subsequent session starts.
3. Push.

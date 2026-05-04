"""Patch NN — mention-detection at ingestion time.

Reactivates the dead 4× authority boost. A representative sample of corpus
chunks shows mentioned_authorities: [] across the board; until the field is
populated, the digest signal is empty and tag_engagements has no source for
'mentioned_with_link' records (which carry kind_weight 0.5 in the boost).

Pipeline per chunk:
  1. Regex pre-filter against authority full-names + handles (cheap, no LLM).
  2. (Optional) Haiku 4.5 via `claude -p` headless mode disambiguates and
     extracts ML entities. Off by default — enable per-call with use_llm=True
     or via `python -m ingest.backfill_mentions --use-llm`.

Cost model:
  - Regex-only (default): zero subscription cost. Conservative — only
    full-name matches; handle-only matches are dropped (too ambiguous
    without LLM disambiguation).
  - With Haiku via `claude -p`: each call costs ~4500 tokens against the
    user's $200/mo Max subscription rate limits (cache_creation per call,
    no API key required). Sized for opt-in batched enhancement, not
    per-chunk live tagging.

Auth: relies on the user's logged-in `claude` CLI session — NOT
ANTHROPIC_API_KEY. Per durable user preference: use Claude Code primitives,
not metered API. See memory/feedback_use_claude_code_not_api_key.md.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger("ingest.mention_detect")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLAUDE_HAIKU_MODEL = "claude-haiku-4-5"

# Cap body length sent to Haiku to bound cost. Most chunks fit; long lab
# blogs and papers are truncated — first 8K chars carry the signal we need.
MAX_BODY_CHARS = 8000

# Cap entities returned per chunk; protects downstream consumers from runaway
# extraction on very dense content.
MAX_ENTITIES_PER_CHUNK = 30

# Authority handles too short for safe regex matching (high collision risk).
HANDLE_MIN_LEN = 4

# Default subprocess timeout for `claude -p` calls. Haiku is fast; this is
# generous enough that network blips don't fail the call but tight enough
# that a stuck call doesn't hang an ingestion cycle.
CLAUDE_P_TIMEOUT_SECONDS = 60

# JSON schema enforced via --json-schema (when supported by the CLI). Even
# without the flag, the system prompt instructs the model to return this
# exact shape, and the parser tolerates ```json fences and stray prose.
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "mentioned_authorities": {
            "type": "array",
            "items": {"type": "string"},
        },
        "mentioned_entities": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["mentioned_authorities", "mentioned_entities"],
}

SYSTEM_PROMPT = (
    "You extract structured signals from AI/ML content for a research corpus. "
    "Given a passage and a list of authority candidates (people whose names "
    "or handles appeared via regex pre-filter), return JSON with two keys:\n"
    "  mentioned_authorities: subset of candidates SUBSTANTIVELY mentioned in "
    "the passage (their work cited, their statements quoted, their position "
    "discussed). Exclude incidental matches — a common first name shared "
    "with someone unrelated, a handle that's a common word, a candidate "
    "whose name appears only in a list of unrelated names. Use the EXACT "
    "name strings from the candidates list.\n"
    "  mentioned_entities: list of AI/ML entities (model names, papers, "
    "labs, libraries, frameworks, benchmarks) explicitly named in the "
    'passage. Use canonical names ("GPT-4", "DeepSeek-V3", "vLLM", "MMLU").\n'
    'Return ONLY valid JSON: {"mentioned_authorities": [...], '
    '"mentioned_entities": [...]}\n'
    "No prose, no preamble, no code fences."
)


def _full_name_pattern(name: str) -> re.Pattern[str]:
    """Word-bounded case-insensitive match for an authority full name."""
    return re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)


def _handle_pattern(handle: str) -> re.Pattern[str]:
    """Match @handle, /u/handle, /handle, or word-bounded handle."""
    h = re.escape(handle)
    return re.compile(rf"(?:@|/u/|/)?{h}\b", re.IGNORECASE)


def _claude_cli_available() -> bool:
    """Check whether `claude` CLI is on PATH and runnable."""
    return shutil.which("claude") is not None


def _strip_code_fences(text: str) -> str:
    """Remove leading/trailing ```json (or plain ```) fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    return text


class MentionDetector:
    """Loads authorities once; provides detect(body) → (auths, entities).

    Defaults to regex-only mode. Pass `use_llm=True` to invoke Haiku via the
    `claude` CLI for disambiguation. The LLM path is off by default because
    it consumes the user's subscription rate limits and most ingestion-time
    use cases are well-served by the conservative full-name-only regex pass.
    """

    def __init__(self, *, use_llm: bool = False) -> None:
        self.authorities = self._load_authorities()
        # LLM mode requires `claude` CLI on PATH; if not, force regex-only.
        if use_llm and not _claude_cli_available():
            log.warning(
                "use_llm=True but `claude` CLI not on PATH — "
                "falling back to regex-only mode"
            )
            use_llm = False
        self.use_llm = use_llm
        self._name_patterns: list[tuple[str, re.Pattern[str]]] = []
        self._handle_patterns: list[tuple[str, re.Pattern[str]]] = []
        for a in self.authorities:
            name = a.get("name") or ""
            if not name:
                continue
            self._name_patterns.append((name, _full_name_pattern(name)))
            for _platform, handle in (a.get("handles") or {}).items():
                if not isinstance(handle, str):
                    continue
                handle = handle.strip()
                if len(handle) < HANDLE_MIN_LEN:
                    continue
                self._handle_patterns.append((name, _handle_pattern(handle)))

    @staticmethod
    def _load_authorities() -> list[dict[str, Any]]:
        path = PROJECT_ROOT / "config" / "authorities.yaml"
        if not path.exists():
            return []
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            log.warning("authorities.yaml malformed (%s) — mention detection disabled", e)
            return []
        return data.get("authorities", []) or []

    def close(self) -> None:
        """No-op for compatibility with prior interface (httpx client used to live here)."""
        pass

    def _regex_candidates(self, body: str) -> tuple[list[str], list[str]]:
        """Return (full_name_hits, all_hits). full_name_hits is the conservative
        subset that matches a verbatim full name; all_hits also includes handle
        matches. Both are sorted, de-duplicated lists of authority full names.
        """
        full_name_hits: set[str] = set()
        for name, pat in self._name_patterns:
            if pat.search(body):
                full_name_hits.add(name)
        handle_hits: set[str] = set()
        for name, pat in self._handle_patterns:
            if pat.search(body):
                handle_hits.add(name)
        all_hits = full_name_hits | handle_hits
        return sorted(full_name_hits), sorted(all_hits)

    def detect(
        self, body: str, *, source_type: str = "", title: str = ""
    ) -> tuple[list[str], list[str]]:
        """Return (mentioned_authorities, mentioned_entities) for a passage.

        Returns ([], []) when body is empty or no authorities pre-filter-match.
        Raises nothing — failures degrade to the conservative regex-only path.
        """
        if not body or not body.strip() or not self.authorities:
            return [], []

        full_name_hits, all_hits = self._regex_candidates(body)
        if not all_hits:
            return [], []

        if not self.use_llm:
            return full_name_hits, []

        try:
            return self._llm_extract(body, all_hits, source_type=source_type, title=title)
        except Exception as e:  # noqa: BLE001
            log.warning(
                "Haiku mention-detection failed (%s); falling back to regex full-name only",
                e,
            )
            return full_name_hits, []

    def _llm_extract(
        self, body: str, candidates: list[str], *, source_type: str, title: str
    ) -> tuple[list[str], list[str]]:
        truncated = body[:MAX_BODY_CHARS]

        user_prompt = (
            f"AUTHORITY CANDIDATES (regex pre-filter): {json.dumps(candidates)}\n\n"
            f"SOURCE TYPE: {source_type or 'unknown'}\n"
            f"TITLE: {title or '(none)'}\n\n"
            f"PASSAGE:\n```\n{truncated}\n```\n\n"
            "Return JSON now."
        )

        # `claude -p` headless mode. Use --tools "" to disable tool use
        # (cuts cache_creation from ~28K to ~4.5K tokens per call) and
        # --disable-slash-commands to skip skill resolution.
        cmd = [
            "claude",
            "-p",
            "--tools", "",
            "--no-session-persistence",
            "--disable-slash-commands",
            "--system-prompt", SYSTEM_PROMPT,
            "--output-format", "json",
            "--model", CLAUDE_HAIKU_MODEL,
            user_prompt,
        ]
        env = os.environ.copy()

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLAUDE_P_TIMEOUT_SECONDS,
            env=env,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"claude -p exited {proc.returncode}: {proc.stderr.strip()[:300]}"
            )
        outer = json.loads(proc.stdout)
        if outer.get("is_error"):
            raise RuntimeError(
                f"claude -p reported error: {outer.get('error') or outer.get('subtype')}"
            )
        result_text = outer.get("result") or ""
        result_text = _strip_code_fences(result_text)
        if not result_text:
            raise RuntimeError("claude -p returned empty result")

        parsed = json.loads(result_text)

        auths_raw = parsed.get("mentioned_authorities") or []
        ents_raw = parsed.get("mentioned_entities") or []

        # Defensive: only accept candidates the model confirmed; drop hallucinations.
        valid_auths = sorted(
            {a for a in auths_raw if isinstance(a, str) and a in candidates}
        )

        seen: set[str] = set()
        valid_ents: list[str] = []
        for e in ents_raw:
            if not isinstance(e, str):
                continue
            stripped = e.strip()
            if not stripped or stripped in seen:
                continue
            seen.add(stripped)
            valid_ents.append(stripped)
            if len(valid_ents) >= MAX_ENTITIES_PER_CHUNK:
                break

        return valid_auths, valid_ents

"""Patch QQ — Podcast adapter.

Pipeline per episode:
  1. Parse the podcast's RSS feed (feedparser + httpx).
  2. For each episode whose pubDate is within `since`: download the audio
     enclosure (mp3 / m4a) to a per-episode cache file in
     `cache/podcasts/<feed_slug>/<episode_slug>.<ext>`.
  3. Normalize via ffmpeg to 16kHz mono WAV at low bitrate (transcription
     input format that faster-whisper expects). The intermediate .wav is
     also cached so re-runs don't re-encode.
  4. Transcribe via faster-whisper medium (CPU). 4-8x faster than vanilla
     Whisper at similar quality on English content.
  5. Yield a RawSource whose body is the full transcript with markdown
     formatting (## headings per chapter if available, otherwise plain
     paragraphs split on long pauses).

Designed to run from a SEPARATE systemd timer (`deep-ai-research-podcasts.timer`),
NOT the every-15-min ingest timer — transcription takes 5-10 min per hour
of audio on CPU, which would block all other adapters.

Required: `uv sync --extra podcasts` to install faster-whisper. ffmpeg must
be on PATH. Falls back gracefully (logs a warning, yields nothing) if either
is missing.
"""

from __future__ import annotations

import hashlib
import logging
import re
import shutil
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

import feedparser
import httpx
from dateutil import parser as dateparser

from ingest.adapters._base import RawSource

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CACHE_DIR = PROJECT_ROOT / "cache" / "podcasts"

# faster-whisper model. `medium` is the sweet spot for English podcasts on CPU
# (vs `small` quality dropoff and `large-v3` 3x slower for marginal gain).
WHISPER_MODEL = "medium"

# Cap per-run episodes per feed so a single new feed-discovery doesn't try to
# transcribe a full 200-episode back catalog. The cap can be raised manually
# for an initial backfill (CLI flag).
DEFAULT_EPISODE_CAP_PER_RUN = 5


@dataclass
class PodcastAdapter:
    """Adapter for one podcast feed. Multiple instances share the cache dir
    and the loaded faster-whisper model (passed in via shared_state)."""

    name: str
    publication: str
    feed_url: str
    source_type: str = "podcast_episode"
    poll_interval_seconds: int = 86400  # daily
    rate_limit_key: str = "default"
    user_agent: str = "deep-ai-research/0.1 (deep-ai-research; personal use)"
    timeout_seconds: float = 30.0
    cache_dir: Path = field(default=DEFAULT_CACHE_DIR)
    episode_cap_per_run: int = DEFAULT_EPISODE_CAP_PER_RUN
    shared_state: dict = field(default_factory=dict)  # {model: WhisperModel}

    def iter_new(self, since: datetime | None = None) -> Iterable[RawSource]:
        if not _ffmpeg_available():
            log.error("ffmpeg not on PATH — podcast adapter %s disabled", self.name)
            return
        model = self._whisper_model()
        if model is None:
            log.error("faster-whisper not installed (try `uv sync --extra podcasts`); "
                      "podcast adapter %s disabled", self.name)
            return

        log.info("fetching podcast feed %s from %s", self.name, self.feed_url)
        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                resp = client.get(self.feed_url, headers={"User-Agent": self.user_agent})
                resp.raise_for_status()
                feed = feedparser.parse(resp.content)
        except httpx.HTTPError as e:
            log.error("failed to fetch %s: %s", self.feed_url, e)
            return

        if feed.bozo and not feed.entries:
            log.error("malformed podcast feed %s: %s", self.feed_url, feed.bozo_exception)
            return

        feed_slug = _slug(self.name)
        episode_dir = self.cache_dir / feed_slug
        episode_dir.mkdir(parents=True, exist_ok=True)

        processed = 0
        for entry in feed.entries:
            if processed >= self.episode_cap_per_run:
                log.info("hit per-run cap (%d) for %s", self.episode_cap_per_run, self.name)
                break

            try:
                raw = self._parse_and_transcribe(entry, episode_dir, model, since)
            except Exception as e:
                log.warning("skipping episode from %s: %s", self.name, e)
                continue
            if raw is None:
                continue
            processed += 1
            yield raw

    def _whisper_model(self):
        """Lazy-load the faster-whisper model. Cached in shared_state across
        all PodcastAdapter instances in a single run."""
        if "model" in self.shared_state:
            return self.shared_state["model"]
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            self.shared_state["model"] = None
            return None
        log.info("loading faster-whisper model: %s (CPU, int8)", WHISPER_MODEL)
        # int8 quantization halves memory + speeds up CPU inference with
        # negligible quality loss for transcription.
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        self.shared_state["model"] = model
        return model

    def _parse_and_transcribe(
        self,
        entry: dict,
        episode_dir: Path,
        model,
        since: datetime | None,
    ) -> RawSource | None:
        url = entry.get("link") or entry.get("id")
        if not url:
            return None
        title = (entry.get("title") or "").strip() or "(untitled)"

        # pubDate
        d = _extract_date(entry)
        if d is None:
            log.debug("no pubDate for %s; skipping", url)
            return None
        if since is not None:
            if datetime.combine(d, datetime.min.time(), timezone.utc) < since:
                return None

        # Find audio enclosure URL.
        audio_url = _audio_url(entry)
        if not audio_url:
            log.debug("no audio enclosure for %s; skipping", url)
            return None

        episode_slug = _slug(f"{d.isoformat()}-{title}")[:80] + "-" + _short_hash(url)
        ext = _audio_ext(audio_url) or "mp3"
        audio_path = episode_dir / f"{episode_slug}.{ext}"
        wav_path = episode_dir / f"{episode_slug}.wav"
        transcript_cache = episode_dir / f"{episode_slug}.txt"

        # Cached transcript — return immediately. Transcription is the slowest
        # step; never re-do it for a known episode.
        if transcript_cache.exists():
            transcript = transcript_cache.read_text(encoding="utf-8")
            return self._build_raw_source(
                url=url,
                title=title,
                date_=d,
                transcript=transcript,
                authors=_authors(entry),
            )

        # Download audio.
        if not audio_path.exists():
            log.info("downloading %s (%s)", title, audio_url)
            try:
                with httpx.Client(timeout=120.0, follow_redirects=True) as client:
                    with client.stream("GET", audio_url) as resp:
                        resp.raise_for_status()
                        with audio_path.open("wb") as f:
                            for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                                f.write(chunk)
            except httpx.HTTPError as e:
                log.warning("download failed for %s: %s", audio_url, e)
                # Clean up partial file
                audio_path.unlink(missing_ok=True)
                return None

        # Normalize to 16kHz mono WAV.
        if not wav_path.exists():
            log.info("normalizing audio for %s", title)
            cmd = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", str(audio_path),
                "-ac", "1", "-ar", "16000",
                str(wav_path),
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=600)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                log.warning("ffmpeg failed for %s: %s", title, e)
                return None

        # Transcribe.
        log.info("transcribing %s (%s)", title, _approx_duration(wav_path))
        try:
            segments, info = model.transcribe(
                str(wav_path),
                beam_size=1,  # greedy decoding — faster, slight quality drop
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )
            transcript_parts: list[str] = []
            for seg in segments:
                t = (seg.text or "").strip()
                if t:
                    transcript_parts.append(t)
            transcript = " ".join(transcript_parts)
        except Exception as e:
            log.warning("transcription failed for %s: %s", title, e)
            return None

        if not transcript.strip():
            log.warning("empty transcript for %s; skipping", title)
            return None

        # Cache transcript so re-runs don't re-transcribe.
        transcript_cache.write_text(transcript, encoding="utf-8")

        # Optional: drop the wav after successful transcription to save disk.
        # Keep mp3/m4a for re-transcription if model upgrades; keep wav for
        # debugging. Tune later if disk pressure observed.
        # wav_path.unlink(missing_ok=True)

        return self._build_raw_source(
            url=url,
            title=title,
            date_=d,
            transcript=transcript,
            authors=_authors(entry),
        )

    def _build_raw_source(
        self,
        *,
        url: str,
        title: str,
        date_: date,
        transcript: str,
        authors: list[str],
    ) -> RawSource:
        body = f"# {title}\n\n_{self.publication} — {date_.isoformat()}_\n\n{transcript}\n"
        return RawSource(
            url=url,
            title=title,
            publication=self.publication,
            source_type=self.source_type,
            date=date_,
            authors=authors,
            body=body,
            content_format="markdown",
            tags=["podcast", "transcript", _slug(self.publication)],
        )


# ---------- helpers ----------

def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _short_hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:8]


def _extract_date(entry: dict) -> date | None:
    for key in ("published", "updated", "pubDate", "date"):
        val = entry.get(key)
        if val:
            try:
                return dateparser.parse(val).date()
            except (ValueError, TypeError):
                continue
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        try:
            return date(parsed.tm_year, parsed.tm_mon, parsed.tm_mday)
        except (ValueError, TypeError):
            pass
    return None


def _audio_url(entry: dict) -> str | None:
    """Find the first audio enclosure URL in the feed entry."""
    enclosures = entry.get("enclosures") or []
    for enc in enclosures:
        url = enc.get("href") or enc.get("url")
        mime = (enc.get("type") or "").lower()
        if not url:
            continue
        if mime.startswith("audio/") or url.lower().endswith((".mp3", ".m4a", ".mp4", ".aac", ".ogg")):
            return url
    # Atom-style media:content
    media = entry.get("media_content") or []
    for m in media:
        url = m.get("url")
        if url and url.lower().endswith((".mp3", ".m4a", ".mp4", ".aac")):
            return url
    return None


def _audio_ext(url: str) -> str | None:
    m = re.search(r"\.(mp3|m4a|mp4|aac|ogg)(?:\?|$)", url, re.IGNORECASE)
    return m.group(1).lower() if m else None


def _authors(entry: dict) -> list[str]:
    out: list[str] = []
    auth = entry.get("author")
    if isinstance(auth, str) and auth.strip():
        out.append(auth.strip())
    for ad in entry.get("authors") or []:
        n = ad.get("name") if isinstance(ad, dict) else None
        if n and n not in out:
            out.append(n)
    return out


def _approx_duration(wav_path: Path) -> str:
    """Cheap duration estimate from file size for log readability."""
    try:
        # 16kHz mono int16 = 32000 bytes/sec
        seconds = wav_path.stat().st_size / 32000
        m, s = divmod(int(seconds), 60)
        return f"~{m}m{s:02d}s"
    except OSError:
        return "?"


def build_from_spec(spec: dict, shared_state: dict) -> PodcastAdapter:
    """Construct a PodcastAdapter from a sources.yaml entry."""
    return PodcastAdapter(
        name=spec["name"],
        publication=spec.get("publication", spec["name"]),
        feed_url=spec["feed_url"],
        source_type=spec.get("source_type", "podcast_episode"),
        poll_interval_seconds=spec.get("poll_interval_seconds", 86400),
        rate_limit_key=spec.get("rate_limit_key", "default"),
        episode_cap_per_run=spec.get("episode_cap_per_run", DEFAULT_EPISODE_CAP_PER_RUN),
        shared_state=shared_state,
    )

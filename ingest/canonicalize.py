"""URL canonicalization. Turns variant URLs (with tracking params, mixed case,
trailing slashes, mobile prefixes) into a stable canonical form for source_id.
"""

from __future__ import annotations

import hashlib
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

# Tracking params we drop before hashing.
_TRACKING_PARAMS = frozenset(
    {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "ref", "ref_src", "fbclid", "gclid", "mc_cid", "mc_eid",
        "_hsenc", "_hsmi", "hsCtaTracking",
        "source", "share",  # common Substack/Buttondown trackers
    }
)


def canonicalize(url: str) -> str:
    """Return a stable canonical form. Idempotent."""
    parts = urlsplit(url.strip())

    scheme = "https"  # always https; we don't care about http variants
    netloc = parts.netloc.lower()

    # Twitter/X normalization (kept for v2 — Twitter deferred in v1)
    if netloc in ("twitter.com", "mobile.twitter.com", "www.twitter.com"):
        netloc = "x.com"
    if netloc.startswith("www."):
        netloc = netloc[4:]

    # Drop tracking params; preserve everything else.
    if parts.query:
        kept = {
            k: v for k, v in parse_qs(parts.query, keep_blank_values=True).items()
            if k.lower() not in _TRACKING_PARAMS
        }
        # Sort for stability.
        query = urlencode(sorted(kept.items()), doseq=True)
    else:
        query = ""

    # Strip trailing slash except on root.
    path = parts.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    return urlunsplit((scheme, netloc, path, query, ""))


def source_id(canonical_url: str, *, length: int = 16) -> str:
    """Stable id from canonical URL. 16 hex chars = 64 bits collision space."""
    return hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()[:length]


def content_hash(text: str) -> str:
    """sha256 of normalized content for revision detection."""
    normalized = text.strip()
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()

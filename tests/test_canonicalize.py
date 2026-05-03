"""Tests for URL canonicalization and stable IDs."""

from ingest.canonicalize import canonicalize, content_hash, source_id


class TestCanonicalize:
    def test_strips_tracking_params(self) -> None:
        url = "https://example.com/post?utm_source=feed&utm_medium=rss&id=42"
        canon = canonicalize(url)
        assert "utm_source" not in canon
        assert "utm_medium" not in canon
        assert "id=42" in canon

    def test_lowercases_host(self) -> None:
        assert canonicalize("https://Example.COM/Path") == "https://example.com/Path"

    def test_strips_trailing_slash(self) -> None:
        assert canonicalize("https://example.com/post/") == "https://example.com/post"

    def test_preserves_root_slash(self) -> None:
        assert canonicalize("https://example.com/") == "https://example.com/"

    def test_normalizes_twitter_to_x(self) -> None:
        assert canonicalize("https://twitter.com/user/status/1") == "https://x.com/user/status/1"
        assert canonicalize("https://mobile.twitter.com/user/status/1") == "https://x.com/user/status/1"

    def test_strips_www(self) -> None:
        assert canonicalize("https://www.example.com/post") == "https://example.com/post"

    def test_idempotent(self) -> None:
        url = "https://example.com/post?utm_source=x&id=42"
        once = canonicalize(url)
        twice = canonicalize(once)
        assert once == twice

    def test_query_param_order_stable(self) -> None:
        a = canonicalize("https://example.com/post?b=2&a=1")
        b = canonicalize("https://example.com/post?a=1&b=2")
        assert a == b


class TestSourceId:
    def test_deterministic(self) -> None:
        url = "https://example.com/post"
        assert source_id(url) == source_id(url)

    def test_different_urls_different_ids(self) -> None:
        assert source_id("https://example.com/a") != source_id("https://example.com/b")

    def test_length_default_16(self) -> None:
        assert len(source_id("https://example.com/post")) == 16


class TestContentHash:
    def test_deterministic(self) -> None:
        assert content_hash("hello world") == content_hash("hello world")

    def test_different_content_different_hash(self) -> None:
        assert content_hash("a") != content_hash("b")

    def test_strips_whitespace(self) -> None:
        # Trailing/leading whitespace shouldn't trigger a revision.
        assert content_hash("hello\n") == content_hash("hello")
        assert content_hash("  hello  ") == content_hash("hello")

    def test_starts_with_sha256(self) -> None:
        assert content_hash("anything").startswith("sha256:")

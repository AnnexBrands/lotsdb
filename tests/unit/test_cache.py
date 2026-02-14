"""Unit tests for catalog.cache safe wrappers (015-redis-caching)."""

from unittest.mock import patch, MagicMock

from catalog.cache import safe_cache_get, safe_cache_set


class TestSafeCacheGet:
    """Tests for safe_cache_get."""

    @patch("catalog.cache.cache")
    def test_returns_cached_value_on_hit(self, mock_cache):
        mock_cache.get.return_value = [{"id": 1}]
        assert safe_cache_get("mykey") == [{"id": 1}]
        mock_cache.get.assert_called_once_with("mykey", None)

    @patch("catalog.cache.cache")
    def test_returns_default_on_miss(self, mock_cache):
        mock_cache.get.return_value = None
        assert safe_cache_get("mykey", default="fallback") is None
        mock_cache.get.assert_called_once_with("mykey", "fallback")

    @patch("catalog.cache.cache")
    def test_returns_default_on_exception(self, mock_cache):
        mock_cache.get.side_effect = ConnectionError("Redis down")
        assert safe_cache_get("mykey", default="safe") == "safe"

    @patch("catalog.cache.cache")
    def test_logs_warning_on_exception(self, mock_cache, caplog):
        mock_cache.get.side_effect = Exception("boom")
        safe_cache_get("mykey")
        assert "Cache read failed for key=mykey" in caplog.text


class TestSafeCacheSet:
    """Tests for safe_cache_set."""

    @patch("catalog.cache.cache")
    def test_calls_cache_set(self, mock_cache):
        safe_cache_set("mykey", [1, 2, 3], timeout=60)
        mock_cache.set.assert_called_once_with("mykey", [1, 2, 3], 60)

    @patch("catalog.cache.cache")
    def test_noop_on_exception(self, mock_cache):
        mock_cache.set.side_effect = ConnectionError("Redis down")
        # Should not raise
        safe_cache_set("mykey", "value")

    @patch("catalog.cache.cache")
    def test_logs_warning_on_exception(self, mock_cache, caplog):
        mock_cache.set.side_effect = Exception("boom")
        safe_cache_set("mykey", "value")
        assert "Cache write failed for key=mykey" in caplog.text

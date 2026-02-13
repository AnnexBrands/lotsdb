"""Tests for catalog.services — concurrent fetching, caching, cache invalidation."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache

from catalog import services


# --- Fixtures ---


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear Django cache before each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def mock_request():
    """Django request mock with valid session token."""
    req = MagicMock()
    req.session = {
        "abc_token": {"access_token": "test", "expires_at": 9999999999},
        "abc_username": "test@example.com",
    }
    return req


def _make_lot(lot_id):
    """Create a picklable lot-like object."""
    return SimpleNamespace(
        id=lot_id,
        customer_item_id=f"ITEM-{lot_id}",
        image_links=[],
        overriden_data=[],
        catalogs=[],
        initial_data=None,
    )


def _make_catalog(catalog_id):
    """Create a picklable catalog-like object."""
    return SimpleNamespace(id=catalog_id, title=f"Catalog {catalog_id}", lots=[])


# --- get_lot caching ---


class TestGetLotCaching:
    def test_cache_miss_fetches_from_api(self, mock_request):
        lot = _make_lot(42)
        with patch.object(services, "get_catalog_api") as mock_api:
            mock_api.return_value.lots.get.return_value = lot
            result = services.get_lot(mock_request, 42)

        assert result.id == 42
        mock_api.return_value.lots.get.assert_called_once_with(42)

    def test_cache_hit_skips_api(self, mock_request):
        lot = _make_lot(42)
        cache.set("lot:42", lot)

        with patch.object(services, "get_catalog_api") as mock_api:
            result = services.get_lot(mock_request, 42)

        assert result.id == 42
        mock_api.assert_not_called()

    def test_fetched_lot_is_cached(self, mock_request):
        lot = _make_lot(42)
        with patch.object(services, "get_catalog_api") as mock_api:
            mock_api.return_value.lots.get.return_value = lot
            services.get_lot(mock_request, 42)

        cached = cache.get("lot:42")
        assert cached is not None
        assert cached.id == 42


# --- get_catalog caching ---


class TestGetCatalogCaching:
    def test_cache_miss_fetches_from_api(self, mock_request):
        cat = _make_catalog(10)
        with patch.object(services, "get_catalog_api") as mock_api:
            mock_api.return_value.catalogs.get.return_value = cat
            result = services.get_catalog(mock_request, 10)

        assert result.id == 10
        mock_api.return_value.catalogs.get.assert_called_once_with(10)

    def test_cache_hit_skips_api(self, mock_request):
        cat = _make_catalog(10)
        cache.set("catalog:10", cat)

        with patch.object(services, "get_catalog_api") as mock_api:
            result = services.get_catalog(mock_request, 10)

        assert result.id == 10
        mock_api.assert_not_called()


# --- save_lot_override cache invalidation ---


class TestSaveLotOverrideCacheInvalidation:
    def test_invalidates_cache_after_save(self, mock_request):
        lot = _make_lot(42)
        cache.set("lot:42", lot)

        with patch.object(services, "get_catalog_api") as mock_api:
            mock_api.return_value.lots.get.return_value = lot
            mock_api.return_value.lots.update.return_value = lot
            services.save_lot_override(mock_request, 42, {"description": "new"})

        assert cache.get("lot:42") is None


# --- get_lots_for_event concurrent + caching ---


class TestGetLotsForEvent:
    def test_empty_ids_returns_empty(self, mock_request):
        assert services.get_lots_for_event(mock_request, []) == []

    def test_all_cached_skips_api(self, mock_request):
        lots = [_make_lot(i) for i in range(3)]
        for lot in lots:
            cache.set(f"lot:{lot.id}", lot)

        with patch.object(services, "get_catalog_api") as mock_api:
            result = services.get_lots_for_event(mock_request, [0, 1, 2])

        mock_api.assert_not_called()
        assert len(result) == 3
        assert result[0].id == 0
        assert result[2].id == 2

    def test_uncached_lots_fetched_and_cached(self, mock_request):
        lots = {i: _make_lot(i) for i in range(5)}

        # Pre-cache lots 0 and 2
        cache.set("lot:0", lots[0])
        cache.set("lot:2", lots[2])

        with patch.object(services, "get_catalog_api") as mock_api:
            mock_api.return_value.lots.get.side_effect = lambda lid: lots[lid]
            result = services.get_lots_for_event(mock_request, [0, 1, 2, 3, 4])

        assert len(result) == 5
        # Verify ordering preserved
        for i in range(5):
            assert result[i].id == i
        # Verify uncached lots are now cached
        assert cache.get("lot:1") is not None
        assert cache.get("lot:3") is not None
        assert cache.get("lot:4") is not None

    def test_preserves_ordering(self, mock_request):
        lots = {i: _make_lot(i) for i in [10, 20, 30]}

        with patch.object(services, "get_catalog_api") as mock_api:
            mock_api.return_value.lots.get.side_effect = lambda lid: lots[lid]
            result = services.get_lots_for_event(mock_request, [10, 20, 30])

        assert [r.id for r in result] == [10, 20, 30]

    def test_graceful_degradation_on_failure(self, mock_request):
        lot1 = _make_lot(1)
        lot3 = _make_lot(3)

        def side_effect(lid):
            if lid == 2:
                raise Exception("API error")
            return {1: lot1, 3: lot3}[lid]

        with patch.object(services, "get_catalog_api") as mock_api:
            mock_api.return_value.lots.get.side_effect = side_effect
            result = services.get_lots_for_event(mock_request, [1, 2, 3])

        # Lot 2 failed, but 1 and 3 should succeed
        assert len(result) == 2
        ids = [r.id for r in result]
        assert 1 in ids
        assert 3 in ids

    @patch("catalog.services.settings")
    def test_uses_configured_max_workers(self, mock_settings, mock_request):
        mock_settings.LOT_FETCH_MAX_WORKERS = 5
        lots = {i: _make_lot(i) for i in range(3)}

        with patch.object(services, "get_catalog_api") as mock_api:
            mock_api.return_value.lots.get.side_effect = lambda lid: lots[lid]
            with patch("catalog.services.ThreadPoolExecutor", wraps=ThreadPoolExecutor) as mock_pool:
                services.get_lots_for_event(mock_request, [0, 1, 2])
                mock_pool.assert_called_once_with(max_workers=5)

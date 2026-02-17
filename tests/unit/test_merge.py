from types import SimpleNamespace
from unittest.mock import patch, call, MagicMock

import pytest

from catalog.services import lots_differ, merge_catalog


def _mock_catalog_obj(seller_display_id="1874"):
    """Build a mock catalog object with sellers for merge_catalog's get_catalog call."""
    return SimpleNamespace(
        sellers=[SimpleNamespace(customer_display_id=seller_display_id)],
    )


def _make_lot_data(**kwargs):
    """Build a SimpleNamespace mimicking LotDataDto with comparison fields."""
    defaults = {"qty": 0, "l": 0.0, "w": 0.0, "h": 0.0, "wgt": 0.0, "cpack": "", "force_crate": False}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_server_lot(lot_id, customer_item_id, initial_data, overriden_data=None):
    """Build a SimpleNamespace mimicking LotDto from server."""
    return SimpleNamespace(
        id=lot_id,
        customer_item_id=customer_item_id,
        initial_data=initial_data,
        overriden_data=overriden_data or [],
        catalogs=[],
        image_links=[],
    )


def _make_file_lot(customer_item_id, initial_data, lot_number="1", image_links=None):
    """Build a SimpleNamespace mimicking BulkInsertLotRequest from file."""
    return SimpleNamespace(
        customer_item_id=customer_item_id,
        lot_number=lot_number,
        image_links=image_links or [],
        initial_data=initial_data,
        overriden_data=[initial_data],
    )


def _make_bulk_request(file_lots, customer_catalog_id="CAT-001"):
    """Build a SimpleNamespace mimicking BulkInsertRequest."""
    catalog = SimpleNamespace(
        customer_catalog_id=customer_catalog_id,
        lots=file_lots,
    )
    return SimpleNamespace(catalogs=[catalog])


class TestLotsDiffer:
    def test_identical_lots_return_false(self):
        a = _make_lot_data(qty=1, l=10.0, w=5.0, h=3.0, wgt=2.0, cpack="3", force_crate=False)
        b = _make_lot_data(qty=1, l=10.0, w=5.0, h=3.0, wgt=2.0, cpack="3", force_crate=False)
        assert lots_differ(a, b) is False

    def test_different_qty_returns_true(self):
        a = _make_lot_data(qty=1)
        b = _make_lot_data(qty=2)
        assert lots_differ(a, b) is True

    def test_none_vs_zero_returns_false(self):
        a = _make_lot_data(qty=None, l=None, w=None, h=None, wgt=None)
        b = _make_lot_data(qty=0, l=0.0, w=0.0, h=0.0, wgt=0.0)
        assert lots_differ(a, b) is False

    def test_different_cpack_returns_true(self):
        a = _make_lot_data(cpack="1")
        b = _make_lot_data(cpack="3")
        assert lots_differ(a, b) is True

    def test_different_force_crate_returns_true(self):
        a = _make_lot_data(force_crate=True)
        b = _make_lot_data(force_crate=False)
        assert lots_differ(a, b) is True

    def test_different_dimensions_returns_true(self):
        a = _make_lot_data(l=10.0, w=5.0, h=3.0)
        b = _make_lot_data(l=10.0, w=5.0, h=4.0)
        assert lots_differ(a, b) is True

    def test_none_cpack_vs_empty_returns_false(self):
        a = _make_lot_data(cpack=None)
        b = _make_lot_data(cpack="")
        assert lots_differ(a, b) is False


class TestMergeCatalog:
    @patch("catalog.services.cache_recovery_entry")
    @patch("catalog.services.get_catalog", return_value=_mock_catalog_obj())
    @patch("catalog.services.create_lot")
    @patch("catalog.services.delete_lot")
    @patch("catalog.services.fetch_all_lots", return_value=[])
    def test_all_new_lots(self, mock_fetch, mock_delete, mock_create, mock_get_cat, mock_cache, db):
        """When server has no lots, all file lots are added."""
        request = SimpleNamespace(session={"abc_username": "test"})
        data = _make_lot_data(qty=1, l=10.0, w=5.0, h=3.0, wgt=2.0, cpack="3", force_crate=False)
        file_lots = [
            _make_file_lot("A", data, "1"),
            _make_file_lot("B", data, "2"),
            _make_file_lot("C", data, "3"),
        ]
        bulk = _make_bulk_request(file_lots)

        result = merge_catalog(request, bulk, catalog_id=42)

        assert result["added"] == 3
        assert result["updated"] == 0
        assert result["unchanged"] == 0
        assert result["failed"] == 0
        assert mock_create.call_count == 3
        mock_delete.assert_not_called()

    @patch("catalog.services.cache_recovery_entry")
    @patch("catalog.services.get_catalog", return_value=_mock_catalog_obj())
    @patch("catalog.services.create_lot")
    @patch("catalog.services.delete_lot")
    @patch("catalog.services.fetch_all_lots")
    def test_all_unchanged(self, mock_fetch, mock_delete, mock_create, mock_get_cat, mock_cache, db):
        """When all lots have identical data, nothing is modified."""
        request = SimpleNamespace(session={"abc_username": "test"})
        data = _make_lot_data(qty=1, l=10.0, w=5.0, h=3.0, wgt=2.0, cpack="3", force_crate=False)
        server_lots = [
            _make_server_lot(1, "A", data),
            _make_server_lot(2, "B", data),
        ]
        mock_fetch.return_value = server_lots

        file_lots = [
            _make_file_lot("A", data, "1"),
            _make_file_lot("B", data, "2"),
        ]
        bulk = _make_bulk_request(file_lots)

        result = merge_catalog(request, bulk, catalog_id=42)

        assert result["added"] == 0
        assert result["updated"] == 0
        assert result["unchanged"] == 2
        assert result["failed"] == 0
        mock_create.assert_not_called()
        mock_delete.assert_not_called()

    @patch("catalog.services.cache_recovery_entry")
    @patch("catalog.services.get_catalog", return_value=_mock_catalog_obj())
    @patch("catalog.services.create_lot")
    @patch("catalog.services.delete_lot")
    @patch("catalog.services.fetch_all_lots")
    def test_mixed_scenario(self, mock_fetch, mock_delete, mock_create, mock_get_cat, mock_cache, db):
        """1 new, 1 changed, 1 unchanged."""
        request = SimpleNamespace(session={"abc_username": "test"})
        same_data = _make_lot_data(qty=1, l=10.0, w=5.0, h=3.0, wgt=2.0, cpack="3")
        changed_data_server = _make_lot_data(qty=1, l=10.0, w=5.0, h=3.0, wgt=2.0, cpack="3")
        changed_data_file = _make_lot_data(qty=2, l=10.0, w=5.0, h=3.0, wgt=2.0, cpack="3")

        server_lots = [
            _make_server_lot(1, "UNCHANGED", same_data),
            _make_server_lot(2, "CHANGED", changed_data_server),
        ]
        mock_fetch.return_value = server_lots

        file_lots = [
            _make_file_lot("UNCHANGED", same_data, "1"),
            _make_file_lot("CHANGED", changed_data_file, "2"),
            _make_file_lot("NEW", same_data, "3"),
        ]
        bulk = _make_bulk_request(file_lots)

        result = merge_catalog(request, bulk, catalog_id=42)

        assert result["added"] == 1
        assert result["updated"] == 1
        assert result["unchanged"] == 1
        assert result["failed"] == 0
        mock_delete.assert_called_once_with(request, 2)
        assert mock_create.call_count == 2

    @patch("catalog.services.cache_recovery_entry")
    @patch("catalog.services.get_catalog", return_value=_mock_catalog_obj())
    @patch("catalog.services.create_lot")
    @patch("catalog.services.delete_lot")
    @patch("catalog.services.fetch_all_lots")
    def test_override_preservation(self, mock_fetch, mock_delete, mock_create, mock_get_cat, mock_cache, db):
        """Changed lot preserves existing overrides from server."""
        request = SimpleNamespace(session={"abc_username": "test"})
        server_data = _make_lot_data(qty=1, l=10.0)
        file_data = _make_lot_data(qty=2, l=10.0)
        override = _make_lot_data(qty=5, l=12.0, w=6.0, h=4.0, wgt=3.0, cpack="2")

        server_lot = _make_server_lot(1, "LOT-X", server_data, overriden_data=[override])
        mock_fetch.return_value = [server_lot]

        file_lots = [_make_file_lot("LOT-X", file_data, "1")]
        bulk = _make_bulk_request(file_lots)

        result = merge_catalog(request, bulk, catalog_id=42)

        assert result["updated"] == 1
        # Verify the create call included the saved override
        create_call = mock_create.call_args
        add_req = create_call[0][1]
        assert len(add_req.overriden_data) == 1
        assert add_req.overriden_data[0].qty == 5
        assert add_req.overriden_data[0].l == 12.0
        assert add_req.overriden_data[0].w == 6.0

    @patch("catalog.services.cache_recovery_entry")
    @patch("catalog.services.get_catalog", return_value=_mock_catalog_obj())
    @patch("catalog.services.create_lot", side_effect=[Exception("server error"), None])
    @patch("catalog.services.delete_lot")
    @patch("catalog.services.fetch_all_lots", return_value=[])
    def test_best_effort_failure(self, mock_fetch, mock_delete, mock_create, mock_get_cat, mock_cache, db):
        """When one lot fails, others continue. Failed count incremented."""
        request = SimpleNamespace(session={"abc_username": "test"})
        data = _make_lot_data(qty=1)
        file_lots = [
            _make_file_lot("FAIL", data, "1"),
            _make_file_lot("OK", data, "2"),
        ]
        bulk = _make_bulk_request(file_lots)

        result = merge_catalog(request, bulk, catalog_id=42)

        assert result["added"] == 1
        assert result["failed"] == 1
        assert len(result["errors"]) == 1
        assert "FAIL" in result["errors"][0]
        # Verify recovery entry was cached for the failed lot
        mock_cache.assert_called_once()
        cached_entry = mock_cache.call_args[0][1]
        assert cached_entry["customer_item_id"] == "FAIL"
        assert cached_entry["operation"] == "create"

    @patch("catalog.services.cache_recovery_entry")
    @patch("catalog.services.get_catalog", return_value=_mock_catalog_obj())
    @patch("catalog.services.create_lot", side_effect=Exception("total failure"))
    @patch("catalog.services.delete_lot")
    @patch("catalog.services.fetch_all_lots", return_value=[])
    def test_100pct_failure_reraise(self, mock_fetch, mock_delete, mock_create, mock_get_cat, mock_cache, db):
        """When ALL lots fail, merge_catalog raises RuntimeError."""
        request = SimpleNamespace(session={"abc_username": "test"})
        data = _make_lot_data(qty=1)
        file_lots = [_make_file_lot("A", data, "1"), _make_file_lot("B", data, "2")]
        bulk = _make_bulk_request(file_lots)

        with pytest.raises(RuntimeError, match="All 2 lots failed"):
            merge_catalog(request, bulk, catalog_id=42)

    @patch("catalog.services.cache_recovery_entry")
    @patch("catalog.services.get_catalog", return_value=_mock_catalog_obj())
    @patch("catalog.services.create_lot")
    @patch("catalog.services.delete_lot")
    @patch("catalog.services.fetch_all_lots", return_value=[])
    def test_duplicate_customer_item_id_dedup(self, mock_fetch, mock_delete, mock_create, mock_get_cat, mock_cache, db):
        """Duplicate customer_item_id in file: only first occurrence processed."""
        request = SimpleNamespace(session={"abc_username": "test"})
        data1 = _make_lot_data(qty=1)
        data2 = _make_lot_data(qty=99)
        file_lots = [
            _make_file_lot("DUP", data1, "1"),
            _make_file_lot("DUP", data2, "2"),
        ]
        bulk = _make_bulk_request(file_lots)

        result = merge_catalog(request, bulk, catalog_id=42)

        assert result["added"] == 1
        mock_create.assert_called_once()
        add_req = mock_create.call_args[0][1]
        assert add_req.initial_data.qty == 1

    @patch("catalog.services.cache_recovery_entry")
    @patch("catalog.services.get_catalog", return_value=_mock_catalog_obj())
    @patch("catalog.services.create_lot")
    @patch("catalog.services.delete_lot")
    @patch("catalog.services.fetch_all_lots", return_value=[])
    def test_merge_returns_seller_and_catalog_ids(self, mock_fetch, mock_delete, mock_create, mock_get_cat, mock_cache, db):
        """Merge result includes seller_display_id and customer_catalog_id for redirect."""
        request = SimpleNamespace(session={"abc_username": "test"})
        data = _make_lot_data(qty=1)
        file_lots = [_make_file_lot("A", data, "1")]
        bulk = _make_bulk_request(file_lots, customer_catalog_id="EVT-100")

        result = merge_catalog(request, bulk, catalog_id=42)

        assert result["seller_display_id"] == "1874"
        assert result["customer_catalog_id"] == "EVT-100"

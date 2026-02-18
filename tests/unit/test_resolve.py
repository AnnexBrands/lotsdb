from types import SimpleNamespace
from unittest.mock import patch

import pytest

from catalog.services import resolve_item


def _mock_lot(lot_id, customer_item_id, catalog_id):
    return SimpleNamespace(
        id=lot_id,
        customer_item_id=customer_item_id,
        catalogs=[SimpleNamespace(catalog_id=catalog_id)],
    )


def _mock_catalog(catalog_id, customer_catalog_id, seller_display_id, lots=None):
    return SimpleNamespace(
        id=catalog_id,
        customer_catalog_id=customer_catalog_id,
        sellers=[SimpleNamespace(customer_display_id=seller_display_id)],
        lots=lots or [],
    )


def _mock_paginated(items):
    return SimpleNamespace(items=items)


class TestResolveItem:
    @patch("catalog.services.get_catalog")
    @patch("catalog.services.get_catalog_api")
    def test_item_found_returns_correct_dict(self, mock_api, mock_get_cat, db):
        lot = _mock_lot(100, "ITEM-1", 42)
        mock_api.return_value.lots.list.return_value = _mock_paginated([lot])
        catalog_lots = [
            SimpleNamespace(id=99),
            SimpleNamespace(id=100),
            SimpleNamespace(id=101),
        ]
        mock_get_cat.return_value = _mock_catalog(42, "EVT-200", "1874", lots=catalog_lots)

        request = SimpleNamespace(session={"abc_username": "test"})
        result = resolve_item(request, "ITEM-1")

        assert result is not None
        assert result["customer_item_id"] == "ITEM-1"
        assert result["lot_id"] == 100
        assert result["catalog_id"] == 42
        assert result["customer_catalog_id"] == "EVT-200"
        assert result["seller_display_id"] == "1874"
        assert result["lot_position"] == 1  # index 1 in catalog_lots

    @patch("catalog.services.get_catalog_api")
    def test_item_not_found_returns_none(self, mock_api, db):
        mock_api.return_value.lots.list.return_value = _mock_paginated([])

        request = SimpleNamespace(session={"abc_username": "test"})
        result = resolve_item(request, "MISSING")

        assert result is None

    @patch("catalog.services.get_catalog")
    @patch("catalog.services.get_catalog_api")
    def test_lot_position_first(self, mock_api, mock_get_cat, db):
        lot = _mock_lot(50, "FIRST", 10)
        mock_api.return_value.lots.list.return_value = _mock_paginated([lot])
        catalog_lots = [SimpleNamespace(id=50), SimpleNamespace(id=51)]
        mock_get_cat.return_value = _mock_catalog(10, "EVT-10", "S1", lots=catalog_lots)

        request = SimpleNamespace(session={"abc_username": "test"})
        result = resolve_item(request, "FIRST")
        assert result["lot_position"] == 0

    @patch("catalog.services.get_catalog")
    @patch("catalog.services.get_catalog_api")
    def test_lot_position_last(self, mock_api, mock_get_cat, db):
        lot = _mock_lot(53, "LAST", 10)
        mock_api.return_value.lots.list.return_value = _mock_paginated([lot])
        catalog_lots = [SimpleNamespace(id=50), SimpleNamespace(id=51), SimpleNamespace(id=53)]
        mock_get_cat.return_value = _mock_catalog(10, "EVT-10", "S1", lots=catalog_lots)

        request = SimpleNamespace(session={"abc_username": "test"})
        result = resolve_item(request, "LAST")
        assert result["lot_position"] == 2

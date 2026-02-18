from types import SimpleNamespace

import pytest
from unittest.mock import patch

from django.test import Client

from tests.conftest import AUTH_SESSION


def _mock_paginated(**overrides):
    """Build a mock paginated response for sellers list."""
    defaults = {
        "items": [],
        "total_pages": 1,
        "page_number": 1,
        "has_previous_page": False,
        "has_next_page": False,
        "total_items": 0,
    }
    defaults.update(overrides)
    return type("R", (), defaults)()


@pytest.fixture
def client(staff_user):
    c = Client()
    c.force_login(staff_user)
    session = c.session
    session.update(AUTH_SESSION)
    session.save()
    return c


@patch("catalog.views.sellers.services.list_sellers")
class TestDropzoneUI:
    """Integration tests for dropzone presence and JS wiring in base.html."""

    def test_dropzone_element_present(self, mock_sellers, client):
        mock_sellers.return_value = _mock_paginated()
        resp = client.get("/")
        content = resp.content.decode()
        assert 'class="dropzone"' in content
        assert 'id="dropzone"' in content
        assert 'for="dropzone-input"' in content
        assert "Add Catalog" in content

    def test_file_input_with_accept(self, mock_sellers, client):
        mock_sellers.return_value = _mock_paginated()
        resp = client.get("/")
        content = resp.content.decode()
        assert 'id="dropzone-input"' in content
        assert 'accept=".xlsx,.csv,.json"' in content

    def test_toast_container_present(self, mock_sellers, client):
        mock_sellers.return_value = _mock_paginated()
        resp = client.get("/")
        content = resp.content.decode()
        assert 'id="toast-container"' in content
        assert "showToast" in content

    def test_upload_js_wired(self, mock_sellers, client):
        mock_sellers.return_value = _mock_paginated()
        resp = client.get("/")
        content = resp.content.decode()
        assert "/imports/upload/" in content
        assert "dragover" in content
        assert "dragleave" in content
        assert "drop" in content

    def test_multi_file_guard(self, mock_sellers, client):
        mock_sellers.return_value = _mock_paginated()
        resp = client.get("/")
        content = resp.content.decode()
        assert "files[0]" in content

    def test_merge_summary_handling(self, mock_sellers, client):
        mock_sellers.return_value = _mock_paginated()
        resp = client.get("/")
        content = resp.content.decode()
        assert "data.merge" in content
        assert "Added:" in content
        assert "Updated:" in content
        assert "Unchanged:" in content

    def test_pending_toast_session_storage(self, mock_sellers, client):
        mock_sellers.return_value = _mock_paginated()
        resp = client.get("/")
        content = resp.content.decode()
        assert "pendingToast" in content
        assert "sessionStorage.getItem" in content
        assert "sessionStorage.removeItem" in content

    def test_client_side_file_size_check(self, mock_sellers, client):
        mock_sellers.return_value = _mock_paginated()
        resp = client.get("/")
        content = resp.content.decode()
        assert "file.size > 1048576" in content
        assert "File too large" in content

    def test_100pct_failure_detection(self, mock_sellers, client):
        mock_sellers.return_value = _mock_paginated()
        resp = client.get("/")
        content = resp.content.decode()
        assert "data.merge.failed > 0" in content
        assert "all lots encountered errors" in content.lower() or "Merge failed: all" in content

    def test_navbar_search_form(self, mock_sellers, client):
        mock_sellers.return_value = _mock_paginated()
        resp = client.get("/")
        content = resp.content.decode()
        assert 'class="nav-search"' in content
        assert 'name="q"' in content
        assert 'placeholder="Item ID"' in content


class TestDeepLinkHydration:
    """Integration tests for ?seller=&event=&item= deep-link hydration."""

    @patch("catalog.views.sellers.services.get_lots_for_event")
    @patch("catalog.views.sellers.services.get_catalog")
    @patch("catalog.views.sellers.services.find_catalog_by_customer_id")
    @patch("catalog.views.sellers.services.list_catalogs")
    @patch("catalog.views.sellers.services.find_seller_by_display_id")
    @patch("catalog.views.sellers.services.list_sellers")
    def test_item_param_sets_selected_item_id(
        self, mock_sellers, mock_find_seller, mock_list_cats, mock_find_cat, mock_get_cat, mock_get_lots, client
    ):
        mock_sellers.return_value = _mock_paginated()
        mock_find_seller.return_value = SimpleNamespace(id=10)
        mock_list_cats.return_value = _mock_paginated(items=[
            SimpleNamespace(id=42, customer_catalog_id="405438"),
        ])
        mock_find_cat.return_value = 42
        mock_get_cat.return_value = SimpleNamespace(
            id=42,
            customer_catalog_id="405438",
            sellers=[SimpleNamespace(id=10, customer_display_id="1874")],
            lots=[
                SimpleNamespace(id=100, customer_item_id="2100000001"),
                SimpleNamespace(id=101, customer_item_id="2100000000"),
            ],
        )
        mock_get_lots.return_value = [
            SimpleNamespace(
                id=100, customer_item_id="2100000001", lot_number="001",
                initial_data=SimpleNamespace(qty=1, l=10, w=5, h=3, wgt=2, value=None, cpack=None, description=None, notes=None, item_id=None, force_crate=None, noted_conditions=None, do_not_tip=None, commodity_id=None),
                overriden_data=[], image_links=[],
                catalogs=[SimpleNamespace(catalog_id=42, lot_number="001")],
            ),
            SimpleNamespace(
                id=101, customer_item_id="2100000000", lot_number="002",
                initial_data=SimpleNamespace(qty=1, l=10, w=5, h=3, wgt=2, value=None, cpack=None, description=None, notes=None, item_id=None, force_crate=None, noted_conditions=None, do_not_tip=None, commodity_id=None),
                overriden_data=[], image_links=[],
                catalogs=[SimpleNamespace(catalog_id=42, lot_number="002")],
            ),
        ]

        resp = client.get("/?seller=1874&event=405438&item=2100000000")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "lot-active" in content

    @patch("catalog.views.sellers.services.get_lots_for_event")
    @patch("catalog.views.sellers.services.get_catalog")
    @patch("catalog.views.sellers.services.find_catalog_by_customer_id")
    @patch("catalog.views.sellers.services.list_catalogs")
    @patch("catalog.views.sellers.services.find_seller_by_display_id")
    @patch("catalog.views.sellers.services.list_sellers")
    def test_item_param_without_match_no_highlight(
        self, mock_sellers, mock_find_seller, mock_list_cats, mock_find_cat, mock_get_cat, mock_get_lots, client
    ):
        mock_sellers.return_value = _mock_paginated()
        mock_find_seller.return_value = SimpleNamespace(id=10)
        mock_list_cats.return_value = _mock_paginated(items=[
            SimpleNamespace(id=42, customer_catalog_id="405438"),
        ])
        mock_find_cat.return_value = 42
        mock_get_cat.return_value = SimpleNamespace(
            id=42,
            customer_catalog_id="405438",
            sellers=[SimpleNamespace(id=10, customer_display_id="1874")],
            lots=[
                SimpleNamespace(id=100, customer_item_id="2100000001"),
            ],
        )
        mock_get_lots.return_value = [
            SimpleNamespace(
                id=100, customer_item_id="2100000001", lot_number="001",
                initial_data=SimpleNamespace(qty=1, l=10, w=5, h=3, wgt=2, value=None, cpack=None, description=None, notes=None, item_id=None, force_crate=None, noted_conditions=None, do_not_tip=None, commodity_id=None),
                overriden_data=[], image_links=[],
                catalogs=[SimpleNamespace(catalog_id=42, lot_number="001")],
            ),
        ]

        resp = client.get("/?seller=1874&event=405438&item=NONEXISTENT")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "lot-active" not in content

import pytest
from unittest.mock import patch

from django.test import Client

from tests.conftest import AUTH_SESSION


@pytest.fixture
def client(staff_user):
    c = Client()
    c.force_login(staff_user)
    session = c.session
    session.update(AUTH_SESSION)
    session.save()
    return c


class TestSearchItem:
    @patch("catalog.views.imports.services.resolve_item")
    def test_found_redirects_to_deep_link(self, mock_resolve, client):
        mock_resolve.return_value = {
            "customer_item_id": "2100000000",
            "lot_id": 100,
            "catalog_id": 42,
            "customer_catalog_id": "405438",
            "seller_display_id": "1874",
            "lot_position": 3,
        }
        resp = client.get("/search/item/?q=2100000000")
        assert resp.status_code == 302
        assert "seller=1874" in resp.url
        assert "event=405438" in resp.url
        assert "item=2100000000" in resp.url

    @patch("catalog.views.imports.services.resolve_item")
    def test_not_found_redirects_with_toast(self, mock_resolve, client):
        mock_resolve.return_value = None
        resp = client.get("/search/item/?q=INVALID")
        assert resp.status_code == 302
        assert resp.url == "/"
        # Check pending toast in session
        session = client.session
        assert session.get("pending_toast") is not None
        assert "not found" in session["pending_toast"]["msg"].lower()

    def test_empty_query_redirects(self, client):
        resp = client.get("/search/item/")
        assert resp.status_code == 302
        assert resp.url == "/"

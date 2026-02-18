import json

import pytest
from unittest.mock import patch
from types import SimpleNamespace

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


SAMPLE_ENTRY = {
    "customer_item_id": "2100000000",
    "lot_number": "001",
    "catalog_id": 42,
    "customer_catalog_id": "405438",
    "seller_display_id": "1874",
    "operation": "create",
    "add_lot_request": {
        "customerItemId": "2100000000",
        "imageLinks": [],
        "initialData": {"Qty": 1, "L": 10, "W": 5, "H": 3, "Wgt": 2},
        "overridenData": [],
        "catalogs": [{"catalogId": 42, "lotNumber": "001"}],
    },
    "error_message": "Connection timeout",
    "timestamp": "2026-02-17T10:30:00Z",
}


class TestRecoveryDashboard:
    @patch("catalog.views.recovery.services.get_recovery_entries")
    def test_shows_entries_when_present(self, mock_entries, client):
        mock_entries.return_value = [SAMPLE_ENTRY]
        resp = client.get("/imports/recovery/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "2100000000" in content
        assert "001" in content
        assert "Connection timeout" in content

    @patch("catalog.views.recovery.services.get_recovery_entries")
    def test_shows_empty_when_no_entries(self, mock_entries, client):
        mock_entries.return_value = []
        resp = client.get("/imports/recovery/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "No pending recoveries" in content


class TestRecoveryCheck:
    @patch("catalog.views.recovery.services.get_catalog_api")
    def test_found_shows_lot_info(self, mock_api, client):
        lot = SimpleNamespace(
            id=100,
            initial_data=SimpleNamespace(qty=5, l=12, w=10, h=8),
        )
        mock_api.return_value.lots.list.return_value = SimpleNamespace(items=[lot])

        resp = client.post("/imports/recovery/check/2100000000/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Exists on server" in content

    @patch("catalog.views.recovery.services.get_catalog_api")
    def test_missing_shows_not_found(self, mock_api, client):
        mock_api.return_value.lots.list.return_value = SimpleNamespace(items=[])

        resp = client.post("/imports/recovery/check/2100000000/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Not found on server" in content


class TestRecoveryRetry:
    @patch("catalog.views.recovery.services.remove_recovery_entry")
    @patch("catalog.views.recovery.services.get_recovery_entries")
    @patch("catalog.views.recovery.services.create_lot")
    @patch("catalog.views.recovery.services.get_catalog_api")
    def test_retry_success(self, mock_api, mock_create, mock_get_entries, mock_remove, client):
        mock_api.return_value.lots.list.return_value = SimpleNamespace(items=[])  # not existing
        mock_get_entries.side_effect = [
            [SAMPLE_ENTRY],  # first call: get entry
            [],  # second call: check remaining after removal
        ]

        resp = client.post("/imports/recovery/retry/2100000000/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "success" in content.lower() or "Retry successful" in content
        mock_create.assert_called_once()
        mock_remove.assert_called_once()

    @patch("catalog.views.recovery.services.get_recovery_entries")
    @patch("catalog.views.recovery.services.get_catalog_api")
    def test_retry_already_exists_shows_warning(self, mock_api, mock_get_entries, client):
        mock_get_entries.return_value = [SAMPLE_ENTRY]
        existing = SimpleNamespace(id=200)
        mock_api.return_value.lots.list.return_value = SimpleNamespace(items=[existing])

        resp = client.post("/imports/recovery/retry/2100000000/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "already exists" in content.lower() or "warning" in content.lower() or "Force" in content


class TestRecoverySkip:
    @patch("catalog.views.recovery.services.get_recovery_entries")
    @patch("catalog.views.recovery.services.remove_recovery_entry")
    def test_skip_removes_entry(self, mock_remove, mock_get_entries, client):
        mock_get_entries.return_value = [SAMPLE_ENTRY]  # still has entries
        resp = client.post("/imports/recovery/skip/2100000000/")
        assert resp.status_code == 200
        mock_remove.assert_called_once()

    @patch("catalog.views.recovery.services.get_recovery_entries")
    @patch("catalog.views.recovery.services.remove_recovery_entry")
    def test_skip_last_entry_shows_all_recovered(self, mock_remove, mock_get_entries, client):
        mock_get_entries.return_value = []  # empty after removal
        resp = client.post("/imports/recovery/skip/2100000000/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "All items recovered" in content

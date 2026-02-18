import json
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest
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


class TestUploadCatalogNewPath:
    """Contract tests for POST /imports/upload/ — new catalog (US1)."""

    def test_no_file_returns_400(self, client):
        resp = client.post("/imports/upload/")
        assert resp.status_code == 400
        data = json.loads(resp.content)
        assert data["success"] is False
        assert "No file uploaded" in data["error"]

    def test_unsupported_extension_returns_400(self, client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        f = SimpleUploadedFile("test.txt", b"hello", content_type="text/plain")
        resp = client.post("/imports/upload/", {"file": f})
        assert resp.status_code == 400
        data = json.loads(resp.content)
        assert data["success"] is False
        assert ".txt" in data["error"]
        assert ".xlsx" in data["error"]

    @patch("catalog.views.imports.services.find_catalog_by_customer_id", return_value=None)
    @patch("catalog.views.imports.services.bulk_insert")
    @patch("catalog.views.imports.load_file")
    def test_valid_file_new_catalog_returns_success(self, mock_load, mock_bulk, mock_find, client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        mock_catalog = SimpleNamespace(customer_catalog_id="123456")
        mock_bulk_req = SimpleNamespace(catalogs=[mock_catalog])
        mock_load.return_value = (mock_bulk_req, "1 catalog, 5 lots")

        # After bulk insert, find_catalog returns the new ID
        mock_find.side_effect = [None, 42]

        f = SimpleUploadedFile("catalog.xlsx", b"fake", content_type="application/octet-stream")
        resp = client.post("/imports/upload/", {"file": f})
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["success"] is True
        assert "redirect" in data
        mock_bulk.assert_called_once()

    @patch("catalog.views.imports.load_file", side_effect=ValueError("missing column 'Catalog ID'"))
    def test_parse_failure_returns_400(self, mock_load, client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        f = SimpleUploadedFile("bad.xlsx", b"fake", content_type="application/octet-stream")
        resp = client.post("/imports/upload/", {"file": f})
        assert resp.status_code == 400
        data = json.loads(resp.content)
        assert data["success"] is False
        assert "Failed to parse file" in data["error"]

    @patch("catalog.views.imports.load_file")
    def test_empty_file_returns_400(self, mock_load, client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        mock_load.return_value = (SimpleNamespace(catalogs=[]), "empty")
        f = SimpleUploadedFile("empty.xlsx", b"fake", content_type="application/octet-stream")
        resp = client.post("/imports/upload/", {"file": f})
        assert resp.status_code == 400
        data = json.loads(resp.content)
        assert data["success"] is False
        assert "no catalog data" in data["error"]


class TestUploadCatalogMergePath:
    """Contract tests for POST /imports/upload/ — merge path (US2)."""

    @patch("catalog.views.imports.services.merge_catalog")
    @patch("catalog.views.imports.services.find_catalog_by_customer_id", return_value=42)
    @patch("catalog.views.imports.load_file")
    def test_merge_returns_success_with_summary(self, mock_load, mock_find, mock_merge, client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        mock_catalog = SimpleNamespace(customer_catalog_id="123456")
        mock_bulk_req = SimpleNamespace(catalogs=[mock_catalog])
        mock_load.return_value = (mock_bulk_req, "1 catalog, 10 lots")
        mock_merge.return_value = {
            "added": 3, "updated": 2, "unchanged": 5, "failed": 0, "errors": [],
        }

        f = SimpleUploadedFile("catalog.xlsx", b"fake", content_type="application/octet-stream")
        resp = client.post("/imports/upload/", {"file": f})
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["success"] is True
        assert data["merge"]["added"] == 3
        assert data["merge"]["updated"] == 2
        assert data["merge"]["unchanged"] == 5
        assert data["merge"]["failed"] == 0
        assert "redirect" in data
        mock_merge.assert_called_once()
        call_args = mock_merge.call_args[0]
        assert call_args[1] is mock_bulk_req
        assert call_args[2] == 42

    @patch("catalog.views.imports.services.merge_catalog", side_effect=Exception("connection timeout"))
    @patch("catalog.views.imports.services.find_catalog_by_customer_id", return_value=42)
    @patch("catalog.views.imports.load_file")
    def test_merge_failure_returns_500(self, mock_load, mock_find, mock_merge, client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        mock_catalog = SimpleNamespace(customer_catalog_id="123456")
        mock_bulk_req = SimpleNamespace(catalogs=[mock_catalog])
        mock_load.return_value = (mock_bulk_req, "1 catalog")

        f = SimpleUploadedFile("catalog.xlsx", b"fake", content_type="application/octet-stream")
        resp = client.post("/imports/upload/", {"file": f})
        assert resp.status_code == 500
        data = json.loads(resp.content)
        assert data["success"] is False
        assert "Merge failed" in data["error"]

    @patch("catalog.views.imports.services.merge_catalog")
    @patch("catalog.views.imports.services.find_catalog_by_customer_id", return_value=42)
    @patch("catalog.views.imports.load_file")
    def test_merge_with_failures_includes_warnings(self, mock_load, mock_find, mock_merge, client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        mock_catalog = SimpleNamespace(customer_catalog_id="123456")
        mock_bulk_req = SimpleNamespace(catalogs=[mock_catalog])
        mock_load.return_value = (mock_bulk_req, "1 catalog")
        mock_merge.return_value = {
            "added": 2, "updated": 1, "unchanged": 5, "failed": 1,
            "errors": ["Failed to update lot ABC-001: server error"],
        }

        f = SimpleUploadedFile("catalog.xlsx", b"fake", content_type="application/octet-stream")
        resp = client.post("/imports/upload/", {"file": f})
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["success"] is True
        assert data["merge"]["failed"] == 1
        assert len(data["warnings"]) == 1

    @patch("catalog.views.imports.services.merge_catalog")
    @patch("catalog.views.imports.services.find_catalog_by_customer_id", return_value=42)
    @patch("catalog.views.imports.load_file")
    def test_merge_with_failures_includes_recovery_url(self, mock_load, mock_find, mock_merge, client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        mock_catalog = SimpleNamespace(customer_catalog_id="123456")
        mock_bulk_req = SimpleNamespace(catalogs=[mock_catalog])
        mock_load.return_value = (mock_bulk_req, "1 catalog")
        mock_merge.return_value = {
            "added": 2, "updated": 1, "unchanged": 5, "failed": 1,
            "errors": ["server error"],
        }

        f = SimpleUploadedFile("catalog.xlsx", b"fake", content_type="application/octet-stream")
        resp = client.post("/imports/upload/", {"file": f})
        data = json.loads(resp.content)
        assert "recovery_url" in data
        assert "/imports/recovery/" in data["recovery_url"]

    @patch("catalog.views.imports.services.merge_catalog")
    @patch("catalog.views.imports.services.find_catalog_by_customer_id", return_value=42)
    @patch("catalog.views.imports.load_file")
    def test_merge_deep_link_redirect(self, mock_load, mock_find, mock_merge, client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        mock_catalog = SimpleNamespace(customer_catalog_id="123456")
        mock_bulk_req = SimpleNamespace(catalogs=[mock_catalog])
        mock_load.return_value = (mock_bulk_req, "1 catalog")
        mock_merge.return_value = {
            "added": 3, "updated": 0, "unchanged": 0, "failed": 0, "errors": [],
            "seller_display_id": "1874",
            "customer_catalog_id": "123456",
        }

        f = SimpleUploadedFile("catalog.xlsx", b"fake", content_type="application/octet-stream")
        resp = client.post("/imports/upload/", {"file": f})
        data = json.loads(resp.content)
        assert "seller=1874" in data["redirect"]
        assert "event=123456" in data["redirect"]

    @patch("catalog.views.imports.services.get_catalog")
    @patch("catalog.views.imports.services.find_catalog_by_customer_id")
    @patch("catalog.views.imports.services.bulk_insert")
    @patch("catalog.views.imports.load_file")
    def test_new_catalog_deep_link_redirect(self, mock_load, mock_bulk, mock_find, mock_get_cat, client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        mock_catalog = SimpleNamespace(customer_catalog_id="123456")
        mock_bulk_req = SimpleNamespace(catalogs=[mock_catalog])
        mock_load.return_value = (mock_bulk_req, "1 catalog, 5 lots")
        mock_find.side_effect = [None, 42]  # first call: not existing, second: after insert
        mock_get_cat.return_value = SimpleNamespace(
            sellers=[SimpleNamespace(customer_display_id="1874")],
        )

        f = SimpleUploadedFile("catalog.xlsx", b"fake", content_type="application/octet-stream")
        resp = client.post("/imports/upload/", {"file": f})
        data = json.loads(resp.content)
        assert "seller=1874" in data["redirect"]
        assert "event=123456" in data["redirect"]

    def test_oversized_file_returns_400(self, client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        # 1.1 MB file
        f = SimpleUploadedFile("big.xlsx", b"x" * (1048576 + 1), content_type="application/octet-stream")
        resp = client.post("/imports/upload/", {"file": f})
        assert resp.status_code == 400
        data = json.loads(resp.content)
        assert data["success"] is False
        assert "too large" in data["error"].lower()

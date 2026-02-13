import json
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest
from django.test import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile

from catalog.views.imports import upload_catalog
from conftest import AUTH_SESSION

_MOCK_STAFF_USER = SimpleNamespace(is_staff=True, is_authenticated=True, pk=1, id=1)


@pytest.fixture
def factory():
    return RequestFactory()


def _make_post(factory, auth_session, filename, content=b"data", content_type="application/octet-stream"):
    f = SimpleUploadedFile(filename, content, content_type=content_type)
    request = factory.post("/imports/upload/", {"file": f})
    request.session = auth_session
    request.user = _MOCK_STAFF_USER
    return request


class TestUploadCatalogContract:
    def test_no_file_returns_error(self, factory, auth_session):
        request = factory.post("/imports/upload/")
        request.session = auth_session
        request.user = _MOCK_STAFF_USER
        response = upload_catalog(request)
        data = json.loads(response.content)
        assert data["success"] is False
        assert "No file provided" in data["error"]

    def test_unsupported_extension_returns_error(self, factory, auth_session):
        request = _make_post(factory, auth_session, "file.txt")
        response = upload_catalog(request)
        data = json.loads(response.content)
        assert data["success"] is False
        assert "Unsupported file type" in data["error"]

    @patch("catalog.views.imports.services.find_catalog_by_customer_id", return_value=42)
    @patch("catalog.views.imports.services.bulk_insert")
    @patch("catalog.views.imports.load_file")
    def test_valid_file_returns_redirect(self, mock_load, mock_bulk, mock_find, factory, auth_session):
        mock_request = MagicMock()
        mock_request.catalogs = [MagicMock(customer_catalog_id="123")]
        mock_load.return_value = (mock_request, "summary")

        request = _make_post(factory, auth_session, "catalog.xlsx")
        response = upload_catalog(request)
        data = json.loads(response.content)

        assert data["success"] is True
        assert "/events/42/" in data["redirect"]
        mock_bulk.assert_called_once()
        mock_find.assert_called_once_with(request, "123")

    @patch("catalog.views.imports.load_file")
    def test_empty_catalogs_returns_error(self, mock_load, factory, auth_session):
        mock_request = MagicMock()
        mock_request.catalogs = []
        mock_load.return_value = (mock_request, "summary")

        request = _make_post(factory, auth_session, "catalog.xlsx")
        response = upload_catalog(request)
        data = json.loads(response.content)

        assert data["success"] is False
        assert "no catalog data" in data["error"]

    @patch("catalog.views.imports.load_file", side_effect=KeyError("Catalog ID"))
    def test_parse_error_returns_error(self, mock_load, factory, auth_session):
        request = _make_post(factory, auth_session, "bad.csv")
        response = upload_catalog(request)
        data = json.loads(response.content)
        assert data["success"] is False
        assert "Failed to read file" in data["error"]

    @patch("catalog.views.imports.services.bulk_insert", side_effect=Exception("API down"))
    @patch("catalog.views.imports.load_file")
    def test_api_error_returns_error(self, mock_load, mock_bulk, factory, auth_session):
        mock_request = MagicMock()
        mock_request.catalogs = [MagicMock(customer_catalog_id="123")]
        mock_load.return_value = (mock_request, "summary")

        request = _make_post(factory, auth_session, "catalog.xlsx")
        response = upload_catalog(request)
        data = json.loads(response.content)

        assert data["success"] is False
        assert "API error" in data["error"]

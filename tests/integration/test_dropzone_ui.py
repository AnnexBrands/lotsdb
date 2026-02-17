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


@patch("catalog.views.sellers.services.list_sellers")
class TestDropzoneUI:
    """Integration tests for dropzone presence and JS wiring in base.html."""

    def test_dropzone_element_present(self, mock_sellers, client):
        mock_sellers.return_value = type("R", (), {"items": [], "total_pages": 1, "page_number": 1, "has_previous_page": False, "has_next_page": False, "total_items": 0})()
        resp = client.get("/")
        content = resp.content.decode()
        assert 'class="dropzone"' in content
        assert 'id="dropzone"' in content
        assert 'for="dropzone-input"' in content
        assert "Add Catalog" in content

    def test_file_input_with_accept(self, mock_sellers, client):
        mock_sellers.return_value = type("R", (), {"items": [], "total_pages": 1, "page_number": 1, "has_previous_page": False, "has_next_page": False, "total_items": 0})()
        resp = client.get("/")
        content = resp.content.decode()
        assert 'id="dropzone-input"' in content
        assert 'accept=".xlsx,.csv,.json"' in content

    def test_toast_container_present(self, mock_sellers, client):
        mock_sellers.return_value = type("R", (), {"items": [], "total_pages": 1, "page_number": 1, "has_previous_page": False, "has_next_page": False, "total_items": 0})()
        resp = client.get("/")
        content = resp.content.decode()
        assert 'id="toast-container"' in content
        assert "showToast" in content

    def test_upload_js_wired(self, mock_sellers, client):
        mock_sellers.return_value = type("R", (), {"items": [], "total_pages": 1, "page_number": 1, "has_previous_page": False, "has_next_page": False, "total_items": 0})()
        resp = client.get("/")
        content = resp.content.decode()
        assert "/imports/upload/" in content
        assert "dragover" in content
        assert "dragleave" in content
        assert "drop" in content

    def test_multi_file_guard(self, mock_sellers, client):
        mock_sellers.return_value = type("R", (), {"items": [], "total_pages": 1, "page_number": 1, "has_previous_page": False, "has_next_page": False, "total_items": 0})()
        resp = client.get("/")
        content = resp.content.decode()
        assert "files[0]" in content

    def test_merge_summary_handling(self, mock_sellers, client):
        mock_sellers.return_value = type("R", (), {"items": [], "total_pages": 1, "page_number": 1, "has_previous_page": False, "has_next_page": False, "total_items": 0})()
        resp = client.get("/")
        content = resp.content.decode()
        assert "data.merge" in content
        assert "Added:" in content
        assert "Updated:" in content
        assert "Unchanged:" in content

"""Integration tests for the catalog dropzone UI.

Covers acceptance scenarios AS1 (dropzone visible) and AS2 (dragover visual state)
plus toast, upload JS, and multi-file behaviour.
"""

import pytest
from unittest.mock import patch, MagicMock

from django.test import Client


@pytest.fixture
def authenticated_client(auth_session):
    """Django test Client with session auth injected."""
    client = Client()
    client.get("/login/")  # establish session on exempt path
    session = client.session
    for key, value in auth_session.items():
        session[key] = value
    session.save()
    return client


@pytest.fixture
def _mock_sellers():
    """Patch list_sellers so GET / doesn't hit the real API."""
    result = MagicMock()
    result.items = []
    result.total_pages = 0
    result.page_number = 1
    result.has_previous_page = False
    result.has_next_page = False
    result.total_items = 0
    with patch("catalog.services.list_sellers", return_value=result):
        yield


@pytest.mark.django_db
@pytest.mark.usefixtures("_mock_sellers")
class TestDropzoneVisible:
    """AS1: Dropzone element is present and correctly configured on authenticated pages."""

    def test_dropzone_element_present(self, authenticated_client):
        response = authenticated_client.get("/")
        content = response.content.decode()
        assert 'id="dropzone"' in content
        assert "Add Catalog" in content

    def test_file_input_present(self, authenticated_client):
        response = authenticated_client.get("/")
        content = response.content.decode()
        assert 'id="dropzone-input"' in content
        assert 'accept=".xlsx,.csv,.json"' in content


@pytest.mark.django_db
@pytest.mark.usefixtures("_mock_sellers")
class TestDragoverVisualState:
    """AS2: Dragover/dragleave/drop JS event listeners toggle the 'dragover' CSS class."""

    def test_dragover_event_listeners(self, authenticated_client):
        response = authenticated_client.get("/")
        content = response.content.decode()
        assert "addEventListener('dragover'" in content
        assert "addEventListener('dragleave'" in content
        assert "addEventListener('drop'" in content

    def test_dragover_class_toggle(self, authenticated_client):
        response = authenticated_client.get("/")
        content = response.content.decode()
        assert "classList.add('dragover')" in content
        assert "classList.remove('dragover')" in content


@pytest.mark.django_db
@pytest.mark.usefixtures("_mock_sellers")
class TestToast:
    """Toast container and showToast JS function are present."""

    def test_toast_container_present(self, authenticated_client):
        response = authenticated_client.get("/")
        content = response.content.decode()
        assert 'id="toast-container"' in content
        assert 'class="toast-container"' in content

    def test_show_toast_function(self, authenticated_client):
        response = authenticated_client.get("/")
        content = response.content.decode()
        assert "function showToast" in content


@pytest.mark.django_db
@pytest.mark.usefixtures("_mock_sellers")
class TestUploadJS:
    """Upload JavaScript POSTs to the upload endpoint and handles responses."""

    def test_fetch_posts_to_upload_url(self, authenticated_client):
        response = authenticated_client.get("/")
        content = response.content.decode()
        assert "fetch(UPLOAD_URL" in content

    def test_success_redirect(self, authenticated_client):
        response = authenticated_client.get("/")
        content = response.content.decode()
        assert "window.location.href = data.redirect" in content

    def test_error_toast(self, authenticated_client):
        response = authenticated_client.get("/")
        content = response.content.decode()
        assert "showToast(data.error" in content


@pytest.mark.django_db
@pytest.mark.usefixtures("_mock_sellers")
class TestMultiFile:
    """Only the first file in a drop event is processed."""

    def test_processes_first_file_only(self, authenticated_client):
        response = authenticated_client.get("/")
        content = response.content.decode()
        assert "files[0]" in content

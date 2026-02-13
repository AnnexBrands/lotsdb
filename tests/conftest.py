import pytest
from unittest.mock import MagicMock

from django.contrib.auth.models import User


# Shared test constants — derived from spec examples and data-model.md payloads.
AUTH_SESSION = {
    "abc_token": {"access_token": "test", "expires_at": 9999999999},
    "abc_username": "test@example.com",
}


@pytest.fixture
def auth_session():
    """Session dict that passes is_authenticated — derived from spec examples."""
    return AUTH_SESSION.copy()


@pytest.fixture
def sample_bulk_request():
    """MagicMock matching BulkInsertRequest with one catalog — derived from data-model examples."""
    mock = MagicMock()
    mock.catalogs = [MagicMock(customer_catalog_id="123456")]
    return mock


@pytest.fixture
def staff_user(db):
    """Django User with is_staff=True and unusable password."""
    user, _ = User.objects.get_or_create(
        username="test@example.com",
        defaults={"is_staff": True},
    )
    user.set_unusable_password()
    user.save()
    return user


@pytest.fixture
def non_staff_user(db):
    """Django User with is_staff=False and unusable password."""
    user, _ = User.objects.get_or_create(
        username="noaccess@example.com",
        defaults={"is_staff": False},
    )
    user.set_unusable_password()
    user.save()
    return user

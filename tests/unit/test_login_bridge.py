"""Unit tests for the login bridge (services.login → Django User)."""

from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def request_with_session(factory):
    """Create a request with a real Django session (supports cycle_key)."""
    request = factory.post("/login/")
    request.session = SessionStore()
    return request


@pytest.mark.django_db
class TestLoginBridge:

    @patch("catalog.services.ABConnectAPI")
    def test_first_login_creates_django_user(self, mock_abc, request_with_session):
        from catalog.services import login

        login(request_with_session, "newuser@test.com", "pass123")

        user = User.objects.get(username="newuser@test.com")
        assert user.is_staff is True
        assert user.has_usable_password() is False

    @patch("catalog.services.ABConnectAPI")
    def test_repeat_login_retrieves_existing_user(self, mock_abc, request_with_session):
        from catalog.services import login

        User.objects.create_user(username="existing@test.com", is_staff=True)
        login(request_with_session, "existing@test.com", "pass123")

        assert User.objects.filter(username="existing@test.com").count() == 1

    @patch("catalog.services.ABConnectAPI")
    def test_request_user_is_set_after_login(self, mock_abc, request_with_session):
        from catalog.services import login

        login(request_with_session, "bridged@test.com", "pass123")

        # django.contrib.auth.login stores _auth_user_id in session
        assert "_auth_user_id" in request_with_session.session

    @patch("catalog.services.ABConnectAPI", side_effect=Exception("Bad creds"))
    def test_abc_failure_does_not_create_user(self, mock_abc, request_with_session):
        from catalog.services import login

        with pytest.raises(Exception, match="Bad creds"):
            login(request_with_session, "fail@test.com", "badpass")

        assert not User.objects.filter(username="fail@test.com").exists()

    @patch("catalog.services.ABConnectAPI")
    def test_session_has_abc_username(self, mock_abc, request_with_session):
        from catalog.services import login

        login(request_with_session, "sessionuser@test.com", "pass123")

        assert request_with_session.session["abc_username"] == "sessionuser@test.com"

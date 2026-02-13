"""Integration tests for LoginRequiredMiddleware authorization enforcement."""

from unittest.mock import patch, MagicMock

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.contrib.sessions.backends.db import SessionStore

from catalog.middleware import LoginRequiredMiddleware


def _dummy_view(request):
    """Dummy view that returns 200 — used as get_response for middleware."""
    from django.http import HttpResponse
    return HttpResponse("OK", status=200)


@pytest.fixture
def middleware():
    return LoginRequiredMiddleware(_dummy_view)


@pytest.fixture
def factory():
    return RequestFactory()


def _make_request(factory, path="/", session=None, user=None):
    """Build a GET request with real session and optional user."""
    request = factory.get(path)
    request.session = session if session is not None else SessionStore()
    if user:
        request.user = user
    else:
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()
    return request


@pytest.mark.django_db
class TestStaffPassesThrough:
    """Staff users reach the view unchanged."""

    def test_staff_user_gets_200(self, middleware, factory):
        user = User.objects.create_user(username="staff@test.com", is_staff=True)
        session = SessionStore()
        session["abc_token"] = {"access_token": "t", "expires_at": 9999999999}
        session["abc_username"] = "staff@test.com"
        session.save()

        request = _make_request(factory, "/sellers/", session=session, user=user)
        response = middleware(request)

        assert response.status_code == 200
        assert response.content == b"OK"


@pytest.mark.django_db
class TestUnauthenticatedRedirectsToLogin:
    """Unauthenticated requests redirect to /login/."""

    def test_no_session_redirects_to_login(self, middleware, factory):
        request = _make_request(factory, "/sellers/")
        response = middleware(request)

        assert response.status_code == 302
        assert response.url == "/login/"

    def test_empty_session_redirects_to_login(self, middleware, factory):
        request = _make_request(factory, "/sellers/", session=SessionStore())
        response = middleware(request)

        assert response.status_code == 302
        assert response.url == "/login/"


@pytest.mark.django_db
class TestLegacySessionRebridge:
    """Legacy sessions (abc_token but no Django User) get re-bridged."""

    def test_rebridge_creates_user_and_continues(self, middleware, factory):
        session = SessionStore()
        session["abc_token"] = {"access_token": "t", "expires_at": 9999999999}
        session["abc_username"] = "legacy@test.com"
        session.save()

        request = _make_request(factory, "/sellers/", session=session)
        response = middleware(request)

        # Should have created the user and passed through
        assert User.objects.filter(username="legacy@test.com").exists()
        user = User.objects.get(username="legacy@test.com")
        assert user.is_staff is True
        assert response.status_code == 200

    def test_rebridge_without_abc_username_flushes_session(self, middleware, factory):
        session = SessionStore()
        session["abc_token"] = {"access_token": "t", "expires_at": 9999999999}
        # No abc_username
        session.save()

        request = _make_request(factory, "/sellers/", session=session)
        response = middleware(request)

        assert response.status_code == 302
        assert response.url == "/login/"


@pytest.mark.django_db
class TestNonStaffRedirectsToNoAccess:
    """Non-staff users redirect to /no-access/."""

    def test_non_staff_redirected(self, middleware, factory):
        user = User.objects.create_user(username="noaccess@test.com", is_staff=False)
        session = SessionStore()
        session["abc_token"] = {"access_token": "t", "expires_at": 9999999999}
        session["abc_username"] = "noaccess@test.com"
        session.save()

        request = _make_request(factory, "/sellers/", session=session, user=user)
        response = middleware(request)

        assert response.status_code == 302
        assert response.url == "/no-access/"

    def test_non_staff_panels_endpoint_redirected(self, middleware, factory):
        user = User.objects.create_user(username="noaccess2@test.com", is_staff=False)
        session = SessionStore()
        session["abc_token"] = {"access_token": "t", "expires_at": 9999999999}
        session["abc_username"] = "noaccess2@test.com"
        session.save()

        request = _make_request(factory, "/panels/sellers/", session=session, user=user)
        response = middleware(request)

        assert response.status_code == 302
        assert response.url == "/no-access/"


@pytest.mark.django_db
class TestNoAccessView:
    """Tests for the /no-access/ endpoint."""

    def test_no_access_returns_403_with_message(self, factory):
        from catalog.views.auth import no_access

        request = factory.get("/no-access/")
        response = no_access(request)

        assert response.status_code == 403
        content = response.content.decode()
        assert "You do not have access to this application" in content
        assert "Contact an administrator" in content

    def test_no_access_has_logout_button(self, factory):
        from catalog.views.auth import no_access

        request = factory.get("/no-access/")
        response = no_access(request)

        content = response.content.decode()
        assert "/logout/" in content
        assert "Logout" in content


@pytest.mark.django_db
class TestExemptPaths:
    """Exempt paths bypass all checks."""

    def test_login_page_exempt(self, middleware, factory):
        request = _make_request(factory, "/login/")
        response = middleware(request)
        assert response.status_code == 200

    def test_static_exempt(self, middleware, factory):
        request = _make_request(factory, "/static/catalog/styles.css")
        response = middleware(request)
        assert response.status_code == 200

    def test_no_access_page_exempt(self, middleware, factory):
        request = _make_request(factory, "/no-access/")
        response = middleware(request)
        assert response.status_code == 200

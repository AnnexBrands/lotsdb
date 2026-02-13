import logging

from django.contrib.auth import login as django_login
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from catalog.authorization import is_authorized
from catalog.services import is_authenticated

logger = logging.getLogger(__name__)

EXEMPT_PATHS = ("/login/", "/static/", "/no-access/")


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(p) for p in EXEMPT_PATHS):
            return self.get_response(request)

        if not is_authenticated(request):
            return HttpResponseRedirect(reverse("login"))

        # Re-bridge legacy sessions: abc_token exists but no Django User in session
        if not request.user.is_authenticated:
            abc_username = request.session.get("abc_username")
            if abc_username:
                user, created = User.objects.get_or_create(
                    username=abc_username,
                    defaults={"is_staff": True},
                )
                if created:
                    user.set_unusable_password()
                    user.save()
                django_login(
                    request, user,
                    backend="django.contrib.auth.backends.ModelBackend",
                )
            else:
                # No abc_username — can't re-bridge, force re-login
                request.session.flush()
                return HttpResponseRedirect(reverse("login"))

        # Authorization check
        if not is_authorized(request.user):
            return HttpResponseRedirect(reverse("no_access"))

        return self.get_response(request)


class CatalogAPIErrorMiddleware:
    """Catch unhandled API errors and render a user-friendly error page."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        from requests.exceptions import RequestException

        if isinstance(exception, RequestException):
            logger.exception("Catalog API request failed")
            return render(request, "catalog/error.html", {
                "message": f"Unable to reach the Catalog API: {str(exception)}",
            }, status=502)
        return None

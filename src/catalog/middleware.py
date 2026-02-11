import logging

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from catalog.services import is_authenticated

logger = logging.getLogger(__name__)

EXEMPT_PATHS = ("/login/", "/static/")


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not any(request.path.startswith(p) for p in EXEMPT_PATHS):
            if not is_authenticated(request):
                return HttpResponseRedirect(reverse("login"))
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
                "message": "Unable to reach the Catalog API. Please try again later.",
            }, status=502)
        return None

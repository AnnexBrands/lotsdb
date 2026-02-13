from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from catalog import services

import logging

logger = logging.getLogger(__name__)


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        if not username or not password:
            return render(
                request,
                "catalog/auth/login.html",
                {"error": "Username and password are required."},
            )
        try:
            services.login(request, username, password)
            return HttpResponseRedirect(reverse("seller_list"))
        except Exception as e:
            logger.error(f"Login failed for user {username}: {e}")
            return render(
                request,
                "catalog/auth/login.html",
                {"error": "Invalid credentials. Please try again."},
            )
    return render(request, "catalog/auth/login.html")


def logout_view(request):
    request.session.flush()
    return HttpResponseRedirect(reverse("login"))


def no_access(request):
    """Render the 'no access' page for unauthorized users."""
    return render(request, "catalog/auth/no_access.html", status=403)

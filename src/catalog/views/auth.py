from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from catalog import services


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        if not username or not password:
            return render(
                request, "catalog/auth/login.html", {"error": "Username and password are required."}
            )
        try:
            services.login(request, username, password)
            return HttpResponseRedirect(reverse("seller_list"))
        except Exception:
            return render(
                request, "catalog/auth/login.html", {"error": "Invalid credentials. Please try again."}
            )
    return render(request, "catalog/auth/login.html")


def logout_view(request):
    request.session.flush()
    return HttpResponseRedirect(reverse("login"))

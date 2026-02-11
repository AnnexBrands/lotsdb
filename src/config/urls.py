from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("", include("catalog.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL)

from django.urls import path

from catalog.views.auth import login_view, logout_view
from catalog.views.sellers import seller_list, seller_detail
from catalog.views.events import event_detail
from catalog.views.lots import lot_detail, override_form
from catalog.views.search import search_lots_view
from catalog.views.imports import import_list, import_file, upload_catalog

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("", seller_list, name="seller_list"),
    path("sellers/<int:seller_id>/", seller_detail, name="seller_detail"),
    path("events/<int:event_id>/", event_detail, name="event_detail"),
    path("lots/<int:lot_id>/", lot_detail, name="lot_detail"),
    path("lots/<int:lot_id>/override/", override_form, name="override_form"),
    path("search/", search_lots_view, name="search"),
    path("imports/", import_list, name="import_list"),
    path("imports/run/", import_file, name="import_file"),
    path("imports/upload/", upload_catalog, name="upload_catalog"),
]

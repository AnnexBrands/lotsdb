from django.urls import path

from catalog.views.auth import login_view, logout_view
from catalog.views.sellers import seller_list, seller_detail
from catalog.views.events import event_detail
from catalog.views.lots import lot_detail, override_form
from catalog.views.search import search_lots_view
from catalog.views.imports import import_list, import_file, upload_catalog
from catalog.views.panels import sellers_panel, seller_events_panel, event_lots_panel

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("", seller_list, name="home"),
    path("sellers/", seller_list, name="seller_list"),
    path("panels/sellers/", sellers_panel, name="sellers_panel"),
    path("panels/sellers/<int:seller_id>/events/", seller_events_panel, name="seller_events_panel"),
    path("panels/events/<int:event_id>/lots/", event_lots_panel, name="event_lots_panel"),
    path("sellers/<int:seller_id>/", seller_detail, name="seller_detail"),
    path("events/<int:event_id>/", event_detail, name="event_detail"),
    path("lots/<int:lot_id>/", lot_detail, name="lot_detail"),
    path("lots/<int:lot_id>/override/", override_form, name="override_form"),
    path("search/", search_lots_view, name="search"),
    path("imports/", import_list, name="import_list"),
    path("imports/run/", import_file, name="import_file"),
    path("imports/upload/", upload_catalog, name="upload_catalog"),
]

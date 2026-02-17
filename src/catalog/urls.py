from django.urls import path

from catalog.views.auth import login_view, logout_view, no_access
from catalog.views.imports import upload_catalog, search_item
from catalog.views.sellers import seller_list
from catalog.views.panels import sellers_panel, seller_events_panel, event_lots_panel, lot_override_panel, lot_detail_panel, lot_text_save
from catalog.views.recovery import recovery_dashboard, recovery_check, recovery_retry, recovery_skip

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("no-access/", no_access, name="no_access"),
    path("", seller_list, name="home"),
    path("panels/sellers/", sellers_panel, name="sellers_panel"),
    path("panels/sellers/<int:seller_id>/events/", seller_events_panel, name="seller_events_panel"),
    path("panels/events/<int:event_id>/lots/", event_lots_panel, name="event_lots_panel"),
    path("panels/lots/<int:lot_id>/detail/", lot_detail_panel, name="lot_detail_panel"),
    path("panels/lots/<int:lot_id>/override/", lot_override_panel, name="lot_override_panel"),
    path("panels/lots/<int:lot_id>/text-save/", lot_text_save, name="lot_text_save"),
    path("imports/upload/", upload_catalog, name="upload_catalog"),
    path("search/item/", search_item, name="search_item"),
    path("imports/recovery/", recovery_dashboard, name="recovery_dashboard"),
    path("imports/recovery/check/<str:customer_item_id>/", recovery_check, name="recovery_check"),
    path("imports/recovery/retry/<str:customer_item_id>/", recovery_retry, name="recovery_retry"),
    path("imports/recovery/skip/<str:customer_item_id>/", recovery_skip, name="recovery_skip"),
]

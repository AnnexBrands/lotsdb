import logging

from django.shortcuts import render

from ABConnect.exceptions import ABConnectError
from catalog import services

logger = logging.getLogger(__name__)


def sellers_panel(request):
    """Return HTML fragment: seller list for Left1 panel."""
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 50))

    try:
        result = services.list_sellers(request, page=page, page_size=page_size)
    except ABConnectError:
        logger.exception("Failed to load sellers")
        return render(request, "catalog/partials/panel_error.html", {
            "error_message": "Could not load sellers",
            "retry_url": "/panels/sellers/",
            "retry_target": "#panel-left1-content",
        })

    return render(request, "catalog/partials/seller_list_panel.html", {
        "sellers": result.items,
        "paginated": result,
    })


def seller_events_panel(request, seller_id):
    """Return HTML fragment: events list for Left2 panel + OOB clear of Main panel."""
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 50))

    try:
        seller = services.get_seller(request, seller_id)
        result = services.list_catalogs(request, page=page, page_size=page_size, seller_id=seller_id)
    except ABConnectError:
        logger.exception("Failed to load events for seller %s", seller_id)
        return render(request, "catalog/partials/panel_error.html", {
            "error_message": "Could not load events",
            "retry_url": f"/panels/sellers/{seller_id}/events/",
            "retry_target": "#panel-left2-content",
        })

    return render(request, "catalog/partials/events_panel.html", {
        "seller": seller,
        "events": result.items,
        "paginated": result,
        "seller_id": seller_id,
        "pagination_url": f"/panels/sellers/{seller_id}/events/",
    })


def event_lots_panel(request, event_id):
    """Return HTML fragment: lots cards for Main panel."""
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 50))

    try:
        event = services.get_catalog(request, event_id)
        result = services.list_lots_by_catalog(
            request, event.customer_catalog_id, page=page, page_size=page_size,
        )
    except ABConnectError:
        logger.exception("Failed to load lots for event %s", event_id)
        return render(request, "catalog/partials/panel_error.html", {
            "error_message": "Could not load lots",
            "retry_url": f"/panels/events/{event_id}/lots/",
            "retry_target": "#panel-main-content",
        })

    return render(request, "catalog/partials/lots_panel.html", {
        "event": event,
        "lots": result.items,
        "paginated": result,
        "event_id": event_id,
        "pagination_url": f"/panels/events/{event_id}/lots/",
    })

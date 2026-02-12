import logging

from django.shortcuts import render

from ABConnect.exceptions import ABConnectError
from catalog import services

logger = logging.getLogger(__name__)


def _parse_page_params(request, default_page_size=50):
    """Parse and clamp pagination query params. Never raises on bad input."""
    try:
        page = max(1, int(request.GET.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = max(1, min(200, int(request.GET.get("page_size", default_page_size))))
    except (ValueError, TypeError):
        page_size = default_page_size
    return page, page_size


def _parse_int_or_none(value):
    """Parse a string to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def sellers_panel(request):
    """Return HTML fragment: seller list for Left1 panel."""
    page, page_size = _parse_page_params(request)
    selected_seller_id = _parse_int_or_none(request.GET.get("selected"))
    filter_name = request.GET.get("name", "").strip()

    filters = {}
    if filter_name:
        filters["Name"] = filter_name

    try:
        result = services.list_sellers(request, page=page, page_size=page_size, **filters)
    except ABConnectError:
        logger.exception("Failed to load sellers")
        return render(request, "catalog/partials/panel_error.html", {
            "error_message": "Could not load sellers",
            "retry_url": "/panels/sellers/",
            "retry_target": "#panel-left1-content",
        })

    extra_params = {}
    if selected_seller_id:
        extra_params["selected"] = selected_seller_id

    return render(request, "catalog/partials/seller_list_panel.html", {
        "sellers": result.items,
        "paginated": result,
        "selected_seller_id": selected_seller_id,
        "pagination_extra_params": extra_params,
        "filter_name": filter_name,
    })


def seller_events_panel(request, seller_id):
    """Return HTML fragment: events list for Left2 panel + OOB seller list with selection."""
    page, page_size = _parse_page_params(request)
    filter_title = request.GET.get("title", "").strip()

    filters = {}
    if filter_title:
        filters["Title"] = filter_title

    try:
        seller = services.get_seller(request, seller_id)
        result = services.list_catalogs(request, page=page, page_size=page_size, seller_id=seller_id, **filters)
        sellers_result = services.list_sellers(request, page=1, page_size=50)
    except ABConnectError:
        logger.exception("Failed to load events for seller %s", seller_id)
        return render(request, "catalog/partials/panel_error.html", {
            "error_message": "Could not load events",
            "retry_url": f"/panels/sellers/{seller_id}/events/",
            "retry_target": "#panel-left2-content",
        })

    response = render(request, "catalog/partials/events_panel.html", {
        "seller": seller,
        "events": result.items,
        "paginated": result,
        "seller_id": seller_id,
        "pagination_url": f"/panels/sellers/{seller_id}/events/",
        "selected_seller_id": seller_id,
        "selected_seller_name": seller.name,
        "oob_sellers": sellers_result.items,
        "oob_sellers_paginated": sellers_result,
        "pagination_extra_params": {"selected": seller_id},
        "filter_title": filter_title,
    })
    response["HX-Push-Url"] = f"/?seller={seller.customer_display_id}"
    return response


def _paginate_locally(items, page, page_size):
    """Paginate an in-memory list and return (page_items, paginated_metadata)."""
    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start:start + page_size]
    total_pages = max(1, (total + page_size - 1) // page_size)
    paginated = {
        "page_number": page,
        "total_pages": total_pages,
        "total_items": total,
        "has_previous_page": page > 1,
        "has_next_page": page < total_pages,
    }
    return page_items, paginated


def event_lots_panel(request, event_id):
    """Return HTML fragment: lots cards for Main panel + OOB events list with selection."""
    page, page_size = _parse_page_params(request)

    try:
        event = services.get_catalog(request, event_id)
        # Use embedded lots from the expanded catalog response (reliable)
        # instead of list_lots_by_catalog which is unreliable for event scoping.
        page_lots, paginated = _paginate_locally(event.lots or [], page, page_size)
        # Resolve seller from event data for OOB re-render and URL push
        seller_id = event.sellers[0].id if event.sellers else None
        if seller_id:
            events_result = services.list_catalogs(request, page=1, page_size=50, seller_id=seller_id)
        else:
            events_result = None
    except ABConnectError:
        logger.exception("Failed to load lots for event %s", event_id)
        return render(request, "catalog/partials/panel_error.html", {
            "error_message": "Could not load lots",
            "retry_url": f"/panels/events/{event_id}/lots/",
            "retry_target": "#panel-main-content",
        })

    context = {
        "event": event,
        "lots": page_lots,
        "paginated": paginated,
        "event_id": event_id,
        "seller_id": seller_id,
        "pagination_url": f"/panels/events/{event_id}/lots/",
        "selected_event_id": event_id,
    }
    if events_result:
        context["oob_events"] = events_result.items
        context["oob_events_paginated"] = events_result
        context["oob_seller_id"] = seller_id
        context["oob_events_pagination_url"] = f"/panels/sellers/{seller_id}/events/"
        context["selected_event_title"] = event.title

    response = render(request, "catalog/partials/lots_panel.html", context)
    if seller_id:
        seller_display_id = event.sellers[0].customer_display_id
        response["HX-Push-Url"] = f"/?seller={seller_display_id}&event={event.customer_catalog_id}"
    return response

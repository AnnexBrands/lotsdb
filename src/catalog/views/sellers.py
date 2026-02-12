import logging

from django.shortcuts import render

from ABConnect.exceptions import ABConnectError
from catalog import services

logger = logging.getLogger(__name__)


def _parse_int_or_none(value):
    """Parse a string to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_page_params(request, default_page_size=25):
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


def seller_list(request):
    page, page_size = _parse_page_params(request)
    name = request.GET.get("name", "").strip()
    is_active = request.GET.get("is_active", "")

    filters = {}
    if name:
        filters["Name"] = name
    if is_active in ("true", "false"):
        filters["IsActive"] = is_active == "true"

    result = services.list_sellers(request, page=page, page_size=page_size, **filters)

    filter_fields = [
        {"name": "name", "label": "Name", "type": "text", "value": name, "placeholder": "Filter by name..."},
        {
            "name": "is_active",
            "label": "Status",
            "type": "select",
            "value": is_active,
            "options": [("true", "Active"), ("false", "Inactive")],
        },
    ]

    preserved_params = {}
    if name:
        preserved_params["name"] = name
    if is_active:
        preserved_params["is_active"] = is_active

    # Home page (/) renders the SPA shell; /sellers/ renders the full-page list
    if request.path == "/":
        context = {
            "sellers": result.items,
            "paginated": result,
        }

        # URL hydration: read ?seller=<display_id>&event=<catalog_id> for deep-link support
        seller_display_id = request.GET.get("seller", "").strip()
        event_catalog_id = request.GET.get("event", "").strip()

        if seller_display_id:
            try:
                seller = services.find_seller_by_display_id(request, seller_display_id)
                if seller:
                    selected_seller_id = seller.id
                    context["selected_seller_id"] = selected_seller_id
                    events_result = services.list_catalogs(
                        request, page=1, page_size=50, seller_id=selected_seller_id,
                    )
                    context["hydrate_seller"] = seller
                    context["hydrate_events"] = events_result.items
                    context["hydrate_events_paginated"] = events_result
                    context["hydrate_events_pagination_url"] = f"/panels/sellers/{selected_seller_id}/events/"

                    if event_catalog_id:
                        try:
                            event_internal_id = services.find_catalog_by_customer_id(request, event_catalog_id)
                            if event_internal_id:
                                event = services.get_catalog(request, event_internal_id)
                                # Validate event belongs to the selected seller
                                event_seller_ids = [s.id for s in (event.sellers or [])]
                                if selected_seller_id in event_seller_ids:
                                    context["selected_event_id"] = event_internal_id
                                    # Use embedded lots from expanded catalog (reliable)
                                    # instead of list_lots_by_catalog endpoint.
                                    all_lots = event.lots or []
                                    page_lots = all_lots[:50]
                                    total = len(all_lots)
                                    total_pages = max(1, (total + 49) // 50)
                                    context["hydrate_event"] = event
                                    context["hydrate_lots"] = page_lots
                                    context["hydrate_lots_paginated"] = {
                                        "page_number": 1,
                                        "total_pages": total_pages,
                                        "total_items": total,
                                        "has_previous_page": False,
                                        "has_next_page": 1 < total_pages,
                                    }
                                    context["hydrate_lots_pagination_url"] = f"/panels/events/{event_internal_id}/lots/"
                        except ABConnectError:
                            logger.exception("Failed to hydrate event %s", event_catalog_id)
            except ABConnectError:
                logger.exception("Failed to hydrate seller %s", seller_display_id)

        return render(request, "catalog/shell.html", context)

    return render(request, "catalog/sellers/list.html", {
        "sellers": result.items,
        "paginated": result,
        "filter_fields": filter_fields,
        "preserved_params": preserved_params,
    })


def seller_detail(request, seller_id):
    seller = services.get_seller(request, seller_id)

    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 25))
    title = request.GET.get("title", "").strip()
    agent = request.GET.get("agent", "").strip()
    is_completed = request.GET.get("is_completed", "")

    filters = {}
    if title:
        filters["Title"] = title
    if agent:
        filters["Agent"] = agent
    if is_completed in ("true", "false"):
        filters["IsCompleted"] = is_completed == "true"

    result = services.list_catalogs(
        request, page=page, page_size=page_size, seller_id=seller_id, **filters
    )

    filter_fields = [
        {"name": "title", "label": "Title", "type": "text", "value": title, "placeholder": "Filter by title..."},
        {"name": "agent", "label": "Agent", "type": "text", "value": agent, "placeholder": "Filter by agent..."},
        {
            "name": "is_completed",
            "label": "Status",
            "type": "select",
            "value": is_completed,
            "options": [("true", "Completed"), ("false", "Active")],
        },
    ]

    preserved_params = {}
    if title:
        preserved_params["title"] = title
    if agent:
        preserved_params["agent"] = agent
    if is_completed:
        preserved_params["is_completed"] = is_completed

    return render(request, "catalog/sellers/detail.html", {
        "seller": seller,
        "events": result.items,
        "paginated": result,
        "filter_fields": filter_fields,
        "preserved_params": preserved_params,
    })

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


def seller_list(request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 25))
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

        # URL hydration: read ?seller=<id>&event=<id> for deep-link support
        selected_seller_id = _parse_int_or_none(request.GET.get("seller"))
        selected_event_id = _parse_int_or_none(request.GET.get("event"))

        if selected_seller_id:
            context["selected_seller_id"] = selected_seller_id
            try:
                seller = services.get_seller(request, selected_seller_id)
                events_result = services.list_catalogs(
                    request, page=1, page_size=50, seller_id=selected_seller_id,
                )
                context["hydrate_seller"] = seller
                context["hydrate_events"] = events_result.items
                context["hydrate_events_paginated"] = events_result

                if selected_event_id:
                    context["selected_event_id"] = selected_event_id
                    try:
                        event = services.get_catalog(request, selected_event_id)
                        lots_result = services.list_lots_by_catalog(
                            request, event.customer_catalog_id, page=1, page_size=50,
                        )
                        context["hydrate_event"] = event
                        context["hydrate_lots"] = lots_result.items
                        context["hydrate_lots_paginated"] = lots_result
                    except ABConnectError:
                        logger.exception("Failed to hydrate event %s", selected_event_id)
            except ABConnectError:
                logger.exception("Failed to hydrate seller %s", selected_seller_id)

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

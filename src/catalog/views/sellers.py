import logging

from django.shortcuts import render

from ABConnect.exceptions import ABConnectError
from catalog import services
from catalog.views.panels import build_lot_table_rows

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
    """Render the SPA shell (always — only served at /)."""
    page, page_size = _parse_page_params(request)

    result = services.list_sellers(request, page=page, page_size=page_size)

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
                                # Paginate embedded lots and fetch full LotDto
                                all_lot_refs = event.lots or []
                                page_lot_refs = all_lot_refs[:25]
                                total = len(all_lot_refs)
                                total_pages = max(1, (total + 24) // 25)
                                lot_ids = [ref.id for ref in page_lot_refs]
                                full_lots = services.get_lots_for_event(request, lot_ids)
                                lot_rows = build_lot_table_rows(full_lots)
                                context["hydrate_event"] = event
                                context["hydrate_lots"] = page_lot_refs
                                context["hydrate_lot_rows"] = lot_rows
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

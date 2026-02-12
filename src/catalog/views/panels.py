import json
import logging

from django.http import HttpResponse
from django.shortcuts import render

from ABConnect.exceptions import ABConnectError
from catalog import services
from catalog.forms import OverrideForm

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


_LOT_TABLE_FIELDS = [
    ("description", False),
    ("notes", False),
    ("qty", False),
    ("l", False),
    ("w", False),
    ("h", False),
    ("wgt", False),
    ("cpack", False),
    ("force_crate", True),
    ("do_not_tip", True),
]


def build_lot_table_rows(lots):
    """Build LotTableRow dicts with per-field override comparison."""
    rows = []
    for lot in lots:
        initial = lot.initial_data
        override = lot.overriden_data[0] if lot.overriden_data else None

        fields = {}
        for attr, is_flag in _LOT_TABLE_FIELDS:
            init_val = getattr(initial, attr, None) if initial else None
            over_val = getattr(override, attr, None) if override else None
            changed = override is not None and over_val != init_val
            fields[attr] = {
                "value": over_val if override and over_val is not None else init_val,
                "changed": changed,
                "original": init_val,
            }

        lot_number = ""
        if lot.catalogs:
            lot_number = getattr(lot.catalogs[0], "lot_number", "")

        rows.append({
            "lot": lot,
            "lot_number": lot_number,
            "fields": fields,
        })
    return rows


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
    """Return HTML fragment: lots table for Main panel + OOB events list with selection."""
    page, page_size = _parse_page_params(request, default_page_size=25)

    try:
        event = services.get_catalog(request, event_id)
        # Paginate embedded lots (LotCatalogInformationDto: id + lot_number only)
        page_lot_refs, paginated = _paginate_locally(event.lots or [], page, page_size)
        # Fetch full LotDto for each lot in the page
        lot_ids = [ref.id for ref in page_lot_refs]
        full_lots = services.get_lots_for_event(request, lot_ids)
        lot_rows = build_lot_table_rows(full_lots)
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
        "lots": page_lot_refs,
        "lot_rows": lot_rows,
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


_LOT_DETAIL_FIELDS = [
    ("Quantity", "qty", False),
    ("Length", "l", False),
    ("Width", "w", False),
    ("Height", "h", False),
    ("Weight", "wgt", False),
    ("Value", "value", False),
    ("Case/Pack", "cpack", False),
    ("Description", "description", False),
    ("Notes", "notes", False),
    ("Conditions", "noted_conditions", False),
    ("Commodity ID", "commodity_id", False),
    ("Force Crate", "force_crate", True),
    ("Do Not Tip", "do_not_tip", True),
]


def _build_detail_rows(lot):
    """Build field rows for the lot detail modal (all 13 fields)."""
    initial = lot.initial_data
    override = lot.overriden_data[0] if lot.overriden_data else None
    rows = []
    for label, attr, is_flag in _LOT_DETAIL_FIELDS:
        init_val = getattr(initial, attr, None) if initial else None
        over_val = getattr(override, attr, None) if override else None
        changed = override is not None and over_val != init_val
        rows.append({
            "label": label,
            "attr": attr,
            "initial": init_val,
            "override": over_val,
            "changed": changed,
            "is_flag": is_flag,
        })
    return rows, override is not None


def lot_detail_panel(request, lot_id):
    """Return HTML fragment for the lot detail/edit modal."""
    try:
        lot = services.get_lot(request, lot_id)
    except ABConnectError:
        logger.exception("Failed to load lot %s", lot_id)
        return render(request, "catalog/partials/panel_error.html", {
            "error_message": "Could not load lot details",
            "retry_url": f"/panels/lots/{lot_id}/detail/",
            "retry_target": "#lot-modal-body",
        })

    if request.method == "POST":
        form = OverrideForm(request.POST)
        if form.is_valid():
            override_data = {k: v for k, v in form.cleaned_data.items() if v is not None}
            try:
                services.save_lot_override(request, lot_id, override_data)
                lot = services.get_lot(request, lot_id)
                lot_rows = build_lot_table_rows([lot])
                oob_row = render(request, "catalog/partials/lots_table_row.html", {
                    "row": lot_rows[0],
                }).content.decode()
                # Wrap with OOB swap attribute
                oob_html = oob_row.replace(
                    f'<tr id="lot-row-{lot_id}"',
                    f'<tr id="lot-row-{lot_id}" hx-swap-oob="outerHTML"',
                    1,
                )
                response = HttpResponse(oob_html, content_type="text/html")
                response["HX-Trigger"] = json.dumps({
                    "closeModal": True,
                    "showToast": {"message": "Override saved", "type": "success"},
                })
                return response
            except ABConnectError:
                logger.exception("Failed to save override for lot %s", lot_id)
                response = render(request, "catalog/partials/panel_error.html", {
                    "error_message": "Could not save override",
                    "retry_url": f"/panels/lots/{lot_id}/detail/?edit=1",
                    "retry_target": "#lot-modal-body",
                })
                response["HX-Trigger"] = json.dumps({
                    "showToast": {"message": "Could not save override", "type": "error"},
                })
                return response
        else:
            return render(request, "catalog/partials/lot_edit_modal.html", {
                "lot": lot,
                "form": form,
            })

    # GET request
    if request.GET.get("edit") == "1":
        override = lot.overriden_data[0] if lot.overriden_data else None
        source = override or lot.initial_data
        initial_data = {}
        if source:
            for field_name in OverrideForm.base_fields:
                val = getattr(source, field_name, None)
                if val is not None:
                    initial_data[field_name] = val
        form = OverrideForm(initial=initial_data)
        return render(request, "catalog/partials/lot_edit_modal.html", {
            "lot": lot,
            "form": form,
        })

    rows, has_override = _build_detail_rows(lot)
    return render(request, "catalog/partials/lot_detail_modal.html", {
        "lot": lot,
        "has_override": has_override,
        "rows": rows,
    })


def lot_override_panel(request, lot_id):
    """Handle POST to save inline override for a single lot row, return updated <tr>."""
    if request.method != "POST":
        return render(request, "catalog/partials/panel_error.html", {
            "error_message": "Method not allowed",
            "retry_url": "/",
            "retry_target": "#panel-main-content",
        }, status=405)

    override_data = {}
    for field in ("qty", "l", "w", "h", "wgt"):
        val = request.POST.get(field, "").strip()
        if val:
            try:
                override_data[field] = float(val) if "." in val else int(val)
            except (ValueError, TypeError):
                pass
    for field in ("description", "notes", "cpack"):
        val = request.POST.get(field, "").strip()
        if val:
            override_data[field] = val
    for field in ("force_crate", "do_not_tip"):
        override_data[field] = field in request.POST

    try:
        services.save_lot_override(request, lot_id, override_data)
        lot = services.get_lot(request, lot_id)
        lot_rows = build_lot_table_rows([lot])
        return render(request, "catalog/partials/lots_table_row.html", {
            "row": lot_rows[0],
        })
    except ABConnectError:
        logger.exception("Failed to save override for lot %s", lot_id)
        return render(request, "catalog/partials/panel_error.html", {
            "error_message": "Could not save override",
            "retry_url": "/",
            "retry_target": "#panel-main-content",
        })

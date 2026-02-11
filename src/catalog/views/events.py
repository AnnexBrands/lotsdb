from django.shortcuts import render

from catalog import services


def event_detail(request, event_id):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 25))

    event = services.get_catalog(request, event_id)

    # CatalogExpandedDto includes lots (LotCatalogInformationDto: id + lot_number).
    # The Lot list API does not support CustomerCatalogId filtering, so we use
    # the embedded lots from the catalog response and paginate locally.
    all_lots = event.lots or []
    total = len(all_lots)
    start = (page - 1) * page_size
    page_lots = all_lots[start : start + page_size]
    total_pages = max(1, (total + page_size - 1) // page_size)

    paginated = {
        "page_number": page,
        "total_pages": total_pages,
        "total_items": total,
        "has_previous_page": page > 1,
        "has_next_page": page < total_pages,
    }

    # Find seller context for breadcrumbs
    seller = event.sellers[0] if event.sellers else None

    return render(request, "catalog/events/detail.html", {
        "event": event,
        "lots": page_lots,
        "paginated": paginated,
        "seller": seller,
        "preserved_params": {},
    })

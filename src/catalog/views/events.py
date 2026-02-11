from django.shortcuts import render

from catalog import services


def event_detail(request, event_id):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 25))

    event = services.get_catalog(request, event_id)

    lots_result = None
    if event.customer_catalog_id:
        lots_result = services.list_lots_by_catalog(
            request, customer_catalog_id=event.customer_catalog_id, page=page, page_size=page_size
        )

    # Find seller context for breadcrumbs
    seller = event.sellers[0] if event.sellers else None

    return render(request, "catalog/events/detail.html", {
        "event": event,
        "lots": lots_result.items if lots_result else [],
        "paginated": lots_result,
        "seller": seller,
        "preserved_params": {},
    })

from django.shortcuts import render

from catalog import services


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

    return render(request, "catalog/sellers/list.html", {
        "sellers": result.items,
        "paginated": result,
        "filter_fields": filter_fields,
        "preserved_params": preserved_params,
    })


def seller_detail(request, seller_id):
    seller = services.get_seller(request, seller_id)
    return render(request, "catalog/sellers/detail.html", {
        "seller": seller,
        "events": seller.catalogs if seller.catalogs else [],
    })

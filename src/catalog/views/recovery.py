from ABConnect.api.models.catalog import AddLotRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from catalog import services


@require_GET
def recovery_dashboard(request):
    entries = services.get_recovery_entries(request)
    return render(request, "catalog/recovery.html", {
        "entries": entries,
        "empty": len(entries) == 0,
    })


@require_POST
def recovery_check(request, customer_item_id):
    api = services.get_catalog_api(request)
    result = api.lots.list(CustomerItemId=customer_item_id, page_size=1)
    if result.items:
        lot = result.items[0]
        return render(request, "catalog/partials/recovery_status.html", {"lot": lot})
    return render(request, "catalog/partials/recovery_status.html", {"missing": True})


@require_POST
def recovery_retry(request, customer_item_id):
    force = request.GET.get("force") == "true"
    entries = services.get_recovery_entries(request)
    entry = next((e for e in entries if e.get("customer_item_id") == customer_item_id), None)
    if not entry:
        return HttpResponse('<tr><td colspan="6">Entry not found in recovery cache</td></tr>')

    # Check if lot already exists on server (unless force)
    if not force:
        api = services.get_catalog_api(request)
        existing = api.lots.list(CustomerItemId=customer_item_id, page_size=1)
        if existing.items:
            return render(request, "catalog/partials/recovery_row.html", {
                "entry": entry,
                "warning": True,
                "existing_lot": existing.items[0],
            })

    # If force and lot exists, delete it first
    if force:
        api = services.get_catalog_api(request)
        existing = api.lots.list(CustomerItemId=customer_item_id, page_size=1)
        if existing.items:
            services.delete_lot(request, existing.items[0].id)

    # Retry create
    try:
        add_req = AddLotRequest.model_validate(entry["add_lot_request"])
        services.create_lot(request, add_req)
        services.remove_recovery_entry(request, customer_item_id)
        remaining = services.get_recovery_entries(request)
        return render(request, "catalog/partials/recovery_row.html", {
            "entry": entry,
            "success": True,
            "all_recovered": len(remaining) == 0,
        })
    except Exception as e:
        return render(request, "catalog/partials/recovery_row.html", {
            "entry": entry,
            "error": str(e),
        })


@require_POST
def recovery_skip(request, customer_item_id):
    services.remove_recovery_entry(request, customer_item_id)
    remaining = services.get_recovery_entries(request)
    if not remaining:
        return HttpResponse(
            '<tr id="recovery-all-done"><td colspan="6" class="empty-state">'
            'All items recovered. <a href="/">Return to catalog</a>'
            '</td></tr>'
        )
    return HttpResponse("")

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from catalog import services
from catalog.forms import OverrideForm


def lot_detail(request, lot_id):
    lot = services.get_lot(request, lot_id)

    initial = lot.initial_data
    override = lot.overriden_data[0] if lot.overriden_data else None

    # Resolve seller/event context for breadcrumbs
    seller = None
    event = None
    if lot.catalogs:
        catalog_id = lot.catalogs[0].catalog_id
        try:
            event = services.get_catalog(request, catalog_id)
            if event.sellers:
                seller = event.sellers[0]
        except Exception:
            pass

    field_defs = [
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

    rows = []
    for label, attr, is_flag in field_defs:
        init_val = getattr(initial, attr, None) if initial else None
        over_val = getattr(override, attr, None) if override else None
        changed = override is not None and over_val != init_val
        rows.append({
            "label": label,
            "initial": init_val,
            "override": over_val,
            "changed": changed,
            "is_flag": is_flag,
        })

    return render(request, "catalog/lots/detail.html", {
        "lot": lot,
        "has_override": override is not None,
        "rows": rows,
        "seller": seller,
        "event": event,
    })


def override_form(request, lot_id):
    lot = services.get_lot(request, lot_id)
    override = lot.overriden_data[0] if lot.overriden_data else None
    source = override or lot.initial_data

    # Resolve breadcrumb context
    seller = None
    event = None
    if lot.catalogs:
        catalog_id = lot.catalogs[0].catalog_id
        try:
            event = services.get_catalog(request, catalog_id)
            if event.sellers:
                seller = event.sellers[0]
        except Exception:
            pass

    if request.method == "POST":
        form = OverrideForm(request.POST)
        if form.is_valid():
            override_data = {k: v for k, v in form.cleaned_data.items() if v is not None}
            services.save_lot_override(request, lot_id, override_data)
            return HttpResponseRedirect(reverse("lot_detail", args=[lot_id]))
    else:
        initial_data = {}
        if source:
            for field_name in OverrideForm.base_fields:
                val = getattr(source, field_name, None)
                if val is not None:
                    initial_data[field_name] = val
        form = OverrideForm(initial=initial_data)

    return render(request, "catalog/lots/override.html", {
        "form": form,
        "lot": lot,
        "seller": seller,
        "event": event,
    })

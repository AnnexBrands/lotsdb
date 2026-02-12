# Research: Lots Table & Bugfixes

**Branch**: `006-lots-table-bugfix` | **Date**: 2026-02-11

## R1: Event selection OOB bug

**Decision**: Wrap the `#panel-main-content` OOB in `events_panel.html` with a conditional guard.

**Rationale**: `events_panel.html` is included in two contexts:
1. As the main response from `seller_events_panel` (should clear main panel)
2. Via OOB include from `lots_panel.html` (must NOT clear main panel — lots were just loaded)

The nested OOB `<div id="panel-main-content" hx-swap-oob="innerHTML">` fires unconditionally, overwriting the lots that were just swapped into `#panel-main-content` by the primary response.

**Fix**: Add a template variable `skip_main_oob` and pass `skip_main_oob=True` when including from `lots_panel.html`. Guard the OOB block: `{% if not skip_main_oob %}`.

**Alternatives considered**:
- Removing the OOB entirely and using a separate clear mechanism → more complex, breaks existing seller→events flow
- Using HTMX `hx-swap-oob="none"` → not a valid HTMX value

## R2: Lot data fetching strategy

**Decision**: Hybrid approach — use embedded `event.lots` for reliable ID scoping, then fetch full `LotDto` per lot via `services.get_lot()`.

**Rationale**:
- `GET /api/Lot` does NOT support `CustomerCatalogId` filter (confirmed via swagger). The `list_lots_by_catalog` service method passes it as a query param but the API doesn't officially support it — explains unreliability.
- `GET /api/Lot` does NOT support batch ID fetching (single `Id` param only).
- No batch endpoint exists for lots.
- Individual `get_lot(lot_id)` calls are the only reliable way to get full `LotDto`.

**Performance mitigation**: Reduce default page size from 50 to 25. At 25 lots per page: 1 `get_catalog` + 25 `get_lot` = 26 API calls.

**Alternatives considered**:
- Use `list_lots_by_catalog` and cross-reference with embedded IDs → unreliable source, may miss lots
- HTMX lazy-load per row → complex, poor UX for table layout
- Add batch endpoint to ABConnectTools → out of scope for bugfix release

## R3: Override display model

**Decision**: Compute effective value and override status server-side, pass to template as row metadata.

**Rationale**: The existing `lot_detail` view already does this (see `views/lots.py` lines 27-54). Reuse the same pattern: for each field, compare `initial_data.{field}` vs `overriden_data[0].{field}` and set `changed=True` if they differ.

**Data structure per lot row**:
```python
{
    "lot": lot,                    # Full LotDto
    "fields": {
        "qty": {"value": 5, "changed": True, "original": 3},
        "l": {"value": 12.0, "changed": False, "original": 12.0},
        ...
    }
}
```

## R4: LotDataDto field mapping to table columns

| Column | LotDataDto field | Type | Notes |
|--------|-----------------|------|-------|
| Image | `lot.image_links[0].link` | URL | From LotDto, not LotDataDto |
| Description | `description` | str | Combined with notes in one cell |
| Notes | `notes` | str | Shown below description |
| Qty | `qty` | int | nullable |
| L | `l` | float | Length in inches |
| W | `w` | float | Width in inches |
| H | `h` | float | Height in inches |
| Wgt | `wgt` | float | Weight in pounds |
| CPack | `cpack` | str | Fragility code (1-4, pbo) |
| Crate | `force_crate` | bool | Checkbox/icon |
| Do Not Tip | `do_not_tip` | bool | Checkbox/icon |

## R5: HTMX save pattern

**Decision**: Each table row is a mini-form. Save button posts to `/panels/lots/{lot_id}/override/` via HTMX, returns the updated row HTML which replaces just that `<tr>`.

**Rationale**: This matches HTMX's fragment-swap pattern already used throughout the app. The existing `save_lot_override` service method handles the API call.

# Research: Import Hardening (020)

**Date**: 2026-02-17
**Feature**: `020-import-hardening`

## R1: Item Search — API Resolution Chain

**Decision**: Resolve customer_item_id via two API calls: lot lookup then catalog fetch for seller context.

**Rationale**: The ABConnect API has no single endpoint that resolves `customer_item_id` → seller + event. The lot listing endpoint (`GET /api/Lot?CustomerItemId=<value>`) returns `LotDto` with a `catalogs` list (each containing `catalog_id`), but no seller info. A second call to `GET /api/Catalog/{id}` returns `CatalogExpandedDto` with `sellers` list. This two-step chain is the only path.

**Resolution chain**:
1. `api.lots.list(CustomerItemId=query)` → `LotDto` with `lot.catalogs[0].catalog_id`
2. `api.catalogs.get(catalog_id)` → `CatalogExpandedDto` with `catalog.sellers[0].customer_display_id`
3. Build redirect URL: `/?seller={display_id}&event={customer_catalog_id}&item={customer_item_id}`

**Existing code**: `services.search_lots()` (services.py:383-400) already does step 1 but doesn't resolve seller context. New service function `resolve_item` will extend this.

**Alternatives considered**: Caching a reverse index (item→seller) — rejected as premature complexity; the two-call chain is fast enough for single-item lookups.

## R2: Events Panel Bug — Cache Ignores `future_only` Parameter

**Decision**: Fix `list_catalogs` cache early-return to respect the `future_only` parameter.

**Rationale**: `services.list_catalogs` (services.py:107-113) stores only future events in cache. The early-return path returns cached data unconditionally, ignoring `future_only=False`. When `event_lots_panel` (panels.py:260) calls `list_catalogs(..., future_only=False)` to re-render the events sidebar, it gets only future events from cache, silently dropping past events.

**Root cause**: Cache stores `projected_future` (lines 117-127) but the early-return (lines 107-113) doesn't check whether `future_only=False` was requested.

**Fix options**:
1. Store ALL events in cache, filter at return time — chosen, simplest fix
2. Add `future_only` to cache key — rejected, doubles cache entries per seller
3. Bypass cache when `future_only=False` — rejected, loses perf benefit

## R3: Do Not Tip Field — Wiring Confirmed Correct

**Decision**: No code change needed for `do_not_tip` wiring.

**Rationale**: Investigation confirmed `do_not_tip` is correctly wired in all paths:
- `save_lot_override` merges it (services.py:195)
- `lot_override_panel` reads it via `field in request.POST` (panels.py:486)
- `OverrideForm` has `do_not_tip = forms.BooleanField(...)` (forms.py:15)
- Both inline (`lots_table_row.html:36`) and modal (`lot_detail_modal.html:49`) templates have `name="do_not_tip"`

The API model uses `do_not_tip` (Python) / `DoNotTip` (serialization alias). The field maps correctly through `LotDataDto`.

**Action**: Mark FR-021 as requiring UAT verification only. If the bug persists, it's a different root cause (possibly checkbox value not being sent on certain browsers, or a race condition).

## R4: Cpack Override Indicator — Missing Template Code

**Decision**: Add `<span class="initial-ref">` with `show_ref` conditional to cpack in both table row and modal templates.

**Rationale**: Every dimension field (qty, l, w, h, wgt) in `lots_table_row.html` has:
```html
<span class="initial-ref{% if row.fields.X|show_ref %} initial-changed{% endif %}">
    {% if row.fields.X|show_ref %}{{ row.fields.X.original|format_number }}{% endif %}
</span>
```
But cpack (`lots_table_row.html:34`) has no such span. The `lot_detail_modal.html:47` has an empty `<span class="initial-ref">` that never renders the original value.

The `build_lot_table_rows` function (panels.py:51-63) already computes `changed` and `original` for cpack — the data is available, just not rendered.

## R5: Upload Redirect — Available Context

**Decision**: Construct deep-link redirect URL from available data after upload.

**Rationale**: After upload, the view has `customer_catalog_id` from the parsed file. To build `?seller=X&event=Y`, we need:
- `event_catalog_id` = `customer_catalog_id` (already available from `bulk_request.catalogs[0].customer_catalog_id`)
- `seller_display_id` = NOT available — requires `get_catalog(request, catalog_id)` → `catalog.sellers[0].customer_display_id`

For the new-catalog path: `find_catalog_by_customer_id` is already called (line 125 of imports.py) and returns the internal ID. Then `get_catalog()` resolves seller info.

For the merge path: `result["catalog_id"]` (internal) is already in the merge return dict. Same `get_catalog()` call resolves seller info.

**Cost**: One extra API call per upload to resolve seller. Acceptable since uploads are infrequent.

## R6: Toast Persistence Across Navigation

**Decision**: Use `sessionStorage` to persist toast message across page navigation.

**Rationale**: `window.showToast()` creates a DOM element that is destroyed on navigation. The merge toast fires then `window.location.href` navigates away immediately. Options:
1. **sessionStorage** — write toast data before redirect, read + display on page load. Chosen: simple, no backend changes, works with any redirect target.
2. **Query parameter** — rejected, clutters URL and message size is limited.
3. **Delay redirect** — rejected, poor UX (arbitrary wait time).

**Implementation**: Before redirect, write `{msg, type}` to `sessionStorage.setItem('pendingToast', ...)`. In `base.html` page load script, check `sessionStorage.getItem('pendingToast')`, show toast, then `removeItem`.

## R7: `UpdateLotRequest` — No `initial_data` Field

**Decision**: Recovery retry uses `create_lot` (AddLotRequest), not `update`. Force-update (FR-005) also uses `create_lot` after deleting the existing lot.

**Rationale**: `UpdateLotRequest` only allows changing `customer_item_id`, `image_links`, `overriden_data`, and `catalogs`. It has no `initial_data` field — source dimensional data cannot be changed via update. Since recovery entries cache the full `AddLotRequest` (which includes `initial_data`), retry must use `create_lot`. If the lot already exists on the server, the recovery page must delete it first before re-creating (same delete+create pattern as the merge itself).

## R8: Inline Save Bug — Investigation Needed

**Decision**: Requires live debugging during implementation.

**Rationale**: The research did not find a clear code-level root cause for "inline values not persisting." The `lot_override_panel` POST handler reads fields correctly. Possible causes:
1. Form submission not including all fields (partial POST)
2. `save_lot_override` merge logic overwriting new values with stale values
3. HTMX swap replacing the row before the response is processed
4. Stale lot data being re-fetched from cache after save

This needs to be debugged with a live server and browser devtools during implementation.

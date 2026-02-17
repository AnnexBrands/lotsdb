# PR #21 Review — Restore catalog import with dropzone and merge

**Branch:** `019-restore-catalog-import` → `main`
**Date:** 2026-02-17
**Tests:** 154 passing (21 new — contract, integration, unit)

---

## UAT Findings (FR-019)

### Upload catalog works, with issues

**UX — User feedback is missing during hover and upload**
- Dropzone hover state and upload-in-progress state lack modern feedback. Need animated grow on hover, upload progress indication, and completion animation.
- `window.showToast(msg, 'success')` is not shown because of race with `window.location.href = data.redirect` — the page navigates away before the toast is visible.
- 100% fail rate should not toast as success — if every lot fails merge, the response is still `{"success": true}` with "Added: 0, Updated: 0, Failed: N".
- No file size or type enforcement beyond extension check — add a `MAX_UPLOAD_SIZE` guard.

**UX — Redirect loses context, wasted API call**
- During upload we already have `seller_id` and `event_id` available, but the view makes a wasted API call to `find_catalog_by_customer_id` after bulk insert (line 125) and then discards the result, redirecting to `/` instead of `/?seller={seller_id}&event={event_id}`.
- Redirect should deep-link to the imported catalog: `/?seller=1874&event=405438`.

### Editing lots table does not work as expected

- **Values do not persist on save:** Changing values in the lots table inline edit and clicking save — new values do not stick.
- **Modal edit works, but cpack missing orange indicator:** Modal editing persists correctly, but `cpack` field needs the orange "original value" treatment like weight and dimensions already have.
- **DNT does not persist:** Checking Do Not Tip on table or modal does not persist. Likely needs `DoNotTip` (not `do_not_tip`) in the DTO field mapping — check API contract for correct casing.
- **Events panel drops past events after save:** After clicking save in the lots table, panel 2 (events) drops past events and only shows future events.

---

## Code Review

### Critical — Data Loss Risk in Update Path (DEFERRED)

**`src/catalog/services.py:347-367`** — The delete-then-create update strategy has a failure window. If `delete_lot` succeeds but `create_lot` throws, the lot is permanently deleted with no recovery. The `except` block catches and logs it, but the lot is already gone from the server.

```python
delete_lot(request, server_lot.id)   # succeeds
create_lot(request, add_req)         # fails -> lot is gone
```

The API supports `api.lots.update` (already used in `save_lot_override`) which would be safer. **Deferring this to a follow-up** — the current approach works for the happy path and the risk is low for typical catalog sizes. Will revisit when hardening the merge pipeline.

### Medium

**1. Dead code — `event_id` fetched but unused (`imports.py:125`)**

```python
event_id = services.find_catalog_by_customer_id(request, customer_catalog_id)
return JsonResponse({"success": True, "redirect": "/"})
```

Wasted API round-trip. Should be removed or used for the deep-link redirect.

**2. Toast races with redirect (`base.html:84-86`)**

```javascript
window.showToast(msg, 'success');
window.location.href = data.redirect;
```

Toast fires then page navigates away immediately. User never sees the merge summary. Options: delay redirect, pass summary via query param, or use `sessionStorage` to persist across navigation.

**3. Blanket `except Exception` in merge loop (`services.py:342,364`)**

Best-effort per-lot is reasonable, but when ALL lots fail (e.g., expired auth), the function returns `{"added": 0, "failed": N}` with `success: True`. Should re-raise when failure rate is 100%.

### Minor

**4. Confirm `fetch_all_lots` filter key** — Verify `list_lots_by_catalog` filters by `customer_catalog_id` and not by internal `catalog_id`. Wrong key would pull lots from an unrelated catalog into the merge.

**5. No file size limit** — Large uploads loaded entirely into memory. Add `MAX_UPLOAD_SIZE` check early in `upload_catalog`.

**6. CSS formatting inconsistency** — Dropzone CSS is single-line; rest of file is multi-line.

**7. `_to_dict` with `exclude_none=True`** — Correct for now, but if API ever distinguishes "field absent" from "field = 0", this could be a subtle bug.

**8. Repeated anonymous mock in `test_dropzone_ui.py`** — The `type("R", ...)` pattern is repeated 6 times. Extract to a shared fixture.

---

## What's Good

- Merge logic is well-designed: dedup by `customer_item_id`, preserve overrides, best-effort per-lot
- `lots_differ` normalization is careful (None-vs-0, None-vs-empty-string)
- Test coverage is excellent: 7 `lots_differ` cases, 6 merge scenarios, full contract tests for both paths
- Auth inherited from `LoginRequiredMiddleware` — no gap
- Client-side validation mirrors server-side extension check
- Drag-and-drop + click-to-browse dual interaction on the same element

## Verdict

Upload works end-to-end but the UX needs polish (feedback, toast visibility, deep-link redirect). Lots table editing has real bugs (values not persisting, DNT mapping, events panel regression). Delete-then-create risk is acknowledged and deferred. Recommend a follow-up PR to address the UAT findings before shipping to users.

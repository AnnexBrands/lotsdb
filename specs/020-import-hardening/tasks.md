# Tasks: Import Hardening

**Input**: Design documents from `/specs/020-import-hardening/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.yaml

**Tests**: Included per constitution requirement (Artifact Harmony — tests are first-class artifacts).

**Organization**: Four user stories. US1 (recovery) and US2 (search) are both P1 and independent. US3 (upload UX) and US4 (bug fixes) are P2 and independent. All stories depend on the foundational phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Fix shared infrastructure bugs and clean up code that affects multiple stories.

- [x] T001 Fix `list_catalogs` cache in `src/catalog/services.py` — change the cache to store ALL events (not just future), then filter by `future_only` at return time. The early-return path (lines 107-113) currently returns cached data unconditionally, ignoring `future_only=False`. Fix: store `result.items` projected to dicts (with `start_date` as ISO string) in the cache. On cache hit, filter to future-only if `future_only=True`, return all if `future_only=False`. Per research R2.
- [x] T002 [P] Add 100%-failure re-raise in merge loop in `src/catalog/services.py` — at the end of `merge_catalog`, after the per-lot iteration, if `failed > 0` and `added == 0` and `updated == 0` and `unchanged == 0` (i.e., every lot failed), raise an exception with the first error message so the view returns a 500 error instead of `success: true`. Per FR-025.
- [x] T003 [P] Remove dead code in `src/catalog/views/imports.py` — delete the unused `event_id = services.find_catalog_by_customer_id(...)` call after `bulk_insert` (currently line 125). The result is assigned but never used. Per FR-024, research R5.
- [x] T004 [P] Reformat dropzone CSS in `src/catalog/static/catalog/styles.css` — expand the single-line `.dropzone` rules into multi-line format matching the rest of the stylesheet. No behavioral change. Per FR-026.
- [x] T005 [P] Extract shared mock fixture in `tests/integration/test_dropzone_ui.py` — the `type("R", ...)` anonymous mock pattern is repeated 6 times. Extract to a `@pytest.fixture` or helper function in the test file (e.g., `_make_mock_response(...)`) and replace all usages. Per FR-027.

**Checkpoint**: Shared bugs fixed, code clean. User story implementation can begin.

---

## Phase 2: User Story 1 — Merge Recovery Dashboard (Priority: P1) 🎯 MVP

**Goal**: When a merge has lot-level failures, cache the failed payloads to Redis and provide a dedicated recovery page with check/retry/skip actions per item.

**Independent Test**: Trigger a merge with failures → recovery page lists failed lots → check server state → retry or skip → all recovered.

### Implementation for User Story 1

- [x] T006 [US1] Add recovery cache helper functions to `src/catalog/services.py` — implement four functions: (1) `cache_recovery_entry(request, entry_dict)` — reads existing list from Redis key `{abc_username}:merge_recovery`, appends new entry, writes back with 24h TTL. Wrap in try/except so Redis failure doesn't break the merge. (2) `get_recovery_entries(request)` — reads and returns the list, or empty list on miss/error. (3) `remove_recovery_entry(request, customer_item_id)` — removes entry by `customer_item_id` from the list, writes back. If list is empty after removal, delete the key. (4) `clear_recovery_entries(request)` — deletes the key. Cache key format: `{request.session['abc_username']}:merge_recovery`. Per data-model.md Recovery Entry schema, FR-001, FR-006.
- [x] T007 [US1] Modify `merge_catalog` in `src/catalog/services.py` to cache failed lots — in the per-lot `except` blocks (both new-lot and changed-lot paths), after incrementing `failed` and appending to `errors`, call `cache_recovery_entry(request, entry)` with a dict containing: `customer_item_id`, `lot_number`, `catalog_id`, `customer_catalog_id` (from `bulk_request.catalogs[0].customer_catalog_id`), `seller_display_id` (resolve via `get_catalog(request, catalog_id)` once at the start and cache the seller display ID), `operation` ("create" or "update"), `add_lot_request` (the `AddLotRequest` serialized via `model_dump(by_alias=True)`), `error_message` (str(e)), `timestamp` (ISO 8601). Also add `seller_display_id` and `customer_catalog_id` to the return dict for use by the upload view. Per FR-001, FR-006, data-model.md.
- [x] T008 [US1] Add recovery URL routes to `src/catalog/urls.py` — import `recovery_dashboard`, `recovery_check`, `recovery_retry`, `recovery_skip` from `catalog.views.recovery`. Add paths: `path("imports/recovery/", recovery_dashboard, name="recovery_dashboard")`, `path("imports/recovery/check/<str:customer_item_id>/", recovery_check, name="recovery_check")`, `path("imports/recovery/retry/<str:customer_item_id>/", recovery_retry, name="recovery_retry")`, `path("imports/recovery/skip/<str:customer_item_id>/", recovery_skip, name="recovery_skip")`. Per contracts/api.yaml.
- [x] T009 [US1] Create recovery views in `src/catalog/views/recovery.py` — implement four views: (1) `recovery_dashboard(request)` GET — calls `services.get_recovery_entries(request)`, renders `catalog/recovery.html` with entries list context. If empty, context includes `empty=True`. (2) `recovery_check(request, customer_item_id)` POST — calls `api.lots.list(CustomerItemId=customer_item_id, page_size=1)`. If found, renders `catalog/partials/recovery_status.html` with lot summary (qty, dimensions). If not found, renders same template with `missing=True`. (3) `recovery_retry(request, customer_item_id)` POST — reads `force` from `request.GET`. Gets the cached entry. If not `force`, first checks if lot exists on server; if exists, returns warning row with skip/force buttons. If `force` or lot missing: calls `create_lot(request, AddLotRequest(**entry['add_lot_request']))`. On success, calls `remove_recovery_entry`, returns success row. On failure, returns error row with full error message. (4) `recovery_skip(request, customer_item_id)` POST — calls `remove_recovery_entry`. If no entries remain, returns "all recovered" HTML. Otherwise returns empty `""`. All views require login (existing middleware). Per FR-002 through FR-005, FR-007, contracts/api.yaml.
- [x] T010 [US1] Create recovery page template at `src/catalog/templates/catalog/recovery.html` — extends `catalog/base.html`. Content: heading "Merge Recovery", a `<table>` with columns: Item ID, Lot #, Operation, Error, Status, Actions. If `empty` is true, show "No pending recoveries" message with a link to home. Each row uses `{% include "catalog/partials/recovery_row.html" %}`. Include the `showToast` script and a page-load check for `sessionStorage.getItem('pendingToast')` (same as base.html will have). Per FR-002.
- [x] T011 [P] [US1] Create recovery row partial at `src/catalog/templates/catalog/partials/recovery_row.html` — a `<tr id="recovery-{{ entry.customer_item_id }}">` with: customer_item_id, lot_number, operation badge ("create"/"update"), error_message (truncated, full on hover via title), a status cell (initially empty, filled by check/retry responses), and action buttons: "Check Server" (`hx-post="{% url 'recovery_check' entry.customer_item_id %}"` targeting the status cell, `hx-swap="innerHTML"`), "Retry" (`hx-post="{% url 'recovery_retry' entry.customer_item_id %}"` targeting the entire row, `hx-swap="outerHTML"`), "Skip" (`hx-post="{% url 'recovery_skip' entry.customer_item_id %}"` targeting the row, `hx-swap="outerHTML"`). CSS classes: `.recovery-row`, `.recovery-row.success`, `.recovery-row.error`, `.recovery-row.warning`. Per FR-003, FR-004, FR-005.
- [x] T012 [P] [US1] Create recovery status partial at `src/catalog/templates/catalog/partials/recovery_status.html` — if `missing`: `<span class="recovery-status missing">Not found on server</span>`. If found: `<span class="recovery-status found">Exists on server (Qty: {{ lot.initial_data.qty }}, {{ lot.initial_data.l }}x{{ lot.initial_data.w }}x{{ lot.initial_data.h }})</span>`. Per FR-003, contracts/api.yaml.
- [x] T013 [P] [US1] Add recovery page CSS to `src/catalog/static/catalog/styles.css` — add styles for `.recovery-row`, `.recovery-row.success` (green-tinted background), `.recovery-row.error` (red-tinted background), `.recovery-row.warning` (amber-tinted background), `.recovery-status.found` (green text), `.recovery-status.missing` (red text), recovery table layout, action button styles.
- [x] T014 [US1] Modify `upload_catalog` in `src/catalog/views/imports.py` to include `recovery_url` in merge response — after `merge_catalog` returns, if `result["failed"] > 0`, add `"recovery_url": reverse("recovery_dashboard")` to the JSON response. Also update the merge response to use the deep-link redirect URL: call `services.get_catalog(request, result["catalog_id"])` to get seller display ID, then set `redirect` to `/?seller={seller_display_id}&event={customer_catalog_id}`. Per FR-007, FR-015, contracts/api.yaml.
- [x] T015 [P] [US1] Add contract tests for recovery endpoints in `tests/contract/test_recovery.py` — test `recovery_dashboard` GET returns HTML with table when entries exist and "no pending" when empty (mock `get_recovery_entries`). Test `recovery_check` POST returns found/missing HTML fragments (mock `api.lots.list`). Test `recovery_retry` POST success removes entry and returns success row (mock `create_lot` + `remove_recovery_entry`). Test `recovery_retry` when lot exists returns warning row (mock `api.lots.list` returning a lot). Test `recovery_skip` POST removes entry. Use Django test client with session injection and `SimpleNamespace` for mocks.
- [x] T016 [P] [US1] Add unit tests for recovery cache helpers in `tests/unit/test_merge.py` — test `cache_recovery_entry` appends to existing list and creates new list. Test `get_recovery_entries` returns entries on hit, empty list on miss. Test `remove_recovery_entry` removes by customer_item_id and deletes key when empty. Test `clear_recovery_entries` deletes the key. Test Redis failure in `cache_recovery_entry` doesn't raise (logs warning). Use Django's test cache override.

**Checkpoint**: Full US1 functional. Merge failures are cached, recovery page works with check/retry/skip.

---

## Phase 3: User Story 2 — Search by Customer Item ID (Priority: P1)

**Goal**: Navbar search input resolves a customer item ID to its seller, event, and lot position, redirecting to a deep-link that highlights the lot.

**Independent Test**: Type an item ID → redirected to correct seller+event+page → lot row highlighted.

### Implementation for User Story 2

- [x] T017 [US2] Add `resolve_item` service function to `src/catalog/services.py` — implement `resolve_item(request, customer_item_id)` that: (1) calls `api.lots.list(CustomerItemId=customer_item_id, page_size=1)`, (2) if no results returns `None`, (3) takes `lot.catalogs[0].catalog_id`, calls `services.get_catalog(request, catalog_id)` to get the full catalog, (4) extracts `seller_display_id = catalog.sellers[0].customer_display_id`, `customer_catalog_id = catalog.customer_catalog_id`, (5) computes `lot_position` by iterating `catalog.lots` (embedded `LotCatalogInformationDto`) and finding the index where `lot_ref.id == lot.id`, (6) returns a dict: `{customer_item_id, lot_id, catalog_id, customer_catalog_id, seller_display_id, lot_position}`. Per research R1, data-model.md Item Search Result, FR-009.
- [x] T018 [US2] Add item search view to `src/catalog/views/imports.py` — implement `search_item(request)` GET view: reads `q = request.GET.get("q", "").strip()`. If empty, redirects to `/` with sessionStorage toast "Enter an item ID". Calls `services.resolve_item(request, q)`. If `None`, redirects to `/` with sessionStorage toast "Item not found". If found, redirects to `/?seller={seller_display_id}&event={customer_catalog_id}&item={customer_item_id}`. For the toast-via-redirect pattern, set a session key `request.session['pending_toast'] = {msg, type}` (read and cleared by seller_list view). Per FR-010, FR-011, contracts/api.yaml.
- [x] T019 [US2] Add search URL route to `src/catalog/urls.py` — import `search_item` from `catalog.views.imports`, add `path("search/item/", search_item, name="search_item")`. Per contracts/api.yaml.
- [x] T020 [US2] Add search input to navbar in `src/catalog/templates/catalog/base.html` — add a `<form action="{% url 'search_item' %}" method="get" class="nav-search">` between the dropzone and the logout form. Contains: `<input type="text" name="q" placeholder="Item ID" class="search-input">` and a submit button (magnifying glass icon or "Go" text). Style: inline with navbar, compact. Per FR-008.
- [x] T021 [US2] Extend `seller_list` view in `src/catalog/views/sellers.py` to handle `?item=` parameter — read `item_id = request.GET.get("item", "").strip()`. When `item_id` is present AND `hydrate_lots` is already populated (event is hydrated): (1) find the lot's position in the embedded `event.lots` list by matching `customer_item_id`, (2) compute the page number: `page = (position // page_size) + 1`, (3) if not page 1, re-paginate `event.lots` for that page and re-fetch full lot data, (4) set `context["selected_item_id"] = item_id` for template highlighting. Also check `request.session.pop('pending_toast', None)` and pass to context as `pending_toast` for the template to render on page load. Per FR-012, FR-013.
- [x] T022 [US2] Add lot active highlight to templates — in `src/catalog/templates/catalog/partials/lots_table_row.html`, add a conditional class: `<tr class="lot-row{% if row.lot.customer_item_id == selected_item_id %} lot-active{% endif %}" ...>`. In `src/catalog/templates/catalog/shell.html`, pass `selected_item_id` to the lots panel include. In `src/catalog/templates/catalog/partials/lots_panel.html`, pass `selected_item_id` to each row include. Per FR-014.
- [x] T023 [P] [US2] Add search and highlight CSS to `src/catalog/static/catalog/styles.css` — add `.nav-search` (inline flex, gap), `.search-input` (compact input matching navbar style), `.lot-active` (distinct highlight — e.g., light blue left border + subtle blue background tint, should contrast with hover state). Per FR-008, FR-014.
- [x] T024 [P] [US2] Add unit tests for `resolve_item` in `tests/unit/test_resolve.py` — test: (1) item found returns correct dict with seller_display_id, customer_catalog_id, lot_position. (2) item not found returns None. (3) lot with multiple catalogs uses first catalog. (4) lot_position computation is correct (index 0, middle, last). Mock `api.lots.list` and `api.catalogs.get` with `SimpleNamespace` objects. Per research R1.
- [x] T025 [P] [US2] Add contract tests for search endpoint in `tests/contract/test_search.py` — test: (1) GET `/search/item/?q=VALID_ID` with mocked `resolve_item` returning a result → 302 redirect to `/?seller=X&event=Y&item=Z`. (2) GET `/search/item/?q=INVALID_ID` with mocked `resolve_item` returning None → 302 redirect to `/` with pending_toast in session. (3) GET `/search/item/` with no `q` → 302 redirect to `/`. Use Django test client with session injection.
- [x] T026 [P] [US2] Add integration test for item deep-link hydration in `tests/integration/test_dropzone_ui.py` or new file — test that `seller_list` view with `?seller=X&event=Y&item=Z` params passes `selected_item_id` to template context. Test that `lots_table_row.html` renders `.lot-active` class when `selected_item_id` matches.

**Checkpoint**: Full US2 functional. Navbar search resolves items and deep-links with lot highlighting.

---

## Phase 4: User Story 3 — Upload UX Polish (Priority: P2)

**Goal**: Fix upload redirect, toast persistence, file size enforcement, 100%-failure detection, and dropzone animations.

**Independent Test**: Upload a file → toast persists on destination page → redirect lands on correct seller+event. Oversized file rejected. 100% failure shown as error.

**Depends on**: Phase 2 (US1) for `recovery_url` in response. Phase 3 (US2) for deep-link infrastructure used by redirect.

### Implementation for User Story 3

- [x] T027 [US3] Add sessionStorage toast persistence to `src/catalog/templates/catalog/base.html` — add a page-load script block that checks `sessionStorage.getItem('pendingToast')`: if present, parse JSON `{msg, type}`, call `showToast(msg, type)`, then `removeItem('pendingToast')`. Also check `{{ pending_toast|safe }}` context variable (from search redirect) and show that toast. In the dropzone JS success handler: before `window.location.href = data.redirect`, write `sessionStorage.setItem('pendingToast', JSON.stringify({msg, type: 'success'}))` for merge toasts. Remove the existing `showToast` call before redirect (it's now handled on the destination page). Per FR-016, research R6.
- [x] T028 [US3] Add 100%-failure detection to dropzone JS in `src/catalog/templates/catalog/base.html` — in the success handler, after checking `data.success`, add: if `data.merge && data.merge.added === 0 && data.merge.updated === 0 && data.merge.unchanged === 0 && data.merge.failed > 0`, treat as error: call `showToast('Merge failed: all lots encountered errors', 'error')` and if `data.recovery_url` exists, append a link. Do NOT redirect. Per FR-017.
- [x] T029 [US3] Add file size check to `src/catalog/templates/catalog/base.html` and `src/catalog/views/imports.py` — client-side: in `handleFile(file)`, before the extension check, add `if (file.size > 1048576) { showToast('File too large (max 1 MB)', 'error'); return; }`. Server-side: in `upload_catalog`, after getting `uploaded`, add `if uploaded.size > 1048576: return JsonResponse({"success": False, "error": "File too large. Maximum size: 1 MB"}, status=400)`. Per FR-018, clarification (1 MB limit).
- [x] T030 [US3] Update deep-link redirect in `src/catalog/views/imports.py` — for new-catalog path: after `bulk_insert`, call `find_catalog_by_customer_id` to get internal ID, then `get_catalog(request, internal_id)` to get seller info, build redirect URL `/?seller={seller_display_id}&event={customer_catalog_id}`. For merge path: use `result["seller_display_id"]` and `result["customer_catalog_id"]` (added in T007) to build the same redirect URL. Remove the existing hardcoded `"/"` redirect. Per FR-015, research R5.
- [x] T031 [P] [US3] Add dropzone animation CSS and JS — in `src/catalog/static/catalog/styles.css`: add `.dropzone:hover` scale transform (`transform: scale(1.05)`), transition on `.dropzone` (`transition: all 0.2s ease`). Add `.dropzone.uploading` pulsing animation (`@keyframes pulse`, opacity 0.4-0.8 cycle). In `src/catalog/templates/catalog/base.html`: the existing `dropzone.classList.add('uploading')` already triggers the CSS state; verify the animation is visible. Per FR-019.
- [x] T032 [P] [US3] Update contract tests for upload endpoint in `tests/contract/test_upload.py` — add test: new catalog upload returns redirect URL with `?seller=` and `?event=` params (mock `get_catalog` to return seller info). Add test: merge with failures includes `recovery_url` in response. Add test: oversized file (>1 MB) returns 400 with size error. Update existing success tests to expect deep-link redirect URL instead of `"/"`.
- [x] T033 [P] [US3] Update integration tests in `tests/integration/test_dropzone_ui.py` — add test: `pendingToast` sessionStorage script is present in base.html. Add test: file size check JS is present (`file.size > 1048576`). Add test: 100%-failure detection logic is present in JS (check for `data.merge.failed > 0` with all others zero).

**Checkpoint**: Full US3 functional. Upload redirects to deep-link, toast persists, file size enforced, failures detected.

---

## Phase 5: User Story 4 — Lots Table Bug Fixes (Priority: P2)

**Goal**: Fix cpack override indicator, events panel past-events regression, and investigate inline save persistence.

**Independent Test**: Cpack shows orange indicator when overridden. Events panel shows past events after save. Inline save values persist.

**Depends on**: Phase 1 (T001 fixes the underlying cache bug for FR-023).

### Implementation for User Story 4

- [x] T034 [US4] Fix cpack override indicator in `src/catalog/templates/catalog/partials/lots_table_row.html` — the cpack `<select>` (line 34) has no `<span class="initial-ref">` indicator. Add one following the same pattern as qty/l/w/h/wgt fields: after the `</select>`, add `<span class="initial-ref{% if row.fields.cpack|show_ref %} initial-changed{% endif %}">{% if row.fields.cpack|show_ref %}{{ row.fields.cpack.original }}{% endif %}</span>`. Note: cpack original is a string, not a number, so use `{{ row.fields.cpack.original }}` without `|format_number`. Per FR-022, research R4.
- [x] T035 [P] [US4] Fix cpack override indicator in `src/catalog/templates/catalog/partials/lot_detail_modal.html` — the cpack `<span class="initial-ref">` (line 47) is always empty. Add the `show_ref` conditional and original value display matching the pattern used for dimension fields in the same template. Per FR-022, research R4.
- [ ] T036 [US4] Debug and fix inline save persistence — REQUIRES LIVE SERVER in `src/catalog/views/panels.py` and related files — per research R8, the root cause is not yet identified. Debug with live server: (1) check browser devtools Network tab to verify POST body includes all field values, (2) check `lot_override_panel` response to verify returned `<tr>` has updated values, (3) check if HTMX swap is replacing the row correctly, (4) check if page refresh re-fetches stale data from cache. Fix whatever is found. If the issue is that `save_lot_override` re-fetches the lot after save and the API returns stale data, add a short delay or cache invalidation. Per FR-020.
- [ ] T037 [US4] Verify DNT persistence via UAT — REQUIRES LIVE SERVER — per research R3, the `do_not_tip` field is correctly wired in all code paths. Test manually on the dev server: toggle DNT in the modal, save, refresh, verify it persists. If it does not persist, investigate further (possibly API-side issue with `DoNotTip` serialization). Per FR-021.

**Checkpoint**: All US4 bugs fixed. Cpack indicator shows, events panel retains past events, inline save verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories.

- [ ] T038 Run quickstart.md manual validation — start dev server, test all four user stories per `specs/020-import-hardening/quickstart.md`. Verify: recovery dashboard works end-to-end, item search resolves and highlights, upload redirects with persistent toast, cpack indicator shows, events panel retains past events after save.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately
  - T001 modifies services.py (cache logic) — no conflicts with other T001-T005 tasks
  - T002, T003, T004, T005 are fully parallel (different files)
- **US1 (Phase 2)**: Depends on Phase 1 (T001 cache fix, T002 re-raise)
  - T006 → T007 → T014 (services chain → upload view)
  - T008 parallel with T006 (urls.py vs services.py)
  - T009 depends on T006+T008 (views need services + routes)
  - T010 depends on T009 (template needs views)
  - T011, T012, T013 parallel with each other (partials + CSS)
  - T015, T016 parallel, depend on T009/T006
- **US2 (Phase 3)**: Depends on Phase 1 only
  - T017 → T018 → T019 (service → view → route)
  - T020 depends on T019 (navbar needs route for URL)
  - T021 depends on T017 (seller_list needs resolve context)
  - T022 depends on T021 (templates need context variables)
  - T023, T024, T25, T026 parallel
- **US3 (Phase 4)**: Depends on Phase 2 (US1 for recovery_url) and Phase 3 (US2 for deep-link)
  - T027, T028, T029 touch base.html — execute sequentially
  - T030 depends on T014 (imports.py already modified in US1)
  - T031, T032, T033 parallel
- **US4 (Phase 5)**: Depends on Phase 1 (T001 cache fix) only
  - T034 → T035 parallel (different templates)
  - T036, T037 independent investigation tasks
- **Polish (Phase 6)**: Depends on all phases complete

### Within User Story 1

```
T006 ──→ T007 ──→ T014
  │
  ├──→ T009 ──→ T010
  │       │
T008 ─┘   ├──→ T011 (parallel)
          ├──→ T012 (parallel)
          └──→ T013 (parallel)
T015 (parallel with T009+)
T016 (parallel with T009+)
```

### Within User Story 2

```
T017 ──→ T018 ──→ T019 ──→ T020
  │         │
  ├──→ T021 ──→ T022
  │
T023 (parallel)
T024 (parallel with T017+)
T025 (parallel with T018+)
T026 (parallel with T021+)
```

### Parallel Opportunities

```bash
# Phase 1 — all parallel except T001:
Task: "Add 100%-failure re-raise in services.py"
Task: "Remove dead code in imports.py"
Task: "Reformat dropzone CSS"
Task: "Extract shared mock fixture"

# Phase 2 — US1 partials + CSS parallel:
Task: "Create recovery_row.html partial"
Task: "Create recovery_status.html partial"
Task: "Add recovery page CSS"

# Phase 3 — US2 CSS + tests parallel:
Task: "Add search and highlight CSS"
Task: "Unit tests for resolve_item"
Task: "Contract tests for search endpoint"

# Phase 4 — US3 CSS + tests parallel:
Task: "Add dropzone animation CSS"
Task: "Update upload contract tests"
Task: "Update dropzone integration tests"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 4)

1. Complete Phase 1: Foundational (T001-T005)
2. Complete Phase 5: US4 Bug Fixes (T034-T037) — quick wins, unblocks daily use
3. Complete Phase 2: US1 Recovery Dashboard (T006-T016)
4. **STOP and VALIDATE**: Test recovery flow + bug fixes per quickstart.md
5. Deploy if ready — merge is now safe with recovery

### Full Feature (Add US2 + US3)

6. Complete Phase 3: US2 Item Search (T017-T026)
7. Complete Phase 4: US3 Upload UX Polish (T027-T033)
8. **STOP and VALIDATE**: Test search + upload UX per quickstart.md
9. Complete Phase 6: Polish (T038)

### Summary

| Metric | Value |
|--------|-------|
| Total tasks | 38 |
| Foundational tasks | 5 (T001-T005) |
| User Story 1 tasks | 11 (T006-T016) |
| User Story 2 tasks | 10 (T017-T026) |
| User Story 3 tasks | 7 (T027-T033) |
| User Story 4 tasks | 4 (T034-T037) |
| Polish tasks | 1 (T038) |
| Parallel opportunities | 4 groups |
| Files modified | 12 existing |
| Files created | 6 new (1 view, 3 templates, 3 test files) |

---

## Notes

- [P] tasks = different files, no dependencies
- [US1]/[US2]/[US3]/[US4] label maps task to specific user story for traceability
- Commit after each task or logical group
- US1 and US2 are both P1 but independent — can be done in either order
- US4 (bug fixes) can be done early as quick wins since they only depend on Phase 1
- `SimpleNamespace` (not `MagicMock`) for test fixtures due to `LocMemCache` pickling
- Research R3 confirmed `do_not_tip` wiring is correct — FR-021 is UAT verification only
- Research R8 (inline save bug) requires live debugging — T036 is investigative

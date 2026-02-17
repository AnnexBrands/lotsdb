# Tasks: Restore Catalog Import with Merge

**Input**: Design documents from `/specs/019-restore-catalog-import/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.yaml

**Tests**: Included per constitution requirement (Artifact Harmony — tests are first-class artifacts).

**Organization**: Two P1 user stories. US1 (new catalog import) must complete before US2 (merge) because US2 extends the upload view created in US1. Tests are included within each story phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Restore URL routing and CSS that must exist before the UI and view logic can function.

- [X] T001 [P] Add dropzone and upload CSS to `src/catalog/static/catalog/styles.css` — add `.dropzone` styles (nav element, border dashed, flex layout, gap), `.dropzone:hover` (border highlight), `.dropzone.dragover` (active state with blue border and background), `.dropzone.uploading` (opacity 0.6, pointer-events none), `.dropzone input[type="file"]` (display none). Per research R1.
- [X] T002 [P] Add upload route to `src/catalog/urls.py` — import `upload_catalog` from `catalog.views.imports`, add `path("imports/upload/", upload_catalog, name="upload_catalog")` to urlpatterns.

**Checkpoint**: CSS ready, URL route wired. Upload view is reachable.

---

## Phase 2: User Story 1 — Import New Catalog via Dropzone (Priority: P1) 🎯 MVP

**Goal**: A user can drag-and-drop (or click-to-browse) a catalog file onto the "Add Catalog" dropzone in the navbar. Valid files with new catalog IDs are bulk-inserted and the user is redirected to the event page. Invalid files show a toast error.

**Independent Test**: Drop a valid `.xlsx` catalog file with a new customer catalog ID → redirected to `/events/<id>/`. Drop a `.txt` file → toast error appears, page unchanged.

### Implementation for User Story 1

- [X] T003 [US1] Verify and update `upload_catalog` view in `src/catalog/views/imports.py` — confirm the existing view handles: file validation (extension check against `SUPPORTED_EXTENSIONS`), temp file write, `load_file()` call, `bulk_insert()` call, `find_catalog_by_customer_id()` for redirect URL, and returns `JsonResponse` with `{success, redirect}` or `{success: false, error}`. Ensure error messages match contract examples (e.g., "No file uploaded", "Unsupported file type: .X. Accepted: .xlsx, .csv, .json", "File contains no catalog data"). Add catalog-exists check stub: after `find_catalog_by_customer_id()`, if catalog exists, return a placeholder (to be implemented in US2). Per contract `POST /imports/upload/` and FR-001 through FR-007.
- [X] T004 [US1] Add dropzone HTML and drag-and-drop JavaScript to `src/catalog/templates/catalog/base.html` — (1) Add dropzone element in navbar between the brand logo and the logout form: `<label class="dropzone" id="dropzone" for="dropzone-input">Add Catalog<input type="file" id="dropzone-input" accept=".xlsx,.csv,.json"></label>`. (2) Add inline `<script>` after the existing `showToast` script implementing: click-to-browse via hidden file input, `dragover`/`dragleave`/`drop` event handlers on the dropzone element, client-side extension validation (.xlsx/.csv/.json), `fetch()` POST to `{% url 'upload_catalog' %}` with `FormData` and CSRF token, response handling (redirect on success via `window.location.href`, `showToast(error, 'error')` on failure), loading state toggle (`.uploading` class) on dropzone during upload, multi-file guard (use `files[0]` only). Per FR-001, FR-002, FR-003, FR-016, FR-018.
- [X] T005 [P] [US1] Add contract tests for upload endpoint (new catalog path) in `tests/contract/test_upload.py` — test POST with no file returns 400 error JSON, test POST with unsupported extension (.txt) returns 400 error JSON with message, test POST with valid file structure (mock `load_file`, `bulk_insert`, `find_catalog_by_customer_id` returning `None` for new catalog) returns 200 success JSON with redirect URL, test POST with file that causes `load_file` to raise returns 400 error JSON. Use Django test client with `SimpleUploadedFile`. Import `AUTH_SESSION` from conftest for session injection.
- [X] T006 [P] [US1] Add integration tests for dropzone UI in `tests/integration/test_dropzone_ui.py` — test dropzone element present in navbar (`label.dropzone` with `for="dropzone-input"`), file input with `accept=".xlsx,.csv,.json"`, toast container present, `showToast` function defined in script, upload JS wires fetch to `{% url 'upload_catalog' %}`, dragover/dragleave/drop event listeners present, multi-file guard (`files[0]`). Use Django test Client with session injection and mocked `list_sellers`.

**Checkpoint**: Full US1 functional. Drag-and-drop imports new catalogs, toasts errors, redirects on success.

---

## Phase 3: User Story 2 — Merge into Existing Catalog (Priority: P1)

**Goal**: When the dropped file's customer catalog ID already exists on the server, the system fetches all existing lots, computes a set difference by customer item ID, inserts new lots individually, deletes+recreates changed lots preserving overrides, skips identical lots, and shows a summary toast.

**Independent Test**: Import a catalog file for an existing catalog with overlapping lots. Verify new lots appear, changed lots are updated with file data but retain overrides, unchanged lots remain as-is, and summary toast shows correct counts.

**Depends on**: Phase 2 (US1) — the upload view and UI must exist.

### Implementation for User Story 2

- [X] T007 [US2] Add `fetch_all_lots`, `create_lot`, `delete_lot`, `lots_differ`, and `merge_catalog` to `src/catalog/services.py`:
  - `fetch_all_lots(request, customer_catalog_id)` — paginate through `list_lots_by_catalog(request, customer_catalog_id, page, page_size=100)` collecting all `LotDto` items until `has_next_page` is false. Return list of all `LotDto`.
  - `create_lot(request, add_lot_request)` — call `get_catalog_api(request).lots.create(add_lot_request)`, return created `LotDto`.
  - `delete_lot(request, lot_id)` — call `get_catalog_api(request).lots.delete(lot_id)`.
  - `lots_differ(file_initial_data, server_initial_data)` — compare 7 dimensional/shipping fields (`qty`, `l`, `w`, `h`, `wgt`, `cpack`, `force_crate`) between two `LotDataDto` objects. Normalize `None` to `0` for numeric fields, `None` to `""` for string fields, `None` to `False` for bool. Return `True` if any field differs.
  - `merge_catalog(request, bulk_request, catalog_id)` — implements the merge flow per data-model.md: (1) call `fetch_all_lots` to get server lots, (2) build `{customer_item_id: LotDto}` lookup for server lots, (3) build `{customer_item_id: BulkInsertLotRequest}` for file lots (first occurrence only — deduplicate), (4) iterate file lots: if not in server → `create_lot` with `AddLotRequest` (empty overrides, catalogs=[LotCatalogDto(catalog_id, lot_number)]); if in server and `lots_differ` → save `overriden_data` from server lot, `delete_lot`, `create_lot` with `AddLotRequest` (preserved overrides); if identical → skip, (5) wrap each individual lot operation in try/except — on failure, increment `failed` counter and append error message, continue, (6) return dict `{added, updated, unchanged, failed, errors, catalog_id}`. Per FR-008 through FR-014, FR-017, research R2/R3/R4/R5/R6.
- [X] T008 [US2] Extend `upload_catalog` view in `src/catalog/views/imports.py` to call merge when catalog exists — after parsing file and checking `find_catalog_by_customer_id()`: if catalog ID is found, call `services.merge_catalog(request, bulk_request, catalog_id)`, build `JsonResponse` with `{success: true, redirect: "/events/<catalog_id>/", merge: {added, updated, unchanged, failed}}`, include `warnings` list if `failed > 0`. If `fetch_all_lots` fails entirely (raises exception before any lot processing), return `{success: false, error: "Merge failed: unable to fetch existing lots"}`. Per contract MergeResponse schema and FR-006, FR-015.
- [X] T009 [US2] Update dropzone JavaScript in `src/catalog/templates/catalog/base.html` to handle merge response — after successful fetch response, check if `data.merge` exists: if so, build summary message string "Added: {added}, Updated: {updated}, Unchanged: {unchanged}" (append ", Failed: {failed}" only if failed > 0), call `showToast(summaryMsg, 'success')`, then redirect via `window.location.href = data.redirect`. Per FR-015, FR-016.
- [X] T010 [P] [US2] Add unit tests for merge logic in `tests/unit/test_merge.py` — test `lots_differ`: identical lots return False, lots with different qty return True, lots with None vs 0 return False (normalization), lots with different cpack return True. Test `merge_catalog` with mocked API calls: (1) all-new lots scenario (3 file lots, 0 server lots → added=3), (2) all-unchanged scenario (same data → unchanged=N), (3) mixed scenario (1 new, 1 changed, 1 unchanged → correct counts), (4) override preservation (changed lot has overrides → recreated lot's AddLotRequest includes those overrides), (5) best-effort failure (mock `create_lot` to raise for one lot → failed=1, others succeed), (6) duplicate customer_item_id in file (only first processed). Use `SimpleNamespace` for mock objects per memory note.
- [X] T011 [P] [US2] Add contract tests for upload endpoint (merge path) in `tests/contract/test_upload.py` — extend existing test file: test POST with valid file where `find_catalog_by_customer_id` returns an existing catalog ID (mock `merge_catalog` to return summary dict) → returns 200 JSON with `merge` key containing `{added, updated, unchanged, failed}` and `redirect` URL. Test POST where merge fetch fails → returns 500 error JSON. Use same test client and session setup as US1 tests.

**Checkpoint**: Full merge functional. Re-importing an existing catalog diffs lots, preserves overrides, shows summary.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Edge case hardening and validation.

- [X] T012 Verify dropzone handles multiple-file drops by processing only the first file — confirm in the JS `drop` handler in `src/catalog/templates/catalog/base.html` that `files[0]` is used. Verify loading state (`.uploading` class) disables additional drops during processing via `pointer-events: none` in CSS.
- [X] T013 Run quickstart.md manual validation — start dev server, test happy path for US1 (valid new file → redirect), error paths (invalid file → toast), and US2 (re-import existing catalog → merge summary toast + redirect) per `specs/019-restore-catalog-import/quickstart.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately
  - T001 and T002 are fully parallel (different files, no shared state)
- **User Story 1 (Phase 2)**: Depends on Phase 1 completion
  - T003 depends on T002 (URL route must exist for view to be reachable)
  - T004 depends on T001 (CSS must exist) and T002 (URL name must exist for `{% url %}` tag)
  - T005 depends on T003 (tests the view)
  - T006 depends on T004 (tests the template)
  - T005 and T006 are parallel with each other once their deps are met
- **User Story 2 (Phase 3)**: Depends on Phase 2 completion
  - T007 has no file-level dependencies but must be written after US1 view exists (for context)
  - T008 depends on T007 (calls merge_catalog service)
  - T009 depends on T008 (JS must handle new response format)
  - T010 depends on T007 (tests the service functions)
  - T011 depends on T008 (tests the merge view path)
  - T010 and T011 are parallel with each other once their deps are met
- **Polish (Phase 4)**: Depends on Phase 3 completion
  - T012 refines T004/T009 JS behavior
  - T013 validates the full feature

### Within User Story 1

```
T001 ──┐
       ├──→ T003 ──→ T004
T002 ──┘       │        │
               ↓        ↓
             T005      T006
        (parallel with T006)
```

### Within User Story 2

```
T007 ──→ T008 ──→ T009
  │         │
  ↓         ↓
T010      T011
(parallel with T011)
```

### Parallel Opportunities

```bash
# Phase 1 — launch together:
Task: "Add dropzone CSS to src/catalog/static/catalog/styles.css"
Task: "Add upload route to src/catalog/urls.py"

# Phase 2 — T005 and T006 can overlap once T003+T004 are done:
Task: "Contract tests for upload endpoint in tests/contract/test_upload.py"
Task: "Integration tests for dropzone UI in tests/integration/test_dropzone_ui.py"

# Phase 3 — T010 and T011 can overlap once T007+T008 are done:
Task: "Unit tests for merge logic in tests/unit/test_merge.py"
Task: "Contract tests for merge path in tests/contract/test_upload.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1: Foundational (T001, T002 in parallel)
2. Complete Phase 2: User Story 1 (T003 → T004 → T005 + T006)
3. **STOP and VALIDATE**: Test via quickstart.md — new catalog import only
4. Deploy/demo if ready — dropzone is functional for new catalogs

### Full Feature (Add US2)

5. Complete Phase 3: User Story 2 (T007 → T008 → T009 + T010 + T011)
6. **STOP and VALIDATE**: Test merge via quickstart.md
7. Complete Phase 4: Polish (T012, T013)

### Summary

| Metric | Value |
|--------|-------|
| Total tasks | 13 |
| User Story 1 tasks | 4 (T003–T006) |
| User Story 2 tasks | 5 (T007–T011) |
| Foundational tasks | 2 (T001–T002) |
| Polish tasks | 2 (T012–T013) |
| Parallel opportunities | 3 pairs (Phase 1, Phase 2 tests, Phase 3 tests) |
| Files modified | 5 existing |
| Files created | 3 new test files |

---

## Notes

- [P] tasks = different files, no dependencies
- [US1]/[US2] label maps task to specific user story for traceability
- Commit after each task or logical group
- US2 depends on US1 — the merge path extends the upload view created in US1
- All backend changes are additive (new functions, extended view) — no modifications to existing behavior
- `SimpleNamespace` (not `MagicMock`) for test fixtures due to `LocMemCache` pickling
- `AUTH_SESSION` from `tests/conftest.py` for session injection in tests

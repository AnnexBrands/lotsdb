# Tasks: Catalog Dropzone

**Input**: Design documents from `/specs/002-catalog-dropzone/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.yaml

**Tests**: Included per constitution requirement (Artifact Harmony — tests are first-class artifacts).

**Organization**: Single user story (US1) with foundational backend tasks separated to enable parallel frontend work.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Backend service helper and CSS that must exist before the main UI and view can be wired together.

- [X] T001 [P] Add `find_catalog_by_customer_id` service method to `src/catalog/services.py` — accepts `request` and `customer_catalog_id` string, calls `api.catalogs.list(CustomerCatalogId=customer_catalog_id)`, returns the first catalog's internal `id` or `None`. Per research R2.
- [X] T002 [P] Add dropzone and toast CSS to `src/catalog/static/catalog/styles.css` — add `.dropzone` styles (nav element styling, `.dragover` active state highlight), `.toast-container` (fixed top-right), `.toast` (slide-in animation, `.toast-error` red, `.toast-success` green, auto-fade-out). Per research R4.

**Checkpoint**: Service helper callable, CSS ready for frontend.

---

## Phase 2: User Story 1 — Drop File to Import Catalog (Priority: P1) 🎯 MVP

**Goal**: A user can drag-and-drop a catalog file onto the "Add Catalog" area in the navbar. Valid files are imported and the user is redirected to the event page. Invalid files show a toast error.

**Independent Test**: Drop a valid `.xlsx` catalog file → redirected to `/events/<id>/`. Drop a `.txt` file → toast error appears, page unchanged.

### Implementation for User Story 1

- [X] T003 [US1] Add `upload_catalog` view to `src/catalog/views/imports.py` — POST-only JSON endpoint: receive `request.FILES["file"]`, validate extension against `SUPPORTED_EXTENSIONS`, write to `tempfile.NamedTemporaryFile` with correct suffix, call `load_file()`, call `services.bulk_insert()`, call `services.find_catalog_by_customer_id()` to resolve redirect URL, return `JsonResponse` with `{success, redirect}` or `{success, error}`. Per contract `POST /imports/upload/` and research R3, R5, R6.
- [X] T004 [US1] Add URL route `path("imports/upload/", upload_catalog, name="upload_catalog")` to `src/catalog/urls.py` and add `upload_catalog` to the imports in the URL conf.
- [X] T005 [US1] Add dropzone HTML, toast container, and drag-and-drop JavaScript to `src/catalog/templates/catalog/base.html` — (1) Add dropzone element in navbar between the "Import" link and the search form: `<label class="dropzone" for="dropzone-input">Add Catalog<input type="file" id="dropzone-input" ...></label>`. (2) Add `<div id="toast-container" class="toast-container"></div>` before closing `</body>`. (3) Add inline `<script>` implementing: `showToast(msg, type)` function, click-to-browse via hidden file input, `dragover`/`dragleave`/`drop` event handlers on the dropzone element, client-side extension validation (.xlsx/.csv/.json), `fetch()` POST to `{% url 'upload_catalog' %}` with `FormData`, response handling (redirect on success, toast on error), loading state toggle on dropzone during upload. Per research R3, R4, R5.
- [X] T006 [US1] Add contract tests for upload endpoint in `tests/contract/test_upload.py` — test POST with no file returns error JSON, test POST with unsupported extension returns error JSON, test POST with valid file structure (mock `load_file` and `bulk_insert` and `find_catalog_by_customer_id`) returns success JSON with redirect URL, test POST with file that causes `load_file` to raise returns error JSON. Use Django test client with `SimpleUploadedFile`.

**Checkpoint**: Full feature functional. Drag-and-drop imports catalogs, toasts errors, redirects on success.

---

## Phase 3: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling and validation.

- [X] T007 Verify dropzone handles multiple-file drops by processing only the first file — enforce in the JS `drop` handler in `src/catalog/templates/catalog/base.html` (use `e.dataTransfer.files[0]` only). Verify loading state disables additional drops during processing.
- [X] T008 Run quickstart.md manual validation — start dev server, test happy path (valid file → redirect) and error path (invalid file → toast) per `specs/002-catalog-dropzone/quickstart.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately
  - T001 and T002 are fully parallel (different files, no shared state)
- **User Story 1 (Phase 2)**: Depends on Phase 1 completion
  - T003 depends on T001 (uses `find_catalog_by_customer_id`)
  - T004 depends on T003 (imports the new view)
  - T005 depends on T002 (CSS must exist) and T004 (URL name must exist for `{% url %}`)
  - T006 depends on T003 (tests the view)
- **Polish (Phase 3)**: Depends on Phase 2 completion
  - T007 refines T005 JS behavior
  - T008 validates the full feature

### Within User Story 1

```
T001 ──┐
       ├──→ T003 → T004 ──→ T005
T002 ──┘                      │
                              ↓
                    T006 (parallel with T005 once T003 exists)
```

### Parallel Opportunities

```bash
# Phase 1 — launch together:
Task: "Add find_catalog_by_customer_id to src/catalog/services.py"
Task: "Add dropzone and toast CSS to src/catalog/static/catalog/styles.css"

# Phase 2 — T005 and T006 can overlap once T003+T004 are done:
Task: "Add dropzone HTML and JS to src/catalog/templates/catalog/base.html"
Task: "Add contract tests to tests/test_upload.py"
```

---

## Implementation Strategy

### MVP First (Single Story)

1. Complete Phase 1: Foundational (T001, T002 in parallel)
2. Complete Phase 2: User Story 1 (T003 → T004 → T005 + T006)
3. **STOP and VALIDATE**: Test via quickstart.md
4. Complete Phase 3: Polish (T007, T008)

### Summary

| Metric | Value |
|--------|-------|
| Total tasks | 8 |
| User Story 1 tasks | 4 (T003–T006) |
| Foundational tasks | 2 (T001–T002) |
| Polish tasks | 2 (T007–T008) |
| Parallel opportunities | 2 (Phase 1 pair, Phase 2 T005+T006 pair) |
| Files modified | 4 existing + 1 new test file |

---

## Phase 4: PR Review Fixes

**Purpose**: Address Codex reviewer feedback — missing automated tests for AS1/AS2, spec-example fixtures, and test evidence.

- [X] T009 [P] Create shared test fixtures in `tests/conftest.py` — `auth_session` fixture (session dict from spec examples), `sample_bulk_request` fixture (MagicMock BulkInsertRequest with `customer_catalog_id="123456"` from data-model examples). Exported as `AUTH_SESSION` constant for TestCase-based tests.
- [X] T010 Add UI/template integration tests in `tests/integration/test_dropzone_ui.py` — covers AS1 (dropzone element present, file input with accept attribute), AS2 (dragover/dragleave/drop event listeners, classList.add/remove('dragover')), toast container, showToast function, fetch upload JS, success redirect, error toast, and multi-file (files[0]) handling. Uses Django test Client with session injection and mocked `list_sellers`.
- [X] T011 Refactor contract tests in `tests/contract/test_upload.py` — convert from Django TestCase to pytest class, import `AUTH_SESSION` from conftest, use `auth_session` fixture via injection. All 6 original test assertions preserved.

**Checkpoint**: 16 tests pass (10 integration + 6 contract). Test output included in PR body as evidence.

---

## Notes

- [P] tasks = different files, no dependencies
- [US1] label maps task to User Story 1 for traceability
- Commit after each task or logical group
- The feature is a single MVP story — no incremental story delivery needed
- All backend changes are additive (new function/view/route) — no modifications to existing behavior

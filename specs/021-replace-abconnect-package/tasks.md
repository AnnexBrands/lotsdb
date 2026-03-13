# Tasks: Replace ABConnectTools with AB SDK

**Input**: Design documents from `/specs/021-replace-abconnect-package/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Remove old package, install replacement

- [x] T001 Uninstall ABConnectTools and install AB SDK as editable package: `.venv/bin/pip uninstall -y ABConnectTools && .venv/bin/pip install -e /usr/src/pkgs/AB`; verify with `from ab.client import ABConnectAPI`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core auth bridge and exception handling — MUST complete before any user story work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Update `login()` function in src/catalog/services.py: replace `ABConnectAPI(request=request, username=username, password=password)` with new SDK init pattern — instantiate `ABConnectAPI(request=request)`, then mutate `api._settings.username` and `api._settings.password` with form-provided credentials before first API call triggers auth. Update import from `from ABConnect import ABConnectAPI` to `from ab.client import ABConnectAPI`. Change session key check from `"abc_token"` to `"ab_token"` (lines ~22-33, ~49)
- [x] T003 Update `get_catalog_api()` in src/catalog/services.py: change from `ABConnectAPI(request=request).catalog` to `ABConnectAPI(request=request)` — cache the top-level client on `request._catalog_api` instead of the `.catalog` sub-object (lines ~36-44)
- [x] T004 [P] Update exception imports in src/catalog/views/auth.py: replace `from ABConnect.exceptions import LoginFailedError, ABConnectError` with `from ab.exceptions import AuthenticationError, ABConnectError`; update the `except LoginFailedError` catch block to `except AuthenticationError`
- [x] T005 [P] Update exception imports in src/catalog/views/panels.py: replace `from ABConnect.exceptions import ABConnectError` with `from ab.exceptions import ABConnectError`
- [x] T006 [P] Update exception imports in src/catalog/views/sellers.py: replace `from ABConnect.exceptions import ABConnectError` with `from ab.exceptions import ABConnectError`
- [x] T007 [P] Update mock paths in tests/unit/test_login_bridge.py: change all `@patch("catalog.services.ABConnectAPI")` (or equivalent) mock targets to point to the new `ab.client.ABConnectAPI` import path; update any `LoginFailedError` mock references to `AuthenticationError`

**Checkpoint**: Auth flow works with new SDK, all exception handling updated, tests mock correct paths

---

## Phase 3: User Story 1 — Migrate to New AB SDK (Priority: P1) 🎯 MVP

**Goal**: All existing catalog API interactions (sellers, catalogs, lots, bulk insert, file loading) work identically through the new AB SDK with no ABConnect references remaining

**Independent Test**: Login → browse sellers → open event → view lots → edit lot override → import catalog → verify all operations succeed

### Implementation for User Story 1

- [x] T008 [US1] Update all seller service methods in src/catalog/services.py: change `api.sellers.list(page_number=page, page_size=page_size, **filters)` to use new SDK signature — `page_number=` → `page=`; adapt filter params (`CustomerDisplayId`, `Name`) to work with new SDK (pass as raw query params if SDK lacks filter support). Affects: `list_sellers()` (~lines 71-89), `get_seller()` (~line 92-94), `find_seller_by_display_id()` (~lines 97-103)
- [x] T009 [US1] Update all catalog service methods in src/catalog/services.py: change `api.catalogs.*` to `api.catalog.*` (singular); update `page_number=` → `page=`; adapt filter params (`SellerIds`, `CustomerCatalogId`, `Title`). Affects: `list_catalogs()` (~lines 109-164), `get_catalog()` (~line 167-169), `find_catalog_by_customer_id()` (~lines 248-256)
- [x] T010 [US1] Update all lot service methods in src/catalog/services.py: update `page_number=` → `page=`; adapt filter params (`CustomerItemId`, `LotNumber`, `customer_catalog_id`); update model imports from `ABConnect.api.models.catalog` to `ab.api.models.lots` and `ab.api.models.catalog`. Affects: `list_lots_by_catalog()` (~lines 175-181), `get_lot()` (~line 184-186), `search_lots()` (~lines 485-502), `resolve_item()` (~lines 561-597)
- [x] T011 [US1] Update `save_lot_override()` in src/catalog/services.py: change `from ABConnect.api.models.catalog import UpdateLotRequest, LotDataDto` to new import path `from ab.api.models.lots import LotDataDto, UpdateLotRequest`; since new LotDataDto lacks `cpack`, `notes`, `force_crate` etc., use raw dicts for override merge logic instead of model instantiation (~lines 197-239)
- [x] T012 [US1] Update `merge_catalog()` in src/catalog/services.py: change `from ABConnect.api.models.catalog import AddLotRequest, LotDataDto, LotCatalogDto` to use raw dicts for AddLotRequest since new model lacks `customer_item_id`, `image_links`, `initial_data`, `overriden_data`, `catalogs` fields; update `api.lots.create()` call to pass raw dict; update `lots_differ()` comparison to use raw dict access (~lines 323-482)
- [x] T013 [US1] Update `bulk_insert()` in src/catalog/services.py: change `api.bulk.insert(data)` to `api.catalog.bulk_insert(data=data)` (~lines 242-245)
- [x] T014 [US1] Replace FileLoader in src/catalog/importers.py: remove `from ABConnect import FileLoader`; implement inline file loading — use `openpyxl.load_workbook()` for XLSX, `csv.DictReader` for CSV, `json.load()` for JSON; the `load_file()` function (~lines 239-258) must return the same `list[dict]` of rows that `FileLoader(path).data` returned
- [x] T015 [US1] Update BulkInsert model usage in src/catalog/importers.py: remove imports of `BulkInsertRequest`, `BulkInsertCatalogRequest`, `BulkInsertSellerRequest`, `BulkInsertLotRequest`, `LotDataDto` from `ABConnect.api.models.catalog`; replace with plain dicts matching the same JSON structure — the `CatalogDataBuilder.build()` method (~lines 200-221) must produce a dict-based payload compatible with `api.catalog.bulk_insert(data=...)`
- [x] T016 [P] [US1] Update management command in src/catalog/management/commands/import_catalog.py: change `from ABConnect import ABConnectAPI` to `from ab.client import ABConnectAPI`; update `api.catalog.bulk.insert(request)` to `api.catalog.bulk_insert(data=request)` (~lines 50, 67)
- [x] T017 [P] [US1] Update recovery views in src/catalog/views/recovery.py: change `from ABConnect.api.models.catalog import AddLotRequest` to use raw dict (since new AddLotRequest lacks needed fields) or import from `ab.api.models.lots`; update `AddLotRequest.model_validate()` calls to work with new model or raw dicts (~lines 1, 56)
- [x] T018 [US1] Verify zero ABConnect references remain: grep the entire codebase for `ABConnect`, `ABConnectTools`, `from ABConnect`, `import ABConnect`; remove any residual references in comments, docstrings, or code
- [x] T019 [US1] Run full test suite (`.venv/bin/python -m pytest tests/ -v`) and fix any failures caused by the migration; ensure all existing tests pass with updated imports and mock paths

**Checkpoint**: All existing workflows function identically with new SDK. No ABConnect references remain. All tests pass.

---

## Phase 4: User Story 2 — Bulk Insert Begins with Empty Overrides (Priority: P1)

**Goal**: Bulk insert payloads for newly imported lots contain zero pre-populated overrides — initial data only

**Independent Test**: Import a catalog spreadsheet, inspect the bulk insert request payload — each lot's `overriden_data` must be `[]`

### Implementation for User Story 2

- [x] T020 [US2] Modify `CatalogDataBuilder._add_lot()` in src/catalog/importers.py: remove the `override_data = LotDataDto(...)` construction (~lines 182-186) and change `overriden_data=[override_data]` to `overriden_data=[]` (or equivalent dict key) in the lot dict (~line 194); keep `initial_data` populated with full dimensional/descriptive data from spreadsheet
- [x] T021 [US2] Verify `merge_catalog()` in src/catalog/services.py correctly preserves existing overrides when re-creating changed lots: the delete-and-recreate flow (~lines 418-438) must carry forward `server_lot.overriden_data` (not file overrides) so user-made changes survive re-import

**Checkpoint**: New imports produce lots with empty overrides. Existing overrides preserved on re-import.

---

## Phase 5: User Story 3 — Scan for Lot Images (Priority: P2)

**Goal**: Image URLs included in bulk insert and merge catalog payloads are verified by probing the CDN; scanning stops after 3 consecutive non-2xx responses

**Independent Test**: Import a catalog, verify image_links arrays contain only URLs confirmed to exist via HTTP HEAD probes

### Implementation for User Story 3

- [x] T022 [US3] Implement `scan_lot_images(house_id, catalog_id, lot_id)` function in src/catalog/services.py: construct URL pattern `https://s3.amazonaws.com/static2.liveauctioneers.com/{house_id}/{catalog_id}/{lot_id}_{n}_m.jpg` starting at n=1; send HTTP HEAD with 5s timeout; collect 2xx URLs; count consecutive non-2xx (4xx, 5xx, network errors all count); stop after 3 consecutive failures or n>200; return `list[str]` of valid URLs; log warnings for network errors
- [x] T023 [US3] Implement `scan_images_for_catalog(lots, max_workers=10)` function in src/catalog/services.py: accept list of `(house_id, catalog_id, lot_id)` tuples; use `ThreadPoolExecutor(max_workers)` to call `scan_lot_images` in parallel across lots; return `dict[int, list[str]]` mapping lot_id to valid URLs; log summary of total lots scanned and images found
- [x] T024 [US3] Integrate image scanner into `CatalogDataBuilder._add_lot()` in src/catalog/importers.py: replace static `build_image_url()` call (~line 188) with call to `scan_lot_images(seller_id, catalog_id, lot_id)`; set lot's `image_links` to the returned list of verified URLs; remove `build_image_url()` function and `IMAGE_URL_TEMPLATE` constant if no longer used
- [x] T025 [US3] Integrate image scanner into `merge_catalog()` in src/catalog/services.py: when creating new lots or re-creating changed lots (~lines 371-390, 418-438), call `scan_lot_images()` to get verified image URLs instead of using `file_lot.image_links` passthrough

**Checkpoint**: Only verified image URLs appear in bulk insert and merge payloads. Non-existent images are excluded.

---

## Phase 6: User Story 4 — Document Compatibility Gaps (Priority: P2)

**Goal**: AB SDK maintainers receive a clear document of all missing capabilities needed by lotsdb

**Independent Test**: Read external_deps.md — each gap has description, usage context, and suggested SDK change

### Implementation for User Story 4

- [x] T026 [P] [US4] Write external_deps.md at project root documenting all AB SDK compatibility gaps identified during migration. Include these gaps with severity, current workaround, and requested SDK change: (1) CRITICAL — per-request credentials: constructor must accept optional username/password for multi-user web apps; (2) CRITICAL — filter kwargs on list endpoints: sellers.list(), catalog.list(), lots.list() must accept filter parameters (SellerIds, CustomerDisplayId, CustomerItemId, LotNumber, customer_catalog_id); (3) MEDIUM — FileLoader: spreadsheet/CSV/JSON file loading utility; (4) MEDIUM — BulkInsert nested models: BulkInsertCatalogRequest, BulkInsertSellerRequest, BulkInsertLotRequest; (5) MEDIUM — LotDataDto missing fields: cpack, notes, force_crate, noted_conditions, do_not_tip, item_id, commodity_id; (6) LOW — LotCatalogDto model; (7) LOW — AddLotRequest missing fields (customer_item_id, image_links, initial_data, overriden_data, catalogs)

**Checkpoint**: external_deps.md exists and is actionable for AB SDK maintainers.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [x] T027 Run `ruff check .` from src/ and fix any linting issues introduced by migration
- [x] T028 Validate quickstart.md steps: confirm file paths, env var names, setup commands, and troubleshooting notes match the actual implementation
- [x] T029 Final review: re-read spec.md acceptance scenarios and verify each is satisfied by the implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — BLOCKS US2 and US3 (modifies same files)
- **US2 (Phase 4)**: Depends on Phase 3 (modifies importers.py and services.py after US1)
- **US3 (Phase 5)**: Depends on Phase 3 (modifies importers.py and services.py after US1); independent of US2
- **US4 (Phase 6)**: Independent — can run in parallel with any phase after Phase 2 (writes new file only)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (Phase 2). Blocks US2 and US3.
- **US2 (P1)**: Depends on US1 (Phase 3). Independent of US3.
- **US3 (P2)**: Depends on US1 (Phase 3). Independent of US2.
- **US4 (P2)**: Independent of all other stories — can start after Phase 2.

### Within Each User Story

- Services before integration points
- Core logic before edge case handling
- Verify after each story checkpoint

### Parallel Opportunities

- **Phase 2**: T004, T005, T006, T007 can all run in parallel (different files)
- **Phase 3**: T016, T017 can run in parallel with each other (different files), and parallel with T014-T015 (different files)
- **Phase 6**: T026 can run in parallel with any Phase 3+ task (new file, no conflicts)

---

## Parallel Example: Phase 2 (Foundational)

```bash
# These can all run in parallel (different files):
Task T004: "Update exception imports in src/catalog/views/auth.py"
Task T005: "Update exception imports in src/catalog/views/panels.py"
Task T006: "Update exception imports in src/catalog/views/sellers.py"
Task T007: "Update mock paths in tests/unit/test_login_bridge.py"
```

## Parallel Example: Phase 3 (US1 - late stage)

```bash
# These can run in parallel (different files):
Task T016: "Update management command in src/catalog/management/commands/import_catalog.py"
Task T017: "Update recovery views in src/catalog/views/recovery.py"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002-T007)
3. Complete Phase 3: US1 (T008-T019)
4. **STOP and VALIDATE**: Login, browse, edit, import — all work with new SDK
5. Deploy if ready — app is fully functional on new SDK

### Incremental Delivery

1. Setup + Foundational + US1 → App works on new SDK (MVP!)
2. Add US2 → Import data integrity fixed (empty overrides)
3. Add US3 → Import includes only verified images
4. Add US4 → SDK maintainers have gap documentation
5. Polish → Linting, quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 and US3 both modify files touched by US1 — must complete US1 first
- US4 writes a new file and can run at any time after Phase 2
- Commit after each phase or logical group
- Stop at any checkpoint to validate story independently

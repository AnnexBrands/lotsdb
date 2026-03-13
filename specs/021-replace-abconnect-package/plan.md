# Implementation Plan: Replace ABConnectTools with AB SDK

**Branch**: `021-replace-abconnect-package` | **Date**: 2026-03-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/021-replace-abconnect-package/spec.md`

## Summary

Replace the deprecated ABConnectTools package (`ABConnect`) with the new AB SDK (`ab`) across all catalog API interactions. Update all imports, authentication flow, endpoint call patterns, and exception handling. Fix bulk insert to use empty overrides. Add image URL scanning that probes the CDN and stops after 3 consecutive non-2xx responses. Replace `FileLoader` with inline openpyxl/stdlib logic. Document all SDK compatibility gaps in `external_deps.md` for the AB SDK maintainers.

## Technical Context

**Language/Version**: Python 3.14, Django 5.2
**Primary Dependencies**: AB SDK 0.1.0 (editable install from `/usr/src/pkgs/AB`), HTMX 2.0.4 (CDN), redis 7.1.1, openpyxl (for FileLoader replacement)
**Storage**: SQLite3 (sessions + Django User table), Redis (cache)
**Testing**: pytest (`.venv/bin/python -m pytest tests/ -v`)
**Target Platform**: Linux server (gunicorn)
**Project Type**: Web application (Django monolith)
**Performance Goals**: Image scanning must not block imports unreasonably — parallelize across lots using ThreadPoolExecutor (max_workers=10)
**Constraints**: Thread-safe API instances for concurrent lot fetching; per-user cache key namespacing
**Scale/Scope**: ~10 files modified, 1 new file (`external_deps.md`), 1 new capability (image scanner)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate (Phase 0)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Artifact Harmony | PASS | Spec, contracts, data model, tests, and code will all be updated in same changeset |
| II. Executable Knowledge | PASS | Existing tests updated; new tests for image scanner and empty overrides |
| III. Contracted Boundaries | PASS | SDK interface contract defined in `contracts/sdk-interface.md`; image scanner contract in `contracts/image-scanner.md` |
| IV. Versioned Traceability | PASS | Feature branch with spec-first workflow |
| V. Communicable Truth | PASS | quickstart.md covers setup, verification, and troubleshooting |

### Post-Design Gate (Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Artifact Harmony | PASS | data-model.md documents all entity changes; contracts define SDK interface |
| II. Executable Knowledge | PASS | Contract tests verify SDK integration; unit tests verify image scanner logic |
| III. Contracted Boundaries | PASS | 2 contract files define all interfaces; gaps documented in external_deps.md |
| IV. Versioned Traceability | PASS | All changes on feature branch with clear commit history |
| V. Communicable Truth | PASS | quickstart.md updated with new env vars, setup steps, troubleshooting |

No violations. Complexity tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/021-replace-abconnect-package/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── sdk-interface.md
│   └── image-scanner.md
├── checklists/
│   └── requirements.md
└── tasks.md              (Phase 2 — /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── catalog/
│   ├── services.py          # API accessor, CRUD wrappers, merge logic, image scanning
│   ├── importers.py          # FileLoader replacement, empty overrides, image scanning integration
│   ├── views/
│   │   ├── auth.py           # AuthenticationError handling
│   │   ├── panels.py         # ABConnectError import path
│   │   ├── sellers.py        # ABConnectError import path
│   │   └── recovery.py       # AddLotRequest import path
│   └── management/
│       └── commands/
│           └── import_catalog.py  # API init + bulk insert path
├── config/
│   └── settings.py           # No changes expected

tests/
└── unit/
    └── test_login_bridge.py  # Mock paths updated

external_deps.md              # NEW — SDK gap documentation (project root)
```

**Structure Decision**: Existing Django web app structure. No new directories. All changes within existing `src/catalog/` module plus new `external_deps.md` at project root.

## Implementation Approach

### Phase 1: Package Swap & Import Migration (FR-001, FR-008)

1. Uninstall ABConnectTools, install AB SDK as editable
2. Update all `from ABConnect` imports to `from ab` equivalents
3. Update `get_catalog_api()` to return top-level `ABConnectAPI` instance
4. Update all accessor paths: `api.catalogs.*` → `api.catalog.*`, `api.bulk.insert()` → `api.catalog.bulk_insert()`

### Phase 2: Authentication Bridge (FR-002, FR-004)

1. Update `login()` to work with new SDK auth flow (credential injection workaround)
2. Update session key references: `"abc_token"` → `"ab_token"`
3. Update exception handling: `LoginFailedError` → `AuthenticationError`
4. Update all `ABConnectError` import paths in views

### Phase 3: Endpoint Call Adaptation (FR-003, FR-010)

1. Update all `list()` calls: `page_number=` → `page=`
2. Adapt filter parameter passing for SDK gaps (raw query params or workaround)
3. Verify thread safety of new SDK client instances
4. Update concurrent lot fetching to use per-thread `ABConnectAPI` instances

### Phase 4: FileLoader Replacement (FR-009)

1. Replace `from ABConnect import FileLoader` with openpyxl-based loader
2. Implement `load_file()` using openpyxl for XLSX, stdlib csv for CSV, stdlib json for JSON
3. Preserve existing `CatalogDataBuilder` interface (no changes needed there)

### Phase 5: Empty Overrides (FR-005)

1. Modify `CatalogDataBuilder._add_lot()` to set `overriden_data=[]` instead of duplicating initial data
2. Verify `merge_catalog()` preserves overrides correctly for existing lots

### Phase 6: Image Scanner (FR-006)

1. Implement `scan_lot_images()` function with HEAD probing and 3-consecutive-failure stop
2. Implement `scan_images_for_catalog()` with ThreadPoolExecutor parallelization
3. Integrate into `CatalogDataBuilder._add_lot()` (bulk insert path)
4. Integrate into `merge_catalog()` (merge path)

### Phase 7: Gap Documentation (FR-007)

1. Write `external_deps.md` with all identified SDK gaps
2. Include: per-request credentials, filter kwargs, FileLoader, bulk insert models, LotDataDto fields

### Phase 8: Test Updates

1. Update mock paths in `test_login_bridge.py`
2. Add tests for image scanner (mock HTTP responses)
3. Add tests for empty overrides in bulk insert
4. Verify all existing tests pass

# PR Analysis: 021 — Replace ABConnectTools with AB SDK

**Branch**: `021-replace-abconnect-package`
**Date**: 2026-03-13
**Files changed**: 13 modified, 1 new (`external_deps.md`)
**Lines**: +401 / -228

---

## Summary

Replaces the deprecated ABConnectTools package (`ABConnect`) with the new AB SDK (`ab` v0.1.0) across all catalog API interactions. Fixes bulk insert to begin with empty overrides. Adds image URL scanning that probes the CDN until 3 consecutive non-2xx responses. Replaces `FileLoader` with inline openpyxl/csv/json loaders. Documents all SDK compatibility gaps for the AB SDK maintainers.

---

## Spec Compliance

| Requirement | Status | Notes |
|---|---|---|
| FR-001: Replace all ABConnect imports | PASS | All imports now use `from ab.*` |
| FR-002: Auth bridge via AB SDK | PASS | Credential injection workaround documented |
| FR-003: Seller/catalog/lot CRUD | PASS | Via `_filtered_list` helper for filter support |
| FR-004: Error handling with new exceptions | PASS | `AuthenticationError`, `ABConnectError` |
| FR-005: Empty overrides on bulk insert | PASS | `overriden_data=[]` in both importers and merge |
| FR-006: Image URL scanning | PASS | HEAD probes, 3-consecutive-failure stop, 200 max |
| FR-007: external_deps.md | PASS | 7 gaps documented with severity + workarounds |
| FR-008: Zero ABConnect residuals | PASS | Only `ABConnectError`/`ABConnectAPI` class names remain (from new SDK) |
| FR-009: Spreadsheet file loading | PASS | openpyxl for XLSX, csv.DictReader for CSV, json for JSON |
| FR-010: Thread-safe concurrent fetching | PASS | Per-thread API instances unchanged |

---

## Findings

### BUG — `conftest.py` session key not updated (35 test failures)

**File**: `tests/conftest.py:9`
**Severity**: Blocking — causes 35 test failures across 4 test modules
**Root cause**: `AUTH_SESSION` uses `"abc_token"` but `services.is_authenticated()` now checks `"ab_token"`. All tests using this fixture fail auth middleware and get redirected to `/login/`.
**Fix**: Change `"abc_token"` to `"ab_token"` in `AUTH_SESSION`.
**Affected tests**: `test_recovery.py` (8), `test_search.py` (3), `test_upload.py` (12), `test_dropzone_ui.py` (12).

### OBSERVATION — Private attribute access in SDK workarounds

**Files**: `services.py:33-36, 69-93, 119, 148, 189, 235, 296, 548, 552, 701`

The `_filtered_list()` helper accesses `endpoint._client` (private) to bypass SDK list methods that don't support filter params. The login flow accesses `api._settings` and `api._catalog._ensure_token()` (private). All workarounds are documented in `external_deps.md` gaps #1 and #2 with clear requests for SDK changes. Acceptable given SDK v0.1.0 state.

### OBSERVATION — Sequential image scanning in import path

**Files**: `importers.py:215`, `services.py:441, 485`

`CatalogDataBuilder._add_lot()` calls `scan_lot_images()` synchronously per lot. For large imports (200+ lots), each lot probes 1-200 CDN URLs sequentially. The parallel `scan_images_for_catalog()` function exists (services.py:604-634) but isn't used in the importer — it would require restructuring the row-by-row builder pattern to batch all lots first, then scan images in parallel, then assign results.

The merge path (`merge_catalog`) also scans per-lot sequentially.

This is functionally correct per spec requirements. A future optimization could batch-scan after building all lots.

### OBSERVATION — Stale middleware comment

**File**: `middleware.py:28`

Comment says "abc_token" but this is just a descriptive comment about legacy sessions — the functional code calls `is_authenticated()` which correctly checks `ab_token`. No functional impact.

---

## Architecture Changes

### `_filtered_list()` helper (services.py:69-93)

New function that bypasses SDK list endpoints to pass arbitrary query params directly. Uses SDK's internal HTTP client and manually constructs `PaginatedList` from the raw response. Used by all list-with-filter call sites (sellers, catalogs, lots, search, resolve).

### FileLoader replacement (importers.py:98-137)

Three inline loaders (`_load_xlsx`, `_load_csv`, `_load_json`) replace ABConnectTools' `FileLoader`. Uses openpyxl for XLSX (lazy import), stdlib csv/json. `_load_data()` dispatches by file extension.

### Image scanner (services.py:572-634)

Two new functions:
- `scan_lot_images(house_id, catalog_id, lot_id)` — sequential HEAD probe, stops after 3 consecutive failures or 200 positions
- `scan_images_for_catalog(lots, max_workers=10)` — ThreadPoolExecutor parallelization across lots (currently unused, available for future optimization)

### Dict-based API payloads

All Pydantic model construction (`AddLotRequest`, `LotDataDto`, `UpdateLotRequest`, `BulkInsertRequest`, etc.) replaced with raw dicts using camelCase keys matching the API's JSON schema. The SDK's models are too narrow for lotsdb's needs (documented in external_deps.md).

### `_get_field()` helper (services.py:337-341)

Dual-mode field accessor for `lots_differ()` — handles both dict (from file) and object (from API) comparison without requiring callers to normalize first.

---

## Test Changes

| File | Changes |
|---|---|
| `test_panels.py` | 4 tests updated: mock `_filtered_list` instead of `api.*.list` for filter/cache-miss paths |
| `test_middleware_auth.py` | 5 session setups: `abc_token` → `ab_token` |
| `test_login_bridge.py` | Import updated: added `MagicMock` |
| `test_merge.py` | All 8 tests: added `@patch("catalog.services.scan_lot_images")`, dict assertions replace model attribute assertions, file lot helpers return dicts |
| `test_resolve.py` | 4 tests: mock `_filtered_list` instead of `api.lots.list` |

---

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Private SDK attribute access breaks on SDK update | Documented in external_deps.md; SDK v0.1.0 is stable for now |
| Image scanning adds latency to imports | Bounded: 5s timeout per probe, 3-failure stop, 200 max positions |
| Dict payloads bypass type validation | API backend validates; SDK models too narrow anyway |
| `conftest.py` bug blocks all contract/integration tests | Trivial fix: single line change |

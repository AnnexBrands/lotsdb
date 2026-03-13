# AB SDK Compatibility Gaps

**From**: lotsdb project (021-replace-abconnect-package)
**Date**: 2026-03-13
**For**: AB SDK maintainers

This document lists capabilities that the old ABConnectTools package provided but the current AB SDK (`ab` v0.1.0) does not. Each gap includes what lotsdb needs, the current workaround, and the requested SDK change.

---

## 1. Per-Request Credentials in Constructor

**Severity**: CRITICAL

**What lotsdb needs**: Pass username/password at construction time for per-user authentication in a multi-user web app. Each login form submission provides different credentials.

**Old behavior**: `ABConnectAPI(request=request, username=username, password=password)` — credentials accepted as constructor kwargs.

**Current behavior**: Credentials read exclusively from `ABCONNECT_USERNAME` / `ABCONNECT_PASSWORD` environment variables. Process-global env vars are not thread-safe for concurrent logins.

**Current workaround**: Mutate `api._settings.username` and `api._settings.password` post-construction before the first API call triggers authentication. This accesses private attributes.

**Requested SDK change**: Accept optional `username` and `password` keyword arguments in `ABConnectAPI.__init__()`. When provided, use them instead of environment variables for the password grant.

---

## 2. Filter Parameters on List Endpoints

**Severity**: CRITICAL

**What lotsdb needs**: Pass query filter parameters to `sellers.list()`, `catalog.list()`, and `lots.list()` — e.g., `CustomerDisplayId`, `SellerIds`, `CustomerItemId`, `LotNumber`, `customer_catalog_id`.

**Old behavior**: `api.sellers.list(page_number=1, page_size=25, CustomerDisplayId="123")` — arbitrary kwargs forwarded as query params.

**Current behavior**: `list()` methods only accept `page` and `page_size`. The filter param models (`SellerListParams`, `CatalogListParams`, `LotListParams`) exist in the SDK but are not wired into the endpoint methods.

**Current workaround**: Bypass SDK endpoint methods entirely; call `endpoint._client.request("GET", "/Seller", params={...})` directly and manually construct `PaginatedList` from the response.

**Requested SDK change**: Accept `**kwargs` in `list()` methods and merge them into the `params` dict. Or accept a `filters` dict parameter. The param models already define the valid filter fields — wire them in.

---

## 3. FileLoader Utility

**Severity**: MEDIUM

**What lotsdb needs**: Load spreadsheet files (XLSX, CSV, JSON) into `list[dict]` with encoding detection.

**Old behavior**: `from ABConnect import FileLoader; data = FileLoader("file.xlsx").data` — returned rows as list of dicts with automatic format detection, encoding handling, and title field cleanup.

**Current behavior**: No equivalent in the AB SDK.

**Current workaround**: Inline file loading using `openpyxl` for XLSX, `csv.DictReader` for CSV, and `json.load()` for JSON. No encoding detection.

**Requested SDK change**: Provide a `FileLoader` class or utility function in the SDK. Dependencies: `openpyxl` (for XLSX). Optional: `chardet` (for encoding detection).

---

## 4. Bulk Insert Nested Models

**Severity**: MEDIUM

**What lotsdb needs**: Typed Pydantic models for the nested bulk insert structure: `BulkInsertRequest → catalogs[] → BulkInsertCatalogRequest (with lots[] and sellers[])`.

**Old models**: `BulkInsertRequest`, `BulkInsertCatalogRequest`, `BulkInsertSellerRequest`, `BulkInsertLotRequest` — fully typed with validation.

**Current models**: `BulkInsertRequest(catalog_id: int, items: list[dict])` — flat, untyped.

**Current workaround**: Pass raw dicts matching the expected JSON structure via `items`.

**Requested SDK change**: Add `BulkInsertCatalogRequest`, `BulkInsertSellerRequest`, and `BulkInsertLotRequest` models. Update `BulkInsertRequest` to have a `catalogs` field matching the old structure.

---

## 5. LotDataDto Missing Fields

**Severity**: MEDIUM

**What lotsdb needs**: Full lot data model including shipping and classification fields.

**Missing fields** (present in old SDK, absent in new):

| Field | Type | Purpose |
|-------|------|---------|
| `cpack` | str | Case/pack fragility code |
| `notes` | str | Lot notes/description |
| `force_crate` | bool | Force crating flag |
| `noted_conditions` | str | Condition notes |
| `do_not_tip` | bool | Do-not-tip flag |
| `item_id` | int | Item reference ID |
| `commodity_id` | int | Commodity classification ID |

**Current workaround**: Pass these fields as raw dict keys — the API backend accepts them even though the SDK model doesn't define them.

**Requested SDK change**: Add the 7 missing fields to `LotDataDto`.

---

## 6. LotCatalogDto Model

**Severity**: LOW

**What lotsdb needs**: A model representing the lot-to-catalog relationship (catalog_id + lot_number).

**Old model**: `LotCatalogDto(catalog_id=123, lot_number="1A")`

**Current workaround**: Use raw dict `{"catalogId": 123, "lotNumber": "1A"}`.

**Requested SDK change**: Add `LotCatalogDto` model to `ab.api.models.lots`.

---

## 7. AddLotRequest Missing Fields

**Severity**: LOW

**What lotsdb needs**: `AddLotRequest` with fields for `customer_item_id`, `image_links`, `initial_data`, `overriden_data`, and `catalogs`.

**Current model**: `AddLotRequest(catalog_id, lot_number, data)` — only 3 fields.

**Current workaround**: Pass raw dict with all needed fields instead of using the model.

**Requested SDK change**: Expand `AddLotRequest` to include `customer_item_id`, `image_links`, `initial_data`, `overriden_data`, and `catalogs` fields matching the API's actual schema.

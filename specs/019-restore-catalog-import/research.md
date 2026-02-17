# Research: Restore Catalog Import with Merge

**Feature**: 019-restore-catalog-import | **Date**: 2026-02-16

## R1: Current State of Upload Infrastructure

**Decision**: The existing `upload_catalog` view in `src/catalog/views/imports.py` (lines 63-103) is functional but only supports the new-catalog path (bulk insert). It will be extended with merge logic rather than replaced.

**Rationale**: The view already handles file validation, temp file creation, `load_file()` parsing, and JSON response format. Adding a branch after the `find_catalog_by_customer_id` check is the minimal change.

**Findings**:
- View exists at `src/catalog/views/imports.py:63` — `@require_POST def upload_catalog(request)`
- URL route missing from `src/catalog/urls.py` — removed in commit 430cedd (011 UX overhaul)
- Toast JS (`window.showToast`) intact in `src/catalog/templates/catalog/base.html:37-47`
- Toast CSS intact in `src/catalog/static/catalog/styles.css:235-242`
- Dropzone HTML, CSS, and JS fully removed — must be restored

## R2: Lot CRUD API Capabilities

**Decision**: Use individual `LotEndpoint` methods for merge operations: `.create()` for new lots, `.delete()` + `.create()` for changed lots, `.get()` for fetching override data.

**Rationale**: The bulk insert endpoint (`POST /api/Bulk/insert`) creates entire catalog structures and cannot add individual lots to existing catalogs. The individual lot endpoint (`POST /api/Lot`) accepts `AddLotRequest` with `catalogs` list to associate with existing catalogs.

**Findings**:
- `LotEndpoint.create(data: AddLotRequest)` → `LotDto` (lot.py:69-79)
- `LotEndpoint.delete(lot_id: int)` → `None` (lot.py:94-100)
- `LotEndpoint.get(lot_id: int)` → `LotDto` (lot.py:57-67)
- `LotEndpoint.list(customer_catalog_id=...)` → `LotDtoPaginatedList` (lot.py:30-55)
- No batch create/delete endpoints — must iterate individually

**Alternatives considered**:
- Bulk insert for new lots during merge: Rejected — bulk endpoint creates entire catalog structure, not suitable for appending lots
- `UpdateLotRequest` (PUT) to update changed lots in-place: Rejected — `initial_data` is not updateable via PUT, only override data can be changed. Delete+recreate is required to change initial_data.

## R3: Lot Data Comparison Strategy

**Decision**: Compare 7 dimensional/shipping fields from `LotDataDto` between file's `initial_data` and server lot's `initial_data`: `qty`, `l`, `w`, `h`, `wgt`, `cpack`, `force_crate`.

**Rationale**: These are the structured fields that come from the spreadsheet and represent physical lot characteristics. Description/notes/images are text fields that may diverge between file versions without representing a meaningful data change.

**Findings**:
- `LotDataDto` field names with Python attribute names: `qty`, `l`, `w`, `h`, `wgt`, `cpack`, `force_crate`
- The importer (`importers.py:170-183`) sets these same fields when building `LotDataDto` from spreadsheet rows
- Server returns these fields via `lot.initial_data.qty`, etc.
- Comparison must handle `None` vs `0` and type coercion (float vs int) — normalize before comparing

## R4: Override Preservation During Delete+Recreate

**Decision**: Before deleting a changed lot, read its full `LotDto` including `overriden_data`. After creating the new lot with file data as `initial_data`, apply the saved overrides via the new lot's `overriden_data` field in the `AddLotRequest`.

**Rationale**: The `AddLotRequest` accepts an `overriden_data: List[LotDataDto]` field. By passing the original lot's overrides directly into the create request, overrides are preserved in a single API call rather than requiring a separate update.

**Findings**:
- `LotDto.overriden_data: List[LotDataDto]` — typically 0 or 1 entries
- `AddLotRequest.overriden_data: List[LotDataDto]` — can pass existing overrides at creation time
- This avoids the need for a separate `UpdateLotRequest` call after creation
- If `overriden_data` is empty, the lot simply has no overrides (no special handling needed)

## R5: Fetching All Lots for Existing Catalog

**Decision**: Use `list_lots_by_catalog` with pagination to fetch all server lots. Page through results until all lots are collected.

**Rationale**: The API is paginated (default page_size=10, max unknown). A catalog may have hundreds of lots. Must fetch all pages to build the complete server-side lot map.

**Findings**:
- `services.list_lots_by_catalog(request, customer_catalog_id, page, page_size)` calls `api.lots.list()`
- Returns `LotDtoPaginatedList` which has `.data` (list of `LotDto`) and pagination metadata
- Each `LotDto` in the list response includes `id`, `customer_item_id`, `initial_data`, `overriden_data`
- Must paginate through all pages (page_size=100 to minimize round-trips)
- Individual `get_lot()` calls NOT needed — list response already includes full `LotDto` with `initial_data` and `overriden_data`

## R6: AddLotRequest Catalog Association

**Decision**: When creating individual lots during merge, associate them with the existing catalog using `LotCatalogDto` in the `AddLotRequest.catalogs` list.

**Rationale**: A lot must be associated with at least one catalog. The `AddLotRequest.catalogs` field accepts `List[LotCatalogDto]` where each entry contains the catalog ID.

**Findings**:
- `LotCatalogDto` contains: `id` (catalog internal ID), `lot_number` (optional)
- The catalog's internal ID is already known from `find_catalog_by_customer_id()`
- Lot number comes from the spreadsheet row's `Lot Num` field (available in `BulkInsertLotRequest.lot_number`)
- Image links from the spreadsheet are available in `BulkInsertLotRequest.image_links`

# Data Model: Restore Catalog Import with Merge

**Feature**: 019-restore-catalog-import | **Date**: 2026-02-16

## Entities

### Uploaded File (transient)

Not persisted. Exists only during request handling.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| file | UploadedFile | request.FILES["file"] | Raw uploaded file |
| extension | str | Derived from filename | Must be in {.xlsx, .csv, .json} |
| tmp_path | Path | tempfile.NamedTemporaryFile | Written with original suffix for `load_file()` |

### BulkInsertLotRequest (from file parse)

Produced by `load_file()` → `CatalogDataBuilder`. One per lot row in the spreadsheet.

| Field | Type | API Alias | Notes |
|-------|------|-----------|-------|
| customer_item_id | str | customerItemId | Unique lot identifier within catalog — **merge key** |
| lot_number | str | lotNumber | Display lot number |
| image_links | List[str] | imageLinks | Auto-generated S3 URLs |
| initial_data | LotDataDto | initialData | Dimensional/shipping data from spreadsheet |
| overriden_data | List[LotDataDto] | overridenData | Same as initial_data at import time |

### LotDataDto (comparison fields)

The 7 dimensional/shipping fields used for change detection (per clarification):

| Field | Type | API Alias | Description |
|-------|------|-----------|-------------|
| qty | int | Qty | Shipping quantity |
| l | float | L | Length (inches) |
| w | float | W | Width (inches) |
| h | float | H | Height (inches) |
| wgt | float | Wgt | Weight (pounds) |
| cpack | str | CPack | Container pack code ("1"=nf, "2"=lf, "3"=f, "4"=vf, "pbo") |
| force_crate | bool | ForceCrate | Whether lot requires crating |

Non-comparison fields (present in LotDataDto but ignored for diff): `value`, `description`, `notes`, `item_id`, `noted_conditions`, `do_not_tip`, `commodity_id`.

### LotDto (server lot)

Fetched via `list_lots_by_catalog`. One per existing lot on server.

| Field | Type | API Alias | Notes |
|-------|------|-----------|-------|
| id | int | id | Internal lot ID — used for delete/get operations |
| customer_item_id | str | customerItemId | **Merge key** — matched against file lots |
| initial_data | LotDataDto | initialData | Server's initial data — compared against file |
| overriden_data | List[LotDataDto] | overridenData | User overrides — **must be preserved** on delete+recreate |
| catalogs | List[LotCatalogDto] | catalogs | Catalog associations |
| image_links | List[ImageLinkDto] | imageLinks | Image URLs |

### AddLotRequest (for individual lot creation during merge)

Used when inserting new lots or re-creating changed lots.

| Field | Type | API Alias | Source |
|-------|------|-----------|--------|
| customer_item_id | str | customerItemId | From file's BulkInsertLotRequest |
| image_links | List[str] | imageLinks | From file's BulkInsertLotRequest |
| initial_data | LotDataDto | initialData | From file's BulkInsertLotRequest |
| overriden_data | List[LotDataDto] | overridenData | Empty for new lots; original lot's overrides for changed lots |
| catalogs | List[LotCatalogDto] | catalogs | [{catalog_id: existing_catalog_id, lot_number: from_file}] |

### LotCatalogDto (catalog association)

| Field | Type | API Alias | Notes |
|-------|------|-----------|-------|
| catalog_id | int | catalogId | Internal catalog ID from `find_catalog_by_customer_id()` |
| lot_number | str | lotNumber | From file's BulkInsertLotRequest.lot_number |

### MergeResult (internal, not API)

Returned by the merge service function. Used to build summary toast and JSON response.

| Field | Type | Notes |
|-------|------|-------|
| added | int | Count of lots inserted (file-only) |
| updated | int | Count of lots deleted+recreated (changed) |
| unchanged | int | Count of lots skipped (identical) |
| failed | int | Count of lots where delete+recreate failed |
| errors | List[str] | Error messages for failed lots |
| catalog_id | int | Internal catalog ID for redirect URL |

## Data Flow

### New Catalog Path (US1)

```
File → load_file() → BulkInsertRequest
     → find_catalog_by_customer_id() → None (not found)
     → bulk_insert(BulkInsertRequest)
     → JsonResponse {success: true, redirect: "/events/<id>/"}
```

### Merge Path (US2)

```
File → load_file() → BulkInsertRequest
     → find_catalog_by_customer_id() → catalog_id (found)
     → list_lots_by_catalog(catalog_id, paginated) → all server LotDto[]
     → build lookup: {customer_item_id: LotDto} for server lots
     → build lookup: {customer_item_id: BulkInsertLotRequest} for file lots (first occurrence only)
     → for each file lot:
         if not in server → create(AddLotRequest)           [added]
         if in server and fields differ → delete(id) + create(AddLotRequest with overrides)  [updated]
         if in server and fields same → skip                [unchanged]
     → JsonResponse {success: true, redirect: "/events/<id>/", merge: {added, updated, unchanged, failed}}
```

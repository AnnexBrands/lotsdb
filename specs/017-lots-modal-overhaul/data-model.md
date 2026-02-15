# Data Model: Lots Modal Overhaul

**Branch**: `017-lots-modal-overhaul` | **Date**: 2026-02-14

## Overview

This feature introduces no new data entities or storage. All data comes from the existing ABConnect API via `services.get_lot()`. The changes are purely in how data is transformed and presented in the modal template.

## Existing Entities (Unchanged)

### LotDto (from ABConnect API)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `id` | int | Internal lot ID |
| `customer_item_id` | str? | External item ID |
| `initial_data` | LotDataDto | Original/baseline lot data |
| `overriden_data` | LotDataDto[] | List of overrides (0 or 1) |
| `catalogs` | LotCatalogDto[] | Associated catalogs |
| `image_links` | ImageLinkDto[] | Image references |

### LotDataDto (shared by initial_data and overriden_data)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `qty` | int? | Quantity |
| `l` | float? | Length (inches) |
| `w` | float? | Width (inches) |
| `h` | float? | Height (inches) |
| `wgt` | float? | Weight (pounds) |
| `value` | float? | Monetary value |
| `cpack` | str? | Container pack code ("1"=NF, "2"=LF, "3"=F, "4"=VF, "PBO") |
| `description` | str? | Lot description |
| `notes` | str? | Additional notes |
| `noted_conditions` | str? | Condition notes |
| `commodity_id` | int? | Commodity/HS code ID |
| `force_crate` | bool? | Force crating flag |
| `do_not_tip` | bool? | Do not tip flag |
| `item_id` | int? | Item reference ID |

### ImageLinkDto

| Field | Type | Description |
| ----- | ---- | ----------- |
| `id` | int | Image ID |
| `link` | str | Full image URL |

## View-Layer Data Structures

### Modal Field Context (new shape for template)

The modal template receives a `fields` dict matching the structure already used by `lots_table_row.html`:

```python
fields = {
    "qty":         {"value": int|None,   "changed": bool, "original": int|None},
    "l":           {"value": float|None, "changed": bool, "original": float|None},
    "w":           {"value": float|None, "changed": bool, "original": float|None},
    "h":           {"value": float|None, "changed": bool, "original": float|None},
    "wgt":         {"value": float|None, "changed": bool, "original": float|None},
    "cpack":       {"value": str|None,   "changed": bool, "original": str|None},
    "force_crate": {"value": bool|None,  "changed": bool, "original": bool|None},
    "do_not_tip":  {"value": bool|None,  "changed": bool, "original": bool|None},
}
```

- `value`: Effective value (override if present, else initial)
- `changed`: Whether override differs from initial
- `original`: Initial parsed value (shown as reference below input)

### Template Context (GET /panels/lots/{id}/detail/)

```python
{
    "lot": LotDto,              # Full lot object (images, catalogs, etc.)
    "fields": dict,             # Override field dict (see above)
    "lot_description": str,     # Effective description (override or initial)
    "lot_notes": str,           # Effective notes (override or initial)
}
```

## Placeholder Data Structures (Future Integration)

These structures exist only as HTML in the template for now. When the quoter and similarity matching engines are integrated, they will be populated from backend data.

### Sizing Suggestion (placeholder)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `label` | str | "Minimum", "Recommended", or "Oversize" |
| `dims` | str | Box dimensions (e.g., "24 x 34 x 115") |
| `pack_type` | str | Pack type (e.g., "Full Crate (VF)") |
| `is_recommended` | bool | Whether this is the highlighted option |

### Related Lot Card (placeholder)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `lot_number` | str | Lot number/title |
| `image_url` | str | Image thumbnail URL |
| `dims` | str | Dimensions string |
| `weight` | str | Weight string |
| `cpack` | str | CPack code |
| `column` | str | "q25", "q50", or "q75" |

## Relationships

```
LotDto
  ├── initial_data: LotDataDto (1:1)
  ├── overriden_data: LotDataDto[] (0..1)
  ├── image_links: ImageLinkDto[] (0..n)
  └── catalogs: LotCatalogDto[] (1..n)

Modal Template Context
  ├── lot → LotDto
  ├── fields → derived from initial_data + overriden_data comparison
  ├── lot_description → derived from override or initial description
  └── lot_notes → derived from override or initial notes
```

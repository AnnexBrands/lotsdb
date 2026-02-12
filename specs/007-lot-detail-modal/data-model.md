# Data Model: Lot Detail Modal

**Feature**: 007-lot-detail-modal | **Date**: 2026-02-11

## Overview

No new data entities are introduced. This feature reuses existing data structures from the ABConnect API.

## Existing Entities Used

### LotDto (from ABConnect API)

| Field | Type | Description |
|-------|------|-------------|
| id | int | Internal lot ID |
| customer_item_id | string | Customer's item identifier |
| initial_data | LotDataDto | Original lot data |
| overriden_data | list[LotDataDto] | Override data (0 or 1 entries) |
| image_links | list[ImageLinkDto] | Lot images |
| catalogs | list[LotCatalogInformationDto] | Catalog references (lot_number, catalog_id) |

### LotDataDto (from ABConnect API)

| Field | Type | Description |
|-------|------|-------------|
| qty | int | Quantity |
| l | decimal | Length |
| w | decimal | Width |
| h | decimal | Height |
| wgt | decimal | Weight |
| value | decimal | Monetary value |
| cpack | string | Case/pack info |
| description | string | Lot description |
| notes | string | Additional notes |
| noted_conditions | string | Condition notes |
| commodity_id | int | Commodity reference |
| force_crate | bool | Force crate flag |
| do_not_tip | bool | Do not tip flag |

### View Context (Django template context)

The modal detail view builds the same row structure as the existing `lot_detail` view:

```python
# Context for lot_detail_modal.html
{
    "lot": LotDto,
    "has_override": bool,
    "rows": [
        {
            "label": str,        # Display label (e.g., "Quantity")
            "attr": str,         # Field name (e.g., "qty")
            "initial": any,      # Initial value
            "override": any,     # Override value (None if no override)
            "changed": bool,     # True if override differs from initial
            "is_flag": bool,     # True for boolean fields
        }
    ],
}
```

### Table Row ID Convention

Each `<tr>` in the lots table gains an `id` attribute for OOB targeting:

```
id="lot-row-{lot.id}"
```

## State Transitions

### Modal State

```
Closed → Opening (HTMX request in flight)
       → Open/Detail (detail fragment loaded in dialog)
       → Open/Edit (edit form fragment loaded in dialog)
       → Saving (form submission in flight)
       → Closed (after save success or user dismiss)
```

No persistent state changes — the modal is ephemeral UI.

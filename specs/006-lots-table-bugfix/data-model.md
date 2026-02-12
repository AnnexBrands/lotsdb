# Data Model: Lots Table & Bugfixes

**Branch**: `006-lots-table-bugfix` | **Date**: 2026-02-11

## Existing Entities (No Schema Changes)

### LotDto (from ABConnect API)
| Field | Type | Source |
|-------|------|--------|
| id | int | Primary key |
| customer_item_id | str? | Customer's item ID |
| initial_data | LotDataDto | Original lot data |
| overriden_data | List[LotDataDto] | Override data (0-1 items) |
| catalogs | List[LotCatalogDto] | Catalog associations |
| image_links | List[ImageLinkDto] | Image URLs |

### LotDataDto (field values)
| Field | Type | Table Column |
|-------|------|-------------|
| qty | int? | Qty |
| l | float? | L |
| w | float? | W |
| h | float? | H |
| wgt | float? | Wgt |
| cpack | str? | CPack |
| description | str? | Desc |
| notes | str? | Notes |
| force_crate | bool? | Crate |
| do_not_tip | bool? | Do Not Tip |
| value | float? | (not displayed) |
| noted_conditions | str? | (not displayed) |
| commodity_id | str? | (not displayed) |

### LotCatalogInformationDto (embedded in catalog)
| Field | Type | Notes |
|-------|------|-------|
| id | int | Lot ID — used for scoping |
| lot_number | str | Display identifier |

## New View-Layer Data Structures

### LotTableRow (template context, not persisted)
```python
{
    "lot": LotDto,           # Full lot object
    "lot_number": str,       # From embedded catalog data
    "fields": {              # Per-field override metadata
        "<field_name>": {
            "value": Any,    # Effective value (override or initial)
            "changed": bool, # True if overridden
            "original": Any, # Initial value (for tooltip)
        },
        ...
    }
}
```

## Data Flow

```
event.lots (LotCatalogInformationDto[])
    → local pagination (page of lot IDs)
    → services.get_lot(lot_id) for each
    → build LotTableRow[] with override comparison
    → render lots_table.html
```

# Data Model: Auction Catalog Manager

**Branch**: `001-auction-catalog-manager` | **Date**: 2026-02-10

## Overview

All data is managed by the remote Catalog API. This application has no local database — it acts as a web interface to the API via ABConnectTools. The models below describe the data shapes as consumed from the API.

## Entities

### Seller

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Primary identifier |
| name | string (optional) | Seller name |
| customer_display_id | integer | Customer-facing display ID |
| is_active | boolean | Active/inactive status |

**Expanded view** includes:
- `catalogs`: List of associated CatalogDto objects

**API source**: `SellerDto` / `SellerExpandedDto`

---

### Event (Catalog)

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Primary identifier |
| customer_catalog_id | string (optional) | External catalog reference |
| agent | string (optional) | Managing agent |
| title | string (optional) | Event/catalog title |
| start_date | datetime | Auction start date |
| end_date | datetime | Auction end date |
| is_completed | boolean | Whether event has concluded |

**Expanded view** includes:
- `sellers`: List of associated SellerDto objects
- `lots`: List of LotCatalogInformationDto (id + lot_number)

**API source**: `CatalogDto` / `CatalogExpandedDto`

---

### Lot

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Primary identifier |
| customer_item_id | string (optional) | External item reference |
| initial_data | LotData | Original lot specifications |
| overriden_data | List[LotData] | Override specifications |
| catalogs | List[LotCatalog] | Associated catalog mappings |
| image_links | List[ImageLink] | Product images |

**API source**: `LotDto`

---

### LotData (shared by initial and override)

| Field | Type | Description |
|-------|------|-------------|
| qty | integer (optional) | Quantity |
| l | float (optional) | Length |
| w | float (optional) | Width |
| h | float (optional) | Height |
| wgt | float (optional) | Weight |
| value | float (optional) | Estimated/reserve value |
| cpack | string (optional) | Case/pack information |
| description | string (optional) | Item description |
| notes | string (optional) | General notes |
| item_id | integer (optional) | Internal item reference |
| force_crate | boolean (optional) | Requires crating |
| noted_conditions | string (optional) | Condition remarks |
| do_not_tip | boolean (optional) | Handling restriction |
| commodity_id | integer (optional) | Commodity classification |

**API source**: `LotDataDto`

---

### LotCatalog (lot-to-catalog association)

| Field | Type | Description |
|-------|------|-------------|
| catalog_id | integer | Associated catalog ID |
| lot_number | string | Lot number within that catalog |

**API source**: `LotCatalogDto`

---

### ImageLink

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Image identifier |
| link | string | Image URL |

**API source**: `ImageLinkDto`

## Relationships

```
Seller 1──M Catalog (via SellerExpandedDto.catalogs / CatalogExpandedDto.sellers)
Catalog 1──M Lot (via CatalogExpandedDto.lots / LotDto.catalogs)
Lot 1──1 LotData (initial_data)
Lot 1──M LotData (overriden_data)
Lot 1──M ImageLink (image_links)
```

Note: Seller ↔ Catalog is many-to-many (a catalog can have multiple sellers, a seller can have multiple catalogs). The API exposes both directions.

## Override Behavior

- `initial_data` is read-only from this application's perspective — it represents the original catalog entry
- `overriden_data` is an array of LotData objects that can be added/modified via `LotEndpoint.update()`
- When displaying a lot, the UI compares `overriden_data` fields against `initial_data` to highlight differences
- Overrides apply to the lot globally (not per-catalog)
- Overrides remain editable regardless of the parent event's completion status

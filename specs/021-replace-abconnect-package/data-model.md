# Data Model: 021-replace-abconnect-package

**Date**: 2026-03-13

## Entities

### 1. AB SDK Client Instance

**Purpose**: Replaces `ABConnectAPI(request).catalog` as the cached API accessor.

| Attribute | Type | Notes |
|-----------|------|-------|
| catalog | CatalogEndpoint | Catalog CRUD + bulk_insert |
| lots | LotsEndpoint | Lot CRUD + get_overrides |
| sellers | SellersEndpoint | Seller CRUD |

**Lifecycle**: Created once per HTTP request, cached on `request._catalog_api`. Reuses session token from `request.session["ab_token"]`.

**Change from old**: Was `ABConnectAPI(request).catalog` (CatalogAPI sub-object). Now `ABConnectAPI(request=request)` (top-level client).

---

### 2. BulkInsertRequest (Modified)

**Purpose**: Payload for batch lot creation. Structure changes from nested typed models to flat dict-based items.

#### Old Structure (ABConnectTools)
```
BulkInsertRequest
  catalogs: List[BulkInsertCatalogRequest]
    customer_catalog_id: str
    agent: str
    title: str
    start_date: datetime
    end_date: datetime
    sellers: List[BulkInsertSellerRequest]
      name: str
      customer_display_id: int
      is_active: bool
    lots: List[BulkInsertLotRequest]
      customer_item_id: str
      lot_number: str
      image_links: List[str]
      initial_data: LotDataDto
      overriden_data: List[LotDataDto]  ← WAS POPULATED, NOW EMPTY
```

#### New Structure (AB SDK)
```
BulkInsertRequest
  catalog_id: Optional[int]
  items: Optional[List[dict]]  ← Generic dict list
```

#### Behavioral Change
- `overriden_data` MUST be an empty list `[]` for all new lots (FR-005)
- `image_links` MUST contain only verified URLs from image scanning (FR-006)

---

### 3. LotDataDto (Field Gap)

**Purpose**: Lot dimensional/descriptive data payload.

| Field | Old SDK | New SDK | Gap? |
|-------|---------|---------|------|
| qty | int | int | No |
| l (length) | float | float (alias "l") | No |
| w | float | float | No |
| h | float | float | No |
| wgt | float | float | No |
| value | float | float | No |
| description | str | str | No |
| cpack | str | - | YES |
| notes | str | - | YES |
| force_crate | bool | - | YES |
| noted_conditions | str | - | YES |
| do_not_tip | bool | - | YES |
| item_id | int | - | YES |
| commodity_id | int | - | YES |

**Workaround**: Pass as raw dict keys — the API backend accepts all fields regardless of SDK model coverage.

---

### 4. Image Scanner Result

**Purpose**: New entity representing the result of probing CDN URLs for a single lot.

| Attribute | Type | Notes |
|-----------|------|-------|
| house_id | int | Seller/house identifier |
| catalog_id | int | Catalog identifier |
| lot_id | int | Lot identifier |
| valid_urls | List[str] | URLs that returned 2xx responses |
| probed_count | int | Total URLs probed |
| stopped_reason | str | "consecutive_failures" or "max_reached" |

**URL Pattern**: `https://s3.amazonaws.com/static2.liveauctioneers.com/{house_id}/{catalog_id}/{lot_id}_{n}_m.jpg` where n starts at 1.

**Stop conditions**:
- 3 consecutive non-2xx responses (4xx, 5xx, network error all count)
- Upper bound of 200 images per lot

---

### 5. Session Keys

| Key | Old Value | New Value | Owner |
|-----|-----------|-----------|-------|
| Token storage | `"abc_token"` | `"ab_token"` | AB SDK |
| Username | `"abc_username"` | `"abc_username"` (unchanged) | lotsdb |
| Recovery cache | `"{username}:merge_recovery"` | `"{username}:merge_recovery"` (unchanged) | lotsdb |

---

## State Transitions

### Image Scanner Per-Lot Flow
```
START → probe(n=1)
  ├─ 2xx → record URL, reset failure counter, probe(n+1)
  ├─ non-2xx → increment failure counter
  │    ├─ failures < 3 → probe(n+1)
  │    └─ failures >= 3 → STOP (consecutive_failures)
  └─ n > 200 → STOP (max_reached)
```

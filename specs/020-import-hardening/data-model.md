# Data Model: Import Hardening (020)

**Date**: 2026-02-17
**Feature**: `020-import-hardening`

## Entities

### Recovery Entry (Redis cache)

A cached record of a failed lot operation during merge. Keyed by user and stored as a JSON-serialized list.

**Cache key**: `{abc_username}:merge_recovery`
**TTL**: 86400 seconds (24 hours)
**Storage**: Redis (existing `default` cache backend)

| Field | Type | Description |
|-------|------|-------------|
| `customer_item_id` | string | The lot's customer-assigned item identifier |
| `lot_number` | string | The lot number within the catalog |
| `catalog_id` | int | Internal catalog ID (for context/navigation) |
| `customer_catalog_id` | string | Customer-facing catalog identifier |
| `seller_display_id` | string | Seller's customer display ID (for deep-link) |
| `operation` | string | `"create"` or `"update"` (update = delete succeeded, create failed) |
| `add_lot_request` | dict | Full serialized `AddLotRequest` payload (initial_data, overriden_data, catalogs, image_links) |
| `error_message` | string | The exception message from the failed operation |
| `timestamp` | string (ISO 8601) | When the failure occurred |

**Shape**: The cache value is a JSON list of recovery entry dicts:
```json
[
  {
    "customer_item_id": "2100000000",
    "lot_number": "001",
    "catalog_id": 405438,
    "customer_catalog_id": "400160",
    "seller_display_id": "1874",
    "operation": "update",
    "add_lot_request": { ... },
    "error_message": "Connection timeout",
    "timestamp": "2026-02-17T10:30:00Z"
  }
]
```

**Operations**:
- **Append**: After a lot failure in `merge_catalog`, append to the list (read-modify-write with Redis).
- **Read**: Recovery page reads the full list for the current user.
- **Remove**: On successful retry, remove the entry by `customer_item_id`.
- **Clear**: On "skip", remove the entry. On "all recovered", delete the key.

### Item Search Result (transient, not persisted)

Resolved mapping from a customer item ID to its navigation context.

| Field | Type | Description |
|-------|------|-------------|
| `customer_item_id` | string | The searched item identifier |
| `lot_id` | int | Internal lot ID |
| `catalog_id` | int | Internal catalog ID |
| `customer_catalog_id` | string | Customer-facing catalog identifier (for `?event=` param) |
| `seller_display_id` | string | Seller display ID (for `?seller=` param) |
| `lot_position` | int | 0-based index of the lot in the event's embedded lots list |

**Not persisted** — computed on-demand per search request via the API resolution chain (R1).

## Existing Entities Modified

### Upload Response (JSON)

Current shape (both new and merge paths):
```json
{"success": true, "redirect": "/"}
```

New shape:
```json
{
  "success": true,
  "redirect": "/?seller=1874&event=400160",
  "merge": {"added": 2, "updated": 1, "unchanged": 5, "failed": 1},
  "recovery_url": "/imports/recovery/",
  "warnings": ["Failed to update lot 2100000000: Connection timeout"]
}
```

- `redirect` changes from `"/"` to deep-link URL with seller and event params.
- `recovery_url` added when `failed > 0`.
- `merge` and `warnings` unchanged (already existed).

### Pending Toast (sessionStorage, browser-side)

```json
{"msg": "Added: 2, Updated: 1, Unchanged: 5", "type": "success"}
```

Written to `sessionStorage` before redirect, consumed on page load.

## Validation Rules

- Recovery entries expire after 24 hours (Redis TTL).
- Recovery cache key MUST be namespaced by `abc_username` (multi-user safety).
- Item search returns first match only when multiple lots share the same `customer_item_id`.
- Upload file size MUST be validated at <=1 MB before processing (client-side `file.size` check + server-side guard).
- `lot_position` is computed by finding the item's index in `event.lots` (embedded `LotCatalogInformationDto` list, ordered by lot_number).

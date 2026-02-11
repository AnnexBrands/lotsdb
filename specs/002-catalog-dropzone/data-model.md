# Data Model: Catalog Dropzone

## Overview

This feature introduces no new persistent data models. It reuses the existing catalog import pipeline (`load_file` → `bulk_insert`) and the existing `Event (Catalog)` entity for redirection.

## Request/Response Shapes

### Upload Request

| Field | Type | Description |
|-------|------|-------------|
| `file` | File (multipart) | The catalog file (.xlsx, .csv, .json) |

### Upload Response (Success)

```json
{
  "success": true,
  "redirect": "/events/123/"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Always `true` on success |
| `redirect` | string | URL to the created event detail page |

### Upload Response (Error)

```json
{
  "success": false,
  "error": "Failed to read file: missing required column 'Catalog ID'"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Always `false` on error |
| `error` | string | Human-readable error description |

## Entity Relationships (Existing)

```
BulkInsertRequest
  └── catalogs[] (BulkInsertCatalogRequest)
        ├── customer_catalog_id  ← used to resolve internal ID after insert
        ├── sellers[]
        └── lots[]

CatalogExpandedDto (returned by catalogs.list)
  ├── id                      ← internal ID used for /events/<id>/ URL
  ├── customer_catalog_id     ← matches the bulk insert input
  ├── sellers[]
  └── lots[]
```

## State Transitions

```
File Dropped
  → [Client] Extension check
    → FAIL: Toast error, stop
    → PASS: Upload to server
      → [Server] load_file() parse
        → FAIL: Return error JSON → Toast error
        → PASS: bulk_insert() API call
          → FAIL: Return error JSON → Toast error
          → PASS: Lookup catalog by customer_catalog_id
            → Return redirect URL → Browser navigates to event page
```

# Contract: Events Panel View — Stale-While-Revalidate

## Endpoint: `GET /panels/sellers/{seller_id}/events/`

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 50 | Items per page |
| `title` | str | "" | Filter by event title |
| `fresh` | str | "" | If `"1"`, bypass cache and fetch from API |

### Behavior Matrix

| Cache state | `fresh` param | `title` filter | Response |
|-------------|---------------|----------------|----------|
| Hit | absent | absent | Cached HTML + auto-refresh trigger |
| Hit | absent | present | API fetch (filters bypass cache) |
| Hit | `"1"` | absent | API fetch, update cache, fresh HTML |
| Miss | absent | absent | API fetch, populate cache, fresh HTML |
| Miss | `"1"` | absent | API fetch, update cache, fresh HTML |

### Auto-Refresh Trigger

When serving from cache (row 1 above), the response HTML includes a hidden element at the end of the events panel content (before OOB swaps):

```html
<div style="display:none"
     hx-get="/panels/sellers/{{ seller_id }}/events/?fresh=1"
     hx-target="#panel-left2-content"
     hx-swap="innerHTML"
     hx-trigger="load"></div>
```

This element fires immediately when swapped into the DOM, triggering a background refresh. The fresh response does NOT include this element (preventing infinite loops).

### Race Condition Guard

The events panel container tracks the current seller:
```html
<div id="panel-left2-content" data-seller-id="{{ seller_id }}">
```

JavaScript `htmx:beforeSwap` handler checks: if the incoming response is a `?fresh=1` request and the panel's `data-seller-id` no longer matches the response's seller, the swap is prevented.

### Skeleton Suppression

The `htmx:beforeRequest` handler is modified: when the request URL contains `fresh=1`, do NOT inject skeleton HTML (the panel already shows cached content).

### Response Headers

| Header | Value | Condition |
|--------|-------|-----------|
| `HX-Push-Url` | `/?seller={display_id}` | Always on initial request (not on `?fresh=1`) |

## Test Contracts

### TC-SWR01: Cache hit serves cached HTML with refresh trigger
- Mock cache hit with seller events
- GET `/panels/sellers/1/events/`
- Assert response contains events HTML
- Assert response contains hidden div with `hx-get="...?fresh=1"`

### TC-SWR02: Fresh request bypasses cache, returns without trigger
- GET `/panels/sellers/1/events/?fresh=1`
- Assert API was called
- Assert response contains events HTML
- Assert response does NOT contain hidden div with `fresh=1`

### TC-SWR03: Cache miss returns normal HTML without refresh trigger
- Mock cache miss
- GET `/panels/sellers/1/events/`
- Assert API was called
- Assert response does NOT contain hidden div with `fresh=1`

### TC-SWR04: Filter active bypasses cache entirely
- Mock cache hit
- GET `/panels/sellers/1/events/?title=foo`
- Assert API was called with title filter
- Assert response does NOT contain hidden div with `fresh=1`

### TC-SWR05: Fresh request skips HX-Push-Url
- GET `/panels/sellers/1/events/?fresh=1`
- Assert response does NOT have `HX-Push-Url` header

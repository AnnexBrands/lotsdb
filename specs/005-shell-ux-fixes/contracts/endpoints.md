# API Contracts: Shell UX Fixes

**Feature Branch**: `005-shell-ux-fixes` | **Date**: 2026-02-11

## Modified Endpoints

### GET `/` (Home Page / Shell)

**Changes**:
- Query params `seller` and `event` now expect **customer-facing IDs** (not internal IDs)
- `seller`: `customer_display_id` (int, e.g., `4098`)
- `event`: `customer_catalog_id` (string, e.g., `395768`)
- Uses defensive `_parse_page_params` instead of raw `int()` for pagination
- Validates event belongs to seller when both params present; ignores event if mismatch
- Hydrated includes pass concrete `pagination_url` values (not empty string)

**Query Parameters**:

| Param | Type | Description |
|-------|------|-------------|
| `seller` | int | Seller `customer_display_id` — look up via API filter |
| `event` | string | Catalog `customer_catalog_id` — look up via API filter |

**Hydration behavior**:
1. If `seller` present: look up seller by `CustomerDisplayId` filter, fetch events
2. If `event` also present: look up catalog by `CustomerCatalogId` filter, verify seller match, fetch lots from expanded catalog
3. If event's seller doesn't match URL seller: ignore event param, hydrate seller-only
4. Pass `pagination_url` to hydrated includes: `/panels/sellers/{seller_id}/events/` and `/panels/events/{event_id}/lots/`

---

### GET `/panels/sellers/`

**Changes**:
- Accepts optional `name` query parameter for filtering sellers by name
- Filter value passed through to `services.list_sellers(Name=name)`

**Query Parameters** (added):

| Param | Type | Description |
|-------|------|-------------|
| `name` | string | Filter sellers by name (partial match) |

---

### GET `/panels/sellers/{seller_id}/events/`

**Changes**:
- `HX-Push-Url` now uses `/?seller={seller.customer_display_id}` instead of internal ID
- Accepts optional `title` query parameter for filtering events by title
- Filter value passed through to `services.list_catalogs(Title=title)`

**Query Parameters** (added):

| Param | Type | Description |
|-------|------|-------------|
| `title` | string | Filter events by title (partial match) |

**Response Headers**:

| Header | Value (changed) |
|--------|----------------|
| `HX-Push-Url` | `/?seller={customer_display_id}` |

---

### GET `/panels/events/{event_id}/lots/`

**Changes**:
- `HX-Push-Url` now uses `/?seller={customer_display_id}&event={customer_catalog_id}`
- Lots fetched from expanded catalog response (`event.lots`) with local pagination, not from Lots list endpoint
- Still uses internal `event_id` in URL path (this is Django routing, not user-facing)

**Response Headers**:

| Header | Value (changed) |
|--------|----------------|
| `HX-Push-Url` | `/?seller={customer_display_id}&event={customer_catalog_id}` |

---

## Template Changes

### seller_list_panel.html

- Each `<li>` item adds `hx-indicator="#panel-left2 .htmx-indicator"` for reliable spinner

### events_panel.html

- Header replaced: static `<h3>` becomes inline filter form with `hx-get` to `/panels/sellers/{seller_id}/events/`
- Each `<li>` item adds `hx-indicator="#panel-main .htmx-indicator"` for reliable spinner
- OOB includes pass concrete `pagination_url` (not empty string)

### lots_panel.html

- OOB events include passes concrete `pagination_url` value

### shell.html

- Hydrated includes pass concrete `pagination_url` values
- Mobile JS resize handler resets `data-mobile-panel` to "sellers"

---

## Contract Test Requirements

### Customer-Friendly URL Tests
1. `seller_events_panel` response `HX-Push-Url` contains `customer_display_id`, not internal ID
2. `event_lots_panel` response `HX-Push-Url` contains `customer_display_id` and `customer_catalog_id`
3. Shell hydration with `?seller=<display_id>` resolves correct seller
4. Shell hydration with `?seller=<display_id>&event=<catalog_id>` resolves both
5. Shell hydration with mismatched seller/event ignores event

### Filter Tests
6. `sellers_panel` with `?name=Test` filters results via service call
7. `seller_events_panel` with `?title=Test` filters results via service call

### Lots Fix Tests
8. `event_lots_panel` uses lots from expanded catalog response

### Pagination URL Tests
9. Hydrated events panel include has valid `pagination_url` (not empty)
10. OOB events include in lots_panel has valid `pagination_url` (not empty)

### Defensive Parsing Tests
11. Shell view with `?page=abc` on `/` returns 200 (not 500)

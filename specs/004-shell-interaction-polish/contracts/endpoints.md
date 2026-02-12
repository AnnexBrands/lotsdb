# API Contracts: Shell Interaction Polish

**Feature Branch**: `004-shell-interaction-polish`
**Date**: 2026-02-11

## Overview

This feature modifies **3 existing panel endpoints** and the **home page endpoint**. No new endpoints are added. Changes add selection-state context, `HX-Push-Url` response headers, pagination parameter validation, and loading indicator markup.

---

## Modified Endpoints

### GET `/` (Home Page / Shell)

**Before**: Renders `shell.html` with sellers pre-loaded. Ignores query parameters.
**After**: Reads `?seller=<id>&event=<id>` from query string. If present, pre-fetches data and renders the shell with panels hydrated.

**Query Parameters** (new):

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `seller` | int | (none) | Pre-select seller: load events into Left2 |
| `event` | int | (none) | Pre-select event: load lots into Main |

**Behavior**:
- If `seller` param is present and valid: fetch events, render Left2 with content, highlight seller in Left1
- If `event` param is also present and valid: fetch lots, render Main with content, highlight event in Left2
- If params are invalid (non-integer, seller/event not found): ignore silently, render default empty state
- Pagination params (`page`, `page_size`) are NOT supported on hydration (always page 1)

**Response** (HTML full page): `shell.html` with conditionally pre-populated panels.

**Template context additions**:

| Variable | Type | Description |
|----------|------|-------------|
| `selected_seller_id` | int or None | Seller ID from query param, for `.active` class |
| `selected_event_id` | int or None | Event ID from query param, for `.active` class |
| `events` | list or None | Pre-fetched events if seller param present |
| `lots` | list or None | Pre-fetched lots if event param present |

---

### GET `/panels/sellers/`

**Before**: Returns sellers list fragment. No selection awareness.
**After**: Accepts optional `selected` query parameter to apply `.active` class.

**Query Parameters** (added):

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `selected` | int | (none) | Seller ID to highlight with `.active` class |

**Pagination validation** (changed):
- `page`: Clamped to `max(1, int(value))`; invalid values default to `1`
- `page_size`: Clamped to `max(1, min(200, int(value)))`; invalid values default to `50`
- **No longer raises `ValueError`** on bad input

**Template context additions**:

| Variable | Type | Description |
|----------|------|-------------|
| `selected_seller_id` | int or None | From `selected` query param |

**Response** (HTML fragment): Same structure as before, with `.active` class on matching seller row.

**Status codes**: 200 (success), 502 (ABConnect API error). **No 500 from bad pagination params.**

---

### GET `/panels/sellers/{seller_id}/events/`

**Before**: Returns events list fragment + OOB clear of Main panel. No selection state. No URL push.
**After**: Returns events list fragment + OOB clear of Main panel + OOB update of sellers list (with selected seller highlighted). Sets `HX-Push-Url` header.

**Pagination validation**: Same clamping behavior as `/panels/sellers/`.

**Response headers** (added):

| Header | Value | Description |
|--------|-------|-------------|
| `HX-Push-Url` | `/?seller={seller_id}` | Pushes shell URL with seller param |

**OOB fragments** (added):

| Target | Swap | Content |
|--------|------|---------|
| `#panel-main-content` | `innerHTML` | Empty state (unchanged from before) |
| `#panel-left1-content` | `innerHTML` | Re-rendered seller list with `selected_seller_id` set |

**Template context additions**:

| Variable | Type | Description |
|----------|------|-------------|
| `selected_seller_id` | int | The clicked seller ID, for `.active` class in OOB seller list |

**Status codes**: 200 (success), 404 (seller not found), 502 (ABConnect API error).

---

### GET `/panels/events/{event_id}/lots/`

**Before**: Returns lots list fragment. No selection state. No URL push.
**After**: Returns lots list fragment + OOB update of events list (with selected event highlighted). Sets `HX-Push-Url` header.

**Pagination validation**: Same clamping behavior as `/panels/sellers/`.

**Response headers** (added):

| Header | Value | Description |
|--------|-------|-------------|
| `HX-Push-Url` | `/?seller={seller_id}&event={event_id}` | Pushes shell URL with both params |

**OOB fragments** (added):

| Target | Swap | Content |
|--------|------|---------|
| `#panel-left2-content` | `innerHTML` | Re-rendered events list with `selected_event_id` set |

**Template context additions**:

| Variable | Type | Description |
|----------|------|-------------|
| `selected_event_id` | int | The clicked event ID, for `.active` class in OOB events list |

**Note**: The view must resolve `seller_id` from the event data to construct the correct `HX-Push-Url`.

**Status codes**: 200 (success), 404 (event not found), 502 (ABConnect API error).

---

## Unchanged Endpoints

All endpoints not listed above remain unchanged. See `specs/003-spa-shell-layout/contracts/endpoints.md` for the full list.

---

## Contract Test Requirements

### Selection State Tests

1. **Seller selection**: `GET /panels/sellers/{id}/events/` response includes OOB fragment for `#panel-left1-content` with `.active` class on the selected seller
2. **Event selection**: `GET /panels/events/{id}/lots/` response includes OOB fragment for `#panel-left2-content` with `.active` class on the selected event
3. **Seller list with selection**: `GET /panels/sellers/?selected=42` renders `.active` class on seller ID 42

### URL Push Tests

4. **Seller click pushes URL**: `GET /panels/sellers/{id}/events/` response has `HX-Push-Url: /?seller={id}` header
5. **Event click pushes URL**: `GET /panels/events/{id}/lots/` response has `HX-Push-Url: /?seller={sid}&event={eid}` header

### Shell Hydration Tests

6. **Shell with seller param**: `GET /?seller=42` renders events in Left2, seller highlighted in Left1
7. **Shell with both params**: `GET /?seller=42&event=7` renders events + lots, both highlighted
8. **Shell with invalid params**: `GET /?seller=abc` renders default empty state (no error)

### Pagination Validation Tests

9. **Invalid page**: `GET /panels/sellers/?page=abc` returns 200 with page 1 content (not 500)
10. **Negative page**: `GET /panels/sellers/?page=-5` returns 200 with page 1 content
11. **Oversized page_size**: `GET /panels/sellers/?page_size=9999` returns 200 with page_size clamped to 200

### Loading Indicator Tests

12. **Left1 indicator markup**: Shell HTML contains `.htmx-indicator` inside `#panel-left1`
13. **All panels have indicator**: All three panels in shell contain `.htmx-indicator` markup

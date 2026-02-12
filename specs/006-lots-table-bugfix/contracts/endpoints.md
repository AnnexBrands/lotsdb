# API Contracts: Lots Table & Bugfixes

**Branch**: `006-lots-table-bugfix` | **Date**: 2026-02-11

## Modified Endpoints

### GET `/panels/events/{event_id}/lots/`

**Changes**: Now fetches full `LotDto` objects and renders a table instead of cards.

**Request**: Unchanged — `event_id` path param, `page`/`page_size` query params.

**Response**: HTML fragment containing `<table class="lots-table">` with:
- One `<tr>` per lot with columns: img, desc/notes, qty, L, W, H, wgt, cpack, crate, do-not-tip, save
- Overridden cells have `class="overridden"` and `title="Original: {value}"`
- OOB swap for `#panel-left2-content` (events list with selection) — unchanged
- OOB swap for `#panel-main-content` nested inside events_panel.html is now **suppressed** via `skip_main_oob=True`

**Default page_size**: Changed from 50 to 25.

### GET `/` (Shell Hydration)

**Changes**: Hydration path fetches full `LotDto` objects when event is present.

**Response**: Shell HTML with hydrated lots table in `#panel-main-content`.

## New Endpoint

### POST `/panels/lots/{lot_id}/override/`

**Purpose**: Save inline override for a single lot row.

**Request**:
- Method: POST
- Content-Type: application/x-www-form-urlencoded
- Body fields: `qty`, `l`, `w`, `h`, `wgt`, `cpack`, `description`, `notes`, `force_crate`, `do_not_tip`

**Response**:
- 200: HTML fragment — single `<tr>` replacing the submitted row
- HTMX: `hx-target="closest tr"`, `hx-swap="outerHTML"`

**Headers**: None special.

## Template Contract Changes

### `events_panel.html`

**Before**: Always renders `<div id="panel-main-content" hx-swap-oob="innerHTML">` with empty state.

**After**: Guarded by `{% if not skip_main_oob %}`. When included from `lots_panel.html`, `skip_main_oob=True` is passed, preventing the nested OOB from overwriting lots.

### `lots_panel.html` → `lots_table.html`

**Before**: Card layout (`<ul class="lot-cards">`) with minimal lot data.

**After**: Table layout (`<table class="lots-table">`) with full lot data, override highlighting, and per-row save forms.

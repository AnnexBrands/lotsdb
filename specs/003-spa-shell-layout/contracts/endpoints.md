# API Contracts: SPA Shell Layout

**Feature Branch**: `003-spa-shell-layout`
**Date**: 2026-02-11

## Overview

This feature introduces **3 new endpoints** that return HTML fragments for HTMX panel swaps, plus modifies the existing home page endpoint. All existing endpoints remain unchanged.

---

## New Endpoints

### GET `/panels/sellers/`

**Purpose**: Returns the sellers list HTML fragment for Left1 panel.
**Used by**: Initial shell load (`{% include %}`), pagination within Left1.

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 50 | Items per page |
| `name` | string | (none) | Filter by seller name (contains) |
| `status` | string | (none) | Filter by active status |

**Response** (HTML fragment):
```html
<ul class="panel-list">
  <li class="panel-item" hx-get="/panels/sellers/{id}/events/" hx-target="#panel-left2-content">
    <span class="panel-item-title">{name} <span class="panel-item-id">{customer_display_id}</span></span>
  </li>
  <!-- ... more sellers ... -->
</ul>
<div class="panel-pagination">
  <a hx-get="/panels/sellers/?page=2" hx-target="#panel-left1-content">Next</a>
</div>
```

**OOB fragments**: None.
**Status codes**: 200 (success), 502 (ABConnect API error).

---

### GET `/panels/sellers/{seller_id}/events/`

**Purpose**: Returns the events list HTML fragment for Left2 panel when a seller is clicked.
**Used by**: Seller click in Left1 panel.

**Path Parameters**:

| Param | Type | Description |
|-------|------|-------------|
| `seller_id` | int | The seller ID |

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 50 | Items per page |

**Response** (HTML fragment):
```html
<!-- Primary response: swapped into #panel-left2-content via hx-target -->
<div class="panel-header">
  <h3>{seller_name}<span class="panel-count">({count})</span></h3>
</div>
<ul class="panel-list">
  <li class="panel-item" hx-get="/panels/events/{id}/lots/" hx-target="#panel-main-content">
    <span class="panel-item-title">{title}</span>
    <span class="panel-item-meta">{customer_catalog_id} | {start_date}</span>
  </li>
  <!-- ... more events ... -->
</ul>
<div class="panel-pagination">
  <a hx-get="/panels/sellers/{seller_id}/events/?page=2" hx-target="#panel-left2-content">Next</a>
</div>

<!-- OOB: clear the lots panel -->
<div id="panel-main-content" hx-swap-oob="innerHTML">
  <div class="panel-empty">
    <p>Select an event to view lots</p>
  </div>
</div>
```

**OOB fragments**: `#panel-main-content` (innerHTML) — clears the lots panel.
**Status codes**: 200 (success), 404 (seller not found), 502 (ABConnect API error).

---

### GET `/panels/events/{event_id}/lots/`

**Purpose**: Returns the lots list HTML fragment for Main panel when an event is clicked.
**Used by**: Event click in Left2 panel.

**Path Parameters**:

| Param | Type | Description |
|-------|------|-------------|
| `event_id` | int | The event/catalog ID |

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 50 | Items per page |

**Response** (HTML fragment):
```html
<div class="panel-header">
  <h3>{event_title}<span class="panel-count">({count})</span></h3>
</div>
<ul class="lot-cards">
  <li class="lot-card">
    <a href="/lots/{id}/" class="lot-card-link">
      <div class="lot-card-thumb"><img src="{image_url}" alt=""></div>
      <div class="lot-card-info">
        <span class="lot-card-title">{lot_number}: {description}</span>
        <span class="lot-card-notes">{notes_truncated} <span class="lot-card-more">[more]</span></span>
      </div>
    </a>
  </li>
  <!-- ... more lots ... -->
</ul>
<div class="panel-pagination">
  <a hx-get="/panels/events/{event_id}/lots/?page=2" hx-target="#panel-main-content">Next</a>
</div>
```

**OOB fragments**: None.
**Status codes**: 200 (success), 404 (event not found), 502 (ABConnect API error).

---

## Modified Endpoints

### GET `/` (Home Page)

**Before**: Renders `sellers/list.html` — full-page seller list with filters and pagination.
**After**: Renders `shell.html` — the three-panel SPA shell with sellers pre-loaded in Left1.

**Behavior change**:
- Still calls `services.list_sellers()` for initial data
- Returns `shell.html` instead of `sellers/list.html`
- Left2 and Main panels render empty-state placeholders on initial load

**Backward compatibility**: The `/sellers/` URL continues to work as a full-page view for direct access.

---

## Unchanged Endpoints

All existing endpoints remain unchanged and continue to return full-page HTML:

| Endpoint | Template | Notes |
|----------|----------|-------|
| `GET /sellers/` | `sellers/list.html` | Full-page seller list (preserved) |
| `GET /sellers/{id}/` | `sellers/detail.html` | Full-page seller detail (preserved) |
| `GET /events/{id}/` | `events/detail.html` | Full-page event detail (preserved) |
| `GET /lots/{id}/` | `lots/detail.html` | Full-page lot detail (preserved) |
| `GET /lots/{id}/override/` | `lots/override.html` | Override form (preserved) |
| `POST /lots/{id}/override/` | redirect | Override save (preserved) |
| `GET /search/` | `search/results.html` | Search results (preserved) |
| `GET /imports/` | `imports/list.html` | Import list (preserved) |
| `POST /imports/run/` | redirect | Import execution (preserved) |
| `POST /imports/upload/` | JSON | Dropzone upload (preserved) |

---

## Contract Test Requirements

Each new endpoint requires contract tests verifying:

1. **Response is an HTML fragment** (not a full page — no `<!DOCTYPE>`, no `<html>` tag)
2. **Expected DOM structure** (correct IDs, classes, HTMX attributes)
3. **Pagination parameters** are respected
4. **OOB fragments** are present when expected
5. **Empty state** is rendered when data set is empty
6. **Error state** is rendered when API call fails

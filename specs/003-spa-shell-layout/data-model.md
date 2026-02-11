# Data Model: SPA Shell Layout

**Feature Branch**: `003-spa-shell-layout`
**Date**: 2026-02-11

## Overview

This feature introduces **no new data entities**. All data is sourced from the existing ABConnect API via `catalog/services.py`. The SPA shell is a presentation-layer change only.

The data model below documents the **existing entities** as they flow through the three panels, including the fields displayed and the API calls that source them.

## Entities

### Seller (Left1 Panel)

**Source**: `services.list_sellers(request, page, page_size, filters)`
**API**: ABConnect `SellerEndpoint.list()`

| Field | Type | Displayed | Notes |
|-------|------|-----------|-------|
| `id` | int | No (used for links) | Primary key in ABConnect |
| `name` | string | Yes | Seller name, single row with ID |
| `customer_display_id` | string | Yes | Inline after name, muted style |
| `is_active` | bool | No | Not displayed in panel |

**Panel behavior**: Paginated list. Each item shows `Name ID` on one row. Clicking a seller triggers HTMX load of events into Left2.

### Event / Catalog (Left2 Panel)

**Source**: `services.list_catalogs(request, seller_id, page, page_size, filters)`
**API**: ABConnect `CatalogEndpoint.list()`

| Field | Type | Displayed | Notes |
|-------|------|-----------|-------|
| `id` | int | No (used for links) | Primary key in ABConnect |
| `title` | string | Yes | Event title, clickable |
| `customer_catalog_id` | string | Yes | Shown in meta row with start_date |
| `start_date` | date | Yes | Shown as `customer_catalog_id \| start_date` |
| `agent` | string | No | Not displayed in panel |
| `end_date` | date | No | Not displayed in panel |
| `is_completed` | bool | No | Not displayed in panel |

**Panel behavior**: Paginated list filtered by selected seller. Each item shows title on row 1, `{customer_catalog_id} | {start_date}` on row 2. Clicking an event triggers HTMX load of lots into Main.

### Lot (Main Panel)

**Source**: `services.list_lots_by_catalog(request, customer_catalog_id, page, page_size)`
**API**: ABConnect `LotEndpoint.list(customer_catalog_id=...)`

| Field | Type | Displayed | Notes |
|-------|------|-----------|-------|
| `id` | int | Yes (link) | Primary key, links to lot detail page |
| `catalogs[0].lot_number` | string | Yes | Lot number in card title |
| `initial_data.description` | string | Yes | Description after lot number |
| `initial_data.notes` | string | Yes | Truncated to 2 lines with [more] |
| `image_links[0].link` | string | Yes | Thumbnail image (56x56) |

**Panel behavior**: Card-style list for selected event. Each card shows thumbnail image on left, lot number + description (bold) and notes (2-line clamp) on right. Clicking a card navigates to the existing full-page lot detail view (`/lots/<id>/`).

## Relationships

```text
Seller (1) ──→ (N) Event/Catalog ──→ (N) Lot
```

- One seller has many events/catalogs
- One event/catalog has many lots
- Navigation flows left to right: Seller → Event → Lot

## State

The SPA shell maintains **client-side selection state** only:

| State | Stored In | Cleared When |
|-------|-----------|-------------|
| Selected seller ID | CSS `.active` class on Left1 item | New seller clicked |
| Selected event ID | CSS `.active` class on Left2 item | New event clicked or new seller clicked |
| Panel content | DOM (HTMX-managed) | HTMX swap replaces innerHTML |

No server-side session state is introduced by this feature.

## Pagination

Each panel supports independent pagination using the existing `page` and `page_size` query parameters:

| Panel | Default Page Size | Pagination Controls |
|-------|------------------|-------------------|
| Left1 (Sellers) | 50 | Prev/Next within panel |
| Left2 (Events) | 50 | Prev/Next within panel |
| Main (Lots) | 50 | Prev/Next within panel |

Pagination links use `hx-get` with `hx-target` pointing to their own panel container, so paginating one panel does not affect the others.

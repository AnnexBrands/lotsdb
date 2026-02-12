# Data Model: Shell Interaction Polish

**Feature Branch**: `004-shell-interaction-polish`
**Date**: 2026-02-11

## Overview

This feature introduces **no new data entities**. All data continues to be sourced from the ABConnect API via `catalog/services.py`. Changes are confined to view context variables and template rendering logic.

The data model below documents the **new view context variables** introduced by this feature, extending the existing entity documentation from `specs/003-spa-shell-layout/data-model.md`.

## New View Context Variables

### Selection State

Selection state is tracked server-side via template context variables. These are passed to templates and used to apply the `.active` CSS class to the matching panel item.

| Variable | Type | Set By | Consumed By |
|----------|------|--------|-------------|
| `selected_seller_id` | int or None | `seller_events_panel` view, `sellers_panel` view (`selected` param), shell view (`seller` param) | `seller_list_panel.html` template |
| `selected_event_id` | int or None | `event_lots_panel` view, shell view (`event` param) | `events_panel.html` template |

**State flow**:
```text
User clicks seller → seller_events_panel(request, seller_id)
  → sets selected_seller_id = seller_id
  → re-renders seller_list_panel.html with active class
  → renders events_panel.html
  → sets HX-Push-Url: /?seller=seller_id

User clicks event → event_lots_panel(request, event_id)
  → sets selected_event_id = event_id
  → re-renders events_panel.html with active class
  → renders lots_panel.html
  → sets HX-Push-Url: /?seller=seller_id&event=event_id
```

### Shell Hydration State

On initial page load, the shell view reads URL query parameters and pre-fetches data:

| URL Param | Maps To | View Logic |
|-----------|---------|------------|
| `?seller=<id>` | `selected_seller_id` | Fetch events via `list_catalogs(seller_id)`, render Left2 |
| `?event=<id>` | `selected_event_id` | Fetch lots via `list_lots_by_catalog(event_id)`, render Main |

Invalid or missing params result in empty panel state (no error).

## Pagination Parameters

Pagination parameters are validated defensively (changed from raw `int()` parsing):

| Parameter | Valid Range | Default | Invalid Behavior |
|-----------|------------|---------|-----------------|
| `page` | >= 1 | 1 | Clamped to 1 |
| `page_size` | 1–200 | 50 | Clamped to 1 (min) or 200 (max) |

## Entities (Unchanged)

No changes to Seller, Event/Catalog, or Lot entities. See `specs/003-spa-shell-layout/data-model.md` for field definitions and relationships.

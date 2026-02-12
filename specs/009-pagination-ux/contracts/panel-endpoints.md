# Panel Endpoint Contracts: Pagination

**Feature**: 009-pagination-ux | **Date**: 2026-02-12

## Common Pagination Query Parameters

All panel endpoints accept these query parameters:

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `page` | int | 1 | 1–total_pages | Page number (1-indexed) |
| `page_size` | int | varies | 1–200 | Items per page |

**Default page sizes** (unchanged):
- Sellers panel: 50
- Events panel: 50
- Lots panel: 25

## Endpoints

### GET `/panels/sellers/`

**Query params** (existing + modified):
| Param | Type | Notes |
|-------|------|-------|
| `page` | int | Existing |
| `page_size` | int | Existing (already parsed, now exposed in UI) |
| `name` | str | Existing filter |
| `selected` | int | Existing selection state |

**Response**: HTML fragment containing seller list + `panel_pagination.html` partial.

**Pagination context** (template variables):
```
paginated.page_number = <current page>
paginated.total_pages = <total pages>
paginated.total_items = <total sellers matching filter>
paginated.start_item = <first item index on page>
paginated.end_item = <last item index on page>
paginated.page_size = <current page size>
paginated.has_previous_page = <bool>
paginated.has_next_page = <bool>
```

### GET `/panels/sellers/<seller_id>/events/`

**Query params** (existing + modified):
| Param | Type | Notes |
|-------|------|-------|
| `page` | int | Existing |
| `page_size` | int | Existing (already parsed, now exposed in UI) |
| `title` | str | Existing filter |

**Response**: HTML fragment containing events list + `panel_pagination.html` partial + OOB seller list update.

**Pagination context**: Same shape as sellers panel.

### GET `/panels/events/<event_id>/lots/`

**Query params** (existing + modified):
| Param | Type | Notes |
|-------|------|-------|
| `page` | int | Existing |
| `page_size` | int | Existing (already parsed, now exposed in UI) |

**Response**: HTML fragment containing lots table + `panel_pagination.html` partial + OOB events list update.

**Pagination context**: Same shape as sellers/events panels.

## Template Contract: `panel_pagination.html`

**Required include variables**:
```django
{% include "catalog/partials/panel_pagination.html"
    with base_url=<str>
         target_id=<str>
         indicator_id=<str>
         extra_params=<dict>  {# includes page_size if non-default #}
%}
```

**Rendered HTML structure** (new):
```html
<div class="panel-pagination">
  <a hx-get="...?page=N-1&...">« Prev</a>

  <span class="page-range">26–50 of 73</span>

  <span class="page-jump" onclick="...">
    <!-- Click to show input, Enter to navigate -->
    <span class="page-display">2 / 3</span>
    <input type="number" class="page-input" min="1" max="3" value="2" hidden>
  </span>

  <a hx-get="...?page=N+1&...">Next »</a>

  <select class="page-size-select" onchange="...">
    <option value="10">10</option>
    <option value="25" selected>25</option>
    <option value="50">50</option>
    <option value="100">100</option>
  </select>
</div>
```

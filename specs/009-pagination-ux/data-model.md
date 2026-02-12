# Data Model: Pagination UX Improvements

**Feature**: 009-pagination-ux | **Date**: 2026-02-12

## Entities

### PaginatedContext (dict)

Extended pagination metadata passed from views to templates. No database entity — this is a view-layer context dict.

**Existing fields** (unchanged):
| Field | Type | Description |
|-------|------|-------------|
| `page_number` | int | Current page (1-indexed) |
| `total_pages` | int | Total number of pages |
| `total_items` | int | Total items across all pages |
| `has_previous_page` | bool | Whether a previous page exists |
| `has_next_page` | bool | Whether a next page exists |

**New fields**:
| Field | Type | Description |
|-------|------|-------------|
| `start_item` | int | First item number on current page (1-indexed) |
| `end_item` | int | Last item number on current page |
| `page_size` | int | Current page size |

**Derivation rules**:
- `start_item = (page_number - 1) * page_size + 1`
- `end_item = min(page_number * page_size, total_items)`
- `page_size` = value from query param or default

### PanelPaginationTemplate (context)

Template context passed to `panel_pagination.html` via Django `{% include %}`.

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `paginated` | PaginatedContext | View | Pagination metadata (see above) |
| `base_url` | str | View | Panel endpoint URL (e.g., `/panels/events/123/lots/`) |
| `target_id` | str | Parent template | HTMX swap target (e.g., `#panel-main-content`) |
| `indicator_id` | str | Parent template | HTMX loading indicator selector |
| `extra_params` | dict | View | Preserved query params (selected, filters, page_size) |

## State Transitions

No state transitions — pagination is stateless (query-param driven).

## Validation Rules

- `page_number`: int, >= 1, clamped to `total_pages` (existing via `_parse_page_params`)
- `page_size`: int, >= 1, <= 200, clamped (existing via `_parse_page_params`)
- `start_item`: always >= 1 when total_items > 0
- `end_item`: always <= total_items

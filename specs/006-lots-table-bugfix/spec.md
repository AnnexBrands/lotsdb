# Feature Spec: Lots Table & Bugfixes

**Branch**: `006-lots-table-bugfix` | **Status**: Draft | **Date**: 2026-02-11

## Problem Statement

Three issues in the shell lots panel:

1. **Event selection breaks after first use**: Clicking an event loads lots once, but clicking a different event fails silently. Root cause: the OOB swap in `lots_panel.html` re-renders `events_panel.html`, which unconditionally includes a nested OOB that overwrites `#panel-main-content` with "Select an event" empty state.

2. **No thumbnails or descriptions**: The lots panel uses embedded `LotCatalogInformationDto` (id + lot_number only). The template references `lot.image_links` and `lot.initial_data.description` which don't exist on this minimal DTO.

3. **Lots panel needs tabular layout**: Operators need to see and edit lot data inline — not just lot numbers in cards. Required columns: image, description/notes, qty, L, W, H, weight, cpack, crate, do not tip, save action. Overridden values must be visually distinct with tooltip showing the original.

## User Stories

- **US1** (Bug): As an operator, I can click multiple events in sequence and see the correct lots each time.
- **US2** (Bug): As an operator, I can see lot thumbnails, descriptions, and notes in the lots panel.
- **US3** (Feature): As an operator, I can view lots in a table with columns: img, desc/notes, qty, L, W, H, wgt, cpack, crate, do-not-tip, save.
- **US4** (Feature): As an operator, I can see which values are overridden (highlighted with CSS class) and hover to see the original value in a tooltip.

## Functional Requirements

### US1: Fix event selection

- **FR-301**: Clicking any event in the left2 panel always triggers an HTMX request to `/panels/events/{id}/lots/` and updates `#panel-main-content`.
- **FR-302**: The OOB events-list re-render in `lots_panel.html` must NOT include the nested `#panel-main-content` OOB from `events_panel.html`.

### US2: Full lot data in panel

- **FR-303**: The lots panel view fetches full `LotDto` objects (with `initial_data`, `overriden_data`, `image_links`) for all lots on the current page.
- **FR-304**: Lot data source: get lot IDs from `event.lots` (embedded, reliable scoping), paginate locally, then fetch full `LotDto` for each visible lot via `services.get_lot()`.

### US3: Lots table layout

- **FR-305**: Replace the card-based lots panel with a table layout.
- **FR-306**: Table columns (in order): thumbnail image, description + notes, qty, L, W, H, wgt, cpack, crate (boolean), do-not-tip (boolean), save icon/button.
- **FR-307**: Each row represents one lot. The save button submits the override for that row.
- **FR-308**: Table renders inside `#panel-main-content` as an HTML fragment (no full page reload).

### US4: Override display

- **FR-309**: For each field, display the effective value (override if present, otherwise initial).
- **FR-310**: If a field has been overridden (value differs from initial), apply CSS class `overridden` to the cell.
- **FR-311**: Overridden cells have a `title` attribute showing the original (initial) value as a tooltip.
- **FR-312**: The save action per row submits only that row's data as an override via HTMX POST, updating the row in place.

## Acceptance Criteria

- **AC-1**: Click seller → click event A → lots load. Click event B → lots load. Click event A again → lots load. No failures.
- **AC-2**: Lots table shows thumbnail images (or placeholder) for lots that have `image_links`.
- **AC-3**: Lots table shows description and notes from `initial_data` (or override if present).
- **AC-4**: Table has all specified columns: img, desc/notes, qty, L, W, H, wgt, cpack, crate, do-not-tip, save.
- **AC-5**: Overridden cells have `class="overridden"` and `title="Original: {value}"`.
- **AC-6**: Save button per row posts override data and updates the row without full page reload.
- **AC-7**: Hydration path (`/?seller=X&event=Y`) also renders the lots table with full data.

## Non-Functional Requirements

- **NFR-1**: Page load with 25 lots should complete within acceptable time (25 individual API calls + 1 catalog call).
- **NFR-2**: Default page size reduced to 25 for the lots table (from 50) to limit API calls.

## Out of Scope

- Batch lot API endpoint (requires backend API changes)
- Inline editing of lot fields (save submits full row as override)
- Lot search/filter within the table

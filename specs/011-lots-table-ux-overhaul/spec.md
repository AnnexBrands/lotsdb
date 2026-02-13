# Feature Specification: Lots Table UX Overhaul

**Feature Branch**: `011-lots-table-ux-overhaul`
**Created**: 2026-02-13
**Status**: Draft

## Clarifications

### Session 2026-02-13

- Q: Modal editing model — view-first + edit button, or direct-edit for text? → A: Prefer auto-save everywhere. Modal opens with directly editable description/notes textareas; each field auto-saves immediately on blur. Lots table uses 15s inactivity debounce while the row is active, or immediate save on row blur. No manual "Save" button flow for text fields.
- Q: Route removal scope — keep search/import routes or remove all non-SPA routes? → A: Remove all (Option B). Search was not usable as created. Search and imports inaccessible until re-implemented as panels in a future feature. Remove navbar search form.

## User Scenarios & Testing

### US1 — Simplified URL Routing (P1)

As a user, when I visit the application, only `/login/` and `/` (the SPA shell) are navigable. All full-page seller, event, and lot routes are removed. All data interaction happens through the SPA panels.

**Why this priority**: Eliminates dead-end routes that bypass the SPA and create inconsistent UX.

**Independent Test**: Navigate to `/sellers/`, `/sellers/1/`, `/events/1/`, `/lots/1/` — all return 404. `/` loads the SPA shell. `/login/` loads the login form. All panel endpoints (`/panels/...`) remain functional.

**Acceptance Scenarios**:

1. **Given** the application is running, **When** a user visits `/`, **Then** the SPA shell loads with sellers panel.
2. **Given** any previously-valid full-page URL (e.g., `/sellers/`, `/events/1/`, `/lots/1/override/`), **When** a user navigates to it, **Then** they receive a 404.
3. **Given** the SPA shell, **When** a user interacts with panels and modals, **Then** all HTMX panel endpoints continue working identically.

---

### US2 — Clean Number Formatting (P1)

As a user viewing lots, weight and dimension values should display as integers when they have no meaningful decimal (e.g., `10` not `10.0`), and as decimals only when precision matters (e.g., `10.5`).

**Why this priority**: Visual noise reduction. `0.0` and `10.0` clutter the inputs.

**Independent Test**: Load a lot with weight=10.0 and length=10.5. Verify weight input shows "10" and length input shows "10.5".

**Acceptance Scenarios**:

1. **Given** a lot with wgt=10.0, **When** the table renders, **Then** the weight input displays "10".
2. **Given** a lot with l=10.5, **When** the table renders, **Then** the length input displays "10.5".
3. **Given** a lot with h=0.0, **When** the table renders, **Then** the height input displays "0".
4. **Given** a lot with no value (None), **When** the table renders, **Then** the input is empty.

---

### US3 — CPack Colored Badges (P1)

As a user scanning the lots table, CPack values display as color-coded letter badges (1→NF, 2→LF, 3→F, 4→VF, PBO→PBO) in Poppins 900 font weight, each with a distinct mapped color.

**Why this priority**: Quick visual scanning of condition pack status at a glance.

**Independent Test**: Load lots with different cpack values. Verify each displays the correct letter code with the assigned color in Poppins 900.

**Acceptance Scenarios**:

1. **Given** a lot with cpack=1, **When** the table renders, **Then** "NF" displays in Poppins 900 with its mapped color.
2. **Given** a lot with cpack=4, **When** the table renders, **Then** "VF" displays in Poppins 900 with its mapped color.
3. **Given** a lot with cpack=PBO, **When** the table renders, **Then** "PBO" displays in Poppins 900 with its mapped color.
4. **Given** a lot with no cpack, **When** the table renders, **Then** the cell shows "—".
5. **Given** a user changing cpack via the select, **When** they select a new value, **Then** the badge color updates immediately.

---

### US4 — Remove Img Header & Vertical Gridlines (P1)

As a user viewing the lots table, there are no vertical column borders (only horizontal row separators), and the image column has no `<th>` header text.

**Why this priority**: Reduces visual clutter for a cleaner data-dense table.

**Independent Test**: Inspect the rendered table. Verify no vertical borders between columns. Verify the image column `<th>` is empty.

**Acceptance Scenarios**:

1. **Given** the lots table, **When** it renders, **Then** `<td>` elements have no left/right borders.
2. **Given** the lots table, **When** it renders, **Then** rows are separated by horizontal bottom borders only.
3. **Given** the lots table header, **When** it renders, **Then** the first column header (image) has no text content.

---

### US5 — Merged Dimensions Column with Auto-Save (P2)

As a user, Qty, L, W, H, and Wgt columns are merged into a single "Dimensions" cell displayed as inline inputs: `{Qty} @ {L} x {W} x {H}, {Wgt} lbs`. Inputs support select-on-focus and tab navigation for efficient override entry. Only individually overridden values receive override styling (not the entire row or cell). The row auto-saves with a 15-second inactivity debounce while the row has focus, or saves immediately when the row loses focus.

**Why this priority**: Consolidates 5 columns into 1, dramatically improving table density and scan-ability. Auto-save eliminates the need for a manual save step.

**Independent Test**: Load a lot with qty=2, l=10, w=8, h=6, wgt=50. Verify the cell shows "2 @ 10 x 8 x 6, 50 lbs" as editable inputs. Click a value — it selects all. Tab moves to the next value. Change a value, wait 15s without further input — verify auto-save fires. Change a value, click outside the row — verify immediate save.

**Acceptance Scenarios**:

1. **Given** a lot with all dimension values, **When** the table renders, **Then** a single cell shows inline inputs separated by `@`, `x`, `,` and `lbs`.
2. **Given** a user clicks an input, **When** it gains focus, **Then** the current value is selected for easy replacement.
3. **Given** a lot where only wgt is overridden, **When** the table renders, **Then** only the wgt input has override styling; qty, l, w, h inputs do not.
4. **Given** a user tabs through the dimensions cell, **When** pressing Tab, **Then** focus moves qty→l→w→h→wgt in order.
5. **Given** a lot with no dimension values, **When** the table renders, **Then** all inputs are empty with no separators causing layout issues.
6. **Given** a user editing a row, **When** 15 seconds pass with no input and focus remains in the row, **Then** the row auto-saves.
7. **Given** a dirty row, **When** focus leaves the row entirely, **Then** the row saves immediately (no delay).
8. **Given** an inline row save, **When** the save fires, **Then** existing description/notes overrides (set via modal) MUST be preserved.

---

### US6 — Larger Thumbnails (P1)

As a user, lot thumbnails use more of the available row height for better visibility.

**Why this priority**: Small 40x40 thumbnails waste row space; larger images help identify lots faster.

**Independent Test**: Load lots with images. Verify thumbnails fill more of the row height than 40px.

**Acceptance Scenarios**:

1. **Given** a lot with an image, **When** the table renders, **Then** the thumbnail is visually larger (≥56px) and uses the available row height.
2. **Given** a lot without an image, **When** the table renders, **Then** the placeholder icon scales to match the new size.

---

### US7 — Immutable Description Cell with Modal Launch (P1)

As a user, the description/notes column header reads "Lot Description", shows the description as immutable text (not a textarea), and clicking the image or description cell opens the lot modal.

**Why this priority**: Description is not inline-editable; it should not look editable. Textarea adds unwanted resize handles and styling. Modal is the right editing surface.

**Independent Test**: Load a lot with a description. Verify it renders as plain text, not a textarea. Click it — the lot modal opens.

**Acceptance Scenarios**:

1. **Given** the lots table, **When** it renders, **Then** the description column header reads "Lot Description".
2. **Given** a lot with a description, **When** the table renders, **Then** the description displays as immutable text (no textarea, no resize handle).
3. **Given** a lot row, **When** the user clicks the description cell, **Then** the lot modal opens for that lot.
4. **Given** a lot row, **When** the user clicks the thumbnail image, **Then** the lot modal opens for that lot (existing behavior preserved).
5. **Given** a lot with notes, **When** the table renders, **Then** notes text appears below the description (truncated, immutable).

---

### US8 — Upgraded Lot Modal with Auto-Save (P2)

As a user, the lot modal displays an image gallery header, then a directly editable description, then directly editable notes. There is no separate "Edit" step — text fields are immediately editable and auto-save on blur. Each field saves independently when it loses focus. Edits save to the API's override storage but are presented as the lot's working text. This is critical because notes often contain long boilerplate that harms recommendation engine performance, and only the user can decide what to trim.

**Why this priority**: The modal is the primary editing surface for text fields. Gallery-first layout helps identification. Auto-save on blur eliminates friction — no "Save" button needed for text.

**Independent Test**: Open a lot modal. Verify image gallery at top, then editable description, then editable notes. Edit the description, click into the notes field — verify the description auto-saves immediately and the table row updates. Edit notes, close the modal — verify notes auto-save on blur.

**Acceptance Scenarios**:

1. **Given** a lot with images, **When** the modal opens, **Then** an image gallery fills the modal header area with navigation.
2. **Given** a lot with a description, **When** the modal opens, **Then** the description appears as an editable text area below the gallery.
3. **Given** a lot with notes, **When** the modal opens, **Then** the notes appear as an editable text area below the description.
4. **Given** a user editing the description, **When** the description field loses focus, **Then** the change auto-saves immediately via the override API and the table row updates (OOB swap).
5. **Given** a user editing the notes, **When** the notes field loses focus, **Then** the change auto-saves immediately and the table row updates.
6. **Given** description/notes fields in the modal, **When** the modal renders, **Then** they are labeled as "Description" and "Notes" (not "Override Description").
7. **Given** a lot with verbose boilerplate notes, **When** the user trims the text and saves (via blur), **Then** only the trimmed text is stored as the working value.
8. **Given** a modal text save, **When** the save fires, **Then** existing dimension/cpack/flag overrides MUST be preserved.

---

### Edge Cases

- What happens if a lot has no images? The modal header area should show a placeholder, not break the layout.
- What happens if description or notes are very long? The table cell should truncate with ellipsis; the modal should scroll.
- What happens if a user changes cpack and dimensions in the same row? Both changes save together when the row auto-saves (15s debounce or blur).
- What happens if a lot has overridden dimensions AND the user edits description in the modal? The inline save handler MUST merge existing override values for fields not in the form. The modal save handler MUST merge existing override values for dimension/flag fields. Neither save path may clobber the other's overrides.
- What happens if the auto-save fires while a previous save is in flight? Queue the second save; do not fire concurrent saves for the same lot.
- What happens to existing description/notes overrides? They display as the current value. No migration needed.
- What happens if all dimension values are None? The dims cell shows empty inputs; the `@`, `x`, `,`, `lbs` separators still render to maintain the layout structure.

## Requirements

### Functional Requirements

- **FR-001**: The URL configuration MUST only expose `/login/`, `/logout/`, `/no-access/`, `/` (SPA shell), and `/panels/*` (HTMX endpoints). All full-page seller, event, lot, search, and import routes MUST be removed. The navbar search form MUST also be removed.
- **FR-002**: Number values (weight, dimensions) MUST display as integers when the fractional part is zero (e.g., `10` not `10.0`).
- **FR-003**: CPack values MUST display as letter codes: 1→NF, 2→LF, 3→F, 4→VF, PBO→PBO.
- **FR-004**: CPack display MUST use Poppins font at weight 900 with a distinct color per code.
- **FR-005**: The image column header (`<th>`) MUST have no text content.
- **FR-006**: The lots table MUST have no vertical gridlines between columns; only horizontal borders separate rows.
- **FR-007**: Qty, L, W, H, and Wgt MUST be merged into a single table column with the display format `{Qty} @ {L} x {W} x {H}, {Wgt} lbs`.
- **FR-008**: Each dimension/weight input MUST select its content on focus.
- **FR-009**: Override styling MUST apply to individual overridden values, not to the entire row or cell.
- **FR-010**: Lot thumbnails MUST be larger than the current 40×40px to use more row height.
- **FR-011**: The description/notes column header MUST read "Lot Description".
- **FR-012**: Description and notes MUST render as immutable text in the table (not textarea).
- **FR-013**: Clicking the description cell or image MUST open the lot modal.
- **FR-014**: The lot modal MUST display an image gallery header, then description, then notes.
- **FR-015**: Description and notes MUST be directly editable in the modal (no view-first step, no "Edit" button for text).
- **FR-016**: Modal description/notes MUST auto-save individually on field blur, persisting via the override API.
- **FR-017**: Modal text saves MUST update the corresponding table row via OOB swap.
- **FR-018**: Lots table rows MUST auto-save with a 15-second inactivity debounce while the row has focus.
- **FR-019**: Lots table rows MUST save immediately (no delay) when focus leaves the row.
- **FR-020**: Inline row saves MUST preserve existing description/notes overrides set via the modal.
- **FR-021**: Modal text saves MUST preserve existing dimension/cpack/flag overrides set inline.
- **FR-022**: Poppins font MUST be loaded via Google Fonts CDN.

### Key Entities

- **LotDataDto**: Core lot data (qty, l, w, h, wgt, value, cpack, description, notes, etc.). Immutable `initial_data` + mutable `overriden_data` via API.
- **CPack Mapping**: Static map of numeric/string codes to display labels and colors.

## Non-Functional Requirements

- No new Python dependencies (Poppins is loaded via CDN, all changes are CSS/HTML/JS)
- Changes confined to: `urls.py`, templates, static CSS, `catalog_tags.py`, `panels.py`, `forms.py`
- View modules for removed routes (`sellers.py`, `events.py`, `lots.py`) can be cleaned up or left as dead code

## Out of Scope

- Lot data migration (override vs initial_data distinction is API-level; no schema change)
- Mobile-specific modal layout changes (existing responsive behavior preserved)
- Re-implementing search or import as SPA panel endpoints (future feature)

## Success Criteria

- **SC-001**: Only `/login/`, `/logout/`, `/no-access/`, `/`, and `/panels/*` URLs resolve; all others return 404
- **SC-002**: No `0.0` or `10.0` values display in dimension/weight inputs when the value is a whole number
- **SC-003**: CPack values render as colored letter badges readable at a glance
- **SC-004**: Table has no vertical gridlines; information density improves with merged dimensions column
- **SC-005**: Description is immutable in the table; clicking it opens the modal
- **SC-006**: Modal edits to description/notes auto-save on blur and update the table row
- **SC-007**: Inline row auto-saves fire at 15s inactivity or immediately on blur, preserving modal text overrides
- **SC-008**: All existing tests pass (with necessary fixture/URL updates)

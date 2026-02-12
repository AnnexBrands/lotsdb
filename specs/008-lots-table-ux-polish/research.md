# Research: Lots Table UX Polish

**Feature**: 008-lots-table-ux-polish | **Date**: 2026-02-11

## R1: Description + Notes — Single Textarea vs Two Fields

**Decision**: Replace two separate inputs with a single `<textarea>` for description and a read-only truncated notes display below it.

**Rationale**: The user wants "description and notes should be one td, not separate inputs." Notes are secondary metadata — displaying them as read-only text with a "more" link keeps the cell clean while description remains editable inline.

**Alternatives considered**:
- Single combined textarea with separator: Rejected — makes it hard to parse description vs notes on save.
- Keep two inputs but style differently: Rejected — user explicitly wants them combined visually.

## R2: Row Click Highlight Behavior

**Decision**: Remove the yellow highlight that appears when clicking a row. The `.overridden` class with yellow background should only be applied to cells with persistent override differences, not as a click/interaction state.

**Rationale**: User says "clicking row should not highlight yellow and never clear." The current `tbody tr:hover` style is `#f8fafc` (light gray), which is fine. The yellow `.overridden` class should remain only for cells that have an actual override diff. The issue is likely the HTMX request/swap cycle making the row flash — no new yellow should be introduced on interaction.

**Alternatives considered**:
- Remove all highlighting: Rejected — override indicators are still valuable.

## R3: Save Button Redesign — Debounce + Visual State

**Decision**: Remove border from save icon. Track dirty state via JS `input`/`change` events. Use CSS classes `.save-dirty` (red) and `.save-clean` (green). Auto-save after 2s debounce on `focusout` from the row.

**Rationale**: The user wants a spreadsheet-like experience with visual feedback and auto-save. A 2-second debounce on row blur prevents accidental saves while still being responsive.

**Implementation approach**:
- Listen for `input`/`change` events on row inputs → mark row as dirty, set save icon red
- On row `focusout` (with relatedTarget check to see if focus left the row), start 2s debounce timer
- If focus returns to row before timer fires, cancel debounce
- On save success (htmx:afterSwap), icon goes green briefly
- Clicking save icon triggers immediate submit (existing behavior)

**Alternatives considered**:
- Auto-save on each field change: Rejected — too many API calls, user wants "long debounce"
- Save on Enter key: Not requested, but doesn't conflict

## R4: Cpack Select Dropdown

**Decision**: Replace `<input type="text">` for cpack with `<select>` containing options: "", "1", "2", "3", "4", "PBO". Native `<select>` supports arrow key navigation by default.

**Rationale**: User specifically lists "1, 2, 3, 4, PBO" as the only valid values. A `<select>` restricts input and supports keyboard arrow navigation natively.

**Alternatives considered**:
- Datalist with text input: More flexible but doesn't restrict to valid values.
- Custom dropdown component: Over-engineered for 5 options.

## R5: Input Border Removal

**Decision**: Remove `border` from `.lot-input` inputs. Add a subtle border to the `<td>` cells instead. Inputs get border only on `:focus`.

**Rationale**: User wants "inputs for qty, l, w, h, wgt cpack should have no border, only box border in td." This creates a cleaner, spreadsheet-like appearance.

## R6: Photo Hover Preview

**Decision**: Use CSS-only hover preview with `position: absolute` on a hidden `<img>` that becomes visible on `.lot-thumb-btn:hover`. The large image uses the same `src` as the thumbnail.

**Rationale**: Pure CSS approach — no JS needed. The ABConnect image URLs serve full-size images; the thumbnail is just CSS-scaled.

**Alternatives considered**:
- JS tooltip library: Over-engineered for a simple image preview.
- Separate preview endpoint: Unnecessary — same image URL works at any size.

## R7: Notes "More" Link

**Decision**: Display notes as read-only truncated text with a "more" button that triggers the lot detail modal (same `hx-get` as thumbnail click).

**Rationale**: User wants notes visible but not editable inline. A "more" link that opens the existing detail modal reuses existing infrastructure.

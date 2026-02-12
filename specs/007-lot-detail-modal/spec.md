# Feature Spec: Lot Detail Modal in SPA

**Branch**: `007-lot-detail-modal` | **Status**: Draft | **Date**: 2026-02-11

## Problem Statement

The lot detail page (`/lots/<id>/`) and its override form (`/lots/<id>/override/`) are full-page views that navigate the user away from the SPA shell. When an operator clicks a lot in the lots table to view or edit details, they lose their seller/event/lots navigation context and must re-navigate back through the shell after viewing or editing a lot.

The lot detail and override functionality should be presented as a modal overlay within the SPA shell, preserving the three-panel layout and navigation context underneath.

## User Stories

- **US1** (Feature): As an operator, I can click a lot row in the lots table and see the full lot detail (all 13 fields, images) in a modal overlay without leaving the SPA shell.
- **US2** (Feature): As an operator, I can edit lot override data from the modal and save changes, with the modal closing and the underlying table row updating in place.
- **US3** (UX): As an operator, I can close the modal by clicking an X button, clicking the backdrop, or pressing Escape, returning to the SPA shell with my navigation state intact.

## Functional Requirements

### US1: Lot detail modal

- **FR-001**: Clicking a lot's thumbnail or a dedicated "view" icon in the lots table row opens a modal overlay containing the lot detail view.
- **FR-002**: The modal displays all lot fields: qty, length, width, height, weight, value, case/pack, description, notes, conditions, commodity_id, force_crate, do_not_tip.
- **FR-003**: The modal shows initial values and override values side by side when overrides exist, with changed fields highlighted (same visual treatment as the existing detail page).
- **FR-004**: The modal displays lot images if `image_links` are present.
- **FR-005**: The modal shows the lot number and customer item ID in the header.
- **FR-006**: The modal content is loaded via HTMX GET to a panel endpoint, returning an HTML fragment (no full-page load).

### US2: Override editing from modal

- **FR-007**: The modal includes an "Edit Override" button that switches the modal content to an editable form.
- **FR-008**: The override form contains all 13 editable fields (same as existing OverrideForm).
- **FR-009**: Saving the form submits via HTMX POST. On success, the modal closes and the corresponding table row is updated via an out-of-band swap.
- **FR-010**: Form validation errors are displayed inline within the modal (no page navigation).
- **FR-011**: Cancel in the edit form returns to the detail view within the modal (no close).

### US3: Modal UX

- **FR-012**: The modal is a centered overlay with a semi-transparent backdrop that dims the SPA shell behind it.
- **FR-013**: The modal can be closed by: (a) clicking the X button, (b) clicking the backdrop, (c) pressing the Escape key.
- **FR-014**: Closing the modal preserves all SPA shell state (selected seller, event, lots table scroll position).
- **FR-015**: Only one modal can be open at a time.
- **FR-016**: The modal has a maximum width appropriate for the lot detail content (~700px) and scrolls vertically if content exceeds viewport height.

## Acceptance Criteria

- **AC-1**: Click lot thumbnail/view icon in lots table → modal opens with lot detail data, SPA shell visible behind backdrop.
- **AC-2**: Modal shows all 13 lot fields with initial/override comparison and highlight for changed fields.
- **AC-3**: Modal shows lot images when present.
- **AC-4**: Click "Edit Override" in modal → modal switches to editable form with all 13 fields.
- **AC-5**: Save override in modal → modal closes, table row updates with new values, toast confirms success.
- **AC-6**: Close modal via X / backdrop / Escape → SPA state preserved (seller, event, lots table unchanged).
- **AC-7**: Validation errors in override form display inline in the modal.
- **AC-8**: Loading state shown while modal content is being fetched.

## Non-Functional Requirements

- **NFR-1**: Modal content fetched via a single API call (reuse existing `services.get_lot()`).
- **NFR-2**: No external JS libraries — modal behavior implemented with vanilla JS + HTMX + CSS.
- **NFR-3**: Modal is accessible: focus trap while open, Escape to close, appropriate ARIA attributes.

## Out of Scope

- Deep-linking to a specific lot modal via URL (can be added later)
- Removing the existing full-page lot detail/override routes (kept for backwards compatibility and direct navigation)
- Image upload or editing within the modal
- Batch editing of multiple lots from a multi-select

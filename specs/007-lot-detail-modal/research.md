# Research: Lot Detail Modal in SPA

**Feature**: 007-lot-detail-modal | **Date**: 2026-02-11

## R1: Modal Implementation Pattern (HTMX + Django)

**Decision**: Use HTMX `hx-get` to load modal content as an HTML fragment, with a reusable modal container in the shell template and vanilla JS for open/close behavior.

**Rationale**:
- The existing codebase uses HTMX 2.0.4 for all dynamic content loading (panels, inline save). No JS frameworks are in use.
- HTMX natively supports loading HTML fragments into a target element, which is exactly what a modal needs.
- The pattern: an empty `#lot-modal` container in `shell.html`, HTMX requests load content into it, CSS handles visibility and positioning.
- HTMX events (`htmx:afterSwap`) can trigger showing the modal, and custom JS handles dismiss.

**Alternatives Considered**:
- **Alpine.js**: Would add a dependency for reactivity. Unnecessary — the modal's open/close state is trivially managed with a CSS class toggle + HTMX events.
- **Dialog element (`<dialog>`)**: Native HTML dialog with `showModal()`/`close()` methods. Good accessibility support (built-in focus trap, Escape handling). However, HTMX loads content async and the dialog's `showModal()` must be called after swap. We can still use `<dialog>` as the container element for free accessibility features while loading content via HTMX.
- **Dedicated JS modal library**: Overkill for this use case, adds a dependency.

**Final Decision**: Use the native `<dialog>` element as the modal container. This gives us:
- Free backdrop via `::backdrop` pseudo-element
- Built-in Escape key handling
- Built-in focus trapping
- `showModal()` / `close()` API
- Content loaded via HTMX into the dialog's inner container

## R2: Modal Content Loading Strategy

**Decision**: Create a new panel endpoint `/panels/lots/<lot_id>/detail/` that returns the lot detail as an HTML fragment (no base template, no breadcrumbs). Reuse the existing `lot_detail` view logic but render a modal-specific partial template.

**Rationale**:
- The existing `lot_detail` view renders a full page with `{% extends "catalog/base.html" %}`. We need a fragment for HTMX injection.
- Creating a new partial template (`lot_detail_modal.html`) avoids modifying the existing full-page view.
- The view logic (fetching lot, building field rows, resolving seller/event context) can be extracted into a shared helper or the panel view can duplicate the small amount of logic.
- The override form also needs a fragment version — either a second endpoint or the same endpoint with a query param (e.g., `?edit=1`).

**Alternatives Considered**:
- **Reuse existing views with `HX-Request` header detection**: Django can check `request.headers.get('HX-Request')` and return different templates. However, the existing lot_detail view extends base.html which includes navbar, breadcrumbs — hard to strip cleanly. Separate endpoints are cleaner.
- **Single endpoint with mode param**: `/panels/lots/<id>/detail/?mode=edit`. Simpler routing but mixes concerns.

**Final Decision**: Two new panel endpoints:
1. `GET /panels/lots/<lot_id>/detail/` — returns lot detail fragment for the modal
2. `POST /panels/lots/<lot_id>/detail/` — handles override form submission, returns updated fragment or closes modal

The edit form is toggled within the same modal by HTMX-swapping the modal content with a `?edit=1` variant.

## R3: Row Update After Modal Save

**Decision**: Use HTMX out-of-band (OOB) swap to update the lot's table row when the override is saved from the modal.

**Rationale**:
- The existing inline save in `lot_override_panel` already returns an updated `<tr>` with `hx-swap="outerHTML"`. The same pattern works for the modal save.
- After a successful save, the response includes:
  1. A signal to close the modal (empty content or a `HX-Trigger` header)
  2. An OOB swap for the table row: `<tr hx-swap-oob="outerHTML" id="lot-row-{id}">...updated row...</tr>`
- This requires adding `id="lot-row-{lot_id}"` to each table row.

**Alternatives Considered**:
- **Reload the entire lots table**: Too heavy — re-fetches all lot data for the page.
- **JS-driven row update**: Manually update DOM cells with JS. Fragile and doesn't match HTMX patterns.

**Final Decision**: OOB swap with a row ID. The modal save response includes the updated row as an OOB fragment.

## R4: Modal Accessibility

**Decision**: Use `<dialog>` element with `showModal()` for built-in accessibility, supplemented with ARIA attributes.

**Rationale**:
- `<dialog>` with `showModal()` provides: focus trap, Escape to close, inert background, `::backdrop` styling.
- Browser support for `<dialog>` is universal in modern browsers (96%+ global support as of 2025).
- ARIA: `role="dialog"` is implicit on `<dialog>`. Add `aria-labelledby` pointing to the modal title.
- Close button: `<button>` with accessible label.

**No Alternatives Needed**: `<dialog>` is the right tool for this job.

## R5: Toast Notification on Save

**Decision**: Reuse existing toast system from `base.html` for save confirmation.

**Rationale**: The toast system is already implemented (lines 51-61 of base.html script). The modal save handler can call `showToast()` directly after successful save, or trigger it via an HTMX response header (`HX-Trigger: showToast`).

**Final Decision**: Use `HX-Trigger` response header with `showToast` event. The existing toast JS listens for this custom event and displays the message.

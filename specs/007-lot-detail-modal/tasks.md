# Tasks: Lot Detail Modal in SPA

**Input**: Design documents from `/specs/007-lot-detail-modal/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec. Test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the `<dialog>` modal container to the SPA shell, wire up modal open/close JS, and add modal CSS. These are shared by all user stories.

- [X] T001 Add `<dialog id="lot-modal">` container with modal-header, modal-body, and close button to `src/catalog/templates/catalog/shell.html` — place it after the `.shell` div but before the `<script>` block. Include `aria-labelledby="lot-modal-title"` on the dialog element. The header should contain `<h2 id="lot-modal-title">Lot Detail</h2>` and a close button `<button class="modal-close" aria-label="Close">&times;</button>`. The body is `<div id="lot-modal-body" class="modal-body"></div>` with a loading spinner inside.
- [X] T002 Add modal JavaScript to the `<script>` block in `src/catalog/templates/catalog/shell.html` — add event listeners for: (a) close button click calls `dialog.close()`, (b) backdrop click (click on `<dialog>` element itself, not children) calls `dialog.close()`, (c) `htmx:afterSwap` on `#lot-modal-body` calls `dialog.showModal()` if dialog is not already open, (d) `closeModal` custom event (from HX-Trigger header) calls `dialog.close()`, (e) `showToast` custom event (from HX-Trigger header) calls the existing `showToast()` function — requires making `showToast()` accessible from `base.html` (e.g., attach to `window`).
- [X] T003 [P] Add modal CSS styles to `src/catalog/static/catalog/styles.css` — add a `/* === Modal === */` section with styles for: `dialog#lot-modal` (max-width 700px, width 90vw, max-height 85vh, border-radius 8px, border none, padding 0, box-shadow), `dialog::backdrop` (background rgba(0,0,0,0.5)), `.modal-container` (display flex, flex-direction column, max-height 85vh), `.modal-header` (display flex, justify-content space-between, align-items center, padding 1rem 1.25rem, border-bottom 1px solid #e2e8f0, flex-shrink 0), `.modal-header h2` (font-size 1.1rem, margin 0), `.modal-close` (background none, border none, font-size 1.5rem, cursor pointer, color #64748b, padding 0.25rem, line-height 1), `.modal-close:hover` (color #1e293b), `.modal-body` (padding 1.25rem, overflow-y auto, flex 1).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the `lot_detail_panel` view, URL route, and add row IDs to the table rows. These enable all three user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add `lot_detail_panel()` view function to `src/catalog/views/panels.py` — handles GET requests. Fetch the lot via `services.get_lot(request, lot_id)`. Build field rows using the same `field_defs` list as in `src/catalog/views/lots.py:lot_detail()` (13 fields: qty, l, w, h, wgt, value, cpack, description, notes, noted_conditions, commodity_id, force_crate, do_not_tip with labels). Compare initial_data vs overriden_data[0] for each field to determine `changed` status. If `?edit=1` query param is present, render `catalog/partials/lot_edit_modal.html`; otherwise render `catalog/partials/lot_detail_modal.html`. Context: `lot`, `has_override`, `rows` (same structure as existing lot_detail view). Wrap API call in try/except ABConnectError, returning error HTML fragment on failure.
- [X] T005 Add URL pattern for `lot_detail_panel` in `src/catalog/urls.py` — add `path("panels/lots/<int:lot_id>/detail/", lot_detail_panel, name="lot_detail_panel")` to `urlpatterns`. Import `lot_detail_panel` from `catalog.views.panels`.
- [X] T006 [P] Add `id="lot-row-{{ row.lot.id }}"` attribute to the `<tr>` element in `src/catalog/templates/catalog/partials/lots_table_row.html` — this enables OOB swap targeting from the modal save response. The `<tr>` currently has `hx-post`, `hx-target`, `hx-swap`, and `hx-indicator` attributes; add the `id` alongside these.

**Checkpoint**: Foundation ready — the modal container exists in the shell, the view endpoint is routed, and table rows have IDs for OOB targeting.

---

## Phase 3: User Story 1 — Lot Detail Modal (Priority: P1) 🎯 MVP

**Goal**: Clicking a lot in the table opens a modal showing full lot detail (all 13 fields, images, override comparison).

**Independent Test**: Click a lot thumbnail in the lots table → modal opens with lot number, customer item ID, field table with initial/override values, changed fields highlighted, and images. Close modal → SPA state unchanged.

### Implementation for User Story 1

- [X] T007 [US1] Create `src/catalog/templates/catalog/partials/lot_detail_modal.html` — HTML fragment (no extends, no base template). Content: (1) Lot header with lot number `{{ lot.catalogs.0.lot_number|default:lot.id }}` and customer item ID `{{ lot.customer_item_id|default:"—" }}` displayed as `<dl class="meta">`. (2) Field table with columns: Field, Initial Value, and (if `has_override`) Override Value. Loop `{% for row in rows %}` rendering each row — use `{% load catalog_tags %}` and `{{ row.initial|display_val }}` / `{{ row.override|display_val }}` for values, `.badge.badge-flag` for boolean flag fields, `.changed` CSS class on override cells when `row.changed` is true. (3) Images section: if `lot.image_links`, display each image in a flex container. (4) "Edit Override" button: `<button hx-get="/panels/lots/{{ lot.id }}/detail/?edit=1" hx-target="#lot-modal-body" hx-swap="innerHTML" class="btn btn-primary">Edit Override</button>`.
- [X] T008 [US1] Add HTMX trigger to the thumbnail cell in `src/catalog/templates/catalog/partials/lots_table_row.html` — modify the `<td class="lot-thumb-cell">` to add `hx-get="/panels/lots/{{ row.lot.id }}/detail/"` `hx-target="#lot-modal-body"` `hx-swap="innerHTML"` and `style="cursor: pointer;"`. These attributes go on the `<td>` element so clicking the thumbnail area opens the modal. The click should NOT trigger the row's `hx-post` (the `<td>` click is separate from the form submit).
- [X] T009 [US1] Update the modal title dynamically in `src/catalog/templates/catalog/shell.html` — in the `htmx:afterSwap` handler for `#lot-modal-body`, read a `data-lot-title` attribute from the first child of `#lot-modal-body` and update `#lot-modal-title` text content. Add `data-lot-title="Lot {{ lot.catalogs.0.lot_number|default:lot.id }}"` to the root element of `lot_detail_modal.html`.

**Checkpoint**: US1 complete — clicking a lot thumbnail opens a modal with full detail view. Modal can be closed via X, backdrop, or Escape.

---

## Phase 4: User Story 2 — Override Editing from Modal (Priority: P2)

**Goal**: Edit and save lot overrides from within the modal, with the table row updating in place.

**Independent Test**: Open lot detail modal → click "Edit Override" → form appears with all 13 fields → change a value → click "Save Override" → modal closes, table row reflects new override (yellow highlight + tooltip), success toast appears.

**Depends on**: US1 (modal must exist to edit within it)

### Implementation for User Story 2

- [X] T010 [US2] Create `src/catalog/templates/catalog/partials/lot_edit_modal.html` — HTML fragment (no extends). Content: (1) Root element with `data-lot-title="Edit Override — Lot {{ lot.catalogs.0.lot_number|default:lot.id }}"`. (2) `<form hx-post="/panels/lots/{{ lot.id }}/detail/" hx-target="#lot-modal-body" hx-swap="innerHTML">` with `{% csrf_token %}`. (3) All 13 form fields rendered using the existing `OverrideForm` instance: loop `{% for field in form %}` in `<div class="form-group">` with label, widget, and error display (same pattern as `override.html`). (4) Form actions: "Save Override" submit button (`.btn.btn-primary`) and "Cancel" button (`<button type="button" hx-get="/panels/lots/{{ lot.id }}/detail/" hx-target="#lot-modal-body" hx-swap="innerHTML" class="btn btn-secondary">Cancel</button>`).
- [X] T011 [US2] Add POST handling to `lot_detail_panel()` in `src/catalog/views/panels.py` — when `request.method == "POST"`: (1) Instantiate `OverrideForm(request.POST)`. (2) If form is valid: save via `services.save_lot_override()`, fetch updated lot, build table row via `build_lot_table_rows([lot])`, render `catalog/partials/lots_table_row.html` as OOB fragment with `hx-swap-oob="outerHTML"` wrapping, and return a minimal response with `HX-Trigger` header containing JSON `{"closeModal": true, "showToast": {"message": "Override saved", "type": "success"}}`. (3) If form invalid: re-render `lot_edit_modal.html` with the form containing errors (same context as GET `?edit=1`). (4) Wrap in try/except ABConnectError for API failures.
- [X] T012 [US2] Add GET `?edit=1` handling to `lot_detail_panel()` in `src/catalog/views/panels.py` — when `request.GET.get("edit") == "1"`: instantiate `OverrideForm` with initial data from the lot's override (if present) or initial_data. Render `catalog/partials/lot_edit_modal.html` with context `{"lot": lot, "form": form}`. Import `OverrideForm` from `catalog.forms`.
- [X] T013 [US2] Expose `showToast()` globally in `src/catalog/templates/catalog/base.html` — change the `showToast` function to `window.showToast = function(msg, type) { ... }` so it can be called from the `showToast` HX-Trigger event handler in the shell's modal JS. Add an HTMX event listener in `base.html`'s script block: `document.body.addEventListener('showToast', function(e) { var d = e.detail; if (d && d.message) window.showToast(d.message, d.type || 'success'); });`.

**Checkpoint**: US2 complete — override editing works end-to-end from modal. Table row updates on save.

---

## Phase 5: User Story 3 — Modal UX Polish (Priority: P3)

**Goal**: Ensure modal close behavior is robust, loading states are clear, and only one modal can be open at a time.

**Independent Test**: Open modal → verify centered overlay with backdrop. Close via X → state preserved. Close via backdrop → state preserved. Close via Escape → state preserved. Open modal while content loading → spinner visible. Try to open second modal → only one appears.

**Depends on**: US1 (modal must exist)

### Implementation for User Story 3

- [X] T014 [US3] Add loading state to modal in `src/catalog/templates/catalog/shell.html` — add a `.modal-loading` spinner inside `#lot-modal-body` as default content (shown until HTMX swap replaces it). Add CSS in `src/catalog/static/catalog/styles.css`: `.modal-loading` centered spinner (reuse `.spinner` class), shown by default, replaced on HTMX swap. Add `hx-indicator` behavior: while the HTMX request to load modal content is in flight, the spinner is visible.
- [X] T015 [US3] Ensure single-modal behavior in `src/catalog/templates/catalog/shell.html` — in the `htmx:afterSwap` handler, before calling `dialog.showModal()`, check `dialog.open` — if already open, do not call `showModal()` again (the content swap is sufficient). In the thumbnail click handler, clear `#lot-modal-body` content before the HTMX request fires (set innerHTML to the loading spinner) so stale content from a previous lot is not briefly visible.
- [X] T016 [US3] Verify backdrop click closes modal in `src/catalog/templates/catalog/shell.html` — the native `<dialog>` element's backdrop click does NOT automatically close it. The click handler on the dialog element should check if `event.target === dialog` (click was on the backdrop/dialog itself, not on content inside it) and call `dialog.close()`. This was specified in T002 but verify it handles edge cases: clicking on padding areas of the dialog, clicking on the modal-container edges.

**Checkpoint**: All user stories complete — modal UX is polished with loading states, single-modal behavior, and robust close handling.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and validation

- [X] T017 [P] Run `ruff check .` from `src/` and fix any linting issues introduced by the new view code in `src/catalog/views/panels.py`
- [X] T018 Validate quickstart.md manual test steps against the implementation — walk through each of the 5 test scenarios in `specs/007-lot-detail-modal/quickstart.md` and verify accuracy of expected behavior descriptions and file paths

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: T004, T005 depend on Phase 1 completion (modal container must exist). T006 is independent [P].
- **US1 (Phase 3)**: Depends on Phase 2 (view + URL + row IDs must exist)
- **US2 (Phase 4)**: Depends on US1 (edit button lives in the detail modal template)
- **US3 (Phase 5)**: Depends on US1 (modal must exist to polish)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US2 (P2)**: Depends on US1 — the "Edit Override" button is in the detail modal template, and the POST handler returns content that replaces the same modal body
- **US3 (P3)**: Can start after US1 — polishes modal behavior that US1 establishes. Can run in parallel with US2 since it modifies different code (shell.html JS vs panels.py/templates)

### Within Each User Story

- Templates before view logic (so view can reference templates)
- View modifications before URL wiring (already done in Phase 2)
- Core implementation before integration refinements

### Parallel Opportunities

- T003 (CSS) runs in parallel with T001/T002 (different files)
- T006 (row IDs) runs in parallel with T004/T005 (different files)
- T014, T015, T016 (US3 tasks) can all run sequentially within shell.html but US3 overall can run in parallel with US2 (different files: shell.html vs panels.py + templates)
- T017 (lint) runs in parallel with T018 (validation)

---

## Parallel Example: Phase 1

```bash
# These touch different files and can run in parallel:
Task T001: "Add <dialog> container to shell.html"      # shell.html
Task T003: "Add modal CSS to styles.css"                # styles.css

# T002 depends on T001 (same file: shell.html)
Task T002: "Add modal JS to shell.html"                 # shell.html (after T001)
```

## Parallel Example: Phase 2

```bash
# These touch different files and can run in parallel:
Task T004: "Add lot_detail_panel view to panels.py"     # panels.py
Task T006: "Add row IDs to lots_table_row.html"         # lots_table_row.html

# T005 depends on T004 (imports the view function)
Task T005: "Add URL pattern to urls.py"                 # urls.py (after T004)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (modal container, JS, CSS) — 3 tasks
2. Complete Phase 2: Foundational (view, URL, row IDs) — 3 tasks
3. Complete Phase 3: US1 (detail template, click trigger, title) — 3 tasks
4. **STOP and VALIDATE**: Click lot thumbnail → modal opens with detail → close modal → SPA state intact
5. This is a usable MVP: operators can view lot details without leaving the shell

### Incremental Delivery

1. Setup + Foundational → Modal infrastructure ready (6 tasks)
2. Add US1 → View lot detail in modal (9 tasks total) → **MVP deployable**
3. Add US2 → Edit overrides from modal (13 tasks total) → Full editing workflow
4. Add US3 → Polish UX (16 tasks total) → Production-ready
5. Polish → Lint + validate (18 tasks total) → Ship

---

## Notes

- Total tasks: **18**
- US1: 3 tasks (Phase 3) + 6 foundational = **9 tasks to MVP**
- US2: 4 tasks (Phase 4)
- US3: 3 tasks (Phase 5)
- Polish: 2 tasks (Phase 6)
- No new data models — all existing entities reused
- No new dependencies — vanilla JS + HTMX + CSS only
- Existing full-page lot detail/override routes preserved (out of scope to remove)

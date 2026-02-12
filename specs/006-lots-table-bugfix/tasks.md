# Tasks: Lots Table & Bugfixes

**Input**: Design documents from `/specs/006-lots-table-bugfix/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Contract tests included — existing test patterns in `tests/contract/test_panels.py`.

**Organization**: Tasks grouped by user story. US1 is independent. US2→US3→US4 are sequential (each builds on the previous).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Foundational

**Purpose**: Service layer and shared infrastructure changes needed before UI work.

- [x] T001 Add `get_lots_for_event` service method in `src/catalog/services.py` that takes a request + list of lot IDs and returns a list of full `LotDto` objects by calling `get_lot()` for each ID
- [x] T002 Add `build_lot_table_rows` helper in `src/catalog/views/panels.py` that takes a list of `LotDto` objects and returns `LotTableRow` dicts with per-field override comparison (value, changed, original) for fields: description, notes, qty, l, w, h, wgt, cpack, force_crate, do_not_tip — following the pattern in `src/catalog/views/lots.py` lines 27-54
- [x] T003 Change default page_size for lots panel from 50 to 25 in `src/catalog/views/panels.py` `event_lots_panel` (update `_parse_page_params` call)

**Checkpoint**: Service layer ready for full lot data fetching.

---

## Phase 2: User Story 1 — Fix Event Selection (Bug)

**Goal**: Clicking multiple events in sequence always loads correct lots without failures.

**Independent Test**: Click seller → click event A → lots load → click event B → lots load → click event A again → lots load. No silent failures (AC-1).

- [x] T004 [US1] Add `{% if not skip_main_oob %}` guard around the `<div id="panel-main-content" hx-swap-oob="innerHTML">` block in `src/catalog/templates/catalog/partials/events_panel.html` (lines 30-35) so the nested OOB only renders when `events_panel.html` is the primary response, not when included from lots panel
- [x] T005 [US1] Pass `skip_main_oob=True` in the `{% include %}` tag in `src/catalog/templates/catalog/partials/lots_panel.html` (line 36) where it includes `events_panel.html` via OOB swap
- [x] T006 [US1] Add contract test `test_lots_panel_oob_does_not_contain_main_clear` in `tests/contract/test_panels.py` — verify that the response from `event_lots_panel` does NOT contain a second `id="panel-main-content"` OOB div that would overwrite the lots content
- [x] T007 [US1] Add contract test `test_events_panel_still_clears_main` in `tests/contract/test_panels.py` — verify that the response from `seller_events_panel` still contains the `id="panel-main-content"` OOB with "Select an event" empty state

**Checkpoint**: Event selection works reliably on repeated clicks. Existing tests still pass.

---

## Phase 3: User Story 2 — Full Lot Data in Panel (Bug)

**Goal**: Lots panel fetches and displays full lot data (thumbnails, descriptions, notes) instead of minimal embedded data.

**Independent Test**: Select an event with lots that have images and descriptions → verify thumbnails and descriptions appear (AC-2, AC-3).

**Dependencies**: Requires T001 (`get_lots_for_event`), T002 (`build_lot_table_rows`), T003 (page_size=25).

- [x] T008 [US2] Modify `event_lots_panel` in `src/catalog/views/panels.py` to: (1) paginate `event.lots` locally to get page of lot IDs, (2) call `get_lots_for_event` to fetch full `LotDto` for each, (3) build `LotTableRow` list via `build_lot_table_rows`, (4) pass `lot_rows` to template context instead of bare `lots`
- [x] T009 [US2] Modify hydration path in `src/catalog/views/sellers.py` (`seller_list` function, lines ~89-104) to fetch full `LotDto` objects for hydrated lots using the same `get_lots_for_event` + `build_lot_table_rows` pattern, passing `lot_rows` to template context
- [x] T010 [US2] Update contract tests in `tests/contract/test_panels.py`: update `_mock_lot` factory to include `initial_data`, `overriden_data`, and `image_links` fields matching `LotDto` shape; update `_mock_event` usage to provide lots with full data; mock `get_lot` calls in `get_lots_for_event`
- [x] T011 [US2] Add contract test `test_lots_panel_contains_thumbnail` in `tests/contract/test_panels.py` — verify lots panel HTML contains `<img` tag with lot image URL when lot has `image_links`
- [x] T012 [US2] Add contract test `test_lots_panel_contains_description` in `tests/contract/test_panels.py` — verify lots panel HTML contains description text from `initial_data.description`

**Checkpoint**: Lots panel shows full lot data. Thumbnails and descriptions visible.

---

## Phase 4: User Story 3 — Lots Table Layout (Feature)

**Goal**: Replace card layout with a table showing columns: img, desc/notes, qty, L, W, H, wgt, cpack, crate, do-not-tip, save.

**Independent Test**: Select an event → verify table renders with all 11 columns and data populates correctly (AC-4).

**Dependencies**: Requires US2 (full lot data available in context).

- [x] T013 [P] [US3] Create `src/catalog/templates/catalog/partials/lots_table_row.html` — single `<tr>` partial for one lot row with `<td>` for each column: img thumbnail (or placeholder SVG), desc+notes, qty, l, w, h, wgt, cpack, crate (checkbox/icon), do-not-tip (checkbox/icon), save button. Each `<td>` uses `row.fields.<field>.value` for display.
- [x] T014 [P] [US3] Create `src/catalog/templates/catalog/partials/lots_table.html` — table wrapper with `<thead>` column headers (Img, Desc/Notes, Qty, L, W, H, Wgt, CPack, Crate, DNT, Save) and `<tbody>` that loops over `lot_rows` and includes `lots_table_row.html` for each
- [x] T015 [US3] Update `src/catalog/templates/catalog/partials/lots_panel.html` to replace the `<ul class="lot-cards">` block with `{% include "catalog/partials/lots_table.html" %}`, passing `lot_rows` context. Keep the panel-header, empty state, pagination, and OOB events sections unchanged.
- [x] T016 [P] [US3] Add table CSS in `src/catalog/static/catalog/styles.css`: `.lots-table` (full width, border-collapse), `.lots-table th` (sticky header, background), `.lots-table td` (padding, vertical-align), `.lot-thumb` (40px thumbnail), `.lot-thumb-placeholder` (SVG placeholder sizing)
- [x] T017 [US3] Add contract test `test_lots_panel_renders_table_with_columns` in `tests/contract/test_panels.py` — verify response contains `<table class="lots-table">` and all column headers: Img, Desc/Notes, Qty, L, W, H, Wgt, CPack, Crate, DNT, Save
- [x] T018 [US3] Update existing lots panel contract tests in `tests/contract/test_panels.py` to expect table markup instead of card markup (replace `lot-card` assertions with `lots-table` assertions)

**Checkpoint**: Lots panel renders as a table with all columns. All data from full LotDto visible.

---

## Phase 5: User Story 4 — Override Display & Save (Feature)

**Goal**: Overridden values are visually highlighted with tooltip showing original; per-row save submits override via HTMX.

**Independent Test**: Find a lot with overrides → verify cells have `class="overridden"` and `title="Original: X"` → edit a value → click save → row updates in place (AC-5, AC-6).

**Dependencies**: Requires US3 (table layout with row partial).

- [x] T019 [US4] Update `src/catalog/templates/catalog/partials/lots_table_row.html` to add `class="overridden"` and `title="Original: {{ row.fields.<field>.original }}"` on each `<td>` where `row.fields.<field>.changed` is True
- [x] T020 [US4] Wrap each `<tr>` in `lots_table_row.html` as an HTMX form: add `hx-post="/panels/lots/{{ row.lot.id }}/override/"` `hx-target="closest tr"` `hx-swap="outerHTML"` `hx-indicator="closest tr"` on the `<tr>` element. Change display `<td>` cells for editable fields (qty, l, w, h, wgt, cpack, description, notes) to `<input>` elements with `name` attributes. Boolean fields (force_crate, do_not_tip) use `<input type="checkbox">`.
- [x] T021 [P] [US4] Add `.overridden` CSS class in `src/catalog/static/catalog/styles.css` — subtle background highlight (e.g., `background: #fff3cd`) and cursor pointer. Add `.lots-table input` sizing for inline inputs.
- [x] T022 [US4] Add `lot_override_panel` view in `src/catalog/views/panels.py` — handles POST to `/panels/lots/{lot_id}/override/`, reads form data, calls `services.save_lot_override()`, re-fetches the lot, builds a single `LotTableRow`, and returns the rendered `lots_table_row.html` partial
- [x] T023 [US4] Add URL route `path("panels/lots/<int:lot_id>/override/", panels.lot_override_panel, name="lot_override_panel")` in `src/catalog/urls.py`
- [x] T024 [US4] Add contract test `test_override_cells_have_class_and_tooltip` in `tests/contract/test_panels.py` — provide a lot with differing initial and override values, verify output contains `class="overridden"` and `title="Original: ` on the changed cells
- [x] T025 [US4] Add contract test `test_lot_override_panel_saves_and_returns_row` in `tests/contract/test_panels.py` — POST form data to `lot_override_panel`, verify `save_lot_override` is called with correct data, verify response contains a `<tr>` with updated values

**Checkpoint**: Overridden cells highlighted, tooltips work, per-row save functional.

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: Final validation and cleanup across all stories.

- [x] T026 Run full test suite (`.venv/bin/python -m pytest tests/ -v`) and fix any failures
- [x] T027 Verify hydration path (`/?seller=X&event=Y`) renders lots table with full data and override highlighting (AC-7)
- [x] T028 Validate `specs/006-lots-table-bugfix/quickstart.md` manual test steps against running application

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies — start immediately
- **Phase 2 (US1)**: Independent — can run in parallel with Phase 1
- **Phase 3 (US2)**: Depends on Phase 1 (T001, T002, T003)
- **Phase 4 (US3)**: Depends on Phase 3 (US2 provides full lot data)
- **Phase 5 (US4)**: Depends on Phase 4 (US3 provides table layout)
- **Phase 6 (Polish)**: Depends on all prior phases

### User Story Dependencies

- **US1**: Independent — no dependencies on other stories
- **US2**: Depends on foundational service methods (T001, T002)
- **US3**: Depends on US2 (needs full lot data in context)
- **US4**: Depends on US3 (needs table row partial for override display + save)

### Parallel Opportunities

Within Phase 1:
- T001 and T002 can run in parallel (different functions, no dependencies)

Within Phase 2 (US1):
- T004 and T005 can run in parallel (different template files)
- T006 and T007 can run in parallel (independent tests)

Within Phase 4 (US3):
- T013 and T014 can run in parallel (different template files)
- T016 can run in parallel with T013/T014 (CSS file, no conflicts)

Within Phase 5 (US4):
- T021 can run in parallel with T019/T020 (CSS vs template)

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: Foundational service methods
2. Complete Phase 2: US1 — fix event selection bug
3. Complete Phase 3: US2 — full lot data
4. **STOP and VALIDATE**: Event selection works, thumbnails/descriptions visible
5. Deploy if ready — card layout with full data is already an improvement

### Full Delivery

6. Complete Phase 4: US3 — table layout
7. Complete Phase 5: US4 — override display + save
8. Complete Phase 6: Polish and validation
9. Deploy complete feature

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Lot data fetching uses individual `get_lot()` calls (no batch API available)
- Default page_size reduced to 25 to keep API calls manageable
- Override comparison reuses pattern from existing `lot_detail` view
- The `skip_main_oob` template variable is the minimal fix for the OOB bug

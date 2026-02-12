# Tasks: Shell UX Fixes

**Input**: Design documents from `/specs/005-shell-ux-fixes/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/endpoints.md, quickstart.md

**Tests**: Included — constitution requires executable verification (Principle II), and contracts define 11 test requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

---

## Phase 1: Foundational — Service Layer Additions

**Purpose**: Add service methods needed by multiple user stories. Blocks US1 (customer-friendly URL hydration).

- [X] T001 Add `find_seller_by_display_id(request, display_id)` service method in `src/catalog/services.py` that calls `api.sellers.list(CustomerDisplayId=display_id)` and returns the first match or None

**Checkpoint**: New service method available. `pytest` passes (no behavioral change yet).

---

## Phase 2: User Story 5 — PR #5 Review Bug Fixes (Priority: P1) 🎯 MVP

**Goal**: Resolve all P0/P1 issues from `specs/004-shell-interaction-polish/pr-5-review.md`: broken pagination URLs, unsafe parsing, hydration integrity, mobile reset, and indicator wiring.

**Independent Test**: Hydrated shell at `/?seller=X&event=Y` has working pagination links. Bad query params on `/` return 200. Resize mobile→desktop→mobile starts at sellers. Clicking a seller shows spinner on Left2 panel.

### Tests for User Story 5

- [X] T002 [P] [US5] Add contract tests in `tests/contract/test_panels.py`: (1) shell at `/?seller=X` with `?page=abc` returns 200 not 500, (2) hydrated events panel contains valid `hx-get` pagination URL starting with `/panels/sellers/`, (3) hydrated lots panel contains valid `hx-get` pagination URL starting with `/panels/events/`, (4) hydration with mismatched seller/event ignores event and renders seller-only state
- [X] T003 [P] [US5] Add contract test in `tests/contract/test_panels.py` verifying seller list items have `hx-indicator` attribute and event list items have `hx-indicator` attribute

### Implementation for User Story 5

- [X] T004 [US5] Replace raw `int()` page/page_size parsing in `src/catalog/views/sellers.py` shell path (lines 22-23) with `_parse_page_params` helper (already exists in panels.py — import or duplicate)
- [X] T005 [US5] Fix hydrated events include in `src/catalog/templates/catalog/shell.html` to pass concrete `pagination_url` value (e.g., `/panels/sellers/{{ selected_seller_id }}/events/`) instead of empty string
- [X] T006 [US5] Fix hydrated lots include in `src/catalog/templates/catalog/shell.html` to pass concrete `pagination_url` value (e.g., `/panels/events/{{ selected_event_id }}/lots/`) instead of empty string
- [X] T007 [US5] Fix OOB events include in `src/catalog/templates/catalog/partials/lots_panel.html` to pass concrete `pagination_url` (e.g., `/panels/sellers/{{ oob_seller_id }}/events/`) instead of empty string
- [X] T008 [US5] Add event-belongs-to-seller validation in `src/catalog/views/sellers.py` hydration: after fetching event, check `event.sellers` contains the selected seller; if not, skip event hydration
- [X] T009 [US5] Update mobile resize handler in `src/catalog/templates/catalog/shell.html` JS to reset `shell.setAttribute('data-mobile-panel', 'sellers')` when viewport crosses to desktop width
- [X] T010 [US5] Add `hx-indicator="#panel-left2"` attribute on seller list `<li>` items in `src/catalog/templates/catalog/partials/seller_list_panel.html`
- [X] T011 [US5] Add `hx-indicator="#panel-main"` attribute on event list `<li>` items in `src/catalog/templates/catalog/partials/events_panel.html`
- [X] T012 [US5] Add optional `indicator_id` param to `src/catalog/templates/catalog/partials/panel_pagination.html` and set `hx-indicator="{{ indicator_id }}"` on pagination `<a>` tags; update all pagination includes to pass the appropriate panel ID (`#panel-left1`, `#panel-left2`, `#panel-main`)

**Checkpoint**: All PR #5 review P0/P1 bugs fixed. Pagination works in hydrated/OOB contexts. Spinners show on correct panels. `pytest` passes.

---

## Phase 3: User Story 2 — Fix Lots Panel Data (Priority: P1)

**Goal**: Lots panel shows exactly the lots belonging to the selected catalog, not random or missing data.

**Independent Test**: Click an event → lots shown are exactly for that event. Click another event → lots update correctly. Event with no lots → "No lots in this event".

### Tests for User Story 2

- [X] T013 [P] [US2] Add contract test in `tests/contract/test_panels.py` verifying `event_lots_panel` calls service with correct `customer_catalog_id` and renders matching lots

### Implementation for User Story 2

- [X] T014 [US2] Modify `event_lots_panel` in `src/catalog/views/panels.py` to use lots from expanded catalog response (`event.lots`) with local pagination instead of `services.list_lots_by_catalog`, matching the pattern in `src/catalog/views/events.py` lines 15-26. Build a paginated result from the embedded lot list.

**Checkpoint**: Lots panel shows correct data for each event. `pytest` passes.

---

## Phase 4: User Story 1 — Customer-Friendly URL Identifiers (Priority: P1)

**Goal**: URLs show customer-facing IDs (`?seller=4098&event=395768`) instead of internal database IDs.

**Independent Test**: Click seller → URL shows `?seller=<4-digit display ID>`. Click event → URL shows `?seller=4098&event=395768`. Copy URL, open new tab → same state renders.

### Tests for User Story 1

- [X] T015 [P] [US1] Add contract tests in `tests/contract/test_panels.py`: (1) `seller_events_panel` `HX-Push-Url` contains `customer_display_id` not internal ID, (2) `event_lots_panel` `HX-Push-Url` contains `customer_display_id` and `customer_catalog_id`
- [X] T016 [P] [US1] Add contract tests in `tests/contract/test_panels.py`: (1) shell at `/?seller=<display_id>` resolves correct seller and renders events, (2) shell at `/?seller=<display_id>&event=<catalog_id>` resolves both and renders lots

### Implementation for User Story 1

- [X] T017 [US1] Modify `seller_events_panel` in `src/catalog/views/panels.py` to set `HX-Push-Url` to `/?seller={seller.customer_display_id}` instead of `/?seller={seller_id}`
- [X] T018 [US1] Modify `event_lots_panel` in `src/catalog/views/panels.py` to set `HX-Push-Url` to `/?seller={seller_display_id}&event={event.customer_catalog_id}` where `seller_display_id` is resolved from `event.sellers[0].customer_display_id`
- [X] T019 [US1] Modify shell hydration in `src/catalog/views/sellers.py` to: (1) read `seller` param as `customer_display_id` and look up via `find_seller_by_display_id`, (2) read `event` param as `customer_catalog_id` and look up via `find_catalog_by_customer_id`, (3) use resolved internal IDs for template context (`selected_seller_id`, `selected_event_id`)
- [X] T020 [US1] Update existing `HX-Push-Url` contract tests in `tests/contract/test_panels.py` (`TestUrlPushContract`) to assert customer-friendly ID values instead of internal IDs

**Checkpoint**: URLs use customer-friendly IDs. Shared links work. `pytest` passes.

---

## Phase 5: User Story 3 — Improved Empty States & Feedback (Priority: P2)

**Goal**: Clear, contextual feedback when panels are empty or loading. No confusing stale messages.

**Independent Test**: Select seller → Left2 loads events, Main shows "Select an event to view lots". Select event → Main shows lots. Select different seller → Main shows "Select an event to view lots" (not stale lot data or confusing text).

### Tests for User Story 3

- [X] T021 [P] [US3] Add contract test in `tests/contract/test_panels.py` verifying events_panel response's OOB `#panel-main-content` contains "Select an event to view lots" text

### Implementation for User Story 3

- [X] T022 [US3] Verify and ensure OOB `#panel-main-content` clear in `src/catalog/templates/catalog/partials/events_panel.html` shows "Select an event to view lots" (currently correct — confirm no regressions from other changes)

**Checkpoint**: Empty states are contextual and accurate. `pytest` passes.

---

## Phase 6: User Story 4 — Panel Header Filters (Priority: P2)

**Goal**: Sellers and events panels have inline filter inputs in headers. Filters drive HTMX-powered list reloading. When a record is selected, filter shows "Selected: <name>" as placeholder.

**Independent Test**: Type in sellers filter → sellers list filters. Type in events filter → events list filters. Click a seller → seller filter shows placeholder "Selected: <name>". Clear filter → full list reloads.

### Tests for User Story 4

- [X] T023 [P] [US4] Add contract tests in `tests/contract/test_panels.py`: (1) `sellers_panel` with `?name=Test` calls `list_sellers` with Name filter, (2) `seller_events_panel` with `?title=Test` calls `list_catalogs` with Title filter
- [X] T024 [P] [US4] Add contract test in `tests/contract/test_panels.py` verifying seller list panel HTML contains a `panel-filter` form element

### Implementation for User Story 4

- [X] T025 [US4] Move sellers panel header from `src/catalog/templates/catalog/shell.html` into `src/catalog/templates/catalog/partials/seller_list_panel.html` — replace static `<h3>` with a `<form class="panel-filter">` containing a text input (`name="name"`) with `hx-get="/panels/sellers/"` and `hx-target="#panel-left1-content"`, plus count badge. Include `selected` as hidden input if `selected_seller_id` is set.
- [X] T026 [US4] Replace events panel header in `src/catalog/templates/catalog/partials/events_panel.html` — replace static `<h3>` with a `<form class="panel-filter">` containing a text input (`name="title"`) with `hx-get="/panels/sellers/{{ seller_id }}/events/"` and `hx-target="#panel-left2-content"`, plus count badge
- [X] T027 [US4] Modify `sellers_panel` in `src/catalog/views/panels.py` to read optional `name` query param and pass `Name=name` filter to `services.list_sellers()`. Pass `filter_name` to template context.
- [X] T028 [US4] Modify `seller_events_panel` in `src/catalog/views/panels.py` to read optional `title` query param and pass `Title=title` filter to `services.list_catalogs()`. Pass `filter_title` to template context.
- [X] T029 [US4] Pass `selected_seller_name` context variable in `seller_events_panel` OOB seller list re-render (from `seller.name`) so filter input placeholder shows "Selected: <name>". Update `seller_list_panel.html` filter input: when `selected_seller_id` is set, use `placeholder="Selected: {{ selected_seller_name }}"` with empty value.
- [X] T030 [US4] Pass `selected_event_title` context variable in `event_lots_panel` OOB events re-render. Update `events_panel.html` filter input: when `selected_event_id` is set, use `placeholder="Selected: {{ selected_event_title }}"` with empty value.
- [X] T031 [P] [US4] Add panel filter CSS styles in `src/catalog/static/catalog/styles.css`: `.panel-filter` form layout (flex row), `.panel-filter-input` styling (small font, transparent border, full width), selected-placeholder styling

**Checkpoint**: Panel headers have working filters. Selected state shows placeholder. `pytest` passes.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories

- [X] T032 Run full test suite (`pytest`) and fix any failures
- [X] T033 Validate all quickstart.md verification steps against running application

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — start immediately. BLOCKS US1.
- **US5 (Phase 2)**: Depends on Phase 1 only. BLOCKS US1 (pagination/hydration fixes must be in place).
- **US2 (Phase 3)**: Depends on Phase 1 only. Can run in parallel with US5.
- **US1 (Phase 4)**: Depends on Phase 1 + Phase 2 (needs service methods and bug-fixed hydration).
- **US3 (Phase 5)**: No dependencies beyond Phase 1. Can run in parallel with US5/US2.
- **US4 (Phase 6)**: Depends on Phase 2 (modifies same templates). Should run after US5.
- **Polish (Phase 7)**: Depends on all user stories being complete.

### Within Each User Story

- Tests written first (should fail before implementation)
- View logic before template changes
- Templates before CSS

### Parallel Opportunities

- T002 and T003 (US5 tests) can run in parallel
- T013 (US2 test) can run in parallel with US5 implementation
- T015 and T016 (US1 tests) can run in parallel
- T021 (US3 test) can run in parallel with US1/US2 implementation
- T023 and T024 (US4 tests) can run in parallel
- T031 (US4 CSS) can run in parallel with US4 view/template tasks

---

## Implementation Strategy

### MVP First (US5 + US2 — Fix Broken Things)

1. Complete Phase 1: Foundational (service method)
2. Complete Phase 2: US5 (PR #5 bug fixes)
3. Complete Phase 3: US2 (lots data fix)
4. **STOP and VALIDATE**: Broken things are fixed. Pagination works. Lots are correct.

### Incremental Delivery

1. Phase 1 → Service foundation
2. Phase 2 (US5) → Bug fixes (production-grade shell)
3. Phase 3 (US2) → Correct lots data
4. Phase 4 (US1) → Customer-friendly URLs
5. Phase 5 (US3) → Better empty states
6. Phase 6 (US4) → Panel filters (biggest new feature)
7. Phase 7 → Polish and validate

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- All views are in panels.py or sellers.py so view tasks within a story are sequential
- The lots fix (US2) changes the data source but keeps the same template rendering
- Customer-friendly IDs (US1) change HX-Push-Url headers AND hydration lookup — both must change together
- Filter inputs (US4) require moving sellers header from shell.html into seller_list_panel.html
- hx-indicator wiring requires updates to panel_pagination.html (shared partial) with optional indicator_id param

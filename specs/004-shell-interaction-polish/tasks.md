# Tasks: Shell Interaction Polish

**Input**: Design documents from `/specs/004-shell-interaction-polish/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/endpoints.md, quickstart.md

**Tests**: Included — constitution requires executable verification (Principle II), and contracts define 13 test requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Foundational — Pagination Validation

**Purpose**: Defensive pagination parameter parsing that all panel views share. Blocks all user stories since views are modified in every story.

- [X] T001 Add `_parse_page_params(request, default_page_size=50)` helper to `src/catalog/views/panels.py` that clamps `page` to `max(1, int(...))` and `page_size` to `max(1, min(200, int(...)))`, returning defaults on `ValueError`/`TypeError`
- [X] T002 Refactor `sellers_panel`, `seller_events_panel`, and `event_lots_panel` in `src/catalog/views/panels.py` to use `_parse_page_params()` instead of raw `int()` parsing
- [X] T003 [P] Add contract tests for pagination validation in `tests/contract/test_panels.py`: invalid page returns 200 with page 1, negative page clamps to 1, oversized page_size clamps to 200

**Checkpoint**: All panel endpoints handle bad pagination params gracefully (200, not 500). `pytest` passes.

---

## Phase 2: User Story 1 — Active Selection Highlighting (Priority: P1) 🎯 MVP

**Goal**: Selected seller and event rows display `.active` CSS class via server-side OOB swaps, surviving pagination.

**Independent Test**: Click a seller → it highlights in Left1. Click an event → it highlights in Left2. Seller stays highlighted. Paginate sellers → selected seller remains highlighted if on current page. Click different seller → old highlight clears, new one appears.

### Tests for User Story 1

- [X] T004 [P] [US1] Add contract tests for seller selection in `tests/contract/test_panels.py`: (1) `GET /panels/sellers/?selected=42` renders `.active` on seller 42, (2) `GET /panels/sellers/{id}/events/` response contains OOB `#panel-left1-content` with `.active` on selected seller
- [X] T005 [P] [US1] Add contract tests for event selection in `tests/contract/test_panels.py`: (1) `GET /panels/events/{id}/lots/` response contains OOB `#panel-left2-content` with `.active` on selected event

### Implementation for User Story 1

- [X] T006 [US1] Modify `sellers_panel` view in `src/catalog/views/panels.py` to read `selected` query param and pass `selected_seller_id` to template context
- [X] T007 [US1] Modify `seller_events_panel` view in `src/catalog/views/panels.py` to re-fetch current sellers page via `services.list_sellers()` and pass `selected_seller_id=seller_id` plus sellers data for OOB re-render
- [X] T008 [US1] Append OOB swap block to `src/catalog/templates/catalog/partials/events_panel.html` that re-renders `seller_list_panel.html` into `#panel-left1-content` with `selected_seller_id` context
- [X] T009 [US1] Modify `event_lots_panel` view in `src/catalog/views/panels.py` to resolve parent seller from event data, re-fetch events via `services.list_catalogs()`, and pass `selected_event_id=event_id` plus events data for OOB re-render
- [X] T010 [US1] Append OOB swap block to `src/catalog/templates/catalog/partials/lots_panel.html` that re-renders `events_panel.html` into `#panel-left2-content` with `selected_event_id` context (without the nested OOB for sellers to avoid double-swap)
- [X] T011 [US1] Update `src/catalog/templates/catalog/partials/panel_pagination.html` to accept and forward an optional `extra_params` string (e.g., `&selected=42`) in pagination `hx-get` URLs so selection survives pagination

**Checkpoint**: Seller and event highlighting works via OOB swaps. Selection survives pagination. `pytest` passes.

---

## Phase 3: User Story 2 — Consistent Loading Indicators (Priority: P2)

**Goal**: All three panels show identical spinner overlay during HTMX requests.

**Independent Test**: Click a seller → Left2 shows spinner. Paginate sellers → Left1 shows spinner. Click an event → Main shows spinner. All three spinners look identical.

### Tests for User Story 2

- [X] T012 [P] [US2] Add contract test in `tests/contract/test_panels.py` verifying shell HTML contains `.htmx-indicator` div inside all three panel containers (`#panel-left1`, `#panel-left2`, `#panel-main`)

### Implementation for User Story 2

- [X] T013 [US2] Add `.htmx-indicator` div with spinner inside `#panel-left1` in `src/catalog/templates/catalog/shell.html`, matching the existing markup pattern in Left2 and Main. Ensure Left1 content is wrapped in a `.panel-content` div so the existing `.htmx-request .panel-content { opacity: 0.5 }` rule applies.

**Checkpoint**: All three panels show identical loading behavior. `pytest` passes.

---

## Phase 4: User Story 3 — URL-Addressable Shell State (Priority: P3)

**Goal**: Browser URL reflects current selection (`/?seller=<id>&event=<id>`). Shareable links work. Back/forward buttons restore state.

**Independent Test**: Click seller → URL shows `?seller=42`. Click event → URL shows `?seller=42&event=7`. Copy URL, open new tab → same state renders. Back button restores previous state.

### Tests for User Story 3

- [X] T014 [P] [US3] Add contract tests for `HX-Push-Url` headers in `tests/contract/test_panels.py`: (1) `seller_events_panel` response has `HX-Push-Url: /?seller={id}`, (2) `event_lots_panel` response has `HX-Push-Url: /?seller={sid}&event={eid}`
- [X] T015 [P] [US3] Add contract tests for shell hydration in `tests/contract/test_panels.py`: (1) `GET /?seller=42` renders events in Left2 with seller highlighted, (2) `GET /?seller=42&event=7` renders events + lots with both highlighted, (3) `GET /?seller=abc` renders default shell without error

### Implementation for User Story 3

- [X] T016 [US3] Add `HX-Push-Url` response header to `seller_events_panel` in `src/catalog/views/panels.py` with value `/?seller={seller_id}`
- [X] T017 [US3] Add `HX-Push-Url` response header to `event_lots_panel` in `src/catalog/views/panels.py` with value `/?seller={seller_id}&event={event_id}` (seller_id resolved from event data)
- [X] T018 [US3] Modify shell view in `src/catalog/views/sellers.py` to read `seller` and `event` query params, conditionally fetch events and lots, and pass `selected_seller_id`, `selected_event_id`, `events`, `lots`, and paginated data to template context. Silently ignore invalid/non-integer params.
- [X] T019 [US3] Update `src/catalog/templates/catalog/shell.html` to conditionally render pre-populated Left2 content (events list via `events_panel.html` include) and Main content (lots list via `lots_panel.html` include) when hydration data is present, instead of empty-state placeholders

**Checkpoint**: URLs are shareable, back/forward works, hydration renders correct state. `pytest` passes.

---

## Phase 5: User Story 4 — Mobile/Narrow Viewport Layout (Priority: P4)

**Goal**: On viewports < 768px, panels show one at a time with back button navigation. Drill-down: Sellers → Events → Lots.

**Independent Test**: Resize browser to < 768px. Only Sellers panel visible. Click seller → Events panel appears with back button. Click event → Lots panel appears. Back button navigates backwards. Resize to desktop → all three panels visible.

### Tests for User Story 4

- [X] T020 [P] [US4] Add contract test in `tests/contract/test_panels.py` verifying shell HTML contains `data-mobile-panel` attribute on `.shell`, `data-panel` attributes on each panel, `mobile-back-btn` element, and `panel-announcer` ARIA live region

### Implementation for User Story 4

- [X] T021 [US4] Add `data-mobile-panel="sellers"` attribute to `.shell` div and `data-panel` attributes (`sellers`, `events`, `lots`) to each panel in `src/catalog/templates/catalog/shell.html`
- [X] T022 [P] [US4] Add responsive CSS in `src/catalog/static/catalog/styles.css`: media query `@media (max-width: 767px)` that sets grid to single column, hides all panels, shows panel matching `[data-mobile-panel]` value, styles mobile back button, and adds `.sr-only` utility class
- [X] T023 [US4] Add mobile back button element and ARIA live region `#panel-announcer` to `src/catalog/templates/catalog/shell.html`
- [X] T024 [US4] Add mobile panel-switching JavaScript IIFE in `src/catalog/templates/catalog/shell.html` that: (1) listens for `htmx:afterSwap` to show events/lots panel, (2) handles back button clicks, (3) manages focus to first interactive element on panel switch, (4) announces panel changes via ARIA live region, (5) resets on resize to desktop

**Checkpoint**: Mobile layout works with drill-down navigation and back button. Desktop layout unaffected. `pytest` passes.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories

- [X] T025 Run full test suite (`pytest`) and fix any failures
- [X] T026 Validate all quickstart.md verification steps against running application

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — start immediately. BLOCKS all user stories.
- **US1 (Phase 2)**: Depends on Phase 1. BLOCKS US3 (URL state needs selection context).
- **US2 (Phase 3)**: Depends on Phase 1 only. Can run in parallel with US1.
- **US3 (Phase 4)**: Depends on Phase 1 + Phase 2 (needs selection state to push correct URLs and hydrate correctly).
- **US4 (Phase 5)**: Depends on Phase 1 only. Can run in parallel with US1/US2. Should run after US3 for best integration.
- **Polish (Phase 6)**: Depends on all user stories being complete.

### Within Each User Story

- Tests written first (should fail before implementation)
- View logic before template changes
- Templates before CSS/JS

### Parallel Opportunities

- T004 and T005 (US1 tests) can run in parallel
- T012 (US2 test) can run in parallel with US1 implementation
- T014 and T015 (US3 tests) can run in parallel
- T020 (US4 test) can run in parallel with US3 implementation
- T022 (US4 CSS) can run in parallel with T021 (US4 HTML attributes)

---

## Parallel Example: User Story 1

```text
# Launch tests in parallel:
Task: T004 — Contract tests for seller selection
Task: T005 — Contract tests for event selection

# Then implement sequentially (same file):
Task: T006 — sellers_panel selected param
Task: T007 — seller_events_panel OOB re-render
Task: T008 — events_panel.html OOB block
Task: T009 — event_lots_panel OOB re-render
Task: T010 — lots_panel.html OOB block
Task: T011 — panel_pagination.html extra params
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational (pagination validation)
2. Complete Phase 2: User Story 1 (selection highlighting)
3. **STOP and VALIDATE**: Click sellers/events, verify `.active` class, verify pagination preserves selection
4. All other stories add incremental value without breaking US1

### Incremental Delivery

1. Phase 1 → Pagination safety net
2. Phase 2 (US1) → Selection highlighting (MVP!)
3. Phase 3 (US2) → Loading indicators (quick win — 1 task)
4. Phase 4 (US3) → URL state (builds on US1 selection context)
5. Phase 5 (US4) → Mobile layout (independent CSS/JS)
6. Phase 6 → Polish and validate

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- All views are in the same file (`panels.py`) so view tasks within a story are sequential
- Template OOB blocks must NOT nest (lots_panel OOB should NOT include events_panel's own OOB for sellers)
- The `HX-Push-Url` header requires seller_id in `event_lots_panel` — resolve from event data before setting header
- Mobile JS runs only on narrow viewports (early return on desktop) — zero performance impact on desktop

# Tasks: SPA Shell Layout

**Input**: Design documents from `/specs/003-spa-shell-layout/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/endpoints.md, quickstart.md

**Tests**: Included — constitution requires contract tests for all new endpoints (Principle II: Executable Knowledge).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create new files and register routes needed by all subsequent phases

- [X] T001 Create panel views module with imports in src/catalog/views/panels.py
- [X] T002 Register panel URL routes in src/catalog/urls.py — add `panels/sellers/`, `panels/sellers/<int:seller_id>/events/`, `panels/events/<int:event_id>/lots/` pointing to views in panels.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shell layout structure and base template updates that MUST be complete before any user story panel work can begin

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Add CSS Grid shell layout styles to src/catalog/static/catalog/styles.css — add `.shell` grid container (`grid-template-columns: 250px 300px 1fr`, `grid-template-rows: auto 1fr`, `height: 100vh`), `.panel` base styles (`overflow-y: auto`, `min-height: 0`), panel-specific classes (`.panel-left1`, `.panel-left2`, `.panel-main`), `.panel-list`, `.panel-item`, `.panel-header`, `.panel-table`, `.panel-pagination` component styles. Preserve all existing CSS rules.
- [X] T004 Create three-panel SPA shell template in src/catalog/templates/catalog/shell.html — extends base.html, overrides content block with a `.shell` grid div containing: `#panel-left1` (with `hx-sync="this:replace"`), `#panel-left2` (with `hx-sync="this:replace"`), and `#panel-main` wrapping `#panel-main-content`. Left1 uses `{% include "catalog/partials/seller_list_panel.html" %}` for initial load. Left2 and Main show empty-state placeholders. Include HTMX CSRF header setup via `hx-headers`.
- [X] T005 Update navbar in src/catalog/templates/catalog/base.html — replace text "Catalog Manager" in `.nav-brand` with an `<img>` tag referencing `{% static 'catalog/lotsdb_logo.svg' %}` with appropriate sizing (height ~28px). Preserve all existing navbar elements (import link, dropzone, search form, logout).

**Checkpoint**: Shell structure ready — panels exist but contain placeholder content only

---

## Phase 3: User Story 1 — Three-Panel Browse (Priority: P1) MVP

**Goal**: Clicking a seller loads events in Left2 via HTMX; clicking an event loads lots in Main via HTMX. No full page reloads. Selected items are visually highlighted.

**Independent Test**: Login → home page shows three panels with sellers loaded → click a seller → events appear in Left2 (no reload, seller highlighted) → click an event → lots appear in Main (no reload, event highlighted) → click a different seller → events update, lots clear.

### Contract Tests for User Story 1

- [X] T006 [P] [US1] Write contract tests for all 3 panel endpoints in tests/contract/test_panels.py — test each endpoint returns HTML fragment (no `<!DOCTYPE>`), verify DOM structure contains expected classes (`panel-list`, `panel-item`, `panel-header`), verify HTMX attributes (`hx-get`, `hx-target`) are present on interactive elements, verify `hx-swap-oob` fragment is included in seller_events_panel response, verify empty state is rendered when API returns zero results, verify error state on API failure. Use Django TestCase + RequestFactory with mocked services.

### Implementation for User Story 1

- [X] T007 [P] [US1] Create seller list panel partial in src/catalog/templates/catalog/partials/seller_list_panel.html — render `<ul class="panel-list">` with `<li class="panel-item">` for each seller. Each item has `hx-get="/panels/sellers/{{ seller.id }}/events/"` and `hx-target="#panel-left2"`. Display seller name, `customer_display_id`, and active/inactive badge. Support `.active` class for selected state via template variable `selected_seller_id`.
- [X] T008 [P] [US1] Create events panel partial in src/catalog/templates/catalog/partials/events_panel.html — render panel header with seller name and event count, `<ul class="panel-list">` with `<li class="panel-item">` for each event. Each item has `hx-get="/panels/events/{{ event.id }}/lots/"` and `hx-target="#panel-main-content"`. Display event title, date range, agent, and completed/active badge. Support `.active` class for selected state.
- [X] T009 [P] [US1] Create lots panel partial in src/catalog/templates/catalog/partials/lots_panel.html — render panel header with event title and lot count, `<table class="panel-table">` with lot rows. Each lot number is a standard `<a href="/lots/{{ lot.id }}/">` link (full page navigation, not HTMX). Display lot number and customer_item_id columns.
- [X] T010 [US1] Implement all three panel views in src/catalog/views/panels.py — `sellers_panel(request)`: call `services.list_sellers()` with page/page_size params, render `seller_list_panel.html`. `seller_events_panel(request, seller_id)`: call `services.list_catalogs()` filtered by seller_id, render `events_panel.html` as primary response PLUS OOB fragment `<div id="panel-main-content" hx-swap-oob="innerHTML">` containing empty-state placeholder to clear the lots panel. `event_lots_panel(request, event_id)`: call `services.get_catalog()`, extract lots, render `lots_panel.html`.
- [X] T011 [US1] Modify home page view in src/catalog/views/sellers.py — update `seller_list` view: when the request path is `/` (home), render `catalog/shell.html` with sellers context instead of `catalog/sellers/list.html`. Keep `/sellers/` rendering the existing full-page seller list template unchanged.
- [X] T012 [US1] Wire HTMX attributes across templates — ensure shell.html panels have `hx-sync="this:replace"` on `#panel-left1` and `#panel-left2` containers for request cancellation. Verify `hx-target` attributes in seller_list_panel.html point to `#panel-left2` and events_panel.html point to `#panel-main-content`. Add `hx-swap="innerHTML"` where needed. Test the click-through flow: seller → events → lots.

**Checkpoint**: Three-panel HTMX navigation works end-to-end. Contract tests pass.

---

## Phase 4: User Story 2 — Professional Visual Design (Priority: P1)

**Goal**: Refine the visual design to production quality — branded navbar, polished panel styling, loading indicators, empty states with icons, hover transitions, selection highlights. The UI should feel like a shipped product.

**Independent Test**: Load the app and visually confirm: LotsDB logo in header, consistent spacing, professional empty states with messaging, smooth hover transitions, loading spinners during HTMX fetches, clear selection highlighting on active seller/event items.

**Depends on**: US1 (panels must exist to style)

### Implementation for User Story 2

- [X] T013 [P] [US2] Add professional empty-state placeholders to panel partials — update events_panel.html and lots_panel.html empty states: include an SVG icon or CSS-drawn graphic, descriptive message ("Select a seller to view events" / "Select an event to view lots"), muted color styling. Also add empty states for zero-data cases ("No events for this seller" / "No lots in this event") in src/catalog/templates/catalog/partials/events_panel.html and src/catalog/templates/catalog/partials/lots_panel.html.
- [X] T014 [P] [US2] Add HTMX loading indicators to shell.html and styles.css — add `<div class="htmx-indicator">` spinner elements inside `#panel-left2` and `#panel-main-content` in src/catalog/templates/catalog/shell.html. Add CSS for `.htmx-indicator` (hidden by default, visible when `.htmx-request` is on parent) and a subtle CSS spinner animation in src/catalog/static/catalog/styles.css.
- [X] T015 [US2] Refine panel visual styling in src/catalog/static/catalog/styles.css — add selection highlight for `.panel-item.active` (left border accent, background tint), smooth hover transitions on `.panel-item` (background change, 150ms ease), panel border/divider styling between columns, panel header styling (`.panel-header` with bottom border, font weight, item count), refined typography scale for panel items (title, meta, badges).
- [X] T016 [US2] Style navbar consistently in src/catalog/static/catalog/styles.css — ensure logo, search input, dropzone, and user controls are visually balanced. Refine spacing between navbar elements. Ensure dropzone styling is consistent with the new design language. Adjust `.nav-brand` to accommodate the logo image.

**Checkpoint**: Visual design is polished and production-ready. All panels have professional styling, empty states, and loading indicators.

---

## Phase 5: User Story 3 — Scrollable Panels with Pagination (Priority: P2)

**Goal**: Each panel handles large datasets with independent scrolling and HTMX-powered pagination controls (prev/next) that swap content within their own panel only.

**Independent Test**: Access a seller with many events. Confirm events panel shows pagination controls and clicking "Next" loads page 2 within the events panel only (seller panel unchanged). Click a different seller — events reset to page 1.

**Depends on**: US1 (panels must exist to paginate)

### Implementation for User Story 3

- [X] T017 [P] [US3] Create panel pagination partial in src/catalog/templates/catalog/partials/panel_pagination.html — render prev/next links using `hx-get` with page parameter and `hx-target` pointing to the panel's own content container. Accept template variables: `has_previous`, `has_next`, `previous_page`, `next_page`, `base_url`, `target_id`. Style with `.panel-pagination` class.
- [X] T018 [US3] Add pagination to all three panel views and templates — update `sellers_panel` view in src/catalog/views/panels.py to pass pagination context (page, has_previous, has_next). Include `{% include "catalog/partials/panel_pagination.html" %}` in seller_list_panel.html with `target_id="#panel-left1-content"`. Repeat for `seller_events_panel` (target Left2) and `event_lots_panel` (target Main). Ensure pagination links use `hx-get` so they swap within their own panel via HTMX without affecting other panels.
- [X] T019 [US3] Add pagination contract tests in tests/contract/test_panels.py — add test cases verifying: `?page=2` returns second page of results, pagination nav HTML is present when results exceed page_size, pagination `hx-target` points to the correct panel ID, page resets to 1 when a new seller/event is selected (verified by checking OOB fragment does not carry forward page state).

**Checkpoint**: All three panels paginate independently. Scrolling in one panel does not affect others.

---

## Phase 6: User Story 4 — Preserved Navigation to Detail Views (Priority: P2)

**Goal**: Lot rows link to existing full-page lot detail views. All existing pages (lot detail, override, search, import) continue to work. The SPA shell augments but does not break existing navigation.

**Independent Test**: From three-panel layout, click a lot → lot detail page opens. Back button returns to shell. Navigate to `/sellers/`, `/events/<id>/`, `/imports/`, `/search/?q=test` directly — all render correctly.

**Depends on**: US1 (lots panel must exist)

### Implementation for User Story 4

- [X] T020 [US4] Verify lot links in lots_panel.html use standard `<a href>` navigation (not `hx-get`) in src/catalog/templates/catalog/partials/lots_panel.html — ensure clicking a lot triggers full-page navigation to `/lots/<id>/`. Verify the lot detail page renders correctly with the updated base.html (logo in navbar).
- [X] T021 [US4] Verify all existing pages render correctly with updated base.html — load `/sellers/`, `/sellers/<id>/`, `/events/<id>/`, `/lots/<id>/`, `/lots/<id>/override/`, `/search/`, `/imports/` and confirm they render without errors. The updated navbar (with logo) must display correctly on all existing pages. Add a contract test in tests/contract/test_panels.py verifying the home page (`/`) returns shell.html (not sellers/list.html) while `/sellers/` still returns the full-page seller list.

**Checkpoint**: All existing pages work. Lot detail is reachable from the SPA shell. Back-navigation returns to the shell.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, error handling, and final validation

- [X] T022 Add API error handling to panel views in src/catalog/views/panels.py — catch `RequestException` from ABConnect API in each panel view and return an error-state HTML fragment with a retry button (using `hx-get` to re-request). Style error state in src/catalog/static/catalog/styles.css.
- [X] T023 Handle edge case: rapid seller/event clicking — verify `hx-sync="this:replace"` on panel containers correctly cancels stale requests. Manual test: click seller A, immediately click seller B — only seller B's events should appear.
- [X] T024 Run quickstart.md validation — execute all manual verification steps from specs/003-spa-shell-layout/quickstart.md: verify three-panel layout on home page, HTMX navigation, fragment endpoint curl tests, existing page accessibility, pytest pass.
- [X] T025 Final CSS audit in src/catalog/static/catalog/styles.css — verify consistent spacing, typography, and color usage across all panel states (empty, loading, populated, error). Confirm no visual regressions on existing pages (lot detail, override form, search results, import list).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — three-panel structure and behavior
- **US2 (Phase 4)**: Depends on US1 — polish requires panels to exist
- **US3 (Phase 5)**: Depends on US1 — pagination requires panels to exist
- **US4 (Phase 6)**: Depends on US1 — navigation verification requires panels to exist
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only — no other story dependencies. **This is the MVP.**
- **US2 (P1)**: Depends on US1 — visual polish applied to panels created in US1
- **US3 (P2)**: Depends on US1 — pagination added to panels created in US1
- **US4 (P2)**: Depends on US1 — lot links and existing page verification require US1 panels

### After US1 Completes, US2 + US3 + US4 Can Run in Parallel

```text
Phase 1 → Phase 2 → Phase 3 (US1) ──┬── Phase 4 (US2)
                                      ├── Phase 5 (US3)  → Phase 7 (Polish)
                                      └── Phase 6 (US4)
```

### Within Each User Story

- Contract tests (T006) can run in parallel with template creation (T007-T009)
- Templates (T007, T008, T009) can run in parallel — different files
- Views (T010) depend on templates existing
- HTMX wiring (T012) depends on views + templates
- Home page change (T011) depends on shell.html (T004)

### Parallel Opportunities

**Phase 3 (US1)**:
```
Parallel: T006, T007, T008, T009  (contract tests + 3 template files)
Then:     T010                     (all 3 views in panels.py)
Then:     T011, T012               (home view + HTMX wiring)
```

**After US1 completes**:
```
Parallel: Phase 4 (US2), Phase 5 (US3), Phase 6 (US4)
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T005)
3. Complete Phase 3: US1 (T006–T012)
4. **STOP and VALIDATE**: Three-panel HTMX navigation works. Contract tests pass.
5. Deploy/demo if ready — the core SPA shell is functional

### Incremental Delivery

1. Setup + Foundational → Shell structure ready
2. US1 → Three-panel HTMX browse works → **MVP complete**
3. US2 → Visual polish applied → Production-quality design
4. US3 → Pagination for large datasets → Scalable for real data
5. US4 → Preserved navigation verified → No regressions
6. Polish → Edge cases, error handling, final validation

### Suggested MVP Scope

**US1 alone** delivers a functional three-panel SPA shell. All other stories add polish, pagination, and verification on top of this foundation.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- US1 is the critical path — all other stories depend on it
- Contract tests included per constitution Principle II (Executable Knowledge)
- No new dependencies, no new models — presentation-layer changes only
- All existing pages preserved — SPA shell is additive, not destructive

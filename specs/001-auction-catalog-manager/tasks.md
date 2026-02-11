# Tasks: Auction Catalog Manager

**Input**: Design documents from `/specs/001-auction-catalog-manager/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.yaml, quickstart.md

**Tests**: Not explicitly requested. Test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — Django project structure, dependencies, configuration

- [x] T001 Create pyproject.toml at repo root with Django 5, pytest, pytest-django dependencies and ABConnectTools as editable dependency
- [x] T002 Create Django project structure: src/manage.py, src/config/__init__.py, src/config/settings.py, src/config/urls.py, src/config/wsgi.py
- [x] T003 [P] Create catalog app skeleton: src/catalog/__init__.py, src/catalog/urls.py, src/catalog/views/__init__.py
- [x] T004 [P] Configure Django settings in src/config/settings.py: INSTALLED_APPS (catalog, sessions), TEMPLATES (catalog/templates dir), STATIC files, SESSION_ENGINE (db), SECRET_KEY from env, DEBUG from env, ALLOWED_HOSTS, MIDDLEWARE (sessions, CSRF), SQLite database for sessions only
- [x] T005 Install dependencies into venv and run initial migrate for sessions table

**Checkpoint**: Django project boots with `python src/manage.py runserver` — shows default page

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**Warning**: No user story work can begin until this phase is complete

- [x] T006 Implement catalog service layer in src/catalog/services.py — initialize ABConnectAPI with SessionTokenStorage from Django request, expose methods: get_api(request) returning configured CatalogAPI instance
- [x] T007 [P] Implement login view (GET + POST) in src/catalog/views/auth.py — GET renders login form, POST authenticates via ABConnectAPI(request=request) using submitted username/password, stores token in Django session, redirects to / on success, re-renders with error on failure
- [x] T008 [P] Create login template in src/catalog/templates/catalog/auth/login.html — username/password form with CSRF token, error message display
- [x] T009 Implement logout view (POST) in src/catalog/views/auth.py — clears Django session, redirects to /login/
- [x] T010 Implement auth-required middleware in src/catalog/middleware.py — redirects unauthenticated requests to /login/ (exempt: /login/, /static/)
- [x] T011 Create base template in src/catalog/templates/catalog/base.html — HTML layout with nav bar (search input, logout button), breadcrumb block, content block, HTMX script from CDN, CSRF token in hx-headers for HTMX requests
- [x] T012 Wire up root URL configuration in src/config/urls.py — include catalog.urls, serve static files in debug mode
- [x] T013 Wire up catalog URL patterns in src/catalog/urls.py — /login/, /logout/, and placeholder for remaining routes

**Checkpoint**: Foundation ready — user can log in at /login/, see base layout, log out. Unauthenticated users redirected to login.

---

## Phase 3: User Story 1 — Browse Seller, Event, and Lot Hierarchy (Priority: P1) — MVP

**Goal**: Navigate the drill-down hierarchy: Sellers list → Seller detail (events) → Event detail (lots) with pagination and filtering

**Independent Test**: Log in, view seller list, click a seller to see events, click an event to see lots. Pagination works on all lists. Filtering works on sellers and events.

### Implementation for User Story 1

- [x] T014 [US1] Add service methods to src/catalog/services.py: list_sellers(request, page, page_size, **filters), get_seller(request, seller_id) wrapping api.catalog.sellers.list() and api.catalog.sellers.get()
- [x] T015 [US1] Add service methods to src/catalog/services.py: list_catalogs(request, page, page_size, **filters), get_catalog(request, catalog_id) wrapping api.catalog.catalogs.list() and api.catalog.catalogs.get()
- [x] T016 [US1] Add service method to src/catalog/services.py: list_lots_by_catalog(request, customer_catalog_id, page, page_size) wrapping api.catalog.lots.list(customer_catalog_id=...)
- [x] T017 [P] [US1] Create pagination partial template in src/catalog/templates/catalog/partials/pagination.html — previous/next links, page numbers, uses hx-get for HTMX page navigation, accepts paginated_list context (page_number, total_pages, has_previous_page, has_next_page)
- [x] T018 [P] [US1] Create filter partial template in src/catalog/templates/catalog/partials/filters.html — reusable filter form component with hx-get submission
- [x] T019 [US1] Implement seller list view in src/catalog/views/sellers.py — GET / with query params: page, page_size, name, is_active. Calls list_sellers service. Renders sellers/list.html with seller list and pagination context. Includes breadcrumb: Home
- [x] T020 [US1] Create seller list template in src/catalog/templates/catalog/sellers/list.html — table with name, display ID, active status columns. Each row links to /sellers/{id}/. Includes pagination partial and filter controls (name text input, active status dropdown)
- [x] T021 [US1] Implement seller detail view in src/catalog/views/sellers.py — GET /sellers/{seller_id}/ calls get_seller service (returns SellerExpandedDto with catalogs). Renders sellers/detail.html with seller info and event list. Includes breadcrumb: Home > Seller Name
- [x] T022 [US1] Create seller detail template in src/catalog/templates/catalog/sellers/detail.html — seller info header (name, display ID, active status), event table with title, agent, start/end dates, completion status. Each event row links to /events/{id}/. Empty state message if no events
- [x] T023 [US1] Implement event detail view in src/catalog/views/events.py — GET /events/{event_id}/ calls get_catalog service (returns CatalogExpandedDto) and list_lots_by_catalog for paginated lots. Renders events/detail.html. Breadcrumb: Home > Seller Name > Event Title
- [x] T024 [US1] Create event detail template in src/catalog/templates/catalog/events/detail.html — event info header (title, agent, dates, completion status), lot table with lot number, customer item ID, description. Each lot row links to /lots/{id}/. Pagination partial. Empty state if no lots
- [x] T025 [US1] Add URL patterns to src/catalog/urls.py: path("", seller_list), path("sellers/<int:seller_id>/", seller_detail), path("events/<int:event_id>/", event_detail)
- [x] T026 [US1] Create minimal styles in src/catalog/static/catalog/styles.css — table styling, pagination controls, filter form layout, breadcrumb styling, active/completed status badges, empty state messaging

**Checkpoint**: Full Sellers → Events → Lots navigation works. Pagination and filtering functional. This is the MVP.

---

## Phase 4: User Story 2 — Review Lot Details (Priority: P2)

**Goal**: Display full lot detail including initial data, override comparison, and images

**Independent Test**: Navigate to any lot from the event detail page and verify all initial data fields, existing overrides (highlighted where different), and images are displayed.

### Implementation for User Story 2

- [x] T027 [US2] Add service method to src/catalog/services.py: get_lot(request, lot_id) wrapping api.catalog.lots.get() returning full LotDto with initial_data, overriden_data, image_links, catalogs
- [x] T028 [US2] Create custom template tag in src/catalog/templatetags/catalog_tags.py — register filter `override_diff` that compares a field value from overriden_data against initial_data and returns a CSS class (e.g., "changed") when they differ. Also add `format_dimension` filter for L/W/H display
- [x] T029 [US2] Implement lot detail view in src/catalog/views/lots.py — GET /lots/{lot_id}/ calls get_lot service. Builds context with initial_data fields, overriden_data (first override if present), image_links, and catalog associations. Breadcrumb: Home > Seller > Event > Lot #N
- [x] T030 [US2] Create lot detail template in src/catalog/templates/catalog/lots/detail.html — display initial data in a data table (qty, L/W/H, wgt, value, cpack, description, notes, noted_conditions, commodity_id, force_crate, do_not_tip). If overrides exist, show side-by-side or inline comparison with changed values highlighted via catalog_tags. Display images from image_links. Show handling flags (force crate, do not tip) as badges. Link to override edit form. Empty/null fields displayed as blank, not zero
- [x] T031 [US2] Add URL pattern to src/catalog/urls.py: path("lots/<int:lot_id>/", lot_detail)
- [x] T032 [US2] Add override comparison styles to src/catalog/static/catalog/styles.css — highlight changed values, image gallery layout, handling flag badges

**Checkpoint**: Lot detail page shows all data fields, override comparison with visual diff, and images. Handling flags clearly indicated.

---

## Phase 5: User Story 3 — Set and Edit Lot Overrides (Priority: P3)

**Goal**: Create and edit override values for a lot via a Django form, persisting to the Catalog API

**Independent Test**: Navigate to a lot, click "Edit Override", change one or more fields, save. Return to lot detail and verify override values are reflected and differences highlighted.

### Implementation for User Story 3

- [x] T033 [US3] Create Django form OverrideForm in src/catalog/forms.py — fields matching LotDataDto: qty (IntegerField), l/w/h/wgt/value (DecimalField), cpack/description/notes/noted_conditions (CharField/TextField), commodity_id (IntegerField), force_crate/do_not_tip (BooleanField). All fields optional. Pre-populate from existing override or initial_data
- [x] T034 [US3] Add service method to src/catalog/services.py: save_lot_override(request, lot_id, override_data) — fetches current lot, builds UpdateLotRequest with updated overriden_data list, calls api.catalog.lots.update(lot_id, data)
- [x] T035 [US3] Implement override form views in src/catalog/views/lots.py — GET /lots/{lot_id}/override/ fetches lot, creates OverrideForm pre-populated with existing override (or initial_data if no override), renders override.html. POST validates form, calls save_lot_override service, redirects to /lots/{lot_id}/ on success, re-renders form with errors on failure
- [x] T036 [US3] Create override form template in src/catalog/templates/catalog/lots/override.html — renders OverrideForm fields with labels matching lot data terminology. CSRF token included. Submit and Cancel buttons (cancel links back to lot detail without saving). Breadcrumb: Home > Seller > Event > Lot #N > Edit Override
- [x] T037 [US3] Add URL patterns to src/catalog/urls.py: path("lots/<int:lot_id>/override/", override_form, name="override_form")

**Checkpoint**: Override create/edit workflow complete. Changes persist to Catalog API and are visible in lot detail view with diff highlighting.

---

## Phase 6: User Story 4 — Search and Filter Lots Across Events (Priority: P4)

**Goal**: Search for lots by customer item ID or lot number from any page, with results showing parent event/seller context

**Independent Test**: Enter a known customer item ID or lot number in the search bar, verify matching lots appear with seller/event context, click a result to reach the lot detail page.

### Implementation for User Story 4

- [x] T038 [US4] Add service method to src/catalog/services.py: search_lots(request, query, page, page_size) — calls api.catalog.lots.list() with customer_item_id filter and/or lot_number filter based on query. Returns paginated results with catalog context
- [x] T039 [US4] Implement search view in src/catalog/views/search.py — GET /search/?q=...&page=... calls search_lots service. For each result, resolves parent catalog and seller names for context. Renders search/results.html
- [x] T040 [US4] Create search results template in src/catalog/templates/catalog/search/results.html — displays matching lots with columns: lot number, customer item ID, description, parent event title, parent seller name. Each row links to /lots/{id}/. Pagination partial. Empty state if no results. Search query preserved in search input
- [x] T041 [US4] Add URL pattern to src/catalog/urls.py: path("search/", search_lots_view)
- [x] T042 [US4] Wire search input in base.html nav bar to submit GET to /search/?q=...

**Checkpoint**: Global lot search works from any page. Results show hierarchy context and link to lot detail.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T043 [P] Add empty state templates/messaging across all list views — sellers with no events, events with no lots, search with no results (FR-013)
- [x] T044 [P] Add error handling for Catalog API failures in src/catalog/services.py — catch RequestError from ABConnectTools, display user-friendly error pages
- [x] T045 Validate quickstart.md by running full setup from scratch: install deps, migrate, runserver, log in, browse hierarchy, set override, search
- [x] T046 Add db.sqlite3 to .gitignore

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — delivers MVP
- **US2 (Phase 4)**: Depends on Foundational. Builds on US1 navigation (lot links from event detail)
- **US3 (Phase 5)**: Depends on US2 (override form links from lot detail page)
- **US4 (Phase 6)**: Depends on Foundational. Can run in parallel with US2/US3 (independent search route)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P2)**: Can start after Phase 2 — uses lot links created in US1 but the route itself is independent
- **US3 (P3)**: Depends on US2 — override form is accessed from the lot detail page built in US2
- **US4 (P4)**: Can start after Phase 2 — fully independent search route, can run in parallel with US2/US3

### Within Each User Story

- Service methods before views (views call services)
- Views before templates (templates consume view context)
- URL patterns after views are implemented
- Partials before pages that include them

### Parallel Opportunities

- T003 + T004 can run in parallel (different files)
- T007 + T008 can run in parallel (view + template)
- T017 + T018 can run in parallel (different partial templates)
- T014 + T015 + T016 are sequential (same file: services.py) but logically independent methods
- US4 can run in parallel with US2 and US3 (completely independent route)
- T043 + T044 can run in parallel (different concerns)

---

## Parallel Example: User Story 1

```bash
# After Phase 2 is complete, launch partial templates in parallel:
Task: "Create pagination partial in src/catalog/templates/catalog/partials/pagination.html"  # T017
Task: "Create filter partial in src/catalog/templates/catalog/partials/filters.html"          # T018

# Then implement views and templates sequentially (views first, templates second):
# seller_list view → seller list template → seller_detail view → seller detail template → ...
```

## Parallel Example: After US1 Complete

```bash
# US2 and US4 can start in parallel:
# Developer A: US2 (lot detail)
Task: "Add get_lot service method"          # T027
Task: "Create template tags"                 # T028
# Developer B: US4 (search)
Task: "Add search_lots service method"       # T038
Task: "Implement search view"                # T039
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T005)
2. Complete Phase 2: Foundational (T006–T013)
3. Complete Phase 3: User Story 1 (T014–T026)
4. **STOP and VALIDATE**: Log in, browse sellers → events → lots with pagination and filtering
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Deploy (MVP: hierarchy browsing)
3. Add US2 → Test independently → Deploy (lot detail with override comparison)
4. Add US3 → Test independently → Deploy (override editing — core business value)
5. Add US4 → Test independently → Deploy (search for efficiency)
6. Polish → Final validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No local Django models for catalog data — all data from ABConnectTools CatalogAPI
- ABConnectTools is already installed in the venv as editable package
- Django sessions use SQLite — only migration needed is the built-in sessions table
- HTMX loaded from CDN in base.html — no npm/build step
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

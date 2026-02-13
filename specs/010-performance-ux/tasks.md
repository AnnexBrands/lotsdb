# Tasks: Performance UX — Loading Feedback & Optimization

**Input**: Design documents from `/specs/010-performance-ux/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configure Django cache backend and concurrency settings needed by US2–US4.

- [X] T001 Add `CACHES` configuration (LocMemCache backend, `lotsdb-cache` location, 600s timeout, 500 max entries) and `LOT_FETCH_MAX_WORKERS = 10` setting in `src/config/settings.py`

---

## Phase 2: US1 — Loading Feedback on Event Selection (Priority: P0) — MVP

**Goal**: Fix broken HTMX loading indicators so spinners show immediately when operators click sellers, events, or pagination links.

**Independent Test**: Click any seller or event — a spinner overlay and content dimming should appear within 100ms. Click pagination Next/Prev — same behavior. Verify across all three panels.

**Root Cause (from research.md R1)**: `hx-indicator="#panel-main .htmx-indicator"` targets the indicator div itself. HTMX 2.0 adds `htmx-request` to that element, but the CSS uses descendant selector `.htmx-request .htmx-indicator` requiring the class on a parent. Fix: target the panel div instead (e.g., `hx-indicator="#panel-main"`).

- [X] T002 [P] [US1] Fix `hx-indicator` targets in `src/catalog/templates/catalog/partials/seller_list_panel.html` — change `hx-indicator="#panel-left1 .htmx-indicator"` to `hx-indicator="#panel-left1"` (filter form, line 2), change `hx-indicator="#panel-left2 .htmx-indicator"` to `hx-indicator="#panel-left2"` (seller click, line 17), and change `indicator_id` in pagination include from `"#panel-left1 .htmx-indicator"` to `"#panel-left1"` (line 22)
- [X] T003 [P] [US1] Fix `hx-indicator` targets in `src/catalog/templates/catalog/partials/events_panel.html` — change `hx-indicator="#panel-left2 .htmx-indicator"` to `hx-indicator="#panel-left2"` (filter form, line 2), change `hx-indicator="#panel-main .htmx-indicator"` to `hx-indicator="#panel-main"` (event click, line 16), and change `indicator_id` in pagination include from `"#panel-left2 .htmx-indicator"` to `"#panel-left2"` (line 22)
- [X] T004 [P] [US1] Fix `hx-indicator` target in `src/catalog/templates/catalog/partials/lots_panel.html` — change `indicator_id` in pagination include from `"#panel-main .htmx-indicator"` to `"#panel-main"` (line 6)

**Checkpoint**: Loading spinners now visible for all panel transitions. Content dims during load. This is independently testable and deployable.

---

## Phase 3: US2 — Concurrent Lot Fetching (Priority: P0)

**Goal**: Replace sequential lot fetching with concurrent execution to reduce event selection time from ~13s to ~2s.

**Independent Test**: Click an event with 25+ lots. Time from click to table render should be under 3 seconds. Check server logs for "Failed to fetch lot" warnings — should be absent under normal conditions.

**Depends on**: T001 (LOT_FETCH_MAX_WORKERS setting)

- [X] T005 [US2] Rewrite `get_lots_for_event()` in `src/catalog/services.py` to use `concurrent.futures.ThreadPoolExecutor` — create per-thread API instances via `get_catalog_api(request)` inside each thread worker (thread-safe per research.md R2), use `max_workers` from `settings.LOT_FETCH_MAX_WORKERS` (default 10), preserve lot ordering with indexed results array, log and skip individual failures with `logger.warning`, filter out `None` results

**Checkpoint**: Event selection now completes in ~2s for 25 lots. Graceful degradation on individual lot fetch failures.

---

## Phase 4: US3 + US4 — Data Caching (Priority: P1)

**Goal**: Cache lot and catalog data so repeat visits and page changes are near-instant (< 500ms).

**Independent Test**: (1) Click an event, note load time (~2s). Click away, click back — should load in < 500ms. (2) Change to page 2, then back to page 1 — page 1 instant from cache. (3) Edit a lot inline, navigate away and back — edited lot shows fresh data (cache invalidated). (4) Wait 10+ minutes — data refreshed from API.

**Depends on**: T001 (CACHES configuration), T005 (concurrent fetching)

- [X] T006 [US4] Add cache-through logic to `get_catalog()` in `src/catalog/services.py` — check `cache.get(f"catalog:{catalog_id}")` first, on miss fetch from API and `cache.set()` with default TTL, import `from django.core.cache import cache`
- [X] T007 [US3] Add cache-through logic to `get_lot()` in `src/catalog/services.py` — check `cache.get(f"lot:{lot_id}")` first, on miss fetch from API and `cache.set()` with default TTL
- [X] T008 [US3] Update `get_lots_for_event()` in `src/catalog/services.py` to partition `lot_ids` into cached (from `cache.get`) and uncached, only fetch uncached lots concurrently via ThreadPoolExecutor, cache newly fetched lots, merge cached + fetched results preserving original ordering
- [X] T009 [US3] Add cache invalidation to `save_lot_override()` in `src/catalog/services.py` — after successful `api.lots.update()`, call `cache.delete(f"lot:{lot_id}")` to ensure next load fetches fresh data

**Checkpoint**: Repeat visits and page changes load in < 500ms. Override saves correctly invalidate cache. Cache expires after 10 minutes.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Tests and final validation.

- [X] T010 Create service-layer tests in `tests/test_services.py` — test concurrent fetching (mock API, verify ThreadPoolExecutor used, verify ordering preserved), test cache hit/miss for `get_lot()` and `get_catalog()`, test cache invalidation on `save_lot_override()`, test graceful degradation when individual lot fetch fails
- [X] T011 Run `quickstart.md` validation — execute `.venv/bin/python -m pytest tests/ -v` to verify all tests pass, manually verify loading indicators per quickstart steps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **US1 (Phase 2)**: No dependencies on Phase 1 — can run in parallel with Setup (template-only changes)
- **US2 (Phase 3)**: Depends on T001 (needs `LOT_FETCH_MAX_WORKERS` setting)
- **US3 + US4 (Phase 4)**: Depends on T001 (needs `CACHES` config) and T005 (caching integrates with concurrent fetching)
- **Polish (Phase 5)**: Depends on all previous phases

### User Story Dependencies

- **US1 (Loading Feedback)**: Fully independent — template-only, no Python changes
- **US2 (Concurrent Fetching)**: Independent of US1, depends on settings (T001)
- **US3 (Lot Caching)**: Depends on US2 (T005) — caching wraps the concurrent fetcher
- **US4 (Catalog Caching)**: Depends on settings (T001) only, independent of US2/US3

### Within Each Phase

- Phase 2: T002, T003, T004 are all [P] (different template files)
- Phase 4: T006 and T007 modify different functions in the same file (sequential), T008 depends on T005 and T007, T009 is independent of T006–T008

### Parallel Opportunities

```
T001 (settings) ──────┬──> T005 (concurrent) ──> T008 (cache+concurrent)
                      │                           ↑
                      ├──> T006 (catalog cache)   │
                      │                           │
                      └──> T007 (lot cache) ──────┘

T002 ─┐
T003 ─┼─ (all parallel, independent of Python tasks)
T004 ─┘
```

---

## Parallel Example: US1 (Loading Feedback)

```bash
# All three template fixes can run simultaneously (different files):
Task: "Fix hx-indicator targets in src/catalog/templates/catalog/partials/seller_list_panel.html"
Task: "Fix hx-indicator targets in src/catalog/templates/catalog/partials/events_panel.html"
Task: "Fix hx-indicator target in src/catalog/templates/catalog/partials/lots_panel.html"
```

---

## Implementation Strategy

### MVP First (US1 Only — Phase 2)

1. Complete Phase 1: Settings configuration
2. Complete Phase 2: Fix loading indicators (T002–T004)
3. **STOP and VALIDATE**: Deploy — users now see immediate spinner feedback
4. This alone dramatically improves perceived performance even before actual speed improvements

### Incremental Delivery

1. **Phase 1 + Phase 2** → Loading feedback visible (MVP) → Deploy
2. **Phase 3** → Event selection drops from 13s to ~2s → Deploy
3. **Phase 4** → Repeat visits and page changes < 500ms → Deploy
4. **Phase 5** → Tests and validation → Final deploy

### Optimal Single-Developer Order

1. T001 (settings) — 1 file, quick
2. T002 + T003 + T004 (indicator fixes) — 3 templates, quick
3. T005 (concurrent fetching) — core perf win
4. T006 + T007 (cache-through for catalog + lot) — same file, do together
5. T008 (integrate cache with concurrent fetcher)
6. T009 (cache invalidation on save)
7. T010 + T011 (tests and validation)

---

## Notes

- All changes are in existing files except `tests/test_services.py` (new)
- No new Python package dependencies — stdlib `concurrent.futures` + Django `cache`
- Template fixes (US1) are purely cosmetic — zero risk to backend logic
- Concurrent fetching (US2) is isolated to one function in services.py
- Caching (US3/US4) wraps existing functions transparently — views unchanged

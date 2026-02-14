# Tasks: Cache Polish

**Input**: Design documents from `/specs/016-cache-polish/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cache-service.md, contracts/events-panel-view.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: US1 + US2 — Cache Correctness Fixes (Priority: P1)

**Goal**: Fix start_date type fidelity through cache round-trip and fix catalog pagination contract violation. Both bugs are in `list_catalogs()` in the same file, so they execute sequentially.

**Independent Test**: Click a seller twice — cached event dates display identically. Request page 2 of cached events — correct pagination metadata returned.

- [X] T001 [US1] Fix start_date type in `list_catalogs()` cache write and read — cache write: use `c.start_date.isoformat() if c.start_date else None`; cache read: parse with `datetime.fromisoformat(d["start_date"])` if present, wrapping each cached dict before creating `SimpleNamespace` — in `src/catalog/services.py`
- [X] T002 [US2] Fix pagination in `list_catalogs()` — change both cache-hit branch (line 106) and cache-miss branch (line 122) from `_make_paginated(items, 1, len(items) or 1)` to `_make_paginated(items, page, page_size)` to respect caller's pagination args — in `src/catalog/services.py`
- [X] T003 [US1] Add contract test TC-P01 (start_date survives cache round-trip as datetime) — mock `safe_cache_get` to return a list with `"start_date": "2099-01-01T00:00:00"`, call `list_catalogs()`, assert `type(item.start_date) is datetime` — in `tests/contract/test_panels.py`
- [X] T004 [US2] Add contract test TC-P02 (cached catalog pagination respects page/page_size) — mock cache with 30 items, request page=2 page_size=25, assert 5 items returned with `has_previous_page=True` and `has_next_page=False` — in `tests/contract/test_panels.py`

**Checkpoint**: `cd src && python -m pytest ../tests/ -v` passes. Cached event dates render correctly, pagination works.

---

## Phase 2: US3 + US4 + US5 — Quick Wins (Priority: P2)

**Goal**: Environment-driven Redis URL, fix misleading test assertion, increase skeleton rows. All three touch different files and can run in parallel.

- [X] T005 [P] [US3] Replace hardcoded Redis URL in CACHES config with `os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")` — add `import os` at top if not present — in `src/config/settings.py`
- [X] T006 [P] [US4] Fix `test_returns_default_on_miss` — the test passes `default="fallback"` but the mock returns `None` and the assertion checks `None`; fix: mock `cache.get` to return the sentinel `"fallback"` value, assert result equals `"fallback"` — in `tests/unit/test_cache.py`
- [X] T007 [P] [US5] Increase skeleton row count — change events panel skeleton from 3 `<li class="skeleton-item">` elements to 15; change lots table skeleton from 4 `lotsSkeletonRow` concatenations to 15 — in `src/catalog/templates/catalog/shell.html`

**Checkpoint**: `cd src && python -m pytest ../tests/ -v` passes. Settings uses env var. Skeleton shows 15 rows.

---

## Phase 3: US6 — Stale-While-Revalidate for Events (Priority: P1)

**Goal**: When a seller with cached events is clicked, show cached events instantly (no skeleton). Simultaneously fire a background refresh from the server. When fresh data arrives, seamlessly replace panel content. If cache is empty, keep skeleton until server responds.

**Depends on**: Phase 1 (correct start_date types and pagination) and Phase 2 T007 (skeleton changes in shell.html, same file modified here).

**Independent Test**: Click a seller with cached events — events appear instantly. Wait — panel updates with fresh server data. Click a different seller before refresh completes — no stale data flash.

- [X] T008 [US6] Add `use_cache=True` parameter to `list_catalogs()` — when `use_cache=False`, skip cache read but still fetch from API, update cache, and return. This supports the SWR fresh-fetch path — in `src/catalog/services.py`
- [X] T009 [US6] Implement SWR logic in `seller_events_panel` view — check cache directly via `safe_cache_get` for the seller's catalog cache key; if cache hit AND no filters AND not `fresh=1` request: render events from cache with `from_cache=True` context flag; if `fresh=1`: call `list_catalogs(use_cache=False)`, skip `HX-Push-Url` header; if cache miss: normal flow (skeleton stays visible) — in `src/catalog/views/panels.py`
- [X] T010 [US6] Add auto-refresh trigger to events panel template — when `from_cache` is truthy, include a hidden `<div>` with `hx-get="/panels/sellers/{{ seller_id }}/events/?fresh=1" hx-target="#panel-left2-content" hx-swap="innerHTML" hx-trigger="load"` before the OOB swaps; skip this div when not from_cache (prevents infinite loops) — in `src/catalog/templates/catalog/partials/events_panel.html`
- [X] T011 [US6] Add SWR JavaScript guards in shell.html — (1) modify `htmx:beforeRequest` handler to NOT inject skeleton when request URL contains `fresh=1` (cached content already visible); (2) add `htmx:beforeSwap` handler that checks: if incoming request URL contains `fresh=1`, read `data-seller-id` from `#panel-left2-content`, extract seller ID from request URL, prevent swap if they don't match — in `src/catalog/templates/catalog/shell.html`
- [X] T012 [US6] Add SWR contract tests — TC-SWR01: cache hit serves HTML with `fresh=1` trigger div; TC-SWR02: `?fresh=1` request returns HTML without trigger div; TC-SWR03: cache miss returns HTML without trigger div; TC-SWR04: filter active bypasses cache, no trigger div; TC-SWR05: `?fresh=1` request has no `HX-Push-Url` header — in `tests/contract/test_panels.py`

**Checkpoint**: `cd src && python -m pytest ../tests/ -v` passes. Cached sellers show events instantly with background refresh.

---

## Phase 4: Polish & Verification

- [X] T013 Run full test suite: `cd src && python -m pytest ../tests/ -v` — confirm all existing and new tests pass
- [ ] T014 Manual verification per `specs/016-cache-polish/quickstart.md` — event dates, pagination, env config, SWR, skeleton rows

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1+US2)**: No dependencies — start immediately (correctness fixes)
- **Phase 2 (US3+US4+US5)**: No dependencies — can run in parallel with Phase 1 (different files)
- **Phase 3 (US6)**: Depends on Phase 1 (needs correct start_date + pagination) and Phase 2 T007 (skeleton changes in shell.html, same file)
- **Phase 4 (Polish)**: Depends on all phases complete

### Parallel Opportunities

- T005, T006, T007 can all run in parallel (different files: settings.py, test_cache.py, shell.html)
- Phase 1 and Phase 2 can overlap (different files: services.py vs settings.py/test_cache.py/shell.html)
- Within Phase 3, T008→T009→T010→T011→T012 are sequential (same-file dependencies)

```text
T001→T002→T003→T004 (US1+US2, services.py + tests) ─┐
T005 (US3, settings.py) ─────────────────────────────┤
T006 (US4, test_cache.py) ───────────────────────────┤
T007 (US5, shell.html) ──────────────────────────────┤
                                                      └→ T008→T009→T010→T011→T012 (US6) → T013→T014
```

---

## Implementation Strategy

### MVP First (US1 + US2 correctness fixes)

1. Complete T001-T004 — cache correctness bugs fixed
2. **STOP and VALIDATE**: Cached event dates render, pagination works
3. Can ship this alone if needed

### Full Delivery

1. T001-T004: Cache correctness fixes (services.py + tests)
2. T005+T006+T007 in parallel: Quick wins (settings, test fix, skeletons)
3. T008-T012: SWR implementation (the big UX improvement)
4. T013-T014: Verification

All changes ship together as a single commit.

---

## Notes

- **6 modified files**: `services.py`, `settings.py`, `panels.py`, `events_panel.html`, `shell.html`, `test_panels.py`
- **1 modified test file**: `test_cache.py` (assertion fix)
- **0 new files**: All changes to existing files from 015-redis-caching
- Total: 14 tasks across 7 files
- The SWR pattern uses HTMX's built-in `hx-trigger="load"` on a hidden div — no new JS libraries needed
- Race condition guard uses `data-seller-id` attribute + `htmx:beforeSwap` event — pure vanilla JS

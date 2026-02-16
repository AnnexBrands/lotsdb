# Tasks: Redis Caching for Sellers and Catalogs

**Input**: Design documents from `/specs/015-redis-caching/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cache-service.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup — Redis Dependency and Configuration

**Goal**: Add Redis as a project dependency and configure Django's cache backend.

- [X] T001 [P] Add `redis>=5.0` to dependencies in `pyproject.toml` and install with `pip install -e ".[dev]"`
- [X] T002 [P] Add CACHES configuration to `src/config/settings.py` — use `django.core.cache.backends.redis.RedisCache` backend with `LOCATION: "redis://127.0.0.1:6379"`, `KEY_PREFIX: "cat_"`, `TIMEOUT: 300`

**Checkpoint**: `python -c "from django.core.cache import cache; print(cache.__class__)"` returns RedisCache.

---

## Phase 2: Foundational — Cache Helper Module

**Goal**: Create the safe cache wrapper functions that all user stories depend on.

- [X] T003 Create `src/catalog/cache.py` with `safe_cache_get(key, default=None)` and `safe_cache_set(key, value, timeout=None)` — both wrap `django.core.cache.cache` in try/except, log warnings on failure, never raise (per contract and research R3)
- [X] T004 Create `tests/unit/test_cache.py` with unit tests for `safe_cache_get` and `safe_cache_set` — test cache hit, cache miss, and exception handling (mock `django.core.cache.cache` to simulate Redis down)

**Checkpoint**: `pytest tests/unit/test_cache.py -v` passes.

---

## Phase 3: User Story 1 — Cached Seller List (Priority: P1)

**Goal**: When a user opens the sellers panel, serve the seller list from cache (lightweight dicts with `id`, `name`, `customer_display_id`) on cache hit. On miss, fetch all sellers from API, project to dicts, cache, paginate locally, return.

**Independent Test**: Open sellers panel twice — second load serves from cache with no API call.

- [X] T005 [US1] Modify `list_sellers()` in `src/catalog/services.py` — when `filters` is empty: check cache key `sellers_all` via `safe_cache_get`; on hit, wrap cached dicts in `types.SimpleNamespace`, paginate locally using `_paginate_locally` pattern from `panels.py`, return paginated result; on miss, call API with `page_size=500`, project each seller DTO to `{"id": s.id, "name": s.name, "customer_display_id": s.customer_display_id}`, cache the list via `safe_cache_set`, then paginate and return. When `filters` is non-empty, bypass cache and call API directly (existing behavior).
- [X] T006 [US1] Update existing seller panel tests in `tests/contract/test_panels.py` to account for the caching layer — mock `catalog.cache.safe_cache_get` and `safe_cache_set` (or `django.core.cache.cache`) so existing tests continue to pass without requiring a real Redis instance
- [X] T007 [US1] Add seller cache contract tests in `tests/contract/test_panels.py` (class `TestSellerCacheContract`) — TC-001: cache hit returns cached data without API call, TC-002: cache miss fetches from API and populates cache, TC-003: filter bypasses cache

**Checkpoint**: Sellers panel loads from cache on second request. `pytest tests/contract/test_panels.py -v` passes.

---

## Phase 4: User Story 2 — Cached Catalog (Event) List (Priority: P1)

**Goal**: When a user clicks a seller, serve future catalogs from cache (lightweight dicts with `id`, `title`, `customer_catalog_id`, `start_date`) on cache hit. On miss, fetch all catalogs for seller, filter to future-only, project to dicts, cache, return.

**Independent Test**: Click a seller twice — second click serves events from cache with no API call.

- [X] T008 [US2] Modify `list_catalogs()` in `src/catalog/services.py` — when `seller_id` is provided and `filters` is empty: check cache key `catalogs_seller_{seller_id}` via `safe_cache_get`; on hit, wrap cached dicts in `SimpleNamespace`, return; on miss, call API with `page_size=200`, filter items to `start_date >= today`, project each to `{"id": c.id, "title": c.title, "customer_catalog_id": c.customer_catalog_id, "start_date": c.start_date}` (keep `start_date` as-is for sort compatibility), cache via `safe_cache_set`, return. When `seller_id` is None or `filters` is non-empty, bypass cache.
- [X] T009 [US2] Update existing events panel tests in `tests/contract/test_panels.py` to account for catalog caching — ensure mocks cover the cache layer so tests pass without Redis
- [X] T010 [US2] Add catalog cache contract tests in `tests/contract/test_panels.py` (class `TestCatalogCacheContract`) — TC-004: cache hit returns cached catalogs without API call, TC-005: cache miss fetches/filters/projects/caches

**Checkpoint**: Events panel loads from cache on repeated seller click. `pytest tests/contract/test_panels.py -v` passes.

---

## Phase 5: User Story 3 — Graceful Cache Unavailability (Priority: P2)

**Goal**: Verify the application works identically when Redis is down — all panels load, no errors, just slower.

**Independent Test**: Stop Redis, use the app — all panels load. Start Redis — caching resumes.

- [X] T011 [US3] Add fallback contract test in `tests/contract/test_panels.py` (class `TestCacheFallbackContract`) — TC-006: mock `safe_cache_get` to raise `Exception`, verify `list_sellers` still returns data from API with no error, and a warning is logged
- [X] T012 [US3] Add fallback contract test for catalogs — mock `safe_cache_get` to raise `Exception`, verify `list_catalogs` still returns data from API

**Checkpoint**: `pytest tests/contract/test_panels.py -v` passes. All fallback tests green.

---

## Phase 6: Polish & Verification

- [X] T013 Run `cd src && python -m pytest ../tests/ -v` to confirm all existing and new tests pass
- [X] T014 Run manual verification per `specs/015-redis-caching/quickstart.md` — seller caching, catalog caching, filter bypass, cache unavailability, key prefix

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 (needs redis dependency + CACHES config)
- **Phase 3 (US1)**: Depends on Phase 2 (needs cache helpers)
- **Phase 4 (US2)**: Depends on Phase 2 (needs cache helpers); can run in parallel with Phase 3 (different service function)
- **Phase 5 (US3)**: Depends on Phases 3 & 4 (verifies fallback of implemented caching)
- **Phase 6 (Polish)**: Depends on all phases complete

### Parallel Opportunities

- T001 and T002 can run in parallel (different files: pyproject.toml vs settings.py)
- T005 and T008 could run in parallel (different service functions, same file — but sequential is safer since patterns are identical)
- T006/T007 and T009/T010 are sequential within their phases but the phases themselves can overlap

```text
T001 (deps) ──┐
T002 (config) ─┤
               ├→ T003 (cache.py) → T004 (tests) ─┬→ T005→T006→T007 (US1) ─┬→ T011→T012 (US3) → T013→T014
               │                                    └→ T008→T009→T010 (US2) ─┘
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete T001 + T002 in parallel (setup)
2. Complete T003 → T004 (foundational cache helpers + tests)
3. Complete T005 → T006 → T007 (seller caching + test updates + contract tests)
4. Complete T008 → T009 → T010 (catalog caching + test updates + contract tests)
5. Complete T011 → T012 (fallback verification)
6. Run T013 + T014 (full test suite + manual check)

All changes ship together as a single commit.

---

## Notes

- **1 new file**: `src/catalog/cache.py` (safe wrappers)
- **1 new test file**: `tests/unit/test_cache.py` (helper unit tests)
- **3 modified files**: `pyproject.toml`, `src/config/settings.py`, `src/catalog/services.py`
- **1 modified test file**: `tests/contract/test_panels.py` (mock updates + new contract test classes)
- Cached values are lightweight dicts, NOT full Pydantic DTOs (per research R2)
- `SimpleNamespace` wrapping provides dot-notation access for template compatibility
- Total: 14 tasks across 6 files

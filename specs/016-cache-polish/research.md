# Research: Cache Polish (016)

## R1: start_date Type Fidelity Through Cache Round-Trip

**Decision**: Store `start_date` as ISO string in cache dict, parse back to `datetime` on cache read.

**Rationale**: Django's `|date` template filter only works with `datetime`/`date` objects — it silently returns empty string for plain strings. Currently `str(c.start_date)` stores e.g. `"2025-06-15 10:30:45"` which the template renders as blank. Parsing back via `datetime.fromisoformat()` on cache read restores type fidelity cheaply.

**Alternatives considered**:
- Store `datetime` objects directly in cache dict: Redis/pickle would handle it, but dicts-with-datetimes are less portable and harder to debug in Redis CLI. Also contradicts the lightweight-dict design decision from R2 in 015.
- Use a custom template filter that accepts strings: Adds complexity for no benefit — parsing on read is simpler.

## R2: Catalog Cache Pagination Contract

**Decision**: Change `list_catalogs()` cache-hit and cache-miss branches to use `_make_paginated(items, page, page_size)` consistently, passing through the caller's `page` and `page_size` arguments.

**Rationale**: Current code hardcodes `_make_paginated(items, 1, len(items) or 1)`, ignoring the requested page/size. This violates the contract that cached and uncached paths produce identical pagination metadata.

**Alternatives considered**: None — this is a straightforward bug fix.

## R3: Environment-Driven Redis URL

**Decision**: Use `os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")` in the CACHES configuration.

**Rationale**: Standard 12-factor app practice. Zero effort, immediate deploy portability. The project already uses `python-dotenv` (in `manage.py` / `wsgi.py`), so `.env` files work automatically.

**Alternatives considered**:
- Django settings module switching: Overkill for a single value.
- `django-environ`: Adds a dependency for no benefit when `os.environ.get` suffices.

## R4: Test Assertion Bug

**Decision**: Fix `test_returns_default_on_miss` — the test passes `default="fallback"` but mocks `cache.get` to return `None`, then asserts `None`. The mock returns `None` regardless of the default arg, so the test passes by coincidence. Fix: mock should return the sentinel default, and assertion should match.

**Rationale**: The test claims to verify default-return behavior but actually tests that `cache.get` returning `None` passes through. The real default-return behavior is handled by Django's cache — `safe_cache_get` delegates to `cache.get(key, default)`. The test should verify the wrapper passes the default through correctly.

## R5: Stale-While-Revalidate Pattern for Events Panel

**Decision**: Two-phase HTMX load — cached HTML served immediately on seller click, background refresh triggered automatically via hidden `hx-trigger="load"` element.

**Rationale**: This is the highest-impact UX improvement. The HTMX codebase already supports OOB swaps and `HX-Trigger` headers. The pattern:

1. **Seller click** → `hx-get="/panels/sellers/{id}/events/"` fires as normal
2. **View checks cache** → if cache hit (and no filter active), render events from cache. Include a hidden `<div>` with `hx-get="...?fresh=1" hx-trigger="load"` that auto-fires a background refresh.
3. **Background refresh** → `?fresh=1` bypasses cache, fetches from API, updates cache, returns fresh HTML without the auto-refresh trigger.
4. **Cache miss** → normal flow: skeleton stays visible until server responds (no two-phase).

**Race condition guard**: When user clicks a different seller before the fresh-fetch returns, the `htmx:beforeRequest` handler injects skeleton into `#panel-left2-content`, which destroys the hidden refresh div. However, the in-flight `?fresh=1` request could still return. Solution: track current seller ID on the panel via `data-seller-id` attribute; in a `htmx:beforeSwap` handler, check if the incoming `?fresh=1` response matches the current seller — if not, prevent the swap.

**Skeleton suppression**: Modify the `htmx:beforeRequest` handler to NOT inject skeleton when the request URL contains `fresh=1` (the panel already has cached content visible).

**Alternatives considered**:
- Client-side cache (localStorage/sessionStorage): Adds JS complexity, duplicates server-side cache, hard to invalidate.
- Service worker: Massive over-engineering for an internal tool.
- Server-Sent Events: Adds infrastructure complexity (SSE endpoint, connection management).
- Two separate HTMX requests from the client: More complex client JS; the hidden-div-with-`hx-trigger="load"` is an established HTMX pattern.

## R6: Skeleton Row Count

**Decision**: Change skeleton HTML from 3 `<li>` items to 15 in the events skeleton, and from 4 `<tr>` rows to 15 in the lots skeleton.

**Rationale**: 3 skeleton rows look sparse in a panel that typically shows 25+ items. 15 rows better approximate real content density without excessive DOM.

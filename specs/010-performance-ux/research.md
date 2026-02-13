# Research: Performance UX

## R1: Why HTMX Loading Indicators Don't Show

**Decision**: Fix `hx-indicator` to target the panel div, not the indicator child.

**Findings**: All three panels have this structure:
```html
<div id="panel-main" class="panel panel-main">
    <div class="htmx-indicator"><div class="spinner"></div></div>
    <div id="panel-main-content" class="panel-content">...</div>
</div>
```

And event links use:
```html
<li hx-get="..." hx-indicator="#panel-main .htmx-indicator">
```

HTMX 2.0 adds `htmx-request` class to the element(s) resolved by `hx-indicator`. So `htmx-request` is added to the `.htmx-indicator` div itself. But the CSS uses a descendant selector:
```css
.htmx-request .htmx-indicator { display: flex; }
.htmx-request .panel-content { opacity: 0.5; }
```

This requires `htmx-request` on a **parent** of `.htmx-indicator`, not on the indicator itself. Since both classes end up on the same element, the descendant selector never matches.

**Fix**: Change `hx-indicator` to target the panel div:
```html
hx-indicator="#panel-main"
```
Now `htmx-request` is added to `#panel-main`, and both `.htmx-request .htmx-indicator` and `.htmx-request .panel-content` descendant selectors match correctly.

**Rationale**: This is the minimal change — no CSS modifications needed, and it aligns the markup with the existing CSS design intent.

**Alternatives considered**:
- Add compound selector CSS (`.htmx-indicator.htmx-request`) — requires CSS changes and doesn't fix the `.panel-content` opacity rule.
- Move indicator inside content div — breaks the overlay positioning.

---

## R2: Concurrent Lot Fetching Strategy

**Decision**: Use `concurrent.futures.ThreadPoolExecutor` with per-thread API instances.

**Findings**: ABConnectTools is NOT thread-safe for shared instances:
- `SessionTokenStorage.get_token()` has a TOCTOU race on `self.expired` check
- Token refresh can be triggered by multiple threads simultaneously
- No locks or synchronization in the library

However, creating a **new `ABConnectAPI(request=request)` per thread** is safe because:
- Each instance gets its own `SessionTokenStorage` with its own `self._token` copy
- Token is read from `request.session["abc_token"]` (dict read, effectively immutable during request)
- The `requests` library is thread-safe for independent calls
- No shared mutable state between instances

**Implementation pattern**:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_lots_concurrent(request, lot_ids, max_workers=10):
    def fetch_one(lot_id):
        api = get_catalog_api(request)
        return api.lots.get(lot_id)

    results = [None] * len(lot_ids)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fetch_one, lid): i for i, lid in enumerate(lot_ids)}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception:
                logger.warning("Failed to fetch lot %s", lot_ids[idx])
    return [r for r in results if r is not None]
```

**Performance estimate**: 25 lots with 10 workers = 3 batches of ~700ms = ~2.1s (vs 17.5s sequential).

**Rationale**: ThreadPoolExecutor is ideal for I/O-bound work. Per-thread API instances avoid all shared-state issues. The `max_workers=10` default balances throughput against API rate limits.

**Alternatives considered**:
- `asyncio` with `httpx` — would require changing ABConnectTools to async, too invasive.
- `multiprocessing` — overkill for I/O-bound work, higher overhead.
- `grequests` / `gevent` — adds dependency, monkey-patching risks.
- `requests-futures` — adds dependency; ThreadPoolExecutor is stdlib.

---

## R3: Caching Strategy

**Decision**: Use Django's built-in cache framework with `LocMemCache` backend.

**Findings**:
- Django's cache framework is built-in, requires zero new dependencies
- `LocMemCache` stores data in process memory — no external services needed
- Per-process cache (each gunicorn worker has its own) — acceptable for this use case
- Cache keys: `lot:{lot_id}` and `catalog:{catalog_id}`
- TTL: 10 minutes default (configurable via settings)
- Invalidation: On `save_lot_override()`, delete `lot:{lot_id}` from cache

**Cache integration points**:
1. `get_lot()` → check cache first, fetch + cache on miss
2. `get_catalog()` → check cache first, fetch + cache on miss
3. `save_lot_override()` → invalidate `lot:{lot_id}` after save
4. `get_lots_for_event()` → check cache for each lot, only fetch uncached lots concurrently

**Configuration**:
```python
# settings.py
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "lotsdb-cache",
        "TIMEOUT": 600,  # 10 minutes
        "OPTIONS": {"MAX_ENTRIES": 500},
    }
}
LOT_FETCH_MAX_WORKERS = 10
```

**Rationale**: LocMemCache is zero-dependency, zero-config, and sufficient for a single-server deployment. Cache resets on gunicorn restart, which is fine — the data is not user-generated, just API response caching.

**Alternatives considered**:
- Redis — adds infrastructure dependency, overkill for single-server.
- File-based cache — slower than memory, adds disk I/O.
- `@lru_cache` / `functools.cache` — doesn't support TTL, not per-request scoped, no invalidation.
- Database cache — adds writes to SQLite, unnecessary.

---

## R4: ABConnect API Batch Capabilities

**Decision**: No batch lot endpoint exists; concurrent individual calls is the only option.

**Findings from Swagger**:
- `GET /api/Lot/{id}` — single lot by ID (only option for full LotDto)
- `GET /api/Lot` — paginated list, filterable by `CustomerItemId`, `LotNumber`, `CustomerCatalogId`; does NOT accept multiple IDs
- `POST /api/Lot/get-overrides` — returns override data only (not full LotDto), accepts customer item IDs (not lot IDs)

The `list` endpoint with `CustomerCatalogId` filter was already evaluated (see `list_lots_by_catalog` in services.py) and found unreliable for event scoping — embedded lot refs from the catalog are the canonical source.

**Alternatives considered**:
- `GET /api/Lot?CustomerCatalogId=X` with large page size — unreliable scoping (existing code comment confirms this).
- `POST /api/Lot/get-overrides` — only returns overrides, not full lot data (no initial_data, no image_links).

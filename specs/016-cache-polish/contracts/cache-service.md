# Contract: Cache Service Layer (Updated)

## Changes from 015-redis-caching

### 1. `list_catalogs()` — start_date Type Fix

**Cache write** (on miss):
```python
projected = [
    {"id": c.id, "title": c.title, "customer_catalog_id": c.customer_catalog_id,
     "start_date": c.start_date.isoformat() if c.start_date else None}
    for c in future_items
]
```

**Cache read** (on hit):
```python
from datetime import datetime

items = []
for d in cached:
    if d.get("start_date"):
        d["start_date"] = datetime.fromisoformat(d["start_date"])
    items.append(SimpleNamespace(**d))
```

**Invariant**: `event.start_date` is always `datetime | None` in all code paths (cached and uncached). Django's `|date` template filter works identically in both paths.

### 2. `list_catalogs()` — Pagination Fix

**Cache-hit branch**: `_make_paginated(items, page, page_size)` (pass through caller's args)
**Cache-miss branch**: `_make_paginated(items, page, page_size)` (pass through caller's args)

**Before (broken)**:
```python
return _make_paginated(items, 1, len(items) or 1)  # ignores page/page_size
```

**After (fixed)**:
```python
return _make_paginated(items, page, page_size)  # respects caller's args
```

### 3. `list_catalogs()` — Fresh Fetch (No Cache Read)

New behavior when called with `use_cache=False`:
- Skip cache read
- Fetch from API
- Update cache
- Return fresh results

This supports the stale-while-revalidate pattern where the view needs to force a fresh fetch after serving cached data.

## Test Contracts

### TC-P01: start_date survives cache round-trip as datetime
- Cache a catalog with `start_date=datetime(2099, 1, 1)`
- Read from cache
- Assert `type(item.start_date) is datetime`
- Assert Django `date` filter produces `"Jan 1, 2099"`

### TC-P02: Cached catalog pagination respects page/page_size
- Cache 30 items
- Request page=2, page_size=25
- Assert 5 items returned, `has_previous_page=True`, `has_next_page=False`

### TC-P03: Fresh fetch bypasses cache read
- Pre-populate cache with stale data
- Call `list_catalogs(..., use_cache=False)`
- Assert API was called (not cache)
- Assert cache was updated with fresh data

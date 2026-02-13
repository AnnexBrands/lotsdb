# Quickstart: Performance UX Testing

## Prerequisites

- LotsDB running locally: `.venv/bin/python src/manage.py runserver`
- Valid ABConnect credentials (login at `/login/`)
- A seller with at least one event containing 20+ lots

## Manual Verification

### 1. Loading Indicators (FR-001)

**Test**: Verify spinners show during panel loads.

1. Log in and observe the sellers panel loading — spinner should overlay the panel briefly.
2. Click a seller — the events panel should show a spinner overlay while loading.
3. Click an event — the main panel should show a spinner overlay while lots load.
4. Navigate to page 2 in any panel — spinner should show during pagination.

**Expected**: White semi-transparent overlay with spinning blue circle appears within 100ms of click. Panel content dims to 50% opacity during load.

### 2. Concurrent Fetching Performance (FR-002, FR-003)

**Test**: Verify event selection is fast.

1. Click an event with 25+ lots.
2. Time the load from click to table appearing.

**Expected**: Table appears in under 3 seconds (was 10–15 seconds before).

**Test**: Verify graceful degradation.

1. This is best tested via unit tests (`test_services.py`), but can be verified by checking server logs for any "Failed to fetch lot" warnings during normal operation.

### 3. Caching — Repeat Visit (FR-004, FR-005)

**Test**: Verify cached loads are fast.

1. Click an event (first load — should take ~2s).
2. Click a different event, then click back to the first event.
3. Second load should be near-instant (< 500ms).

### 4. Caching — Page Change (FR-004, FR-005)

**Test**: Verify page changes within an event are fast.

1. Click an event to load page 1.
2. Click "Next" or jump to page 2.
3. If any lots on page 2 were already cached, load should be faster.
4. Navigate back to page 1 — should be near-instant (all lots cached).

### 5. Cache Invalidation (FR-006)

**Test**: Verify overrides invalidate the cache.

1. Click an event to load lots (data is now cached).
2. Edit a lot's description via the inline table and let it auto-save.
3. Navigate away (click another event) then navigate back.
4. The edited lot should show the updated override data (not stale cached data).

### 6. Catalog Caching (FR-005)

**Test**: Verify catalog data is cached across page changes.

1. Click an event to load lots (catalog + lots fetched).
2. Change to page 2 — the server log should NOT show a new catalog API call (catalog served from cache).

## Programmatic Tests

```bash
.venv/bin/python -m pytest tests/test_services.py -v
```

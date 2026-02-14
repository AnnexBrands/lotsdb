# Quickstart: Cache Polish (016) — Manual Verification

## Prerequisites

- Redis running locally: `redis-server` on port 6379
- Dev server running: `cd src && python manage.py runserver`
- Some sellers with future events in ABConnect

## 1. Event Date Rendering (US1)

1. Open the app, click a seller with events
2. Note the event dates (e.g., "Jun 15, 2025")
3. Click a different seller, then click the first seller again (cache hit)
4. **Verify**: Event dates display identically on the cached load — not blank

## 2. Catalog Pagination (US2)

1. Find a seller with many future events (>25)
2. Click the seller, note the events panel shows page 1 with pagination
3. Click page 2
4. **Verify**: Page 2 shows the next set of events with correct pagination controls

## 3. Environment-Driven Redis URL (US3)

1. Stop the dev server
2. Set env: `export REDIS_URL=redis://127.0.0.1:6379`
3. Start the dev server
4. **Verify**: App works normally (sellers/events cache)
5. Unset env: `unset REDIS_URL`
6. Restart dev server
7. **Verify**: App still works (falls back to default localhost)

## 4. Stale-While-Revalidate (US6)

### 4a. Cache hit — instant display + background refresh

1. Click a seller (first time — populates cache)
2. Click a different seller
3. Click the first seller again
4. **Verify**: Events appear instantly (no skeleton flicker)
5. **Verify**: After a moment, the events panel content may subtly update (if server data differs)

### 4b. Cache miss — skeleton until server responds

1. Flush Redis: `redis-cli FLUSHDB`
2. Click a seller
3. **Verify**: Skeleton loading animation shows until events load from server

### 4c. Navigation during background refresh

1. Click seller A (cached — instant display)
2. Immediately click seller B before refresh completes
3. **Verify**: Seller B's events load normally — no flash of seller A's fresh data

## 5. Skeleton Row Count (US5)

1. Flush Redis: `redis-cli FLUSHDB`
2. Click a seller
3. **Verify**: Skeleton shows ~15 placeholder rows (not 3)
4. Click an event
5. **Verify**: Lots skeleton shows ~15 placeholder rows (not 4)

## 6. Test Suite

```bash
cd src && python -m pytest ../tests/ -v
```

All tests should pass including new SWR contract tests.

## 7. Redis Key Check

```bash
redis-cli KEYS "cat_*"
```

Should show `cat_:1:sellers_all` and `cat_:1:catalogs_seller_{id}` keys after using the app.

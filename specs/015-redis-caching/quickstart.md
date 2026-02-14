# Quickstart: Redis Caching for Sellers and Catalogs

**Feature Branch**: `015-redis-caching`
**Date**: 2026-02-14

## Prerequisites

1. Redis running locally on default port: `redis-cli ping` should return `PONG`
2. Python dependencies installed: `pip install redis>=5.0`

## Automated Tests

```bash
cd src && python -m pytest ../tests/ -v
```

## Manual Verification

### 1. Seller Caching (US1)

1. Start the app: `cd src && python manage.py runserver`
2. Log in and open the sellers panel
3. Note the load time for sellers (first load — cold cache)
4. Refresh the page or navigate away and back to sellers
5. **Expected**: Second load is noticeably faster (served from cache)
6. **Verify in Redis**: `redis-cli KEYS "*cat_*"` should show a `cat_sellers_all` key
7. **Verify TTL**: `redis-cli TTL ":1:cat_sellers_all"` should show ~300 seconds

### 2. Catalog Caching (US2)

1. Click a seller to load their events
2. Note the load time (first load — cold cache)
3. Click the same seller again
4. **Expected**: Events load faster on second click
5. **Verify in Redis**: `redis-cli KEYS "*cat_catalogs*"` should show a key like `cat_catalogs_seller_42`

### 3. Filter Bypass

1. Type a name in the seller filter
2. **Expected**: Results come from API (not cache) — filtered queries bypass cache
3. Clear the filter
4. **Expected**: Results come from cache again

### 4. Cache Unavailability (US3)

1. Stop Redis: `sudo systemctl stop redis` (or `redis-cli SHUTDOWN`)
2. Use the application — navigate sellers, click events
3. **Expected**: Everything works normally, just slower (no errors displayed)
4. Start Redis: `sudo systemctl start redis`
5. Navigate again
6. **Expected**: Caching resumes automatically

### 5. Key Prefix Verification

1. `redis-cli KEYS "*"` — all keys from this app should contain `cat_`
2. No keys without the `cat_` prefix should exist from this application

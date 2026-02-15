# PR Review: Redis Caching Architecture (015-redis-caching)

## Summary
This is a strong foundational cache integration with clear service-layer boundaries and graceful fallback intent. The current implementation has several correctness and operability gaps that should be fixed before relying on it in higher-scale or production-like environments.

## Findings (Ordered by Severity)

### 1. Cached `start_date` is stored as string, breaking template date rendering
- **File**: `src/catalog/services.py:117`
- **Issue**: `start_date` is cached as `str(c.start_date)`, but templates expect date/datetime objects and apply the `date` filter.
- **Evidence**: `src/catalog/templates/catalog/partials/events_panel.html:18` uses `{{ event.start_date|date:"M j, Y" }}`.
- **Impact**: event dates render empty on cache-hit paths.
- **Fix**: keep `start_date` as datetime in cache payload (or parse string back to datetime on read) and add a regression test for rendered date output.

### 2. `list_catalogs()` cache path violates pagination contract
- **File**: `src/catalog/services.py:106`, `src/catalog/services.py:122`
- **Issue**: cache-hit and cache-miss branches always return page 1 with `page_size=len(items)`, ignoring requested `page` and `page_size`.
- **Impact**: inconsistent behavior versus non-cached path; larger payloads and paging drift in callers.
- **Fix**: return `_make_paginated(items, page, page_size)` consistently.

### 3. Single-page warmup can silently truncate cached datasets
- **File**: `src/catalog/services.py:73`, `src/catalog/services.py:109`
- **Issue**: seller/cache fill uses fixed one-page fetch (`500`, `200`) and assumes completeness.
- **Impact**: incomplete cache as data grows beyond those limits.
- **Fix**: iterate API pages until complete (prefer API `total_pages`/`total_items` if available).

### 4. No cache stampede protection on misses
- **File**: `src/catalog/services.py` (cache fill sections)
- **Issue**: concurrent misses can trigger many identical upstream API requests.
- **Impact**: amplified upstream load during expirations/failures.
- **Fix**: add per-key lock (e.g., `cache.add(lock_key, 1, lock_ttl)`), short backoff, and stale fallback.

### 5. Redis config is hardcoded and under-specified for production
- **File**: `src/config/settings.py:74-77`
- **Issue**: static `redis://127.0.0.1:6379`, no env-driven URL, no TLS/auth pattern, no timeout/pool tuning.
- **Impact**: weak deploy portability/security and fragile runtime behavior.
- **Fix**: use `REDIS_URL`; support `rediss://`; set connect/socket timeouts and health checks.

### 6. Freshness model relies only on TTL
- **File**: service-level cache strategy
- **Issue**: no explicit invalidation/versioning when source data changes.
- **Impact**: stale data windows after meaningful upstream updates.
- **Fix**: add key versioning/invalidation hooks and document freshness SLAs.

### 7. Missing cache observability
- **File**: `src/catalog/cache.py`, `src/catalog/services.py`
- **Issue**: no hit/miss/fill/fallback metrics.
- **Impact**: cannot tune TTL/policies or detect regressions quickly.
- **Fix**: instrument counters/timers and log structured cache events with outcome/key class.

### 8. Test coverage gaps in cache semantics
- **File**: `tests/unit/test_cache.py:20`
- **Issue**: test passes `default="fallback"` but asserts `None`; it does not validate intended default-return behavior.
- **Impact**: false confidence in wrapper semantics.
- **Fix**: correct assertions and add integration-style tests that verify rendered dates and paginated cache-hit behavior.

## Best-Practice Upgrades (Priority Order)
1. Preserve datetime typing for cached catalog fields and add rendering regression tests.
2. Make cached and non-cached pagination semantics identical.
3. Implement full pagination fetch on cache fill.
4. Add singleflight/stampede protection.
5. Move Redis config to env and harden connection settings.
6. Introduce key versioning + explicit invalidation strategy.
7. Add cache telemetry and alerting baselines.
8. Replace operational `KEYS` usage with `SCAN` in docs.

## Source Cross-Checks
- Django cache framework and Redis backend capabilities: https://docs.djangoproject.com/en/6.0/topics/cache/
- Redis keyspace commands (`SCAN` vs `KEYS`): https://redis.io/docs/latest/develop/using-commands/keyspace/
- Redis eviction policy guidance: https://redis.io/docs/latest/develop/reference/eviction/
- redis-py connection options (TLS/timeouts/pool): https://redis.readthedocs.io/en/v5.2.0/connections.html
- Redis performance best-practices overview: https://redis.io/faq/doc/1mebipyp1e/performance-tuning-best-practices

## Final Assessment
Architecture direction is good (service-layer cache + graceful fallback), but this PR should address the high-severity correctness and pagination consistency issues before calling the implementation production-ready.

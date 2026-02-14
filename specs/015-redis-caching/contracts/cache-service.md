# Contract: Cache Service Layer

**Feature Branch**: `015-redis-caching`
**Date**: 2026-02-14

## Overview

The cache service provides safe wrappers around Django's cache framework, ensuring Redis failures never crash the application. The service layer projects full API DTOs to lightweight dicts before caching and wraps them in `SimpleNamespace` on read for dot-notation access.

## Functions

### `safe_cache_get(key, default=None)`

Retrieve a value from cache. Returns `default` if key not found or cache is unavailable.

- **Input**: `key` (str), `default` (any, optional)
- **Output**: Cached value or `default`
- **On Redis failure**: Logs warning, returns `default`
- **Never raises**: Any exception from the cache backend is caught and logged

### `safe_cache_set(key, value, timeout=None)`

Store a value in cache. No-op if cache is unavailable.

- **Input**: `key` (str), `value` (any picklable), `timeout` (int seconds, optional — uses CACHES default if None)
- **Output**: None
- **On Redis failure**: Logs warning, returns without storing
- **Never raises**: Any exception from the cache backend is caught and logged

## Cached Data Shapes

### Seller (cached dict)

```python
{"id": 42, "name": "Acme Corp", "customer_display_id": "ACME-001"}
```

Projected from `SellerExpandedDto` — only the 3 fields templates use.

### Catalog/Event (cached dict)

```python
{"id": 7, "title": "Spring Auction", "customer_catalog_id": "SA-2026", "start_date": "2026-03-15"}
```

Projected from `CatalogExpandedDto` — only the 4 fields templates use. Only future events (start_date >= today) are cached.

## Cached Service Functions

### `list_sellers(request, page=1, page_size=25, **filters)`

**Cache behavior**:
- When `filters` is empty (no name filter):
  - Cache key: `sellers_all`
  - On cache miss: fetch ALL sellers from API (page_size=500), project each to `{id, name, customer_display_id}`, cache the list of dicts
  - On cache hit: wrap cached dicts in `SimpleNamespace`, paginate locally, return
- When `filters` is non-empty (name filter active):
  - Bypass cache, call API directly (filtered results are not cached)

**Return type**: Same interface as before — paginated result with `.items` list. Items support dot-notation access (SimpleNamespace from cache, or Pydantic DTO from API).

### `list_catalogs(request, page=1, page_size=25, seller_id=None, **filters)`

**Cache behavior**:
- When `seller_id` is provided and `filters` is empty:
  - Cache key: `catalogs_seller_{seller_id}`
  - On cache miss: fetch ALL catalogs for seller (page_size=200), filter to future-only (start_date >= today), project each to `{id, title, customer_catalog_id, start_date}`, cache the list of dicts
  - On cache hit: wrap cached dicts in `SimpleNamespace`, return
- When `seller_id` is None or `filters` is non-empty:
  - Bypass cache, call API directly

**Return type**: Same interface as before.

## Test Contracts

### TC-001: Seller cache hit returns cached data without API call

- **Given**: Sellers are in cache under key `sellers_all`
- **When**: `list_sellers(request)` is called with no filters
- **Then**: Returns cached sellers as SimpleNamespace objects, API is NOT called

### TC-002: Seller cache miss fetches from API, projects, and populates cache

- **Given**: Cache is empty
- **When**: `list_sellers(request)` is called
- **Then**: API is called with page_size=500, result is projected to lightweight dicts, cached under `sellers_all`, sellers are returned

### TC-003: Seller filter bypasses cache

- **Given**: Sellers are in cache
- **When**: `list_sellers(request, Name="foo")` is called
- **Then**: API is called directly (filter bypass), cache is not consulted

### TC-004: Catalog cache hit returns cached data without API call

- **Given**: Catalogs for seller 42 are in cache under key `catalogs_seller_42`
- **When**: `list_catalogs(request, seller_id=42)` is called
- **Then**: Returns cached catalogs, API is NOT called

### TC-005: Catalog cache miss fetches, filters future, projects, and populates cache

- **Given**: Cache is empty
- **When**: `list_catalogs(request, seller_id=42)` is called
- **Then**: API is called, only future catalogs are kept, projected to lightweight dicts, cached, result is returned

### TC-006: Cache unavailable falls back to direct API call

- **Given**: Redis is down (connection refused)
- **When**: `list_sellers(request)` is called
- **Then**: Returns data from API, no error raised, warning logged

### TC-007: All cache keys use `cat_` prefix

- **Given**: Cache is configured with KEY_PREFIX `cat_`
- **When**: Any cache operation occurs
- **Then**: Redis keys are prefixed with `:1:cat_` (Django's versioned prefix format)

### TC-008: Cached seller dicts support dot-notation access

- **Given**: Sellers are cached as dicts
- **When**: Returned to a view/template
- **Then**: `seller.id`, `seller.name`, `seller.customer_display_id` all work via attribute access

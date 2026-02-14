# Research: Redis Caching for Sellers and Catalogs

**Feature Branch**: `015-redis-caching`
**Date**: 2026-02-14

## R1: Cache Backend Choice

**Decision**: Use Django's built-in `django.core.cache.backends.redis.RedisCache` (added in Django 4.0).

**Rationale**: The project already runs Django 5. The built-in backend requires only `redis` (redis-py) as a dependency — no third-party packages. It covers all required functionality: get/set with TTL, key prefixing, pickle serialization.

**Alternatives considered**:
- `django-redis`: More features (Sentinel, IGNORE_EXCEPTIONS, raw client access) but adds an unnecessary dependency. The features we'd want (IGNORE_EXCEPTIONS) are better handled with a thin wrapper.
- Direct `redis-py`: Bypasses Django cache framework, losing KEY_PREFIX and TIMEOUT config. No benefit.

## R2: Cache Lightweight Dicts, Not Full DTOs

**Decision**: Cache plain Python dicts containing only the fields the templates actually use, not the full Pydantic DTO objects.

**Rationale**: The ABConnect API returns heavyweight Pydantic models (`SellerExpandedDto`, `CatalogExpandedDto`) with dozens of fields, nested objects, and validation metadata. But the templates only use:

- **Sellers**: `id`, `name`, `customer_display_id` (3 fields)
- **Events/Catalogs**: `id`, `title`, `customer_catalog_id`, `start_date` (4 fields)

Caching the full DTOs would store ~50x more data per entry than needed. By projecting to minimal dicts at cache-write time, we get:
- Much smaller cache footprint (bytes vs kilobytes per entry)
- No dependency on ABConnect model pickling behavior across library versions
- Plain dicts are trivially serializable — no Pydantic version coupling
- To rebuild cache: fetch from API, project to dicts, store

The views already access these attributes via dot notation on the DTO objects, so the cached dicts need to support attribute-style access. A simple `types.SimpleNamespace` or a thin wrapper provides this.

**Alternatives considered**:
- Cache full Pydantic DTOs via pickle: Works (verified) but wasteful and couples cache to ABConnect internals.
- Cache `model.model_dump()` dicts: Less wasteful than full DTOs but still includes dozens of unused fields.

## R3: Graceful Fallback on Redis Unavailability

**Decision**: Wrap `cache.get` / `cache.set` in try/except helpers (`safe_cache_get`, `safe_cache_set`) that catch `Exception` and log a warning, returning None / no-op respectively.

**Rationale**: Django's built-in `RedisCache` raises `redis.exceptions.ConnectionError` when Redis is down. Unlike `django-redis`, there is no `IGNORE_EXCEPTIONS` option. A thin wrapper (6 lines per function) is simpler than subclassing the backend and keeps the failure mode explicit and logged.

**Alternatives considered**:
- Subclass `RedisCache` and override `get`/`set`: More hidden, harder to test, same outcome.
- `django-redis` with `IGNORE_EXCEPTIONS=True`: Adds a dependency just for one config flag.

## R4: Caching Level

**Decision**: Cache at the service layer in `catalog/services.py`, using `cache.get` / `cache.set` around the API calls.

**Rationale**: The service layer is the boundary between the application and the ABConnect API. Views call service functions; service functions call the API. Caching at this boundary means all views benefit automatically, and the cache key can be computed from function arguments (no request/response coupling).

`@cache_page` is wrong — it caches entire HTTP responses, which are HTMX partials with user-specific context.

**Alternatives considered**:
- View-level caching: Too coarse, caches HTML fragments that vary by user state.
- Middleware caching: Same problem — wrong granularity.

## R5: Cache Key Design

**Decision**: Use the following key patterns (Django's KEY_PREFIX `cat_` is automatically prepended by the framework):

| Cache Entry | Key (without prefix) | Notes |
|-------------|---------------------|-------|
| All sellers | `sellers_all` | Single entry for all sellers |
| Future catalogs for seller | `catalogs_seller_{seller_id}` | One entry per seller |

**Rationale**:
- Sellers: The spec says "always cache all sellers" — a single key for the entire seller list. The `list_sellers` service function fetches with pagination; the caching wrapper should fetch ALL sellers (large page_size) and store as one entry, then paginate locally on read.
- Catalogs: Keyed per seller because `list_catalogs` is always called with a `seller_id` in the panel workflow. Only future catalogs are cached (filtered by `start_date >= today`).

## R6: Dependency Requirements

**Decision**: Add `redis>=5.0` to project dependencies.

**Rationale**: `redis` (redis-py) is the only new dependency. Version 5.0+ supports the connection interface Django's built-in backend expects. Optional `hiredis` for faster C-based parsing is not needed at this scale.

## R7: Cache Population Strategy for Sellers

**Decision**: On cache miss for sellers, fetch ALL sellers from the API in a single request (page_size=500), project each to a lightweight dict (`{id, name, customer_display_id}`), and cache the list of dicts. The service layer then paginates locally from the cached list when the view requests a specific page.

**Rationale**: The spec says "always cache all sellers." The seller count is in the hundreds. One API call to populate the cache is simpler and more efficient than caching per-page. Local pagination matches the existing pattern in `seller_events_panel` (already uses `_paginate_locally()`).

# Data Model: Redis Caching for Sellers and Catalogs

**Feature Branch**: `015-redis-caching`
**Date**: 2026-02-14

## Overview

No new database entities. This feature adds a caching layer using Redis as a key-value store. Cached values are lightweight Python dicts projected from the full API response objects — only the fields the templates actually use are stored.

## Cache Entries

### Cached Seller List

- **Key**: `sellers_all` (with automatic `cat_` prefix → full Redis key: `:1:cat_sellers_all`)
- **Value**: List of dicts, each with:
  - `id` (int) — seller ID
  - `name` (str) — seller name
  - `customer_display_id` (str) — external display ID
- **TTL**: 300 seconds (5 minutes), configurable
- **Population**: On cache miss, fetch all sellers from API (page_size=500), project each DTO to `{id, name, customer_display_id}`, cache the list
- **Eviction**: Time-based expiry only

### Cached Catalog List (per seller)

- **Key**: `catalogs_seller_{seller_id}` (with automatic `cat_` prefix → full Redis key: `:1:cat_catalogs_seller_{seller_id}`)
- **Value**: List of dicts, each with:
  - `id` (int) — catalog/event ID
  - `title` (str) — event title
  - `customer_catalog_id` (str) — external catalog ID
  - `start_date` (str or None) — event start date
- **TTL**: 300 seconds (5 minutes), configurable
- **Population**: On cache miss, fetch all catalogs for seller from API (page_size=200), filter to future-only (start_date >= today), project each DTO to `{id, title, customer_catalog_id, start_date}`, cache the list
- **Eviction**: Time-based expiry only

## Attribute Access

Templates access seller/event fields via dot notation (e.g., `seller.name`, `event.title`). Cached dicts are wrapped in `types.SimpleNamespace` on read so dot-notation access works identically to the original Pydantic DTO objects.

## No Schema Changes

- No database migrations required
- No new Django models
- SQLite database is unaffected

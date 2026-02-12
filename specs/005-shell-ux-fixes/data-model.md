# Data Model: Shell UX Fixes

**Branch**: `005-shell-ux-fixes` | **Date**: 2026-02-11

## Overview

No new database entities. This feature modifies view context variables and URL parameter semantics. All data continues to come from the ABConnect Catalog API.

## Changed Identifier Semantics

### URL Parameters (before → after)

| Parameter | Before | After | Source Field |
|-----------|--------|-------|-------------|
| `seller` | Internal `seller.id` (int) | `seller.customer_display_id` (int) | `SellerDto.customer_display_id` |
| `event` | Internal `event.id` (int) | `event.customer_catalog_id` (string) | `CatalogDto.customer_catalog_id` |

### Entity Lookup by Customer ID

| Entity | Lookup Method | API Filter |
|--------|--------------|------------|
| Seller | `list_sellers(CustomerDisplayId=value)` | `CustomerDisplayId` |
| Catalog | `list_catalogs(CustomerCatalogId=value)` | `CustomerCatalogId` |

## View Context Variables

### sellers_panel

| Variable | Type | New? | Description |
|----------|------|------|-------------|
| `filter_name` | str | YES | Current name filter value from query param |

### seller_events_panel

| Variable | Type | New? | Description |
|----------|------|------|-------------|
| `filter_title` | str | YES | Current title filter value from query param |
| `seller_display_id` | int | YES | `seller.customer_display_id` for URL push |

### event_lots_panel

| Variable | Type | New? | Description |
|----------|------|------|-------------|
| `seller_display_id` | int | YES | Resolved from event's seller for URL push |
| `event_catalog_id` | str | YES | `event.customer_catalog_id` for URL push |

### Shell hydration (seller_list view at `/`)

| Variable | Type | Changed? | Description |
|----------|------|----------|-------------|
| `selected_seller_id` | int | CHANGED | Now set from `customer_display_id` lookup, still internal ID for template `.active` matching |
| `selected_event_id` | int | CHANGED | Now set from `customer_catalog_id` lookup, still internal ID for template `.active` matching |

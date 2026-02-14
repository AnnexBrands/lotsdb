# Data Model: Cache Polish (016)

## Changes to Cached Event Dict

### Before (015-redis-caching)

```python
{
    "id": int,                        # catalog ID
    "title": str,                     # event title
    "customer_catalog_id": str,       # customer-facing ID
    "start_date": str,                # "2025-06-15 10:30:45" — BROKEN: template |date filter returns ""
}
```

### After (016-cache-polish)

```python
{
    "id": int,                        # catalog ID
    "title": str,                     # event title
    "customer_catalog_id": str,       # customer-facing ID
    "start_date": str | None,         # ISO format: "2025-06-15T10:30:45" or None
}
```

**Cache write**: `c.start_date.isoformat() if c.start_date else None`
**Cache read**: `datetime.fromisoformat(d["start_date"]) if d.get("start_date") else None`

After cache read, the `SimpleNamespace` object has `start_date` as `datetime | None`, matching the uncached DTO behavior. Django's `|date:"M j, Y"` filter works correctly.

## No Changes

- Cached seller dict: `{"id", "name", "customer_display_id"}` — unchanged
- Cache keys: `sellers_all`, `catalogs_seller_{id}` — unchanged
- Cache TTL: 300s — unchanged
- Key prefix: `cat_` — unchanged

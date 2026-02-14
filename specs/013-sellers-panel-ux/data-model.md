# Data Model: Sellers Panel UX

No data model changes. This feature modifies template rendering, CSS styling, and client-side behavior only.

## Affected Entities (no changes)

| Entity | Field | Notes |
|--------|-------|-------|
| Seller | name, id, customer_display_id | Filter by name — no change to data shape |
| Catalog/Event | title, start_date, customer_catalog_id | Sort by start_date — no change to data shape |

## View-Level Change

The `seller_events_panel` view in `panels.py` will sort `result.items` by `start_date` descending before passing to the template. No model or service changes needed.

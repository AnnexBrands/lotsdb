# Research: Shell UX Fixes

**Branch**: `005-shell-ux-fixes` | **Date**: 2026-02-11

## Decision 1: Customer-Friendly ID Lookup Strategy

**Decision**: Use ABConnect API filters to look up entities by customer-facing IDs.

**Rationale**:
- Sellers: `api.sellers.list(CustomerDisplayId=4098)` returns the seller with that display ID
- Catalogs: `api.catalogs.list(CustomerCatalogId="395768")` returns the catalog with that ID (already exists as `find_catalog_by_customer_id` in services.py)
- Both endpoints support `**kwargs` for arbitrary PascalCase filters
- No new service infrastructure needed — just new service helper methods

**Alternatives considered**:
- Store a mapping table locally: Rejected — violates "no local catalog data" principle
- Use internal IDs and display friendly names elsewhere: Rejected — user explicitly wants URLs to be recognizable

## Decision 2: Lots Data Source — Expanded Catalog Response

**Decision**: Use the expanded CatalogDto response (from `get_catalog`) which includes embedded lots, and paginate locally. Remove the unreliable `list_lots_by_catalog` service call from panel views.

**Rationale**:
- The Lots list endpoint's `CustomerCatalogId` filter is unreliable (confirmed by user: "sometimes nothing returned, sometimes all across events")
- The events detail view (`events.py`) already uses this pattern: `event.lots` from expanded DTO with local pagination
- `get_catalog(event_id)` returns `CatalogExpandedDto` which includes `lots` attribute (list of `LotCatalogInformationDto` with id + lot_number)
- However, `LotCatalogInformationDto` only has `id` and `lot_number` — for full lot data (description, notes, images), we need to fetch individual lots or use a different approach

**Important caveat**: The embedded lots in the expanded catalog only have `id` and `lot_number`. For the lot cards in the main panel, we need description, notes, and images. Two approaches:
1. Fetch each lot individually via `get_lot()` — too many API calls
2. Use the Lots list endpoint but with the correct lot IDs from the catalog — batch fetch
3. Keep using `list_lots_by_catalog` but pass `CustomerCatalogId` as a string filter on the Catalog endpoint first to validate

**Revised decision**: Use `services.list_catalogs(CustomerCatalogId=customer_catalog_id)` to get the catalog, then use `list_lots_by_catalog` with the validated `customer_catalog_id`. The real fix is ensuring we pass the correct `customer_catalog_id` string value. The current code already does this — the issue may be in how the value is obtained or formatted.

**Final approach**: Keep `list_lots_by_catalog` but ensure `customer_catalog_id` is passed as the correct string. Add error handling for empty results. The user's "broken" experience may stem from mismatched IDs when navigating via internal IDs that don't correspond to the right catalog.

## Decision 3: Panel Header Filter Implementation

**Decision**: Replace static `<h3>` headers in seller and events panels with inline filter inputs using HTMX `hx-get` on form submission.

**Rationale**:
- The old `/sellers/` and `/events/` pages already have filter support (name, is_active for sellers; title, agent for events)
- Panel headers have limited space — use a single text input for the most useful filter (name for sellers, title for events)
- On Enter/submit, `hx-get` reloads the panel content with the filter param
- When a record is selected, clear the input and set placeholder to "Selected: <name>"

**Implementation**:
- Filter form in each panel header partial (not the list partial) using `hx-get` to panel endpoint
- `sellers_panel` view reads `name` filter param and passes to `list_sellers`
- `seller_events_panel` view reads `title` filter param and passes to `list_catalogs`
- Template includes a small form with input + hidden params for existing context

## Decision 4: Empty State Improvements

**Decision**: Make empty states contextual — differentiate between "nothing selected" and "selected but no results".

**Rationale**:
- Currently after selecting an event, the events panel OOB reset of main panel shows "Select an event to view lots" — but an event IS selected, this is the events panel's OOB clear for the main content
- The fix: when events panel renders, the OOB main-panel clear should say "Select an event to view lots" (this is correct since no event is selected yet at that point — a NEW seller was clicked)
- The lots panel's own empty state ("No lots in this event") is correct
- The confusion may be: after selecting a seller, the main panel shows "Select an event..." which IS correct

**Actual fix needed**: The OOB clear of `#panel-main-content` in `events_panel.html` correctly shows "Select an event to view lots" — this is right because selecting a seller clears the lots panel. The user's complaint may be about the events panel itself still showing old text. Need to verify and fix the specific confusing state.

## Decision 5: HTMX Indicator Wiring

**Decision**: Add explicit `hx-indicator` attributes on panel trigger elements pointing to their parent panel's `.htmx-indicator` div.

**Rationale**:
- Current CSS relies on `.htmx-request .htmx-indicator` but HTMX adds the `htmx-request` class to the element making the request, not the target panel
- With `hx-sync="this:replace"` on panels, the panel gets the request class — this should work since triggers inherit from parent
- However, for clicks on `<li>` items that target a DIFFERENT panel, the requesting panel gets the class but the TARGET panel's indicator should fire
- Fix: Use `hx-indicator` attribute on trigger elements pointing to the target panel's indicator

**Implementation**: Add `hx-indicator="#panel-left2 .htmx-indicator"` on seller list items, `hx-indicator="#panel-main .htmx-indicator"` on event list items.

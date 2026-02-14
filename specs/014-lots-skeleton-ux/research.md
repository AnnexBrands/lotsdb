# Research: Lots Panel Skeleton Loading

## R1: Existing skeleton pattern in the codebase

**Decision**: Reuse the existing skeleton CSS classes (`skeleton-bar`, `skeleton-pulse` animation, `skeleton-loading` container) and the JS `htmx:beforeRequest` event listener pattern.

**Rationale**: The events panel already implements skeleton loading on seller click (`shell.html:250-268`). The pattern is proven: build an HTML string in JS, inject it into the target panel's content div on `htmx:beforeRequest`, and let the HTMX response replace it naturally. No new libraries or patterns needed.

**Alternatives considered**:
- Server-rendered skeleton partial: Rejected — adds an HTTP round-trip and defeats the purpose of instant feedback.
- CSS-only shimmer on existing content: Rejected — doesn't clear stale data, and the column structure would be wrong if switching between events with different lot counts.

## R2: Skeleton row structure

**Decision**: The skeleton row will be a `<tr>` with 7 `<td>` elements matching the lots table columns: thumbnail (56x56 rounded rect), description (two bars: title + notes), dimensions (cluster of small bars), and placeholders for cpack/crate/dnt/action columns.

**Rationale**: Matching the real column structure eliminates layout shift when real data replaces the skeleton. The existing `lots_table_row.html` has 7 `<td>` elements. Each skeleton `<td>` mirrors the approximate width and height of its real counterpart using `skeleton-bar` divs.

**Alternatives considered**:
- Simple list-style skeleton (like events panel): Rejected — would cause a jarring layout shift when the table replaces the list.
- Full table with header: Accepted — include the real `<thead>` in the skeleton so column headers appear immediately.

## R3: Trigger condition for lots skeleton

**Decision**: Show the lots skeleton when `htmx:beforeRequest` fires with `target.id === 'panel-main-content'` AND the triggering element is a `.panel-item` inside `#panel-left2` (events panel). This distinguishes event clicks from seller clicks (which target `panel-left2-content`) and from pagination (which also targets `panel-main-content` but triggers from pagination controls).

**Rationale**: The existing seller-click handler already sets `mainEmptyHTML` for the lots panel. The new event-click handler must not conflict with it. Checking that the trigger element is inside the events panel ensures only event clicks produce lots skeletons.

**Alternatives considered**:
- Check `e.detail.elt.closest('#panel-left2')`: This works and is the chosen approach.
- Use a custom HTMX header: Rejected — over-engineered for a simple DOM check.

## R4: Number of skeleton rows

**Decision**: 4 skeleton rows. This matches the default visible area at typical viewport heights without overshooting for small result sets.

**Rationale**: The default page size is 25 lots, so there will always be content to fill. But showing too many skeleton rows (e.g., 25) creates excessive DOM and visual noise. 4 rows fill the visible area above the fold and give a clear "loading" signal.

## R5: Event sort order instability on event click (FR-008)

**Decision**: Add `events_result.items.sort(key=lambda e: e.start_date or "", reverse=True)` in `event_lots_panel()` before passing OOB events to the template context.

**Rationale**: `seller_events_panel()` sorts events by `start_date` descending (FR-011 from spec 013). But `event_lots_panel()` fetches events for the OOB swap via `services.list_catalogs()` without applying the same sort. When the OOB swap re-renders the events panel, the unsorted API response order replaces the sorted list, causing the events to visually reorder on every event click.

**Root cause**: `src/catalog/views/panels.py:228` — `events_result.items` is passed to context as `oob_events` without sorting. The fix is a single `.sort()` call matching the pattern already used at line 168.

**Alternatives considered**:
- Sort in template: Rejected — Django templates don't support lambda-based sorting.
- Extract sort into a shared helper: Considered, but a one-liner `.sort()` in two places is simpler than an abstraction.

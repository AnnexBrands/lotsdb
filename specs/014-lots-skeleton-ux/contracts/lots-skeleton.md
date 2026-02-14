# Contract: Lots Panel Skeleton HTML

## Trigger

The skeleton is shown when ALL of these conditions are true:
- `htmx:beforeRequest` fires
- Target is `#panel-main-content`
- Triggering element is a `.panel-item` inside `#panel-left2` (events panel)

The skeleton is NOT shown when:
- A seller is clicked (target is `#panel-left2-content`) — shows empty state instead
- Pagination controls are clicked (trigger is inside `.panel-pagination`)

## Expected HTML Structure

The skeleton consists of a `<table class="lots-table">` with a real `<thead>` (matching the production table headers) and a `<tbody>` containing 4 skeleton `<tr>` rows.

Each skeleton row has 7 `<td>` cells matching the lots table columns:

| Column | Cell Content |
|--------|-------------|
| Thumbnail | 56x56 rounded skeleton rectangle |
| Description | Two skeleton bars: title (~60% width) + notes (~40% width, shorter) |
| Dimensions | Cluster of small skeleton bars (~4ch wide each) |
| CPack | Single small skeleton bar |
| Crate | Single small skeleton bar |
| DNT | Single small skeleton bar |
| Action | Empty (no skeleton needed) |

All skeleton bars use the existing `skeleton-bar` class with `skeleton-pulse` animation.

## Lifecycle

1. Event click triggers `htmx:beforeRequest`
2. JS replaces `#panel-main-content` innerHTML with skeleton table HTML
3. HTMX response arrives and replaces `#panel-main-content` innerHTML with real lots panel
4. Skeleton is fully removed — no cleanup needed

## CSS Classes

New classes needed:
- `.skeleton-table-row` — skeleton `<tr>` styling
- `.skeleton-thumb` — 56x56 skeleton thumbnail placeholder

Reused classes:
- `.lots-table` — table wrapper
- `.skeleton-bar` — animated bar placeholder
- `.skeleton-pulse` — pulse animation (via `skeleton-bar`)

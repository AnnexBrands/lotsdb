# Research: Shell Interaction Polish

**Branch**: `004-shell-interaction-polish` | **Date**: 2026-02-11

## Decision 1: Selection State Highlighting

**Decision**: Server-side OOB swap approach

**Rationale**: When a seller is clicked, `seller_events_panel()` returns both the events panel AND an updated seller list via `hx-swap-oob` with `selected_seller_id` in context. This is the canonical HTMX/HATEOAS pattern — state lives on the server and flows via HTML.

**Key benefits**:
- Selection survives pagination (server always knows the selected ID)
- Works with deep linking and URL hydration
- Single source of truth (server context)
- Already proven: OOB swaps are tested in existing contract tests
- No client-side state management or JavaScript needed

**Alternatives considered**:
- *Client-side JS toggle*: Simpler (10-15 LOC JS) but selection is lost on pagination, can't deep link, violates HTMX philosophy. Rejected.
- *Hybrid (client JS + server context)*: Worst of both worlds — split brain between client and server state, race conditions on rapid clicks, high test complexity. Rejected.

**Server load impact**: Negligible. Re-rendering paginated seller list adds ~2-5KB HTML and ~5-10ms template time. ABConnect API calls are the dominant cost and are already happening.

**Implementation sketch**:
```python
# seller_events_panel view: re-render seller list with selected_seller_id
# events_panel.html: add OOB swap block for panel-left1-content
# event_lots_panel view: pass selected_event_id to events panel OOB
```

## Decision 2: URL State Synchronization

**Decision**: Server-side `HX-Push-Url` response header + Django shell view hydration

**Rationale**: Two complementary mechanisms:
1. **URL updates after clicks**: Django views set the `HX-Push-Url` response header with the shell URL (`/?seller=42&event=7`). HTMX respects this header and pushes the URL into browser history automatically, handling both push and pop (back/forward).
2. **Initial page hydration**: The shell view reads `?seller=<id>&event=<id>` from `request.GET` and pre-renders all panels server-side.

**Key benefits**:
- Zero JavaScript for URL management
- HTMX handles history caching/restoration automatically
- Back/forward buttons work correctly (HTMX manages `popstate`)
- Shareable URLs work via server-side hydration
- Clean separation: views already know seller/event IDs from path params

**Alternatives considered**:
- *`hx-push-url` attribute*: Pushes fragment endpoint URL (`/panels/sellers/42/events/`), not the shell URL with query params. Wrong URL. Rejected.
- *`hx-replace-url` attribute*: Same problem as `hx-push-url`. Rejected.
- *`htmx:afterSwap` + `history.pushState` in JS*: Breaks HTMX's internal history cache. Manual `pushState` bypasses DOM snapshot/restore, causing broken back button behavior. Rejected.

**Implementation sketch**:
```python
# seller_events_panel: response["HX-Push-Url"] = f"/?seller={seller_id}"
# event_lots_panel: response["HX-Push-Url"] = f"/?seller={seller_id}&event={event_id}"
# seller_list (shell view): read request.GET params, pre-fetch if present
```

## Decision 3: Loading Indicator Consistency

**Decision**: Add `htmx-indicator` div to Left1 panel (matching Left2/Main pattern)

**Rationale**: Left2 and Main already have `.htmx-indicator` divs inside the panel wrapper. Left1 is missing this. The fix is structural: add the same indicator markup to the Left1 panel in `shell.html`. The existing CSS rules (`.htmx-request .htmx-indicator { display: flex }`) handle the rest.

**Key requirement**: The Left1 panel must have its content wrapped in a div that receives `hx-sync` and triggers the `.htmx-request` class. Currently the shell has `hx-sync="this:replace"` on the panel wrapper, but Left1's content loads inline (not via HTMX swap on initial render). Pagination clicks inside Left1 need to trigger the indicator on the panel wrapper.

**Implementation sketch**:
```html
<!-- shell.html: add indicator to Left1 panel, matching Left2/Main pattern -->
<div id="panel-left1" class="panel panel-left1" hx-sync="this:replace">
    <div class="htmx-indicator"><div class="spinner"></div></div>
    <!-- existing content -->
</div>
```

Pagination links in `panel_pagination.html` already target `#panel-left1-content` with `hx-swap="innerHTML"`. The `hx-indicator` attribute or parent `.htmx-request` class propagation will show the spinner during these requests.

## Decision 4: Responsive Mobile Layout

**Decision**: Minimal vanilla JS listening for HTMX events + CSS media query

**Rationale**: A ~35-line IIFE script listens for `htmx:afterSwap` events and toggles a `data-mobile-panel` attribute on `.shell`. CSS media query `@media (max-width: 767px)` hides all panels except the one matching the data attribute. A back button provides navigation: Lots -> Events -> Sellers.

**Key benefits**:
- Natural drill-down UX matching mobile app patterns
- Back button for clear backwards navigation
- Focus management: script focuses first interactive element on panel switch
- ARIA live region announces panel transitions for screen readers
- Script only runs on mobile viewports (early return on desktop)
- Handles resize gracefully: desktop -> mobile preserves state, mobile -> desktop shows all panels

**Alternatives considered**:
- *CSS-only stacked*: All panels visible at once — cognitive overload on mobile, poor UX. Rejected.
- *CSS `:target` hack*: Fragment URLs conflict with HTMX, no back button, accessibility issues. Rejected.
- *HTMX + server-injected CSS classes*: Server must know about mobile layout state (coupling), no back button without extra server logic. Rejected.

**Implementation sketch**:
```html
<!-- shell.html additions -->
<div class="shell" data-mobile-panel="sellers">
  <button class="mobile-back-btn" id="mobile-back-btn">Back</button>
  <div class="panel" data-panel="sellers">...</div>
  <div class="panel" data-panel="events">...</div>
  <div class="panel" data-panel="lots">...</div>
</div>
<div id="panel-announcer" role="status" aria-live="polite" class="sr-only"></div>
```
```css
@media (max-width: 767px) {
  .shell { grid-template-columns: 1fr; }
  .panel { display: none; }
  .shell[data-mobile-panel="sellers"] .panel[data-panel="sellers"] { display: block; }
  /* ... same for events, lots */
}
```

## Decision 5: Pagination Parameter Validation

**Decision**: Clamp invalid values to defaults instead of raising ValueError

**Rationale**: Current code uses raw `int()` on query params. Bad values raise `ValueError` -> 500 error. Replace with a helper that returns clamped defaults: page defaults to 1, page_size defaults to 50, both clamped to positive integers.

**Implementation sketch**:
```python
def _parse_page_params(request, default_page_size=50):
    try:
        page = max(1, int(request.GET.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = max(1, min(200, int(request.GET.get("page_size", default_page_size))))
    except (ValueError, TypeError):
        page_size = default_page_size
    return page, page_size
```

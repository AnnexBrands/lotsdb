# Research: SPA Shell Layout

**Feature Branch**: `003-spa-shell-layout`
**Date**: 2026-02-11

## Decision 1: HTMX Multi-Target Swap Pattern

**Decision**: Use `hx-target` for the primary swap, plus `hx-swap-oob` in the server response for secondary panel updates.

**Rationale**: Clicking a seller in Left1 must update Left2 (events) and optionally clear Main (lots). With `hx-target="#panel-left2"` on the seller link, the primary response swaps into Left2. The server response includes an OOB fragment `<div id="panel-main" hx-swap-oob="innerHTML">...</div>` to clear or update Main simultaneously. This is a single HTTP request — no extensions, no custom JS.

**Alternatives Considered**:
- `hx-select-oob` (client-side extraction): Less explicit; harder to debug since the template doesn't declare what it updates.
- `multi-swap` extension: Third-party dependency for something OOB handles natively.
- Separate HTMX requests per panel: Doubles round trips, creates race conditions.
- `hx-swap="none"` + all OOB: Works but unintuitive — no primary target makes debugging harder.

## Decision 2: HTMX Request Cancellation

**Decision**: Use `hx-sync="this:replace"` on each panel container, inherited by all child elements.

**Rationale**: Without `hx-sync`, clicking Seller A then Seller B fires parallel requests. Whichever finishes last wins the DOM swap — a race condition. The `replace` strategy on the panel container aborts the in-flight request and replaces it with the new one. Applied via inheritance on `#panel-left1`, it covers all seller links automatically.

**Alternatives Considered**:
- `drop` strategy: Ignores new clicks while in-flight — confusing UX.
- `queue last`: Waits for first request to finish, adding latency.
- No `hx-sync`: Race condition. Unacceptable.
- JavaScript `htmx:abort` event: Requires manual tracking. `hx-sync` is declarative.

## Decision 3: CSS Three-Column Layout

**Decision**: CSS Grid with `grid-template-columns: 250px 300px 1fr`, `grid-template-rows: auto 1fr`, `height: 100vh` on the shell container, and `min-height: 0; overflow-y: auto` on each panel.

**Rationale**: CSS Grid handles both the navbar row and three-column panel row in a single layout context. `100vh` constrains to viewport, enabling independent scroll on each panel. `min-height: 0` is critical — without it, grid children default to `min-height: auto`, which prevents overflow scrolling.

**Alternatives Considered**:
- Flexbox: Requires two nested containers (vertical + horizontal). Grid is more direct.
- `position: fixed` panels: Fragile, breaks with dynamic navbar heights.
- `100dvh`: Unnecessary for desktop-first SPA. `100vh` has broader support.

## Decision 4: Django Partial Template Pattern

**Decision**: Separate URL endpoints for panel fragments. No `HX-Request` header checking. Use `{% include %}` for template reuse between the full shell page and fragment endpoints.

**Rationale**: Each URL returns exactly one thing — a full page or a fragment. No branching logic in views. Contract tests hit fragment endpoints directly. No third-party packages required.

**Alternatives Considered**:
- Single view with `HX-Request` header check: Introduces branching, ambiguity, and `Vary: HX-Request` caching complexity.
- `django-template-partials`: Dependency for syntactic sugar over `{% include %}`.
- `django-render-block`: Parses full template even when only a block is needed.
- `django-htmx` middleware: No value when not checking headers.

## Decision 5: Visual Design Direction

**Decision**: Evolve the existing design system (system font stack, blue/slate palette, card-based components) into a polished product-quality UI. Keep the existing color foundation (#2563eb primary, #1e293b dark) but refine spacing, typography scale, panel headers, selection states, and transitions.

**Rationale**: The current CSS is a solid functional foundation with clean structure. Rather than replacing it with a framework (Tailwind, Bootstrap), we refine what exists. This avoids dependency bloat, keeps the CSS maintainable, and preserves continuity with existing pages (lot detail, override, import) that remain outside the SPA shell.

**Alternatives Considered**:
- Tailwind CSS: Would require build tooling (PostCSS, npm). The project uses CDN-only dependencies. Adding a build step is scope creep.
- Bootstrap: Opinionated grid system would conflict with our CSS Grid shell. Heavy CSS payload for components we don't need.
- Complete redesign: Unnecessary. The existing palette and component patterns are professional. They need refinement, not replacement.

## Decision 6: URL State Synchronization with Query Parameters

**Decision**: Use server-side `HX-Push-Url` response header to push custom URLs with query parameters (`?seller=123&event=456`) instead of fragment endpoint URLs. Combine with Django shell view hydration that reads query params on initial page load.

**Rationale**: This approach solves both the "update URL after clicks" and "load a shared URL" problems:

1. **After clicks (URL update)**: When the user clicks a seller/event, the panel fragment endpoint sets the `HX-Push-Url` response header to the shell URL with appropriate query params. HTMX respects this header and updates the browser URL to `/?seller=123` or `/?seller=123&event=456`, not the fragment endpoint URL.

2. **Initial page load (URL hydration)**: The Django `seller_list` view (shell) reads `?seller=<id>&event=<id>` from `request.GET`. If present, it pre-fetches the seller, events, and lots data and renders the shell with those panels populated. No JavaScript required.

3. **Back button (popstate)**: HTMX handles this automatically. When the user clicks back, HTMX restores from its DOM cache if available. If not cached, it makes a request to the URL in history (the shell URL with query params), which the Django view hydrates correctly.

**Implementation Details**:

```python
# In views/panels.py
from django.http import HttpResponse

def seller_events_panel(request, seller_id):
    # ... existing logic ...
    response = render(request, "catalog/partials/events_panel.html", context)
    response["HX-Push-Url"] = f"/?seller={seller_id}"
    return response

def event_lots_panel(request, event_id):
    # ... fetch event to get seller_id ...
    response = render(request, "catalog/partials/lots_panel.html", context)
    response["HX-Push-Url"] = f"/?seller={event.seller_id}&event={event_id}"
    return response
```

```python
# In views/sellers.py
def seller_list(request):
    seller_id = request.GET.get("seller")
    event_id = request.GET.get("event")

    # Fetch sellers (always)
    sellers = services.list_sellers(request)

    # If seller_id, pre-fetch events
    events = None
    if seller_id:
        events = services.list_catalogs(request, seller_id=seller_id)

    # If event_id, pre-fetch lots
    lots = None
    if event_id:
        lots = services.list_lots_by_catalog(request, event_id)

    return render(request, "catalog/shell.html", {
        "sellers": sellers,
        "events": events,
        "lots": lots,
        "selected_seller_id": seller_id,
        "selected_event_id": event_id,
    })
```

**Alternatives Considered**:

### 1. HTMX `hx-push-url` attribute
**Rejected**: When `hx-push-url="true"`, HTMX pushes the fragment endpoint URL (`/panels/sellers/42/events/`) into browser history, not the shell URL with query params. When `hx-push-url="/custom-url"`, HTMX doesn't preserve query parameters from the current URL or allow dynamic values based on response data. This makes it unsuitable for our use case.

**Complexity**: Low (attribute only) but doesn't solve the problem.

### 2. HTMX `hx-replace-url` attribute
**Rejected**: Same fundamental limitation as `hx-push-url`. It replaces history instead of pushing, but still pushes the fragment endpoint URL, not a custom shell URL with query params.

**Complexity**: Low but doesn't solve the problem.

### 3. `htmx:afterSwap` event + `history.pushState`
**Considered**: Listen for the `htmx:afterSwap` event, extract the seller/event ID from the request URL or response, and manually call `history.pushState` with the desired query string.

**Example**:
```javascript
document.body.addEventListener("htmx:afterSwap", (event) => {
  const requestUrl = event.detail.pathInfo.requestPath;
  // Parse /panels/sellers/42/events/ to extract seller_id
  const match = requestUrl.match(/\/panels\/sellers\/(\d+)\/events\//);
  if (match) {
    const sellerId = match[1];
    history.pushState({}, "", `/?seller=${sellerId}`);
  }
});
```

**Rejected**:
- Requires custom JavaScript (violates "no JS frameworks, CDN-only" constraint)
- Breaks HTMX's built-in history caching mechanism. HTMX snapshots the DOM when it pushes a URL via `hx-push-url`. If we bypass HTMX and call `history.pushState` directly, HTMX doesn't know about the history entry and won't cache/restore correctly.
- Back button becomes fragile: HTMX expects `popstate` events to correspond to URLs it pushed, not manually injected ones.
- Duplicates URL parsing logic that the server already handles.

**Complexity**: Medium (50-100 LOC JavaScript, event handling, URL parsing, history management). Does NOT handle back button correctly without additional work to sync HTMX history cache.

### 4. Server-side `HX-Push-Url` response header (CHOSEN)
**Accepted**: The Django view sets the `HX-Push-Url` response header with the desired shell URL and query params. HTMX respects this header and pushes that URL into history instead of the request URL.

**Handles both push and pop**:
- Push: Header sets the URL directly.
- Pop: HTMX handles `popstate` events automatically. It either restores from cache OR re-requests the URL (which is the shell URL with query params, so the Django view hydrates correctly).

**Works with existing architecture**: Fragment endpoints already know the seller/event IDs — they're in the URL path (`/panels/sellers/42/events/`). No URL parsing needed.

**Complexity**: Low (~10 LOC Python per endpoint, 2 lines per response).

### 5. Django shell view hydration (REQUIRED for all approaches)
**Accepted**: This is not an alternative to the other approaches — it's a required complement. Regardless of how we update the URL after clicks, we must handle initial page loads with query params. The shell view reads `?seller=<id>&event=<id>` and pre-renders panels.

**Handles initial load**: When a user loads `/?seller=123&event=456` directly (shared link, bookmark, browser refresh), the Django view fetches the seller, events, and lots data and renders the full shell with those panels populated.

**Complexity**: Medium (~50-80 LOC Python in `seller_list` view to conditionally fetch events/lots based on query params and pass to template).

**No impact on click behavior**: This only affects initial page load. The HTMX fragment endpoints and URL update mechanism (approach 4) handle subsequent navigation.

## Recommendation: Server-Side `HX-Push-Url` + Django Hydration

**Selected**: Approach 4 (`HX-Push-Url` response header) + Approach 5 (Django shell view hydration)

**Why**:
1. **Simplicity**: ~10 LOC Python per endpoint to set response header. ~50 LOC Python in shell view for hydration. No custom JavaScript. No build tools. No new dependencies.
2. **Correctness**: HTMX handles history caching/restoration automatically. Back/forward buttons work as expected.
3. **Architecture alignment**: Fragment endpoints already know seller/event IDs from URL path params. Shell view already renders panels — just needs conditional data fetching.
4. **Shareable links**: Users can copy `/?seller=123&event=456` and share it. The recipient sees the same panels.
5. **Browser refresh**: Refreshing the page maintains state because the URL holds the state.

**Total LOC estimate**: ~80-100 lines of Python (2 response headers per panel endpoint, ~50 lines of hydration logic in shell view, template conditionals).

**No JavaScript required**: All state management happens server-side via response headers and query param parsing.

**Testing**: Contract tests verify response headers. Integration tests verify hydration logic.

## Summary

| Topic | Decision | Key Dependency |
|-------|----------|---------------|
| Multi-target swap | `hx-target` + `hx-swap-oob` | HTMX 2.0.4 (already installed) |
| Request cancellation | `hx-sync="this:replace"` | HTMX 2.0.4 (already installed) |
| CSS layout | CSS Grid, `100vh`, `min-height: 0` | No dependencies |
| Django partials | Separate endpoints + `{% include %}` | No dependencies |
| Visual design | Evolve existing CSS | No dependencies |
| URL state sync | `HX-Push-Url` header + shell hydration | HTMX 2.0.4 (already installed) |

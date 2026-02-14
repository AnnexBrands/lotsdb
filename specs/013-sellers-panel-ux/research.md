# Research: Sellers Panel UX

## R1: Debounced Realtime Filtering with HTMX

**Decision**: Use HTMX's built-in `hx-trigger="input changed delay:300ms"` on the filter input to achieve debounced realtime filtering without custom JavaScript.

**Rationale**: HTMX natively supports trigger modifiers including `delay:` which debounces the trigger. The current seller filter form uses `hx-get` on the `<form>` element — by moving the `hx-get` and trigger attributes to the `<input>` element directly with `hx-trigger="input changed delay:300ms"`, we get debounced realtime filtering with zero JavaScript. The `changed` modifier ensures the request only fires if the value actually changed, and `delay:300ms` provides the debounce.

**Alternatives considered**:
- Custom JavaScript debounce wrapper: Adds complexity, not needed since HTMX supports it natively
- `hx-trigger="keyup delay:300ms"`: Works but `input` is better — it captures paste, clear, autofill events too
- Client-side filtering: Not feasible — seller list is paginated server-side with potentially hundreds of entries

## R2: Skeleton Loading Pattern

**Decision**: Use a pre-built skeleton HTML snippet injected into the events panel via JavaScript `htmx:beforeRequest` event handler. When a seller item is clicked, immediately swap the events panel content with skeleton HTML before the HTMX request fires.

**Rationale**: HTMX's built-in `hx-indicator` shows/hides an element but doesn't replace content. To show skeletons (which replace the panel content), we need to inject skeleton HTML before the request fires. The `htmx:beforeRequest` event is the right hook — it fires after HTMX has set up the request but before it sends. We intercept requests targeting `#panel-left2-content` and replace its innerHTML with skeleton markup.

**Alternatives considered**:
- `hx-indicator` with CSS skeletons: Only overlays; doesn't replace stale content underneath
- `hx-on::before-request` inline attribute: Works but puts logic in the template; prefer centralized JS in shell.html
- `hx-swap="innerHTML show:none"` + separate skeleton trigger: Over-complicated, two requests instead of one

## R3: Skeleton Visual Design

**Decision**: Static CSS skeleton using muted gray bars with a subtle pulse animation. Three placeholder rows mimicking the event list item shape (title bar + metadata bar). A small spinner centered above the rows.

**Rationale**: Matches the existing design system (slate colors, rounded corners). Three rows is enough to convey "content is loading" without overdoing it. A pulse animation (opacity oscillation) provides visual feedback that loading is active, complementing the spinner.

**Alternatives considered**:
- Shimmer/gradient animation: More complex CSS, higher visual weight than needed for this simple list
- No animation (static gray bars only): Feels broken/frozen without movement
- Full-height skeleton filling the panel: Overkill — three representative rows suffice

## R4: Events Sorting by Start Date

**Decision**: Sort events client-side after receiving from the API, using `start_date` descending (most recent first). Implemented in the `seller_events_panel` view before passing to the template.

**Rationale**: The ABConnect `catalogs.list()` API returns events in its own default order. Since we paginate server-side (default 50 per page), sorting the page of results in the view is trivial and doesn't require API changes. Sorting descending by `start_date` puts the most relevant (recent) events at the top.

**Alternatives considered**:
- API-level sort parameter: Would require ABConnectTools changes; not available in current API
- Template-level sort filter: Django templates don't support complex sorting; better in the view
- No sort (keep API order): Doesn't meet FR-011

## R5: Main Panel Clear on Seller Selection

**Decision**: The events panel response already includes an OOB swap for `#panel-main-content` that shows "Select an event to view lots". This existing behavior (in `events_panel.html` via `skip_main_oob`) already handles FR-010. No changes needed.

**Rationale**: The current `events_panel.html` template already includes an OOB innerHTML swap for `panel-main-content` that resets it to the empty state. This fires whenever a seller is clicked and events are loaded. FR-010 is already satisfied by the existing implementation.

## R6: Request Cancellation on Rapid Seller Clicks

**Decision**: The existing `hx-sync="this:replace"` on `#panel-left2` already handles FR-008. When a new request targets the same panel, HTMX cancels the previous in-flight request and replaces it with the new one.

**Rationale**: The shell.html already has `hx-sync="this:replace"` on each panel div, which tells HTMX to abort any pending request for that element when a new one arrives. This naturally handles the "click seller A, then quickly click seller B" case.

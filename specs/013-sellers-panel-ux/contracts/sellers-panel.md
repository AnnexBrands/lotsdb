# Contract: Sellers Panel UX

## Overview

Defines the rendering and behavior contracts for the sellers panel realtime filter and skeleton loading. No API endpoint changes — existing endpoints are reused with modified HTMX trigger behavior.

## Realtime Filter Contract

### Trigger Behavior

The seller filter input MUST:
- Fire a GET request to `/panels/sellers/` on every input change
- Debounce with a 300ms delay (only the last keystroke in a burst triggers a request)
- Include the current filter value as the `name` query parameter
- Target `#panel-left1-content` for the response swap
- Show the panel loading indicator during the request

### HTMX Attribute Contract

The filter `<input>` element MUST have:
```
hx-get="/panels/sellers/"
hx-target="#panel-left1-content"
hx-swap="innerHTML"
hx-trigger="input changed delay:300ms, search"
hx-indicator="#panel-left1 .htmx-indicator"
```

The parent `<form>` MUST NOT have `hx-get` (moved to the input to avoid double-firing on form submit).

## Skeleton Loading Contract

### HTML Structure

When a seller is clicked and the events panel is loading, the panel content MUST show:

```html
<div class="skeleton-loading">
    <div class="skeleton-spinner"><div class="spinner"></div></div>
    <ul class="skeleton-list">
        <li class="skeleton-item">
            <div class="skeleton-bar skeleton-title"></div>
            <div class="skeleton-bar skeleton-meta"></div>
        </li>
        <!-- 3 skeleton items total -->
    </ul>
</div>
```

### CSS Class Contract

| Class | Element | Purpose |
|-------|---------|---------|
| `.skeleton-loading` | Container | Wraps spinner + placeholder rows |
| `.skeleton-spinner` | Spinner wrapper | Centers the spinner above the skeleton rows |
| `.skeleton-list` | List wrapper | Matches `.panel-list` padding/spacing |
| `.skeleton-item` | Single row | Matches `.panel-item` height/padding |
| `.skeleton-bar` | Placeholder bar | Rounded gray bar with pulse animation |
| `.skeleton-title` | Title placeholder | ~60% width, taller bar |
| `.skeleton-meta` | Metadata placeholder | ~40% width, shorter bar |

### Injection Behavior

- Skeleton HTML MUST be injected into `#panel-left2-content` via the `htmx:beforeRequest` event
- ONLY when the request target is `#panel-left2-content` AND the trigger is a seller item click (not pagination or filter)
- The main panel (`#panel-main-content`) MUST also be cleared to the default empty state at the same time

## Events Sort Contract

Events returned by `seller_events_panel` MUST be sorted by `start_date` descending (most recent first) before rendering.

## Test Contract

Contract tests MUST verify:
1. The seller filter input has `hx-trigger` with `delay:300ms`
2. The events panel response includes events (when present)
3. Override/active states still work after template changes
4. Events are sorted by start_date descending when multiple events exist

# Feature Specification: Shell Interaction Polish

**Feature Branch**: `004-shell-interaction-polish`
**Created**: 2026-02-11
**Status**: Draft
**Input**: PR #4 review (`specs/003-spa-shell-layout/pr-4-review.md`) identified four prioritized follow-up items to close gaps in FR-004 (selection state), FR-010 (loading indicators), URL-addressable state, and mobile/narrow viewport support.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Active Selection Highlighting (Priority: P1)

As a catalog operator, I want the currently selected seller and event to be visually highlighted so that I always know which context I am browsing and do not lose my place when paginating or switching selections.

**Why this priority**: Active context is essential for trust and rapid navigation in multi-panel UIs. Without it, operators lose track of which seller/event is driving the current view.

**Independent Test**: Click a seller — it highlights in Left1. Click an event — it highlights in Left2. The seller stays highlighted. Paginate sellers — the selected seller remains highlighted if visible. Click a different seller — the old highlight clears, the new one appears, and Left2/Main reset.

**Acceptance Scenarios**:

1. **Given** I click a seller in Left1, **When** the Events panel loads, **Then** the clicked seller row has the `.active` CSS class (blue left border + light blue background).
2. **Given** a seller is selected, **When** I paginate the Sellers panel, **Then** the selected seller retains `.active` if it appears on the current page.
3. **Given** a seller is selected, **When** I click a different seller, **Then** the previous seller loses `.active` and the new seller gains it.
4. **Given** I click an event in Left2, **When** the Lots panel loads, **Then** the clicked event row has the `.active` CSS class.
5. **Given** a seller and event are selected, **When** I click a different seller, **Then** the event highlight clears along with the Events panel content.

---

### User Story 2 - Consistent Loading Indicators (Priority: P2)

As an operator, I want to see consistent loading feedback across all panel interactions so that I know the system is working and can trust the interface.

**Why this priority**: Inconsistent feedback patterns reduce perceived speed and increase operator uncertainty. Left2 and Main have indicators; Left1 does not.

**Independent Test**: Trigger a load in each panel (click seller, click event, paginate sellers). Each panel shows a spinner overlay during the request. All three behave identically.

**Acceptance Scenarios**:

1. **Given** I click a seller in Left1, **When** the HTMX request is in flight, **Then** the Left2 panel shows a spinner overlay with dimmed content.
2. **Given** I paginate the Sellers panel, **When** the request is in flight, **Then** the Left1 panel shows a spinner overlay with dimmed content.
3. **Given** I click an event in Left2, **When** the request is in flight, **Then** the Main panel shows a spinner overlay with dimmed content.
4. **Given** any panel shows a loading indicator, **When** the response arrives, **Then** the indicator disappears and the new content is displayed immediately.
5. **Given** a panel request fails, **When** the error state renders, **Then** a retry button is shown and the loading indicator is cleared.

---

### User Story 3 - URL-Addressable Shell State (Priority: P3)

As an operator, I want the browser URL to reflect my current seller, event, and pagination selections so that I can share links, use back/forward navigation, and restore my view after a page refresh.

**Why this priority**: Enables shareable links, better back/forward behavior, and improved external-customer readiness. Without URL state, refreshing the page loses all context.

**Independent Test**: Select a seller and event. Verify the URL updates to include seller and event IDs. Copy the URL, open in a new tab — the same seller and event are pre-selected. Use back/forward buttons — selections update accordingly.

**Acceptance Scenarios**:

1. **Given** I click a seller, **When** the Events panel loads, **Then** the browser URL updates to include `?seller=<id>` without a full page reload.
2. **Given** I click an event, **When** the Lots panel loads, **Then** the browser URL updates to include `&event=<id>`.
3. **Given** I navigate to a URL with `?seller=<id>&event=<id>`, **When** the page loads, **Then** the shell hydrates with the specified seller's events and event's lots pre-loaded, and both are highlighted.
4. **Given** I have selected a seller and event, **When** I click the browser back button, **Then** the previous selection state is restored.
5. **Given** I paginate a panel, **When** the new page loads, **Then** the URL does NOT include panel pagination state (pagination is transient).

---

### User Story 4 - Mobile/Narrow Viewport Layout (Priority: P4)

As an operator on a tablet or narrow screen, I want the panel layout to adapt so that I can still navigate sellers, events, and lots without horizontal scrolling or overlapping panels.

**Why this priority**: Edge-case already identified in the original spec (< 768px). No responsive behavior is currently implemented. The grid overflows on narrow screens.

**Independent Test**: Resize the browser to < 768px. Panels stack vertically. Clicking a seller scrolls to or reveals the Events panel. Clicking an event scrolls to or reveals the Lots panel. A back/up affordance lets the user return to the previous panel.

**Acceptance Scenarios**:

1. **Given** the viewport width is < 768px, **When** the page loads, **Then** the layout switches from a three-column grid to a single-column stacked view showing only the Sellers panel.
2. **Given** I am on a narrow viewport with Sellers visible, **When** I click a seller, **Then** the Events panel slides in or becomes visible, replacing or stacking below the Sellers panel.
3. **Given** I am viewing Events on a narrow viewport, **When** I click an event, **Then** the Lots panel becomes visible.
4. **Given** I am viewing Events or Lots on a narrow viewport, **When** I tap a back/breadcrumb affordance, **Then** I return to the previous panel.
5. **Given** the viewport is resized from narrow to wide (>= 768px), **When** the resize completes, **Then** the layout reverts to the three-column grid with current selections preserved.

---

### Edge Cases

- What happens if the selected seller is on a different pagination page? The `.active` class is only applied when the selected seller appears on the currently rendered page; no auto-navigation to the selected page occurs.
- What happens if the URL contains an invalid seller or event ID? The shell loads normally with an empty Events/Lots panel and no error; the invalid param is ignored.
- What happens on extremely narrow viewports (< 320px)? The stacked layout remains functional; panels fill viewport width.
- What happens if the user modifies the URL hash/params manually? The shell re-hydrates on page load based on whatever params are present.
- What happens if a panel request fails while the URL already has state? The URL retains the params; the panel shows an error state with retry.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-101**: System MUST pass `selected_seller_id` to the Sellers panel template and apply `.active` class to the matching row.
- **FR-102**: System MUST pass `selected_event_id` to the Events panel template and apply `.active` class to the matching row.
- **FR-103**: System MUST preserve selection highlighting across panel pagination.
- **FR-104**: System MUST show a spinner overlay with dimmed content for ALL panel HTMX requests, including Left1 pagination.
- **FR-105**: System MUST unify loading indicator markup and behavior across all three panels.
- **FR-106**: System MUST update the browser URL query parameters (`?seller=<id>&event=<id>`) when selections change, without a full page reload.
- **FR-107**: System MUST hydrate the shell from URL query parameters on initial page load (server-side rendering of pre-selected state).
- **FR-108**: System MUST support browser back/forward navigation by pushing history entries on selection changes.
- **FR-109**: System MUST switch to a stacked single-panel layout on viewports < 768px.
- **FR-110**: System MUST provide a back/breadcrumb affordance to return to the previous panel on narrow viewports.
- **FR-111**: System MUST gracefully handle invalid seller/event IDs in URL parameters (ignore and show empty panels).
- **FR-112**: System MUST reject invalid pagination parameters gracefully (HTTP 400 or clamped defaults) instead of raising ValueError.

### Key Entities

No new entities are introduced. This feature modifies the behavior of existing panel views and templates for Seller, Event (Catalog), and Lot entities defined in `003-spa-shell-layout`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-101**: Selected seller and event are visually highlighted in all interactions (click, paginate, switch).
- **SC-102**: All three panels show identical loading indicator behavior during HTMX requests.
- **SC-103**: A URL with `?seller=<id>&event=<id>` restores the full shell state on page load.
- **SC-104**: Browser back/forward buttons correctly restore previous selection states.
- **SC-105**: The layout is functional and usable at viewport widths from 320px to 2560px.
- **SC-106**: Invalid pagination query parameters return HTTP 400 or silently clamp to valid defaults.

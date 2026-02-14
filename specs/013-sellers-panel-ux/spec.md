# Feature Specification: Sellers Panel UX

**Feature Branch**: `013-sellers-panel-ux`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "improve UX for sellers panel. header search should apply realtime filtering on input. selecting a seller should clear the events panel and load visually appealing skeletons with a spinner until the server responds."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Realtime Search Filtering (Priority: P1)

A staff user types into the sellers panel search field and sees the seller list filter in realtime as they type. The filtering is debounced so that rapid typing does not flood the server with requests — only after the user pauses briefly does the filter request fire. The results update smoothly without the user needing to press Enter or click a button.

**Why this priority**: Realtime filtering is the most impactful UX improvement — it eliminates the friction of waiting for a form submission and makes finding sellers feel instant.

**Independent Test**: Can be tested by typing a partial seller name into the search field and verifying results filter down after a brief pause.

**Acceptance Scenarios**:

1. **Given** the sellers panel is loaded with multiple sellers, **When** the user types "Acme" into the search field, **Then** the seller list filters to show only sellers matching "Acme" after a short debounce delay (300ms).
2. **Given** the user is typing rapidly, **When** they type "A", "Ac", "Acm", "Acme" in quick succession, **Then** only one server request fires (after the final keystroke + debounce delay), not four.
3. **Given** the user has typed a filter and results are showing, **When** they clear the search field, **Then** the full unfiltered seller list is restored.
4. **Given** the user types a filter that matches no sellers, **When** the results return, **Then** the panel shows an appropriate empty state message.

---

### User Story 2 - Skeleton Loading on Seller Selection (Priority: P1)

When a staff user clicks a seller, the events panel (left2) immediately clears its current content and displays a visually appealing skeleton placeholder with a spinner. This skeleton mimics the shape of the events list (a few placeholder rows with muted bars) so the user perceives structured content loading rather than a blank void or a simple overlay. The skeleton remains visible until the server responds with the actual events data, at which point the skeleton is replaced with the real content.

**Why this priority**: The current loading state is a semi-transparent overlay on stale content. Skeleton loading is a modern pattern that provides better perceived performance and a more polished feel.

**Independent Test**: Can be tested by clicking any seller and observing that the events panel immediately shows skeleton placeholders before the real data arrives.

**Acceptance Scenarios**:

1. **Given** the events panel shows content from a previously selected seller, **When** the user clicks a different seller, **Then** the events panel immediately clears and shows skeleton placeholders with a spinner.
2. **Given** the events panel is in its default empty state ("Select a seller to view events"), **When** the user clicks a seller, **Then** the events panel shows skeleton placeholders with a spinner.
3. **Given** the skeleton is showing, **When** the server responds with events data, **Then** the skeleton is replaced with the real events list smoothly.
4. **Given** the skeleton is showing, **When** the server responds with zero events, **Then** the skeleton is replaced with the empty state ("No events found").

---

### Edge Cases

- What happens if the user clicks a second seller while the first is still loading? The new request should cancel the previous one and show fresh skeletons.
- What happens if the search filter request fails (network error)? The panel should show an error state, not remain in a loading state forever.
- What happens if the user types a filter while a seller is selected? The selected state should be preserved visually if the selected seller is still in the filtered results.
- What happens on mobile (single-panel mode)? The skeleton loading should work the same way when the user navigates from sellers to events panel.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The sellers panel search field MUST filter results in realtime as the user types, with a debounce delay to prevent excessive requests.
- **FR-002**: The debounce delay MUST be between 200-400ms — fast enough to feel responsive, slow enough to avoid unnecessary requests.
- **FR-003**: Clearing the search field MUST restore the full unfiltered seller list.
- **FR-004**: When a seller is clicked, the events panel MUST immediately clear its content and display skeleton placeholders with a spinner.
- **FR-005**: Skeleton placeholders MUST visually resemble the shape of the events list (multiple rows with muted placeholder bars mimicking title and metadata lines).
- **FR-006**: The skeleton MUST include a spinner to indicate active loading.
- **FR-007**: When the server responds, the skeleton MUST be replaced with the real content (events list or empty state).
- **FR-008**: If a second seller is clicked while the first is loading, the previous request MUST be cancelled and new skeletons shown.
- **FR-009**: The existing seller selection state (active highlight, blue left border) MUST continue to work correctly.
- **FR-010**: The main panel (lots) MUST also clear to its default empty state when a new seller is selected (since the previous lots belong to a different seller's event).
- **FR-011**: Events in the events panel MUST be sorted by start date (most recent first) so users see the most relevant events at the top.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Seller search results update within 500ms of the user stopping typing (debounce + server response).
- **SC-002**: Rapid typing of 5+ characters produces at most 2 server requests (debounced).
- **SC-003**: When a seller is clicked, the events panel shows skeleton placeholders within 50ms (immediate visual feedback, no stale content visible).
- **SC-004**: Users perceive the loading transition as smooth and intentional — no flash of blank content or jarring layout shifts.
- **SC-005**: No regression in existing seller selection, pagination, or mobile navigation workflows.

## Assumptions

- "Realtime filtering" means debounced input-triggered server requests, not client-side filtering of already-loaded data. The seller list is paginated server-side and may have hundreds of entries, so client-side filtering is not feasible.
- "Skeleton placeholders" are static HTML/CSS elements (not animated shimmer effects) — simple muted bars that approximate the shape of event list items. This keeps the implementation simple while achieving the visual goal.
- The debounce delay of ~300ms is a standard UX default and does not need user configuration.
- The skeleton loading pattern applies to the events panel (left2) when a seller is clicked. The same pattern could later be extended to other panels but is out of scope here.
- The main panel (lots) should revert to its default "Select an event" empty state when a new seller is clicked, since the previous event context is no longer valid.

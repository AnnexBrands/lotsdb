# Feature Specification: Lots Panel Skeleton Loading

**Feature Branch**: `014-lots-skeleton-ux`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "improve ux for selecting an event. clear the lots and show skeletons matching the structure of img, title and notes, dims, etc."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Skeleton loading when selecting an event (Priority: P1)

When a staff member clicks an event in the events panel, the lots panel immediately clears and displays skeleton placeholder rows that visually match the real lots table structure: a thumbnail placeholder, description/notes bars, dimension input placeholders, and remaining column placeholders. This gives instant visual feedback that data is loading and primes the user's eye for where content will appear.

**Why this priority**: This is the core feature. Users currently see either stale lots from the previous event or a generic spinner overlay, which creates uncertainty about whether the click registered and doesn't hint at the layout of incoming content.

**Independent Test**: Click any event in the events panel and observe the lots panel immediately shows skeleton rows matching the table column layout before real data loads.

**Acceptance Scenarios**:

1. **Given** a user is viewing lots for Event A, **When** they click Event B in the events panel, **Then** the lots panel immediately clears and shows skeleton placeholder rows matching the lots table column structure (thumbnail, description, dimensions, cpack, crate, dnt, action).
2. **Given** a user is viewing the "Select an event" empty state, **When** they click an event, **Then** the lots panel shows skeleton placeholder rows while loading.
3. **Given** skeleton rows are displayed, **When** the lots data finishes loading, **Then** the skeletons are fully replaced by the real lots table with no visual glitch or double-render.

---

### User Story 2 - No regression on seller click (Priority: P2)

When a staff member clicks a seller (which triggers both events and lots panels to update), the lots panel should continue showing the "Select an event to view lots" empty state rather than skeleton rows, since no event has been selected yet.

**Why this priority**: Ensures the skeleton only appears in the right context (event selection), not when the lots panel should show an empty state.

**Independent Test**: Click a seller and verify the lots panel shows the existing empty state message, not skeleton rows.

**Acceptance Scenarios**:

1. **Given** a user is viewing lots for an event, **When** they click a different seller, **Then** the lots panel shows "Select an event to view lots" (existing behavior preserved).

---

### User Story 3 - Stable event sort order on event selection (Priority: P1)

When a staff member clicks an event to load its lots, the events panel re-renders (via OOB swap) to highlight the selected event. The events list MUST maintain the same sort order (most recent first by start date) that was shown when the seller was initially selected. Currently, the OOB re-render fetches events without sorting, causing the list to visually reorder.

**Why this priority**: The sort order changing on every click is disorienting and makes it hard to navigate through events sequentially. This is a bug fix bundled with the skeleton UX improvement.

**Independent Test**: Click an event and verify the events list order does not change — only the active highlight moves.

**Acceptance Scenarios**:

1. **Given** a user is viewing events sorted by start date (most recent first), **When** they click an event to load lots, **Then** the events list maintains the same sort order with the clicked event highlighted.
2. **Given** a seller has events with mixed start dates, **When** the user clicks through several events, **Then** the events list order remains stable across all clicks.

---

### Edge Cases

- What happens when the event has zero lots? The skeleton shows briefly, then the real empty/no-lots state replaces it. This is acceptable.
- What happens if the network request fails? The skeleton is replaced by the existing error state. No change to error handling needed.
- What happens on very fast responses? The skeleton may flash briefly; this is acceptable as it still provides layout continuity rather than a jarring content swap.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display skeleton placeholder rows in the lots panel immediately when a user clicks an event, before the lots data loads.
- **FR-002**: Skeleton rows MUST visually match the column structure of the real lots table: thumbnail area, description/notes area, dimensions area, and remaining columns.
- **FR-003**: Skeleton rows MUST use animated pulse placeholders consistent with the existing skeleton style used in the events panel.
- **FR-004**: The skeleton MUST replace any existing lots content (previous event's lots or empty state) immediately on event click.
- **FR-005**: The skeleton MUST be fully replaced by real lots content when the response arrives, with no leftover skeleton elements.
- **FR-006**: Clicking a seller MUST continue to show the "Select an event to view lots" empty state in the lots panel (no skeleton).
- **FR-007**: The skeleton SHOULD display 3-5 placeholder rows to suggest content without overcommitting to a specific count.
- **FR-008**: When events are re-rendered via OOB swap (on event selection), they MUST maintain the same sort order (start date descending) as the initial events panel load.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users see structured skeleton feedback within 100ms of clicking an event (perceived instant response).
- **SC-002**: Skeleton row layout aligns with the real lots table columns so there is no jarring layout shift when real data replaces skeletons.
- **SC-003**: Existing seller-click behavior (clearing lots to empty state) is preserved with no regression.
- **SC-004**: All existing tests continue to pass after the change.
- **SC-005**: Events list sort order remains stable when clicking through multiple events.

## Assumptions

- The skeleton is rendered client-side (same pattern as the existing events panel skeleton), not server-rendered.
- The number of skeleton rows is fixed (not derived from expected lot count) since the count is unknown until the response arrives.
- The existing skeleton CSS classes and animation will be reused for visual consistency.

# Feature Specification: Critical Bug Fixes

**Feature Branch**: `018-critical-bug-fixes`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "Cache read/write always fails; first event not auto-selected on seller click; lots table save (red disk) does nothing and breaks modal; notes in modal not editable"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cache Reads and Writes Succeed (Priority: P1)

As a user, when I navigate the application, previously-fetched seller and event data should load instantly from cache. Currently, every cache read and write fails with warnings (`Cache read failed for key=catalogs_seller_2`, `Cache write failed for key=catalogs_seller_2`), forcing every page load to hit the remote API. This degrades performance and defeats the purpose of the caching layer introduced in feature 015/016.

**Why this priority**: Cache failures affect every single user interaction — sellers, events, and lots all rely on cache for fast load times. Fixing this unblocks the SWR (stale-while-revalidate) pattern and eliminates unnecessary API calls on every navigation.

**Independent Test**: Can be fully tested by selecting a seller, observing no cache warning in logs, then re-selecting the same seller and confirming the events load from cache (no API call logged on second load).

**Acceptance Scenarios**:

1. **Given** the application is running with cache properly configured, **When** a user selects a seller for the first time, **Then** the system fetches events from the API, stores them in cache without error, and no "Cache write failed" warning appears in logs.
2. **Given** events for a seller are already cached, **When** the user navigates back to the same seller, **Then** the system serves events from cache without error, no "Cache read failed" warning appears in logs, and events load noticeably faster than the initial fetch.
3. **Given** the cache service is unavailable (e.g., stopped), **When** a user selects a seller, **Then** the system gracefully falls back to the API without crashing, and appropriate warnings are logged.

---

### User Story 2 - First Event Auto-Selected on Seller Click (Priority: P1)

As a user, when I click a seller in the sellers panel, I expect the first event in the events list to be automatically selected and its lots to load in the main panel. Currently, after clicking a seller, the events list populates but no event is highlighted or clicked — the lots panel remains empty until the user manually clicks an event.

**Why this priority**: This is a core navigation workflow. Every user session starts by selecting a seller, and the expectation is immediate lots visibility. Requiring an extra click on every seller change wastes time and breaks the intended UX flow.

**Independent Test**: Can be fully tested by clicking any seller that has events and confirming the first event becomes active (highlighted) and lots appear in the main panel without any additional clicks.

**Acceptance Scenarios**:

1. **Given** the sellers panel is visible with multiple sellers, **When** the user clicks a seller that has events, **Then** the events panel loads, the first event is automatically selected (highlighted with active state), and the lots for that event load in the main panel.
2. **Given** a seller is already selected, **When** the user clicks a different seller, **Then** the previous selection clears, the new seller's events load, the first event auto-selects, and the corresponding lots appear.
3. **Given** a seller has no events, **When** the user clicks that seller, **Then** the events panel shows "No events for this seller" and the lots panel shows an appropriate empty state.

---

### User Story 3 - Lots Table Save Completes Successfully (Priority: P1)

As a user, when I modify dimension fields (length, width, height, weight, quantity, crate, CPack, DNT) in the lots table and click the red disk save button, I expect the changes to be sent to the server and persisted. Currently, clicking the save button produces no network activity — the save silently fails, and subsequent attempts to open the lot detail modal also fail.

**Why this priority**: Saving lot overrides is the primary data-entry task in the application. If saves don't work, the entire tool is non-functional for its core purpose. The cascading failure that breaks modals makes this especially severe.

**Independent Test**: Can be fully tested by changing a dimension value in the lots table, clicking the red disk button, observing a network request in the browser developer tools, and confirming the saved value persists after page refresh.

**Acceptance Scenarios**:

1. **Given** the lots table is displayed with editable fields, **When** the user changes a dimension value and clicks the red disk save button, **Then** a POST request is sent to the server, the row updates to reflect the saved state, and the save button shows brief success feedback.
2. **Given** a lot override has been saved, **When** the user clicks the lot thumbnail to open the detail modal, **Then** the modal opens successfully showing the updated values.
3. **Given** the user modifies a field and moves focus to another row (blur), **Then** the auto-save triggers and persists the changes without requiring a manual save click.
4. **Given** the server returns an error during save, **When** the save request fails, **Then** an error toast notification appears and the modal remains functional for subsequent interactions.

---

### User Story 4 - Notes Editable in Lot Detail Modal (Priority: P2)

As a user, when I open the lot detail modal and see the notes section, I expect to be able to click on the notes text, edit it inline, and have my changes automatically saved when I click away (blur). Currently, the notes text is displayed as read-only and cannot be edited. The desired interaction is an editable paragraph element (not a textarea) that saves on blur via a PUT/POST to the server.

**Why this priority**: Notes editing is an important workflow for adding context to lots, but it does not block the core dimension-override workflow. The backend endpoint already exists; only the frontend needs to be connected.

**Independent Test**: Can be fully tested by opening a lot modal, clicking on the notes text, typing a change, clicking elsewhere, and confirming the updated notes appear on next modal open.

**Acceptance Scenarios**:

1. **Given** the lot detail modal is open and a lot has existing notes, **When** the user clicks on the notes text, **Then** the text becomes editable inline (contenteditable paragraph, not a textarea).
2. **Given** the user has edited notes text in the modal, **When** the user clicks outside the notes area (blur), **Then** the modified notes are sent to the server via the text-save endpoint and a success confirmation appears.
3. **Given** a lot has no existing notes, **When** the user opens the modal, **Then** a placeholder (e.g., "Click to add notes") is shown and clicking it allows inline editing.
4. **Given** the user edits notes and the save fails, **When** the server returns an error, **Then** an error notification appears and the edited text remains visible so the user can retry.

---

### Edge Cases

- What happens when multiple users edit the same lot's notes simultaneously? Last write wins (acceptable for current user base).
- What happens when the cache contains stale data from a previous application version? Cache entries persist until explicitly busted on insert; a Redis `FLUSHDB` or app restart with cleared Redis handles version changes.
- What happens if the user clicks the save button rapidly multiple times? The existing concurrent-save queueing mechanism should prevent duplicate requests.
- What happens if the browser loses network connectivity during a save? The HTMX error handler should show an error toast and preserve the unsaved state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST successfully read from and write to the cache without errors under normal operating conditions (cache service running and reachable).
- **FR-002**: System MUST log cache operations at DEBUG level on success and WARNING level only on genuine failures (e.g., cache service unreachable).
- **FR-003**: System MUST auto-select the first event in the events panel when a user clicks a seller, triggering the lots to load without additional user interaction.
- **FR-004**: System MUST send a POST request to the override endpoint when the user clicks the red disk save button after modifying lot fields in the table.
- **FR-005**: System MUST keep the lot detail modal functional after a save operation — whether the save succeeds or fails.
- **FR-006**: System MUST render notes in the lot detail modal as an inline-editable element (contenteditable paragraph) rather than read-only text.
- **FR-007**: System MUST save modified notes to the server when the editable notes element loses focus (blur event), using the existing text-save endpoint.
- **FR-008**: System MUST display a placeholder prompt when no notes exist, indicating the field is editable.
- **FR-009**: System MUST preserve existing override data (dimensions, flags) when saving notes, and vice versa (merge behavior).

### Key Entities

- **Lot Override**: The set of user-modified fields for a lot, including dimensions (qty, l, w, h, wgt), flags (force_crate, do_not_tip), packaging (cpack), and text (description, notes). Overrides merge with existing data on each save.
- **Cache Entry**: A time-limited stored copy of API response data (sellers list, events per seller) used to accelerate subsequent page loads.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero "Cache read failed" or "Cache write failed" warnings appear in application logs during normal operation (cache service running).
- **SC-002**: Clicking a seller with events results in the first event being auto-selected and lots visible within a single user action (no extra click required).
- **SC-003**: 100% of lot override saves via the red disk button produce a visible network request and either a success or error response within 5 seconds.
- **SC-004**: The lot detail modal opens successfully both before and after save operations — no cascading failures.
- **SC-005**: Users can edit notes inline in the lot modal and see changes persisted on the next modal open, completing the edit-save cycle in under 10 seconds.

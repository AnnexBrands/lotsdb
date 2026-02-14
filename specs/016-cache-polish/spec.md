# Feature Specification: Cache Polish

**Feature Branch**: `016-cache-polish`
**Created**: 2026-02-14
**Status**: Draft
**Input**: PR review of 015-redis-caching identifying correctness bugs and best-practice gaps

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Event Dates Render Correctly from Cache (Priority: P1)

A staff member clicks a seller to view their upcoming events. On the first click, event dates display correctly (e.g., "Jan 1, 2099"). On subsequent clicks, the data loads from cache, and event dates must still display identically — not as blank or raw text.

**Why this priority**: This is a correctness bug. Cached event dates currently render empty because the template date formatting expects a date-like value but receives plain text after cache round-trip.

**Independent Test**: Click a seller twice. On the second (cached) load, verify event dates display in the same human-readable format as the first load.

**Acceptance Scenarios**:

1. **Given** a cached event list for a seller, **When** the events panel renders, **Then** each event's start date displays in the same formatted style as uncached events (e.g., "Jan 1, 2099").
2. **Given** a fresh cache fill for a seller's events, **When** the data is stored and later retrieved, **Then** the start_date value retains enough type fidelity for the template date formatter to produce correct output.

---

### User Story 2 - Consistent Pagination on Cached Catalogs (Priority: P1)

A staff member navigates to a seller with many future events. The events panel should respect pagination parameters identically whether data comes from cache or from the upstream source. Currently, the cached path ignores the requested page and page size, returning all items as a single page.

**Why this priority**: This is a contract violation that causes inconsistent behavior between cached and uncached code paths.

**Independent Test**: Request page 2 of a seller's events (when more events than page size exist). Verify the response returns the correct page with correct pagination metadata, regardless of whether data came from cache.

**Acceptance Scenarios**:

1. **Given** a seller with 30 cached future events and a page size of 25, **When** page 1 is requested, **Then** 25 events are returned with `has_next_page=True`.
2. **Given** the same cached data, **When** page 2 is requested, **Then** 5 events are returned with `has_previous_page=True` and `has_next_page=False`.

---

### User Story 3 - Environment-Driven Cache Connection (Priority: P2)

An operator deploys the application to a new environment. Instead of editing source code to point to the correct cache server, they set a single environment variable to configure the connection. If no variable is set, the application defaults to a local cache server on the standard port.

**Why this priority**: Hardcoded connection details reduce deploy portability. Environment-driven configuration is a standard best practice and a quick win.

**Independent Test**: Set the environment variable to a different address, start the application, and verify it attempts to connect to that address. Unset the variable and verify it falls back to localhost.

**Acceptance Scenarios**:

1. **Given** the environment variable is set to a custom address, **When** the application starts, **Then** it connects to the specified address.
2. **Given** the environment variable is not set, **When** the application starts, **Then** it connects to the default local address on the standard port.

---

### User Story 4 - Correct Test Assertions for Cache Helpers (Priority: P2)

A developer runs the test suite after making changes to the cache layer. The tests must accurately validate the intended behavior — specifically, that the default-return behavior of the cache wrapper works as documented. A test that passes a custom default but asserts a different value does not provide confidence.

**Why this priority**: A misleading test erodes confidence in the cache safety net and could mask regressions.

**Independent Test**: Run the unit test suite for cache helpers. Verify all assertions match the documented behavior of each function.

**Acceptance Scenarios**:

1. **Given** a cache miss (key not found), **When** the cache wrapper is called with a custom default value, **Then** the wrapper returns that custom default value, and the test asserts this correctly.

---

### User Story 5 - More Skeleton Rows During Loading (Priority: P2)

When a panel is loading data, the skeleton placeholder should show enough rows to fill the visible panel area. Currently only 3 skeleton rows display, which looks sparse and doesn't accurately preview the expected content density.

**Why this priority**: A visual polish item that improves perceived loading quality with minimal effort.

**Independent Test**: Trigger a panel load and verify 15 skeleton placeholder rows appear instead of 3.

**Acceptance Scenarios**:

1. **Given** a panel is loading data, **When** skeleton placeholders render, **Then** 15 skeleton rows are displayed.

---

### User Story 6 - Instant Cache Display with Background Refresh for Events (Priority: P1)

A staff member clicks a seller. If cached events exist for that seller, the events panel immediately displays the cached results — no loading skeleton, no wait. In the background, the system simultaneously fetches the full event list from the server. Once the server response arrives, the events panel seamlessly replaces its content with the fresh server data and updates the cache.

**Why this priority**: This is the highest-impact UX improvement in this feature. It eliminates perceived latency for repeat visits (the most common workflow) while ensuring data freshness on every click. Staff see results instantly and always end up with current data.

**Independent Test**: Click a seller that has cached events. Verify events appear instantly (no skeleton). Wait a moment, then verify the panel content updates to reflect the latest server data.

**Acceptance Scenarios**:

1. **Given** cached events exist for a seller, **When** the user clicks that seller, **Then** cached events display immediately with no loading indicator.
2. **Given** cached events are displayed, **When** the background server fetch completes, **Then** the panel content is replaced with the fresh server data.
3. **Given** cached events are displayed and the background fetch returns different data (e.g., a new event was added), **Then** the panel updates to show the new data.
4. **Given** no cached events exist for a seller, **When** the user clicks that seller, **Then** the loading skeleton remains visible until the server responds — the skeleton is never cleared to show empty content.
5. **Given** cached events are displayed and the background fetch fails (server error), **Then** the cached data remains visible — no error shown to the user.

---

### Edge Cases

- What happens when a cached event has a null start_date? The template should handle it gracefully (display nothing), same as the uncached path.
- What happens when the environment variable contains an invalid address? The application should start without error (graceful fallback already exists) and log a warning on first cache access.
- What happens when the background refresh returns while the user has already navigated to a different seller? The stale panel content should not be replaced — the refresh applies only if the same seller is still selected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Cached event start dates MUST retain sufficient type fidelity for template date formatting to produce identical output as uncached data.
- **FR-002**: The cached catalog code path MUST respect the requested `page` and `page_size` parameters, producing identical pagination metadata as the uncached path.
- **FR-003**: The cache server connection address MUST be configurable via an environment variable, with a sensible default when unset.
- **FR-004**: All unit test assertions for cache helper functions MUST accurately reflect the documented behavior of those functions.
- **FR-005**: Existing graceful fallback behavior MUST be preserved — the application continues to function when the cache server is unavailable.
- **FR-006**: Skeleton loading placeholders MUST show 15 rows instead of 3.
- **FR-007**: When cached events exist for a seller, the system MUST display them immediately upon seller click, with no loading skeleton.
- **FR-008**: The system MUST simultaneously fetch fresh events from the server in the background after displaying cached results.
- **FR-009**: When the background fetch completes, the events panel MUST seamlessly replace its content with the fresh server data.
- **FR-010**: If the background fetch fails, the cached data MUST remain visible with no error shown to the user.
- **FR-011**: If the user navigates to a different seller before the background fetch completes, the stale response MUST NOT replace the current panel content.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Event dates display identically on first load and all subsequent cached loads — zero visual difference.
- **SC-002**: Paginated requests to cached catalog data return correct page slices and metadata, matching the uncached path for all page/page_size combinations.
- **SC-003**: Application connects to a cache server specified by environment variable within one deployment cycle, with zero code changes required.
- **SC-004**: 100% of cache helper unit tests have assertions that match their documented behavior — no misleading passes.
- **SC-005**: Skeleton loading shows 15 rows, filling the visible panel area during loads.
- **SC-006**: Repeat visits to a seller with cached events show results in under 100ms (perceived instant) — no loading skeleton visible.
- **SC-007**: Fresh server data replaces cached content within the normal server response time, ensuring users always end up with current data.

## Assumptions

- The review items for multi-page cache warmup (#3), stampede protection (#4), key versioning (#6), and cache telemetry (#7) are deferred. This is a low-concurrency internal tool where 500-seller and 200-catalog-per-seller limits are sufficient, TTL-based freshness is acceptable, and warning-level logging provides adequate observability.
- The existing `safe_cache_get`/`safe_cache_set` wrapper pattern is preserved — no architectural changes to the cache layer.
- The `cat_` key prefix and 300-second TTL are retained unchanged.

## Scope Boundaries

### In Scope
- Fix start_date type fidelity through cache round-trip
- Fix catalog cache pagination to use consistent pagination helper
- Make cache server URL environment-configurable
- Fix misleading test assertion
- Increase skeleton loading rows from 3 to 15
- Stale-while-revalidate pattern: show cached events instantly, background refresh from server

### Out of Scope
- Multi-page cache warmup (review item #3)
- Cache stampede protection (review item #4)
- Key versioning or explicit invalidation (review item #6)
- Cache hit/miss counters or telemetry (review item #7)
- Lot/item caching (explicitly deferred per original spec)

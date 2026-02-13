# Spec: Performance UX — Loading Feedback & Optimization

**Feature**: 010-performance-ux | **Status**: Draft | **Date**: 2026-02-13

## Overview

Clicking an event currently takes 10–15 seconds with no visual feedback. This feature addresses three layers of the problem: (1) immediate loading feedback so users know something is happening, (2) concurrent API fetching to reduce actual load time from ~13s to ~1–2s, and (3) in-memory caching to make repeat visits and page changes near-instant.

## Root Cause Analysis

The bottleneck is in `services.get_lots_for_event()` which makes N sequential HTTP requests to the ABConnect API (one `GET /api/Lot/{id}` per lot). With the default page size of 25 lots at ~500–700ms per round-trip, this totals 12–17 seconds. There is no batch lot endpoint available in the ABConnect API.

A secondary issue is that the HTMX loading indicators exist in the DOM but never display — the `hx-indicator` attributes target the indicator div directly, but the CSS uses a descendant selector (`.htmx-request .htmx-indicator`) that requires `htmx-request` on a parent element, not the indicator itself.

## User Stories

### US1: Loading Feedback on Event Selection (P0)

As an operator, I want to see immediate visual feedback when I click an event so I know the system is responding.

**Why P0**: Users currently see nothing for 10–15 seconds and assume the app is broken.

**Acceptance Scenarios:**
1. **Given** an event list, **When** the operator clicks an event, **Then** the main panel shows a loading spinner overlay within 100ms.
2. **Given** the main panel is loading, **When** data arrives, **Then** the spinner disappears and the lots table renders.
3. **Given** any panel is loading via HTMX, **When** the request is in-flight, **Then** the panel content dims (opacity) and a spinner overlays it.

---

### US2: Concurrent Lot Fetching (P0)

As an operator, I want event selection to complete in under 3 seconds so I can work efficiently.

**Why P0**: The sequential fetching is the root cause of the 10–15 second wait.

**Acceptance Scenarios:**
1. **Given** an event with 25 lots, **When** the operator selects it, **Then** the lots table loads in under 3 seconds.
2. **Given** an event with 100 lots on a page of 25, **When** lots are fetched, **Then** all 25 API calls execute concurrently via thread pool.
3. **Given** concurrent fetching, **When** one lot request fails, **Then** the error is logged and remaining lots still display (graceful degradation).

---

### US3: Lot Data Caching (P1)

As an operator, I want page changes and revisits to the same event to load instantly so I can navigate lots without waiting.

**Why P1**: After the first load is fast (US2), caching makes subsequent interactions near-instant.

**Acceptance Scenarios:**
1. **Given** an event was loaded 2 minutes ago, **When** the operator returns to it, **Then** the lots table loads from cache in under 500ms.
2. **Given** cached lot data, **When** the operator saves an override for a lot, **Then** that lot's cache entry is invalidated and fresh data is fetched on next load.
3. **Given** cached lot data older than 10 minutes, **When** the operator requests it, **Then** the stale cache is ignored and fresh data is fetched.
4. **Given** the operator changes pages within the same event, **When** the new page loads, **Then** the catalog data (embedded lot list) is served from cache — only uncached lots require API calls.

---

### US4: Catalog Data Caching (P1)

As an operator, I want catalog/event metadata to be cached so that page changes within an event don't re-fetch the catalog.

**Acceptance Scenarios:**
1. **Given** an event was loaded, **When** the operator changes to page 2, **Then** the catalog data (lot list, event metadata) is served from cache.
2. **Given** cached catalog data, **When** the operator navigates back to the event, **Then** the catalog data is served from cache within TTL.

---

### Edge Cases

- What if the ABConnect API token expires mid-concurrent-fetch? Each thread creates its own API instance reading the same session token; if the token expires, threads will fail and the error panel renders.
- What if the operator rapidly clicks multiple events? HTMX `hx-sync="this:replace"` on `#panel-main` cancels in-flight requests, preventing stale data display.
- What if all concurrent lot fetches fail? The existing error panel ("Could not load lots") renders with retry button.
- What if the cache grows too large? LocMemCache has a configurable `MAX_ENTRIES` default of 300; sufficient for typical session scope.

## Requirements

### Functional Requirements

- **FR-001**: HTMX loading indicators MUST display correctly for all panel transitions (seller→events, event→lots, pagination).
- **FR-002**: Lot fetching MUST use concurrent execution (ThreadPoolExecutor) with a configurable max-workers limit.
- **FR-003**: Individual lot fetch failures during concurrent execution MUST be logged and skipped, not abort the entire page.
- **FR-004**: Lot data MUST be cached in Django's cache framework with a configurable TTL (default 10 minutes).
- **FR-005**: Catalog (event) data MUST be cached with a configurable TTL (default 10 minutes).
- **FR-006**: Saving a lot override MUST invalidate that lot's cache entry.
- **FR-007**: Cache MUST use Django's LocMemCache backend (no new infrastructure dependencies).
- **FR-008**: Concurrent fetch worker count MUST be configurable via Django settings (default: 10).

### Non-Functional Requirements

- Event selection with 25 lots MUST complete in under 3 seconds (down from 13+).
- Cached page loads MUST complete in under 500ms.
- No new Python package dependencies (threading and Django cache are stdlib/built-in).
- No changes to ABConnectTools package.
- Must not break existing auto-save, lot detail modal, or override flows.

## Out of Scope

- Streaming/progressive lot loading (skeleton rows that fill in)
- Background prefetching of adjacent pages
- Persistent cache (Redis, memcached) — LocMemCache resets on gunicorn restart, which is acceptable
- ABConnect API batch endpoint (not available)
- Connection pooling in ABConnectTools

## Success Criteria

- **SC-001**: Loading spinner visible within 100ms of event click
- **SC-002**: 25-lot event loads in < 3 seconds (first visit)
- **SC-003**: Same event re-visit or page change loads in < 500ms (cached)
- **SC-004**: Lot override save correctly invalidates cache (fresh data on next load)

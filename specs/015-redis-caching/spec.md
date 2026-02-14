# Feature Specification: Redis Caching for Sellers and Catalogs

**Feature Branch**: `015-redis-caching`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "add redis to our project. expect local on normal port. use cat_ to avoid collisions with other projects. always cache all sellers. always cache all future catalogs. we will consider caching items in a future fr."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cached Seller List (Priority: P1)

When a staff member opens the application or navigates the sellers panel, the full list of sellers loads from a local cache instead of making a remote API call every time. The first request after application start (or after cache expiry) fetches sellers from the upstream API and stores them in cache. All subsequent requests serve sellers from cache until the cache entry expires.

**Why this priority**: Sellers change infrequently (new sellers are onboarded rarely) but the seller list is loaded on every application session and every panel navigation. Caching sellers eliminates the most repetitive API call and delivers the biggest perceived speed improvement.

**Independent Test**: Open the sellers panel twice in quick succession — the second load should be near-instant. Verify via logs or monitoring that only one upstream API call was made.

**Acceptance Scenarios**:

1. **Given** the cache is empty (cold start), **When** a user opens the sellers panel, **Then** the system fetches all sellers from the upstream API, stores them in cache with the `cat_` key prefix, and displays them normally.
2. **Given** sellers are already cached, **When** a user opens the sellers panel, **Then** sellers are served from cache with no upstream API call.
3. **Given** sellers are cached, **When** the cache entry expires, **Then** the next request fetches fresh data from the upstream API and re-populates the cache.

---

### User Story 2 - Cached Catalog (Event) List (Priority: P1)

When a staff member clicks a seller to view their events, the catalog list for future events loads from cache when available. Only catalogs with a start date in the future (or today) are cached. The first request fetches from the API and caches; subsequent requests for the same seller's future catalogs are served from cache.

**Why this priority**: Equal priority to sellers — catalog lists are loaded on every seller click and event navigation. Caching future catalogs eliminates the second-most-frequent API call pattern. Past catalogs are excluded because they are rarely accessed and would bloat cache unnecessarily.

**Independent Test**: Click a seller, observe events load. Click the same seller again — events load faster from cache. Verify only one upstream API call was made for catalogs.

**Acceptance Scenarios**:

1. **Given** no cached catalogs for a seller, **When** a user clicks a seller, **Then** the system fetches catalogs from the upstream API, caches the future catalogs with the `cat_` key prefix, and displays them.
2. **Given** future catalogs for a seller are cached, **When** the user clicks that seller again, **Then** catalogs are served from cache with no upstream API call.
3. **Given** catalogs are cached, **When** the cache entry expires, **Then** the next request fetches fresh catalog data and re-populates the cache.

---

### User Story 3 - Graceful Cache Unavailability (Priority: P2)

If the cache service is unavailable (down, unreachable, connection refused), the application continues to function normally by falling back to direct upstream API calls. No errors are shown to users; the experience degrades only in speed, not in functionality.

**Why this priority**: The cache is a performance optimization, not a data source. The system must never fail because the cache is down. This is lower priority because it's a resilience concern, not a primary user-facing feature.

**Independent Test**: Stop the cache service, then use the application — all panels load correctly (just slower). Restart the cache service — caching resumes automatically.

**Acceptance Scenarios**:

1. **Given** the cache service is not running, **When** a user opens the sellers panel, **Then** sellers are fetched directly from the upstream API and displayed normally.
2. **Given** the cache service goes down mid-session, **When** a user navigates panels, **Then** all data loads from upstream API without errors or visible degradation.
3. **Given** the cache service comes back online after downtime, **When** a user makes the next request, **Then** the system resumes caching without requiring a restart.

---

### Edge Cases

- What happens when the upstream API returns an error? The error propagates as it does today; no stale cache is served (cache miss on error).
- What happens when the seller list changes upstream (new seller added)? The cached seller list becomes stale until cache expiry, then refreshes automatically.
- What happens when a catalog transitions from future to past? It remains in cache until expiry; on next refresh, only future catalogs are re-cached.
- What happens when two concurrent requests hit an empty cache simultaneously? Both may fetch from the API; the second write simply overwrites the first with identical data (no thundering herd protection needed at this scale).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST cache all sellers as a single cache entry, refreshed on expiry.
- **FR-002**: The system MUST cache all future catalogs (start date today or later), keyed per seller when fetched by seller, refreshed on expiry.
- **FR-003**: All cache keys MUST use the prefix `cat_` to avoid collisions with other projects sharing the same cache instance.
- **FR-004**: The cache service MUST be expected on `localhost` at the default port (6379) with no authentication required.
- **FR-005**: The system MUST fall back to direct upstream API calls when the cache service is unavailable, with no user-facing errors.
- **FR-006**: Lot/item caching is explicitly out of scope for this feature and MUST NOT be implemented.
- **FR-007**: Cache expiry times MUST be configurable but default to reasonable values (5 minutes for sellers, 5 minutes for catalogs).

### Key Entities

- **Cached Seller List**: The complete list of all sellers, stored as a single cache entry. Key format: `cat_sellers_all`.
- **Cached Catalog List**: Future catalogs for a given seller, stored per seller. Key format: `cat_catalogs_seller_{seller_id}`. Only catalogs with start date >= today are included.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Repeated seller panel loads complete at least 3x faster than uncached loads when cache is warm.
- **SC-002**: Repeated catalog list loads for the same seller complete at least 3x faster than uncached loads when cache is warm.
- **SC-003**: The application functions identically (all panels load, no errors) when the cache service is unavailable.
- **SC-004**: Zero upstream API calls are made for sellers or catalogs when serving from a warm cache within the expiry window.

## Assumptions

- The cache service is running locally on the default port (6379) in all environments (development and production).
- No authentication or TLS is needed for the cache connection.
- The seller list is small enough (hundreds, not millions) to store as a single cache entry.
- The catalog list per seller is small enough to store as a single cache entry.
- Cache expiry (time-based eviction) is sufficient; no manual invalidation is needed for this iteration.
- Other projects may share the same cache instance, hence the `cat_` prefix requirement.

## Scope Boundaries

**In scope**:
- Cache integration and configuration
- Seller list caching
- Future catalog list caching
- Graceful fallback when cache is unavailable
- `cat_` key prefix for all cache keys

**Out of scope**:
- Lot/item caching (deferred to a future feature request)
- Cache invalidation triggers (manual purge, webhook-based invalidation)
- Cache authentication or TLS
- Cache metrics/monitoring dashboard
- Distributed or multi-node cache setup

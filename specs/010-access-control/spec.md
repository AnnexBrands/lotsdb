# Spec: Access Control

**Feature**: 010-access-control | **Status**: Draft | **Date**: 2026-02-13

## Overview

Add an authorization layer to LotsDB so that access to sellers, events, and lots can be controlled per user. Phase 1 implements a simple `is_staff` gate: staff users see everything, non-staff users see nothing. The architecture anticipates Phase 2 where a remote API returns per-user seller and event access sets, and visibility is the intersection of those sets.

Currently all ABConnect-authenticated users have identical, unrestricted access. This feature introduces Django User model bridging (so `request.user.is_staff` is available), an authorization service abstraction, and view-level enforcement.

## User Stories

### US1: Staff Full Access (P1)

As a staff user, I want to log in and see all sellers, events, and lots exactly as I do today, so that my workflow is unaffected by the new access control layer.

**Why this priority**: Staff users are the primary operators today. Their experience must not regress.

**Independent Test**: Log in as a user whose Django User has `is_staff=True`. All existing views, panels, and actions (browse, search, override, import) work identically to the current behavior.

**Acceptance Scenarios:**
1. **Given** a user with `is_staff=True`, **When** they log in and browse sellers, **Then** all sellers are visible (same as today).
2. **Given** a staff user viewing events or lots, **When** they navigate, filter, search, or save overrides, **Then** all operations succeed unchanged.
3. **Given** a staff user, **When** they access any URL directly (deep link, panel endpoint), **Then** access is granted.

---

### US2: Django User Bridging (P1)

As the system, when an ABConnect user logs in, a corresponding Django User record must be created or retrieved so that Django's `request.user` and `is_staff` flag are available throughout the request lifecycle.

**Why this priority**: Foundation for all access checks. Without a Django User, `is_staff` has no home.

**Independent Test**: Log in via ABConnect. Verify `request.user.is_authenticated` is `True` and `request.user.username` matches the ABConnect username. Verify a `User` row exists in the database.

**Acceptance Scenarios:**
1. **Given** a new ABConnect username, **When** the user logs in for the first time, **Then** a Django User is created with `username=abc_username` and `is_staff=True` (default for initial rollout).
2. **Given** an existing Django User, **When** the same ABConnect user logs in again, **Then** the existing User is retrieved (no duplicate).
3. **Given** a logged-in user, **When** any view accesses `request.user`, **Then** it returns the bridged Django User (not AnonymousUser).

---

### US3: Non-Staff Denial (P2)

As a non-staff user, I am shown a clear "no access" message after login, so I understand why I cannot use the application and whom to contact.

**Why this priority**: Phase 1 only grants access to staff. Non-staff users need a graceful experience, not a cryptic error.

**Independent Test**: Set `is_staff=False` on a Django User. Log in. Verify all data endpoints return a 403 page or redirect to a "no access" view.

**Acceptance Scenarios:**
1. **Given** a user with `is_staff=False`, **When** they log in, **Then** they are redirected to a "no access" page explaining they lack permission.
2. **Given** a non-staff user on the "no access" page, **When** they attempt to access any data URL directly, **Then** they receive a 403 response.
3. **Given** a non-staff user, **When** they click "Logout", **Then** they are logged out normally.

---

### US4: Authorization Service Abstraction (P1)

As a developer, I want a single authorization module that all views call to check access, so that Phase 2 can swap the policy implementation without touching views.

**Why this priority**: Architectural prerequisite. Without this, access checks would be scattered and hard to evolve.

**Independent Test**: Unit test the authorization service: given a staff user, all checks return True. Given a non-staff user, all checks return False. Service is mockable for view tests.

**Acceptance Scenarios:**
1. **Given** the authorization module, **When** called with a staff user, **Then** `can_access_seller`, `can_access_event`, `can_access_lot` all return `True`.
2. **Given** a non-staff user, **When** the authorization module is called, **Then** all access checks return `False`.
3. **Given** a future Phase 2, **When** a new policy class is implemented, **Then** it can be registered without modifying any view code.

---

### Edge Cases

- What happens if ABConnect login succeeds but Django User creation fails? The login should fail with an error; the user should not get a half-authenticated session.
- What happens if an admin demotes a currently logged-in user from staff to non-staff? On next request, middleware should detect the change and enforce denial.
- What happens to existing sessions after deployment? Existing sessions have no Django User. The middleware should handle this gracefully (re-bridge on next request or force re-login).
- What happens if the ABConnect API is down but the user has a valid Django session? The user can still see the "no access" / navigation chrome, but data views will fail via the existing CatalogAPIErrorMiddleware.

## Requirements

### Functional Requirements

- **FR-001**: On ABConnect login, the system MUST create or retrieve a Django `User` with `username` matching the ABConnect username.
- **FR-002**: New Django Users MUST default to `is_staff=True` during the Phase 1 rollout.
- **FR-003**: `request.user` MUST be a fully authenticated Django User on all authenticated requests.
- **FR-004**: An authorization service MUST provide `can_access_seller(user, seller_id)`, `can_access_event(user, event_id)`, and `is_authorized(user)` methods.
- **FR-005**: Phase 1 authorization policy: `is_staff=True` grants full access; `is_staff=False` denies all data access.
- **FR-006**: Non-staff users MUST see a "no access" page (not a blank or broken page).
- **FR-007**: Authorization checks MUST be enforced in middleware (for broad denial) and in views (for future per-resource filtering).
- **FR-008**: The authorization module MUST be designed so that a Phase 2 API-based policy can be added without modifying views.
- **FR-009**: Logout MUST work for all users regardless of staff status.
- **FR-010**: All existing tests MUST continue to pass with the new auth layer (fixtures may need updating).

### Key Entities

- **User (Django)**: Bridged from ABConnect login. Key fields: `username`, `is_staff`. No additional model fields in Phase 1.
- **AccessPolicy**: Abstraction representing the authorization policy. Phase 1: `StaffAccessPolicy`. Phase 2 (future): `APIAccessPolicy` with seller/event sets.

## Non-Functional Requirements

- No new Python dependencies (Django's auth framework is already included)
- Changes confined to: `services.py`, `middleware.py`, `settings.py`, new `authorization.py`, view files, one new template
- Must not degrade login performance noticeably (Django User lookup is local SQLite)
- Session handling must remain compatible with existing session backend

## Out of Scope

- Phase 2 API-based access (seller/event set intersection) - future feature
- User management admin UI
- Permission groups or granular per-object permissions
- ABConnect role mapping (beyond is_staff)

## Future Phase 2 Notes (informational, not implemented)

Phase 2 will introduce:
- An API endpoint called with a user ID that returns `{ sellers: [id, ...], events: [id, ...] }`
- Non-staff users filtered to only see sellers in their allowed set AND events in their allowed set
- The authorization service will cache the API response and filter at the view level
- Views already calling the authorization service will get filtering for free via the new policy

## Success Criteria

- **SC-001**: Staff users experience zero behavioral change from the current application
- **SC-002**: Non-staff users see a clear "no access" page, not errors or blank screens
- **SC-003**: All existing tests pass (with necessary fixture updates)
- **SC-004**: Authorization service has full unit test coverage for both staff and non-staff paths
- **SC-005**: A developer can implement Phase 2 by adding a new policy class without modifying any view

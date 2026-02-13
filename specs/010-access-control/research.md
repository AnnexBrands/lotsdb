# Research: 010-access-control

## R1: Django User Bridging Strategy

**Decision**: Use `User.objects.get_or_create(username=abc_username)` during login, then call `django.contrib.auth.login(request, user)` to attach the Django User to the session.

**Rationale**:
- Django's auth framework is already in INSTALLED_APPS and middleware stack
- `AuthenticationMiddleware` already runs and sets `request.user` (currently AnonymousUser)
- Calling `django.contrib.auth.login()` populates `request.session[SESSION_KEY]` so `request.user` is set on subsequent requests
- No custom auth backend needed — we're not using Django's `authenticate()` pathway, just bridging after ABConnect validates credentials
- `get_or_create` is idempotent and handles both first-login and repeat-login cases

**Alternatives considered**:
- Custom authentication backend (`AUTHENTICATION_BACKENDS`): Overcomplicates things since ABConnect handles credential validation, not Django. We just need to bridge the result.
- Session-only approach (store is_staff in session, no Django User): Loses Django's built-in `request.user`, permission decorators, and admin compatibility. Not extensible for Phase 2.

## R2: Authorization Service Design Pattern

**Decision**: Single module `catalog/authorization.py` with module-level functions backed by a policy object. Policy is selected in settings (`ACCESS_POLICY = "staff"`) and resolved at import time.

**Rationale**:
- Module-level functions (`is_authorized(user)`, `can_access_seller(user, seller_id)`) keep call sites simple
- Policy object pattern allows swapping Phase 2 implementation via settings
- No need for a full class hierarchy — a simple protocol/duck-typing approach suffices
- Phase 1 policy is trivially `return user.is_staff` for all checks

**Alternatives considered**:
- Decorator-based (@requires_staff): Too rigid. Per-resource filtering in Phase 2 needs access to the resource ID, which decorators can't easily provide.
- Django permission framework (Permission, Group): Designed for Django model-level permissions, not for filtering ABConnect API resources. Would require syncing ABConnect entities to Django models.
- Middleware-only: Can handle broad denial but can't do per-resource filtering needed in Phase 2.

## R3: Enforcement Points

**Decision**: Two layers of enforcement:
1. **Middleware**: `LoginRequiredMiddleware` extended to also check `is_authorized(request.user)`. Non-authorized users redirected to "no access" page. This provides blanket denial for non-staff in Phase 1.
2. **Views**: Each view that fetches sellers/events calls authorization service to filter results. In Phase 1 this is a no-op for staff (returns all). In Phase 2, this is where seller/event filtering happens.

**Rationale**:
- Middleware catches all URLs — no risk of forgetting a view
- View-level filtering prepares the call sites for Phase 2 granularity
- Defense in depth: even if a view forgets to filter, middleware blocks non-staff

**Alternatives considered**:
- View-only enforcement: Risk of forgetting a view, especially HTMX panel endpoints.
- Middleware-only enforcement: Can't do per-resource filtering for Phase 2 without moving logic into middleware, which is the wrong layer.

## R4: Existing Session Compatibility

**Decision**: After deployment, existing sessions will have `abc_token` but no Django User attached. The middleware should detect this (check `request.user.is_authenticated`) and force a re-bridge: look up the Django User by `abc_username` from the session, call `django.contrib.auth.login()`. If no `abc_username` in session (shouldn't happen), flush session and redirect to login.

**Rationale**:
- Avoids forcing all users to re-login on deployment
- `abc_username` is already stored in session by the existing login flow
- One-time re-bridge per existing session, then Django session has the user attached

**Alternatives considered**:
- Force re-login (flush all sessions on deploy): Disruptive to operators mid-shift.
- Ignore (let existing sessions fail): Would cause confusing errors.

## R5: Default is_staff Value

**Decision**: New Django Users created during login default to `is_staff=True`. This preserves current behavior (all authenticated users have full access).

**Rationale**:
- Currently all ABConnect users can do everything. Setting `is_staff=True` by default means zero behavior change on deployment.
- Admins can later set specific users to `is_staff=False` via Django admin or management command.
- Phase 2 will revisit defaults (possibly `is_staff=False` with API-based access).

**Alternatives considered**:
- Default to `is_staff=False`: Would lock out all existing users on deployment.
- Configurable default via settings: Over-engineering for Phase 1.

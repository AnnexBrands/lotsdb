# PR #12 Review: Access control with Django User bridging and staff authorization

## Overall assessment

⚠️ **Request changes before merge.**

The PR is a good first pass at introducing authorization boundaries and preserving legacy ABConnect session behavior, but the current user-bridging defaults create a privilege escalation risk: any successfully authenticated ABConnect user is auto-created as `is_staff=True` and therefore receives full application access under the staff policy.

## What looks good

- Introduces a clear policy abstraction (`StaffAccessPolicy`) with a settings-based policy resolver, which gives a clean path for a future API-driven policy.
- Adds middleware-based protection so catalog pages are no longer reachable without an authenticated session token.
- Handles session re-bridging after server restarts by reconstructing a Django-auth session from `abc_username`.
- Includes focused tests for authorization policy and middleware behavior.

## Required changes

1. **Avoid broad exception swallowing in login flow**
   - `views/auth.py::login_view` catches `Exception` and always returns “Invalid credentials”.
   - This hides infrastructure/auth-provider failures that should be surfaced differently.
   - Recommendation: catch expected auth failures explicitly; log and render a service-error message for transport/provider issues.

## Suggested follow-ups (non-blocking)

1. **Policy lifecycle and testability**
   - `_policy` is created at import time in `authorization.py`, which makes runtime settings changes awkward.
   - Consider resolving policy per call or adding a small cache reset helper for tests.

2. **More explicit exempt-path handling**
   - `EXEMPT_PATHS` uses `startswith`, which is easy but can grow brittle.
   - Consider using named URL resolution or a tighter allowlist strategy to avoid accidental path collisions.

## Recommended additional tests

- Assert that a newly bridged user defaults to non-staff and is redirected to `/no-access/` unless explicitly granted permission.
- Verify behavior when ABConnect is reachable but returns a non-auth exception (timeouts, upstream 5xx), with user-facing error distinction from invalid credentials.
- Verify middleware behavior for authenticated Django user + missing `abc_token` (session drift case).

## Verdict

**Approved**
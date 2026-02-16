# Tasks: Access Control

**Input**: Design documents from `/specs/010-access-control/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/authorization.md

**Tests**: Included — spec.md SC-003/SC-004 require test coverage for authorization service and existing test compatibility.

**Organization**: Tasks grouped by user story. US2 (Django User Bridging) and US4 (Authorization Service) are foundational P1 prerequisites. US1 (Staff Full Access) validates end-to-end. US3 (Non-Staff Denial) is P2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Configuration changes and shared test infrastructure

- [X] T001 Add `ACCESS_POLICY = "staff"` setting in src/config/settings.py
- [X] T002 [P] Add `AUTHENTICATION_BACKENDS` setting in src/config/settings.py to include `django.contrib.auth.backends.ModelBackend` (required for `django.contrib.auth.login()` without `authenticate()`)
- [X] T003 [P] Add Django User fixtures to tests/conftest.py: `staff_user` fixture (User with `is_staff=True`, unusable password) and `non_staff_user` fixture (User with `is_staff=False`); update `auth_session` to include `_auth_user_id` for bridged sessions

---

## Phase 2: Foundational — US4 Authorization Service (Priority: P1) + US2 Django User Bridging (Priority: P1)

**Purpose**: Core authorization module and login bridge — MUST be complete before other stories can be validated

**US4 Goal**: Single `catalog/authorization.py` module with `is_authorized()`, `can_access_seller()`, `can_access_event()`, `filter_sellers()`, `filter_events()` functions backed by a settings-selectable policy

**US2 Goal**: On ABConnect login, create/retrieve Django User and call `django.contrib.auth.login()` so `request.user` is a real User on all subsequent requests

### Authorization Service (US4)

- [X] T004 [P] [US4] Create src/catalog/authorization.py with `StaffAccessPolicy` class implementing `is_authorized(user)`, `can_access_seller(user, seller_id)`, `can_access_event(user, event_id)`, `filter_sellers(user, sellers)`, `filter_events(user, events)` — all return `user.is_staff` / full list for staff / empty for non-staff. Module-level functions delegate to policy instance resolved from `settings.ACCESS_POLICY`
- [X] T005 [P] [US4] Create tests/unit/test_authorization.py — test all 5 public functions with staff user (all True / full lists) and non-staff user (all False / empty lists); test that policy is resolved from settings

### Login Bridge (US2)

- [X] T006 [P] [US2] Modify `login()` in src/catalog/services.py — after `ABConnectAPI(request=request, username=username, password=password)`, add `User.objects.get_or_create(username=username, defaults={"is_staff": True})`, call `user.set_unusable_password()` + `user.save()` on creation, then `django.contrib.auth.login(request, user, backend="django.contrib.auth.backends.ModelBackend")`
- [X] T007 [P] [US2] Create tests/unit/test_login_bridge.py — test first login creates Django User with `is_staff=True` and unusable password; test repeat login retrieves existing User (no duplicate); test `request.user` is set after login; test ABConnect failure does not create a half-bridged session

**Checkpoint**: Authorization service and login bridge complete. `request.user` is a real Django User after login. Authorization functions available for middleware and views.

---

## Phase 3: US1 — Staff Full Access (Priority: P1) 🎯 MVP

**Goal**: Staff users experience zero behavioral change — all existing views, panels, and actions work identically

**Independent Test**: Log in as a user (all default to `is_staff=True`). Browse sellers, events, lots. Search, override, import. Everything works exactly as before.

### Middleware Enforcement

- [X] T008 [US1] Modify `LoginRequiredMiddleware` in src/catalog/middleware.py — add `/no-access/` to `EXEMPT_PATHS`; after `is_authenticated` check, add session re-bridge logic: if `abc_token` exists but `request.user` is `AnonymousUser`, look up User by `request.session["abc_username"]` via `get_or_create`, call `django.contrib.auth.login()`; then call `authorization.is_authorized(request.user)` — if False, redirect to `/no-access/`
- [X] T009 [US1] Create tests/integration/test_middleware_auth.py — test staff user passes through middleware to views unchanged; test re-bridge of legacy session (abc_token + abc_username but no Django User in session) creates User and continues; test non-staff user redirected to `/no-access/`; test unauthenticated user still redirected to `/login/`

### Existing Test Compatibility

- [X] T010 [US1] Update existing tests in tests/contract/test_panels.py and tests/contract/test_upload.py — `_make_get` and `_make_post` helpers must set `request.user` to a staff Django User (use `staff_user` fixture or inline `User` creation) so middleware authorization checks pass in any future integration-level test runs; verify all existing tests pass with `.venv/bin/python -m pytest tests/ -v`

**Checkpoint**: Staff users have identical experience. All existing tests pass. Login creates Django User. Legacy sessions re-bridge transparently.

---

## Phase 4: US3 — Non-Staff Denial (Priority: P2)

**Goal**: Non-staff users see a clear "no access" page after login, with working logout

**Independent Test**: Set `is_staff=False` on a Django User. Refresh page → redirected to `/no-access/`. Try direct URL → redirected. Logout works.

### No Access View and Template

- [X] T011 [P] [US3] Create src/catalog/templates/catalog/auth/no_access.html — extends `base.html`, shows "You do not have access to this application. Contact an administrator." with a Logout button (POST to `/logout/`)
- [X] T012 [P] [US3] Add `no_access` view in src/catalog/views/auth.py — renders `catalog/auth/no_access.html` with status 403; requires authentication (abc_token) but not authorization
- [X] T013 [US3] Add URL pattern `path("no-access/", views.no_access, name="no_access")` in src/catalog/urls.py
- [X] T014 [US3] Add non-staff denial tests to tests/integration/test_middleware_auth.py — test non-staff user GET to `/panels/sellers/` redirects to `/no-access/`; test non-staff user GET to `/no-access/` returns 403 with template content; test non-staff user POST to `/logout/` succeeds and redirects to `/login/`

**Checkpoint**: Non-staff users see clear "no access" page. Logout works for all users. All tests pass.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [X] T015 Run full test suite with `.venv/bin/python -m pytest tests/ -v` and fix any failures
- [X] T016 Run quickstart.md manual verification steps (login → verify User created → browse as staff → demote → verify no-access → re-promote)
- [X] T017 Verify `ruff check src/` passes with no new warnings

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (settings + fixtures) — BLOCKS all user stories
- **US1 Staff Full Access (Phase 3)**: Depends on Phase 2 (authorization module + login bridge)
- **US3 Non-Staff Denial (Phase 4)**: Depends on Phase 3 (middleware enforcement already wired)
- **Polish (Phase 5)**: Depends on all phases complete

### User Story Dependencies

- **US2 (Login Bridge)** + **US4 (Authorization Service)**: Co-foundational, can be implemented in parallel (T004-T007 all marked [P])
- **US1 (Staff Full Access)**: Depends on US2 + US4 — validates the integration
- **US3 (Non-Staff Denial)**: Depends on US1 middleware work (T008) — adds the denial path

### Within Each Phase

- Tests and implementation marked [P] can run in parallel
- Sequential tasks depend on prior tasks in the same phase

### Parallel Opportunities

- T004 + T005 + T006 + T007 can all run in parallel (different files)
- T011 + T012 can run in parallel (template + view, different files)
- T001 + T002 + T003 can run in parallel (different files, though T001/T002 share settings.py — combine if needed)

---

## Parallel Example: Phase 2 (Foundational)

```bash
# All four tasks target different files — run in parallel:
Task: "Create authorization.py" (T004) → src/catalog/authorization.py
Task: "Create test_authorization.py" (T005) → tests/unit/test_authorization.py
Task: "Modify services.py login" (T006) → src/catalog/services.py
Task: "Create test_login_bridge.py" (T007) → tests/unit/test_login_bridge.py
```

---

## Implementation Strategy

### MVP First (US2 + US4 + US1)

1. Complete Phase 1: Setup (settings + fixtures)
2. Complete Phase 2: Authorization service + login bridge
3. Complete Phase 3: Middleware enforcement + existing test compat
4. **STOP and VALIDATE**: Staff login works identically to today
5. Deploy — zero visible change to operators

### Incremental Delivery

1. Setup + Foundational → Authorization framework ready
2. Add US1 (Staff Full Access) → Test → Deploy (MVP — operators unaffected)
3. Add US3 (Non-Staff Denial) → Test → Deploy (non-staff now handled gracefully)
4. Polish → Final validation

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 17 |
| Phase 1 (Setup) | 3 |
| Phase 2 (Foundational: US2 + US4) | 4 |
| Phase 3 (US1: Staff Full Access) | 3 |
| Phase 4 (US3: Non-Staff Denial) | 4 |
| Phase 5 (Polish) | 3 |
| Parallel opportunities | T001-T003, T004-T007, T011-T012 |
| MVP scope | Phases 1-3 (US2 + US4 + US1 = 10 tasks) |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 and US4 are co-foundational and implemented together in Phase 2
- Commit after each phase or logical task group
- Stop at any checkpoint to validate independently

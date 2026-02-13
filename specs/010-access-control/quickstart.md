# Quickstart: 010-access-control

## Prerequisites

- LotsDB running locally (`.venv/bin/python src/manage.py runserver`)
- Valid ABConnect credentials
- Database migrated (`src/manage.py migrate`)

## Verify Django User Bridging

1. **Clear existing session** (optional, for clean test):
   ```bash
   .venv/bin/python src/manage.py shell -c "from django.contrib.sessions.models import Session; Session.objects.all().delete()"
   ```

2. **Log in** via the browser at `http://localhost:8000/login/`

3. **Verify Django User was created**:
   ```bash
   .venv/bin/python src/manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.all().values_list('username', 'is_staff'))"
   ```
   Expected: `[('your_abc_username', True)]`

4. **Verify request.user is set** — browse any page. No errors = Django User is attached.

## Verify Staff Access

1. Log in as any user (all new users default to `is_staff=True`)
2. Browse sellers, events, lots — all should work exactly as before
3. Search, override, import — all should work

## Verify Non-Staff Denial

1. **Demote a user**:
   ```bash
   .venv/bin/python src/manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='your_abc_username'); u.is_staff = False; u.save()"
   ```

2. **Refresh the page** — you should be redirected to `/no-access/`

3. **Try direct URL access** (e.g., `/panels/sellers/`) — should redirect to `/no-access/`

4. **Verify logout works**: Click Logout from the no-access page

5. **Re-promote** for continued testing:
   ```bash
   .venv/bin/python src/manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='your_abc_username'); u.is_staff = True; u.save()"
   ```

## Run Tests

```bash
.venv/bin/python -m pytest tests/ -v
```

All tests should pass. New tests cover:
- `tests/unit/test_authorization.py` — authorization service unit tests
- `tests/unit/test_login_bridge.py` — Django User creation on login
- `tests/integration/test_middleware_auth.py` — middleware enforcement

## Files Changed

| File | Change |
|------|--------|
| `src/catalog/authorization.py` | New — authorization service module |
| `src/catalog/services.py` | Modified — login bridges to Django User |
| `src/catalog/middleware.py` | Modified — authorization check added |
| `src/catalog/urls.py` | Modified — added `/no-access/` route |
| `src/catalog/views/auth.py` | Modified — added `no_access` view |
| `src/catalog/templates/catalog/auth/no_access.html` | New — no access page |
| `src/config/settings.py` | Modified — `ACCESS_POLICY` setting |
| `tests/unit/test_authorization.py` | New — authorization unit tests |
| `tests/unit/test_login_bridge.py` | New — login bridge tests |
| `tests/integration/test_middleware_auth.py` | New — middleware auth tests |
| `tests/conftest.py` | Modified — fixtures for Django User |

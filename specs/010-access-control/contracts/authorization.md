# Contract: Authorization Service

## Module: `catalog/authorization.py`

### Public API

```python
def is_authorized(user: User) -> bool:
    """Check if user has any access to the application.

    Phase 1: Returns user.is_staff
    Phase 2: Returns True if user has any seller/event access via API
    """

def can_access_seller(user: User, seller_id: int) -> bool:
    """Check if user can view a specific seller.

    Phase 1: Returns user.is_staff (staff see all sellers)
    Phase 2: Returns seller_id in user's allowed seller set
    """

def can_access_event(user: User, event_id: int) -> bool:
    """Check if user can view a specific event (catalog).

    Phase 1: Returns user.is_staff (staff see all events)
    Phase 2: Returns event_id in user's allowed event set
    """

def filter_sellers(user: User, sellers: list) -> list:
    """Filter a list of seller objects to only those the user can access.

    Phase 1: Returns all sellers if staff, empty list if not
    Phase 2: Filters by user's allowed seller set
    """

def filter_events(user: User, events: list) -> list:
    """Filter a list of event objects to only those the user can access.

    Phase 1: Returns all events if staff, empty list if not
    Phase 2: Filters by user's allowed event set
    """
```

### Settings

```python
# config/settings.py
ACCESS_POLICY = "staff"  # Phase 1. Phase 2: "api"
```

### Behavior Contract

| User State | `is_authorized` | `can_access_seller(*, id)` | `can_access_event(*, id)` | `filter_sellers` | `filter_events` |
|------------|-----------------|---------------------------|--------------------------|-----------------|----------------|
| `is_staff=True` | `True` | `True` | `True` | all items | all items |
| `is_staff=False` | `False` | `False` | `False` | `[]` | `[]` |

### Error Handling

- Functions never raise exceptions for authorization decisions (return bool or filtered list)
- Functions assume `user` is an authenticated Django User (not AnonymousUser)
- Caller is responsible for handling False/empty results (redirect, 403, etc.)

---

## Contract: Login Bridge

### Modified: `catalog/services.py:login()`

```python
def login(request, username, password):
    """Authenticate via ABConnect, then bridge to Django User.

    1. Validate credentials via ABConnectAPI (existing)
    2. get_or_create Django User with username
    3. Call django.contrib.auth.login(request, user)

    Raises: ABConnectError if credentials invalid (existing behavior)
    Side effects:
      - Sets request.session["abc_token"] (existing)
      - Sets request.session["abc_username"] (existing)
      - Sets request.user to Django User (new)
      - Creates User row in database if first login (new)
    """
```

### Post-conditions

- `request.user.is_authenticated == True`
- `request.user.username == username`
- `User.objects.filter(username=username).exists() == True`

---

## Contract: Middleware Authorization

### Modified: `catalog/middleware.py:LoginRequiredMiddleware`

```python
class LoginRequiredMiddleware:
    """Extended to check authorization after authentication.

    Request flow:
    1. Exempt paths (/login/, /static/, /no-access/) → pass through
    2. No abc_token → redirect to /login/
    3. request.user not authenticated → re-bridge Django User from session
    4. not is_authorized(request.user) → redirect to /no-access/
    5. Authorized → continue to view
    """
```

### New URL: `/no-access/`

```
GET /no-access/
Response: 403 status, renders no_access.html template
Template shows: "You do not have access to this application. Contact an administrator."
```

Exempt from authorization check (but requires authentication).

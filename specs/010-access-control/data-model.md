# Data Model: 010-access-control

## Entities

### Django User (existing model, no modifications)

Uses Django's built-in `django.contrib.auth.models.User`. No custom user model or extensions in Phase 1.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `username` | CharField(150) | ABConnect login username | Primary lookup key, set on `get_or_create` |
| `is_staff` | BooleanField | Default `True` in Phase 1 | Controls access: staff = full, non-staff = denied |
| `is_active` | BooleanField | Default `True` | Django built-in; not used for access control in Phase 1 |
| `password` | CharField | Set unusable | ABConnect handles auth; Django password is not used |

**Creation**: `User.objects.get_or_create(username=abc_username, defaults={"is_staff": True})`
**Password**: `user.set_unusable_password()` on creation (ABConnect handles authentication)

### Session Data (existing, modified)

| Key | Type | Source | Notes |
|-----|------|--------|-------|
| `abc_token` | str | ABConnect API | Existing — API auth token |
| `abc_username` | str | Login form | Existing — display name + User lookup key |
| `_auth_user_id` | int | `django.contrib.auth.login()` | New — Django User PK, set by `login()` |
| `_auth_user_backend` | str | `django.contrib.auth.login()` | New — auth backend path |
| `_auth_user_hash` | str | `django.contrib.auth.login()` | New — session verification hash |

### AccessPolicy (conceptual, not persisted)

Abstract interface for authorization decisions. Phase 1 has one implementation.

```
AccessPolicy:
  is_authorized(user) -> bool
  can_access_seller(user, seller_id) -> bool
  can_access_event(user, event_id) -> bool
```

#### StaffAccessPolicy (Phase 1)

```
StaffAccessPolicy:
  is_authorized(user) -> user.is_staff
  can_access_seller(user, seller_id) -> user.is_staff
  can_access_event(user, event_id) -> user.is_staff
```

#### APIAccessPolicy (Phase 2, not implemented)

```
APIAccessPolicy:
  _get_access(user_id) -> { sellers: [id, ...], events: [id, ...] }
  is_authorized(user) -> bool(self._get_access(user.id).sellers)
  can_access_seller(user, seller_id) -> seller_id in self._get_access(user.id).sellers
  can_access_event(user, event_id) -> event_id in self._get_access(user.id).events
```

## Relationships

```
ABConnect Login ──creates/retrieves──> Django User
Django User ──stored in──> Django Session (via django.contrib.auth.login)
Django User.is_staff ──evaluated by──> StaffAccessPolicy
StaffAccessPolicy ──consulted by──> Middleware (broad denial)
StaffAccessPolicy ──consulted by──> Views (per-resource filtering, Phase 2 ready)
```

## State Transitions

### User Lifecycle

```
[No User] ──first login──> [User created, is_staff=True]
[User exists] ──login──> [Session bridged, request.user set]
[User, is_staff=True] ──admin demotes──> [User, is_staff=False]
[User, is_staff=False] ──next request──> [Middleware redirects to no-access]
```

### Session Lifecycle (post-deployment compatibility)

```
[Legacy session: abc_token + abc_username, no Django User in session]
  ──middleware detects──> [Re-bridge: get_or_create User, call login()]
  ──next request──> [Normal session with Django User]
```

## Migration Impact

- `django.contrib.auth` migrations already exist (INSTALLED_APPS includes it)
- `auth_user` table may need initial `migrate` if never run (but sessions require it, so likely already present)
- No custom migrations for this feature

"""Authorization service for access control.

Phase 1: StaffAccessPolicy — is_staff grants full access.
Phase 2 (future): APIAccessPolicy — per-user seller/event sets from remote API.

Policy is selected via settings.ACCESS_POLICY and resolved at module load.
Views call module-level functions; the backing policy is transparent.
"""

from django.conf import settings


class StaffAccessPolicy:
    """Staff users get full access; non-staff get nothing."""

    def is_authorized(self, user):
        return user.is_staff

    def can_access_seller(self, user, seller_id):
        return user.is_staff

    def can_access_event(self, user, event_id):
        return user.is_staff

    def filter_sellers(self, user, sellers):
        return list(sellers) if user.is_staff else []

    def filter_events(self, user, events):
        return list(events) if user.is_staff else []


_POLICIES = {
    "staff": StaffAccessPolicy,
}


def _get_policy():
    policy_name = getattr(settings, "ACCESS_POLICY", "staff")
    cls = _POLICIES.get(policy_name, StaffAccessPolicy)
    return cls()


_policy = _get_policy()


def is_authorized(user):
    """Check if user has any access to the application."""
    return _policy.is_authorized(user)


def can_access_seller(user, seller_id):
    """Check if user can view a specific seller."""
    return _policy.can_access_seller(user, seller_id)


def can_access_event(user, event_id):
    """Check if user can view a specific event (catalog)."""
    return _policy.can_access_event(user, event_id)


def filter_sellers(user, sellers):
    """Filter a list of seller objects to only those the user can access."""
    return _policy.filter_sellers(user, sellers)


def filter_events(user, events):
    """Filter a list of event objects to only those the user can access."""
    return _policy.filter_events(user, events)

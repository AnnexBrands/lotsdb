"""Unit tests for catalog.authorization module."""

from types import SimpleNamespace

import pytest

from catalog.authorization import (
    StaffAccessPolicy,
    is_authorized,
    can_access_seller,
    can_access_event,
    filter_sellers,
    filter_events,
)


@pytest.fixture
def staff():
    return SimpleNamespace(is_staff=True)


@pytest.fixture
def non_staff():
    return SimpleNamespace(is_staff=False)


@pytest.fixture
def sellers():
    return [SimpleNamespace(id=1, name="A"), SimpleNamespace(id=2, name="B")]


@pytest.fixture
def events():
    return [SimpleNamespace(id=10, title="E1"), SimpleNamespace(id=20, title="E2")]


class TestStaffAccessPolicy:
    """Direct tests on the StaffAccessPolicy class."""

    def test_staff_is_authorized(self, staff):
        assert StaffAccessPolicy().is_authorized(staff) is True

    def test_non_staff_not_authorized(self, non_staff):
        assert StaffAccessPolicy().is_authorized(non_staff) is False

    def test_staff_can_access_seller(self, staff):
        assert StaffAccessPolicy().can_access_seller(staff, 1) is True

    def test_non_staff_cannot_access_seller(self, non_staff):
        assert StaffAccessPolicy().can_access_seller(non_staff, 1) is False

    def test_staff_can_access_event(self, staff):
        assert StaffAccessPolicy().can_access_event(staff, 10) is True

    def test_non_staff_cannot_access_event(self, non_staff):
        assert StaffAccessPolicy().can_access_event(non_staff, 10) is False

    def test_staff_filter_sellers_returns_all(self, staff, sellers):
        result = StaffAccessPolicy().filter_sellers(staff, sellers)
        assert len(result) == 2
        assert result[0].id == 1

    def test_non_staff_filter_sellers_returns_empty(self, non_staff, sellers):
        result = StaffAccessPolicy().filter_sellers(non_staff, sellers)
        assert result == []

    def test_staff_filter_events_returns_all(self, staff, events):
        result = StaffAccessPolicy().filter_events(staff, events)
        assert len(result) == 2

    def test_non_staff_filter_events_returns_empty(self, non_staff, events):
        result = StaffAccessPolicy().filter_events(non_staff, events)
        assert result == []


class TestModuleLevelFunctions:
    """Test module-level functions that delegate to the resolved policy."""

    def test_is_authorized_staff(self, staff):
        assert is_authorized(staff) is True

    def test_is_authorized_non_staff(self, non_staff):
        assert is_authorized(non_staff) is False

    def test_can_access_seller_staff(self, staff):
        assert can_access_seller(staff, 42) is True

    def test_can_access_seller_non_staff(self, non_staff):
        assert can_access_seller(non_staff, 42) is False

    def test_can_access_event_staff(self, staff):
        assert can_access_event(staff, 99) is True

    def test_can_access_event_non_staff(self, non_staff):
        assert can_access_event(non_staff, 99) is False

    def test_filter_sellers_staff(self, staff, sellers):
        assert len(filter_sellers(staff, sellers)) == 2

    def test_filter_sellers_non_staff(self, non_staff, sellers):
        assert filter_sellers(non_staff, sellers) == []

    def test_filter_events_staff(self, staff, events):
        assert len(filter_events(staff, events)) == 2

    def test_filter_events_non_staff(self, non_staff, events):
        assert filter_events(non_staff, events) == []

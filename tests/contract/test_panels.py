from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.test import RequestFactory

from catalog.views.panels import sellers_panel, seller_events_panel, event_lots_panel
from catalog.views.sellers import seller_list
from conftest import AUTH_SESSION


@pytest.fixture
def factory():
    return RequestFactory()


def _make_get(factory, path, params=None):
    request = factory.get(path, params or {})
    request.session = AUTH_SESSION.copy()
    return request


def _mock_seller(id=1, name="Test Seller", customer_display_id="S001", is_active=True):
    return SimpleNamespace(id=id, name=name, customer_display_id=customer_display_id, is_active=is_active)


def _mock_event(id=1, title="Test Event", customer_catalog_id="CAT001", agent="Agent A",
                start_date=None, end_date=None, is_completed=False, lots=None, sellers=None):
    return SimpleNamespace(
        id=id, title=title, customer_catalog_id=customer_catalog_id,
        agent=agent, start_date=start_date, end_date=end_date,
        is_completed=is_completed,
        lots=lots if lots is not None else [],
        sellers=sellers if sellers is not None else [],
    )


def _mock_lot(id=1, lot_number="L001", customer_item_id="ITEM001",
              description=None, notes=None, image_links=None):
    initial_data = SimpleNamespace(description=description, notes=notes)
    catalogs = [SimpleNamespace(catalog_id=1, lot_number=lot_number)]
    return SimpleNamespace(
        id=id, lot_number=lot_number, customer_item_id=customer_item_id,
        initial_data=initial_data, catalogs=catalogs,
        image_links=image_links if image_links is not None else [],
    )


def _mock_paginated(items, total_items=None, page_number=1, total_pages=1,
                    has_previous_page=False, has_next_page=False):
    return SimpleNamespace(
        items=items,
        total_items=total_items if total_items is not None else len(items),
        page_number=page_number,
        total_pages=total_pages,
        has_previous_page=has_previous_page,
        has_next_page=has_next_page,
    )


class TestSellersPanelContract:
    """Contract tests for GET /panels/sellers/ — HTML fragment endpoint."""

    @patch("catalog.views.panels.services.list_sellers")
    def test_returns_html_fragment_not_full_page(self, mock_list, factory):
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/")
        response = sellers_panel(request)

        content = response.content.decode()
        assert "<!DOCTYPE" not in content
        assert "<html" not in content
        assert response.status_code == 200

    @patch("catalog.views.panels.services.list_sellers")
    def test_contains_panel_list_structure(self, mock_list, factory):
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/")
        response = sellers_panel(request)

        content = response.content.decode()
        assert "panel-list" in content
        assert "panel-item" in content

    @patch("catalog.views.panels.services.list_sellers")
    def test_contains_htmx_attributes(self, mock_list, factory):
        mock_list.return_value = _mock_paginated([_mock_seller(id=42)])
        request = _make_get(factory, "/panels/sellers/")
        response = sellers_panel(request)

        content = response.content.decode()
        assert 'hx-get="/panels/sellers/42/events/"' in content
        assert 'hx-target="#panel-left2-content"' in content

    @patch("catalog.views.panels.services.list_sellers")
    def test_empty_state_when_no_sellers(self, mock_list, factory):
        mock_list.return_value = _mock_paginated([])
        request = _make_get(factory, "/panels/sellers/")
        response = sellers_panel(request)

        content = response.content.decode()
        assert "panel-empty" in content
        assert "No sellers found" in content


class TestSellerEventsPanelContract:
    """Contract tests for GET /panels/sellers/{id}/events/ — HTML fragment endpoint."""

    @patch("catalog.views.panels.services.list_sellers")
    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_returns_html_fragment(self, mock_seller, mock_catalogs, mock_list_sellers, factory):
        mock_seller.return_value = _mock_seller()
        mock_catalogs.return_value = _mock_paginated([_mock_event()])
        mock_list_sellers.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/1/events/")
        response = seller_events_panel(request, seller_id=1)

        content = response.content.decode()
        assert "<!DOCTYPE" not in content
        assert "<html" not in content
        assert response.status_code == 200

    @patch("catalog.views.panels.services.list_sellers")
    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_contains_panel_structure_and_htmx(self, mock_seller, mock_catalogs, mock_list_sellers, factory):
        mock_seller.return_value = _mock_seller()
        mock_catalogs.return_value = _mock_paginated([_mock_event(id=99)])
        mock_list_sellers.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/1/events/")
        response = seller_events_panel(request, seller_id=1)

        content = response.content.decode()
        assert "panel-list" in content
        assert "panel-item" in content
        assert 'hx-get="/panels/events/99/lots/"' in content
        assert 'hx-target="#panel-main-content"' in content

    @patch("catalog.views.panels.services.list_sellers")
    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_includes_oob_clear_for_main_panel(self, mock_seller, mock_catalogs, mock_list_sellers, factory):
        mock_seller.return_value = _mock_seller()
        mock_catalogs.return_value = _mock_paginated([_mock_event()])
        mock_list_sellers.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/1/events/")
        response = seller_events_panel(request, seller_id=1)

        content = response.content.decode()
        assert 'hx-swap-oob="innerHTML"' in content
        assert 'id="panel-main-content"' in content

    @patch("catalog.views.panels.services.list_sellers")
    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_empty_state_when_no_events(self, mock_seller, mock_catalogs, mock_list_sellers, factory):
        mock_seller.return_value = _mock_seller()
        mock_catalogs.return_value = _mock_paginated([])
        mock_list_sellers.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/1/events/")
        response = seller_events_panel(request, seller_id=1)

        content = response.content.decode()
        assert "panel-empty" in content
        assert "No events for this seller" in content


class TestEventLotsPanelContract:
    """Contract tests for GET /panels/events/{id}/lots/ — HTML fragment endpoint."""

    @patch("catalog.views.panels.services.list_lots_by_catalog")
    @patch("catalog.views.panels.services.get_catalog")
    def test_returns_html_fragment(self, mock_catalog, mock_lots, factory):
        mock_catalog.return_value = _mock_event()
        mock_lots.return_value = _mock_paginated([_mock_lot()])
        request = _make_get(factory, "/panels/events/1/lots/")
        response = event_lots_panel(request, event_id=1)

        content = response.content.decode()
        assert "<!DOCTYPE" not in content
        assert "<html" not in content
        assert response.status_code == 200

    @patch("catalog.views.panels.services.list_lots_by_catalog")
    @patch("catalog.views.panels.services.get_catalog")
    def test_contains_lot_card_structure(self, mock_catalog, mock_lots, factory):
        mock_catalog.return_value = _mock_event()
        mock_lots.return_value = _mock_paginated([
            _mock_lot(id=55, lot_number="L100", description="Test item"),
        ])
        request = _make_get(factory, "/panels/events/1/lots/")
        response = event_lots_panel(request, event_id=1)

        content = response.content.decode()
        assert "lot-card" in content
        assert "L100" in content
        assert "Test item" in content

    @patch("catalog.views.panels.services.list_lots_by_catalog")
    @patch("catalog.views.panels.services.get_catalog")
    def test_lot_links_use_standard_href(self, mock_catalog, mock_lots, factory):
        mock_catalog.return_value = _mock_event()
        mock_lots.return_value = _mock_paginated([_mock_lot(id=77)])
        request = _make_get(factory, "/panels/events/1/lots/")
        response = event_lots_panel(request, event_id=1)

        content = response.content.decode()
        assert 'href="/lots/77/"' in content
        assert "hx-get" not in content.split("lot-cards")[1].split("</ul>")[0]

    @patch("catalog.views.panels.services.list_lots_by_catalog")
    @patch("catalog.views.panels.services.get_catalog")
    def test_empty_state_when_no_lots(self, mock_catalog, mock_lots, factory):
        mock_catalog.return_value = _mock_event()
        mock_lots.return_value = _mock_paginated([])
        request = _make_get(factory, "/panels/events/1/lots/")
        response = event_lots_panel(request, event_id=1)

        content = response.content.decode()
        assert "panel-empty" in content
        assert "No lots in this event" in content


class TestHomePageContract:
    """Contract tests for GET / — should render shell.html."""

    @patch("catalog.views.sellers.services.list_sellers")
    def test_home_renders_shell(self, mock_list, factory):
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/")
        response = seller_list(request)

        content = response.content.decode()
        assert "shell" in content
        assert "panel-left1" in content
        assert "panel-left2" in content
        assert "panel-main" in content

    @patch("catalog.views.sellers.services.list_sellers")
    def test_sellers_page_renders_full_list(self, mock_list, factory):
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/sellers/")
        response = seller_list(request)

        content = response.content.decode()
        # /sellers/ should NOT render the shell layout
        assert "panel-left1" not in content


class TestPaginationContract:
    """Contract tests for pagination across all panel endpoints."""

    @patch("catalog.views.panels.services.list_sellers")
    def test_sellers_panel_shows_pagination_when_multi_page(self, mock_list, factory):
        mock_list.return_value = _mock_paginated(
            [_mock_seller()], total_items=100, page_number=1,
            total_pages=2, has_next_page=True,
        )
        request = _make_get(factory, "/panels/sellers/")
        response = sellers_panel(request)

        content = response.content.decode()
        assert "panel-pagination" in content
        assert "Next" in content
        assert 'hx-target="#panel-left1-content"' in content

    @patch("catalog.views.panels.services.list_sellers")
    def test_sellers_panel_no_pagination_when_single_page(self, mock_list, factory):
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/")
        response = sellers_panel(request)

        content = response.content.decode()
        assert "panel-pagination" not in content

    @patch("catalog.views.panels.services.list_sellers")
    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_events_panel_pagination_targets_left2(self, mock_seller, mock_catalogs, mock_list_sellers, factory):
        mock_seller.return_value = _mock_seller()
        mock_catalogs.return_value = _mock_paginated(
            [_mock_event()], total_items=100, page_number=1,
            total_pages=4, has_next_page=True,
        )
        mock_list_sellers.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/1/events/")
        response = seller_events_panel(request, seller_id=1)

        content = response.content.decode()
        assert "panel-pagination" in content
        assert 'hx-target="#panel-left2-content"' in content

    @patch("catalog.views.panels.services.list_lots_by_catalog")
    @patch("catalog.views.panels.services.get_catalog")
    def test_lots_panel_pagination_targets_main(self, mock_catalog, mock_lots, factory):
        mock_catalog.return_value = _mock_event()
        mock_lots.return_value = _mock_paginated(
            [_mock_lot()], total_items=100, page_number=1,
            total_pages=2, has_next_page=True,
        )
        request = _make_get(factory, "/panels/events/1/lots/")
        response = event_lots_panel(request, event_id=1)

        content = response.content.decode()
        assert "panel-pagination" in content
        assert 'hx-target="#panel-main-content"' in content

    @patch("catalog.views.panels.services.list_lots_by_catalog")
    @patch("catalog.views.panels.services.get_catalog")
    def test_lots_panel_page2_called_with_correct_params(self, mock_catalog, mock_lots, factory):
        mock_catalog.return_value = _mock_event(customer_catalog_id="CAT999")
        mock_lots.return_value = _mock_paginated(
            [_mock_lot(id=51, lot_number="L051")], page_number=2,
            total_pages=2, has_previous_page=True,
        )
        request = _make_get(factory, "/panels/events/1/lots/", {"page": "2"})
        response = event_lots_panel(request, event_id=1)

        content = response.content.decode()
        assert "L051" in content
        mock_lots.assert_called_once_with(request, "CAT999", page=2, page_size=50)


class TestSellerSelectionContract:
    """Contract tests for seller selection highlighting (FR-101, FR-103)."""

    @patch("catalog.views.panels.services.list_sellers")
    def test_selected_param_applies_active_class(self, mock_list, factory):
        """GET /panels/sellers/?selected=42 renders .active on seller 42."""
        mock_list.return_value = _mock_paginated([
            _mock_seller(id=42, name="Selected Seller"),
            _mock_seller(id=99, name="Other Seller"),
        ])
        request = _make_get(factory, "/panels/sellers/", {"selected": "42"})
        response = sellers_panel(request)

        content = response.content.decode()
        # Seller 42 should have active class
        assert 'class="panel-item active"' in content
        # Verify it's on the right item by checking surrounding context
        seller_42_block = content.split('sellers/42/events')[0].rsplit('<li', 1)[-1]
        assert 'active' in seller_42_block

    @patch("catalog.views.panels.services.list_sellers")
    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_events_response_includes_oob_seller_list_with_active(
        self, mock_seller, mock_catalogs, mock_list_sellers, factory
    ):
        """GET /panels/sellers/{id}/events/ includes OOB #panel-left1-content with .active."""
        mock_seller.return_value = _mock_seller(id=42)
        mock_catalogs.return_value = _mock_paginated([_mock_event()])
        mock_list_sellers.return_value = _mock_paginated([
            _mock_seller(id=42, name="Selected"),
            _mock_seller(id=99, name="Other"),
        ])
        request = _make_get(factory, "/panels/sellers/42/events/")
        response = seller_events_panel(request, seller_id=42)

        content = response.content.decode()
        # Must have OOB swap for seller list
        assert 'id="panel-left1-content"' in content
        assert 'hx-swap-oob' in content
        # Must have active class on the selected seller
        assert 'class="panel-item active"' in content


class TestEventSelectionContract:
    """Contract tests for event selection highlighting (FR-102)."""

    @patch("catalog.views.panels.services.list_sellers")
    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.list_lots_by_catalog")
    @patch("catalog.views.panels.services.get_catalog")
    def test_lots_response_includes_oob_events_list_with_active(
        self, mock_catalog, mock_lots, mock_catalogs, mock_list_sellers, factory
    ):
        """GET /panels/events/{id}/lots/ includes OOB #panel-left2-content with .active."""
        mock_catalog.return_value = _mock_event(
            id=7, customer_catalog_id="CAT001",
            sellers=[_mock_seller(id=42)],
        )
        mock_lots.return_value = _mock_paginated([_mock_lot()])
        mock_catalogs.return_value = _mock_paginated([
            _mock_event(id=7, title="Selected Event"),
            _mock_event(id=8, title="Other Event"),
        ])
        mock_list_sellers.return_value = _mock_paginated([_mock_seller(id=42)])
        request = _make_get(factory, "/panels/events/7/lots/")
        response = event_lots_panel(request, event_id=7)

        content = response.content.decode()
        # Must have OOB swap for events list
        assert 'id="panel-left2-content"' in content
        assert 'hx-swap-oob' in content
        # Must have active class on selected event
        assert 'class="panel-item active"' in content


class TestUrlPushContract:
    """Contract tests for HX-Push-Url headers (FR-107, FR-108)."""

    @patch("catalog.views.panels.services.list_sellers")
    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_seller_events_pushes_seller_url(self, mock_seller, mock_catalogs, mock_list_sellers, factory):
        """GET /panels/sellers/{id}/events/ has HX-Push-Url: /?seller={id}."""
        mock_seller.return_value = _mock_seller(id=42)
        mock_catalogs.return_value = _mock_paginated([_mock_event()])
        mock_list_sellers.return_value = _mock_paginated([_mock_seller(id=42)])
        request = _make_get(factory, "/panels/sellers/42/events/")
        response = seller_events_panel(request, seller_id=42)

        assert response["HX-Push-Url"] == "/?seller=42"

    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.list_lots_by_catalog")
    @patch("catalog.views.panels.services.get_catalog")
    def test_event_lots_pushes_seller_and_event_url(self, mock_catalog, mock_lots, mock_catalogs, factory):
        """GET /panels/events/{id}/lots/ has HX-Push-Url: /?seller={sid}&event={eid}."""
        mock_catalog.return_value = _mock_event(
            id=7, customer_catalog_id="CAT001",
            sellers=[_mock_seller(id=42)],
        )
        mock_lots.return_value = _mock_paginated([_mock_lot()])
        mock_catalogs.return_value = _mock_paginated([_mock_event(id=7)])
        request = _make_get(factory, "/panels/events/7/lots/")
        response = event_lots_panel(request, event_id=7)

        assert response["HX-Push-Url"] == "/?seller=42&event=7"


class TestShellHydrationContract:
    """Contract tests for URL-driven shell hydration (FR-109, FR-110)."""

    @patch("catalog.views.sellers.services.list_catalogs")
    @patch("catalog.views.sellers.services.get_seller")
    @patch("catalog.views.sellers.services.list_sellers")
    def test_shell_with_seller_param_renders_events(self, mock_list, mock_get_seller, mock_catalogs, factory):
        """GET /?seller=42 renders events in Left2 with seller highlighted."""
        mock_list.return_value = _mock_paginated([
            _mock_seller(id=42, name="Selected"),
            _mock_seller(id=99, name="Other"),
        ])
        mock_get_seller.return_value = _mock_seller(id=42, name="Selected")
        mock_catalogs.return_value = _mock_paginated([
            _mock_event(id=10, title="Event A"),
        ])
        request = _make_get(factory, "/", {"seller": "42"})
        response = seller_list(request)

        content = response.content.decode()
        # Left2 should contain events
        assert "Event A" in content
        # Seller 42 should be highlighted
        assert 'class="panel-item active"' in content

    @patch("catalog.views.sellers.services.list_lots_by_catalog")
    @patch("catalog.views.sellers.services.get_catalog")
    @patch("catalog.views.sellers.services.list_catalogs")
    @patch("catalog.views.sellers.services.get_seller")
    @patch("catalog.views.sellers.services.list_sellers")
    def test_shell_with_both_params_renders_events_and_lots(
        self, mock_list, mock_get_seller, mock_catalogs, mock_catalog, mock_lots, factory
    ):
        """GET /?seller=42&event=7 renders events + lots with both highlighted."""
        mock_list.return_value = _mock_paginated([_mock_seller(id=42)])
        mock_get_seller.return_value = _mock_seller(id=42)
        mock_catalogs.return_value = _mock_paginated([
            _mock_event(id=7, title="Selected Event"),
            _mock_event(id=8, title="Other Event"),
        ])
        mock_catalog.return_value = _mock_event(
            id=7, customer_catalog_id="CAT001",
            sellers=[_mock_seller(id=42)],
        )
        mock_lots.return_value = _mock_paginated([
            _mock_lot(id=1, lot_number="L001", description="Test Lot"),
        ])
        request = _make_get(factory, "/", {"seller": "42", "event": "7"})
        response = seller_list(request)

        content = response.content.decode()
        # Main should contain lots
        assert "Test Lot" in content
        # Events should be present
        assert "Selected Event" in content

    @patch("catalog.views.sellers.services.list_sellers")
    def test_shell_with_invalid_seller_param_renders_default(self, mock_list, factory):
        """GET /?seller=abc renders default shell without error."""
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/", {"seller": "abc"})
        response = seller_list(request)

        assert response.status_code == 200
        content = response.content.decode()
        # Should render default empty state, not crash
        assert "Select a seller to view events" in content


class TestMobileLayoutContract:
    """Contract tests for mobile viewport layout (FR-111, FR-112)."""

    @patch("catalog.views.sellers.services.list_sellers")
    def test_shell_contains_mobile_attributes_and_elements(self, mock_list, factory):
        """Shell HTML has data-mobile-panel, data-panel attrs, back button, and ARIA region."""
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/")
        response = seller_list(request)

        content = response.content.decode()
        # data-mobile-panel on .shell
        assert 'data-mobile-panel="sellers"' in content
        # data-panel on each panel
        assert 'data-panel="sellers"' in content
        assert 'data-panel="events"' in content
        assert 'data-panel="lots"' in content
        # Mobile back button
        assert 'mobile-back-btn' in content
        # ARIA live region
        assert 'panel-announcer' in content
        assert 'aria-live' in content


class TestLoadingIndicatorContract:
    """Contract tests for consistent loading indicators (FR-105, FR-106)."""

    @patch("catalog.views.sellers.services.list_sellers")
    def test_all_panels_have_htmx_indicator(self, mock_list, factory):
        """Shell HTML contains .htmx-indicator div inside all three panels."""
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/")
        response = seller_list(request)

        content = response.content.decode()
        # All three panels must contain an htmx-indicator
        for panel_id in ("panel-left1", "panel-left2", "panel-main"):
            panel_start = content.index(f'id="{panel_id}"')
            # Find the next panel or end of shell
            panel_section = content[panel_start:panel_start + 500]
            assert "htmx-indicator" in panel_section, (
                f"{panel_id} missing .htmx-indicator"
            )


class TestPaginationValidationContract:
    """Contract tests for defensive pagination parameter handling."""

    @patch("catalog.views.panels.services.list_sellers")
    def test_invalid_page_returns_200(self, mock_list, factory):
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/", {"page": "abc"})
        response = sellers_panel(request)

        assert response.status_code == 200
        mock_list.assert_called_once_with(request, page=1, page_size=50)

    @patch("catalog.views.panels.services.list_sellers")
    def test_negative_page_clamps_to_1(self, mock_list, factory):
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/", {"page": "-5"})
        response = sellers_panel(request)

        assert response.status_code == 200
        mock_list.assert_called_once_with(request, page=1, page_size=50)

    @patch("catalog.views.panels.services.list_sellers")
    def test_oversized_page_size_clamps_to_200(self, mock_list, factory):
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/", {"page_size": "9999"})
        response = sellers_panel(request)

        assert response.status_code == 200
        mock_list.assert_called_once_with(request, page=1, page_size=200)

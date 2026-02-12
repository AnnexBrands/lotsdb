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

    @patch("catalog.views.panels.services.get_catalog")
    def test_returns_html_fragment(self, mock_catalog, factory):
        mock_catalog.return_value = _mock_event(lots=[_mock_lot()])
        request = _make_get(factory, "/panels/events/1/lots/")
        response = event_lots_panel(request, event_id=1)

        content = response.content.decode()
        assert "<!DOCTYPE" not in content
        assert "<html" not in content
        assert response.status_code == 200

    @patch("catalog.views.panels.services.get_catalog")
    def test_contains_lot_card_structure(self, mock_catalog, factory):
        mock_catalog.return_value = _mock_event(lots=[
            _mock_lot(id=55, lot_number="L100", description="Test item"),
        ])
        request = _make_get(factory, "/panels/events/1/lots/")
        response = event_lots_panel(request, event_id=1)

        content = response.content.decode()
        assert "lot-card" in content
        assert "L100" in content
        assert "Test item" in content

    @patch("catalog.views.panels.services.get_catalog")
    def test_lot_links_use_standard_href(self, mock_catalog, factory):
        mock_catalog.return_value = _mock_event(lots=[_mock_lot(id=77)])
        request = _make_get(factory, "/panels/events/1/lots/")
        response = event_lots_panel(request, event_id=1)

        content = response.content.decode()
        assert 'href="/lots/77/"' in content
        assert "hx-get" not in content.split("lot-cards")[1].split("</ul>")[0]

    @patch("catalog.views.panels.services.get_catalog")
    def test_empty_state_when_no_lots(self, mock_catalog, factory):
        mock_catalog.return_value = _mock_event(lots=[])
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

    @patch("catalog.views.panels.services.get_catalog")
    def test_lots_panel_pagination_targets_main(self, mock_catalog, factory):
        # 51 lots at page_size=50 produces 2 pages
        lots = [_mock_lot(id=i, lot_number=f"L{i:03d}") for i in range(51)]
        mock_catalog.return_value = _mock_event(lots=lots)
        request = _make_get(factory, "/panels/events/1/lots/")
        response = event_lots_panel(request, event_id=1)

        content = response.content.decode()
        assert "panel-pagination" in content
        assert 'hx-target="#panel-main-content"' in content

    @patch("catalog.views.panels.services.get_catalog")
    def test_lots_panel_page2_shows_correct_slice(self, mock_catalog, factory):
        # 51 lots: page 1 = lots 0-49, page 2 = lot 50
        lots = [_mock_lot(id=i, lot_number=f"L{i:03d}") for i in range(51)]
        mock_catalog.return_value = _mock_event(lots=lots)
        request = _make_get(factory, "/panels/events/1/lots/", {"page": "2"})
        response = event_lots_panel(request, event_id=1)

        content = response.content.decode()
        assert "L050" in content
        # Page 1 lots should NOT be present
        assert "L000" not in content


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

    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_catalog")
    def test_lots_response_includes_oob_events_list_with_active(
        self, mock_catalog, mock_catalogs, factory
    ):
        """GET /panels/events/{id}/lots/ includes OOB #panel-left2-content with .active."""
        mock_catalog.return_value = _mock_event(
            id=7, customer_catalog_id="CAT001",
            sellers=[_mock_seller(id=42)],
            lots=[_mock_lot()],
        )
        mock_catalogs.return_value = _mock_paginated([
            _mock_event(id=7, title="Selected Event"),
            _mock_event(id=8, title="Other Event"),
        ])
        request = _make_get(factory, "/panels/events/7/lots/")
        response = event_lots_panel(request, event_id=7)

        content = response.content.decode()
        # Must have OOB swap for events list
        assert 'id="panel-left2-content"' in content
        assert 'hx-swap-oob' in content
        # Must have active class on selected event
        assert 'class="panel-item active"' in content


class TestUrlPushContract:
    """Contract tests for HX-Push-Url headers with customer-friendly IDs."""

    @patch("catalog.views.panels.services.list_sellers")
    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_seller_events_pushes_customer_display_id(self, mock_seller, mock_catalogs, mock_list_sellers, factory):
        """GET /panels/sellers/{id}/events/ HX-Push-Url uses customer_display_id (T015)."""
        mock_seller.return_value = _mock_seller(id=42, customer_display_id=4098)
        mock_catalogs.return_value = _mock_paginated([_mock_event()])
        mock_list_sellers.return_value = _mock_paginated([_mock_seller(id=42, customer_display_id=4098)])
        request = _make_get(factory, "/panels/sellers/42/events/")
        response = seller_events_panel(request, seller_id=42)

        assert response["HX-Push-Url"] == "/?seller=4098"

    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_catalog")
    def test_event_lots_pushes_customer_ids(self, mock_catalog, mock_catalogs, factory):
        """GET /panels/events/{id}/lots/ HX-Push-Url uses customer_display_id and customer_catalog_id (T015)."""
        mock_catalog.return_value = _mock_event(
            id=7, customer_catalog_id="395768",
            sellers=[_mock_seller(id=42, customer_display_id=4098)],
            lots=[_mock_lot()],
        )
        mock_catalogs.return_value = _mock_paginated([_mock_event(id=7)])
        request = _make_get(factory, "/panels/events/7/lots/")
        response = event_lots_panel(request, event_id=7)

        assert response["HX-Push-Url"] == "/?seller=4098&event=395768"


class TestShellHydrationContract:
    """Contract tests for URL-driven shell hydration with customer-friendly IDs."""

    @patch("catalog.views.sellers.services.list_catalogs")
    @patch("catalog.views.sellers.services.find_seller_by_display_id")
    @patch("catalog.views.sellers.services.list_sellers")
    def test_shell_with_display_id_renders_events(self, mock_list, mock_find_seller, mock_catalogs, factory):
        """GET /?seller=4098 resolves seller by display_id and renders events (T016)."""
        mock_list.return_value = _mock_paginated([
            _mock_seller(id=42, customer_display_id=4098, name="Selected"),
            _mock_seller(id=99, customer_display_id=5000, name="Other"),
        ])
        mock_find_seller.return_value = _mock_seller(id=42, customer_display_id=4098, name="Selected")
        mock_catalogs.return_value = _mock_paginated([
            _mock_event(id=10, title="Event A"),
        ])
        request = _make_get(factory, "/", {"seller": "4098"})
        response = seller_list(request)

        content = response.content.decode()
        assert "Event A" in content
        assert 'class="panel-item active"' in content

    @patch("catalog.views.sellers.services.get_catalog")
    @patch("catalog.views.sellers.services.find_catalog_by_customer_id")
    @patch("catalog.views.sellers.services.list_catalogs")
    @patch("catalog.views.sellers.services.find_seller_by_display_id")
    @patch("catalog.views.sellers.services.list_sellers")
    def test_shell_with_display_id_and_catalog_id_renders_lots(
        self, mock_list, mock_find_seller, mock_catalogs, mock_find_catalog, mock_catalog, factory
    ):
        """GET /?seller=4098&event=395768 resolves both and renders lots (T016)."""
        mock_list.return_value = _mock_paginated([_mock_seller(id=42, customer_display_id=4098)])
        mock_find_seller.return_value = _mock_seller(id=42, customer_display_id=4098)
        mock_catalogs.return_value = _mock_paginated([
            _mock_event(id=7, title="Selected Event"),
            _mock_event(id=8, title="Other Event"),
        ])
        mock_find_catalog.return_value = 7
        mock_catalog.return_value = _mock_event(
            id=7, customer_catalog_id="395768",
            sellers=[_mock_seller(id=42, customer_display_id=4098)],
            lots=[_mock_lot(id=1, lot_number="L001", description="Test Lot")],
        )
        request = _make_get(factory, "/", {"seller": "4098", "event": "395768"})
        response = seller_list(request)

        content = response.content.decode()
        assert "Test Lot" in content
        assert "Selected Event" in content

    @patch("catalog.views.sellers.services.list_sellers")
    def test_shell_with_invalid_seller_param_renders_default(self, mock_list, factory):
        """GET /?seller=abc renders default shell without error."""
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/", {"seller": "abc"})
        response = seller_list(request)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Select a seller to view events" in content

    @patch("catalog.views.sellers.services.find_seller_by_display_id")
    @patch("catalog.views.sellers.services.list_sellers")
    def test_shell_with_nonexistent_seller_renders_default(self, mock_list, mock_find_seller, factory):
        """GET /?seller=99999 (non-existent display_id) renders default empty state."""
        mock_list.return_value = _mock_paginated([_mock_seller()])
        mock_find_seller.return_value = None
        request = _make_get(factory, "/", {"seller": "99999"})
        response = seller_list(request)

        assert response.status_code == 200
        content = response.content.decode()
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

    @patch("catalog.views.sellers.services.list_sellers")
    def test_shell_with_invalid_page_returns_200(self, mock_list, factory):
        """GET /?page=abc returns 200, not 500 (T002: defensive parsing on shell)."""
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/", {"page": "abc"})
        response = seller_list(request)

        assert response.status_code == 200


class TestHydratedPaginationUrlContract:
    """Contract tests for hydrated panel pagination URLs (T002)."""

    @patch("catalog.views.sellers.services.get_catalog")
    @patch("catalog.views.sellers.services.find_catalog_by_customer_id")
    @patch("catalog.views.sellers.services.list_catalogs")
    @patch("catalog.views.sellers.services.find_seller_by_display_id")
    @patch("catalog.views.sellers.services.list_sellers")
    def test_hydrated_events_panel_has_valid_pagination_url(
        self, mock_list, mock_find_seller, mock_catalogs, mock_find_catalog, mock_catalog, factory
    ):
        """Hydrated events panel contains hx-get pagination URL starting with /panels/sellers/."""
        mock_list.return_value = _mock_paginated([_mock_seller(id=42, customer_display_id=4098)])
        mock_find_seller.return_value = _mock_seller(id=42, customer_display_id=4098)
        mock_catalogs.return_value = _mock_paginated(
            [_mock_event()], total_items=100, page_number=1,
            total_pages=2, has_next_page=True,
        )
        mock_find_catalog.return_value = 7
        mock_catalog.return_value = _mock_event(
            id=7, sellers=[_mock_seller(id=42)],
            lots=[_mock_lot()],
        )
        request = _make_get(factory, "/", {"seller": "4098", "event": "CAT001"})
        response = seller_list(request)

        content = response.content.decode()
        assert 'hx-get="/panels/sellers/42/events/' in content

    @patch("catalog.views.sellers.services.get_catalog")
    @patch("catalog.views.sellers.services.find_catalog_by_customer_id")
    @patch("catalog.views.sellers.services.list_catalogs")
    @patch("catalog.views.sellers.services.find_seller_by_display_id")
    @patch("catalog.views.sellers.services.list_sellers")
    def test_hydrated_lots_panel_has_valid_pagination_url(
        self, mock_list, mock_find_seller, mock_catalogs, mock_find_catalog, mock_catalog, factory
    ):
        """Hydrated lots panel contains hx-get pagination URL starting with /panels/events/."""
        mock_list.return_value = _mock_paginated([_mock_seller(id=42, customer_display_id=4098)])
        mock_find_seller.return_value = _mock_seller(id=42, customer_display_id=4098)
        mock_catalogs.return_value = _mock_paginated([_mock_event(id=7)])
        mock_find_catalog.return_value = 7
        # 51 lots at page_size=50 produces 2 pages of local pagination
        lots = [_mock_lot(id=i, lot_number=f"L{i:03d}") for i in range(51)]
        mock_catalog.return_value = _mock_event(
            id=7, sellers=[_mock_seller(id=42)],
            lots=lots,
        )
        request = _make_get(factory, "/", {"seller": "4098", "event": "CAT001"})
        response = seller_list(request)

        content = response.content.decode()
        assert 'hx-get="/panels/events/7/lots/' in content

    @patch("catalog.views.sellers.services.find_catalog_by_customer_id")
    @patch("catalog.views.sellers.services.get_catalog")
    @patch("catalog.views.sellers.services.list_catalogs")
    @patch("catalog.views.sellers.services.find_seller_by_display_id")
    @patch("catalog.views.sellers.services.list_sellers")
    def test_hydration_with_mismatched_seller_event_ignores_event(
        self, mock_list, mock_find_seller, mock_catalogs, mock_catalog, mock_find_catalog, factory
    ):
        """Hydration with mismatched seller/event ignores event, renders seller-only state."""
        mock_list.return_value = _mock_paginated([_mock_seller(id=42, customer_display_id=4098)])
        mock_find_seller.return_value = _mock_seller(id=42, customer_display_id=4098)
        mock_catalogs.return_value = _mock_paginated([_mock_event(id=10)])
        mock_find_catalog.return_value = 999
        mock_catalog.return_value = _mock_event(
            id=999, sellers=[_mock_seller(id=99)],  # Different seller
        )
        request = _make_get(factory, "/", {"seller": "4098", "event": "BADCAT"})
        response = seller_list(request)

        content = response.content.decode()
        assert "Select an event to view lots" in content


class TestPanelFilterContract:
    """Contract tests for panel header filter inputs (US4 - T023, T024)."""

    @patch("catalog.views.panels.services.list_sellers")
    def test_sellers_panel_with_name_filter(self, mock_list, factory):
        """GET /panels/sellers/?name=Test passes Name filter to list_sellers (T023)."""
        mock_list.return_value = _mock_paginated([_mock_seller(name="Test Seller")])
        request = _make_get(factory, "/panels/sellers/", {"name": "Test"})
        response = sellers_panel(request)

        assert response.status_code == 200
        mock_list.assert_called_once_with(request, page=1, page_size=50, Name="Test")

    @patch("catalog.views.panels.services.list_sellers")
    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_events_panel_with_title_filter(self, mock_seller, mock_catalogs, mock_list_sellers, factory):
        """GET /panels/sellers/{id}/events/?title=Test passes Title filter to list_catalogs (T023)."""
        mock_seller.return_value = _mock_seller()
        mock_catalogs.return_value = _mock_paginated([_mock_event(title="Test Event")])
        mock_list_sellers.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/1/events/", {"title": "Test"})
        response = seller_events_panel(request, seller_id=1)

        assert response.status_code == 200
        mock_catalogs.assert_called_once_with(request, page=1, page_size=50, seller_id=1, Title="Test")

    @patch("catalog.views.panels.services.list_sellers")
    def test_sellers_panel_contains_filter_form(self, mock_list, factory):
        """Seller list panel HTML contains a panel-filter form element (T024)."""
        mock_list.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/")
        response = sellers_panel(request)

        content = response.content.decode()
        assert "panel-filter" in content


class TestEmptyStateContract:
    """Contract tests for contextual empty state messaging (US3 - T021)."""

    @patch("catalog.views.panels.services.list_sellers")
    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_events_panel_oob_main_shows_select_event_message(self, mock_seller, mock_catalogs, mock_list_sellers, factory):
        """When events panel loads, OOB #panel-main-content shows 'Select an event to view lots'."""
        mock_seller.return_value = _mock_seller()
        mock_catalogs.return_value = _mock_paginated([_mock_event()])
        mock_list_sellers.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/1/events/")
        response = seller_events_panel(request, seller_id=1)

        content = response.content.decode()
        # OOB main panel clear should have contextual message
        oob_main = content.split('id="panel-main-content"')[1]
        assert "Select an event to view lots" in oob_main


class TestLotsDataContract:
    """Contract tests for lots panel data source (US2 - T014: embedded lots)."""

    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_catalog")
    def test_event_lots_uses_embedded_lots(self, mock_catalog, mock_catalogs, factory):
        """event_lots_panel renders lots from event.lots (embedded catalog data)."""
        mock_catalog.return_value = _mock_event(
            id=7, customer_catalog_id="CAT001",
            sellers=[_mock_seller(id=42)],
            lots=[
                _mock_lot(id=10, lot_number="L010"),
                _mock_lot(id=11, lot_number="L011"),
            ],
        )
        mock_catalogs.return_value = _mock_paginated([_mock_event(id=7)])
        request = _make_get(factory, "/panels/events/7/lots/")
        response = event_lots_panel(request, event_id=7)

        content = response.content.decode()
        assert response.status_code == 200
        assert "L010" in content
        assert "L011" in content

    @patch("catalog.views.panels.services.list_lots_by_catalog")
    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_catalog")
    def test_event_lots_does_not_call_list_lots_by_catalog(self, mock_catalog, mock_catalogs, mock_lots, factory):
        """event_lots_panel must NOT call list_lots_by_catalog (AC-8)."""
        mock_catalog.return_value = _mock_event(
            id=7, customer_catalog_id="CAT001",
            sellers=[_mock_seller(id=42)],
            lots=[_mock_lot()],
        )
        mock_catalogs.return_value = _mock_paginated([_mock_event(id=7)])
        request = _make_get(factory, "/panels/events/7/lots/")
        event_lots_panel(request, event_id=7)

        mock_lots.assert_not_called()


class TestIndicatorWiringContract:
    """Contract tests for hx-indicator attributes on panel items (T003)."""

    @patch("catalog.views.panels.services.list_sellers")
    def test_seller_items_have_hx_indicator(self, mock_list, factory):
        """Seller list items should have hx-indicator pointing to Left2 panel."""
        mock_list.return_value = _mock_paginated([_mock_seller(id=1)])
        request = _make_get(factory, "/panels/sellers/")
        response = sellers_panel(request)

        content = response.content.decode()
        assert 'hx-indicator=' in content

    @patch("catalog.views.panels.services.list_sellers")
    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_event_items_have_hx_indicator(self, mock_seller, mock_catalogs, mock_list_sellers, factory):
        """Event list items should have hx-indicator pointing to Main panel."""
        mock_seller.return_value = _mock_seller()
        mock_catalogs.return_value = _mock_paginated([_mock_event(id=1)])
        mock_list_sellers.return_value = _mock_paginated([_mock_seller()])
        request = _make_get(factory, "/panels/sellers/1/events/")
        response = seller_events_panel(request, seller_id=1)

        content = response.content.decode()
        assert 'hx-indicator=' in content

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

    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_returns_html_fragment(self, mock_seller, mock_catalogs, factory):
        mock_seller.return_value = _mock_seller()
        mock_catalogs.return_value = _mock_paginated([_mock_event()])
        request = _make_get(factory, "/panels/sellers/1/events/")
        response = seller_events_panel(request, seller_id=1)

        content = response.content.decode()
        assert "<!DOCTYPE" not in content
        assert "<html" not in content
        assert response.status_code == 200

    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_contains_panel_structure_and_htmx(self, mock_seller, mock_catalogs, factory):
        mock_seller.return_value = _mock_seller()
        mock_catalogs.return_value = _mock_paginated([_mock_event(id=99)])
        request = _make_get(factory, "/panels/sellers/1/events/")
        response = seller_events_panel(request, seller_id=1)

        content = response.content.decode()
        assert "panel-list" in content
        assert "panel-item" in content
        assert 'hx-get="/panels/events/99/lots/"' in content
        assert 'hx-target="#panel-main-content"' in content

    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_includes_oob_clear_for_main_panel(self, mock_seller, mock_catalogs, factory):
        mock_seller.return_value = _mock_seller()
        mock_catalogs.return_value = _mock_paginated([_mock_event()])
        request = _make_get(factory, "/panels/sellers/1/events/")
        response = seller_events_panel(request, seller_id=1)

        content = response.content.decode()
        assert 'hx-swap-oob="innerHTML"' in content
        assert 'id="panel-main-content"' in content

    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_empty_state_when_no_events(self, mock_seller, mock_catalogs, factory):
        mock_seller.return_value = _mock_seller()
        mock_catalogs.return_value = _mock_paginated([])
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

    @patch("catalog.views.panels.services.list_catalogs")
    @patch("catalog.views.panels.services.get_seller")
    def test_events_panel_pagination_targets_left2(self, mock_seller, mock_catalogs, factory):
        mock_seller.return_value = _mock_seller()
        mock_catalogs.return_value = _mock_paginated(
            [_mock_event()], total_items=100, page_number=1,
            total_pages=4, has_next_page=True,
        )
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

import logging
import time

import requests
from ABConnect.config import Config, get_config
from ABConnect.api.auth import FileTokenStorage
from ABConnect.api.catalog.http_client import CatalogRequestHandler
from ABConnect.api.catalog.endpoints.base import BaseCatalogEndpoint
from ABConnect.exceptions import LoginFailedError

logger = logging.getLogger(__name__)


class _SessionTokenAdapter:
    """Minimal token storage adapter that reads/writes tokens to a Django session."""

    def __init__(self, session):
        self._session = session

    def get_token(self):
        token = self._session.get("abc_token")
        if not token:
            return None
        if time.time() >= token.get("expires_at", 0):
            if not self._refresh(token):
                return None
        return token

    def _refresh(self, token):
        refresh = token.get("refresh_token")
        if not refresh:
            return False
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": get_config("ABC_CLIENT_ID"),
            "client_secret": get_config("ABC_CLIENT_SECRET"),
            "scope": "offline_access",
            "rememberMe": True,
        }
        try:
            r = requests.post(Config.get_identity_url(), data=data)
            if r.ok:
                new_token = r.json()
                new_token["expires_at"] = time.time() + new_token["expires_in"] - 300
                self._session["abc_token"] = new_token
                return True
        except Exception:
            logger.exception("Token refresh failed")
        return False


def login(request, username, password):
    """Authenticate via ABConnect FileTokenStorage and store token in session."""
    Config.load()
    storage = FileTokenStorage(username=username, password=password)
    token = storage._token
    if not token:
        raise LoginFailedError("Login failed: invalid credentials")
    request.session["abc_token"] = token
    request.session["abc_username"] = username


def get_catalog_api(request):
    """Return a CatalogAPI instance using the session token."""
    adapter = _SessionTokenAdapter(request.session)
    handler = CatalogRequestHandler(adapter)
    BaseCatalogEndpoint.set_request_handler(handler)
    from ABConnect.api.catalog.endpoints import (
        CatalogEndpoint,
        LotEndpoint,
        SellerEndpoint,
        BulkEndpoint,
    )

    class _CatalogAPI:
        def __init__(self):
            self.catalogs = CatalogEndpoint()
            self.lots = LotEndpoint()
            self.sellers = SellerEndpoint()
            self.bulk = BulkEndpoint()

    return _CatalogAPI()


def is_authenticated(request):
    """Check if the session has a valid token."""
    token = request.session.get("abc_token")
    if not token:
        return False
    if time.time() >= token.get("expires_at", 0):
        adapter = _SessionTokenAdapter(request.session)
        return adapter.get_token() is not None
    return True


# --- Seller service methods ---


def list_sellers(request, page=1, page_size=25, **filters):
    api = get_catalog_api(request)
    return api.sellers.list(page_number=page, page_size=page_size, **filters)


def get_seller(request, seller_id):
    api = get_catalog_api(request)
    return api.sellers.get(seller_id)


# --- Catalog (Event) service methods ---


def list_catalogs(request, page=1, page_size=25, seller_id=None, **filters):
    api = get_catalog_api(request)
    if seller_id is not None:
        filters["SellerIds"] = seller_id
    return api.catalogs.list(page_number=page, page_size=page_size, **filters)


def get_catalog(request, catalog_id):
    api = get_catalog_api(request)
    return api.catalogs.get(catalog_id)


# --- Lot service methods ---


def list_lots_by_catalog(request, customer_catalog_id, page=1, page_size=25):
    api = get_catalog_api(request)
    return api.lots.list(
        page_number=page, page_size=page_size, customer_catalog_id=str(customer_catalog_id)
    )


def get_lot(request, lot_id):
    api = get_catalog_api(request)
    return api.lots.get(lot_id)


def save_lot_override(request, lot_id, override_data):
    """Update a lot's overriden_data with new override values."""
    from ABConnect.api.models.catalog import UpdateLotRequest, LotDataDto

    api = get_catalog_api(request)
    lot = api.lots.get(lot_id)

    override = LotDataDto(**override_data)
    update_req = UpdateLotRequest(
        customer_item_id=lot.customer_item_id,
        image_links=[img.link for img in lot.image_links] if lot.image_links else [],
        overriden_data=[override],
        catalogs=lot.catalogs,
    )
    return api.lots.update(lot_id, update_req)


def bulk_insert(request, data):
    """Insert catalog data via the bulk endpoint."""
    api = get_catalog_api(request)
    return api.bulk.insert(data)


def search_lots(request, query, page=1, page_size=25):
    """Search lots by customer item ID and lot number, combining results."""
    api = get_catalog_api(request)

    by_item = api.lots.list(page_number=page, page_size=page_size, CustomerItemId=query)
    by_lot_num = api.lots.list(page_number=page, page_size=page_size, LotNumber=query)

    # Merge and deduplicate by lot id
    seen = set()
    merged = []
    for lot in list(by_item.items) + list(by_lot_num.items):
        if lot.id not in seen:
            seen.add(lot.id)
            merged.append(lot)

    by_item.items = merged
    by_item.total_items = len(merged)
    return by_item

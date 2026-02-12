import logging

from ABConnect import ABConnectAPI

logger = logging.getLogger(__name__)


def login(request, username, password):
    """Authenticate via ABConnectAPI with session-based token storage."""
    ABConnectAPI(request=request, username=username, password=password)
    request.session["abc_username"] = username


def get_catalog_api(request):
    """Return a CatalogAPI instance backed by the session token."""
    return ABConnectAPI(request=request).catalog


def is_authenticated(request):
    """Check if the session has a valid token."""
    return bool(request.session.get("abc_token"))


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


def find_catalog_by_customer_id(request, customer_catalog_id):
    """Look up a catalog by its customer_catalog_id and return its internal id, or None."""
    api = get_catalog_api(request)
    result = api.catalogs.list(page_number=1, page_size=1, CustomerCatalogId=customer_catalog_id)
    if result.items:
        return result.items[0].id
    return None


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

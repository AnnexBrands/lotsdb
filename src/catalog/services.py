import logging
from datetime import date, datetime
from types import SimpleNamespace

from ABConnect import ABConnectAPI
from django.contrib.auth import login as django_login
from django.contrib.auth.models import User

from catalog.cache import safe_cache_get, safe_cache_set

logger = logging.getLogger(__name__)

SELLERS_CACHE_KEY = "sellers_all"
CATALOGS_CACHE_KEY_PREFIX = "catalogs_seller_"


def login(request, username, password):
    """Authenticate via ABConnect, then bridge to Django User."""
    ABConnectAPI(request=request, username=username, password=password)
    request.session["abc_username"] = username

    # Bridge to Django User for authorization support
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"is_staff": True},
    )
    if created:
        user.set_unusable_password()
        user.save()
    django_login(request, user, backend="django.contrib.auth.backends.ModelBackend")


def get_catalog_api(request):
    """Return a CatalogAPI instance backed by the session token."""
    return ABConnectAPI(request=request).catalog


def is_authenticated(request):
    """Check if the session has a valid token."""
    return bool(request.session.get("abc_token"))


# --- Seller service methods ---


def _make_paginated(items, page, page_size):
    """Build a SimpleNamespace mimicking PaginatedList from an in-memory list."""
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    page_items = items[start:start + page_size]
    return SimpleNamespace(
        items=page_items,
        page_number=page,
        total_pages=total_pages,
        total_items=total,
        has_previous_page=page > 1,
        has_next_page=page < total_pages,
    )


def list_sellers(request, page=1, page_size=25, **filters):
    if filters:
        api = get_catalog_api(request)
        return api.sellers.list(page_number=page, page_size=page_size, **filters)

    cached = safe_cache_get(SELLERS_CACHE_KEY)
    if cached is not None:
        items = [SimpleNamespace(**d) for d in cached]
        return _make_paginated(items, page, page_size)

    api = get_catalog_api(request)
    result = api.sellers.list(page_number=1, page_size=500)
    projected = [
        {"id": s.id, "name": s.name, "customer_display_id": s.customer_display_id}
        for s in result.items
    ]
    safe_cache_set(SELLERS_CACHE_KEY, projected)
    items = [SimpleNamespace(**d) for d in projected]
    return _make_paginated(items, page, page_size)


def get_seller(request, seller_id):
    api = get_catalog_api(request)
    return api.sellers.get(seller_id)


def find_seller_by_display_id(request, display_id):
    """Look up a seller by customer_display_id and return the seller object, or None."""
    api = get_catalog_api(request)
    result = api.sellers.list(page_number=1, page_size=1, CustomerDisplayId=display_id)
    if result.items:
        return result.items[0]
    return None


# --- Catalog (Event) service methods ---


def list_catalogs(request, page=1, page_size=25, seller_id=None, use_cache=True, **filters):
    if seller_id is not None and not filters:
        cache_key = f"{CATALOGS_CACHE_KEY_PREFIX}{seller_id}"
        if use_cache:
            cached = safe_cache_get(cache_key)
        else:
            cached = None
        if cached is not None:
            items = []
            for d in cached:
                if d.get("start_date"):
                    d["start_date"] = datetime.fromisoformat(d["start_date"])
                items.append(SimpleNamespace(**d))
            return _make_paginated(items, page, page_size)

        api = get_catalog_api(request)
        result = api.catalogs.list(page_number=1, page_size=200, SellerIds=seller_id)
        today = date.today()
        future_items = [
            c for c in result.items
            if c.start_date and c.start_date.date() >= today
        ]
        projected = [
            {"id": c.id, "title": c.title, "customer_catalog_id": c.customer_catalog_id,
             "start_date": c.start_date.isoformat() if c.start_date else None}
            for c in future_items
        ]
        safe_cache_set(cache_key, projected)
        items = []
        for d in projected:
            if d.get("start_date"):
                d["start_date"] = datetime.fromisoformat(d["start_date"])
            items.append(SimpleNamespace(**d))
        return _make_paginated(items, page, page_size)

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


def get_lots_for_event(request, lot_ids):
    """Fetch full LotDto for each lot ID. No batch API available."""
    results = []
    for lot_id in lot_ids:
        results.append(get_lot(request, lot_id))
    return results


def save_lot_override(request, lot_id, override_data):
    """Update a lot's overriden_data, merging with existing overrides to preserve fields not in override_data."""
    from ABConnect.api.models.catalog import UpdateLotRequest, LotDataDto

    api = get_catalog_api(request)
    lot = api.lots.get(lot_id)

    # Merge: start with existing override values, then overlay new values on top.
    # This prevents inline saves from clobbering description/notes overrides
    # and modal text saves from clobbering dimension/flag overrides.
    merged = {}
    existing = lot.overriden_data[0] if lot.overriden_data else None
    if existing:
        for attr in (
            "qty", "l", "w", "h", "wgt", "value", "cpack",
            "description", "notes", "item_id", "force_crate",
            "noted_conditions", "do_not_tip", "commodity_id",
        ):
            val = getattr(existing, attr, None)
            if val is not None:
                merged[attr] = val
    merged.update(override_data)

    override = LotDataDto(**merged)
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

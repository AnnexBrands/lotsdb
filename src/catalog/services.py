import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from types import SimpleNamespace

import requests
from ab.client import ABConnectAPI
from django.contrib.auth import login as django_login
from django.contrib.auth.models import User
from django.core.cache import cache as django_cache

from catalog.cache import safe_cache_get, safe_cache_set

logger = logging.getLogger(__name__)

SELLERS_CACHE_KEY = "sellers_all"
CATALOGS_CACHE_KEY_PREFIX = "catalogs_seller_"
RECOVERY_CACHE_TTL = 86400  # 24 hours

IMAGE_URL_TEMPLATE = "https://s3.amazonaws.com/static2.liveauctioneers.com/{house_id}/{catalog_id}/{lot_id}_{n}_m.jpg"
IMAGE_SCAN_MAX_POSITIONS = 200
IMAGE_SCAN_CONSECUTIVE_FAILURES = 3
IMAGE_SCAN_TIMEOUT = 5
IMAGE_SCAN_MAX_WORKERS = 10


def login(request, username, password):
    """Authenticate via AB SDK, then bridge to Django User."""
    api = ABConnectAPI(request=request)
    # Override credentials for this login attempt (env vars hold defaults).
    # The first API call triggers _password_grant() with these values.
    api._settings.username = username
    api._settings.password = password
    # Force authentication by triggering token acquisition
    api._catalog._ensure_token()
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
    """Return an ABConnectAPI instance backed by the session token.

    Caches on the request object so only one ABConnectAPI (and one
    token load) is created per HTTP request.
    """
    if not hasattr(request, "_catalog_api"):
        request._catalog_api = ABConnectAPI(request=request)
    return request._catalog_api


def is_authenticated(request):
    """Check if the session has a valid token."""
    return bool(request.session.get("ab_token"))


# --- Filtered list helper (SDK workaround) ---


def _filtered_list(client, path, item_model_name, **params):
    """Make a filtered paginated list request directly via the HTTP client.

    The AB SDK's list() methods only accept page/page_size. This helper
    bypasses them to pass arbitrary query params (filters) directly.
    """
    from ab.api.models.shared import PaginatedList
    from ab.api import models as ab_models

    response = client.request("GET", path, params=params)
    if response is None:
        return PaginatedList(
            items=[], page_number=0, total_pages=0,
            total_items=0, has_previous_page=False, has_next_page=False,
        )
    model_cls = getattr(ab_models, item_model_name)
    items = [model_cls.model_validate(item) for item in response.get("items", [])]
    return PaginatedList(
        items=items,
        page_number=response.get("pageNumber", 0),
        total_pages=response.get("totalPages", 0),
        total_items=response.get("totalItems", 0),
        has_previous_page=response.get("hasPreviousPage", False),
        has_next_page=response.get("hasNextPage", False),
    )


# --- Seller service methods ---


def _make_paginated(items, page, page_size):
    """Build a SimpleNamespace mimicking PaginatedList from an in-memory list."""
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]
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
        return _filtered_list(
            api.sellers._client, "/Seller", "SellerExpandedDto",
            pageNumber=page, pageSize=page_size, **filters,
        )

    cached = safe_cache_get(SELLERS_CACHE_KEY)
    if cached is not None:
        items = [SimpleNamespace(**d) for d in cached]
        return _make_paginated(items, page, page_size)

    api = get_catalog_api(request)
    result = api.sellers.list(page=1, page_size=500)
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
    result = _filtered_list(
        api.sellers._client, "/Seller", "SellerExpandedDto",
        pageNumber=1, pageSize=1, CustomerDisplayId=display_id,
    )
    if result.items:
        return result.items[0]
    return None


# --- Catalog (Event) service methods ---


def list_catalogs(
    request,
    page=1,
    page_size=25,
    seller_id=None,
    use_cache=True,
    future_only=True,
    **filters,
):
    if seller_id is not None and not filters:
        cache_key = f"{CATALOGS_CACHE_KEY_PREFIX}{seller_id}"
        if use_cache:
            cached = safe_cache_get(cache_key)
        else:
            cached = None
        if cached is not None:
            today = date.today()
            items = []
            for d in cached:
                if d.get("start_date"):
                    d["start_date"] = datetime.fromisoformat(d["start_date"])
                items.append(SimpleNamespace(**d))
            if future_only:
                items = [
                    i for i in items if i.start_date and i.start_date.date() >= today
                ]
            return _make_paginated(items, page, page_size)

        api = get_catalog_api(request)
        result = _filtered_list(
            api.catalog._client, "/Catalog", "CatalogExpandedDto",
            pageNumber=1, pageSize=200, SellerIds=seller_id,
        )
        # Cache ALL events so future_only=False hits also benefit from cache
        projected_all = [
            {
                "id": c.id,
                "title": c.title,
                "customer_catalog_id": c.customer_catalog_id,
                "start_date": c.start_date.isoformat() if c.start_date else None,
            }
            for c in result.items
        ]
        safe_cache_set(cache_key, projected_all)

        today = date.today()
        items = []
        for d in projected_all:
            if d.get("start_date"):
                d["start_date"] = datetime.fromisoformat(d["start_date"])
            items.append(SimpleNamespace(**d))
        if future_only:
            items = [i for i in items if i.start_date and i.start_date.date() >= today]
        return _make_paginated(items, page, page_size)

    api = get_catalog_api(request)
    filter_params = dict(filters)
    if seller_id is not None:
        filter_params["SellerIds"] = seller_id
    return _filtered_list(
        api.catalog._client, "/Catalog", "CatalogExpandedDto",
        pageNumber=page, pageSize=page_size, **filter_params,
    )


def get_catalog(request, catalog_id):
    api = get_catalog_api(request)
    return api.catalog.get(catalog_id)


# --- Lot service methods ---


def list_lots_by_catalog(request, customer_catalog_id, page=1, page_size=25):
    api = get_catalog_api(request)
    return _filtered_list(
        api.lots._client, "/Lot", "LotDto",
        pageNumber=page, pageSize=page_size,
        customer_catalog_id=str(customer_catalog_id),
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
    api = get_catalog_api(request)
    lot = api.lots.get(lot_id)

    # Merge: start with existing override values, then overlay new values on top.
    merged = {}
    existing = lot.overriden_data[0] if lot.overriden_data else None
    if existing:
        for attr in (
            "qty", "l", "w", "h", "wgt", "value",
            "cpack", "description", "notes", "item_id",
            "force_crate", "noted_conditions", "do_not_tip", "commodity_id",
        ):
            val = getattr(existing, attr, None)
            if val is not None:
                merged[attr] = val
    merged.update(override_data)

    update_req = {
        "customerItemId": lot.customer_item_id,
        "imageLinks": [img.link for img in lot.image_links] if lot.image_links else [],
        "overridenData": [merged],
        "catalogs": [
            c.model_dump(by_alias=True) if hasattr(c, "model_dump") else c
            for c in (lot.catalogs or [])
        ],
    }
    result = api.lots.update(lot_id, data=update_req)
    return result


def bulk_insert(request, data):
    """Insert catalog data via the bulk endpoint."""
    api = get_catalog_api(request)
    return api.catalog.bulk_insert(data=data)


def find_catalog_by_customer_id(request, customer_catalog_id):
    """Look up a catalog by its customer_catalog_id and return its internal id, or None."""
    api = get_catalog_api(request)
    result = _filtered_list(
        api.catalog._client, "/Catalog", "CatalogExpandedDto",
        pageNumber=1, pageSize=1, CustomerCatalogId=customer_catalog_id,
    )
    if result.items:
        return result.items[0].id
    return None


def fetch_all_lots(request, customer_catalog_id):
    """Paginate through all lots for a catalog and return the complete list."""
    all_lots = []
    page = 1
    while True:
        result = list_lots_by_catalog(
            request, customer_catalog_id, page=page, page_size=100
        )
        all_lots.extend(result.items)
        if not result.has_next_page:
            break
        page += 1
    return all_lots


def create_lot(request, add_lot_request):
    """Create a single lot via the API."""
    api = get_catalog_api(request)
    return api.lots.create(data=add_lot_request)


def delete_lot(request, lot_id):
    """Delete a single lot via the API."""
    api = get_catalog_api(request)
    api.lots.delete(lot_id)


# --- Merge comparison fields ---
_COMPARE_FIELDS_NUMERIC = ("qty", "l", "w", "h", "wgt")
_COMPARE_FIELDS_STR = ("cpack",)
_COMPARE_FIELDS_BOOL = ("force_crate",)


def _get_field(obj, field, default=None):
    """Get a field from a dict or object."""
    if isinstance(obj, dict):
        return obj.get(field, default)
    return getattr(obj, field, default)


def lots_differ(file_data, server_data):
    """Compare dimensional/shipping fields between file and server initial_data.

    Returns True if any of the 7 comparison fields differ.
    Normalizes None to 0 (numeric), "" (string), False (bool).
    """
    for field in _COMPARE_FIELDS_NUMERIC:
        fv = _get_field(file_data, field) or 0
        sv = _get_field(server_data, field) or 0
        if float(fv) != float(sv):
            return True
    for field in _COMPARE_FIELDS_STR:
        fv = _get_field(file_data, field) or ""
        sv = _get_field(server_data, field) or ""
        if str(fv) != str(sv):
            return True
    for field in _COMPARE_FIELDS_BOOL:
        fv = bool(_get_field(file_data, field) or False)
        sv = bool(_get_field(server_data, field) or False)
        if fv != sv:
            return True
    return False


def _to_dict(obj):
    """Convert a model or SimpleNamespace to a dict."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(by_alias=False, exclude_none=True)
    return {k: v for k, v in vars(obj).items() if v is not None}


def _safe_int(value, default=0):
    """Convert to int, returning default if not numeric."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _scan_merge_images(seller_display_id, customer_catalog_id, item_id):
    """Scan images for a lot during merge, handling non-numeric IDs gracefully."""
    house = _safe_int(seller_display_id)
    cat = _safe_int(customer_catalog_id)
    lot = _safe_int(item_id)
    if house and cat and lot:
        return scan_lot_images(house, cat, lot)
    return []


def merge_catalog(request, bulk_request, catalog_id):
    """Merge file lots into an existing catalog.

    Compares file lots against server lots by customer_item_id:
    - New lots (file-only): created individually
    - Changed lots (dimensional fields differ): deleted and re-created, preserving overrides
    - Unchanged lots: skipped
    - Server-only lots: left untouched

    Returns dict with {added, updated, unchanged, failed, errors, catalog_id}.
    """
    # Fetch all server lots for this catalog
    customer_catalog_id = bulk_request["catalogs"][0]["customer_catalog_id"]
    server_lots = fetch_all_lots(request, customer_catalog_id)

    # Resolve seller display ID for recovery entries and redirect
    catalog_obj = get_catalog(request, catalog_id)
    seller_display_id = (
        catalog_obj.sellers[0].customer_display_id if catalog_obj.sellers else ""
    )

    # Build lookup: customer_item_id → LotDto
    server_map = {}
    for lot in server_lots:
        if lot.customer_item_id:
            server_map[lot.customer_item_id] = lot

    # Build file lots lookup — deduplicate, keep first occurrence only
    file_map = {}
    for catalog in bulk_request["catalogs"]:
        for lot in catalog["lots"]:
            item_id = lot["customer_item_id"]
            if item_id not in file_map:
                file_map[item_id] = SimpleNamespace(**lot)

    added = 0
    updated = 0
    unchanged = 0
    failed = 0
    errors = []

    for item_id, file_lot in file_map.items():
        server_lot = server_map.get(item_id)

        if server_lot is None:
            # New lot — create individually
            add_req = None
            try:
                image_links = _scan_merge_images(seller_display_id, customer_catalog_id, item_id)
                add_req = {
                    "customerItemId": file_lot.customer_item_id,
                    "imageLinks": image_links,
                    "initialData": _to_dict(file_lot.initial_data) if hasattr(file_lot.initial_data, "__dict__") else file_lot.initial_data,
                    "overridenData": [],
                    "catalogs": [
                        {
                            "catalogId": catalog_id,
                            "lotNumber": getattr(file_lot, "lot_number", ""),
                        }
                    ],
                }
                create_lot(request, add_req)
                added += 1
            except Exception as e:
                failed += 1
                errors.append(f"Failed to add lot {item_id}: {e}")
                logger.warning("Merge: failed to create lot %s: %s", item_id, e)
                cache_recovery_entry(
                    request,
                    {
                        "customer_item_id": item_id,
                        "lot_number": getattr(file_lot, "lot_number", ""),
                        "catalog_id": catalog_id,
                        "customer_catalog_id": customer_catalog_id,
                        "seller_display_id": seller_display_id,
                        "operation": "create",
                        "add_lot_request": add_req,
                        "error_message": str(e),
                        "timestamp": datetime.now(
                            tz=datetime.now().astimezone().tzinfo
                        ).isoformat(),
                    },
                )

        elif lots_differ(file_lot.initial_data, server_lot.initial_data):
            # Changed lot — delete and re-create, preserving overrides
            add_req = None
            try:
                saved_overrides = [
                    _to_dict(o) for o in (server_lot.overriden_data or [])
                ]
                delete_lot(request, server_lot.id)
                image_links = _scan_merge_images(seller_display_id, customer_catalog_id, item_id)
                add_req = {
                    "customerItemId": file_lot.customer_item_id,
                    "imageLinks": image_links,
                    "initialData": _to_dict(file_lot.initial_data) if hasattr(file_lot.initial_data, "__dict__") else file_lot.initial_data,
                    "overridenData": saved_overrides,
                    "catalogs": [
                        {
                            "catalogId": catalog_id,
                            "lotNumber": getattr(file_lot, "lot_number", ""),
                        }
                    ],
                }
                create_lot(request, add_req)
                updated += 1
            except Exception as e:
                failed += 1
                errors.append(f"Failed to update lot {item_id}: {e}")
                logger.warning("Merge: failed to update lot %s: %s", item_id, e)
                cache_recovery_entry(
                    request,
                    {
                        "customer_item_id": item_id,
                        "lot_number": getattr(file_lot, "lot_number", ""),
                        "catalog_id": catalog_id,
                        "customer_catalog_id": customer_catalog_id,
                        "seller_display_id": seller_display_id,
                        "operation": "update",
                        "add_lot_request": add_req,
                        "error_message": str(e),
                        "timestamp": datetime.now(
                            tz=datetime.now().astimezone().tzinfo
                        ).isoformat(),
                    },
                )

        else:
            # Identical — skip
            unchanged += 1

    # If every lot failed, this is a systemic failure — re-raise so the view returns 500
    if failed > 0 and added == 0 and updated == 0 and unchanged == 0:
        raise RuntimeError(
            f"All {failed} lots failed during merge. First error: {errors[0] if errors else 'unknown'}"
        )

    return {
        "added": added,
        "updated": updated,
        "unchanged": unchanged,
        "failed": failed,
        "errors": errors,
        "catalog_id": catalog_id,
        "customer_catalog_id": customer_catalog_id,
        "seller_display_id": seller_display_id,
    }


def search_lots(request, query, page=1, page_size=25):
    """Search lots by customer item ID and lot number, combining results."""
    api = get_catalog_api(request)

    by_item = _filtered_list(
        api.lots._client, "/Lot", "LotDto",
        pageNumber=page, pageSize=page_size, CustomerItemId=query,
    )
    by_lot_num = _filtered_list(
        api.lots._client, "/Lot", "LotDto",
        pageNumber=page, pageSize=page_size, LotNumber=query,
    )

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


# --- Image scanning ---


def scan_lot_images(house_id, catalog_id, lot_id):
    """Probe CDN URLs for a single lot to discover available images.

    Sends HTTP HEAD requests to sequential image positions starting at 1.
    Stops after 3 consecutive non-2xx responses or 200 positions.
    Returns list of verified image URLs.
    """
    valid_urls = []
    consecutive_failures = 0

    for n in range(1, IMAGE_SCAN_MAX_POSITIONS + 1):
        url = IMAGE_URL_TEMPLATE.format(
            house_id=house_id, catalog_id=catalog_id,
            lot_id=lot_id, n=n,
        )
        try:
            resp = requests.head(url, timeout=IMAGE_SCAN_TIMEOUT)
            if 200 <= resp.status_code < 300:
                valid_urls.append(url)
                consecutive_failures = 0
            else:
                consecutive_failures += 1
        except Exception:
            logger.warning("Image scan network error for %s", url)
            consecutive_failures += 1

        if consecutive_failures >= IMAGE_SCAN_CONSECUTIVE_FAILURES:
            break

    return valid_urls


def scan_images_for_catalog(lots, max_workers=IMAGE_SCAN_MAX_WORKERS):
    """Scan images for all lots in a catalog import, parallelized across lots.

    Args:
        lots: List of (house_id, catalog_id, lot_id) tuples.
        max_workers: Thread pool size.

    Returns:
        Dict mapping lot_id to list of verified image URLs.
    """
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_lot = {
            executor.submit(scan_lot_images, house, cat, lot): lot
            for house, cat, lot in lots
        }
        for future in as_completed(future_to_lot):
            lot_id = future_to_lot[future]
            try:
                results[lot_id] = future.result()
            except Exception:
                logger.warning("Image scan failed for lot %s", lot_id)
                results[lot_id] = []

    total_images = sum(len(urls) for urls in results.values())
    logger.info(
        "Image scan complete: %d lots, %d images found",
        len(results), total_images,
    )
    return results


# --- Recovery cache helpers ---


def _recovery_cache_key(request):
    return f"{request.session['abc_username']}:merge_recovery"


def cache_recovery_entry(request, entry_dict):
    """Append a failed lot entry to the user's recovery cache. Best-effort — won't break merge on failure."""
    try:
        key = _recovery_cache_key(request)
        raw = django_cache.get(key)
        entries = json.loads(raw) if raw else []
        entries.append(entry_dict)
        django_cache.set(key, json.dumps(entries), RECOVERY_CACHE_TTL)
    except Exception:
        logger.warning(
            "Failed to cache recovery entry for %s",
            entry_dict.get("customer_item_id", "?"),
        )


def get_recovery_entries(request):
    """Return the list of cached recovery entries for the current user, or empty list."""
    try:
        key = _recovery_cache_key(request)
        raw = django_cache.get(key)
        return json.loads(raw) if raw else []
    except Exception:
        logger.warning("Failed to read recovery cache")
        return []


def remove_recovery_entry(request, customer_item_id):
    """Remove a single entry by customer_item_id. Deletes the key if list becomes empty."""
    try:
        key = _recovery_cache_key(request)
        raw = django_cache.get(key)
        entries = json.loads(raw) if raw else []
        entries = [e for e in entries if e.get("customer_item_id") != customer_item_id]
        if entries:
            django_cache.set(key, json.dumps(entries), RECOVERY_CACHE_TTL)
        else:
            django_cache.delete(key)
    except Exception:
        logger.warning("Failed to remove recovery entry %s", customer_item_id)


def clear_recovery_entries(request):
    """Delete the entire recovery cache for the current user."""
    try:
        django_cache.delete(_recovery_cache_key(request))
    except Exception:
        logger.warning("Failed to clear recovery cache")


def resolve_item(request, customer_item_id):
    """Resolve a customer_item_id to its seller, event, and lot position.

    Returns a dict with keys: customer_item_id, lot_id, catalog_id,
    customer_catalog_id, seller_display_id, lot_position.
    Returns None if not found.
    """
    api = get_catalog_api(request)
    result = _filtered_list(
        api.lots._client, "/Lot", "LotDto",
        CustomerItemId=customer_item_id, pageSize=1,
    )
    if not result.items:
        return None
    lot = result.items[0]
    if not lot.catalogs:
        return None
    catalog_id = lot.catalogs[0].catalog_id
    catalog = get_catalog(request, catalog_id)
    seller_display_id = (
        catalog.sellers[0].customer_display_id if catalog.sellers else None
    )
    customer_catalog_id = catalog.customer_catalog_id

    # Compute lot_position: index in the event's embedded lots list
    lot_position = 0
    if hasattr(catalog, "lots") and catalog.lots:
        for i, lot_ref in enumerate(catalog.lots):
            if lot_ref.id == lot.id:
                lot_position = i
                break

    return {
        "customer_item_id": customer_item_id,
        "lot_id": lot.id,
        "catalog_id": catalog_id,
        "customer_catalog_id": customer_catalog_id,
        "seller_display_id": seller_display_id,
        "lot_position": lot_position,
    }

# SDK Interface Contract: lotsdb → AB SDK

**Date**: 2026-03-13

This contract defines the interface lotsdb requires from the AB SDK. Where the SDK does not provide an operation, the gap is noted and must appear in `external_deps.md`.

## Authentication

### login(request, username, password)

**Requirement**: Create an authenticated API session for a specific user within a Django request context.

```
Input:
  request: Django HttpRequest
  username: str (from login form)
  password: str (from login form)

Side effects:
  - Validates credentials against ABConnect identity server
  - Stores token in request.session["ab_token"]

Errors:
  - AuthenticationError: invalid credentials
  - ABConnectError: service unreachable

GAP: AB SDK reads credentials from env vars only. Constructor must accept
     optional username/password overrides for multi-user web apps.
```

### get_api(request)

**Requirement**: Return a cached, authenticated API client for the current request.

```
Input:
  request: Django HttpRequest (with session containing "ab_token")

Output:
  ABConnectAPI instance with .catalog, .lots, .sellers endpoints

Caching:
  One instance per request, stored on request._catalog_api
```

## Sellers

### sellers.list(page, page_size, **filters)

```
Input:
  page: int (1-indexed)
  page_size: int
  filters (optional):
    CustomerDisplayId: str
    Name: str
    IsActive: bool

Output:
  PaginatedList with:
    items: List[SellerDto]
    page_number: int
    total_pages: int
    total_items: int
    has_previous_page: bool
    has_next_page: bool

GAP: list() only accepts page/page_size. Filter kwargs not supported.
```

### sellers.get(seller_id)

```
Input: seller_id: int
Output: SellerExpandedDto (id, name, customer_display_id)
Status: Supported
```

## Catalogs

### catalog.list(page, page_size, **filters)

```
Input:
  page: int
  page_size: int
  filters (optional):
    SellerIds: int or List[int]
    CustomerCatalogId: str
    Title: str

Output: PaginatedList[CatalogExpandedDto]

GAP: list() only accepts page/page_size. Filter kwargs not supported.
```

### catalog.get(catalog_id)

```
Input: catalog_id: int
Output: CatalogExpandedDto (id, title, customer_catalog_id, start_date, sellers, lots)
Status: Supported
```

### catalog.bulk_insert(data)

```
Input: BulkInsertRequest | dict
  Old shape: { catalogs: [{ customer_catalog_id, agent, title, start_date, end_date, sellers: [...], lots: [...] }] }
  New shape: { catalog_id: int, items: [dict] }

GAP: Nested typed models (BulkInsertCatalogRequest, BulkInsertSellerRequest,
     BulkInsertLotRequest) not available. Must pass raw dicts.
```

## Lots

### lots.list(page, page_size, **filters)

```
Input:
  page: int
  page_size: int
  filters (optional):
    CustomerItemId: str
    LotNumber: str
    customer_catalog_id: str  ← CRITICAL for list_lots_by_catalog

Output: PaginatedList[LotDto]

GAP: list() only accepts page/page_size. Filter kwargs not supported.
     customer_catalog_id filter is especially critical — without it,
     there is no way to list lots for a specific catalog.
```

### lots.get(lot_id)

```
Input: lot_id: int
Output: LotDto (id, catalog_id, lot_number, customer_item_id, data, image_links, initial_data, overriden_data)
Status: Supported
```

### lots.create(data)

```
Input: AddLotRequest | dict
  Fields: catalog_id, lot_number, data (dict)

Note: Old AddLotRequest had additional fields (customer_item_id, image_links,
      initial_data, overriden_data, catalogs). New model only has catalog_id,
      lot_number, data. May need to pass as raw dict.

GAP: AddLotRequest model is missing fields used by lotsdb.
```

### lots.update(lot_id, data)

```
Input: lot_id: int, UpdateLotRequest | dict
Status: Supported (lot_number, data fields)
```

### lots.delete(lot_id)

```
Input: lot_id: int
Output: None
Status: Supported
```

## Exceptions

| Old Exception | New Exception | Notes |
|---------------|---------------|-------|
| LoginFailedError | AuthenticationError | Different name, same semantics |
| ABConnectError | ABConnectError | Same base class name |
| - | RequestError | New: includes status_code |
| - | ConfigurationError | New: missing env vars |

## Models

| Old Model | New Equivalent | Gap |
|-----------|---------------|-----|
| LotDataDto (13 fields) | LotDataDto (7 fields) | Missing 6 fields |
| BulkInsertRequest | BulkInsertRequest | Different structure |
| BulkInsertCatalogRequest | None | Missing |
| BulkInsertSellerRequest | None | Missing |
| BulkInsertLotRequest | None | Missing |
| LotCatalogDto | None | Missing |
| UpdateLotRequest | UpdateLotRequest | Supported |
| AddLotRequest | AddLotRequest | Missing fields |

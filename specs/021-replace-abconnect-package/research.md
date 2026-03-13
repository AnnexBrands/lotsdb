# Research: 021-replace-abconnect-package

**Date**: 2026-03-13

## Decision 1: Authentication Pattern

**Decision**: Document per-request credentials as an AB SDK gap; use temporary env-var override as interim workaround.

**Rationale**: The old SDK accepted `ABConnectAPI(request=request, username=username, password=password)` — credentials passed per-request from the login form. The new SDK reads credentials exclusively from environment variables (`ABCONNECT_USERNAME`, `ABCONNECT_PASSWORD`). Setting `os.environ` is process-global and not thread-safe for a multi-user web app. The correct fix is for the AB SDK to accept optional credential overrides in the constructor, but until that's available, the workaround is to mutate `api._settings.username` / `api._settings.password` post-construction (or pass credentials through a per-request mechanism). This must be documented in `external_deps.md` as a high-priority gap.

**Alternatives considered**:
- Temporary `.env` file per login: Rejected — filesystem race conditions, no concurrency safety
- Process-wide env var mutation: Rejected — thread-unsafe in gunicorn with threads
- Mutate settings object post-construction: Accepted as interim — settings is a Pydantic model, attributes can be overridden before first API call triggers auth

## Decision 2: Filter Parameters on List Endpoints

**Decision**: Document as AB SDK gap; pass filters as raw query params via workaround until SDK adds support.

**Rationale**: The new SDK's `list()` methods only accept `page` and `page_size`. Filter models (`CatalogListParams`, `LotListParams`, `SellerListParams`) exist in the SDK but are NOT wired into the endpoint methods. Lotsdb depends on filters for: `SellerIds` (catalog listing), `CustomerDisplayId` (seller lookup), `CustomerItemId` and `LotNumber` (lot search), `CustomerCatalogId` (catalog lookup), `customer_catalog_id` (lot-by-catalog listing). Without filter support, all list-based queries are broken. The workaround is to either extend the endpoint methods locally or access the underlying HTTP client to pass raw query params.

**Alternatives considered**:
- Client-side filtering (fetch all, filter in Python): Rejected — too slow for large datasets, wastes API bandwidth
- Monkey-patch endpoint methods: Rejected — fragile, breaks on SDK updates
- Subclass endpoints with filter support: Possible but complex; document gap and use raw HTTP workaround until SDK adds filter kwargs

## Decision 3: FileLoader Replacement

**Decision**: Inline file-loading logic in lotsdb using `openpyxl` (already a transitive dependency) and standard library `csv`/`json`.

**Rationale**: The old `FileLoader` uses `pandas`, `openpyxl`, `chardet`, and `BeautifulSoup` for multi-format reading with encoding detection. The new AB SDK has no equivalent. Rather than adding all those dependencies to lotsdb, we can use `openpyxl` directly for XLSX (our primary format) and stdlib for CSV/JSON. The current `CatalogDataBuilder` already handles all data transformation — only the raw file-to-list-of-dicts step needs replacement. Document `FileLoader` in `external_deps.md` for the SDK team.

**Alternatives considered**:
- Copy `FileLoader` into lotsdb: Rejected — drags in `pandas` + `chardet` + `beautifulsoup4` as new dependencies
- Add `pandas` as dependency: Rejected — heavyweight for a simple row-reading task
- Use `openpyxl` directly: Accepted — already available, handles XLSX which is the primary format

## Decision 4: BulkInsert Model Structure

**Decision**: Document nested model gaps in `external_deps.md`; use dict-based payloads with the new SDK's generic `BulkInsertRequest(items=list[dict])`.

**Rationale**: The old SDK provided typed nested models: `BulkInsertRequest` → `catalogs[]` → `BulkInsertCatalogRequest` (with `lots[]` and `sellers[]`). The new SDK has a flat `BulkInsertRequest(catalog_id, items=list[dict])`. The API backend likely still accepts the nested JSON structure — the SDK just doesn't model it. We can serialize the payload as dicts matching the old JSON schema and pass via `items`. The missing `LotDataDto` fields (cpack, notes, force_crate, etc.) can be included as raw dict keys since the API accepts them. Document all missing models and fields in `external_deps.md`.

**Alternatives considered**:
- Define custom Pydantic models in lotsdb: Rejected — duplicates SDK responsibility, creates drift risk
- Use only the 7 fields the new LotDataDto supports: Rejected — loses critical shipping data (cpack, force_crate, etc.)
- Pass raw dicts: Accepted — API accepts them, SDK's `items=list[dict]` is designed for this

## Decision 5: Image Scanner HTTP Method

**Decision**: Use HTTP HEAD requests for image probing.

**Rationale**: HEAD returns only headers (status code) without downloading the image body. This is ~10x faster than GET for image files (which can be 100KB-1MB each). The S3/CDN endpoint at `static2.liveauctioneers.com` supports HEAD requests. Fallback to GET if HEAD returns unexpected results (some CDNs return 403 for HEAD but 200 for GET).

**Alternatives considered**:
- GET requests: Rejected — downloads full image body unnecessarily
- HEAD with GET fallback: Considered — adds complexity for marginal benefit; if HEAD returns 4xx, count it

## Decision 6: Image Scanner Concurrency

**Decision**: Scan images per-lot sequentially (within a lot), but scan across lots in parallel using the existing ThreadPoolExecutor pattern.

**Rationale**: Within a single lot, images must be probed sequentially (position 1, 2, 3...) because the stop condition depends on consecutive failures. But across lots in a catalog, scanning is independent and can be parallelized. The existing `ThreadPoolExecutor` pattern used for concurrent lot fetching can be reused. For a 1000-lot catalog with ~4 probes each, parallel scanning across lots keeps total time manageable.

**Alternatives considered**:
- Fully sequential (one lot at a time): Rejected — too slow for large catalogs
- Async (aiohttp): Rejected — application uses synchronous Django, adding async adds complexity
- ThreadPoolExecutor across lots: Accepted — matches existing concurrency pattern

## Decision 7: Session Key Migration

**Decision**: Use the new SDK's session key `"ab_token"` and update all references from `"abc_token"`.

**Rationale**: The new SDK stores tokens under `request.session["ab_token"]` (constant in `ab/auth/session.py`). The old SDK used `"abc_token"`. The custom `"abc_username"` key set by lotsdb is unaffected and should remain for cache-key namespacing. All code that checks for `"abc_token"` must be updated to `"ab_token"`.

**Alternatives considered**:
- Configure new SDK to use old key: Not supported — key is a constant in the SDK
- Keep both keys: Rejected — confusing, stale data risk

## Decision 8: Accessor Path Change

**Decision**: Update `get_catalog_api()` to return the top-level `ABConnectAPI` instance instead of `.catalog`.

**Rationale**: Old pattern: `ABConnectAPI(request=request).catalog` returned a `CatalogAPI` sub-object, then callers used `api.sellers`, `api.catalogs`, `api.lots`. New pattern: `ABConnectAPI(request=request)` has `.catalog`, `.lots`, `.sellers` directly as top-level attributes. The cached object should be the top-level `ABConnectAPI`. Callers change from `api.sellers.list()` to `api.sellers.list()` (same), `api.catalogs.list()` to `api.catalog.list()` (singular), `api.bulk.insert()` to `api.catalog.bulk_insert()`.

**Alternatives considered**:
- Wrapper class mimicking old accessor pattern: Rejected — unnecessary indirection
- Direct attribute access: Accepted — cleaner, matches new SDK design

## Compatibility Gap Summary (for external_deps.md)

| # | Gap | Severity | Workaround |
|---|-----|----------|------------|
| 1 | Per-request credentials in constructor | Critical | Mutate settings post-construction |
| 2 | Filter kwargs on list endpoints | Critical | Raw query param passthrough or endpoint subclassing |
| 3 | FileLoader (file parsing utility) | Medium | Inline with openpyxl + stdlib |
| 4 | BulkInsertCatalogRequest, BulkInsertSellerRequest, BulkInsertLotRequest models | Medium | Pass raw dicts via items=list[dict] |
| 5 | LotDataDto missing fields (cpack, notes, force_crate, noted_conditions, do_not_tip, item_id, commodity_id) | Medium | Include in raw dicts, bypass model validation |
| 6 | LotCatalogDto model | Low | Use raw dict |
| 7 | LoginFailedError exception | Low | Map to AuthenticationError |

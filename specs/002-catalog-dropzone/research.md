# Research: Catalog Dropzone

## R1: Bulk Insert Return Value

**Decision**: The `BulkEndpoint.insert()` method returns `None`. The API returns 200 OK with no response body.

**Rationale**: The Catalog API's `POST /api/Bulk/insert` endpoint does not return created resource IDs. After insert, we must look up the created catalog by `CustomerCatalogId` using `api.catalogs.list(CustomerCatalogId=...)` to obtain the internal ID for redirection.

**Alternatives considered**: None - this is an API constraint, not a design choice.

## R2: Resolving Event ID After Import

**Decision**: After `bulk_insert()`, extract the `customer_catalog_id` from the parsed `BulkInsertRequest`, then call `services.list_catalogs()` with `CustomerCatalogId` filter to resolve the internal event ID. Use that ID to build the redirect URL `/events/<id>/`.

**Rationale**: The `CatalogEndpoint.list()` supports `CustomerCatalogId` as a query parameter (confirmed in Swagger). The `BulkInsertRequest.catalogs[0].customer_catalog_id` gives us the lookup key. If multiple catalogs are in the file, redirect to the first.

**Alternatives considered**:
- Redirect to import list page (simpler but doesn't meet spec requirement).
- Hardcode a search by title/date (fragile, race-condition prone).

## R3: Drag-and-Drop Upload Approach

**Decision**: Use a combination of HTML5 Drag & Drop API (JavaScript) for the drop interaction and a standard `fetch()` POST with `FormData` for the upload. The server endpoint returns JSON with either a redirect URL or an error message. Client-side JS handles redirection or toast display.

**Rationale**: HTMX supports file uploads via `hx-encoding="multipart/form-data"`, but drag-and-drop requires JavaScript event handlers regardless (`dragover`, `drop` events). Using `fetch()` for the upload keeps the flow simple and avoids mixing HTMX and manual JS in confusing ways. The response handling (redirect vs toast) is straightforward with `fetch()`.

**Alternatives considered**:
- Pure HTMX with `hx-post` and `HX-Redirect` headers: Would work for the upload, but drag-and-drop still requires JS. Mixing the two patterns adds complexity without benefit.
- Third-party dropzone library (Dropzone.js): Over-engineered for a single-file drop on a nav element.

## R4: Toast Notification Implementation

**Decision**: Add a lightweight client-side toast system using a fixed-position container in `base.html` and a small JS function `showToast(message, type)`. Toasts auto-dismiss after 5 seconds. This supplements (does not replace) the existing Django messages for page-reload scenarios.

**Rationale**: The existing Django messages framework requires a page reload to display. Since the dropzone operates via AJAX (no page reload on error), we need client-side toast capability. A minimal custom implementation (~20 lines of JS + CSS) avoids adding a dependency.

**Alternatives considered**:
- Using Django messages with HTMX swap: Would require a dedicated messages endpoint and partial template. More complex for the same result.
- Alpine.js toast library: Adds a new dependency for a trivial feature.

## R5: File Validation Strategy

**Decision**: Validate in two stages:
1. **Client-side**: Check file extension (.xlsx, .csv, .json) before upload. Reject immediately with toast.
2. **Server-side**: Call `load_file()` which raises exceptions for malformed data (missing required columns like "Catalog ID", "House ID"). Catch exceptions and return error JSON.

**Rationale**: Client-side extension check provides instant feedback. Server-side validation via the existing `load_file()` function reuses all existing parsing logic without duplication. The `CatalogDataBuilder.add_row()` will raise `KeyError` for missing required columns.

**Alternatives considered**:
- Server-only validation: Wastes a network round-trip for obviously wrong file types.
- Custom schema validation before `load_file()`: Duplicates logic already in the builder.

## R6: Uploaded File Handling

**Decision**: Process the uploaded file in-memory using Django's `request.FILES`. Pass the `UploadedFile` to a temporary file (via `tempfile.NamedTemporaryFile`) with the correct extension, then call `load_file()` on it. Clean up after processing.

**Rationale**: `ABConnect.FileLoader` expects a file path string, not a file object. A temporary file bridges the gap. The file is not persisted to `catalog/FILES/` since the user's requirement says "for now toast an error and disregard" invalid files — implying no persistent storage of uploads via this mechanism.

**Alternatives considered**:
- Saving to `catalog/FILES/` first: Adds unnecessary disk state and cleanup burden for a quick-import feature.
- Modifying `FileLoader` to accept file objects: Out of scope (external package).

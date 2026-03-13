# Feature Specification: Replace ABConnectTools with AB SDK

**Feature Branch**: `021-replace-abconnect-package`
**Created**: 2026-03-13
**Status**: Draft
**Input**: User description: "remove package abconnect and install its replacement, /usr/src/pkgs/AB. if the new package lacks compatibility, write external_deps.md with instructions for the maintainers of that package. ensure if we are hosting the code to build the bulk insert request we always begin with empty overrides and are scanning for lot images until three 4xx responses"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Migrate to New AB SDK (Priority: P1)

The application currently depends on ABConnectTools (imported as `ABConnect`) for all catalog API interactions — authentication, seller/catalog/lot CRUD, bulk insert, file parsing, and error handling. This package is being retired and replaced by the AB SDK (`ab`). All existing functionality must continue working identically after the swap: login, browsing sellers and events, viewing and editing lots, importing catalogs from spreadsheets, recovery flows, and caching.

**Why this priority**: Without this migration, the application cannot move forward. ABConnectTools is being deprecated. Every other story depends on the new package being integrated.

**Independent Test**: Can be fully tested by performing a complete workflow — login, browse sellers, open an event, view lots, edit a lot override, import a catalog file, and verify all operations succeed with the new SDK.

**Acceptance Scenarios**:

1. **Given** a user with valid credentials, **When** they log in, **Then** authentication succeeds and a session is established using the new SDK's auth mechanism
2. **Given** an authenticated user, **When** they list sellers, browse catalogs, or view lots, **Then** the data returned is identical to what ABConnectTools returned
3. **Given** any API error (auth failure, not found, server error), **When** the error is caught, **Then** the application handles it gracefully using the new SDK's exception hierarchy
4. **Given** a concurrent lot fetch (parallel requests), **When** multiple lots are fetched simultaneously, **Then** each thread uses its own API instance and results are correct

---

### User Story 2 - Bulk Insert Begins with Empty Overrides (Priority: P1)

When building a bulk insert request from an imported spreadsheet, the system currently duplicates the initial data into the override array. This is incorrect — new lots should always be inserted with empty overrides so the initial data stands as the baseline. Overrides should only exist when a user explicitly changes a value after import.

**Why this priority**: Incorrect override data on import pollutes the data model and makes it impossible to distinguish user-made changes from import defaults. This is a data integrity issue that affects downstream processing.

**Independent Test**: Import a catalog spreadsheet and inspect the resulting bulk insert request payload — each lot's override array must be empty.

**Acceptance Scenarios**:

1. **Given** a spreadsheet with lot data, **When** a bulk insert request is built, **Then** each lot's override data is empty (no pre-populated overrides)
2. **Given** a spreadsheet with lot data, **When** a bulk insert request is built, **Then** each lot's initial data contains the full dimensional and descriptive data from the spreadsheet
3. **Given** a previously imported lot, **When** a user later edits a dimension, **Then** only that user-made change appears in the override data

---

### User Story 3 - Scan for Lot Images Until Three Consecutive 4xx Responses (Priority: P2)

When building a bulk insert request or merging a catalog import, the system currently constructs a single image URL per lot using a template and assumes it exists. Instead, the system should probe (HTTP HEAD or GET) the image URL pattern to discover how many images actually exist for each lot. Image URLs follow a numbered suffix pattern (e.g., `_1_m.jpg`, `_2_m.jpg`, `_3_m.jpg`, ...). The system should keep probing sequential image numbers and stop after receiving three consecutive 4xx (client error) responses, treating those as "no more images exist."

**Why this priority**: Including non-existent image URLs wastes API resources and creates broken references. Scanning finds all real images and stops efficiently.

**Independent Test**: Import a catalog where lots have varying numbers of images (0, 1, 5, etc.) and verify the resulting image_links arrays contain only URLs that returned successful responses.

**Acceptance Scenarios**:

1. **Given** a lot with 3 images available on the CDN, **When** the bulk insert request is built, **Then** the lot's image_links contains exactly 3 valid URLs
2. **Given** a lot with no images on the CDN, **When** the image scanner probes the first URL and gets three consecutive 4xx responses, **Then** the lot's image_links is empty
3. **Given** a lot with images at positions 1-5, **When** the scanner encounters 4xx at positions 6, 7, and 8, **Then** scanning stops and only positions 1-5 are included
4. **Given** a lot where image at position 3 returns 4xx but positions 4 and 5 return 200, **When** scanning, **Then** positions 4 and 5 are still found because three *consecutive* 4xx responses have not yet occurred

---

### User Story 4 - Document Compatibility Gaps for AB SDK Maintainers (Priority: P2)

Where the new AB SDK lacks features that ABConnectTools provided, the project must document those gaps in an `external_deps.md` file. This file serves as a request to the AB SDK maintainers, describing what functionality is missing and what the lotsdb project needs. This avoids re-implementing SDK-level concerns inside the application.

**Why this priority**: Clear documentation of gaps accelerates the AB SDK maintainers' work and ensures nothing is silently dropped during migration.

**Independent Test**: Review external_deps.md and confirm each gap is documented with the missing capability, how it was used, and what the AB SDK would need to provide.

**Acceptance Scenarios**:

1. **Given** a feature present in ABConnectTools but absent from the AB SDK, **When** the migration is complete, **Then** external_deps.md documents that gap with a description of the needed capability
2. **Given** external_deps.md, **When** an AB SDK maintainer reads it, **Then** they can understand what to implement without needing access to the lotsdb codebase

---

### Edge Cases

- What happens when the image CDN is unreachable or returns server errors during scanning? The scanner should treat network errors and 5xx responses the same as 4xx for consecutive-failure counting purposes but log the error.
- What happens when a lot has hundreds of images? The scanner should have a reasonable upper bound (e.g., 200 images) to prevent unbounded probing.
- What happens when the AB SDK's authentication flow differs from ABConnectTools? The login bridge must adapt to the new auth mechanism or document the gap in external_deps.md.
- What happens when the AB SDK returns data in a slightly different shape (field names, nesting)? The service layer must map to the expected shape for views.
- What happens when the AB SDK's BulkInsertRequest model has a different structure (generic items list vs. nested catalogs/sellers/lots)? The import builder must adapt to the new structure or the gap must be documented.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace all ABConnectTools (`ABConnect`) imports with equivalent imports from the AB SDK (`ab`)
- **FR-002**: System MUST authenticate users through the AB SDK and bridge the result to Django's User model, preserving the existing login flow
- **FR-003**: System MUST perform seller, catalog, and lot CRUD operations using the AB SDK's endpoint methods with identical behavior to the current implementation
- **FR-004**: System MUST handle API errors using the AB SDK's exception hierarchy (`ABConnectError`, `AuthenticationError`, `RequestError`) in place of ABConnectTools' exceptions (`ABConnectError`, `LoginFailedError`)
- **FR-005**: System MUST build bulk insert requests with empty override data for all lots — initial data only, no pre-populated overrides
- **FR-006**: System MUST probe image URLs sequentially for each lot during both bulk insert request construction and merge catalog flows, collecting valid URLs and stopping after three consecutive 4xx responses
- **FR-007**: System MUST produce an `external_deps.md` file listing all ABConnectTools capabilities not present in the AB SDK, with descriptions sufficient for the SDK maintainers to implement them
- **FR-008**: System MUST remove the ABConnectTools package from the project's dependencies entirely — no residual imports or references
- **FR-009**: System MUST continue to support spreadsheet file loading (xlsx, csv, json) for catalog import, re-implementing or adapting any file-parsing logic that was provided by ABConnectTools' `FileLoader` if the AB SDK does not offer an equivalent
- **FR-010**: System MUST preserve thread-safe concurrent lot fetching behavior using per-thread API instances from the new SDK

### Key Entities

- **AB SDK Client** (`ABConnectAPI`): The replacement API client providing catalog, lots, and sellers endpoints plus authentication
- **BulkInsertRequest**: The payload structure for batch lot creation — now requires empty overrides and validated image links
- **Image Scanner**: A new capability that probes CDN URLs to discover actual lot images before including them in the bulk insert payload
- **external_deps.md**: A document listing SDK capability gaps for the AB package maintainers

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing application workflows (login, browse, edit, import, recovery) function identically after migration — zero regressions
- **SC-002**: No references to ABConnectTools or the `ABConnect` package remain in the codebase after migration
- **SC-003**: Bulk insert payloads contain zero pre-populated overrides for newly imported lots
- **SC-004**: Image scanning correctly identifies all available lot images and includes only verified URLs in the bulk insert request
- **SC-005**: Image scanning stops within three probes after the last valid image, avoiding unnecessary network requests
- **SC-006**: external_deps.md is present and documents every identified compatibility gap with actionable descriptions
- **SC-007**: All existing tests pass after migration with updated mocks/fixtures reflecting the new SDK

## Clarifications

### Session 2026-03-13

- Q: Should image scanning apply to bulk insert only, or also the merge catalog flow? → A: Both flows — scan images during bulk insert AND merge catalog
- Q: Should 5xx server errors count toward the 3-consecutive-failure threshold or be retried? → A: Count 5xx the same as 4xx (no retry)

## Assumptions

- The AB SDK at `/usr/src/pkgs/AB` is installable as an editable package (like ABConnectTools was)
- The AB SDK's authentication mechanism supports Django session-based token storage (the `SessionTokenStorage` in the SDK's auth module)
- The image CDN URL pattern (`https://s3.amazonaws.com/static2.liveauctioneers.com/{house_id}/{catalog_id}/{lot_id}_{n}_m.jpg`) remains unchanged — only the probing behavior changes
- The AB SDK's `BulkInsertRequest` model (with `catalog_id` and generic `items` list) can represent the same nested catalog/seller/lot structure, or the gap will be documented in external_deps.md
- "Three 4xx responses" means three *consecutive* 4xx HTTP status codes, not three total across all images

# Feature Specification: Import Hardening

**Feature Branch**: `020-import-hardening`
**Created**: 2026-02-17
**Status**: Draft
**Input**: PR #21 review findings — data loss recovery, retry UI, item search, deep-link redirect, UX polish fixes

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Merge Recovery Dashboard (Priority: P1)

When a catalog merge encounters lot-level failures (create fails after delete, or create fails for new lot), the system caches the failed lot payloads and surfaces a recovery page. The user can see every failed lot in a table, inspect the failure reason, check whether the item already exists on the server, and retry the operation with detailed per-item feedback.

**Why this priority**: The current delete-then-create update path can permanently lose lot data if `create_lot` fails after `delete_lot` succeeds. This is the highest-severity issue in the PR review. Recovery must exist before the merge feature is safe for production use.

**Independent Test**: Trigger a merge where one or more lots fail the create step. Navigate to the recovery page. See the failed lots listed with error details. Click "Check server" to verify current state. Click "Retry" to re-attempt the create. Observe success or detailed error feedback per item.

**Acceptance Scenarios**:

1. **Given** a merge where 2 of 5 lots fail during create, **When** the merge completes, **Then** the 2 failed lot payloads are cached with their full payload data and error message, and the merge response includes a link to the recovery page.
2. **Given** the recovery page with 2 cached failed lots, **When** the user views the page, **Then** a table displays each lot's customer item ID, lot number, failure reason, and action buttons.
3. **Given** a failed lot on the recovery page, **When** the user clicks "Check Server", **Then** the system queries for that customer item ID and displays whether the lot exists on the server (with current data summary) or is missing.
4. **Given** a failed lot that is missing from the server, **When** the user clicks "Retry", **Then** the system re-attempts the create operation and displays success (row turns green, removed from retry queue) or detailed error (row turns red with full error message).
5. **Given** a failed lot that already exists on the server (e.g., a previous retry succeeded), **When** the user clicks "Retry", **Then** the system warns "Item already exists on server" and offers to skip or force-update.
6. **Given** all failed lots are successfully retried or skipped, **When** the recovery queue is empty, **Then** the page shows an "All items recovered" message and a link to navigate to the catalog.

---

### User Story 2 - Search by Customer Item ID (Priority: P1)

A search input in the navbar lets users find any lot by customer item ID and navigate directly to it. The result deep-links to the correct seller, event, pagination page, and highlights the specific lot row.

**Why this priority**: This is a general-purpose navigation feature that supports the recovery workflow (jump to a specific lot to verify it) and is independently valuable for daily use. It also DRYs up the "find item" pattern needed by the recovery page.

**Independent Test**: Type a customer item ID into the navbar search. The system locates the lot, determines its seller and event, and redirects to the correct deep-link URL. The page loads with the correct seller selected, event selected, lot table paginated to the correct page, and the lot row visually highlighted.

**Acceptance Scenarios**:

1. **Given** a valid customer item ID that exists on the server, **When** the user enters it in the navbar search and submits, **Then** the system redirects to a URL with seller, event, and item parameters.
2. **Given** the deep-link URL with an item parameter, **When** the page loads, **Then** the seller panel shows the correct seller selected, the events panel shows the correct event selected, the lots table shows the page containing that lot, and the lot row has an active/highlighted style.
3. **Given** a customer item ID that does not exist on the server, **When** the user searches for it, **Then** a toast message says "Item not found" and the page remains unchanged.
4. **Given** a lot that is on page 3 of the lots table (items 51-75 of 100), **When** the deep-link loads, **Then** the lots table automatically shows page 3 with the correct lot highlighted.

---

### User Story 3 - Upload UX Polish (Priority: P2)

Fix the upload/merge user experience issues identified in the PR review: toast-redirect race condition, 100%-failure detection, file size limit, deep-link redirect after import, and dropzone visual feedback.

**Why this priority**: These are medium-severity UX issues that affect usability but don't cause data loss. They should be fixed alongside the P1 stories.

**Independent Test**: Upload a catalog file (new or existing). Observe the toast is visible for a meaningful duration before redirect. The redirect lands on the correct seller+event page. Uploading a file over the size limit shows a clear error. A merge where all lots fail shows an error, not a success message.

**Acceptance Scenarios**:

1. **Given** a successful new catalog import, **When** the upload completes, **Then** the user is redirected to the deep-linked seller+event page (not bare home page).
2. **Given** a successful merge, **When** the merge completes, **Then** the merge summary toast is visible on the destination page (persisted across navigation), and the redirect lands on the correct seller+event.
3. **Given** a merge where 100% of lots fail, **When** the merge response arrives, **Then** the system treats it as an error (not success) and shows an error toast with a link to the recovery page.
4. **Given** a file larger than the maximum allowed size, **When** the user drops it on the dropzone, **Then** an error toast appears with the size limit and the upload is not attempted.
5. **Given** the dropzone, **When** the user hovers a file over it, **Then** the dropzone visually grows/animates to indicate it is a valid drop target. During upload, an animated progress indicator is shown.

---

### User Story 4 - Lots Table Bug Fixes (Priority: P2)

Fix the lots-table editing bugs found during UAT: inline values not persisting, DNT not persisting, cpack missing override indicator, and events panel regression after save.

**Why this priority**: These are real bugs that prevent effective use of the lots table. They were found during 019 UAT and need to be resolved.

**Independent Test**: Edit a lot's dimensions inline and click save — values persist on reload. Toggle DNT in the modal — persists on reload. Edit cpack in the modal — orange "original value" indicator appears. After saving a lot, the events panel still shows past events.

**Acceptance Scenarios**:

1. **Given** a lot in the lots table, **When** the user changes a dimension value inline and clicks save, **Then** the new value persists when the page is refreshed.
2. **Given** a lot in the modal editor, **When** the user toggles Do Not Tip and saves, **Then** the DNT state persists on reload.
3. **Given** a lot with an overridden cpack value, **When** viewing it in the modal, **Then** the cpack field shows the orange "original value" indicator like dimensions and weight already have.
4. **Given** the lots table with an events panel showing past and future events, **When** the user saves a lot override, **Then** the events panel still shows both past and future events (no regression).

---

### Edge Cases

- What happens when the cache backend is unavailable during a failed merge? The merge still completes (best-effort), but failed lots are logged to the application log instead of cached. A warning indicates recovery data could not be saved.
- What happens when a recovery cache entry expires? Entries expire after 24 hours. The recovery page shows "No pending recoveries" if the cache is empty.
- What happens when two users import the same catalog simultaneously? Each merge operates independently. Recovery caches are namespaced by user.
- What happens when the search finds a lot that belongs to multiple catalogs? The search returns the first match and deep-links to its primary catalog.
- What happens when the item is on the last page and page size changes? The deep-link computes the correct page based on the lot's position in the embedded lots list for the event.

## Requirements *(mandatory)*

### Functional Requirements

#### Merge Recovery

- **FR-001**: System MUST cache failed lot payloads (full create-request data, error message, timestamp) when individual lot operations fail during merge.
- **FR-002**: System MUST provide a dedicated recovery page listing all cached failed lots for the current user, showing customer item ID, lot number, error reason, and action buttons.
- **FR-003**: System MUST allow the user to check the current server state of a failed lot by customer item ID before retrying (query and display whether the lot exists).
- **FR-004**: System MUST allow the user to retry a failed lot create operation from the recovery page, with real-time success/failure feedback per item.
- **FR-005**: System MUST detect when a retry target already exists on the server and warn the user before proceeding.
- **FR-006**: Recovery cache entries MUST be namespaced by user and expire after 24 hours.
- **FR-007**: System MUST include a link to the recovery page in the merge response when any lots fail. This is the primary discovery mechanism; no persistent navbar element is provided (users may bookmark the URL).

#### Item Search

- **FR-008**: System MUST provide a search input in the navbar that accepts a customer item ID.
- **FR-009**: System MUST resolve a customer item ID to its seller, event, and lot position.
- **FR-010**: System MUST redirect to a deep-link URL with seller, event, and item parameters on successful search.
- **FR-011**: System MUST display a "not found" toast when the searched item ID does not exist.

#### Deep-Link with Item Selection

- **FR-012**: System MUST support an item query parameter that selects and highlights a specific lot row.
- **FR-013**: When the item parameter is present, system MUST compute the correct pagination page containing that lot and display that page.
- **FR-014**: The selected lot row MUST have a distinct visual highlight (active style) that distinguishes it from other rows.

#### Upload UX Polish

- **FR-015**: After a successful import or merge, system MUST redirect to the deep-link URL for the imported catalog (seller+event), not the bare home page.
- **FR-016**: Merge summary toast MUST be visible on the destination page after redirect (persisted across page navigation).
- **FR-017**: When 100% of lots fail during merge, system MUST treat the response as an error, not a success.
- **FR-018**: System MUST enforce a maximum upload file size of 1 MB and reject oversized files with a clear error message before upload begins.
- **FR-019**: Dropzone MUST provide animated hover feedback and upload-in-progress indication.

#### Lots Table Bug Fixes

- **FR-020**: Inline lot override saves MUST persist values correctly on page refresh.
- **FR-021**: Do Not Tip toggle MUST persist when saved from the table or modal (correct field name casing must match the API contract).
- **FR-022**: The cpack field MUST display the orange "original value" indicator when overridden, matching dimensions and weight behavior.
- **FR-023**: Saving a lot override MUST NOT cause the events panel to drop past events (the events re-render must include all events).

#### Code Cleanup

- **FR-024**: Dead code (unused result fetch after bulk insert) MUST be removed.
- **FR-025**: Blanket exception handling in the merge loop MUST re-raise when the failure rate is 100% (systemic failure detection).
- **FR-026**: Dropzone CSS MUST be reformatted to multi-line style matching the rest of the stylesheet.
- **FR-027**: Repeated anonymous mock pattern in dropzone UI tests MUST be extracted to a shared fixture.

### Key Entities

- **Recovery Entry**: A cached record of a failed lot operation — contains the full lot payload, error message, timestamp, user identifier, and catalog context (seller ID, event ID, customer catalog ID).
- **Item Search Result**: The resolved mapping from a customer item ID to its seller display ID, event catalog ID, and lot position within the event's lot list.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero lots are permanently lost during merge — all failed lots are recoverable via the recovery page within 24 hours.
- **SC-002**: Users can locate any lot by customer item ID and navigate to it in under 5 seconds.
- **SC-003**: After catalog import, users land directly on the imported catalog page (not the home page).
- **SC-004**: Merge summary toast is visible for at least 3 seconds on the destination page.
- **SC-005**: All lots table inline and modal edits persist correctly across page refresh, including DNT and cpack.
- **SC-006**: Events panel consistently shows both past and future events after any save operation.

## Clarifications

### Session 2026-02-17

- Q: How does the user navigate to the recovery page outside of the merge response link? → A: No navbar element. Recovery page is accessed via the merge response link or direct URL/bookmark only.
- Q: What is the maximum upload file size (FR-018)? → A: 1 MB (typical catalog file is ~75 KB).

## Assumptions

- A cache backend is already available in the deployment (confirmed: redis 7.1.1 is in the stack from feature 018).
- The API can resolve a customer item ID to its lot, catalog, and seller context (via existing search or list endpoints).
- The 24-hour TTL for recovery cache entries is sufficient — users will address failures within a working day.
- The recovery retry path uses the lot create operation (same as the original merge). Replacing delete-then-create with update-in-place is deferred per PR review.
- The Do Not Tip field casing issue is a field name mismatch — the fix is to use the correct name from the API schema.

## Out of Scope

- Replacing the delete-then-create merge strategy with update-in-place (deferred per PR review — separate feature).
- Batch retry (retrying all failed lots at once) — initial version retries one at a time for safety.
- Search autocomplete or fuzzy matching — search is exact customer item ID only.
- `_to_dict` with `exclude_none=True` behavior change (noted as minor, not actionable until API behavior changes).

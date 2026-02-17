# Feature Specification: Restore Catalog Import with Merge

**Feature Branch**: `019-restore-catalog-import`
**Created**: 2026-02-16
**Status**: Draft
**Input**: User description: "Restore the import/dropzone from 002-catalog-dropzone. Add merge-on-existing: before upload, check if catalog already exists; if so, compute set difference between file and server data. New lots are inserted, changed lots are deleted and re-posted preserving overrides."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import New Catalog via Dropzone (Priority: P1)

As a catalog manager, I want to drag and drop a catalog file onto an "Add Catalog" dropzone in the navigation bar so that I can quickly import a new catalog without navigating away from my current page. When the file is valid and the catalog does not yet exist on the server, all lots are bulk-inserted and I am redirected to the newly created event page.

**Why this priority**: This is the core import path — without it, the merge story has no entry point. Restores the primary workflow removed during the UX overhaul.

**Independent Test**: Drag a valid .xlsx file with a new (non-existing) customer catalog ID onto the dropzone. Verify bulk insert succeeds and the browser redirects to the event page.

**Acceptance Scenarios**:

1. **Given** I am on any authenticated page, **When** I look at the navigation bar, **Then** I see an "Add Catalog" dropzone element.
2. **Given** I drag a file over the dropzone, **When** the file hovers over the target, **Then** the dropzone shows a visual active/highlight state.
3. **Given** I drop a valid catalog file (.xlsx, .csv, or .json) with a customer catalog ID that does not exist on the server, **When** the file is processed, **Then** all lots are bulk-inserted and I am redirected to the created event page.
4. **Given** I drop a file with an unsupported extension, **When** I release the file, **Then** I see a toast error message and the file is disregarded.
5. **Given** I drop a file that fails parsing (missing required columns, empty data), **When** the file is processed, **Then** I see a toast error message describing the failure.
6. **Given** the server returns an error during bulk insert, **When** the file is processed, **Then** I see a toast error message and I remain on my current page.

---

### User Story 2 - Merge into Existing Catalog (Priority: P1)

As a catalog manager, I want the system to detect when a dropped catalog file matches an existing catalog on the server and automatically merge the differences rather than failing or creating duplicates. New lots from the file are added, lots that have changed are updated (deleted and re-created with the file's data), and any user-applied overrides on changed lots are preserved. Lots on the server that are not in the file are left untouched.

**Why this priority**: Equal to P1 because re-importing updated spreadsheets for existing catalogs is the primary real-world use case. Without merge, users must manually reconcile differences.

**Independent Test**: Import a catalog file for a catalog that already exists on the server with some overlapping lots. Verify that new lots appear, changed lots are updated with file data but retain their overrides, and unchanged lots remain as-is.

**Acceptance Scenarios**:

1. **Given** I drop a valid catalog file whose customer catalog ID matches an existing catalog on the server, **When** the file is processed, **Then** the system compares file lots against server lots by customer item ID.
2. **Given** the file contains lots with customer item IDs not present on the server, **When** the merge runs, **Then** those lots are inserted as new lots.
3. **Given** the file contains lots with customer item IDs that already exist on the server and the dimensional/shipping fields (qty, length, width, height, weight, container pack, force crate) differ from the server's initial data, **When** the merge runs, **Then** the existing lot is deleted and re-created with the file's data.
4. **Given** a lot is deleted and re-created during merge, **When** the original lot had user-applied overrides, **Then** those overrides are preserved and applied to the newly created lot.
5. **Given** the file contains lots where all dimensional/shipping fields match the server's initial data, **When** the merge runs, **Then** those lots are left unchanged (no delete/re-create).
6. **Given** the server has lots that are not present in the file, **When** the merge runs, **Then** those lots are left untouched.
7. **Given** the merge completes successfully, **When** processing finishes, **Then** I am redirected to the existing event page and see a summary toast indicating how many lots were added, updated, and unchanged.

---

### Edge Cases

- What happens when the file contains duplicate customer item IDs? Process only the first occurrence; ignore subsequent duplicates.
- What happens when override preservation fails for a specific lot (e.g., the re-created lot ID changes)? Log the failure, continue with remaining lots, and include a warning in the summary toast.
- What happens when the user drops multiple files at once? Only process the first file; ignore the rest.
- What happens when a delete+re-create fails for an individual lot during merge? The system skips the failed lot, continues processing remaining lots, and includes the failure count in the summary toast.
- What happens when the initial server lot fetch fails before merge begins? Abort the merge, display a toast error, and leave the catalog unmodified.
- What happens when the file is empty or has zero data rows? Toast an error: file contains no data.
- What if the user is not authenticated? The existing LoginRequiredMiddleware redirects to login.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display an "Add Catalog" dropzone element in the top navigation bar on all authenticated pages.
- **FR-002**: System MUST accept file drops of .xlsx, .csv, and .json files matching the existing catalog import structure.
- **FR-003**: System MUST reject files with unsupported extensions with a toast error message.
- **FR-004**: System MUST parse dropped files using the existing `load_file` importer.
- **FR-005**: System MUST display a toast error and disregard the file when parsing fails (structure mismatch, missing columns, empty data).
- **FR-006**: System MUST check whether the catalog already exists on the server (by customer catalog ID) before deciding the import strategy.
- **FR-007**: When the catalog does not exist, system MUST perform a bulk insert of all lots and redirect to the created event page.
- **FR-008**: When the catalog already exists, system MUST fetch all existing lots for that catalog from the server.
- **FR-009**: System MUST compute the set difference between file lots and server lots using customer item ID as the matching key.
- **FR-010**: For lots present in the file but not on the server, system MUST insert them individually as new lots (one at a time, not via bulk insert).
- **FR-011**: For lots present in both file and server where the file's dimensional/shipping fields (qty, length, width, height, weight, container pack, force crate) differ from the server lot's initial data, system MUST delete the server lot and re-create it with the file data.
- **FR-012**: When deleting and re-creating a lot, system MUST preserve any existing override data from the original lot and apply it to the newly created lot.
- **FR-013**: For lots present in both file and server where the dimensional/shipping fields are identical, system MUST leave them unchanged. Non-dimensional fields (description, notes, images) are not compared for change detection.
- **FR-014**: For lots present on the server but not in the file, system MUST leave them unchanged.
- **FR-015**: System MUST display a summary toast after merge indicating counts of lots added, updated, unchanged, and failed (if any).
- **FR-016**: System MUST provide visual feedback (loading state) during file processing, including during the potentially longer merge operation.
- **FR-017**: System MUST display a toast error when any server operation fails during import or merge.
- **FR-018**: System MUST allow click-to-browse as an alternative to drag-and-drop for file selection.

### Key Entities

- **Uploaded File**: A temporary file uploaded via the dropzone. Not persisted beyond request handling.
- **Event (Catalog)**: The catalog entity identified by customer catalog ID. After import, the user is directed to its detail page.
- **Lot**: Individual item within a catalog, identified by customer item ID. Has initial data (set at creation) and optional override data (user modifications).
- **Override Data**: User-applied modifications to lot fields (dimensions, descriptions, shipping parameters). Must survive lot re-creation during merge.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can import a new catalog file via drag-and-drop in under 15 seconds (excluding server processing time).
- **SC-002**: Invalid files produce a visible error toast within 3 seconds.
- **SC-003**: Successful new-catalog imports redirect to the correct event page without manual navigation.
- **SC-004**: Merge operations correctly preserve 100% of existing override data on re-created lots.
- **SC-005**: After a merge, the lot count on the event page reflects all file lots plus any server-only lots, with no duplicates.
- **SC-006**: The summary toast after merge accurately reports the number of lots added, updated, and unchanged.
- **SC-007**: The dropzone is discoverable and accessible from every authenticated page.

## Clarifications

### Session 2026-02-16

- Q: Which fields are compared to determine if a lot has "changed" between file and server? → A: Compare only dimensional/shipping fields (qty, length, width, height, weight, container pack, force crate) from the file against the server lot's initial_data. Non-dimensional fields (description, notes, images) are not used for change detection.
- Q: What happens if a delete+re-create fails for an individual lot during merge? → A: Best-effort — skip the failed lot, continue processing remaining lots, and report failure count in the summary toast.
- Q: How are new lots inserted during merge into an existing catalog? → A: Individual lot creation via the single-lot POST endpoint (one at a time). Bulk insert is only used for the new-catalog path.

## Assumptions

- The customer item ID is a reliable unique key for matching lots between file and server within a given catalog.
- The existing `load_file()` importer output structure is stable and does not need modification.
- Override data on a lot is contained in the `overriden_data` list (typically a single entry) and can be read before deletion and re-applied after re-creation.
- Lot deletion via the API is immediate and does not have cascading side effects beyond removing the lot record.
- During merge, new lots are inserted individually via the single-lot creation endpoint (not via bulk insert). Bulk insert is only used for the new-catalog path (US1).

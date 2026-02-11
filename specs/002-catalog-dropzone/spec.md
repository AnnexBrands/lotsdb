# Feature Specification: Catalog Dropzone

**Feature Branch**: `002-catalog-dropzone`
**Created**: 2026-02-10
**Status**: Implemented
**Input**: User description: "Add a file dropzone onto the top nav labeled Add Catalog. For now toast an error and disregard if it does not match our current file structure. On success redirect to the created event page."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Drop File to Import Catalog (Priority: P1)

As a catalog manager, I want to drag and drop a catalog file onto an "Add Catalog" dropzone in the navigation bar so that I can quickly import a new catalog without navigating to the Import page. When the file is valid and imports successfully, I am redirected to the newly created event page. When the file is invalid or fails, I see a toast error message and remain on my current page.

**Why this priority**: This is the only story in the feature. It provides a streamlined shortcut for the most common import workflow.

**Independent Test**: Can be tested by dragging a valid catalog file (.xlsx/.csv/.json) onto the navbar dropzone, verifying the import succeeds, and confirming redirection to the event detail page. Then repeat with an invalid file and verify a toast error appears.

**Acceptance Scenarios**:

1. **Given** I am on any page, **When** I see the navigation bar, **Then** I see an "Add Catalog" dropzone element.
2. **Given** I am on any page, **When** I drag a file over the "Add Catalog" area, **Then** I see a visual indicator that the drop target is active.
3. **Given** I have dragged a valid catalog file (.xlsx, .csv, or .json) onto the dropzone, **When** the file is processed, **Then** the catalog is imported and I am redirected to the created event page.
4. **Given** I have dragged a file that does not match the expected column structure, **When** the file is processed, **Then** I see a toast error message describing the failure and I remain on my current page.
5. **Given** I have dragged an unsupported file type (not .xlsx, .csv, or .json), **When** I drop it, **Then** I see a toast error message and the file is disregarded.
6. **Given** the API returns an error during bulk insert, **When** the file is processed, **Then** I see a toast error message and I remain on my current page.

---

### Edge Cases

- What happens when the uploaded file contains multiple catalogs? Redirect to the first created event page.
- What happens when the file is empty or has zero data rows? Toast an error: file contains no data.
- What happens when the user drops multiple files at once? Only process the first file; ignore the rest.
- What if the user is not authenticated when dropping? The existing LoginRequiredMiddleware will redirect to login.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display an "Add Catalog" dropzone element in the top navigation bar on all authenticated pages.
- **FR-002**: System MUST accept file drops of .xlsx, .csv, and .json files matching the existing catalog import structure.
- **FR-003**: System MUST reject files with unsupported extensions with a toast error message.
- **FR-004**: System MUST attempt to parse dropped files using the existing `load_file` importer.
- **FR-005**: System MUST display a toast error and disregard the file when parsing fails (structure mismatch, missing required columns, empty data).
- **FR-006**: System MUST call the bulk insert API on successful parse and redirect to the created event page on success.
- **FR-007**: System MUST display a toast error when the bulk insert API call fails.
- **FR-008**: System MUST provide visual feedback during file upload and processing (loading state).

### Key Entities

- **Uploaded File**: A temporary file uploaded via the dropzone. Not persisted to disk beyond request handling.
- **Event (Catalog)**: The existing catalog entity. After successful import, the user is redirected to its detail page at `/events/<event_id>/`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can import a catalog file via drag-and-drop in under 10 seconds (excluding processing time).
- **SC-002**: Invalid files produce a visible error toast within 3 seconds.
- **SC-003**: Successful imports redirect to the correct event page without manual navigation.
- **SC-004**: The dropzone is discoverable and accessible from every authenticated page.

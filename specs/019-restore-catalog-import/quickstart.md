# Quickstart: Restore Catalog Import with Merge

**Feature**: 019-restore-catalog-import | **Date**: 2026-02-16

## Prerequisites

- Dev server running: `cd src && ../.venv/bin/python manage.py runserver`
- Logged in as an authenticated user
- A valid catalog spreadsheet (.xlsx, .csv, or .json) with the expected column structure

## Manual Test: New Catalog Import (US1)

1. Open any page in the application (e.g., the home page)
2. Locate the "Add Catalog" dropzone in the navigation bar
3. Drag a valid `.xlsx` file with a **new** customer catalog ID onto the dropzone
4. **Expected**: Loading state appears on the dropzone
5. **Expected**: Browser redirects to the newly created event page at `/events/<id>/`
6. Verify the event page shows all lots from the file

### Error Cases

- Drop a `.txt` file → toast error: "Unsupported file type"
- Drop a `.xlsx` with invalid columns → toast error describing the parse failure
- Drop an empty `.xlsx` → toast error: "File contains no catalog data"

## Manual Test: Merge into Existing Catalog (US2)

1. Import a catalog file first using the steps above (to create the catalog on the server)
2. Modify the spreadsheet: change some lot dimensions, add new lots, leave some unchanged
3. Drop the modified file onto the dropzone
4. **Expected**: Loading state appears (may take longer than new import)
5. **Expected**: Browser redirects to the existing event page
6. **Expected**: Summary toast appears showing "Added: X, Updated: Y, Unchanged: Z"
7. Verify on the event page:
   - New lots appear in the lots table
   - Changed lots show the new dimensional data in their initial data
   - Changed lots still have their overrides intact (if any were set before)
   - Unchanged lots are unmodified

### Alternative: Click to Browse

1. Click the "Add Catalog" dropzone (instead of dragging)
2. A file browser dialog should open
3. Select a catalog file
4. Same behavior as drag-and-drop

## Automated Tests

```bash
cd /usr/src/lotsdb
.venv/bin/python -m pytest tests/ -v
```

### Expected Test Coverage

- **Contract tests** (`tests/contract/test_upload.py`):
  - POST with no file → error JSON
  - POST with unsupported extension → error JSON
  - POST with valid file (new catalog) → success JSON with redirect
  - POST with valid file (existing catalog) → success JSON with merge summary
  - POST with file parse failure → error JSON

- **Unit tests** (`tests/unit/test_merge.py`):
  - Merge diff computation: new lots, changed lots, unchanged lots
  - Override preservation during delete+recreate
  - Best-effort: skip on individual lot failure
  - Duplicate customer item ID deduplication
  - Field comparison normalization (None vs 0)

- **Integration tests** (`tests/integration/test_dropzone_ui.py`):
  - Dropzone element present in navbar
  - File input with correct accept attribute
  - Toast container present
  - Upload JS wired to correct endpoint

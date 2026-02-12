# Quickstart: Lot Detail Modal

**Feature**: 007-lot-detail-modal | **Date**: 2026-02-11

## Prerequisites

- Python 3.14 with virtual environment
- ABConnectTools 0.2.1 (editable install)
- Django 5 dev server running

## Setup

```bash
cd /usr/src/lotsdb/src
pip install -e ../requirements.txt  # if not already installed
python manage.py runserver
```

## Manual Test Steps

### 1. View Lot Detail Modal

1. Navigate to `http://localhost:8000/`
2. Click a seller in the left panel
3. Click an event in the middle panel → lots table loads
4. Click a lot's thumbnail image (or view icon) in the lots table
5. **Expected**: A modal overlay appears with:
   - Lot number and customer item ID in the header
   - Field table showing all 13 fields with initial values
   - Override column with changed fields highlighted (yellow background) if overrides exist
   - Lot images displayed below the field table (if present)
   - An "Edit Override" button
   - An X close button in the top-right corner

### 2. Close Modal

1. With the modal open, try each close method:
   - Click the X button → modal closes
   - Re-open modal, click the backdrop (dark area outside modal) → modal closes
   - Re-open modal, press Escape → modal closes
2. **Expected**: After closing, the SPA shell state is unchanged (same seller, event, lots visible)

### 3. Edit Override from Modal

1. Open a lot detail modal (step 1 above)
2. Click "Edit Override" button
3. **Expected**: Modal content switches to an editable form with all 13 fields pre-populated
4. Change a field value (e.g., update the description)
5. Click "Save Override"
6. **Expected**:
   - Modal closes
   - The lot's row in the table updates to reflect the new override
   - Overridden cells show yellow background with tooltip showing original value
   - A success toast appears briefly in the top-right corner

### 4. Cancel Override Edit

1. Open a lot detail modal, click "Edit Override"
2. Click "Cancel"
3. **Expected**: Modal returns to the read-only detail view (does not close)

### 5. Validation Error

1. Open a lot detail modal, click "Edit Override"
2. Enter invalid data (e.g., text in the Quantity field)
3. Click "Save Override"
4. **Expected**: Error messages appear inline next to the invalid fields; modal stays open

## Programmatic Tests

```bash
cd /usr/src/lotsdb
pytest tests/ -v
```

## Files Changed

| File | Change |
|------|--------|
| `src/catalog/templates/catalog/shell.html` | Add `<dialog>` modal container and JS for open/close |
| `src/catalog/templates/catalog/partials/lot_detail_modal.html` | New: lot detail fragment for modal |
| `src/catalog/templates/catalog/partials/lot_edit_modal.html` | New: override edit form fragment for modal |
| `src/catalog/templates/catalog/partials/lots_table_row.html` | Add click handler on thumbnail to open modal; add row ID |
| `src/catalog/views/panels.py` | Add `lot_detail_panel()` view for modal content |
| `src/catalog/urls.py` | Add URL pattern for lot detail panel |
| `src/catalog/static/catalog/styles.css` | Add modal CSS styles |
| `tests/contract/test_panels.py` | Add tests for modal endpoints |

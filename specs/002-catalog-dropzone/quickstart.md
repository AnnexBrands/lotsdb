# Quickstart: Catalog Dropzone

## What This Feature Does

Adds a drag-and-drop "Add Catalog" zone to the navigation bar. Users can drop a catalog spreadsheet file onto it to quickly import a catalog. On success, they are redirected to the new event page. On failure, they see a toast error.

## Prerequisites

- Existing 001-auction-catalog-manager feature fully deployed
- Python 3.14, Django 5, HTMX 2.0.4 (already in place)
- ABConnectTools 0.2.1 with `FileLoader` and `BulkEndpoint` (already installed)

## Files Changed

| File | Change |
|------|--------|
| `src/catalog/templates/catalog/base.html` | Add dropzone to navbar, toast container, inline JS for drag-and-drop |
| `src/catalog/static/catalog/styles.css` | Add dropzone and toast styles |
| `src/catalog/views/imports.py` | Add `upload_catalog` view for AJAX file upload |
| `src/catalog/urls.py` | Add `imports/upload/` URL pattern |
| `src/catalog/services.py` | Add `find_catalog_by_customer_id` helper |
| `tests/contract/test_upload.py` | Contract tests for the upload endpoint |

## How to Test Manually

1. Start the dev server: `cd src && python manage.py runserver`
2. Log in at `http://localhost:8000/login/`
3. On any page, locate "Add Catalog" in the top nav bar
4. Drag a valid `.xlsx`/`.csv`/`.json` catalog file and drop it on the "Add Catalog" area
5. Observe: loading indicator appears, then you are redirected to the event detail page
6. Drag an invalid file (e.g., a `.txt` file or a spreadsheet with wrong columns)
7. Observe: a red toast error appears and you remain on the current page

## How to Test Programmatically

```bash
pytest tests/contract/test_upload.py -v
```

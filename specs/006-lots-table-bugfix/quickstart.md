# Quickstart: Lots Table & Bugfixes

**Branch**: `006-lots-table-bugfix` | **Date**: 2026-02-11

## Prerequisites

- Python 3.14, Django 5, HTMX 2.0.4 (CDN)
- ABConnectTools 0.2.1 (editable install at `/usr/src/pkgs/ABConnectTools`)
- Valid ABConnect API credentials in session

## Run Tests

```bash
cd /usr/src/lotsdb
.venv/bin/python -m pytest tests/ -v
```

## Manual Verification

### Bug Fix: Event Selection (AC-1)

1. Navigate to `http://localhost:8000/`
2. Click a seller → events load in left2 panel
3. Click event A → lots table loads in main panel
4. Click event B → lots table updates with event B's lots
5. Click event A again → lots table updates back to event A's lots
6. **Pass**: All three event clicks load lots successfully

### Bug Fix: Thumbnails & Descriptions (AC-2, AC-3)

1. Select a seller and event with lots that have images
2. Verify thumbnail images appear in the img column
3. Verify description and notes appear in the desc/notes column
4. For lots without images, verify placeholder SVG appears

### Feature: Lots Table (AC-4)

1. Select a seller and event
2. Verify table has columns: img, desc/notes, qty, L, W, H, wgt, cpack, crate, do-not-tip, save
3. Verify data populates from lot initial_data or override

### Feature: Override Display (AC-5)

1. Find a lot that has overridden data (different from initial)
2. Verify overridden cells have a visual indicator (highlighted)
3. Hover over an overridden cell → tooltip shows "Original: {value}"

### Feature: Inline Save (AC-6)

1. Modify a value in a lot row
2. Click the save icon
3. Verify the row updates without full page reload
4. Refresh the page → verify the change persisted

### Deep Link Hydration (AC-7)

1. Navigate to `/?seller=<display_id>&event=<catalog_id>`
2. Verify lots table renders with full data on initial load

## Deploy

```bash
ssh iq "cd /www/lotsdb && git pull && .venv/bin/pip install -e . 2>&1 | tail -3 && sudo systemctl restart lotsdb"
```

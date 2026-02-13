# Quickstart: 011-lots-table-ux-overhaul

## Prerequisites

- Python 3.14 venv activated: `source .venv/bin/activate`
- ABConnectTools installed in editable mode
- Development server: `cd src && python manage.py runserver`

## Manual Testing Checklist

### 1. URL Routing (US1)

```bash
# These should return 404:
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/sellers/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/sellers/1/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/events/1/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/lots/1/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/search/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/imports/

# These should return 200 (or 302 to login):
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/login/
```

### 2. Number Formatting (US2)

1. Log in and navigate to a seller → event with lots
2. Find a lot with dimension values that are whole numbers (e.g., weight = 10.0)
3. Verify the input shows `10`, not `10.0`
4. Find a lot with fractional values (e.g., length = 10.5)
5. Verify the input shows `10.5`

### 3. CPack Badges (US3)

1. In the lots table, find lots with different cpack values
2. Verify:
   - cpack=1 shows "NF" in green, Poppins 900
   - cpack=2 shows "LF" in blue, Poppins 900
   - cpack=3 shows "F" in amber, Poppins 900
   - cpack=4 shows "VF" in red, Poppins 900
   - cpack=PBO shows "PBO" in purple, Poppins 900
   - No cpack shows "—"
3. Change a cpack via the select — verify the badge color updates

### 4. Visual Cleanup (US4)

1. Inspect the lots table
2. Verify no vertical borders between columns
3. Verify horizontal borders separate rows
4. Verify the image column has no header text

### 5. Merged Dimensions (US5)

1. Find a lot with qty=2, l=10, w=8, h=6, wgt=50
2. Verify single cell shows: `2 @ 10 x 8 x 6, 50 lbs` as editable inputs
3. Click the qty input — verify the value is selected
4. Tab through: qty → l → w → h → wgt
5. Override one value (e.g., change wgt from 50 to 55)
6. Click outside the row — verify the row auto-saves immediately (no delay) and only the wgt input gets override styling, not the whole cell
7. Change another value, stay in the row, wait 15 seconds — verify the row auto-saves via the 15s inactivity debounce
8. Open the modal for the same lot — verify description/notes are preserved (merge-on-save)

### 6. Larger Thumbnails (US6)

1. Find lots with images
2. Verify thumbnails are visually larger than the previous 40×40px
3. Hover over a thumbnail — verify the preview popup still works

### 7. Immutable Description (US7)

1. Verify the description column header reads "Lot Description"
2. Verify description text is plain text, not a textarea (no resize handle)
3. Click the description text — verify the lot modal opens
4. Click the thumbnail — verify the lot modal opens (same behavior)

### 8. Upgraded Lot Modal with Auto-Save (US8)

1. Open a lot modal (click description or image)
2. Verify layout: image gallery at top → editable description textarea → editable notes textarea → data summary
3. Navigate images in the gallery (scroll/swipe through, click thumbnails)
4. Edit the description text, then click into the notes field (tab or click)
5. Verify the description auto-saves on blur — check for a toast notification and the table row updating behind the modal (OOB swap)
6. Edit notes (trim boilerplate text), then close the modal (click outside or press Escape)
7. Verify notes auto-saved on blur when the modal closed — the table row should show the trimmed notes
8. Re-open the modal — verify both edited description and trimmed notes persisted
9. Verify no "Save" button exists for text fields — saving is automatic on blur
10. Open a lot that has inline dimension overrides, edit description in the modal, verify dimension overrides are preserved after save (merge-on-save)

## Automated Tests

```bash
cd /usr/src/lotsdb
.venv/bin/python -m pytest tests/ -v
```

Key test areas:
- URL routing: verify removed routes return 404
- `build_lot_table_rows`: unchanged behavior
- `format_number` template filter: whole numbers vs decimals
- `cpack_display` template filter: correct label + class mapping
- Lot override panel: save flow still works with merged column form data
- Lot detail panel: modal save for description/notes

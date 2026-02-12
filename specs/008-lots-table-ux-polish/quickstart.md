# Quickstart: Lots Table UX Polish

**Feature**: 008-lots-table-ux-polish | **Date**: 2026-02-11

## Prerequisites

- Python 3.14 with virtual environment
- ABConnectTools 0.2.1 (editable install)
- Django 5 dev server running

## Setup

```bash
cd /usr/src/lotsdb/src
python manage.py runserver
```

## Manual Test Steps

### 1. Clean Input Appearance

1. Navigate to `http://localhost:8000/`
2. Select a seller → event → lots table loads
3. **Expected**:
   - Description field is a `<textarea>` (not a text input)
   - Notes appear as read-only truncated text below the description
   - Qty, L, W, H, Wgt inputs have no visible border — only the `<td>` cell has a subtle border
   - cpack is a `<select>` dropdown
4. Click on a number input (e.g., Qty)
5. **Expected**: Input gets a blue focus border
6. Click the cpack dropdown and use arrow keys
7. **Expected**: Options cycle through: (empty), 1, 2, 3, 4, PBO

### 2. Save Button Visual Feedback

1. In any lot row, change a field value (e.g., update Qty)
2. **Expected**: Save icon turns red (dirty state indicator)
3. Click the save icon
4. **Expected**: Row updates, save icon turns green briefly, then returns to default
5. Change a field value again, then click on a different row (or click outside)
6. **Expected**: After ~2 seconds, the row auto-saves; save icon turns green

### 3. No Yellow Flash on Click

1. Click anywhere on a lot row
2. **Expected**: No yellow highlight appears — only the subtle gray hover state
3. Rows with overridden fields still show yellow background on those specific cells

### 4. Photo Hover Preview

1. Hover over a lot's thumbnail image
2. **Expected**: A larger version (~300px) of the image appears as a popover/tooltip
3. Move mouse away from thumbnail
4. **Expected**: Preview disappears
5. Hover over a lot with no image (placeholder icon)
6. **Expected**: No preview appears

### 5. Notes "More" Link

1. Find a lot with notes text
2. **Expected**: Notes appear as truncated read-only text below the description textarea
3. Click the "more" link next to the notes
4. **Expected**: The lot detail modal opens (same as clicking the thumbnail)

## Files Changed

| File | Change |
|------|--------|
| `src/catalog/templates/catalog/partials/lots_table_row.html` | Redesign: textarea for desc, read-only notes with "more", select for cpack, save button states |
| `src/catalog/static/catalog/styles.css` | Input border removal, save states, photo preview, notes truncation |
| `src/catalog/templates/catalog/shell.html` | JS for dirty tracking, debounce auto-save, save state colors |
| `src/catalog/views/panels.py` | Comment documenting notes field handling in inline override save |

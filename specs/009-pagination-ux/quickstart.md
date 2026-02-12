# Quickstart: Pagination UX Improvements

**Feature**: 009-pagination-ux | **Date**: 2026-02-12

## Setup

```bash
cd /usr/src/lotsdb/src
python manage.py runserver
```

Open http://localhost:8000/ in a browser. Log in with valid ABConnect credentials.

## Manual Testing

### Test 1: Jump-to-Page (US1)

1. Select a seller with many events (50+) or an event with many lots (25+)
2. Observe the pagination bar at the bottom of the panel
3. Click on the page number display (e.g., "2 / 5")
4. Verify the display becomes an editable number input
5. Type a valid page number (e.g., "4") and press Enter
6. Verify the panel navigates to page 4
7. Click the page number again, type "999", press Enter
8. Verify it navigates to the last page (not an error)
9. Click the page number, press Escape
10. Verify it reverts to the static display without navigating

### Test 2: Page Size Selector (US2)

1. On any paginated panel, find the page size dropdown (right side of pagination bar)
2. Change from default (e.g., 25) to 50
3. Verify the panel reloads with 50 items and resets to page 1
4. Navigate to page 2
5. Verify the page size stays at 50 (not reset to default)
6. Change page size to 10
7. Verify the panel shows 10 items and resets to page 1

### Test 3: Item Range Display (US3)

1. Load a panel with multiple pages of data
2. Verify the pagination shows "1–25 of 73" (or similar) instead of just "1 / 3"
3. Navigate to page 2
4. Verify it shows "26–50 of 73"
5. Navigate to the last page
6. Verify the end number matches the total (e.g., "51–73 of 73")

### Test 4: Scroll to Top (US4)

1. Load the lots panel with 25+ lots
2. Scroll to the bottom of the lots table
3. Click "Next" in the pagination
4. Verify the panel scrolls back to the top automatically

### Test 5: Cross-Panel Consistency

1. Verify pagination improvements work identically on:
   - Sellers panel (left1)
   - Events panel (left2)
   - Lots panel (main)
2. Verify filter + pagination interaction: apply a filter, change page, change page size — all work together

### Test 6: Auto-Save Interaction

1. On the lots panel, edit a field in a lot row
2. While the row has unsaved changes (red save icon), click Next
3. Verify auto-save fires before pagination (or unsaved changes are not lost)
4. After navigation, verify the previous page's save completed

## Automated Tests

```bash
cd /usr/src/lotsdb
pytest tests/ -v -k "pagination or page_size"
```

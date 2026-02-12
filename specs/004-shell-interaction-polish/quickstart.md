# Quickstart: Shell Interaction Polish

**Feature Branch**: `004-shell-interaction-polish`
**Date**: 2026-02-11

## Prerequisites

- Python 3.14
- Django 5
- ABConnectTools 0.2.1 (editable install)
- ABConnect API credentials (for live data)

## Setup

No new dependencies. No migrations.

```bash
cd /usr/src/everard/src
python manage.py runserver
```

## Verify Selection State Highlighting

1. Navigate to `http://localhost:8000/`
2. **Click a seller** in the left panel
   - The seller row should have a blue left border and light blue background (`.active` class)
   - The events panel should load the seller's events
3. **Click an event** in the middle panel
   - The event row should highlight with `.active` class
   - The seller highlight should remain in the left panel
4. **Click a different seller**
   - The old seller highlight clears, new one appears
   - Events panel resets, lots panel clears
5. **Paginate the sellers list** (if multi-page)
   - If the selected seller is on the current page, it should remain highlighted

## Verify Loading Indicators

1. **Click a seller** — observe a spinner overlay on the events panel during load
2. **Click the Next page button** on the sellers panel — observe a spinner overlay on the sellers panel
3. **Click an event** — observe a spinner overlay on the lots panel
4. All three panels should show identical spinner behavior (semi-transparent white overlay with spinning circle)

## Verify URL State

1. **Click a seller** — check the browser URL bar: should show `/?seller=<id>`
2. **Click an event** — URL should update to `/?seller=<id>&event=<id>`
3. **Copy the URL** and open in a new tab — the shell should load with the same seller and event pre-selected
4. **Click the browser back button** — the previous selection state should restore
5. **Click the browser forward button** — the next selection state should restore

## Verify Mobile Layout

1. **Resize the browser** to < 768px wide (or use DevTools device emulation)
2. Only the Sellers panel should be visible
3. **Click a seller** — the Events panel should appear (Sellers panel hides)
4. A **Back button** should appear at the top
5. **Click an event** — the Lots panel should appear
6. **Click Back** — should return to Events panel
7. **Click Back** again — should return to Sellers panel
8. **Resize back to desktop** (>= 768px) — all three panels should appear side-by-side

## Verify Pagination Validation

```bash
# These should all return 200 (not 500):
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/panels/sellers/?page=abc"
# Expected: 200

curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/panels/sellers/?page=-5"
# Expected: 200

curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/panels/sellers/?page_size=0"
# Expected: 200
```

## Verify Invalid URL Params

```bash
# Invalid seller ID in URL — should render default shell (no error):
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/?seller=abc"
# Expected: 200

# Non-existent seller — should render default shell:
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/?seller=999999"
# Expected: 200
```

## Run Tests

```bash
cd /usr/src/everard
pytest
```

### Contract Tests Cover

- Selection state: `.active` class present on selected seller/event rows
- OOB swaps: seller list re-rendered with selection on event click
- `HX-Push-Url` header present on panel responses
- Shell hydration: `/?seller=42` pre-renders events
- Pagination validation: bad params return 200, not 500
- Loading indicators: all panels have `.htmx-indicator` markup

## File Changes

### Modified Files

```
src/catalog/views/panels.py              # Selection state, pagination validation, HX-Push-Url
src/catalog/views/sellers.py             # Shell hydration from URL params
src/catalog/templates/catalog/shell.html # Loading indicator for Left1, mobile JS, data attributes
src/catalog/templates/catalog/partials/seller_list_panel.html  # active class wiring
src/catalog/templates/catalog/partials/events_panel.html       # active class + OOB seller list
src/catalog/templates/catalog/partials/lots_panel.html         # OOB events list
src/catalog/templates/catalog/partials/panel_pagination.html   # Carry selected param
src/catalog/static/catalog/styles.css    # Responsive breakpoint, mobile panel styles
tests/contract/test_panels.py           # New contract tests
```

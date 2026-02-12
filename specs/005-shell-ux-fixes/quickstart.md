# Quickstart: Shell UX Fixes

**Branch**: `005-shell-ux-fixes` | **Date**: 2026-02-11

## Prerequisites

- Python 3.14 virtualenv with `pip install -e ".[dev]"`
- ABConnect credentials in `.env`
- `python src/manage.py migrate`

## Automated Verification

```bash
# Run all tests (should be 48+ passing)
.venv/bin/pytest -v

# Run only contract tests for panels
.venv/bin/pytest tests/contract/test_panels.py -v
```

## Manual Verification

### 1. Customer-Friendly URLs

1. Start server: `python src/manage.py runserver 0.0.0.0:8000`
2. Navigate to `http://localhost:8000/`
3. Click any seller → check browser URL shows `?seller=<4-digit-number>` (customer_display_id, NOT a small internal ID)
4. Click any event → check URL shows `?seller=4098&event=395768` (customer_catalog_id)
5. Copy the URL, open in new tab → same state renders correctly
6. Try `?seller=99999` (non-existent) → default empty state, no error

### 2. Lots Data Correctness

1. Click a seller, then click an event that has lots
2. Verify lots shown are specifically for that event (check lot numbers match)
3. Click a different event → lots update correctly
4. Click an event with no lots → see "No lots in this event"

### 3. Panel Filters

1. In the sellers panel header, type a seller name and press Enter
2. Verify seller list filters to matching results
3. Click a seller → filter input clears, placeholder shows "Selected: <seller name>"
4. In the events panel header, type an event title and press Enter
5. Verify events list filters to matching results

### 4. Loading Indicators

1. Click a seller → Left2 panel shows spinner overlay while loading
2. Click an event → Main panel shows spinner overlay while loading
3. Paginate sellers → Left1 panel shows spinner overlay

### 5. Mobile Layout

1. Resize browser to < 768px
2. Only sellers panel visible
3. Click seller → events panel appears with back button
4. Click event → lots panel appears
5. Resize to desktop → all three panels visible, starts at sellers view
6. Resize back to mobile → starts at sellers (not stuck on lots)

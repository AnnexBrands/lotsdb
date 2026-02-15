# Quickstart: 018-critical-bug-fixes

## Prerequisites

- Python 3.14 with the project virtualenv activated
- Redis installed and running (`redis-server`)
- ABConnect API credentials in `.env`

## Setup

```bash
# 1. Switch to the feature branch
git checkout 018-critical-bug-fixes

# 2. Ensure Redis is running
redis-cli ping
# Expected: PONG

# 3. Start the development server
cd src && python manage.py runserver
```

## Manual Testing

### Bug 1: Cache Read/Write

1. Open browser to `http://localhost:8000/`
2. Click any seller in the left panel
3. Check terminal output — should see NO "Cache read failed" or "Cache write failed" warnings
4. Click the same seller again — events should load faster (from cache)
5. Stop Redis (`redis-cli shutdown`), click a seller — should fall back to API gracefully with warnings logged
6. Restart Redis (`redis-server --daemonize yes`)

### Bug 2: First Event Auto-Selected

1. Click any seller that has events
2. Verify: the first event in the events panel is highlighted (active state)
3. Verify: the lots table in the main panel shows lots for that event
4. Click a different seller — same behavior: first event auto-selected, lots loaded

### Bug 3: Save Button Works

1. Select a seller → event → lots are displayed
2. Change a dimension value (e.g., Length) in any lot row
3. Click the red disk save button
4. Verify: a POST request appears in the Network tab
5. Verify: the save button briefly shows success feedback (green flash)
6. Refresh the page, navigate back to the same lot — verify the saved value persists
7. Click the lot thumbnail — verify the modal opens successfully

### Bug 4: Editable Notes

1. Click a lot thumbnail to open the detail modal
2. Click on the notes text area (below the description)
3. Type or modify the notes text
4. Click outside the notes area (anywhere else in the modal)
5. Verify: a success toast appears ("Saved")
6. Close and reopen the modal — verify the updated notes are displayed
7. For a lot without notes: verify a placeholder is shown; click it and type notes

## Programmatic Tests

```bash
cd /usr/src/lotsdb
pytest tests/ -v
```

# Quickstart: Sellers Panel UX

## Files Changed

| File | Change |
|------|--------|
| `src/catalog/templates/catalog/partials/seller_list_panel.html` | Move `hx-get` from form to input; add `hx-trigger="input changed delay:300ms, search"` |
| `src/catalog/templates/catalog/shell.html` | Add skeleton HTML template + JS to inject skeletons on seller click |
| `src/catalog/static/catalog/styles.css` | Add skeleton loading CSS (`.skeleton-*` classes, pulse animation) |
| `src/catalog/views/panels.py` | Sort events by `start_date` descending in `seller_events_panel` |
| `tests/contract/test_panels.py` | Add contract tests for debounced trigger, skeleton injection, event sorting |

## How to Test

### Manual Testing

1. Start the dev server:
   ```bash
   cd src && python manage.py runserver
   ```

2. Log in and navigate to the sellers panel.

3. **Test realtime filtering**:
   - Type a partial seller name (e.g., "Acm")
   - Verify the list filters after a brief pause (~300ms)
   - Type rapidly — verify the list doesn't flicker/update between keystrokes
   - Clear the field — verify the full list restores
   - Type a name that matches nothing — verify empty state appears

4. **Test skeleton loading**:
   - Click a seller
   - Observe the events panel immediately clears and shows skeleton placeholders with a spinner
   - After the server responds, verify the skeleton is replaced with real event data
   - Click a different seller — verify skeletons appear again (no stale data from previous seller)

5. **Test events sort order**:
   - Select a seller with multiple events
   - Verify events are sorted by start date, most recent first

6. **Test existing behavior preserved**:
   - Verify seller selection highlighting (blue left border) still works
   - Verify pagination still works in both panels
   - Verify mobile navigation still works

### Automated Testing

```bash
python -m pytest tests/ -v
```

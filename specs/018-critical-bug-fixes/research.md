# Research: 018-critical-bug-fixes

## Bug 1: Cache Read/Write Always Fails

### Decision
The root cause is that Redis is not running or not reachable on the configured URL. The `.env` file has no `REDIS_URL` set, so it defaults to `redis://127.0.0.1:6379`. If Redis is not installed/running locally, every cache operation throws `ConnectionRefusedError`, caught by `safe_cache_get`/`safe_cache_set` wrappers which log warnings.

### Evidence
- `.env` contains only `ABC_CLIENT_ID` and `ABC_CLIENT_SECRET` — no `REDIS_URL`
- `redis` Python package v7.1.1 is installed (meets `redis>=5.0` requirement)
- Django 5.2's `RedisCache` backend does NOT handle connection errors internally — all exceptions propagate to the caller
- `safe_cache_get`/`safe_cache_set` catch all exceptions and log warnings — this is the observed behavior
- The issue affects both local and production, confirming it's a configuration/infrastructure issue, not a code bug

### Fix Approach
1. Verify Redis is installed and running on both local and production
2. Add `REDIS_URL` to `.env` (and production environment)
3. Add socket timeout configuration to `CACHES` settings to fail fast on connection issues
4. Enhance warning logs to include the actual exception message for easier diagnosis
5. Optionally add a startup health check that pings Redis

### Alternatives Considered
- Switch to Django's `LocMemCache` — rejected: loses cross-process caching benefit
- Add retry logic — rejected: over-engineering; if Redis is down, fallback to API is correct behavior
- Disable cache entirely — rejected: defeats the purpose of the caching feature
- Keep 300s TTL — rejected: user requires no TTL; cache should only be busted on insert, not time-based expiry. Set `TIMEOUT: None` in Django CACHES config

---

## Bug 2: First Event Not Auto-Selected on Seller Click

### Decision
The auto-select code in `shell.html` listens on `htmx:afterSwap` and calls `firstEvent.click()`. The likely root cause is that in HTMX 2.0, `htmx:afterSwap` fires after DOM insertion but **before** HTMX processes (settles) the new elements' `hx-*` attributes. Clicking an element during `afterSwap` may not trigger its HTMX request because HTMX hasn't initialized the element yet. The fix is to use `htmx:afterSettle` instead, or defer the click with `setTimeout`.

### Evidence
- The auto-select was introduced in PR #19 (`017-lots-modal-overhaul`) and appears to have never worked
- Code at shell.html:399-403 correctly sets `_sellerClicked`, finds the first `.panel-item`, and calls `.click()`
- HTMX 2.0 lifecycle: `afterSwap` → element processing → `afterSettle`. Click during `afterSwap` may miss HTMX initialization
- Secondary issue: if cache IS working, the SWR refresh (`hx-trigger="load"` in events_panel.html:29) fires immediately after the cached response and may overwrite the auto-selected state. The `htmx:beforeSwap` guard (shell.html:407-420) only blocks stale seller refreshes, not same-seller SWR

### Fix Approach
1. Change the auto-select listener from `htmx:afterSwap` to `htmx:afterSettle` for the events panel swap
2. Add SWR guard: set a flag when auto-select is in flight, suppress SWR swap until the event click completes
3. After SWR refresh completes, re-apply the `.active` class to the currently selected event

### Alternatives Considered
- `setTimeout(firstEvent.click, 0)` — works but fragile timing dependency
- Server-side auto-select (return first event's lots in the events response) — rejected: changes API contract, adds complexity

---

## Bug 3: Lots Table Save (Red Disk) Does Nothing

### Decision
The `<button type="submit">` in `lots_table_row.html` is inside a `<tr>`, NOT inside a `<form>`. In HTML, clicking a submit button only generates a `submit` event on an ancestor `<form>` element. Since there's no `<form>`, no `submit` event fires. The `<tr>` has `hx-trigger="submit"` which waits for a native submit event that never arrives. The click handler at shell.html:484-491 only clears auto-save timers — it doesn't trigger the submit.

### Evidence
- `lots_table_row.html:2`: `<tr ... hx-trigger="submit">` — no `<form>` wrapping the inputs
- `lots_table_row.html:37`: `<button type="submit" class="btn-icon override-btn">` — button outside a form
- shell.html:484-491: click handler clears timers but does NOT call `htmx.trigger(tr, 'submit')`
- Auto-save via blur (shell.html:470) and inactivity (shell.html:437) work because they explicitly call `htmx.trigger(tr, 'submit')`
- CSRF is not an issue — `base.html:14` sets `hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'` on `<body>`, which HTMX inherits

### Why It Breaks the Modal
After clicking save (no effect), `tr.dataset.dirty` stays `'1'`. When the user then clicks the lot thumbnail to open the modal, `focusout` fires on the row, triggering the blur auto-save (`htmx.trigger(tr, 'submit')`). This races with the modal GET request. If the save response (which targets `closest tr` with `outerHTML` swap) arrives and replaces the `<tr>`, the initiating element for the modal GET may be disrupted, or the error response from a failed save replaces the row with an error panel.

### Fix Approach
Add `htmx.trigger(tr, 'submit')` to the save button click handler after clearing timers:
```javascript
document.body.addEventListener('click', function(e) {
    if (!e.target.closest('.btn-icon[type="submit"]')) return;
    var tr = getLotRow(e.target);
    if (tr) {
        if (tr._autoSaveTimer) { clearTimeout(tr._autoSaveTimer); tr._autoSaveTimer = null; }
        if (tr._inactivityTimer) { clearTimeout(tr._inactivityTimer); tr._inactivityTimer = null; }
        htmx.trigger(tr, 'submit');  // <-- ADD THIS
    }
});
```

### Alternatives Considered
- Wrap row in `<form>` — rejected: `<form>` inside `<tr>` is invalid HTML, breaks table layout
- Use `hx-trigger="click"` on button instead — rejected: would duplicate submission with blur/inactivity saves
- Change button to `type="button"` — rejected: doesn't solve the problem, same issue

---

## Bug 4: Notes Not Editable in Modal

### Decision
The notes are rendered as a plain `<div class="lot-desc-notes">` in `lot_detail_modal.html:30`. There is no `contenteditable` attribute and no JavaScript handler for inline editing. The backend endpoint `lot_text_save` (panels.py:416-459) and URL route (urls.py:17) already exist and work correctly. Only the frontend needs changes.

### Evidence
- `lot_detail_modal.html:30`: `{% if lot_notes %}<div class="lot-desc-notes">{{ lot_notes }}</div>{% endif %}` — read-only
- `panels.py:416-459`: `lot_text_save()` accepts POST with `description` and/or `notes` fields, saves via `save_lot_override()`, returns OOB row update + toast
- `urls.py:17`: `path("panels/lots/<int:lot_id>/text-save/", lot_text_save, name="lot_text_save")`
- No contenteditable-related JavaScript exists in shell.html
- User explicitly wants editable `<p>` tag (contenteditable), NOT a textarea

### Fix Approach
1. Add `contenteditable="true"` to the notes `<div>` (or change to `<p>`) with `data-field="notes"` and `data-lot-id="{{ lot.id }}"`
2. Always render the element (even when empty) with placeholder text
3. Add JavaScript blur handler that:
   - Reads the element's `textContent`
   - Sends POST to `/panels/lots/{lot_id}/text-save/` with `notes` field
   - Uses CSRF token from the body's `hx-headers`
   - Shows success/error toast via the existing `showToast` mechanism
4. Add CSS `:focus` styles to indicate editability (subtle border/background)

### Alternatives Considered
- Use `<textarea>` — rejected: user explicitly requested contenteditable `<p>` tag
- Use HTMX attributes on the element — possible but contenteditable + blur is better handled with vanilla JS + fetch since HTMX doesn't natively support contenteditable elements
- Make description editable too — not requested, avoid scope creep

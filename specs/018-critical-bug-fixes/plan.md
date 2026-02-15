# Implementation Plan: Critical Bug Fixes

**Branch**: `018-critical-bug-fixes` | **Date**: 2026-02-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/018-critical-bug-fixes/spec.md`

## Summary

Fix four critical bugs: (1) Redis cache always fails due to Redis not running/configured — ensure Redis is available and enhance error logging; (2) first event not auto-selected after seller click due to HTMX lifecycle timing — move auto-select to `htmx:afterSettle`; (3) lots table save button does nothing because submit button outside `<form>` never fires submit event — add explicit `htmx.trigger()` in click handler; (4) notes in lot modal not editable — add `contenteditable` attribute and blur-save JavaScript.

## Technical Context

**Language/Version**: Python 3.14, Django 5.2
**Primary Dependencies**: HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install), redis 7.1.1
**Storage**: SQLite3 (sessions + Django User table), Redis (cache)
**Testing**: pytest
**Target Platform**: Linux server (WSL2 dev, Ubuntu prod)
**Project Type**: Web application (Django + HTMX, server-rendered)
**Performance Goals**: Cache operations complete in <50ms; auto-select triggers within a single frame after events load
**Constraints**: No new dependencies; all fixes must be backward-compatible with existing data
**Scale/Scope**: 4 bug fixes across 4 files (1 template, 1 JS in shell, 1 settings, 1 CSS)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Artifact Harmony | PASS | Spec, plan, research, contracts, quickstart, and tests all updated together |
| II. Executable Knowledge | PASS | Quickstart includes manual test steps; existing unit/contract tests will be extended |
| III. Contracted Boundaries | PASS | No new API endpoints; notes-save contract documents existing endpoint |
| IV. Versioned Traceability | PASS | All changes on feature branch with descriptive commits |
| V. Communicable Truth | PASS | Quickstart.md documents how to verify each fix |

**Post-Design Re-Check**: All principles continue to pass. No new boundaries introduced.

## Project Structure

### Documentation (this feature)

```text
specs/018-critical-bug-fixes/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Root cause analysis for all 4 bugs
├── data-model.md        # No new entities; reference doc
├── quickstart.md        # Manual and programmatic test instructions
├── contracts/
│   └── notes-save.md    # Documents existing text-save endpoint
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── config/
│   └── settings.py                              # Bug 1: Redis timeout config
├── catalog/
│   ├── cache.py                                 # Bug 1: Enhanced error logging
│   ├── static/catalog/
│   │   └── styles.css                           # Bug 4: Contenteditable focus styles
│   └── templates/catalog/
│       ├── shell.html                           # Bug 2: afterSettle, Bug 3: click trigger, Bug 4: blur handler
│       └── partials/
│           └── lot_detail_modal.html            # Bug 4: contenteditable notes element

tests/
├── unit/
│   └── test_cache.py                            # Bug 1: Enhanced logging tests
└── contract/
    └── test_panels.py                           # Bug 3: Save button contract tests
```

**Structure Decision**: Single Django project. All changes are within the existing `src/catalog/` app and `tests/` directory. No new files created except spec artifacts.

## Implementation Details

### Bug 1: Cache Read/Write Failures

**Root Cause**: Redis not running or not reachable. `.env` has no `REDIS_URL`. Default `redis://127.0.0.1:6379` fails if Redis isn't started.

**Changes**:

1. **`src/config/settings.py`** — Remove TTL and add socket timeout options to `CACHES`:
   ```python
   CACHES = {
       "default": {
           "BACKEND": "django.core.cache.backends.redis.RedisCache",
           "LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379"),
           "KEY_PREFIX": "cat_",
           "TIMEOUT": None,  # No TTL — cache persists until explicitly busted on insert
           "OPTIONS": {
               "socket_connect_timeout": 5,
               "socket_timeout": 5,
           }
       }
   }
   ```
   Setting `TIMEOUT: None` means cache entries never expire automatically. They are only invalidated when new data is written (e.g., after a lot override save that might change the seller/event data).

2. **`src/catalog/cache.py`** — Log the actual exception message:
   ```python
   except Exception as exc:
       logger.warning("Cache read failed for key=%s: %s", key, exc)
   ```

3. **`.env`** — Add `REDIS_URL=redis://127.0.0.1:6379` (document the requirement)

4. **Verify Redis is running** on both local and production environments.

### Bug 2: First Event Not Auto-Selected

**Root Cause**: Auto-select runs during `htmx:afterSwap`, before HTMX has processed (settled) the new elements' `hx-*` attributes. Clicking an unsettled element doesn't trigger its HTMX request. Secondary: SWR refresh overwrites auto-selected state.

**Changes in `src/catalog/templates/catalog/shell.html`**:

1. Change the auto-select listener from `htmx:afterSwap` to `htmx:afterSettle`:
   ```javascript
   document.body.addEventListener('htmx:afterSettle', function(e) {
       var target = e.detail.target;
       if (target && target.id === 'panel-left2-content') {
           if (_sellerClicked) {
               _sellerClicked = false;
               var firstEvent = target.querySelector('.panel-item');
               if (firstEvent) firstEvent.click();
           }
       }
   });
   ```

2. Keep the `data-seller-id` tracking in `htmx:afterSwap` (or move to `afterSettle` as well).

3. Suppress SWR swap while auto-select is in flight: add an `_autoSelectInFlight` flag set before `firstEvent.click()` and cleared in the lots panel `htmx:afterSettle`. While set, SWR `beforeSwap` guard skips the swap.

### Bug 3: Save Button Click Does Nothing

**Root Cause**: `<button type="submit">` outside a `<form>` doesn't generate a native `submit` event. The click handler at shell.html:484-491 clears timers but never calls `htmx.trigger(tr, 'submit')`.

**Change in `src/catalog/templates/catalog/shell.html`** (lines 484-491):
```javascript
document.body.addEventListener('click', function(e) {
    if (!e.target.closest('.btn-icon[type="submit"]')) return;
    var tr = getLotRow(e.target);
    if (tr) {
        if (tr._autoSaveTimer) { clearTimeout(tr._autoSaveTimer); tr._autoSaveTimer = null; }
        if (tr._inactivityTimer) { clearTimeout(tr._inactivityTimer); tr._inactivityTimer = null; }
        htmx.trigger(tr, 'submit');  // FIX: actually trigger the save
    }
});
```

This is the simplest and most targeted fix. The `hx-trigger="submit"` on the `<tr>` already handles the HTMX POST — it just needs the event.

### Bug 4: Notes Not Editable in Modal

**Root Cause**: Notes rendered as `<div class="lot-desc-notes">{{ lot_notes }}</div>` — plain read-only text. No `contenteditable`, no JavaScript handler.

**Changes**:

1. **`src/catalog/templates/catalog/partials/lot_detail_modal.html`** — Replace read-only notes with contenteditable:
   ```html
   <p class="lot-desc-notes" contenteditable="true"
      data-field="notes" data-lot-id="{{ lot.id }}"
      data-placeholder="Click to add notes">{{ lot_notes|default:"" }}</p>
   ```
   - Always render the element (even when empty) so users can add notes
   - Use `data-placeholder` for CSS-based placeholder

2. **`src/catalog/templates/catalog/shell.html`** — Add blur handler in the modal JS section:
   ```javascript
   document.body.addEventListener('focusout', function(e) {
       var el = e.target;
       if (!el.matches || !el.matches('[contenteditable][data-field]')) return;
       if (!el.closest('#lot-modal-body')) return;
       var field = el.dataset.field;
       var lotId = el.dataset.lotId;
       var value = el.textContent.trim();
       var body = new URLSearchParams();
       body.append(field, value);
       fetch('/panels/lots/' + lotId + '/text-save/', {
           method: 'POST',
           headers: {
               'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
               'Content-Type': 'application/x-www-form-urlencoded',
           },
           body: body,
       }).then(function(resp) {
           if (resp.ok && window.showToast) window.showToast('Saved', 'success');
           else if (window.showToast) window.showToast('Could not save', 'error');
       }).catch(function() {
           if (window.showToast) window.showToast('Could not save', 'error');
       });
   });
   ```

3. **`src/catalog/static/catalog/styles.css`** — Add focus/empty styles:
   ```css
   .lot-desc-notes[contenteditable]:focus {
       outline: 1px solid #94a3b8;
       border-radius: 4px;
       padding: 2px 4px;
   }
   .lot-desc-notes[contenteditable]:empty::before {
       content: attr(data-placeholder);
       color: #94a3b8;
       font-style: italic;
   }
   ```

## Complexity Tracking

No constitution violations. All fixes are minimal, targeted changes to existing files with no new abstractions or patterns introduced.

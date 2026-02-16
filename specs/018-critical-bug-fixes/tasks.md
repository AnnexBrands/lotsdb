# Tasks: Critical Bug Fixes

**Input**: Design documents from `/specs/018-critical-bug-fixes/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested. Existing test updates included where the fix changes observable behavior (cache logging).

**Organization**: Tasks grouped by user story (bug). Each bug fix is independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Ensure Redis infrastructure is available before any cache-related work.

- [X] T001 Verify Redis is installed and running locally — run `redis-cli ping` and confirm `PONG` response
- [X] T002 Add `REDIS_URL=redis://127.0.0.1:6379` to `.env` file

---

## Phase 2: User Story 1 — Cache Reads and Writes Succeed (Priority: P1) 🎯 MVP

**Goal**: Eliminate all "Cache read failed" / "Cache write failed" warnings during normal operation. Cache entries persist indefinitely (no TTL), busted only on insert.

**Independent Test**: Select a seller, confirm no cache warnings in logs. Re-select the same seller and confirm events load from cache (no API call on second load).

### Implementation for User Story 1

- [X] T003 [P] [US1] Update `CACHES` config in `src/config/settings.py` — set `TIMEOUT: None` (no TTL) and add `OPTIONS: {"socket_connect_timeout": 5, "socket_timeout": 5}`
- [X] T004 [P] [US1] Enhance `safe_cache_get` in `src/catalog/cache.py` — change `except Exception:` to `except Exception as exc:` and include `exc` in the warning message: `"Cache read failed for key=%s: %s", key, exc`
- [X] T005 [P] [US1] Enhance `safe_cache_set` in `src/catalog/cache.py` — same pattern: include the actual exception in the warning message: `"Cache write failed for key=%s: %s", key, exc`
- [X] T006 [US1] Update cache warning assertions in `tests/unit/test_cache.py` — adjust any mock assertions that check the exact warning format to match the new `key=%s: %s` pattern with the exception argument

**Checkpoint**: Cache reads/writes succeed when Redis is running. Warnings include the actual exception message when Redis is down. No TTL — entries persist until explicitly busted.

---

## Phase 3: User Story 2 — First Event Auto-Selected on Seller Click (Priority: P1)

**Goal**: Clicking a seller automatically selects the first event and loads its lots — no extra click required.

**Independent Test**: Click any seller with events. First event highlights and lots appear in the main panel without additional clicks.

### Implementation for User Story 2

- [X] T007 [US2] Move auto-select listener from `htmx:afterSwap` to `htmx:afterSettle` in `src/catalog/templates/catalog/shell.html` — change the event listener at ~line 389 so the `_sellerClicked` check and `firstEvent.click()` fire after HTMX has settled the new elements' `hx-*` attributes
- [X] T008 [US2] Add SWR guard flag `_autoSelectInFlight` in `src/catalog/templates/catalog/shell.html` — set flag `true` before `firstEvent.click()`, clear it in `htmx:afterSettle` for `#panel-main-content` (lots loaded). In the `htmx:beforeSwap` guard (~line 407), also suppress SWR swap (`shouldSwap = false`) when `_autoSelectInFlight` is true and the request is a `fresh=1` refresh

**Checkpoint**: Seller click → first event auto-selected → lots visible. SWR background refresh does not overwrite the auto-selected state.

---

## Phase 4: User Story 3 — Lots Table Save Completes Successfully (Priority: P1)

**Goal**: Clicking the red disk save button in the lots table sends a POST request and persists the override. Modal remains functional after saves.

**Independent Test**: Change a dimension value, click red disk, observe network POST in dev tools, confirm saved value persists after page refresh. Open modal afterward — it works.

### Implementation for User Story 3

- [X] T009 [US3] Add `htmx.trigger(tr, 'submit')` to the save button click handler in `src/catalog/templates/catalog/shell.html` — in the click listener at ~line 484 that matches `.btn-icon[type="submit"]`, add `htmx.trigger(tr, 'submit');` after clearing timers so the `<tr>`'s `hx-post` actually fires

**Checkpoint**: Red disk click → POST fires → row updates with success feedback. Subsequent modal opens work correctly.

---

## Phase 5: User Story 4 — Notes Editable in Lot Detail Modal (Priority: P2)

**Goal**: Notes in the lot detail modal are inline-editable via contenteditable. Changes auto-save on blur via the existing text-save endpoint.

**Independent Test**: Open lot modal, click notes, edit text, click away. Success toast appears. Reopen modal — updated notes shown.

### Implementation for User Story 4

- [X] T010 [P] [US4] Replace read-only notes `<div>` with contenteditable `<p>` in `src/catalog/templates/catalog/partials/lot_detail_modal.html` — change the conditional `{% if lot_notes %}<div class="lot-desc-notes">{{ lot_notes }}</div>{% endif %}` to an always-rendered `<p class="lot-desc-notes" contenteditable="true" data-field="notes" data-lot-id="{{ lot.id }}" data-placeholder="Click to add notes">{{ lot_notes|default:"" }}</p>`
- [X] T011 [P] [US4] Add contenteditable focus and placeholder CSS in `src/catalog/static/catalog/styles.css` — add `.lot-desc-notes[contenteditable]:focus` style (outline, border-radius, padding) and `.lot-desc-notes[contenteditable]:empty::before` pseudo-element using `content: attr(data-placeholder)` for placeholder text
- [X] T012 [US4] Add blur handler JavaScript for notes save in `src/catalog/templates/catalog/shell.html` — add a `focusout` event listener in the modal JS section that: checks `el.matches('[contenteditable][data-field]')` and `el.closest('#lot-modal-body')`, reads `textContent`, sends POST to `/panels/lots/{lotId}/text-save/` with the field name and value using `fetch()`, and calls `window.showToast` on success/error

**Checkpoint**: Notes are editable inline. Blur saves to server. Placeholder shown when empty. Success/error toast feedback works.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate all fixes work together and pass existing tests.

- [X] T013 Run full test suite — `pytest tests/ -v` from `/usr/src/lotsdb` and fix any regressions
- [X] T014 Run quickstart.md manual validation — follow all steps in `specs/018-critical-bug-fixes/quickstart.md` to confirm each bug fix works end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (US1 - Cache)**: Depends on Phase 1 (Redis running)
- **Phase 3 (US2 - Auto-select)**: No dependency on US1 — can start after Phase 1
- **Phase 4 (US3 - Save button)**: No dependency on US1 or US2 — can start after Phase 1
- **Phase 5 (US4 - Notes)**: No dependency on US1/US2/US3 — can start after Phase 1
- **Phase 6 (Polish)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (Cache)**: Independent — touches `settings.py`, `cache.py`, `.env`, `test_cache.py`
- **US2 (Auto-select)**: Independent — touches `shell.html` (auto-select section ~line 389)
- **US3 (Save button)**: Independent — touches `shell.html` (click handler ~line 484)
- **US4 (Notes)**: Independent — touches `lot_detail_modal.html`, `styles.css`, `shell.html` (new modal section)

### File Overlap Warning

US2, US3, and US4 all modify `shell.html` in different sections. When implementing sequentially, apply changes in order (US2 → US3 → US4) to avoid merge conflicts. Each modifies a distinct section of the file.

### Parallel Opportunities

```text
# US1 tasks (different files) can all run in parallel:
T003: settings.py
T004: cache.py (safe_cache_get)
T005: cache.py (safe_cache_set) — same file as T004, do together

# US4 tasks across different files can run in parallel:
T010: lot_detail_modal.html
T011: styles.css
T012: shell.html (depends on T010 being the target element)

# Cross-story parallelism:
US1 (settings.py, cache.py) can run fully parallel with US2/US3/US4 (shell.html, templates, CSS)
```

---

## Implementation Strategy

### MVP First (US1 + US3)

1. Complete Phase 1: Ensure Redis is running
2. Complete US1: Cache works — the most impactful fix (every page load benefits)
3. Complete US3: Save button works — the most critical data-entry fix (1 line change)
4. **STOP and VALIDATE**: Test cache + save independently
5. Deploy if ready — these two fixes restore core functionality

### Incremental Delivery

1. Phase 1 (Setup) → Redis confirmed
2. US1 (Cache) → Test: no warnings in logs → Deploy
3. US3 (Save button) → Test: POST fires on click → Deploy
4. US2 (Auto-select) → Test: first event selected → Deploy
5. US4 (Notes editable) → Test: notes save on blur → Deploy
6. Polish → Full regression test → Final deploy

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 and US3 are both 1-2 line fixes in shell.html — fastest wins
- US4 is the most involved (3 files) but all changes are additive (no existing code modified except the notes `<div>`)
- No new dependencies added
- Commit after each user story phase for clean git history

# Tasks: Lots Table UX Polish

**Input**: Design documents from `/specs/008-lots-table-ux-polish/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec. Test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: CSS foundation changes that affect all user stories — input border removal and cell border addition.

- [X] T001 Update input styling in `src/catalog/static/catalog/styles.css` — in the `.lots-table input[type="text"], .lots-table input[type="number"]` rule, change `border: 1px solid #e2e8f0` to `border: none` and add `background: transparent`. Add a new rule `.lots-table input[type="text"]:focus, .lots-table input[type="number"]:focus, .lots-table select:focus` with `outline: none; border: 1px solid #2563eb; border-radius: 3px; background: #fff;`. Add a new rule `.lots-table td` that adds `border: 1px solid #f1f5f9` (subtle cell border) to replace the input borders. Also add `.lots-table select` styling to match inputs: `padding: 0.2rem 0.35rem; border: none; background: transparent; font-size: 0.75rem; color: #1e293b; cursor: pointer;`.
- [X] T002 Remove yellow hover/click highlight in `src/catalog/static/catalog/styles.css` — verify that `.lots-table tbody tr:hover` uses `background: #f8fafc` (gray, not yellow). Ensure no CSS rule applies yellow background on click or active state. The `.overridden` class (`background: #fff3cd`) should remain — it's for persistent override indicators on `<td>` elements, not row-level click states.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational/blocking tasks needed. All user stories can proceed after Phase 1 CSS is in place.

**Checkpoint**: CSS foundation ready — borderless inputs with cell borders, no yellow click highlight.

---

## Phase 3: User Story 1 — Cleaner Input Appearance (Priority: P1) 🎯 MVP

**Goal**: Replace description+notes with textarea + read-only notes, convert cpack to a select dropdown.

**Independent Test**: Load lots table → description is a `<textarea>`, notes appear as read-only text below it, number inputs have no border (cell has border), cpack is a `<select>` with arrow-key navigation through 1, 2, 3, 4, PBO.

### Implementation for User Story 1

- [X] T003 [US1] Replace description+notes inputs in `src/catalog/templates/catalog/partials/lots_table_row.html` — replace the `<div class="lot-desc-cell">` contents. Change the description `<input type="text">` to `<textarea name="description" class="lot-input lot-input-wide" rows="2" placeholder="Description">{{ row.fields.description.value|default:"" }}</textarea>`. Replace the notes `<input>` with a read-only display: `<div class="lot-notes-display">{% if row.fields.notes.value %}<span class="lot-notes-text">{{ row.fields.notes.value }}</span> <button type="button" class="lot-notes-more" hx-get="/panels/lots/{{ row.lot.id }}/detail/" hx-target="#lot-modal-body" hx-swap="innerHTML" aria-label="View full lot details">more</button>{% endif %}</div>`. The notes `name="notes"` input is removed from the inline form — notes are now only editable via the detail modal.
- [X] T004 [US1] Replace cpack text input with select in `src/catalog/templates/catalog/partials/lots_table_row.html` — replace `<input type="text" name="cpack" ...>` with `<select name="cpack" class="lot-input lot-input-sm"><option value="">—</option><option value="1"{% if row.fields.cpack.value == "1" %} selected{% endif %}>1</option><option value="2"{% if row.fields.cpack.value == "2" %} selected{% endif %}>2</option><option value="3"{% if row.fields.cpack.value == "3" %} selected{% endif %}>3</option><option value="4"{% if row.fields.cpack.value == "4" %} selected{% endif %}>4</option><option value="PBO"{% if row.fields.cpack.value == "PBO" %} selected{% endif %}>PBO</option></select>`. Native `<select>` provides arrow key navigation automatically.
- [X] T005 [P] [US1] Add textarea and notes display CSS in `src/catalog/static/catalog/styles.css` — add `.lots-table textarea` styling: `border: none; background: transparent; font-size: 0.75rem; color: #1e293b; resize: vertical; width: 100%; font-family: inherit; line-height: 1.4; padding: 0.2rem 0.35rem;`. Add `.lots-table textarea:focus` with `outline: none; border: 1px solid #2563eb; border-radius: 3px; background: #fff;`. Add `.lot-notes-display` with `font-size: 0.6875rem; color: #64748b; line-height: 1.3; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px;`. Add `.lot-notes-text` with `vertical-align: middle;`. Add `.lot-notes-more` with `all: unset; cursor: pointer; color: #2563eb; font-size: 0.625rem; margin-left: 0.25rem; vertical-align: middle;` and `.lot-notes-more:hover` with `text-decoration: underline;`.

**Checkpoint**: US1 complete — table inputs look clean and spreadsheet-like. Description is a textarea, notes are read-only with "more" link, cpack is a select dropdown.

---

## Phase 4: User Story 2 — Smart Save with Visual Feedback (Priority: P1)

**Goal**: Save icon shows dirty/clean state, auto-saves on row blur with debounce.

**Independent Test**: Edit a field → save icon turns red. Click save → icon turns green briefly. Edit a field, click outside the row → auto-saves after ~2 seconds, icon turns green. No yellow flash on any interaction.

**Depends on**: US1 (textarea and select elements must exist for input/change event listeners)

### Implementation for User Story 2

- [X] T006 [P] [US2] Add save button state CSS in `src/catalog/static/catalog/styles.css` — modify `.btn-icon` to remove any border: add `border: none; background: none;`. Add `.btn-icon.save-dirty` with `color: #dc2626;` (red). Add `.btn-icon.save-dirty:hover` with `color: #b91c1c; background: none;`. Add `.btn-icon.save-clean` with `color: #16a34a;` (green). Add `.btn-icon.save-clean:hover` with `color: #15803d; background: none;`. Transition: keep existing `transition: color 0.15s ease;` on `.btn-icon`.
- [X] T007 [US2] Add dirty tracking and debounced auto-save JS in `src/catalog/templates/catalog/shell.html` — add a new `// --- Row auto-save logic ---` section in the `<script>` block after the modal logic. Implementation: (1) Use event delegation on `document.body` for `input` and `change` events. When an `input`/`change` event fires inside a `<tr>` with `id^="lot-row-"`, find the row's submit button (`.btn-icon`) and add class `save-dirty`, remove `save-clean`. Store a flag on the row element: `tr.dataset.dirty = '1'`. (2) Use event delegation for `focusout` on `document.body`. When `focusout` fires on an element inside a `<tr>` with `id^="lot-row-"`, check if `e.relatedTarget` is still inside the same `<tr>` — if so, ignore. If focus left the row AND `tr.dataset.dirty === '1'`, start a 2000ms `setTimeout` stored as `tr._autoSaveTimer`. (3) Use event delegation for `focusin` on `document.body`. When `focusin` fires inside a `<tr>` with `id^="lot-row-"` that has `tr._autoSaveTimer`, clear the timer via `clearTimeout(tr._autoSaveTimer)`. (4) When the timer fires, trigger the HTMX submit via `htmx.trigger(tr, 'submit')`. (5) Listen for `htmx:afterSwap` on `document.body` — when the swap target is a `<tr>` with `id^="lot-row-"`, find the submit button and add `save-clean`, remove `save-dirty`. After 3 seconds, remove `save-clean` to return to default state. (6) On immediate click of the save button (which triggers submit), clear any pending auto-save timer on the row.

**Checkpoint**: US2 complete — save button shows red on dirty, green on save, auto-saves on row blur after 2s debounce.

---

## Phase 5: User Story 3 — Photo Hover Preview (Priority: P2)

**Goal**: Hovering over a lot thumbnail shows a large preview image.

**Independent Test**: Hover over a lot thumbnail with an image → large preview (~300px) appears above/beside the thumbnail. Move mouse away → preview disappears. Hover over placeholder (no image) → no preview.

**Depends on**: None (can run in parallel with US2)

### Implementation for User Story 3

- [X] T008 [US3] Add preview image element to `src/catalog/templates/catalog/partials/lots_table_row.html` — inside the `<button class="lot-thumb-btn">`, after the existing `<img class="lot-thumb">` tag, add `<img class="lot-thumb-preview" src="{{ row.lot.image_links.0.link }}" alt="">`. This element is only added inside the `{% if row.lot.image_links %}` branch — no preview for placeholder SVGs.
- [X] T009 [P] [US3] Add photo hover preview CSS in `src/catalog/static/catalog/styles.css` — add `.lot-thumb-preview` with `display: none; position: absolute; z-index: 100; left: 52px; top: 50%; transform: translateY(-50%); width: 300px; height: auto; border-radius: 6px; box-shadow: 0 8px 24px rgba(0,0,0,0.2); pointer-events: none; object-fit: contain; background: #fff;`. Add `.lot-thumb-btn:hover .lot-thumb-preview` with `display: block;`. Add `.lot-thumb-cell` needs `position: relative;` — add this to the existing `.lot-thumb-cell` rule if not already present.

**Checkpoint**: US3 complete — hovering over thumbnails shows a large preview image.

---

## Phase 6: User Story 4 — Notes "More" Link (Priority: P2)

**Goal**: Notes displayed as read-only truncated text with "more" link to open detail modal.

**Independent Test**: Find a lot with notes → truncated notes text visible below description textarea → click "more" → lot detail modal opens.

**Depends on**: US1 (the notes display markup was added in T003)

### Implementation for User Story 4

- [X] T010 [US4] Verify notes "more" link works end-to-end — the "more" button added in T003 uses `hx-get="/panels/lots/{{ row.lot.id }}/detail/"` targeting `#lot-modal-body`. Verify this triggers the modal open flow (the existing `htmx:afterSwap` handler on `#lot-modal-body` calls `dialog.showModal()`). No additional code should be needed — this task is verification only. If the click doesn't work because it's inside a `<tr>` with `hx-trigger="submit"`, the button has `type="button"` which should prevent form submission. Verify the HTMX attributes on the button don't conflict with the row's `hx-post`.

**Checkpoint**: US4 complete — notes "more" link opens the lot detail modal.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and validation

- [X] T011 [P] Update `src/catalog/views/panels.py` `lot_override_panel()` — since `notes` is no longer submitted from the inline row form, the override panel should handle the missing `notes` field gracefully. In the string field parsing loop `for field in ("description", "notes", "cpack"):`, notes will now be an empty string from the POST data (absent from form). Verify that this doesn't clear an existing notes override — if `val` is empty/stripped, the field is skipped (current behavior: `if val: override_data[field] = val`), so absent notes won't overwrite. This is correct behavior — notes are only editable from the detail modal. Document this with a code comment.
- [X] T012 [P] Run `ruff check .` from `src/` and fix any linting issues in modified files
- [X] T013 Validate quickstart.md manual test steps — walk through each of the 5 test scenarios in `specs/008-lots-table-ux-polish/quickstart.md` and verify accuracy of expected behavior descriptions and file paths

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **US1 (Phase 3)**: Depends on Phase 1 (borderless input CSS must exist)
- **US2 (Phase 4)**: Depends on US1 (textarea/select elements must exist for event listeners)
- **US3 (Phase 5)**: Depends on Phase 1 only — can run in parallel with US1/US2
- **US4 (Phase 6)**: Depends on US1 (notes markup from T003)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 1 — no dependencies on other stories
- **US2 (P1)**: Depends on US1 — needs textarea/select in DOM for event listeners
- **US3 (P2)**: Independent of US1/US2 — only needs Phase 1 CSS
- **US4 (P2)**: Depends on US1 — the notes "more" markup is created in T003

### Within Each User Story

- CSS tasks marked [P] can run in parallel with template tasks (different files)
- Template changes should complete before JS that depends on new DOM elements

### Parallel Opportunities

- T001 and T002 (Phase 1) can run in parallel (different CSS sections)
- T005 (US1 CSS) runs in parallel with T003/T004 (US1 templates)
- T006 (US2 CSS) runs in parallel with US1 template work
- T008 (US3 template) and T009 (US3 CSS) can run in parallel
- T011, T012, T013 (Polish) — T011 and T012 can run in parallel

---

## Parallel Example: Phase 1

```bash
# These touch different CSS sections and can run in parallel:
Task T001: "Update input styling — remove borders, add cell borders"    # styles.css (input rules)
Task T002: "Remove yellow hover/click highlight"                        # styles.css (hover rules)
```

## Parallel Example: User Story 1

```bash
# Template and CSS touch different files:
Task T003: "Replace description+notes inputs"      # lots_table_row.html
Task T004: "Replace cpack with select"              # lots_table_row.html (after T003)
Task T005: "Add textarea and notes display CSS"     # styles.css (parallel with T003/T004)
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: CSS foundation (2 tasks)
2. Complete US1: Cleaner inputs (3 tasks) → **Visual MVP**
3. Complete US2: Smart save (2 tasks) → **Behavioral MVP**
4. **STOP and VALIDATE**: Edit fields → save icon red → blur row → auto-save → green
5. This is a usable MVP: operators have clean, spreadsheet-like editing

### Incremental Delivery

1. Phase 1 → CSS foundation ready (2 tasks)
2. Add US1 → Clean inputs (5 tasks total) → **Visual improvement deployable**
3. Add US2 → Smart save (7 tasks total) → **Full editing UX**
4. Add US3 → Photo preview (9 tasks total) → **Content discoverability**
5. Add US4 → Notes "more" (10 tasks total) → **Complete**
6. Polish → Verify + lint (13 tasks total) → **Ship**

---

## Notes

- Total tasks: **13**
- US1: 3 tasks (T003–T005)
- US2: 2 tasks (T006–T007)
- US3: 2 tasks (T008–T009)
- US4: 1 task (T010 — verification only, markup added in US1)
- Polish: 3 tasks (T011–T013)
- No new data models — purely frontend changes
- No new dependencies — vanilla JS + CSS only
- No new API endpoints — existing endpoints unchanged
- Notes field removed from inline form but still editable via detail modal

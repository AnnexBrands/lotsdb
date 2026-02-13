# Tasks: Lots Table UX Overhaul

**Input**: Design documents from `/specs/011-lots-table-ux-overhaul/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested. Test tasks included only for the foundational merge-on-save logic (data integrity) and URL routing (regression prevention).

**Organization**: Tasks grouped by user story (US1–US8) in priority order. Many stories touch `lots_table_row.html` and `styles.css`, so execution order matters — stories are sequenced to minimize merge conflicts.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- All paths relative to `/usr/src/lotsdb/`

---

## Phase 1: Setup

**Purpose**: No project initialization needed — existing codebase. This phase is a no-op.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure that multiple user stories depend on. MUST complete before any story phase.

- [X] T001 Add Poppins 900 font CDN `<link>` tags (preconnect + stylesheet) to `<head>` in `src/catalog/templates/catalog/base.html` per research.md R2
- [X] T002 [P] Add `format_number` template filter to `src/catalog/templatetags/catalog_tags.py` — returns `""` for None, `"10"` for 10.0, `"10.5"` for 10.5 (per plan Phase B)
- [X] T003 [P] Add `cpack_label` and `cpack_class` template filters to `src/catalog/templatetags/catalog_tags.py` — maps 1→NF/cpack-nf, 2→LF/cpack-lf, 3→F/cpack-f, 4→VF/cpack-vf, PBO→PBO/cpack-pbo (per plan Phase B)
- [X] T004 Add merge-on-save logic to `save_lot_override` in `src/catalog/services.py` — before creating `LotDataDto`, fetch the lot's existing `overriden_data[0]`, extract all non-None field values into a base dict, then overlay `override_data` on top. This ensures inline saves preserve description/notes overrides and modal saves preserve dimension/flag overrides (FR-020, FR-021). Fields to iterate: all `LotDataDto` attributes (qty, l, w, h, wgt, value, cpack, description, notes, item_id, force_crate, noted_conditions, do_not_tip, commodity_id). The lot is already fetched in this function — reuse it.
- [X] T005 [P] Add `lot_text_save` view function to `src/catalog/views/panels.py` — accepts POST with `description` and/or `notes` fields, calls `save_lot_override` (merge logic handles preservation), re-fetches lot, returns `lots_table_row.html` with `oob=True` + HX-Trigger for `showToast`. Only include fields that are present in POST. Register URL `panels/lots/<int:lot_id>/text-save/` in `src/catalog/urls.py`.

**Checkpoint**: Template filters, font, merge-on-save, and modal text save endpoint are ready. User story implementation can begin.

---

## Phase 3: US1 — Simplified URL Routing (P1) 🎯 MVP

**Goal**: Only `/login/`, `/logout/`, `/no-access/`, `/` (SPA), and `/panels/*` URLs are accessible. All full-page routes removed. Navbar search form removed.

**Independent Test**: `curl` to `/sellers/`, `/events/1/`, `/lots/1/`, `/search/`, `/imports/` all return 404. `/` returns 200 (or 302→login). Panel endpoints still work.

- [X] T006 [US1] Remove URL patterns and their imports from `src/catalog/urls.py`: remove `seller_list` (the `/sellers/` path only — keep the `home` path), `seller_detail`, `event_detail`, `lot_detail`, `override_form`, `search_lots_view`, `import_list`, `import_file`, `upload_catalog`. Remove the corresponding import lines for views not used by any remaining URL.
- [X] T007 [US1] Simplify `seller_list` view in `src/catalog/views/sellers.py` — remove the `if request.path == "/":` branch and the full-page rendering code (the `else` branch at line 125). The view is now only called at `/` so it always renders the SPA shell. Remove unused filter_fields, preserved_params, and the full-page template reference.
- [X] T008 [US1] Remove navbar search form from `src/catalog/templates/catalog/shell.html` (or `base.html` if that's where `.nav-search` lives). Also remove `.nav-search` CSS rules from `src/catalog/static/catalog/styles.css` and the dropzone CSS (`.dropzone` rules) if no longer referenced.
- [X] T009 [US1] Update test assertions in `tests/` for removed URLs — any test that expects 200 from `/sellers/`, `/events/<id>/`, `/lots/<id>/`, `/search/`, `/imports/` should expect 404 or be removed. Verify panel endpoints still return 200.

**Checkpoint**: SPA-only routing. All dead-end full-page routes return 404.

---

## Phase 4: US4 — Remove Img Header & Vertical Gridlines (P1)

**Goal**: Clean table with no vertical column borders, only horizontal row separators. Image column has no header text.

**Independent Test**: Inspect lots table in browser. No vertical borders between cells. First `<th>` is empty.

- [X] T010 [P] [US4] Remove vertical gridlines in `src/catalog/static/catalog/styles.css` — change `.lots-table td { border: 1px solid #f1f5f9; }` (line 180) to `.lots-table td { border: none; border-bottom: 1px solid #f1f5f9; }`. Also update the earlier `.lots-table td` rule (line 162) to only have `border-bottom`.
- [X] T011 [P] [US4] Remove "Img" text from the first `<th>` in `src/catalog/templates/catalog/partials/lots_table.html` — change `<th>Img</th>` to `<th></th>`.

**Checkpoint**: Table visual cleanup complete.

---

## Phase 5: US6 — Larger Thumbnails (P1)

**Goal**: Lot thumbnails are 56×56px instead of 40×40px for better visibility.

**Independent Test**: Load lots with images. Thumbnails visually fill more row height. Hover preview still works.

- [X] T012 [US6] Increase thumbnail size in `src/catalog/static/catalog/styles.css` — change `.lot-thumb` width/height from `40px` to `56px`. Change `.lot-thumb-placeholder` width/height from `40px` to `56px`. Change `.lot-thumb-cell` width from `52px` to `68px`. Adjust `.lot-thumb-preview` left offset from `52px` to `68px`. Update `.lot-thumb-placeholder svg` size from `20px` to `28px`.

**Checkpoint**: Larger thumbnails rendering correctly.

---

## Phase 6: US2 — Clean Number Formatting (P1)

**Goal**: Weight and dimension values display as integers when whole (10 not 10.0).

**Independent Test**: Load a lot with wgt=10.0 → input shows "10". Load l=10.5 → shows "10.5".

- [X] T013 [US2] Apply `format_number` filter to all dimension/weight input values in `src/catalog/templates/catalog/partials/lots_table_row.html` — change `value="{{ row.fields.qty.value|default:"" }}"` to `value="{{ row.fields.qty.value|format_number }}"` for qty, l, w, h, wgt. Add `{% load catalog_tags %}` at top if not already present.

**Checkpoint**: Clean number display in dimension inputs.

---

## Phase 7: US3 — CPack Colored Badges (P1)

**Goal**: CPack values show as color-coded letter badges (NF/LF/F/VF/PBO) in Poppins 900.

**Independent Test**: Load lots with different cpack values. Each shows correct letter code in correct color with Poppins 900 font.

- [X] T014 [US3] Add CPack badge CSS to `src/catalog/static/catalog/styles.css` — add `.cpack-badge { font-family: 'Poppins', sans-serif; font-weight: 900; font-size: 0.75rem; letter-spacing: 0.02em; }` and color classes `.cpack-nf { color: #16a34a; }`, `.cpack-lf { color: #2563eb; }`, `.cpack-f { color: #d97706; }`, `.cpack-vf { color: #dc2626; }`, `.cpack-pbo { color: #7c3aed; }`.
- [X] T015 [US3] Replace cpack `<select>` option text in `src/catalog/templates/catalog/partials/lots_table_row.html` — change numeric options to letter codes: `1`→`NF`, `2`→`LF`, `3`→`F`, `4`→`VF`, `PBO`→`PBO`. Add `cpack-badge` class and initial `{{ row.fields.cpack.value|cpack_class }}` class to the `<select>` element.
- [X] T016 [US3] Add cpack select color-update-on-change JS handler in `src/catalog/templates/catalog/shell.html` — on `change` event for `select[name="cpack"]`, strip existing `cpack-*` classes and add the new class from the classMap (`{'1':'cpack-nf','2':'cpack-lf','3':'cpack-f','4':'cpack-vf','PBO':'cpack-pbo'}`). Add `cpack-badge` class. Per plan Phase G.

**Checkpoint**: CPack badges with distinct colors rendering correctly.

---

## Phase 8: US7 — Immutable Description Cell with Modal Launch (P1)

**Goal**: Description/notes column header reads "Lot Description". Description renders as immutable text. Clicking description cell opens the lot modal.

**Independent Test**: Verify description is plain text (no textarea). Click it → modal opens. Header says "Lot Description".

- [X] T017 [US7] Update column header in `src/catalog/templates/catalog/partials/lots_table.html` — change `<th>Desc/Notes</th>` to `<th>Lot Description</th>`.
- [X] T018 [US7] Replace description `<textarea>` with immutable display in `src/catalog/templates/catalog/partials/lots_table_row.html` — replace the `<textarea name="description" ...>` with a `<button type="button" class="lot-desc-text" hx-get="/panels/lots/{{ row.lot.id }}/detail/" hx-target="#lot-modal-body" hx-swap="innerHTML">{{ row.fields.description.value|default:"" }}</button>`. Keep the notes display below it but remove the "more" button (clicking the whole cell opens the modal). The description `<button>` must have `type="button"` so it doesn't trigger form submit.
- [X] T019 [US7] Add immutable description CSS in `src/catalog/static/catalog/styles.css` — add `.lot-desc-text` styles: `all: unset; cursor: pointer; display: block; width: 100%; text-align: left; font-size: 0.8125rem; color: #1e293b; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;`. On hover, add subtle highlight.

**Checkpoint**: Description is immutable text, clicks open modal.

---

## Phase 9: US5 — Merged Dimensions Column with Auto-Save (P2)

**Goal**: 5 dimension columns merged into 1. Per-input override styling. 15s inactivity auto-save while focused, immediate save on blur.

**Independent Test**: Single cell shows `{Qty} @ {L} x {W} x {H}, {Wgt} lbs` as inputs. Select-on-focus works. Tab order: qty→l→w→h→wgt. Change a value, leave row → saves immediately. Override styling only on changed inputs.

- [X] T020 [US5] Update column headers in `src/catalog/templates/catalog/partials/lots_table.html` — replace the 5 separate `<th>` entries (Qty, L, W, H, Wgt) with single `<th>Dimensions</th>`. Remove the `<th>Save</th>` column header (auto-save replaces it) or keep as `<th></th>` for the save button.
- [X] T021 [US5] Restructure dimension inputs into single merged cell in `src/catalog/templates/catalog/partials/lots_table_row.html` — replace the 5 separate `<td>` elements for qty/l/w/h/wgt with a single `<td>` containing a `<div class="lot-dims">`. Inside: `<input name="qty" type="number" value="{{ row.fields.qty.value|format_number }}" class="lot-input lot-input-num{% if row.fields.qty.changed %} lot-input-overridden{% endif %}" onfocus="this.select()">` then `<span class="lot-dims-sep">@</span>`, then l input with `step="any"`, `<span>x</span>`, w input, `<span>x</span>`, h input, `<span>,</span>`, wgt input with `step="any"` and class `lot-dims-wgt`, `<span>lbs</span>`.
- [X] T022 [US5] Replace per-cell `.overridden` class with per-input `.lot-input-overridden` class in `src/catalog/templates/catalog/partials/lots_table_row.html` — remove all `{% if row.fields.X.changed %} class="overridden" title="..."{% endif %}` from `<td>` elements. The override class is now on each `<input>` (done in T021 for dims). Apply the same pattern to the cpack `<select>`: add `{% if row.fields.cpack.changed %} lot-input-overridden{% endif %}` to its class. Same for checkboxes.
- [X] T023 [US5] Add override and dimensions CSS in `src/catalog/static/catalog/styles.css` — replace `.overridden { background: #fff3cd; }` with `.lot-input-overridden { border-left: 2px solid #f59e0b; padding-left: 0.25rem; }`. Add `.lot-dims` flex layout, `.lot-dims input` sizing (width: 3rem, text-align right), `.lot-dims-wgt` (width: 3.5rem), `.lot-dims-sep` (flex-shrink 0, user-select none, color #64748b, font-size 0.75rem).
- [X] T024 [US5] Update auto-save JS in `src/catalog/templates/catalog/shell.html` — change the existing row auto-save logic: (1) Add a 15-second inactivity timer that starts/resets on each `input`/`change` event while focus is in the row. If 15s pass with no input and focus is still in the row, trigger submit. (2) On `focusout`, if focus is leaving the row entirely (not moving to another element in the same row), save immediately (no 2s delay — change the current `setTimeout(fn, 2000)` to `setTimeout(fn, 0)` or call directly). (3) Cancel the 15s inactivity timer on focusout (blur save takes over).
- [X] T025 [US5] Update `lot_override_panel` in `src/catalog/views/panels.py` — remove the `description` and `notes` parsing from the inline save handler (lines 389-392) since these fields are no longer in the inline form. The merge-on-save logic in `save_lot_override` (T004) handles preserving existing text overrides. Remove the checkbox sentinel issue: since the inline form always includes checkboxes, existing behavior is fine. But verify that `force_crate` and `do_not_tip` are still handled correctly when the row form submits.

**Checkpoint**: Merged dimensions with auto-save. Override styling per-input. 15s debounce / immediate on blur.

---

## Phase 10: US8 — Upgraded Lot Modal with Auto-Save (P2)

**Goal**: Modal shows image gallery → editable description → editable notes → data summary. Text auto-saves on blur. No "Edit" step for text.

**Independent Test**: Open modal → gallery at top, description textarea, notes textarea. Edit description, tab to notes → description auto-saves, table row updates. Close modal → notes auto-saves.

- [X] T026 [US8] Add `lot_description` and `lot_notes` context variables to `lot_detail_panel` GET handler in `src/catalog/views/panels.py` — compute effective values (override if present, else initial) for description and notes. Pass them as separate template context variables alongside the existing `rows` and `has_override`. Remove description and notes from `_LOT_DETAIL_FIELDS` (they're displayed separately now, not in the data table).
- [X] T027 [US8] Restructure `src/catalog/templates/catalog/partials/lot_detail_modal.html` — replace current layout with: (1) Image gallery header using CSS scroll-snap (`div.lot-gallery` with `img` for each `lot.image_links`), thumbnail strip below if >1 image. (2) Description section: `<h3>Description</h3>` then `<textarea name="description" class="lot-modal-textarea" hx-post="/panels/lots/{{ lot.id }}/text-save/" hx-trigger="change" hx-swap="none" hx-headers='{"X-CSRFToken":"{{ csrf_token }}"}'>{{ lot_description|default:"" }}</textarea>`. (3) Notes section: same pattern with `name="notes"` and `{{ lot_notes }}`. (4) Data summary table (read-only, from `rows`). (5) Optional "Edit Details" button linking to `?edit=1` for power fields (value, conditions, commodity_id). Remove `data-lot-title` attribute setup since the title should still show lot number.
- [X] T028 [US8] Add image gallery CSS in `src/catalog/static/catalog/styles.css` — add `.lot-gallery` (flex, overflow-x auto, scroll-snap-type x mandatory, max-height 300px, border-radius 8px 8px 0 0, background #f1f5f9), `.lot-gallery img` (scroll-snap-align start, flex-shrink 0, width 100%, max-height 300px, object-fit contain), `.lot-gallery-thumbs` and `.lot-gallery-thumbs img` per plan Phase D. Add `.lot-modal-section` (padding 1rem 0), `.lot-modal-textarea` (width 100%, min-height 4rem, border 1px solid #e2e8f0, border-radius 4px, padding 0.5rem, font-family inherit, font-size 0.9rem, resize vertical, line-height 1.5). Add `.lot-gallery-empty` placeholder styles for lots with no images.
- [X] T029 [US8] Add gallery thumbnail navigation JS in `src/catalog/templates/catalog/shell.html` — add `window.scrollToGalleryImage` function that scrolls the gallery to the image at the given index using `scrollIntoView({behavior:'smooth', inline:'start'})`, updates `.active` class on thumbnail strip. Per plan Phase G.
- [X] T030 [US8] Simplify `src/catalog/templates/catalog/partials/lot_edit_modal.html` — if keeping the "Edit Details" view, remove description and notes fields from the form (they're auto-saved via the detail modal). The edit form should only show: qty, l, w, h, wgt, value, cpack, noted_conditions, commodity_id, force_crate, do_not_tip. Update `OverrideForm` in `src/catalog/forms.py` if needed (or just hide desc/notes from the template). Alternatively, if the "Edit Details" button is not kept, delete this template entirely.
- [X] T031 [US8] Handle concurrent save queueing in `src/catalog/templates/catalog/shell.html` — add a per-lot save lock (e.g., `data-saving` attribute on the `<tr>` or a JS Map). Before triggering a save (inline or modal), check if a save is already in flight. If so, queue the save to fire after the current one completes. Use `htmx:afterRequest` or `htmx:afterSwap` events to detect completion and fire queued saves. This prevents concurrent saves for the same lot per edge case spec.

**Checkpoint**: Modal with gallery, auto-save description/notes, data summary. Table rows update on save.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, test verification, and cross-story consistency.

- [X] T032 Remove unused CSS rules from `src/catalog/static/catalog/styles.css` — clean up `.overridden` (if still present after T023), `.lot-input-wide` (textarea was using this), and any dead `.lot-desc-title`/`.lot-desc-notes` classes that were replaced.
- [X] T033 Remove the dropzone UI element from `src/catalog/templates/catalog/shell.html` (or wherever the import dropzone lives) since import routes are removed (US1). Remove `.dropzone` CSS from `src/catalog/static/catalog/styles.css`.
- [X] T034 Run full test suite: `.venv/bin/python -m pytest tests/ -v` — fix any regressions from template changes, URL removals, or panels.py modifications.
- [X] T035 Run quickstart.md manual testing checklist against the running dev server to validate all 8 user stories.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 2 (Foundational)**: No dependencies — start immediately
- **Phase 3 (US1)**: Depends on Phase 2 completion (T005 adds URL to urls.py)
- **Phase 4 (US4)**: Depends on Phase 2 only
- **Phase 5 (US6)**: Depends on Phase 2 only
- **Phase 6 (US2)**: Depends on Phase 2 (T002 format_number filter)
- **Phase 7 (US3)**: Depends on Phase 2 (T001 Poppins font, T003 cpack filters)
- **Phase 8 (US7)**: Depends on Phase 2 only — restructures description cell
- **Phase 9 (US5)**: Depends on US2 (format_number in inputs), US4 (gridlines removed), US7 (description cell restructured) — merges dimension columns
- **Phase 10 (US8)**: Depends on US7 (modal launch from description click), Phase 2 (T005 text-save endpoint)
- **Phase 11 (Polish)**: Depends on all story phases complete

### User Story Dependencies

- **US1 (P1)**: Independent — can start after foundational
- **US4 (P1)**: Independent — can run parallel with US1
- **US6 (P1)**: Independent — can run parallel with US1, US4
- **US2 (P1)**: Independent — can run parallel (filter already done in foundational)
- **US3 (P1)**: Independent — can run parallel (filters + font done in foundational)
- **US7 (P1)**: Independent — can run parallel with above (touches description cell only)
- **US5 (P2)**: Depends on US2, US4, US7 — merges dims and restructures row template significantly
- **US8 (P2)**: Depends on US7 — uses modal launch from description click. Also depends on T005 (text-save endpoint).

### Within Each User Story

- CSS before templates (styles must exist before templates reference classes)
- Templates before JS (elements must exist before JS targets them)
- Backend before frontend (endpoints must exist before HTMX targets them)

### Parallel Opportunities

Within Phase 2 (Foundational):
- T002 and T003 can run in parallel (different filter functions in same file — but same file, so mark [P] only if separate write operations are possible)
- T001 is in a different file (base.html) — truly parallel
- T005 is in panels.py + urls.py — truly parallel with T001–T003

P1 stories (US1, US4, US6, US2, US3, US7) touch mostly different areas:
- US1 (urls.py, sellers.py, shell.html) — no conflict with US4/US6/US2
- US4 (styles.css line 180, lots_table.html header) — minimal conflict
- US6 (styles.css thumb sizes) — no conflict with US4
- US2 (lots_table_row.html input values) — independent cell changes
- US3 (lots_table_row.html cpack cell, styles.css, shell.html) — independent cell
- US7 (lots_table.html header, lots_table_row.html desc cell, styles.css) — independent cell

---

## Parallel Example: P1 Stories

```text
# After Phase 2 completes, these can run in parallel:
Agent 1: US1 (T006, T007, T008, T009) — URL cleanup
Agent 2: US4 (T010, T011) + US6 (T012) — visual cleanup (different CSS sections)
Agent 3: US2 (T013) + US3 (T014, T015, T016) — number/cpack formatting
Agent 4: US7 (T017, T018, T019) — description cell restructure

# After P1 stories complete:
Agent 1: US5 (T020–T025) — merged dimensions + auto-save
Agent 2: US8 (T026–T031) — modal upgrade + auto-save

# Both depend on US7 but touch different files:
# US5 → lots_table_row.html (dims cells), shell.html (auto-save JS), panels.py (inline save)
# US8 → lot_detail_modal.html, shell.html (gallery JS), panels.py (detail context)
# Caution: shell.html and panels.py are shared — coordinate if truly parallel.
```

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 2: Foundational (T001–T005)
2. Complete Phases 3–8: All P1 stories (US1, US4, US6, US2, US3, US7)
3. **STOP and VALIDATE**: Test all P1 changes — SPA-only routing, clean formatting, cpack badges, no gridlines, larger thumbs, immutable description
4. Deploy if ready — the table is already improved, modal upgrade comes next

### Full Delivery

5. Complete Phase 9: US5 (merged dimensions + auto-save)
6. Complete Phase 10: US8 (modal upgrade + auto-save)
7. Complete Phase 11: Polish
8. Run full test suite + quickstart validation

---

## Notes

- `lots_table_row.html` is the most-modified file — 6 stories touch it. Execute US5 (merged dims) AFTER all P1 stories to avoid merge conflicts.
- `shell.html` JS is modified by US1 (search removal), US3 (cpack handler), US5 (auto-save), US8 (gallery + modal save). Coordinate additions carefully.
- `save_lot_override` merge logic (T004) is the critical data integrity foundation — test thoroughly before proceeding to US5/US8.
- The `lot_edit_modal.html` template may become dead code after US8. Decision on keeping or removing is in T030.
- The Save button column is preserved in the table as a manual trigger + visual status indicator. Auto-save is the primary mechanism.

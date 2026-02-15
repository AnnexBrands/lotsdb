# Tasks: Lots Modal Overhaul

**Input**: Design documents from `/specs/017-lots-modal-overhaul/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — contract tests for the modified endpoint context per plan.md Phase 5.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Backend + Base CSS)

**Purpose**: Update the backend view context and modal base CSS that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T001 [P] Update `lot_detail_panel()` GET handler in `src/catalog/views/panels.py` to pass a `fields` dict (same structure as `build_lot_table_rows()` output: `{field_name: {value, changed, original}}`) instead of the read-only `rows` list. Keep `lot`, `lot_description`, `lot_notes` in context. Keep `?edit=1` branch for backward compat. Reuse `build_lot_table_rows([lot])` and extract `result[0]["fields"]` (or equivalent) to build the fields dict. POST handler unchanged.
- [X] T002 [P] Increase modal max-width from 700px to 840px in `src/catalog/static/catalog/styles.css`. Change `dialog#lot-modal { max-width: 700px; ... }` to `max-width: 840px`. No other changes in this task.

**Checkpoint**: Backend passes `fields` dict, modal is wider — ready for template rewrite

---

## Phase 2: User Story 1 — Redesigned Modal Layout with Gallery and Override Form (Priority: P1) 🎯 MVP

**Goal**: Two-column hero layout: image gallery (left 45%), description + notes + inline override form (right 55%). Modal centered both axes. Override form has same fields as lots table row (qty, L, W, H, wgt, cpack, force_crate, do_not_tip) with initial value refs and save button.

**Independent Test**: Open any lot modal → verify gallery left + info/form right, save override → table row updates, responsive stacking on narrow viewport.

**Covers**: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-014, FR-015

### Implementation for User Story 1

- [X] T003 [P] [US1] Add hero layout CSS to `src/catalog/static/catalog/styles.css`. Add styles for: `.lot-hero` (CSS grid `grid-template-columns: 45% 1fr`, `min-height: 260px`), `.lot-gallery-main` (flex center, overflow hidden, min-height 200px, `max-height: 240px` for `img`), `.lot-info` (flex column, padding `1.25rem 1.5rem`, gap `0.5rem`), `.lot-desc-title` (font-size `0.9375rem`, font-weight 600, color `#1e293b`), `.lot-desc-notes` (font-size `0.8125rem`, color `#64748b`, line-height 1.6). Add `@media (max-width: 768px) { .lot-hero { grid-template-columns: 1fr; } }` responsive breakpoint. Reference mockup: `/usr/src/BrandGuidelines/mockups/autoparser/modals/m6-full-composite.html` lines 65–118.

- [X] T004 [P] [US1] Add override form CSS to `src/catalog/static/catalog/styles.css`. Add styles for: `.override-row` (margin-top `0.75rem`, padding-top `0.75rem`, border-top `1px solid #e2e8f0`), `.initial-ref` (font-size `0.625rem`, color transparent, text-align center, min-height `0.75rem`), `.initial-changed` (color `#d97706`, font-weight 400), `.override-controls` (flex, align-items center, gap `0.75rem`, margin-top `0.5rem`), `.override-flag` (flex, align-items center, gap `0.25rem`, font-size `0.75rem`, color `#475569`, cursor pointer), `.override-flag input[type="checkbox"]` (width/height 14px, accent-color `#3b82f6`), `.btn-save` (margin-left auto, padding `0.3125rem 0.75rem`, background `#3b82f6`, color white, border-radius `6px`, font-size `0.75rem`). Also add `.modal-body .lot-dims` styles to work in modal context (the `.lot-dims`, `.lot-dims-field`, `.lot-dims-label`, `.lot-dims-sep` classes already exist from lots_table_row — ensure they render correctly inside `.lot-info`). Reference mockup lines 120–205.

- [X] T005 [US1] Rewrite `src/catalog/templates/catalog/partials/lot_detail_modal.html` with the hero section. Structure: outer `<div data-lot-title="Lot {{ lot.catalogs.0.lot_number|default:lot.id }}">`, then `<div class="lot-hero">` containing: (1) `.lot-gallery` div with `.lot-gallery-main` holding a single `<img id="modal-main-img">` showing first image, and `.lot-gallery-thumbs` strip with `{% for img in lot.image_links %}` thumbnails (same as current template but thumbnails use `onclick` to call gallery swap function), and empty state `{% else %}` block with placeholder SVG + "No images" text; (2) `.lot-info` div with `.lot-desc-title` showing `{{ lot_description|default:"No description" }}`, `.lot-desc-notes` showing `{{ lot_notes }}`, description/notes `<textarea>` elements with `hx-post="/panels/lots/{{ lot.id }}/text-save/"` `hx-trigger="change"` `hx-swap="none"` (preserving existing auto-save), and `<form class="override-row">` with `hx-post="/panels/lots/{{ lot.id }}/detail/"` `hx-target="#lot-modal-body"` `hx-swap="innerHTML"` containing: `{% csrf_token %}`, `.lot-dims` div with Qty/L/W/H/Wgt inputs (matching `lots_table_row.html` field names and layout exactly — use `fields.qty.value|format_number`, `lot-input-overridden` class when `fields.qty.changed`, initial ref `<span class="initial-ref{% if fields.qty.changed %} initial-changed{% endif %}">{{ fields.qty.original|format_number }}</span>` below each input), CPack `<select>` dropdown (same options as lots_table_row: —/NF/LF/F/VF/PBO with cpack_class filter), `.override-controls` div with Force Crate and Do Not Tip checkbox labels (`.override-flag`) and Save button (`.btn-save`). Use `{% load catalog_tags %}` for template filters. Single image edge case: hide thumbnail strip if only 1 image (`{% if lot.image_links|length > 1 %}`).

- [X] T006 [US1] Update gallery thumbnail JS in `src/catalog/templates/catalog/shell.html`. Replace or update the existing `scrollToGalleryImage` function with a new approach: on thumbnail click inside `#lot-modal-body`, get the clicked thumbnail's `<img>` src, set `#modal-main-img` src to that value, toggle `.active` class on thumbnails. Use event delegation: add a click listener on `document.body` that checks if `e.target.closest('.lot-gallery-thumb')` is inside `#lot-modal-body`. This replaces the scroll-snap approach with a main-image-swap approach per the mockup.

**Checkpoint**: US1 complete — modal opens with two-column hero, gallery navigates, override form saves, responsive layout works

---

## Phase 3: User Story 2 — Recommendation Engine with Low/Med/High Suggestions (Priority: P2)

**Goal**: Below the hero section, display three sizing suggestion cards (Minimum, Recommended, Oversize) with placeholder data and a "Quoter Pending" badge.

**Independent Test**: Open any lot modal → scroll below hero → verify three cards visible, Recommended highlighted, "Quoter Pending" badge shown.

**Covers**: FR-008, FR-009

### Implementation for User Story 2

- [X] T007 [P] [US2] Add quoter card CSS to `src/catalog/static/catalog/styles.css`. Add styles for: `.modal-body .section` (padding `1rem 1.5rem`, border-top `1px solid #e2e8f0`), `.modal-body .section h3` (font-size `0.6875rem`, font-weight 600, text-transform uppercase, letter-spacing `0.05em`, color `#94a3b8`, margin-bottom `0.625rem`), `.quoter-grid` (display grid, `grid-template-columns: 1fr 1fr 1fr`, gap `0.5rem`), `.quoter-card` (border `1px solid #e2e8f0`, border-radius `6px`, padding `0.625rem`, text-align center, background `#fafbfc`), `.quoter-card.recommended` (border-color `#3b82f6`, background `#eff6ff`), `.quoter-card-label` (font-size `0.5625rem`, font-weight 600, uppercase, letter-spacing `0.05em`, color `#94a3b8`), `.quoter-card.recommended .quoter-card-label` (color `#3b82f6`), `.quoter-card-dims` (font-size `0.9375rem`, font-weight 600, color `#1e293b`), `.quoter-card-type` (font-size `0.6875rem`, color `#64748b`), `.placeholder-badge` (inline-flex, font-size `0.5625rem`, font-weight 600, uppercase, color `#92400e`, background `#fef3c7`, padding `1px 6px`, border-radius `3px`, margin-left `0.375rem`). Add `@media (max-width: 600px) { .quoter-grid { grid-template-columns: 1fr; } }`. Reference mockup lines 207–268.

- [X] T008 [US2] Add recommendation section HTML to `src/catalog/templates/catalog/partials/lot_detail_modal.html` below the `.lot-hero` closing div. Add: `<div class="section"><h3>Box Sizing & Pack Options <span class="placeholder-badge">Quoter Pending</span></h3><div class="quoter-grid">` with three `.quoter-card` divs — first: label "Minimum", dims "20 x 30 x 111", type "Standard Pack"; second: `.quoter-card.recommended`, label "Recommended", dims "24 x 34 x 115", type "Full Crate (VF)"; third: label "Oversize", dims "28 x 38 x 119", type "Custom Crate". Close the grid and section divs. These are hardcoded placeholder values per spec assumption.

**Checkpoint**: US2 complete — recommendation section renders below hero with 3 cards, Recommended visually distinct

---

## Phase 4: User Story 3 — Related Lots Gallery with Card Stacks (Priority: P3)

**Goal**: Below the recommendation section, display three columns (Q25 Low, Q50 Median, Q75 High) of browsable card stacks with placeholder data. Each card shows image, lot title, dimensions, weight, cpack, and an Accept button. Navigation cycles cards. Accept copies values into the override form above.

**Independent Test**: Open lot modal → scroll to bottom → verify 3 columns with stacked cards, navigate cards, click Accept → override form fields update.

**Covers**: FR-010, FR-011, FR-012, FR-013

### Implementation for User Story 3

- [X] T009 [P] [US3] Add card stack CSS to `src/catalog/static/catalog/styles.css`. Add styles for: `.stacks-grid` (display grid, `grid-template-columns: 1fr 1fr 1fr`, gap `0.5rem`), `.stack-col-label` (font-size `0.5625rem`, font-weight 600, uppercase, text-align center, margin-bottom `0.375rem`, flex center with gap `0.375rem`), `.stack-col-label .tag` (font-size `0.5rem`, font-weight 700, padding `1px 5px`, border-radius `3px`), color variants for Q25 (`.q25-label { color: #16a34a }`, `.q25-label .tag { background: #f0fdf4 }`), Q50 (`.q50-label { color: #2563eb }`, `.q50-label .tag { background: #eff6ff }`), Q75 (`.q75-label { color: #d97706 }`, `.q75-label .tag { background: #fffbeb }`), `.card-stack` (position relative, height `200px`), `.stack-card` (position absolute, left/right 0, border `1px solid #e2e8f0`, border-radius `6px`, overflow hidden, background white, transition transform/opacity `0.3s ease`), `.stack-card[data-pos="0"]` (z-index 3, translateY(0), opacity 1, box-shadow), `.stack-card[data-pos="1"]` (z-index 2, translateY(6px) scale(0.97), opacity 0.7), `.stack-card[data-pos="2"]` (z-index 1, translateY(12px) scale(0.94), opacity 0.4), `.stack-card[data-pos="hidden"]` (translateY(16px) scale(0.91), opacity 0, pointer-events none), `.stack-card-img` (height `68px`, background `#f1f5f9`, overflow hidden), `.stack-card-body` (padding `0.375rem 0.5rem`), `.stack-card-lot` (font-size `0.625rem`, font-weight 600, color `#64748b`, truncate), `.stack-card-dims` (font-size `0.6875rem`, color `#1e293b`), `.stack-card-meta` (flex, gap `0.375rem`), `.stack-card-wgt` (font-size `0.625rem`, color `#94a3b8`), `.cpack-pill` + variants (`.cpack-pill-nf/lf/f/vf` with matching colors from existing cpack palette), `.stack-card-accept` (full width, padding `0.1875rem`, border `1px solid #e2e8f0`, border-radius `3px`, background white, color `#3b82f6`, font-size `0.6875rem`, hover state), `.stack-nav` (flex center, gap `0.25rem`, margin-top `0.375rem`), `.stack-nav-btn` (20x20px, border `1px solid #e2e8f0`, border-radius `4px`, disabled opacity 0.3), `.stack-counter` (font-size `0.5rem`, color `#94a3b8`), `.future-badge` (same as placeholder-badge but purple: color `#7e22ce`, background `#f3e8ff`). Reference mockup lines 270–414.

- [X] T010 [US3] Add related lots section HTML to `src/catalog/templates/catalog/partials/lot_detail_modal.html` below the recommendation section. Add: `<div class="section"><h3>Related Lots <span class="future-badge">Similarity Matching</span></h3><div class="stacks-grid">` with three `.stack-column[data-stack="q25|q50|q75"]` divs. Each column has: `.stack-col-label` with colored `.tag` span + "Low"/"Median"/"High" text, `.card-stack` with 2-3 placeholder `.stack-card` elements (each with `data-pos="0|1|2"`, `data-l`, `data-w`, `data-h`, `data-wgt`, `data-cpack` attributes for Accept button, containing `.stack-card-img` with placeholder image, `.stack-card-body` with lot title, dims, weight, cpack pill, and `.stack-card-accept` button), and `.stack-nav` with up/down buttons (`.stack-nav-btn[data-dir="up|down"]`, up disabled initially) and `.stack-counter` showing "1/N". Use realistic placeholder data matching the mockup examples (e.g., "ROSEWOOD POLE SCREENS", "VICTORIAN WHATNOT SHELF", etc.).

- [X] T011 [US3] Add card stack navigation JS in `src/catalog/templates/catalog/shell.html`. Use event delegation on `document.body` for click events. When a `.stack-nav-btn` inside `#lot-modal-body` is clicked: find the parent `.stack-column`, get all `.stack-card` elements, track current index, increment/decrement based on `data-dir` attribute, update `data-pos` attributes on all cards (pos 0 = front, 1 = behind, 2 = further behind, "hidden" = invisible), update `.stack-counter` text to "N/total", disable up button when at first card, disable down button when at last card. Match the mockup's JS logic (lines 864-891 of m6-full-composite.html).

- [X] T012 [US3] Add Accept button JS in `src/catalog/templates/catalog/shell.html`. Use event delegation on `document.body` for click events. When a `.stack-card-accept` button inside `#lot-modal-body` is clicked: find the parent `.stack-card`, read `data-l`, `data-w`, `data-h`, `data-wgt`, `data-cpack` attributes, find the override form inside `#lot-modal-body` (`.override-row`), set the corresponding input values (`input[name="l"]`, `input[name="w"]`, etc.), for cpack set the `<select>` value and trigger a change event to update the color class. Visually indicate the form has been modified (e.g., add a brief highlight or rely on existing dirty-state detection).

**Checkpoint**: US3 complete — related lots section renders with 3 navigable card stack columns, Accept populates override form

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Tests, validation, and cleanup

- [X] T013 Update contract tests in `tests/contract/test_panels.py`. Add or update tests: (1) `test_lot_detail_panel_returns_fields_context` — mock `services.get_lot()` returning a lot with initial_data, verify GET response context contains `fields` dict with keys `qty`, `l`, `w`, `h`, `wgt`, `cpack`, `force_crate`, `do_not_tip`, each having `value`, `changed`, `original` keys; (2) `test_lot_detail_panel_fields_show_override_diff` — mock a lot with differing override, verify `changed` is True for modified fields; (3) `test_lot_detail_panel_description_notes_context` — verify `lot_description` and `lot_notes` context values use override when present, initial when not; (4) verify existing POST test (`test_lot_detail_panel_post_saves_override`) still passes.
- [X] T014 Run full test suite (`pytest` from repo root) and validate all tests pass. Manually verify against quickstart.md test procedures for each priority level (P1 hero layout, P2 recommendation cards, P3 card stacks + Accept).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately. BLOCKS all user stories.
- **US1 (Phase 2)**: Depends on Phase 1 completion (needs `fields` context + wider modal).
- **US2 (Phase 3)**: Depends on US1 completion (adds section below hero in same template).
- **US3 (Phase 4)**: Depends on US2 completion (adds section below recommendation in same template, Accept button writes into US1's override form).
- **Polish (Phase 5)**: Depends on all user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only. MVP — independently testable.
- **US2 (P2)**: Depends on US1 (template structure). Adds to the template built in US1.
- **US3 (P3)**: Depends on US2 (template structure) + US1 (override form for Accept). Adds to the template built in US1+US2.

### Within Each Phase — Parallel Opportunities

**Phase 1 (Foundational)**:
- T001 (panels.py) and T002 (styles.css) — different files, run in parallel

**Phase 2 (US1)**:
- T003 (styles.css) and T004 (styles.css) — same file, run sequentially
- T005 (lot_detail_modal.html) depends on T001 (backend context) — run after T001
- T006 (shell.html) depends on T005 (template has gallery elements) — run after T005

**Phase 3 (US2)**:
- T007 (styles.css) and T008 (lot_detail_modal.html) — different files, run in parallel

**Phase 4 (US3)**:
- T009 (styles.css) can run parallel with T010 (lot_detail_modal.html)
- T011 (shell.html) depends on T010 — run after T010
- T012 (shell.html) depends on T011 — run after T011 (same file)

---

## Parallel Example: Phase 1

```
# Launch both foundational tasks in parallel:
Task T001: "Update lot_detail_panel() GET handler in src/catalog/views/panels.py"
Task T002: "Increase modal max-width to 840px in src/catalog/static/catalog/styles.css"
```

## Parallel Example: Phase 3 (US2)

```
# Launch CSS and template tasks in parallel:
Task T007: "Add quoter card CSS to src/catalog/static/catalog/styles.css"
Task T008: "Add recommendation section HTML to src/catalog/templates/catalog/partials/lot_detail_modal.html"
```

## Parallel Example: Phase 4 (US3)

```
# Launch CSS and template tasks in parallel:
Task T009: "Add card stack CSS to src/catalog/static/catalog/styles.css"
Task T010: "Add related lots section HTML to src/catalog/templates/catalog/partials/lot_detail_modal.html"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational (T001-T002)
2. Complete Phase 2: User Story 1 (T003-T006)
3. **STOP and VALIDATE**: Open lot modal → two-column hero with gallery + override form works
4. Deploy/demo if ready — operators can already use the improved modal

### Incremental Delivery

1. Phase 1 → Foundation ready
2. Phase 2 → US1 complete → **MVP: improved modal layout with inline editing** ✅
3. Phase 3 → US2 complete → Recommendation engine placeholder visible
4. Phase 4 → US3 complete → Related lots with card stacks and Accept
5. Phase 5 → Tests pass, quickstart validated → Production ready

### Single Developer Flow

All stories are sequential (same template file). Optimal order:
1. T001 + T002 (parallel) → T003 → T004 → T005 → T006 → T007 + T008 (parallel) → T009 + T010 (parallel) → T011 → T012 → T013 → T014

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- US2 and US3 depend on US1 because they add sections to the same template file
- Recommendation engine and related lots are placeholder HTML only — no backend integration
- Override form POSTs to existing `/panels/lots/{id}/detail/` endpoint — no new backend routes
- All CSS references the mockup at `/usr/src/BrandGuidelines/mockups/autoparser/modals/m6-full-composite.html`
- Commit after each phase or logical task group

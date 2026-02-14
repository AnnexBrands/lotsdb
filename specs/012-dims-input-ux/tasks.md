# Tasks: Dimensions Input UX

**Input**: Design documents from `/specs/012-dims-input-ux/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/dims-rendering.md, quickstart.md

**Tests**: Included — contract tests validate the rendering contract.

**Organization**: Both user stories are P1 and share the same files (template + CSS), so they are implemented together in a single phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Template Structure (US1 + US2)

**Goal**: Restructure the dimensions cell HTML to wrap each input in a `.lot-dims-field` container with a `.lot-dims-label` span, and add the "in" unit separator after H.

**Independent Test**: Load the lots table — each dim input should have a label above it, separators should include "in" after H, and all input `name` attributes remain unchanged.

- [X] T001 [US1] [US2] Update dimensions cell markup in src/catalog/templates/catalog/partials/lots_table_row.html — wrap each input (qty, l, w, h, wgt) in a `<div class="lot-dims-field">` with a `<span class="lot-dims-label">` above it; change the comma separator after H to "in" followed by ","

**Checkpoint**: Template renders with new structure; existing auto-save and override behavior unaffected (input names unchanged).

---

## Phase 2: CSS Styling (US1 + US2)

**Goal**: Add new CSS classes for floating labels and field wrappers; update separator and input width styling for muted appearance and no-truncation.

- [X] T002 [P] [US1] [US2] Add `.lot-dims-field` and `.lot-dims-label` styles in src/catalog/static/catalog/styles.css — `.lot-dims-field`: flex column, align-items center, gap 0; `.lot-dims-label`: font-size 0.5625rem (9px), font-weight 400, color #94a3b8, line-height 1, user-select none
- [X] T003 [P] [US1] Update `.lot-dims-sep` in src/catalog/static/catalog/styles.css — change color from #64748b to #94a3b8, add font-weight 400, align-self flex-end with padding-bottom to align with inputs
- [X] T004 [P] [US1] Update `.lot-dims-input` and `.lot-dims-wgt` widths in src/catalog/static/catalog/styles.css — change `.lot-dims-input` from `width: 3rem` to `min-width: 5ch; width: auto`, change `.lot-dims-wgt` from `width: 3.5rem` to `min-width: 6ch; width: auto`
- [X] T005 [US1] Update `.lot-dims` container in src/catalog/static/catalog/styles.css — change `align-items: center` to `align-items: flex-end` so separators align with input baselines rather than label tops

**Checkpoint**: Dims cell renders with muted labels and separators, inputs are wide enough for large values, layout aligned at input baseline.

---

## Phase 3: Contract Tests

**Goal**: Validate the rendering contract with automated tests.

- [X] T006 [US2] Add contract test for floating labels in tests/contract/test_panels.py — verify each dim input has a sibling `.lot-dims-label` element with correct text ("Qty", "L", "W", "H", "Wgt")
- [X] T007 [US1] Add contract test for separator tokens in tests/contract/test_panels.py — verify `.lot-dims-sep` elements contain "@", "x", "x", "in", ",", "lbs" in order
- [X] T008 [US1] Update existing TestOverrideCellsContract in tests/contract/test_panels.py — ensure override class `.lot-input-overridden` still applies correctly within the new `.lot-dims-field` wrapper

**Checkpoint**: All 89 existing tests + new contract tests pass.

---

## Phase 4: Polish & Validation

**Purpose**: Final verification across all user stories.

- [X] T009 Run full test suite and fix any regressions via `python -m pytest tests/ -v`
- [X] T010 Run quickstart.md manual validation — verify LTR layout, floating labels, muted separators, no truncation, override indicators, and auto-save

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Template)**: No dependencies — start immediately
- **Phase 2 (CSS)**: Can run in parallel with Phase 1 (different files) — tasks T002-T005 are all in styles.css so T002-T004 are parallel, T005 sequential after
- **Phase 3 (Tests)**: Depends on Phase 1 + Phase 2 completion
- **Phase 4 (Polish)**: Depends on Phase 3 completion

### Parallel Opportunities

```text
# Phase 1 + Phase 2 can start simultaneously (different files):
T001 (template)  ←→  T002, T003, T004 (CSS, all [P])

# Within Phase 2, T002-T004 are parallel (different CSS rules):
T002 (field + label styles)  ||  T003 (separator styles)  ||  T004 (input widths)
# T005 depends on T002 being done (same .lot-dims rule)

# Phase 3 tests after both phases complete:
T006, T007, T008 (sequential — same test file)
```

## Implementation Strategy

### MVP (Single Pass)

This is a small feature — all tasks can be completed in a single pass:

1. T001: Update template structure (adds wrappers + labels + "in" separator)
2. T002-T005: Update CSS (new classes + style updates)
3. T006-T008: Add/update contract tests
4. T009-T010: Validate

Total: 10 tasks across 2 source files + 1 test file.

---

## Notes

- Both user stories (US1: muted separators + wide inputs, US2: floating labels) modify the same two files, so they are co-implemented rather than separated into independent phases.
- No backend, JavaScript, or data model changes required.
- Input `name` attributes MUST NOT change — the override save endpoint depends on them.

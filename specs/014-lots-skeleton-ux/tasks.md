# Tasks: Lots Panel Skeleton Loading

**Input**: Design documents from `/specs/014-lots-skeleton-ux/`
**Prerequisites**: plan.md, spec.md, research.md, contracts/lots-skeleton.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: User Story 1 — Skeleton loading on event click (Priority: P1) MVP

**Goal**: When a user clicks an event, the lots panel immediately shows skeleton rows matching the table column structure (thumbnail, description, dimensions, cpack, crate, dnt, action) before real data loads.

**Independent Test**: Click an event → lots panel shows 4 skeleton rows with column-matched placeholders → real data replaces skeletons cleanly.

- [X] T001 [P] [US1] Add skeleton table CSS classes (`.skeleton-table-row` for row height/spacing, `.skeleton-thumb` for 56x56 rounded thumbnail placeholder) in `src/catalog/static/catalog/styles.css` — reuse existing `skeleton-bar` and `skeleton-pulse` animation
- [X] T002 [P] [US1] Build the lots skeleton HTML string in `src/catalog/templates/catalog/shell.html` — a `<table class="lots-table">` with real `<thead>` (matching `lots_table.html` headers) and `<tbody>` containing 4 skeleton `<tr>` rows, each with 7 `<td>` cells: thumbnail placeholder, description bars (title ~60% + notes ~40%), dims bar cluster, cpack bar, crate bar, dnt bar, empty action cell
- [X] T003 [US1] Add `htmx:beforeRequest` event listener in `src/catalog/templates/catalog/shell.html` that injects the skeleton HTML into `#panel-main-content` when the triggering element is a `.panel-item` inside `#panel-left2` (events panel) and the target is `#panel-main-content` — per research R3 trigger condition

**Checkpoint**: Clicking an event shows skeleton table rows; real data replaces them on HTMX response.

---

## Phase 2: User Story 3 — Stable event sort order (Priority: P1)

**Goal**: Fix the OOB events swap so the events list maintains start_date descending sort order when clicking an event.

**Independent Test**: Click through several events → events list order remains stable; only the active highlight changes.

- [X] T004 [US3] Sort OOB events by `start_date` descending in `event_lots_panel()` in `src/catalog/views/panels.py` — add `events_result.items.sort(key=lambda e: e.start_date or "", reverse=True)` before passing `oob_events` to template context (matching the sort already applied in `seller_events_panel()`)

**Checkpoint**: Events list order stays stable when clicking through events.

---

## Phase 3: User Story 2 — No regression on seller click (Priority: P2)

**Goal**: Verify seller clicks still show the "Select an event" empty state, not skeleton rows.

**Independent Test**: Click a seller while viewing lots → lots panel shows empty state message, not skeleton.

- [X] T005 [US2] Verify that the existing seller-click `htmx:beforeRequest` handler in `src/catalog/templates/catalog/shell.html` (which sets `mainEmptyHTML`) still takes precedence — the new event-click handler must NOT fire for seller clicks because the trigger element is a `.panel-item` inside `#panel-left1`, not `#panel-left2`

**Checkpoint**: Seller clicks produce empty state in lots panel, not skeleton rows.

---

## Phase 4: Polish & Verification

- [X] T006 Run `cd src && python -m pytest ../tests/ -v` to confirm all existing tests pass
- [X] T007 Run manual verification per `specs/014-lots-skeleton-ux/quickstart.md` — skeleton loading, seller click regression, event sort stability

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)**: No dependencies — can start immediately
- **Phase 2 (US3)**: No dependencies — can run in parallel with Phase 1 (different file)
- **Phase 3 (US2)**: Depends on Phase 1 completion (verifies the skeleton listener doesn't fire for seller clicks)
- **Phase 4 (Polish)**: Depends on all phases complete

### Parallel Opportunities

- T001 and T002 can run in parallel (CSS vs JS, different sections of different files)
- T004 can run in parallel with T001/T002 (Python view vs CSS/JS)
- T003 depends on T002 (listener uses the skeleton HTML string built in T002)

```text
T001 (CSS) ─────────────────────┐
T002 (skeleton HTML) → T003 (listener) → T005 (verify) → T006/T007
T004 (sort fix) ────────────────┘
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 3)

1. Complete T001 + T002 in parallel (CSS + skeleton HTML)
2. Complete T004 in parallel with above (sort fix — independent file)
3. Complete T003 (wire up the listener — depends on T002)
4. Verify T005 (seller click regression)
5. Run T006 + T007 (tests + manual check)

All changes ship together as a single commit since they're tightly related UX improvements.

---

## Notes

- No new files — all changes to existing files
- Total: 7 tasks across 3 files
- The skeleton HTML in T002 must match the contract in `contracts/lots-skeleton.md`
- T004 is a one-line fix but has high UX impact (stops disorienting list reorder)

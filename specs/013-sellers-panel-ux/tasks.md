# Tasks: Sellers Panel UX

**Input**: Design documents from `/specs/013-sellers-panel-ux/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/sellers-panel.md, quickstart.md

**Tests**: Included — contract tests specified in contracts/sellers-panel.md.

**Organization**: Tasks grouped by user story. Both stories are P1 but independent — US1 (filter) touches the seller template, US2 (skeleton) touches shell, CSS, and view.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: User Story 1 — Realtime Search Filtering (Priority: P1) 🎯 MVP

**Goal**: Seller search input filters the list in realtime with 300ms debounce — no Enter key or button click required.

**Independent Test**: Type a partial seller name into the search field and verify results filter down after a brief pause (~300ms). Clear the field to restore the full list.

### Implementation

- [x] T001 [US1] Move `hx-get` from the `<form>` to the `<input>`, add `hx-trigger="input changed delay:300ms, search"`, add `hx-target`, `hx-swap`, and `hx-indicator` attributes per contract, and remove `hx-get` from the parent form in `src/catalog/templates/catalog/partials/seller_list_panel.html`

**Checkpoint**: Typing into the seller search field should filter the list in realtime after a 300ms pause. Clearing the field restores the full list. No JavaScript changes needed.

---

## Phase 2: User Story 2 — Skeleton Loading on Seller Selection (Priority: P1)

**Goal**: Clicking a seller immediately clears the events panel and shows skeleton placeholders with a spinner until the server responds. Events are sorted most-recent-first.

**Independent Test**: Click any seller and observe that the events panel immediately shows skeleton placeholders (gray bars + spinner) before the real data arrives.

### Implementation

- [x] T002 [P] [US2] Add skeleton CSS classes (`.skeleton-loading`, `.skeleton-spinner`, `.skeleton-list`, `.skeleton-item`, `.skeleton-bar`, `.skeleton-title`, `.skeleton-meta`) and `@keyframes skeleton-pulse` animation in `src/catalog/static/catalog/styles.css`
- [x] T003 [P] [US2] Add skeleton HTML template string and `htmx:beforeRequest` event listener in `<script>` block that injects skeleton into `#panel-left2-content` and clears `#panel-main-content` when a seller item click triggers a request targeting `#panel-left2-content` in `src/catalog/templates/catalog/shell.html`
- [x] T004 [US2] Sort `result.items` by `start_date` descending (most recent first) in the `seller_events_panel` view before passing to the template in `src/catalog/views/panels.py`

**Checkpoint**: Clicking a seller shows skeleton placeholders immediately, server responds with events sorted by start date (most recent first), skeleton is replaced with real content. Clicking a second seller while first is loading cancels the previous request (existing `hx-sync` behavior) and shows fresh skeletons.

---

## Phase 3: Contract Tests

**Purpose**: Verify rendering contracts and behavior as defined in `contracts/sellers-panel.md`.

- [x] T005 Add contract tests in `tests/contract/test_panels.py`:
  1. Test that the seller filter input element has `hx-trigger` attribute containing `delay:300ms`
  2. Test that the parent `<form>` does NOT have an `hx-get` attribute
  3. Test that events returned by `seller_events_panel` are sorted by `start_date` descending
  4. Test that existing seller selection active/override states still work after template changes

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories.

- [x] T006 Run full test suite (`python -m pytest tests/ -v`) and fix any regressions
- [X] T007 Run quickstart.md manual validation checklist — verify realtime filter, skeleton loading, events sort, existing behavior preserved

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)**: No dependencies — can start immediately
- **Phase 2 (US2)**: No dependencies — can start immediately (independent of US1)
- **Phase 3 (Tests)**: Depends on Phase 1 and Phase 2 completion
- **Phase 4 (Polish)**: Depends on Phase 3 completion

### User Story Dependencies

- **US1 (Realtime Filter)**: Fully independent — touches only `seller_list_panel.html`
- **US2 (Skeleton Loading)**: Fully independent — touches `shell.html`, `styles.css`, `panels.py`
- **No cross-story dependencies**: US1 and US2 modify different files and can be implemented in parallel

### Within Each User Story

- US1: Single task (T001) — template attribute changes only
- US2: T002 and T003 can run in parallel (CSS and JS are in different files); T004 is independent (view file)

### Parallel Opportunities

```text
# US1 and US2 can proceed in parallel (no shared files):
  T001 (seller_list_panel.html)  ──┐
  T002 (styles.css)              ──┤── All parallel
  T003 (shell.html)              ──┤
  T004 (panels.py)               ──┘
                                    │
                                    ▼
  T005 (test_panels.py)         ── Sequential (needs all implementation done)
                                    │
                                    ▼
  T006 (test suite)             ── Sequential
  T007 (manual validation)      ── Sequential
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001 — realtime filter works
2. **STOP and VALIDATE**: Test filter independently
3. Demo/deploy if ready — immediate UX improvement

### Full Delivery

1. T001 + T002 + T003 + T004 in parallel → Both stories implemented
2. T005 → Contract tests pass
3. T006 + T007 → Full validation, no regressions

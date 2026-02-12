# Tasks: Pagination UX Improvements

**Input**: Design documents from `/specs/009-pagination-ux/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec. Omitted.

**Organization**: Tasks grouped by user story. Note: `panel_pagination.html` is modified by US1, US2, and US3 — each story adds its piece incrementally. US1 performs the initial template rewrite.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Enrich the pagination context dict in all three panel views with `start_item`, `end_item`, and `page_size` fields. All user stories depend on this data being available in the template context.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T001 Add `_enrich_pagination()` helper function to `src/catalog/views/panels.py` that computes `start_item`, `end_item`, and `page_size` for both API-backed `Paginated` objects and local pagination dicts (see research.md R3)
- [X] T002 Update `_paginate_locally()` in `src/catalog/views/panels.py` to include `start_item`, `end_item`, and `page_size` in the returned dict
- [X] T003 Update `sellers_panel()` in `src/catalog/views/panels.py` to enrich the API `Paginated` result via `_enrich_pagination()` and include `page_size` in `pagination_extra_params` when non-default
- [X] T004 Update `seller_events_panel()` in `src/catalog/views/panels.py` to enrich the API `Paginated` result via `_enrich_pagination()` and include `page_size` in extra params when non-default
- [X] T005 Update `event_lots_panel()` in `src/catalog/views/panels.py` to include `page_size` in extra params when non-default (local pagination already enriched via T002)

**Checkpoint**: All three panel views return enriched pagination context with `start_item`, `end_item`, `page_size`. Existing UI unchanged (template not yet updated).

---

## Phase 2: User Story 1 — Jump-to-Page Input (Priority: P1) 🎯 MVP

**Goal**: Operators can click the page number, type a target page, and press Enter to navigate directly — eliminating sequential prev/next clicking.

**Independent Test**: Load any panel with multi-page data, click the page display, type a page number, press Enter — panel navigates to that page.

### Implementation for User Story 1

- [X] T006 [US1] Rewrite `src/catalog/templates/catalog/partials/panel_pagination.html` with new HTML structure: prev/next links (preserved), page-jump `<span>` containing a `.page-display` span and a hidden `.page-input` `<input type="number">` with `data-base-url`, `data-target`, `data-indicator`, `data-extra-params` attributes (see contracts/panel-endpoints.md for rendered structure)
- [X] T007 [P] [US1] Add jump-to-page JavaScript in `src/catalog/templates/catalog/shell.html`: (1) click handler on `.page-display` to show `.page-input` and hide `.page-display`, (2) Enter key handler on `.page-input` to clamp value to [1, max] and call `htmx.ajax('GET', url, {target, swap})`, (3) Escape/blur handler to revert input back to static display without navigating
- [X] T008 [P] [US1] Add CSS styles for `.page-jump`, `.page-display`, `.page-input` in `src/catalog/static/catalog/styles.css` — `.page-display` as clickable with cursor:pointer, `.page-input` as compact number input (width ~3em, same font size as pagination), hidden by default

**Checkpoint**: Jump-to-page works on all three panels. Prev/next still works. Page info still shows basic "X / Y" format.

---

## Phase 3: User Story 2 — Page Size Selector (Priority: P2)

**Goal**: Operators can choose how many items per page (10, 25, 50, 100) via a dropdown in the pagination bar.

**Independent Test**: Select a different page size from the dropdown — panel reloads with the new item count at page 1, page size persists when navigating pages.

### Implementation for User Story 2

- [X] T009 [US2] Add `<select class="page-size-select">` element to `src/catalog/templates/catalog/partials/panel_pagination.html` with options 10, 25, 50, 100 — mark the current `paginated.page_size` as selected using template conditional, include `data-base-url`, `data-target`, `data-indicator`, `data-extra-params` attributes for JS handler
- [X] T010 [P] [US2] Add page size change JavaScript handler in `src/catalog/templates/catalog/shell.html`: on `change` event of `.page-size-select`, build URL with `page=1&page_size=<value>` plus extra params, call `htmx.ajax('GET', url, {target, swap})`
- [X] T011 [P] [US2] Add CSS styles for `.page-size-select` in `src/catalog/static/catalog/styles.css` — compact select matching pagination font size (0.75rem), no heavy border, fits within the pagination bar flex layout

**Checkpoint**: Page size selector works on all three panels. Changing page size resets to page 1. Page size persists across prev/next/jump navigation via extra_params.

---

## Phase 4: User Story 3 — Improved Page Info Display (Priority: P2)

**Goal**: Pagination bar shows item range and total count ("26–50 of 73") instead of just "X / Y".

**Independent Test**: Load a paginated panel — verify range display is accurate, navigate pages and confirm range updates correctly.

### Implementation for User Story 3

- [X] T012 [US3] Add `<span class="page-range">` element to `src/catalog/templates/catalog/partials/panel_pagination.html` displaying `{{ paginated.start_item }}–{{ paginated.end_item }} of {{ paginated.total_items }}` (data available from Phase 1 enrichment)
- [X] T013 [P] [US3] Add CSS styles for `.page-range` in `src/catalog/static/catalog/styles.css` — subtle secondary color (#64748b), same font size as pagination, positioned before the page-jump span in the flex layout

**Checkpoint**: All three panels show accurate item ranges. Range updates correctly when navigating pages or changing page size.

---

## Phase 5: User Story 4 — Scroll to Top on Page Change (Priority: P3)

**Goal**: Panels automatically scroll to the top of their content area after any pagination navigation.

**Independent Test**: Scroll to the bottom of a panel, click Next — panel scrolls back to top.

### Implementation for User Story 4

- [X] T014 [US4] Add scroll-to-top behavior in the `htmx:afterSwap` event listener in `src/catalog/templates/catalog/shell.html` — after content swap, find the closest `.panel` ancestor of `e.detail.target` and set `scrollTop = 0`

**Checkpoint**: Scroll resets on all pagination interactions (prev, next, jump-to-page, page size change) across all three panels.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify consistency across all panels and validate against spec.

- [X] T015 Verify cross-panel consistency: confirm pagination improvements (jump-to-page, page size, range display, scroll-to-top) work identically on sellers, events, and lots panels — fix any panel-specific issues
- [X] T016 Verify filter + pagination interaction: apply a filter on sellers or events panel, then use jump-to-page, change page size, navigate — confirm filters and selected state are preserved via extra_params
- [X] T017 Verify auto-save interaction on lots panel: edit a lot row, then paginate — confirm auto-save fires and unsaved changes are not lost
- [X] T018 Run quickstart.md validation: execute all 6 manual test scenarios from `specs/009-pagination-ux/quickstart.md` and confirm pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately. BLOCKS all user stories.
- **US1 (Phase 2)**: Depends on Phase 1. Rewrites `panel_pagination.html` — BLOCKS US2 and US3 (same file).
- **US2 (Phase 3)**: Depends on Phase 2 (adds to rewritten template).
- **US3 (Phase 4)**: Depends on Phase 2 (adds to rewritten template). Can run in parallel with US2 if changes don't conflict, but safer to run sequentially.
- **US4 (Phase 5)**: Depends on Phase 1 only (different file: `shell.html`). CAN run in parallel with US1/US2/US3.
- **Polish (Phase 6)**: Depends on all user stories being complete.

### Within Each User Story

- Template changes before JS handlers (JS references template elements)
- CSS can run in parallel with JS (different files, no dependency)

### Parallel Opportunities

Within Phase 1:
```
T001 → T002 (depends on helper)
T001 → T003, T004, T005 (all depend on helper, can run in parallel with each other)
```

Within Phase 2 (US1):
```
T006 (template) → then T007 (JS) and T008 (CSS) in parallel
```

Cross-story parallelism:
```
US4 (Phase 5, shell.html only) can run in parallel with US1/US2/US3
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational backend enrichment
2. Complete Phase 2: US1 — Jump-to-page input
3. **STOP and VALIDATE**: Test jump-to-page on all three panels
4. Deploy if ready — operators get the highest-value improvement immediately

### Incremental Delivery

1. Phase 1 → Backend ready
2. Phase 2 (US1) → Jump-to-page works → **MVP deployed**
3. Phase 3 (US2) → Page size selector added → Deploy
4. Phase 4 (US3) → Range display added → Deploy
5. Phase 5 (US4) → Scroll-to-top added → Deploy
6. Phase 6 → Polish and validation → Final deploy

---

## Notes

- `panel_pagination.html` is a single shared template included by all 3 panel templates — changes here automatically apply to sellers, events, and lots panels
- `_parse_page_params()` already handles `page_size` parsing and clamping — no changes needed there
- ABConnect API `Paginated` objects are read-only attrs; `_enrich_pagination()` wraps them in a dict for uniform template access
- JS handlers use event delegation (listening on `document`) since pagination content is dynamically swapped by HTMX
- Commit after each phase checkpoint for clean traceability

# Spec: Pagination UX Improvements

**Feature**: 009-pagination-ux | **Status**: Draft | **Date**: 2026-02-12

## Overview

Improve the pagination UX across all three SPA panels (sellers, events, lots) to give operators faster navigation and clearer context. Currently, pagination is prev/next only with no way to jump to a specific page, no page size control, and minimal item count information in panels.

## User Stories

### US1: Jump-to-Page Input (P1)
As an operator browsing a long seller or event list, I want to type a page number and jump directly to it so I can navigate large datasets without clicking "Next" repeatedly.

**Why this priority**: Sequential prev/next is the biggest friction point — operators managing hundreds of sellers or events must click dozens of times to reach later pages.

**Independent Test**: Can be tested by loading any panel with multi-page data, typing a page number, and verifying the panel updates to that page.

**Acceptance Scenarios:**
1. **Given** a panel with multiple pages, **When** the operator clicks the page number display, **Then** it becomes an editable input pre-filled with the current page number.
2. **Given** the page input is active, **When** the operator types a valid page number and presses Enter, **Then** the panel navigates to that page via HTMX.
3. **Given** the page input is active, **When** the operator types a number greater than total pages, **Then** the input is clamped to the last page.
4. **Given** the page input is active, **When** the operator presses Escape or clicks away without pressing Enter, **Then** the input reverts to the static page display without navigating.

---

### US2: Page Size Selector (P2)
As an operator, I want to choose how many items are displayed per page so I can see more items at once or reduce load times as needed.

**Why this priority**: Different operators have different workflow preferences — some want compact lists, others want to see as many lots as possible without paginating.

**Independent Test**: Can be tested by selecting a different page size from the dropdown and verifying the correct number of items loads.

**Acceptance Scenarios:**
1. **Given** a paginated panel, **When** the operator selects a different page size from the dropdown, **Then** the panel reloads with the new page size and resets to page 1.
2. **Given** the lots panel with page size 50, **When** the panel loads, **Then** 50 lots are displayed (or all remaining if fewer).
3. **Given** the operator changes page size, **When** they navigate to another page and back, **Then** the page size preference persists for that panel.

**Page size options**: 10, 25, 50, 100

---

### US3: Improved Page Info Display (P2)
As an operator, I want to see item counts and range in the pagination bar so I know exactly where I am in the dataset.

**Why this priority**: Operators need context about how much data they're working with, especially when filtering.

**Independent Test**: Can be tested by loading a paginated panel and verifying the info text shows the correct range and total.

**Acceptance Scenarios:**
1. **Given** page 2 of lots with 25 per page and 73 total, **When** the panel renders, **Then** the pagination shows "26–50 of 73".
2. **Given** page 1 with fewer items than page size, **When** the panel renders, **Then** it shows "1–N of N" (e.g., "1–12 of 12") and no pagination controls.

---

### US4: Scroll to Top on Page Change (P3)
As an operator, I want the panel to scroll to the top when I navigate to a new page so I always start reading from the first item.

**Why this priority**: Quality-of-life improvement — currently the scroll position may remain at the bottom after a page change, requiring manual scroll.

**Independent Test**: Can be tested by scrolling to the bottom of a panel, clicking Next, and verifying the scroll position resets.

**Acceptance Scenarios:**
1. **Given** a panel scrolled to the bottom, **When** the operator clicks Next/Prev or jumps to a page, **Then** the panel scrolls to the top of the content area.

---

### Edge Cases

- What happens when the operator types a non-numeric value in the page input? → Input rejects non-numeric characters.
- What happens when page size changes and current page exceeds new total pages? → Navigate to the last valid page.
- What happens on single-page results? → Pagination bar is hidden entirely (existing behavior preserved).
- What happens when a filter reduces results to fewer pages than the current page? → Already handled: views clamp to available data.

## Requirements

### Functional Requirements

- **FR-001**: Panel pagination MUST display a clickable page number that becomes an editable input on click.
- **FR-002**: Page input MUST navigate via HTMX on Enter key, clamp to valid range [1, total_pages].
- **FR-003**: Page input MUST revert on Escape or blur without Enter.
- **FR-004**: Panel pagination MUST include a page size `<select>` with options: 10, 25, 50, 100.
- **FR-005**: Changing page size MUST reload the panel at page 1 with the new page size.
- **FR-006**: Pagination info MUST show item range and total count: "X–Y of Z".
- **FR-007**: Panel content areas MUST scroll to top after any pagination navigation.
- **FR-008**: All pagination changes MUST work consistently across sellers, events, and lots panels.
- **FR-009**: Existing `extra_params` preservation MUST continue to work (selected state, filters).

### Key Entities

- **PaginationContext**: Existing paginated metadata dict extended with `start_item` and `end_item` for range display.

## Non-Functional Requirements

- No new dependencies — vanilla JS + CSS only
- Changes confined to: `panel_pagination.html`, `styles.css`, `shell.html` (JS), `panels.py`
- Must not break existing auto-save, lot detail modal, or override flows
- Page navigation must feel instant for API-backed panels (sellers, events)

## Out of Scope

- Infinite scroll / virtual scrolling
- Server-side page size persistence (session/DB)
- Changes to full-page pagination (`pagination.html`)
- Changes to search results pagination

## Success Criteria

- **SC-001**: Operator can reach any page in fewer than 3 interactions (type number + Enter)
- **SC-002**: Page size change works without full page reload (HTMX swap)
- **SC-003**: Item range display ("26–50 of 73") is accurate across all three panels

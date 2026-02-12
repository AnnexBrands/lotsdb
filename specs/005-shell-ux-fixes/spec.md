# Spec: Shell UX Fixes

**Branch**: `005-shell-ux-fixes` | **Date**: 2026-02-11
**Input**: PR #5 review (`specs/004-shell-interaction-polish/pr-5-review.md`) + user feedback

## Problem Statement

The SPA shell has several usability issues: internal IDs in URLs are meaningless to operators, the lots panel call is unreliable, empty states are confusing, panel headers lack filtering, and several bugs from the PR #5 review remain unresolved.

## User Stories

### US1 — Customer-Friendly URL Identifiers (Priority: P1)

**As an** operator sharing a shell URL, **I want** the URL to use customer-facing IDs (e.g., `?seller=4098&event=395768`) **so that** the link is recognizable and meaningful.

**Acceptance Scenarios**:
- AC-1: Clicking a seller pushes `/?seller=<customer_display_id>` (not internal ID)
- AC-2: Clicking an event pushes `/?seller=<customer_display_id>&event=<customer_catalog_id>`
- AC-3: Opening `/?seller=4098` hydrates correctly by looking up seller via customer_display_id
- AC-4: Opening `/?seller=4098&event=395768` hydrates both panels correctly
- AC-5: Invalid/non-existent customer IDs render default empty state without error

### US2 — Fix Lots Panel Data (Priority: P1)

**As an** operator viewing lots for an event, **I want** to see exactly the lots belonging to that event **so that** I can trust the data is correct.

**Acceptance Scenarios**:
- AC-6: Clicking an event shows only lots belonging to that specific catalog
- AC-7: Events with no lots show "No lots in this event" (not a spinner or wrong lots)
- AC-8: Lots call uses the expanded catalog response (embedded lots), not the unreliable Lots list endpoint with CustomerCatalogId filter

### US3 — Improved Empty States & Feedback (Priority: P2)

**As an** operator navigating the shell, **I want** clear feedback about what's happening **so that** I'm never confused about loading state or empty results.

**Acceptance Scenarios**:
- AC-9: When an event is selected, the events panel OOB clear of main says "Select an event to view lots" is replaced with contextual empty state
- AC-10: Empty lot results show "No lots in this event" (not the generic placeholder)
- AC-11: Loading indicators are wired with explicit `hx-indicator` attributes so spinners appear reliably

### US4 — Panel Header Filters (Priority: P2)

**As an** operator browsing sellers or events, **I want** filter inputs in the panel headers **so that** I can narrow results without leaving the SPA shell.

**Acceptance Scenarios**:
- AC-12: Sellers panel header has a text filter input for name search
- AC-13: Events panel header has a text filter input for title search
- AC-14: Typing in the filter and pressing Enter (or after debounce) reloads the panel with filtered results
- AC-15: When a seller is active/selected, the filter input value is empty with placeholder text "Selected: <seller name>"
- AC-16: When an event is active/selected, the filter input value is empty with placeholder text "Selected: <event title>"
- AC-17: Clearing the filter and submitting reloads full unfiltered list

### US5 — PR #5 Review Bug Fixes (Priority: P1)

**As a** developer, **I want** to resolve all P0/P1 issues from the PR #5 review **so that** the shell is production-grade.

**Acceptance Scenarios**:
- AC-18: Hydrated panel includes pass concrete `pagination_url` values (not empty string)
- AC-19: OOB events include in `lots_panel.html` passes concrete `pagination_url`
- AC-20: Shell view (`/`) uses defensive `_parse_page_params` instead of raw `int()` parsing
- AC-21: Hydration validates that event belongs to seller; mismatched event is ignored
- AC-22: Mobile resize-to-desktop resets `data-mobile-panel` to "sellers"
- AC-23: `hx-indicator` attributes on panel trigger elements point to their parent panel's indicator

## Functional Requirements

- FR-201: URLs use `customer_display_id` for sellers and `customer_catalog_id` for events
- FR-202: `HX-Push-Url` headers use customer-friendly IDs
- FR-203: Shell hydration looks up entities by customer-friendly IDs
- FR-204: Lots panel uses expanded catalog response (embedded lots) with local pagination
- FR-205: Events panel OOB clear shows event-appropriate empty state
- FR-206: Panel headers contain inline filter inputs with HTMX-driven filtering
- FR-207: Selected record sets filter input to empty with "Selected: <name>" placeholder
- FR-208: All hydrated/OOB panel includes pass valid `pagination_url` values
- FR-209: Shell view uses defensive page param parsing
- FR-210: Hydration validates event-belongs-to-seller relationship
- FR-211: Mobile resize resets panel state to sellers
- FR-212: Panel triggers use explicit `hx-indicator` attributes

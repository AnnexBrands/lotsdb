# Implementation Plan: Shell UX Fixes

**Branch**: `005-shell-ux-fixes` | **Date**: 2026-02-11 | **Spec**: `specs/005-shell-ux-fixes/spec.md`
**Input**: Feature specification from `/specs/005-shell-ux-fixes/spec.md`

## Summary

Fix shell usability issues: replace internal IDs with customer-friendly identifiers in URLs, fix unreliable lots data by switching to expanded catalog response, add filter inputs to panel headers, improve empty-state feedback, and resolve all P0/P1 bugs from PR #5 review.

## Technical Context

**Language/Version**: Python 3.14, Django 5
**Primary Dependencies**: HTMX 2.0.4 (CDN), ABConnectTools 0.2.1
**Storage**: SQLite3 (sessions only — no new storage)
**Testing**: pytest + pytest-django, Django RequestFactory
**Target Platform**: Linux server, modern browsers
**Project Type**: Web application (Django + HTMX server-rendered SPA)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Artifact Harmony | PASS | Spec, contracts, tests, code updated together |
| II. Executable Knowledge | PASS | Contract tests cover all behavioral changes |
| III. Contracted Boundaries | PASS | Endpoint contracts updated for new params/responses |
| IV. Versioned Traceability | PASS | All changes on feature branch with PR |
| V. Communicable Truth | PASS | Quickstart updated for new verification steps |

## Project Structure

### Documentation (this feature)

```text
specs/005-shell-ux-fixes/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── endpoints.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── catalog/
│   ├── services.py              # Modified: lots-by-catalog via expanded DTO, seller lookup by display ID
│   ├── views/
│   │   ├── panels.py            # Modified: customer-friendly IDs, filter params, lots fix, indicator wiring
│   │   └── sellers.py           # Modified: hydration by customer IDs, defensive parsing
│   ├── templates/catalog/
│   │   ├── shell.html           # Modified: hydration pagination_url, mobile reset, indicator attrs
│   │   └── partials/
│   │       ├── seller_list_panel.html  # Modified: filter input in header, hx-indicator
│   │       ├── events_panel.html       # Modified: filter input in header, OOB empty state, pagination_url fix
│   │       ├── lots_panel.html         # Modified: OOB pagination_url fix
│   │       └── panel_filter.html       # New: reusable inline filter partial
│   └── static/catalog/
│       └── styles.css           # Modified: panel filter styles
tests/
└── contract/
    └── test_panels.py           # Modified: updated for customer-friendly IDs, new filter tests
```

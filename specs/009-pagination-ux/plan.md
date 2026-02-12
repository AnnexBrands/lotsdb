# Implementation Plan: Pagination UX Improvements

**Branch**: `009-pagination-ux` | **Date**: 2026-02-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-pagination-ux/spec.md`

## Summary

Improve the pagination UX across the three SPA panels (sellers, events, lots) by adding a jump-to-page input, page size selector, item range display ("26–50 of 73"), and scroll-to-top on page change. All changes use HTMX + vanilla JS — no new dependencies.

## Technical Context

**Language/Version**: Python 3.14, Django 5
**Primary Dependencies**: HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install)
**Storage**: SQLite3 (sessions only — no new storage)
**Testing**: pytest
**Target Platform**: Linux server, modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (Django + HTMX SPA)
**Performance Goals**: Panel pagination navigation < 500ms perceived latency
**Constraints**: No new JS dependencies; lots panel limited by individual API calls per lot (25 calls/page)
**Scale/Scope**: 3 panel templates, 1 shared pagination partial, 1 CSS file, 1 shell JS block

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Artifact Harmony | PASS | Spec, plan, contracts, tests, and code will be updated together |
| II. Executable Knowledge | PASS | Acceptance scenarios map to testable behaviors; pytest covers views |
| III. Contracted Boundaries | PASS | No new API endpoints; existing panel endpoints gain `page_size` param |
| IV. Versioned Traceability | PASS | Feature branch with spec-first workflow |
| V. Communicable Truth | PASS | quickstart.md will document manual testing steps |
| Complexity | PASS | Minimal changes: 1 template, 1 CSS block, ~20 lines JS, minor view changes |

## Project Structure

### Documentation (this feature)

```text
specs/009-pagination-ux/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (pagination context shape)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (panel endpoint params)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── catalog/
│   ├── views/
│   │   └── panels.py              # Add start_item/end_item to paginated context; honor page_size param
│   ├── templates/catalog/
│   │   └── partials/
│   │       └── panel_pagination.html  # Rewrite: jump-to-page, page size select, range display
│   ├── static/catalog/
│   │   └── styles.css             # Updated .panel-pagination styles
│   └── templates/catalog/
│       └── shell.html             # JS: scroll-to-top on htmx:afterSwap, page input logic

tests/
├── test_panels.py                 # Existing — add page_size param tests, range context tests
```

**Structure Decision**: Existing Django project structure. No new files created — all changes are modifications to existing files. The `panel_pagination.html` partial is rewritten in-place; it is already included by all three panel templates.

## Complexity Tracking

No violations — all changes fit within existing architecture.

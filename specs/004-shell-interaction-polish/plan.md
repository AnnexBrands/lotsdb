# Implementation Plan: Shell Interaction Polish

**Branch**: `004-shell-interaction-polish` | **Date**: 2026-02-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-shell-interaction-polish/spec.md`

## Summary

Close four interaction gaps identified in PR #4 review: (1) wire selection-state highlighting so `.active` class is applied to the selected seller/event rows, (2) unify HTMX loading indicators across all three panels, (3) synchronize browser URL with current selection so links are shareable and back/forward work, (4) add a responsive stacked layout for viewports under 768px. No new dependencies, no new persistence, no new API endpoints — changes are confined to existing views, templates, CSS, and a small amount of inline HTMX/JS for URL management.

## Technical Context

**Language/Version**: Python 3.14, Django 5
**Primary Dependencies**: Django 5, HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install)
**Storage**: SQLite3 (sessions only — no new storage)
**Testing**: pytest + pytest-django, Django TestCase + RequestFactory
**Target Platform**: Linux server, modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (server-rendered with HTMX progressive enhancement)
**Performance Goals**: Panel transitions < 500ms; no perceptible jank on selection/pagination
**Constraints**: No JS framework; HTMX + vanilla JS only; no new dependencies
**Scale/Scope**: Internal tool, < 50 concurrent users; 3 modified views, ~6 modified templates, 1 CSS file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Artifact Harmony** | PASS | Spec, contracts, tests, docs, and code will ship together in one changeset |
| **II. Executable Knowledge** | PASS | Contract tests will assert `.active` class presence, indicator markup, URL hydration behavior, and pagination validation |
| **III. Contracted Boundaries** | PASS | Modified endpoints will have updated contract definitions in `contracts/` |
| **IV. Versioned Traceability** | PASS | All changes on dedicated feature branch with traceable commits |
| **V. Communicable Truth** | PASS | quickstart.md will document testing and verification steps |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/004-shell-interaction-polish/
├── plan.md              # This file
├── research.md          # Phase 0: HTMX patterns for selection, URL sync, responsive
├── data-model.md        # Phase 1: No new entities; documents view context changes
├── quickstart.md        # Phase 1: Manual and automated test instructions
├── contracts/           # Phase 1: Updated endpoint contracts
│   └── endpoints.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── config/
│   └── settings.py
└── catalog/
    ├── views/
    │   ├── panels.py          # Modified: selection state, pagination validation
    │   └── sellers.py         # Modified: URL param hydration on shell load
    ├── templates/catalog/
    │   ├── shell.html          # Modified: loading indicator for Left1, URL sync JS, responsive meta
    │   ├── base.html           # Possibly modified: viewport meta if missing
    │   └── partials/
    │       ├── seller_list_panel.html   # Modified: active class wiring
    │       ├── events_panel.html        # Modified: active class wiring
    │       ├── lots_panel.html          # Unchanged
    │       ├── panel_pagination.html    # Modified: carry selection params
    │       └── panel_error.html         # Unchanged
    └── static/catalog/
        └── styles.css          # Modified: responsive breakpoint, mobile panel styles

tests/
├── contract/
│   └── test_panels.py          # Modified: selection state, indicator, pagination validation tests
├── integration/                # Possibly new tests for URL hydration
└── unit/                       # Possibly new tests for pagination param validation
```

**Structure Decision**: Existing single-project Django structure. No new directories needed — all changes modify existing files in `src/catalog/` and `tests/`.

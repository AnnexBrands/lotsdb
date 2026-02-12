# Implementation Plan: Lot Detail Modal in SPA

**Branch**: `007-lot-detail-modal` | **Date**: 2026-02-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-lot-detail-modal/spec.md`

## Summary

Convert the full-page lot detail and override form into a modal overlay within the SPA shell. The modal is triggered from the lots table, loads content via HTMX into a native `<dialog>` element, supports viewing lot details and editing overrides, and updates the table row in place after save via out-of-band swap. No new data entities or external dependencies — this is purely a UI restructuring using existing HTMX + Django patterns.

## Technical Context

**Language/Version**: Python 3.14, Django 5
**Primary Dependencies**: HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install)
**Storage**: SQLite3 (sessions only — no new storage)
**Testing**: pytest
**Target Platform**: Web (desktop + mobile responsive)
**Project Type**: Web application (Django monolith with HTMX frontend)
**Performance Goals**: Modal content loads within acceptable time (1 API call to `services.get_lot()`)
**Constraints**: No JS frameworks, no external modal libraries, vanilla JS + HTMX + CSS only
**Scale/Scope**: 2 new templates, 1 new view function, ~5 modified files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Artifact Harmony | PASS | Spec, plan, contracts, data-model, quickstart, and tests all created together |
| II. Executable Knowledge | PASS | Contract tests will cover modal endpoints; manual test steps in quickstart |
| III. Contracted Boundaries | PASS | API contracts defined in `contracts/lot-detail-modal.md` before implementation |
| IV. Versioned Traceability | PASS | All changes in feature branch `007-lot-detail-modal` |
| V. Communicable Truth | PASS | quickstart.md documents how to use and test the feature |

**Post-Phase 1 Re-check**: All principles satisfied. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/007-lot-detail-modal/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: technical decisions
├── data-model.md        # Phase 1: data structures (existing entities reused)
├── quickstart.md        # Phase 1: manual test guide
├── contracts/           # Phase 1: API contracts
│   └── lot-detail-modal.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/catalog/
├── views/
│   └── panels.py              # Add lot_detail_panel() view
├── templates/catalog/
│   ├── shell.html             # Add <dialog> modal container + JS
│   └── partials/
│       ├── lot_detail_modal.html    # New: lot detail fragment
│       ├── lot_edit_modal.html      # New: override edit form fragment
│       └── lots_table_row.html      # Modify: add click handler + row ID
├── static/catalog/
│   └── styles.css             # Add modal CSS
└── urls.py                    # Add lot_detail_panel URL

tests/
└── contract/
    └── test_panels.py         # Add modal endpoint tests
```

**Structure Decision**: Follows existing Django project layout. New view added to `panels.py` (where all HTMX panel endpoints live). New templates in `partials/` (where all fragment templates live). No new directories needed.

## Complexity Tracking

No complexity violations. The implementation:
- Adds no new dependencies
- Adds no new data models
- Follows existing HTMX fragment-loading patterns
- Uses the native `<dialog>` element (no custom modal framework)
- Reuses existing `services.get_lot()` and override save logic

# Implementation Plan: Lots Table UX Polish

**Branch**: `008-lots-table-ux-polish` | **Date**: 2026-02-11 | **Spec**: `specs/008-lots-table-ux-polish/spec.md`
**Input**: Feature specification from `/specs/008-lots-table-ux-polish/spec.md`

## Summary

Refine the lots table to feel like a spreadsheet: remove input borders (border on `<td>` only), replace description with textarea, show notes as read-only with "more" link, convert cpack to a `<select>`, redesign save button with dirty/clean state colors and debounced auto-save on row blur, add CSS-only photo hover preview, and remove unwanted yellow highlight on click.

## Technical Context

**Language/Version**: Python 3.14, Django 5 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install)
**Primary Dependencies**: Django templates, HTMX, vanilla JS, CSS
**Storage**: SQLite3 (sessions only — no new storage)
**Testing**: Not explicitly requested in spec. Manual test steps in quickstart.md.
**Target Platform**: Modern browsers (desktop-first SPA shell)
**Project Type**: Web application (Django + HTMX)
**Performance Goals**: N/A — purely visual/UX changes
**Constraints**: No new dependencies, no new endpoints, no changes to OverrideForm
**Scale/Scope**: 3 files modified (template, CSS, shell JS)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Artifact Harmony | PASS | Spec, plan, research, data-model, contracts, quickstart all created together |
| II. Executable Knowledge | PASS (waived) | No automated tests requested; manual test steps in quickstart.md |
| III. Contracted Boundaries | PASS | No new endpoints; contracts doc confirms no API changes |
| IV. Versioned Traceability | PASS | Feature branch with full spec artifacts |
| V. Communicable Truth | PASS | Quickstart.md documents all manual test scenarios |

## Project Structure

### Documentation (this feature)

```text
specs/008-lots-table-ux-polish/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── no-new-endpoints.md
```

### Source Code (files modified)

```text
src/
├── catalog/
│   ├── static/catalog/styles.css          # Input borders, save states, photo preview, notes
│   ├── templates/catalog/
│   │   ├── partials/lots_table_row.html   # Textarea, select, notes display, save button
│   │   └── shell.html                     # JS: dirty tracking, debounce, save states
│   └── views/panels.py                    # Minor: notes field handling adjustment
```

**Structure Decision**: No new files. All changes modify existing files in the established structure.

## Complexity Tracking

No constitution violations. No complexity justification needed.

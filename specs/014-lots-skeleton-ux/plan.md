# Implementation Plan: Lots Panel Skeleton Loading

**Branch**: `014-lots-skeleton-ux` | **Date**: 2026-02-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/014-lots-skeleton-ux/spec.md`

## Summary

When a user clicks an event, the lots panel immediately shows skeleton placeholder rows that match the real table structure (thumbnail, description/notes, dimensions, cpack/crate/dnt, action). This replaces the current behavior of showing stale content with a generic spinner overlay. Implementation is purely client-side: a JS-generated skeleton HTML string injected on `htmx:beforeRequest`, plus CSS for the new skeleton table styles.

## Technical Context

**Language/Version**: Python 3.14, Django 5 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install)
**Primary Dependencies**: No new dependencies — uses existing skeleton CSS classes and JS event listeners
**Storage**: N/A — no backend changes
**Testing**: pytest (contract tests for HTML structure)
**Target Platform**: Web browser (Chrome/Firefox/Safari)
**Project Type**: Web application (Django + HTMX)
**Performance Goals**: Skeleton visible within 100ms of click (synchronous DOM swap)
**Constraints**: Must not affect existing seller-click behavior; must reuse existing skeleton CSS animation
**Scale/Scope**: 3 files changed (styles.css, shell.html, views/panels.py), ~35 lines added

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Artifact Harmony | PASS | Spec, plan, contracts, tests, code all updated together |
| II. Executable Knowledge | PASS | Contract tests will verify skeleton HTML structure |
| III. Contracted Boundaries | PASS | Skeleton HTML contract defined in contracts/ |
| IV. Versioned Traceability | PASS | Single feature branch with clear commit history |
| V. Communicable Truth | PASS | Quickstart documents manual verification steps |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/014-lots-skeleton-ux/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (minimal — no data changes)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── lots-skeleton.md # Expected skeleton HTML structure
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── catalog/
│   ├── static/catalog/styles.css      # Skeleton table row CSS
│   ├── templates/catalog/shell.html   # JS: skeleton HTML + event listener
│   └── views/panels.py               # Sort OOB events (FR-008)
tests/
└── contract/
    └── test_panels.py                 # Verify no regression on existing behavior
```

**Structure Decision**: No new files created. Changes are limited to existing CSS (skeleton row styles), existing JS (skeleton HTML string + beforeRequest listener for event clicks), and a one-line sort fix in the Python view.

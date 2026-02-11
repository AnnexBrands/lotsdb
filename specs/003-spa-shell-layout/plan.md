# Implementation Plan: SPA Shell Layout

**Branch**: `003-spa-shell-layout` | **Date**: 2026-02-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-spa-shell-layout/spec.md`

## Summary

Convert the current full-page-reload Seller/Events navigation into a three-panel SPA shell layout (Left1=Sellers, Left2=Events, Main=Lots) using HTMX 2.0.4 for fragment-based panel swaps. The layout uses CSS Grid with independently scrollable panels. Clicking a seller loads events via HTMX; clicking an event loads lots. All existing full-page views (lot detail, override, search, import) are preserved. The visual design is refined to production quality with branded header, professional empty states, and consistent styling.

## Technical Context

**Language/Version**: Python 3.14, Django 5
**Primary Dependencies**: Django 5, HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install)
**Storage**: SQLite3 (sessions only); no new storage — all data from ABConnect API
**Testing**: pytest, Django TestCase + RequestFactory
**Target Platform**: Linux server, modern desktop browsers (Chrome, Firefox, Edge, Safari)
**Project Type**: Web application (Django monolith, server-rendered with HTMX)
**Performance Goals**: Panel transitions < 500ms for typical datasets (< 100 items)
**Constraints**: No JavaScript frameworks. No build tooling. CDN-only frontend dependencies.
**Scale/Scope**: Internal operators (10–50 users), eventually external customers. ~3 new endpoints, ~5 new/modified templates, ~1 new view module.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Artifact Harmony | PASS | Spec, plan, contracts, data-model, quickstart, and tests will ship together in this branch. |
| II. Executable Knowledge | PASS | Contract tests will verify panel endpoints return correct HTML fragments. Quickstart documents manual verification steps. |
| III. Contracted Boundaries | PASS | `contracts/endpoints.md` defines all new endpoints with request/response shapes before implementation. |
| IV. Versioned Traceability | PASS | All artifacts in `specs/003-spa-shell-layout/`. Changes traceable via git. |
| V. Communicable Truth | PASS | `quickstart.md` documents how to run, verify, and test. |
| Governance: Complexity justified | PASS | No new dependencies. No new data models. Presentation-layer change only. |

### Post-Design Re-Check

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Artifact Harmony | PASS | spec.md FRs map 1:1 to contracts. Data model documents existing entities as displayed. |
| II. Executable Knowledge | PASS | Contract tests cover: fragment responses, DOM structure, pagination, OOB swaps, empty states, error states. |
| III. Contracted Boundaries | PASS | 3 new endpoints fully contracted in `contracts/endpoints.md`. Existing endpoints documented as unchanged. |
| IV. Versioned Traceability | PASS | Feature branch isolates all changes. |
| V. Communicable Truth | PASS | Quickstart includes curl commands for fragment endpoints, manual UI verification, and test commands. |

No gate violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/003-spa-shell-layout/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: HTMX patterns, CSS layout, Django partials research
├── data-model.md        # Phase 1: Existing entities as displayed in panels
├── quickstart.md        # Phase 1: Setup, run, verify, test instructions
├── contracts/
│   └── endpoints.md     # Phase 1: 3 new panel endpoints + modified home
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/catalog/
├── views/
│   ├── panels.py                         # NEW: Panel fragment views (3 views)
│   ├── sellers.py                        # MODIFIED: Home view returns shell.html
│   └── (auth|events|lots|imports|search).py  # UNCHANGED
├── templates/catalog/
│   ├── base.html                         # MODIFIED: Logo in navbar, design refinements
│   ├── shell.html                        # NEW: Three-panel SPA layout (extends base.html)
│   └── partials/
│       ├── seller_list_panel.html        # NEW: Left1 sellers fragment
│       ├── events_panel.html             # NEW: Left2 events fragment
│       ├── lots_panel.html               # NEW: Main lots card layout
│       ├── panel_pagination.html         # NEW: Reusable HTMX pagination
│       ├── panel_error.html              # NEW: Error state with retry
│       ├── filters.html                  # UNCHANGED
│       └── pagination.html               # UNCHANGED
├── static/catalog/
│   ├── styles.css                        # MODIFIED: Shell layout + design refinements
│   └── lotsdb_logo.svg                   # EXISTING: Brand logo (now displayed)
├── urls.py                               # MODIFIED: 3 new panel routes
└── services.py                           # UNCHANGED

tests/
└── contract/
    └── test_panels.py                    # NEW: Contract tests for panel endpoints
```

**Structure Decision**: Follows the existing Django app structure. New panel views go in a dedicated `views/panels.py` module to keep separation clean. New templates use the existing `partials/` convention. No new directories beyond what already exists.

## Key Design Decisions

### 1. HTMX Pattern: `hx-target` + `hx-swap-oob`

Clicking a seller sets `hx-target="#panel-left2"` to swap events into the middle panel. The server response includes an OOB fragment `<div id="panel-main-content" hx-swap-oob="innerHTML">` to clear the lots panel simultaneously. Single request, multiple panel updates.

### 2. Request Cancellation: `hx-sync="this:replace"`

Applied on panel containers via HTMX attribute inheritance. Rapid clicks cancel in-flight requests — always shows the latest selection.

### 3. CSS Layout: Grid Shell

```css
.shell {
  display: grid;
  grid-template-columns: 250px 300px 1fr;
  grid-template-rows: auto 1fr;
  height: 100vh;
}
.panel { overflow-y: auto; min-height: 0; }
```

Navbar spans all columns. Each panel scrolls independently. `min-height: 0` is critical for overflow in grid children.

### 4. Django Partials: Separate Endpoints

Fragment views live at `/panels/sellers/`, `/panels/sellers/<id>/events/`, `/panels/events/<id>/lots/`. No `HX-Request` header sniffing. Each URL returns exactly one thing. `{% include %}` shares templates between shell.html and fragment views.

### 5. Visual Design: Evolve Existing CSS

Refine the current system font stack, blue/slate palette, and card-based components. Add: branded header with SVG logo, panel headers with counts, selection highlight states, loading indicators, professional empty states with icons, smooth hover transitions. No CSS frameworks.

## Complexity Tracking

No violations to justify. This feature:
- Adds no new dependencies
- Adds no new data models
- Introduces no new architectural patterns (HTMX is already loaded, Django partials are a standard pattern)
- Keeps all existing pages functional

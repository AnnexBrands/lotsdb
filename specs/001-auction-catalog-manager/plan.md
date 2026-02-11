# Implementation Plan: Auction Catalog Manager

**Branch**: `001-auction-catalog-manager` | **Date**: 2026-02-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-auction-catalog-manager/spec.md`

## Summary

Build a web application for internal catalog managers to browse auction hierarchies (Sellers → Events → Lots), review lot details, and set value overrides. The application uses Django 5 with Django templates and HTMX, proxying all data operations through the existing ABConnectTools Python wrapper to the Catalog API. No local database for catalog data — SQLite used only for Django session storage.

## Technical Context

**Language/Version**: Python 3.14, Django 5
**Primary Dependencies**: Django 5, HTMX (CDN), ABConnectTools 0.2.1 (editable install)
**Storage**: SQLite (sessions only) — all catalog data via remote Catalog API
**Testing**: pytest, pytest-django
**Target Platform**: Linux server, accessed via web browser
**Project Type**: Web application (server-rendered)
**Performance Goals**: All page loads under 3 seconds (SC-004), constrained by upstream API latency
**Constraints**: Single concurrent API session per user; dependent on Catalog API availability
**Scale/Scope**: Internal tool for catalog management staff; low concurrency (< 20 concurrent users)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Artifact Harmony | PASS | Plan produces spec, contracts, data model, quickstart, and test structure together |
| II. Executable Knowledge | PASS | Quickstart is runnable; tests planned for contract, integration, and unit levels |
| III. Contracted Boundaries | PASS | URL contracts defined in contracts/api.yaml; data model defined in data-model.md |
| IV. Versioned Traceability | PASS | Feature branch with all artifacts versioned in git |
| V. Communicable Truth | PASS | Quickstart explains setup, run, and test; data model documents all entities |

### Post-Design Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Artifact Harmony | PASS | All artifacts produced together: spec, plan, research, data model, contracts, quickstart |
| II. Executable Knowledge | PASS | Contract tests verify route responses; integration tests verify workflows |
| III. Contracted Boundaries | PASS | URL contract defines all routes, parameters, and form schemas |
| IV. Versioned Traceability | PASS | All on feature branch 001-auction-catalog-manager |
| V. Communicable Truth | PASS | Quickstart covers prerequisites, setup, config, run, test, and project structure |

## Project Structure

### Documentation (this feature)

```text
specs/001-auction-catalog-manager/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity definitions
├── quickstart.md        # Phase 1: setup and run guide
├── contracts/
│   └── api.yaml         # Phase 1: URL route contracts
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── manage.py               # Django management script
├── config/
│   ├── __init__.py
│   ├── settings.py         # Django settings (sessions, templates, HTMX)
│   ├── urls.py             # Root URL configuration
│   └── wsgi.py             # WSGI entry point
└── catalog/
    ├── __init__.py
    ├── views/
    │   ├── __init__.py
    │   ├── sellers.py      # Seller list (home) and detail views
    │   ├── events.py       # Event detail view with lot list
    │   ├── lots.py         # Lot detail and override views
    │   ├── search.py       # Lot search view
    │   └── auth.py         # Login/logout views
    ├── forms.py            # Django forms for override editing
    ├── services.py         # Thin wrapper around ABConnectTools CatalogAPI
    ├── middleware.py        # Auth-required middleware
    ├── urls.py             # App URL patterns
    ├── templatetags/
    │   ├── __init__.py
    │   └── catalog_tags.py # Custom template filters (override diff highlighting)
    ├── templates/
    │   └── catalog/
    │       ├── base.html       # Layout: nav, breadcrumbs, HTMX script
    │       ├── sellers/
    │       │   ├── list.html   # Seller list (home page)
    │       │   └── detail.html # Seller detail with events
    │       ├── events/
    │       │   └── detail.html # Event detail with lots
    │       ├── lots/
    │       │   ├── detail.html # Lot detail with overrides and images
    │       │   └── override.html # Override edit form
    │       ├── search/
    │       │   └── results.html # Search results
    │       ├── auth/
    │       │   └── login.html  # Login form
    │       └── partials/
    │           ├── pagination.html  # Reusable pagination component
    │           └── filters.html     # Reusable filter component
    └── static/
        └── catalog/
            └── styles.css  # Minimal custom styles

tests/
├── conftest.py             # Fixtures: mock CatalogAPI, Django test client
├── contract/
│   └── test_routes.py      # Route status codes, redirects, content types
├── integration/
│   └── test_workflows.py   # Full browse → override → verify flows
└── unit/
    └── test_services.py    # Service layer with mocked API
```

**Structure Decision**: Single Django project with one app (`catalog`). No frontend build pipeline — templates are server-rendered, HTMX loaded from CDN. ABConnectTools consumed from the existing editable install at `/usr/src/pkgs/ABConnectTools`. SQLite used only for Django sessions.

## Complexity Tracking

No constitution violations to justify. The design is minimal:
- Single Django project, single app
- No local database for catalog data (SQLite for sessions only)
- No JavaScript build pipeline
- No abstraction layers beyond the existing ABConnectTools wrapper

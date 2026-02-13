# Implementation Plan: Performance UX — Loading Feedback & Optimization

**Branch**: `010-performance-ux` | **Date**: 2026-02-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-performance-ux/spec.md`

## Summary

Fix the broken HTMX loading indicators, add concurrent lot fetching via ThreadPoolExecutor (reducing load time from ~13s to ~2s), and add Django LocMemCache for lot and catalog data (making repeat visits and page changes near-instant). No new dependencies — uses only stdlib threading and Django's built-in cache framework.

## Technical Context

**Language/Version**: Python 3.14, Django 5
**Primary Dependencies**: HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install)
**Storage**: SQLite3 (sessions only); Django LocMemCache for API response caching (new)
**Testing**: pytest
**Target Platform**: Linux server, modern browsers
**Project Type**: Web application (Django + HTMX SPA)
**Performance Goals**: Event selection < 3s (first load), < 500ms (cached); loading spinner visible within 100ms of click
**Constraints**: No new package dependencies; ABConnectTools is not thread-safe for shared instances (per-thread instances required); no batch lot API available
**Scale/Scope**: 3 template files, 1 service file, 1 settings file, 1 CSS file (modifications only)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Artifact Harmony | PASS | Spec, plan, research, quickstart, tests, and code updated together |
| II. Executable Knowledge | PASS | Acceptance scenarios map to testable behaviors; pytest covers services and views |
| III. Contracted Boundaries | PASS | No new API endpoints; existing endpoints unchanged; caching is transparent |
| IV. Versioned Traceability | PASS | Feature branch with spec-first workflow |
| V. Communicable Truth | PASS | quickstart.md documents testing steps |
| Complexity | PASS | Uses stdlib `concurrent.futures` and Django built-in cache — minimal new complexity |

### Post-Design Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Artifact Harmony | PASS | No contracts needed (no new endpoints); data-model.md skipped (no new entities) |
| II. Executable Knowledge | PASS | Tests cover concurrent fetching, caching, cache invalidation |
| III. Contracted Boundaries | PASS | Cache is an implementation detail; external API contract unchanged |
| IV. Versioned Traceability | PASS | All changes on feature branch |
| V. Communicable Truth | PASS | quickstart.md covers manual verification |

## Project Structure

### Documentation (this feature)

```text
specs/010-performance-ux/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: indicator bug, threading, caching, API analysis
└── quickstart.md        # Manual testing guide
```

No `data-model.md` (no new data entities), no `contracts/` (no new API endpoints).

### Source Code (repository root)

```text
src/
├── catalog/
│   ├── services.py                        # Concurrent fetching, cache integration
│   ├── views/
│   │   └── panels.py                      # No changes needed (services handle optimization)
│   ├── templates/catalog/
│   │   └── partials/
│   │       ├── events_panel.html          # Fix hx-indicator target
│   │       ├── seller_list_panel.html     # Fix hx-indicator target
│   │       ├── lots_panel.html            # Fix hx-indicator target (pagination)
│   │       └── panel_pagination.html      # Fix hx-indicator target
│   └── static/catalog/
│       └── styles.css                     # No changes needed (CSS is correct, indicator targeting was wrong)
└── config/
    └── settings.py                        # Add CACHES config and LOT_FETCH_MAX_WORKERS

tests/
├── test_services.py                       # New: concurrent fetching, caching, invalidation
```

**Structure Decision**: Existing Django project structure. All changes are modifications to existing files except `test_services.py` (new test file for service-layer tests). The optimization is entirely in the service layer — views and templates need only indicator fixes.

## Implementation Approach

### Layer 1: Fix Loading Indicators (templates only)

**Problem**: `hx-indicator="#panel-main .htmx-indicator"` targets the indicator div itself. HTMX adds `htmx-request` to that element. But CSS uses descendant selector `.htmx-request .htmx-indicator` which requires `htmx-request` on a parent.

**Fix**: Change all `hx-indicator` attributes to target the **panel** div instead of the indicator child:
- `hx-indicator="#panel-main .htmx-indicator"` → `hx-indicator="#panel-main"`
- `hx-indicator="#panel-left1 .htmx-indicator"` → `hx-indicator="#panel-left1"`
- `hx-indicator="#panel-left2 .htmx-indicator"` → `hx-indicator="#panel-left2"`

This way `htmx-request` is added to the panel, and both `.htmx-request .htmx-indicator` and `.htmx-request .panel-content` CSS rules activate correctly.

**Files**: `events_panel.html`, `seller_list_panel.html`, `lots_panel.html`, `panel_pagination.html`

### Layer 2: Concurrent Lot Fetching (services.py)

**Approach**: Replace sequential loop in `get_lots_for_event()` with `ThreadPoolExecutor`:
- Create a new `get_catalog_api(request)` instance per thread (thread-safe: each gets own `SessionTokenStorage`)
- `max_workers` configurable via `settings.LOT_FETCH_MAX_WORKERS` (default 10)
- Preserve lot ordering (use indexed results array)
- Log and skip individual failures (graceful degradation)

**Optimization**: Check cache first for each lot; only fetch uncached lots concurrently.

### Layer 3: Caching (services.py + settings.py)

**Approach**: Django `LocMemCache` with 10-minute TTL:
- `get_lot()` → cache on `lot:{lot_id}`, return cached if present
- `get_catalog()` → cache on `catalog:{catalog_id}`, return cached if present
- `save_lot_override()` → invalidate `lot:{lot_id}` after successful save
- `get_lots_for_event()` → partition lot_ids into cached/uncached, only fetch uncached concurrently

**Cache keys**: `lot:{id}`, `catalog:{id}`
**TTL**: 600 seconds (10 minutes), configurable via `CACHES["default"]["TIMEOUT"]`

## Complexity Tracking

No violations — all changes use stdlib and Django built-ins within the existing architecture.

# Implementation Plan: Cache Polish

**Branch**: `016-cache-polish` | **Date**: 2026-02-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/016-cache-polish/spec.md`

## Summary

Fix correctness bugs in the Redis caching layer (start_date type fidelity, pagination contract), add environment-driven Redis config, fix a misleading test assertion, increase skeleton row count, and implement stale-while-revalidate for the events panel (show cached events instantly on seller click, background-refresh from server).

## Technical Context

**Language/Version**: Python 3.14, Django 5
**Primary Dependencies**: HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install), redis>=5.0
**Storage**: SQLite3 (sessions + Django User table), Redis (cache)
**Testing**: pytest (from `src/` directory: `cd src && python -m pytest ../tests/ -v`)
**Target Platform**: Linux server (WSL2 dev, production on iq)
**Project Type**: Web application (Django + HTMX SPA shell)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| I. Artifact Harmony | PASS | Spec, contracts, tests, code all updated together |
| II. Executable Knowledge | PASS | Contract tests cover all acceptance scenarios |
| III. Contracted Boundaries | PASS | View contract and cache service contract defined |
| IV. Versioned Traceability | PASS | Single branch, single commit |
| V. Communicable Truth | PASS | quickstart.md provides manual verification steps |

## Project Structure

### Documentation (this feature)

```text
specs/016-cache-polish/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cache-service.md
│   └── events-panel-view.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (files modified)

```text
src/
├── catalog/
│   ├── services.py            # Fix start_date, fix pagination, add list_catalogs_fresh()
│   ├── cache.py               # No changes (safe wrappers preserved)
│   ├── views/
│   │   └── panels.py          # SWR logic in seller_events_panel
│   ├── templates/catalog/
│   │   ├── partials/
│   │   │   └── events_panel.html  # Auto-refresh trigger div
│   │   └── shell.html         # Skeleton count, SWR JS guards
│   └── static/catalog/
│       └── styles.css         # (no changes expected)
├── config/
│   └── settings.py            # Env-driven REDIS_URL

tests/
├── unit/
│   └── test_cache.py          # Fix assertion bug
└── contract/
    └── test_panels.py         # New SWR contract tests, updated cache tests
```

**Structure Decision**: No new files. All changes modify existing files from the 015-redis-caching feature.

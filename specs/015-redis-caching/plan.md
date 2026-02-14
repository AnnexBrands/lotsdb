# Implementation Plan: Redis Caching for Sellers and Catalogs

**Branch**: `015-redis-caching` | **Date**: 2026-02-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-redis-caching/spec.md`

## Summary

Add Redis caching to the catalog application to eliminate repetitive ABConnect API calls for sellers and future catalogs. Cache lightweight projected dicts (3 fields for sellers, 4 for events) instead of full Pydantic DTOs. Use Django's built-in Redis cache backend on localhost:6379 with `cat_` key prefix. Gracefully fall back to direct API calls when Redis is unavailable.

## Technical Context

**Language/Version**: Python 3.14, Django 5
**Primary Dependencies**: ABConnectTools 0.2.1 (existing), `redis>=5.0` (new)
**Storage**: Redis on localhost:6379 (cache only), SQLite3 (sessions — unchanged)
**Testing**: pytest, pytest-django
**Target Platform**: Linux server
**Project Type**: Web application (Django + HTMX)
**Performance Goals**: 3x+ faster repeated panel loads from warm cache
**Constraints**: `cat_` key prefix, no auth/TLS, graceful fallback on Redis down
**Scale/Scope**: Hundreds of sellers, tens of catalogs per seller — all fit in single cache entries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Artifact Harmony | PASS | Spec, plan, contracts, data-model, quickstart, tasks all created together |
| II. Executable Knowledge | PASS | Contract tests defined for all cache behaviors (TC-001 through TC-008) |
| III. Contracted Boundaries | PASS | Cache service contract defines function signatures, data shapes, and behavior |
| IV. Versioned Traceability | PASS | All changes on feature branch, linked to spec |
| V. Communicable Truth | PASS | quickstart.md provides manual verification steps |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/015-redis-caching/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cache-service.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── config/
│   └── settings.py          # Add CACHES configuration
├── catalog/
│   ├── services.py           # Add caching logic to list_sellers, list_catalogs
│   └── cache.py              # NEW: safe_cache_get, safe_cache_set helpers

tests/
├── contract/
│   └── test_panels.py        # Existing tests (update mocks if needed)
├── unit/
│   └── test_cache.py         # NEW: cache helper unit tests
└── integration/
    └── test_cache_service.py # NEW: service-level cache integration tests

pyproject.toml                # Add redis dependency
```

**Structure Decision**: Minimal additions — one new module (`cache.py`) for helpers, caching logic added directly to existing `services.py`. Test files split by level: unit tests for helpers, integration tests for cached service functions.

# Research: Auction Catalog Manager

**Branch**: `001-auction-catalog-manager` | **Date**: 2026-02-10

## R1: Web Framework Selection

**Decision**: Django 5 with Django templates and HTMX for interactivity

**Rationale**:
- ABConnectTools already provides `SessionTokenStorage` specifically designed for Django — native integration
- Django's built-in session framework, form handling, and middleware pipeline are ideal for this auth-gated CRUD app
- Internal tool for catalog managers — server-rendered HTML is sufficient, no need for a full SPA
- HTMX provides dynamic updates (pagination, filtering, form submission) without a JavaScript build pipeline
- Single-language stack (Python only) minimizes complexity per constitution principle V (Communicable Truth)
- Python 3.14 already available in the project venv

**Alternatives considered**:
- **FastAPI + Jinja2**: Lighter but lacks built-in sessions, forms, and middleware that Django provides out-of-the-box; would require manual session/CSRF handling
- **FastAPI + React SPA**: Adds JavaScript toolchain, Node.js dependency, separate build step — unnecessary for an internal CRUD tool
- **Flask + Jinja2**: Viable but requires assembling session management, CSRF protection, and form handling from third-party packages

## R2: Backend Architecture

**Decision**: Thin proxy layer — Django views call ABConnectTools directly, no local models for catalog data

**Rationale**:
- All catalog data lives in the Catalog API; no need to duplicate it locally
- ABConnectTools already handles authentication, HTTP requests, pagination, and model serialization
- Overrides are written directly to the Catalog API via `LotEndpoint.update()`
- Django's ORM is not used for catalog entities — only for session storage (SQLite)
- No local storage requirement identified in the spec beyond sessions

**Alternatives considered**:
- **Local cache/DB mirror**: Would add sync complexity with no clear benefit for an internal tool with low concurrency
- **Django REST Framework**: Unnecessary — we serve HTML, not a JSON API

## R3: Authentication Strategy

**Decision**: Use ABConnectTools' `SessionTokenStorage` with Django sessions

**Rationale**:
- ABConnectTools provides `SessionTokenStorage` that stores API tokens in the Django session
- Users authenticate with existing ABConnect credentials (username/password)
- Token refresh is handled automatically by the storage layer
- Django's session middleware manages cookies and session persistence
- No additional auth infrastructure needed — no Django User model required for login

**Alternatives considered**:
- **Django's built-in auth + User model**: Unnecessary overhead — users authenticate against ABConnect identity server, not a local database
- **Separate OAuth2 flow**: Over-engineered for an internal tool that already has a working auth system

## R4: Frontend Interaction Pattern

**Decision**: HTMX for dynamic page updates, minimal custom JavaScript

**Rationale**:
- Drill-down navigation (Sellers → Events → Lots) maps naturally to HTMX partial page swaps
- Pagination and filtering can use `hx-get` with query parameters
- Override forms use standard Django forms with `hx-post` for submission
- Django's CSRF protection works with HTMX via `hx-headers` attribute
- No complex client-side state management needed
- Reduces JavaScript to near-zero, keeping the stack Python-centric

**Alternatives considered**:
- **Alpine.js + fetch**: More JavaScript than needed for this interaction model
- **Vanilla JS**: Manual DOM manipulation adds maintenance burden without benefit

## R5: Catalog API Wrapper Analysis

**Decision**: Use ABConnectTools `CatalogAPI` directly — all needed operations are already wrapped

**Rationale**:
- `SellerEndpoint`: list (paginated), get (expanded with catalogs) — covers P1 seller browsing
- `CatalogEndpoint`: list (paginated), get (expanded with sellers + lots) — covers P1 event browsing
- `LotEndpoint`: list (paginated, filterable by catalog), get, update, get_overrides — covers P2 review and P3 overrides
- Override editing maps to `LotEndpoint.update()` with modified `overriden_data` field
- Search by customer item ID maps to `LotEndpoint.list()` with filters and `LotEndpoint.get_overrides()` with customerItemIds
- Pagination response includes `total_items`, `total_pages`, `has_next_page`, `has_previous_page` — ready for UI pagination controls

**Key API mappings**:

| Spec Requirement | API Method | Notes |
|-----------------|------------|-------|
| List sellers | `api.catalog.sellers.list()` | Returns `SellerExpandedDtoPaginatedList` |
| Seller → Events | `api.catalog.sellers.get(id)` | Returns `SellerExpandedDto` with `.catalogs` |
| List events | `api.catalog.catalogs.list()` | Returns `CatalogExpandedDtoPaginatedList` |
| Event → Lots | `api.catalog.lots.list(customer_catalog_id=...)` | Filter lots by catalog |
| Lot detail | `api.catalog.lots.get(id)` | Returns full `LotDto` with initialData, overridenData, imageLinks |
| Set override | `api.catalog.lots.update(id, data)` | `UpdateLotRequest` with modified `overriden_data` |
| Get overrides | `api.catalog.lots.get_overrides(query)` | POST with `customerItemIds` filter |

## R6: Project Structure

**Decision**: Django project at repo root with single app

**Rationale**:
- No frontend build step needed (HTMX loaded from CDN, templates are server-side)
- Single Django app (`catalog`) containing views, forms, and templates
- Tests alongside in `tests/` directory
- ABConnectTools consumed as already-installed editable package
- SQLite for Django session storage only (no catalog data stored locally)

**Alternatives considered**:
- **Multiple Django apps**: Over-engineered for a single-purpose application
- **Monorepo with frontend/backend split**: No separate frontend to warrant this

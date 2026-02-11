# Quickstart: Auction Catalog Manager

**Branch**: `001-auction-catalog-manager` | **Date**: 2026-02-10

## Prerequisites

- Python 3.14+
- ABConnectTools package (already installed as editable in `.venv`)
- Valid ABConnect credentials in `.env` / `.env.staging`

## Setup

```bash
# Enter repo
cd /usr/src/everard

# Activate virtual environment
source .venv/bin/activate

# Install dependencies (after pyproject.toml is created)
pip install -e ".[dev]"

# Run Django migrations (sessions table only)
python src/manage.py migrate
```

## Configuration

The application reads ABConnect credentials from `.env` (production) or `.env.staging` (staging):

```env
ABCONNECT_USERNAME=<username>
ABCONNECT_PASSWORD=<password>
ABC_CLIENT_ID=<client_id>
ABC_CLIENT_SECRET=<client_secret>
ABC_ENVIRONMENT=staging  # omit for production
```

These files are gitignored and must be created locally.

Django settings are in `src/config/settings.py`. Key defaults:
- `DEBUG=True` in development (reads from `DJANGO_DEBUG` env var)
- `SECRET_KEY` reads from `DJANGO_SECRET_KEY` env var (generated default for dev)
- SQLite database at `db.sqlite3` for session storage only

## Run

```bash
# Development server (default: staging API)
python src/manage.py runserver 0.0.0.0:8000

# Or with explicit environment
ABC_ENVIRONMENT=staging python src/manage.py runserver 0.0.0.0:8000
```

Open http://localhost:8000 in your browser. Log in with ABConnect credentials.

## Test

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test category
pytest tests/contract/
pytest tests/integration/
pytest tests/unit/
```

## Project Structure

```
src/
├── manage.py               # Django management entry point
├── config/
│   ├── settings.py         # Django settings
│   ├── urls.py             # Root URL routing
│   └── wsgi.py             # WSGI entry point
└── catalog/
    ├── views/              # View functions (sellers, events, lots, search, auth)
    ├── forms.py            # Override edit form
    ├── services.py         # ABConnectTools CatalogAPI wrapper
    ├── middleware.py        # Auth-required middleware
    ├── urls.py             # App URL patterns
    ├── templatetags/       # Custom template filters
    ├── templates/catalog/  # Django templates (base, sellers, events, lots, search, auth, partials)
    └── static/catalog/     # CSS

tests/
├── conftest.py             # Shared fixtures
├── contract/               # Route contract tests
├── integration/            # Workflow tests
└── unit/                   # Service unit tests
```

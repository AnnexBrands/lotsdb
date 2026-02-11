# LotsDB

Auction Catalog Manager — browse and override lot data.

A Django + HTMX web app for internal catalog managers to browse sellers, events, and lots from the ABConnect Catalog API, review lot details, set data overrides, and import catalogs via drag-and-drop.

## Tech Stack

- Python 3.14, Django 5, HTMX 2.0.4
- ABConnectTools 0.2.1 (ABConnect Catalog API wrapper)
- SQLite3 (sessions only — no local catalog data)
- pytest + pytest-django

## Setup

```bash
git clone <repo-url> && cd everard
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Create a `.env` file in the project root with your ABConnect credentials:

```
ABC_CLIENT_ID=<your-client-id>
ABC_CLIENT_SECRET=<your-client-secret>
```

Optional variables:

```
DJANGO_SECRET_KEY=<production-secret-key>
DJANGO_DEBUG=true
ABC_ENVIRONMENT=staging  # loads .env.staging instead of .env
```

Run migrations:

```bash
python src/manage.py migrate
```

## Running

```bash
python src/manage.py runserver 0.0.0.0:8000
```

Open http://localhost:8000 and log in with your ABConnect credentials.

## Testing

```bash
pytest
```

Test directories:

- `tests/contract/` — Contract tests against API service interfaces
- `tests/integration/` — Integration tests for UI and workflows
- `tests/unit/` — Unit tests

## Project Structure

```
src/
  config/          Django settings, URLs, WSGI
  catalog/         Views, services, templates, static assets
tests/
  contract/        Contract tests
  integration/     Integration tests
  unit/            Unit tests
specs/             Feature specifications
```

## License

MIT — see [LICENSE](LICENSE).

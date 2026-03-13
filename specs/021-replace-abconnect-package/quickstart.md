# Quickstart: 021-replace-abconnect-package

**Date**: 2026-03-13

## Prerequisites

- Python 3.14 with venv at `.venv/`
- Redis running locally
- AB SDK source at `/usr/src/pkgs/AB`
- ABConnectTools at `/usr/src/pkgs/ABConnectTools` (will be uninstalled)

## Setup

### 1. Switch to feature branch

```bash
git checkout 021-replace-abconnect-package
```

### 2. Replace the package

```bash
# Uninstall old package
.venv/bin/pip uninstall -y ABConnectTools

# Install new package (editable)
.venv/bin/pip install -e /usr/src/pkgs/AB
```

### 3. Verify installation

```bash
.venv/bin/python -c "from ab.client import ABConnectAPI; print('AB SDK imported successfully')"
```

### 4. Environment variables

Ensure these are set (in `.env` or shell):

```bash
ABCONNECT_USERNAME=<service_account_or_user>
ABCONNECT_PASSWORD=<password>
ABCONNECT_CLIENT_ID=<oauth2_client_id>
ABCONNECT_CLIENT_SECRET=<oauth2_client_secret>
ABCONNECT_ENVIRONMENT=production  # or staging
```

Note: The new SDK requires `CLIENT_ID` and `CLIENT_SECRET` (OAuth2) which the old SDK did not.

## Running Tests

```bash
cd src && ../.venv/bin/python -m pytest ../tests/ -v
```

## Manual Verification

### Login flow
1. Start dev server: `cd src && ../.venv/bin/python manage.py runserver`
2. Navigate to login page
3. Log in with valid credentials
4. Verify seller list loads

### Import flow
1. Navigate to a seller's catalog list
2. Import a test spreadsheet
3. Verify lots appear with correct dimensions
4. Verify override data is empty for newly imported lots
5. Verify image URLs are only those confirmed to exist on CDN

### Recovery flow
1. Trigger a failed import (e.g., invalid lot data)
2. Navigate to recovery dashboard
3. Retry failed entries

## Key Files Changed

| File | Change |
|------|--------|
| `src/catalog/services.py` | All ABConnect imports → ab imports; API accessor changes |
| `src/catalog/importers.py` | FileLoader replacement; empty overrides; image scanning |
| `src/catalog/views/auth.py` | LoginFailedError → AuthenticationError |
| `src/catalog/views/panels.py` | ABConnectError import path |
| `src/catalog/views/sellers.py` | ABConnectError import path |
| `src/catalog/views/recovery.py` | AddLotRequest import path |
| `src/catalog/management/commands/import_catalog.py` | API initialization + bulk insert path |
| `tests/unit/test_login_bridge.py` | Mock paths updated |
| `external_deps.md` | New file — SDK gap documentation |

## Troubleshooting

### "ConfigurationError: ABCONNECT_CLIENT_ID is required"
The new SDK requires OAuth2 client credentials. Ask your team lead for the `CLIENT_ID` and `CLIENT_SECRET` values.

### "AuthenticationError" on login
Replaces old `LoginFailedError`. Check credentials and that the identity server is reachable.

### Import succeeds but no images on lots
Image scanning probes the CDN. If the CDN is down or images haven't been uploaded, lots will have empty image_links. Check logs for scanning warnings.

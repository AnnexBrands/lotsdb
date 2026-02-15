# everard Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-10

## Active Technologies
- Python 3.14, Django 5 + Django 5, HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install) (002-catalog-dropzone)
- SQLite3 (sessions only); file uploads are in-memory/tempfile, not persisted (002-catalog-dropzone)
- SQLite3 (sessions only); no new storage — all data from ABConnect API (003-spa-shell-layout)
- SQLite3 (sessions only — no new storage) (004-shell-interaction-polish)
- Python 3.14, Django 5 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (005-shell-ux-fixes)
- Python 3.14, Django 5 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install) (006-lots-table-bugfix)
- Python 3.14, Django 5 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install) + Django templates, HTMX, vanilla JS, CSS (008-lots-table-ux-polish)
- Python 3.14, Django 5 + ABConnectTools 0.2.1 (editable install), HTMX 2.0.4 (CDN), Django built-in auth framework (010-access-control)
- SQLite3 (sessions + Django User table via `django.contrib.auth`) (010-access-control)
- Python 3.14, Django 5 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install), Poppins font (Google Fonts CDN — new) (011-lots-table-ux-overhaul)
- SQLite3 (sessions + Django User table) — no changes (011-lots-table-ux-overhaul)
- Python 3.14, Django 5 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install) + No new dependencies — uses existing skeleton CSS classes and JS event listeners (014-lots-skeleton-ux)
- N/A — no backend changes (014-lots-skeleton-ux)
- Python 3.14, Django 5 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install), redis>=5.0 (016-cache-polish)
- SQLite3 (sessions + Django User table), Redis (cache) (016-cache-polish)
- No new storage — all data from ABConnect API; SQLite3 for sessions only (017-lots-modal-overhaul)
- Python 3.14, Django 5.2 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install), redis 7.1.1 (018-critical-bug-fixes)

- Python 3.14, Django 5 + Django 5, HTMX (CDN), ABConnectTools 0.2.1 (editable install) (001-auction-catalog-manager)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.14, Django 5: Follow standard conventions

## Recent Changes
- 018-critical-bug-fixes: Added Python 3.14, Django 5.2 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install), redis 7.1.1
- 017-lots-modal-overhaul: Added Python 3.14, Django 5 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install)
- 016-cache-polish: Added Python 3.14, Django 5 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install), redis>=5.0


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

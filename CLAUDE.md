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
- SQLite3 (sessions only); Django LocMemCache for API response caching (new) (010-performance-ux)

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
- 010-performance-ux: Added Python 3.14, Django 5 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install)
- 009-pagination-ux: Added Python 3.14, Django 5 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install)
- 008-lots-table-ux-polish: Added Python 3.14, Django 5 + HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install) + Django templates, HTMX, vanilla JS, CSS


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

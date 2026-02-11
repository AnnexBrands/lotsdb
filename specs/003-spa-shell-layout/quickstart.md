# Quickstart: SPA Shell Layout

**Feature Branch**: `003-spa-shell-layout`
**Date**: 2026-02-11

## Prerequisites

- Python 3.14
- Django 5
- ABConnectTools 0.2.1 (editable install)
- ABConnect API credentials (for live data)

## Setup

```bash
cd /usr/src/everard/src
```

No new dependencies to install. This feature uses only HTMX 2.0.4 (already loaded via CDN) and CSS.

## Run the Application

```bash
cd /usr/src/everard/src
python manage.py runserver
```

Navigate to `http://localhost:8000/`. You should see the three-panel SPA shell layout:

1. **Left panel (Sellers)**: Paginated list of sellers loaded from ABConnect
2. **Middle panel (Events)**: Empty state — "Select a seller to view events"
3. **Right panel (Lots)**: Empty state — "Select an event to view lots"

## Verify the SPA Behavior

1. **Click a seller** in the left panel → The middle panel loads that seller's events (no full page reload)
2. **Click an event** in the middle panel → The right panel loads that event's lots (no full page reload)
3. **Click a lot** in the right panel → Navigates to the full lot detail page (`/lots/<id>/`)
4. **Click the browser back button** from lot detail → Returns to the SPA shell

## Verify Existing Pages Still Work

All existing pages remain accessible via direct URL:

| URL | Expected |
|-----|----------|
| `/sellers/` | Full-page seller list |
| `/sellers/<id>/` | Full-page seller detail |
| `/events/<id>/` | Full-page event detail |
| `/lots/<id>/` | Full-page lot detail |
| `/lots/<id>/override/` | Override form |
| `/search/?q=test` | Search results |
| `/imports/` | Import file list |

## Verify Panel Endpoints (Fragment Responses)

These endpoints return HTML fragments (no `<!DOCTYPE>`, no `<html>` tag):

```bash
# Sellers panel fragment
curl -s http://localhost:8000/panels/sellers/ | head -5

# Events panel for seller ID 1
curl -s http://localhost:8000/panels/sellers/1/events/ | head -5

# Lots panel for event ID 1
curl -s http://localhost:8000/panels/events/1/lots/ | head -5
```

## Run Tests

```bash
cd /usr/src/everard
pytest
```

### Contract Tests

Contract tests verify:
- Panel endpoints return HTML fragments (not full pages)
- Correct DOM structure (IDs, classes, HTMX attributes)
- Pagination works within each panel
- OOB fragments are present (e.g., clearing lots when a new seller is selected)
- Empty states render when no data
- Error states render when API fails

## File Structure

### New Files

```
src/catalog/
├── templates/catalog/
│   ├── shell.html                    # Three-panel SPA layout (extends base.html)
│   └── partials/
│       ├── seller_list_panel.html    # Left1: sellers list fragment
│       ├── events_panel.html         # Left2: events list fragment
│       └── lots_panel.html           # Main: lots list fragment
├── views/
│   └── panels.py                     # Panel fragment views
├── static/catalog/
│   └── styles.css                    # Updated with shell layout styles

src/catalog/urls.py                   # New panel routes added
```

### Modified Files

```
src/catalog/templates/catalog/base.html    # Updated navbar with logo
src/catalog/static/catalog/styles.css      # Shell layout + refined design
src/catalog/urls.py                        # Panel endpoint routes
```

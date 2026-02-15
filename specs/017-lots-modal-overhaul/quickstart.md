# Quickstart: Lots Modal Overhaul

**Branch**: `017-lots-modal-overhaul` | **Date**: 2026-02-14

## Prerequisites

- Python 3.14 with Django 5 development environment
- ABConnectTools 0.2.1 installed (editable install)
- Redis running locally (for caching)
- Valid `.env` file with ABConnect credentials

## Setup

```bash
cd /usr/src/lotsdb
git checkout 017-lots-modal-overhaul
pip install -e /opt/pack/ABConnectTools  # if not already installed
cd src
python manage.py migrate                 # ensure session tables exist
```

## Run Development Server

```bash
cd /usr/src/lotsdb/src
python manage.py runserver 0.0.0.0:8000
```

## Manual Testing

### P1: Modal Layout with Gallery and Override Form

1. Navigate to `http://localhost:8000/`
2. Log in with valid ABConnect credentials
3. Select a seller from the left panel
4. Select an event with lots
5. **Click any lot thumbnail or description** in the lots table

**Verify**:
- Modal opens centered on screen (both axes)
- Left side shows image gallery with main image and thumbnail strip
- Right side shows lot title, description, notes
- Right side shows inline override form with: Qty, L, W, H, Wgt, CPack dropdown, Force Crate checkbox, Do Not Tip checkbox
- Each form field shows initial value reference below the input
- Overridden fields have orange left border indicator
- CPack dropdown shows color-coded badge
- Click Save → override persists, modal closes, toast shows "Override saved", table row updates

### P1: Responsive Layout

1. Resize browser below 768px width
2. Open lot modal

**Verify**:
- Gallery stacks above info section (single column)
- All content remains accessible without horizontal scroll

### P1: Gallery Navigation

1. Open a lot modal for a lot with multiple images

**Verify**:
- Main image displays first image
- Thumbnail strip shows all images
- Clicking a thumbnail swaps the main image
- Active thumbnail has highlighted border

### P1: Empty Image State

1. Open a lot modal for a lot with no images

**Verify**:
- Gallery area shows placeholder icon and "No images" text
- Right column still renders correctly

### P2: Recommendation Engine Section

1. Open any lot modal and scroll below the hero section

**Verify**:
- Three sizing cards visible: Minimum, Recommended, Oversize
- Recommended card has distinct visual highlight (border/background color)
- Each card shows placeholder dimensions and pack type
- "Quoter Pending" badge visible in section header

### P3: Related Lots Card Stacks

1. Open any lot modal and scroll to the bottom section

**Verify**:
- Three columns visible: Q25 Low, Q50 Median, Q75 High
- Each column shows stacked cards with layered visual effect
- Top card fully visible, behind cards progressively faded
- Up/down navigation arrows work (cycling through cards)
- Counter updates (e.g., "1/3" → "2/3")
- Each card shows: image, lot title, dimensions, weight, cpack badge, Accept button
- "Similarity Matching" badge visible in section header

### P3: Accept Button

1. Click "Accept" on any related lot card

**Verify**:
- Override form fields (L, W, H, Wgt, CPack) update to match the accepted lot's values
- Form is marked as dirty (Save button activates)

## Run Tests

```bash
cd /usr/src/lotsdb
pytest
```

## Files Changed

| File | Change |
| ---- | ------ |
| `src/catalog/templates/catalog/partials/lot_detail_modal.html` | Complete rewrite — new two-column hero + recommendation + related lots layout |
| `src/catalog/static/catalog/styles.css` | New CSS for hero grid, override form, quoter cards, card stacks, responsive breakpoints |
| `src/catalog/views/panels.py` | Updated `lot_detail_panel()` GET handler to pass `fields` dict instead of `rows` list |
| `src/catalog/templates/catalog/shell.html` | Updated modal JS for new gallery navigation, card stack nav, and Accept button handler |
| `tests/contract/test_panels.py` | New/updated tests for modal detail endpoint context |

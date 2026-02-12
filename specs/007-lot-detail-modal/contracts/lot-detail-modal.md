# API Contracts: Lot Detail Modal

**Feature**: 007-lot-detail-modal | **Date**: 2026-02-11

## Endpoints

### GET /panels/lots/{lot_id}/detail/

Returns the lot detail as an HTML fragment for the modal.

**Parameters**:
- `lot_id` (path, int, required): Internal lot ID
- `edit` (query, string, optional): If `"1"`, returns the override edit form instead of the read-only detail view

**Response (200)**: HTML fragment
- Content-Type: `text/html`
- Without `?edit=1`: Read-only detail view with field table + images
- With `?edit=1`: Editable override form with all 13 fields

**Response (500)**: HTML error fragment
- Displays error message within the modal body

**HTMX Integration**:
- Triggered by: `hx-get="/panels/lots/{lot_id}/detail/"` on lot row click
- Target: `#lot-modal-body`
- Swap: `innerHTML`
- After swap: JS calls `dialog.showModal()`

### POST /panels/lots/{lot_id}/detail/

Saves override data submitted from the modal edit form.

**Request**:
- Content-Type: `application/x-www-form-urlencoded`
- Body fields: `qty`, `l`, `w`, `h`, `wgt`, `value`, `cpack`, `description`, `notes`, `noted_conditions`, `commodity_id`, `force_crate`, `do_not_tip`
- CSRF token: via `X-CSRFToken` header (provided by HTMX body hx-headers)

**Response (200 — success)**:
- HTML fragment: Empty or minimal content for the modal (will be closed)
- Out-of-band swap: Updated `<tr id="lot-row-{lot_id}" hx-swap-oob="outerHTML">` with refreshed row data
- Headers:
  - `HX-Trigger: {"closeModal": true, "showToast": {"message": "Override saved", "type": "success"}}`

**Response (200 — validation error)**:
- HTML fragment: Re-rendered edit form with error messages displayed inline
- No OOB swap
- No close trigger

**Response (500 — API error)**:
- HTML fragment: Error message within the modal body
- Headers:
  - `HX-Trigger: {"showToast": {"message": "Could not save override", "type": "error"}}`

## Modal HTML Structure

```html
<!-- In shell.html -->
<dialog id="lot-modal" aria-labelledby="lot-modal-title">
    <div class="modal-container">
        <div class="modal-header">
            <h2 id="lot-modal-title">Lot Detail</h2>
            <button class="modal-close" aria-label="Close">&times;</button>
        </div>
        <div id="lot-modal-body" class="modal-body">
            <!-- HTMX loads content here -->
        </div>
    </div>
</dialog>
```

## HTMX Trigger on Lot Row

```html
<!-- In lots_table_row.html — thumbnail cell gains click handler -->
<td class="lot-thumb-cell"
    hx-get="/panels/lots/{{ row.lot.id }}/detail/"
    hx-target="#lot-modal-body"
    hx-swap="innerHTML"
    style="cursor: pointer;">
```

## Custom Events

| Event | Trigger | Handler |
|-------|---------|---------|
| `closeModal` | HX-Trigger response header | JS closes `<dialog>` via `.close()` |
| `showToast` | HX-Trigger response header | Existing toast system displays message |
| `htmx:afterSwap` on `#lot-modal-body` | HTMX swap complete | JS calls `dialog.showModal()` if not already open |

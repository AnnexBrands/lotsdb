# Contract: Lot Detail Panel Endpoint

**Endpoint**: `GET /panels/lots/{lot_id}/detail/`
**View**: `catalog.views.panels.lot_detail_panel`
**Status**: Existing endpoint — contract updated for new modal template

## GET Request (Detail View)

### URL Parameters

| Parameter | Type | Required | Description |
| --------- | ---- | -------- | ----------- |
| `lot_id` | int | Yes | Lot ID (path parameter) |

### Query Parameters

| Parameter | Type | Required | Description |
| --------- | ---- | -------- | ----------- |
| `edit` | str | No | Legacy: if "1", returns old edit form (backward compat) |

### Response (HTML Fragment)

Returns `lot_detail_modal.html` with context:

```python
{
    "lot": LotDto,              # Full lot object
    "fields": {                 # Override field comparison dict
        "qty":         {"value": ..., "changed": bool, "original": ...},
        "l":           {"value": ..., "changed": bool, "original": ...},
        "w":           {"value": ..., "changed": bool, "original": ...},
        "h":           {"value": ..., "changed": bool, "original": ...},
        "wgt":         {"value": ..., "changed": bool, "original": ...},
        "cpack":       {"value": ..., "changed": bool, "original": ...},
        "force_crate": {"value": ..., "changed": bool, "original": ...},
        "do_not_tip":  {"value": ..., "changed": bool, "original": ...},
    },
    "lot_description": str,     # Effective description
    "lot_notes": str,           # Effective notes
}
```

### HTMX Target

- Target: `#lot-modal-body`
- Swap: `innerHTML`
- Response element must include `data-lot-title` attribute for modal title extraction

---

## POST Request (Save Override)

### Request Body (form-encoded)

| Field | Type | Required | Description |
| ----- | ---- | -------- | ----------- |
| `qty` | int | No | Quantity override |
| `l` | decimal | No | Length override |
| `w` | decimal | No | Width override |
| `h` | decimal | No | Height override |
| `wgt` | decimal | No | Weight override |
| `cpack` | str | No | Case/Pack code override |
| `force_crate` | bool | No | Force crate flag |
| `do_not_tip` | bool | No | Do not tip flag |

### Response (Success)

Returns `lots_table_row.html` with OOB swap:

```
HX-Trigger: {"closeModal": true, "showToast": {"message": "Override saved", "type": "success"}}
```

The response body is the updated table row with `hx-swap-oob="outerHTML"` to update the lots table in the background.

### Response (Validation Error)

Returns the modal form with validation errors highlighted. No `closeModal` trigger.

### Response (API Error)

Returns `panel_error.html` with:

```
HX-Trigger: {"showToast": {"message": "Could not save override", "type": "error"}}
```

---

## POST /panels/lots/{lot_id}/text-save/ (Unchanged)

Saves description/notes from modal textareas. Returns OOB table row update. No changes needed for this feature.

---

## POST /panels/lots/{lot_id}/override/ (Unchanged)

Saves inline override from lots table row auto-save. Returns updated table row. No changes needed for this feature.

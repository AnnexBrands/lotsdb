# Contract: Notes Save (Inline Edit)

No new endpoints are introduced. This documents the existing `lot_text_save` endpoint that the notes contenteditable feature will call.

## POST /panels/lots/{lot_id}/text-save/

**Purpose**: Save edited notes (or description) text from the lot detail modal.

### Request

- **Method**: POST
- **Content-Type**: application/x-www-form-urlencoded
- **Headers**: `X-CSRFToken: <token>` (inherited from `<body hx-headers>`)
- **Body parameters**:
  - `notes` (string, optional): Updated notes text
  - `description` (string, optional): Updated description text
  - At least one field must be present

### Response — Success (200)

- **Body**: Updated `<tr>` HTML fragment with `hx-swap-oob="outerHTML"` (updates the lots table row)
- **Headers**:
  - `HX-Trigger: {"showToast": {"message": "Saved", "type": "success"}}`

### Response — No Fields (400)

- **Body**: Error panel HTML
- **Headers**: None

### Response — Server Error (500)

- **Body**: Error panel HTML
- **Headers**:
  - `HX-Trigger: {"showToast": {"message": "Could not save", "type": "error"}}`

### Merge Behavior

The `save_lot_override()` service merges the submitted fields with existing override data. Sending only `notes` preserves all existing dimension/flag overrides. Sending only `description` preserves notes and all other fields.

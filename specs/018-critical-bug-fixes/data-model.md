# Data Model: 018-critical-bug-fixes

No new entities or data model changes are required. This feature fixes bugs in existing functionality.

## Existing Entities (Reference)

### Cache Entry
- **Key format**: `cat_sellers_all` (all sellers), `cat_catalogs_seller_{id}` (events per seller)
- **Value**: List of lightweight projected dicts (serialized via pickle)
- **TTL**: None (no expiry — cache persists until explicitly busted on insert)
- **Storage**: Redis (external)

### Lot Override
- **Fields**: qty, l, w, h, wgt, value, cpack, description, notes, item_id, force_crate, noted_conditions, do_not_tip, commodity_id
- **Behavior**: Merge-on-save — new overrides are merged with existing, preserving fields not in the current save request
- **Storage**: ABConnect API (external)

## Data Flow Changes

### Notes Save (Bug 4)
- **Input**: `notes` field from contenteditable element's `textContent` on blur
- **Endpoint**: `POST /panels/lots/{lot_id}/text-save/`
- **Request body**: `notes=<text content>` (form-encoded)
- **Response**: OOB `<tr>` update + `HX-Trigger: {"showToast": {"message": "Saved", "type": "success"}}`
- **Merge behavior**: Only the `notes` field is sent; existing dimension/flag overrides are preserved by `save_lot_override()`

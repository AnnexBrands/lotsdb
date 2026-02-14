# Data Model: Dimensions Input UX

No data model changes. This feature is purely a template and CSS change — the underlying lot data structure (qty, l, w, h, wgt) and the override save endpoint remain identical.

## Affected Entities (no changes)

| Entity | Field | Type | Notes |
|--------|-------|------|-------|
| Lot | qty | number | Quantity — no change |
| Lot | l | number | Length — no change |
| Lot | w | number | Width — no change |
| Lot | h | number | Height — no change |
| Lot | wgt | number | Weight — no change |

## Template Data Flow (unchanged)

1. `build_lot_table_rows()` in `panels.py` builds `row.fields.{qty,l,w,h,wgt}` dicts with `value`, `changed`, `original` keys
2. `lots_table_row.html` renders each field as an `<input type="number">`
3. The `format_number` template filter formats values (int if whole, decimal if fractional)
4. On save, `lot_override_panel()` reads POST fields `qty`, `l`, `w`, `h`, `wgt` — field names are unchanged

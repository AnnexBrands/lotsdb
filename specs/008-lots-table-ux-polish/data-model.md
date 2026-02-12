# Data Model: Lots Table UX Polish

**Feature**: 008-lots-table-ux-polish | **Date**: 2026-02-11

## No New Data Models

This feature is purely a frontend UX change. No new entities, fields, or data shapes are introduced.

## Existing Entities (Unchanged)

### LotTableRow (view model — built in `build_lot_table_rows()`)

```python
{
    "lot": LotDto,           # Full lot object from ABConnect API
    "lot_number": str,       # From lot.catalogs[0].lot_number
    "fields": {
        "<field_name>": {
            "value": Any,    # Display value (override if present, else initial)
            "changed": bool, # True if overridden and differs from initial
            "original": Any, # Initial value (for tooltip)
        },
        # Fields: description, notes, qty, l, w, h, wgt, cpack, force_crate, do_not_tip
    },
}
```

### Cpack Valid Values (new constraint, no model change)

The `cpack` field accepts: `""` (empty), `"1"`, `"2"`, `"3"`, `"4"`, `"PBO"`.

This is enforced at the template level via `<select>` options, not in the backend form or API. The existing `CharField` in `OverrideForm` and the string parsing in `lot_override_panel` remain unchanged.

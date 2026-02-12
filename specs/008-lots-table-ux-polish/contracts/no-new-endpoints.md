# Contracts: Lots Table UX Polish

**Feature**: 008-lots-table-ux-polish | **Date**: 2026-02-11

## No New Endpoints

This feature modifies no API contracts. All existing endpoints remain unchanged:

| Endpoint | Method | Purpose | Changes |
|----------|--------|---------|---------|
| `/panels/lots/<id>/override/` | POST | Save inline row override | None — same fields, same parsing |
| `/panels/lots/<id>/detail/` | GET | Load lot detail modal | None |
| `/panels/lots/<id>/detail/?edit=1` | GET | Load lot edit form in modal | None |
| `/panels/lots/<id>/detail/` | POST | Save override from modal | None |

## Template Contract Changes

The `lots_table_row.html` template renders differently but sends identical POST data:
- `description` (text) — now from `<textarea>` instead of `<input type="text">`
- `notes` (text) — removed from inline form; now only editable via detail modal
- `cpack` (text) — now from `<select>` instead of `<input type="text">`; value is still a string
- All other fields unchanged

# Data Model: 011-lots-table-ux-overhaul

No new data entities are introduced. This feature modifies presentation and interaction patterns for existing entities.

## Modified Entities

### LotTableRow (view-layer dict, `build_lot_table_rows`)

Current structure:
```python
{
    "lot": LotDto,
    "lot_number": str,
    "fields": {
        "description": {"value": str, "changed": bool, "original": str},
        "notes":       {"value": str, "changed": bool, "original": str},
        "qty":         {"value": int, "changed": bool, "original": int},
        "l":           {"value": float, "changed": bool, "original": float},
        # ... w, h, wgt, cpack, force_crate, do_not_tip
    }
}
```

**Changes**: None to the data structure. The `changed` flag per field drives per-input override styling (instead of per-cell).

### CPack Display Mapping (new static constant)

```python
CPACK_DISPLAY = {
    "1": {"label": "NF", "css_class": "cpack-nf"},
    "2": {"label": "LF", "css_class": "cpack-lf"},
    "3": {"label": "F",  "css_class": "cpack-f"},
    "4": {"label": "VF", "css_class": "cpack-vf"},
    "PBO": {"label": "PBO", "css_class": "cpack-pbo"},
}
```

Location: `catalog/templatetags/catalog_tags.py` (as a template filter or inclusion tag).

### Number Formatting (template filter)

Existing `format_dimension` filter already uses `:g` format which strips trailing zeros. This filter should be applied to input `value` attributes in the lots table row template. Currently inputs use raw `{{ row.fields.wgt.value|default:"" }}` — these need to pipe through a format filter.

## Removed Routes

| Removed URL Pattern | View Function | Template |
|---|---|---|
| `sellers/` | `seller_list` (full-page branch) | `catalog/sellers/list.html` |
| `sellers/<id>/` | `seller_detail` | `catalog/sellers/detail.html` |
| `events/<id>/` | `event_detail` | `catalog/events/detail.html` |
| `lots/<id>/` | `lot_detail` | `catalog/lots/detail.html` |
| `lots/<id>/override/` | `override_form` | `catalog/lots/override.html` |
| `search/` | `search_lots_view` | `catalog/search.html` |
| `imports/` | `import_list` | `catalog/imports/list.html` |
| `imports/run/` | `import_file` | (no template) |
| `imports/upload/` | `upload_catalog` | (no template) |

The `/sellers/` path at `/` (SPA shell) stays — the `seller_list` view still serves the SPA shell when `request.path == "/"`. The separate `/sellers/` route that renders the full-page list is removed.

# Quickstart: Dimensions Input UX

## Files Changed

| File | Change |
|------|--------|
| `src/catalog/templates/catalog/partials/lots_table_row.html` | Wrap each dim input in `.lot-dims-field` with `.lot-dims-label`; add "in" separator |
| `src/catalog/static/catalog/styles.css` | Add `.lot-dims-field`, `.lot-dims-label`; update `.lot-dims-input`, `.lot-dims-wgt`, `.lot-dims-sep` widths and colors |
| `tests/contract/test_panels.py` | Add/update contract tests for floating labels and separator tokens |

## How to Test

### Manual Testing

1. Start the dev server:
   ```bash
   cd src && python manage.py runserver
   ```

2. Log in and navigate to a seller > event with lots

3. Verify dimensions cell layout:
   - Inputs render LTR: Qty @ L x W x H in, Wgt lbs
   - Each input has a small label above it ("Qty", "L", "W", "H", "Wgt")
   - Separators ("@", "x", "in", "lbs") are visually muted (lighter than input values)
   - Labels match the muted separator style

4. Test value display:
   - Find or edit a lot with large dimension values (e.g., 10000.5)
   - Confirm the full value is visible in the input — no truncation or clipping
   - Tab through fields to confirm focus styling works

5. Test overrides:
   - Edit a dimension value and tab out (or wait for auto-save)
   - Confirm the orange left-border indicator appears on changed fields
   - Confirm auto-save triggers correctly

### Automated Testing

```bash
python -m pytest tests/ -v
```

All existing tests must pass plus new contract tests for:
- Floating label presence and text
- Separator token content
- Input field structure

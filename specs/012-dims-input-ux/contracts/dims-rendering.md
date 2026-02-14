# Contract: Dimensions Cell Rendering

## Overview

Defines the HTML structure and CSS class contracts for the dimensions cell in `lots_table_row.html`. No API endpoint changes — this is a rendering contract only.

## HTML Structure Contract

Each lot row's dimensions `<td>` MUST render the following structure:

```html
<td>
    <div class="lot-dims">
        <div class="lot-dims-field">
            <span class="lot-dims-label">Qty</span>
            <input type="number" name="qty" class="lot-input lot-dims-input" ...>
        </div>
        <span class="lot-dims-sep">@</span>
        <div class="lot-dims-field">
            <span class="lot-dims-label">L</span>
            <input type="number" name="l" class="lot-input lot-dims-input" ...>
        </div>
        <span class="lot-dims-sep">x</span>
        <div class="lot-dims-field">
            <span class="lot-dims-label">W</span>
            <input type="number" name="w" class="lot-input lot-dims-input" ...>
        </div>
        <span class="lot-dims-sep">x</span>
        <div class="lot-dims-field">
            <span class="lot-dims-label">H</span>
            <input type="number" name="h" class="lot-input lot-dims-input" ...>
        </div>
        <span class="lot-dims-sep">in</span>
        <span class="lot-dims-sep">,</span>
        <div class="lot-dims-field">
            <span class="lot-dims-label">Wgt</span>
            <input type="number" name="wgt" class="lot-input lot-dims-wgt" ...>
        </div>
        <span class="lot-dims-sep">lbs</span>
    </div>
</td>
```

## CSS Class Contract

| Class | Element | Purpose |
|-------|---------|---------|
| `.lot-dims` | Container div | Flex row, `align-items: flex-end`, no wrap |
| `.lot-dims-field` | Wrapper per input | Flex column: label above input |
| `.lot-dims-label` | Label span | Muted style: slate-400, font-weight 400, small font |
| `.lot-dims-input` | Number inputs (qty, l, w, h) | `min-width: 5ch`, no truncation |
| `.lot-dims-wgt` | Weight input | `min-width: 6ch`, no truncation |
| `.lot-dims-sep` | Separator tokens | Muted style: slate-400, font-weight 400, `user-select: none` |
| `.lot-input-overridden` | Override indicator | Existing orange left-border — unchanged |

## Input Name Contract (unchanged)

POST field names MUST remain: `qty`, `l`, `w`, `h`, `wgt`. The override save endpoint depends on these exact names.

## Test Contract

Contract tests MUST verify:
1. Each dimension input has a sibling `.lot-dims-label` element
2. Label text matches expected values ("Qty", "L", "W", "H", "Wgt")
3. The `.lot-dims-sep` elements contain the expected tokens ("@", "x", "in", "lbs")
4. Input `name` attributes are unchanged
5. Override class `.lot-input-overridden` is applied when field has changed value

# Research: Dimensions Input UX

## R1: Current Dimensions Layout

**Decision**: Modify the existing `lot-dims` flexbox layout in `lots_table_row.html` and `styles.css`.

**Rationale**: The current implementation already uses a flex row with `lot-dims-input` and `lot-dims-sep` classes. The structure is correct (LTR, inline) — what needs to change is:
- Input widths: currently fixed at `3rem` / `3.5rem`, which truncates large values
- Separator styling: currently `color: #64748b` (slate-500), `font-size: 0.6875rem` — needs to shift to `#94a3b8` (slate-400) with `font-weight: 400`
- No labels exist above inputs — need to add floating headers

**Alternatives considered**: Splitting dimensions into separate table columns was rejected because it would break the single-column layout and require changes across the panel system.

## R2: Floating Label Pattern

**Decision**: Use CSS-only floating labels positioned above each input using a wrapper `<div>` per input with a `<span>` label and the `<input>` stacked vertically inside the flex row.

**Rationale**: Each dimension input gets wrapped in a small container:
```html
<div class="lot-dims-field">
    <span class="lot-dims-label">L</span>
    <input ...>
</div>
```
The label uses the same muted color/weight as separators. The wrapper uses `display: flex; flex-direction: column; align-items: center;` so the label sits above the input with minimal vertical space.

**Alternatives considered**:
- `placeholder` attribute: Disappears on focus/value — not suitable for persistent labels
- `<label>` elements: Semantically correct but requires `for`/`id` wiring; since these are table-inline inputs with no form, `<span>` is simpler and equally accessible with `aria-label` on the input
- CSS `::before` pseudo-elements: Fragile, hard to maintain, and can't be selected/read by screen readers

## R3: Input Width Strategy

**Decision**: Use `min-width` based on `ch` units to ensure values up to 7 characters (e.g., "99999.9") are never truncated, while keeping the layout compact for typical 1-3 digit values.

**Rationale**:
- `ch` units are proportional to the font's "0" character width, making them reliable for numeric inputs
- `min-width: 5ch` for qty (typically 1-3 digits), `min-width: 7ch` for L/W/H/wgt (up to 5 digits + decimal)
- Combined with `width: auto`, inputs will grow if content exceeds the minimum
- `type="number"` inputs have built-in spinner controls in some browsers — the existing `padding` already accounts for this

**Alternatives considered**:
- JavaScript auto-resize: Adds complexity, potential layout jank on every keystroke
- Fixed large widths: Wastes space for typical small values, makes the table unnecessarily wide
- `max-content` width: Doesn't work reliably on `<input>` elements

## R4: Separator Token Styling

**Decision**: Update `.lot-dims-sep` to use `color: #94a3b8` (slate-400), `font-weight: 400`, `font-size: 0.625rem` (10px). Add "in" after H input.

**Rationale**: The user specifically mentioned "muted 400?" suggesting font-weight 400 with a muted color. Slate-400 (#94a3b8) is one step lighter than the current slate-500 (#64748b), creating clearer visual separation between editable values and decorative tokens. The slightly smaller font size (10px vs current 11px) further reduces visual weight.

**Alternatives considered**:
- Keeping current slate-500: Too prominent, doesn't achieve the "recede" effect requested
- Using slate-300 (#cbd5e1): Too faint, could be missed entirely

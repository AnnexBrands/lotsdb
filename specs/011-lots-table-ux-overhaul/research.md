# Research: 011-lots-table-ux-overhaul

## R1: Can initial_data be updated via the API?

**Decision**: No — use `overriden_data` for description/notes edits.

**Rationale**: `UpdateLotRequest` only accepts `customer_item_id`, `image_links`, `overriden_data`, and `catalogs`. The `initial_data` field exists only in `AddLotRequest` (creation) and `LotDto` (read). The API treats initial data as immutable after lot creation.

**Implication**: Description and notes edits in the modal save to `overriden_data[0]`, but the UX labels them as "Description" / "Notes" (not "Override Description"). The `build_lot_table_rows` function already resolves the effective value (override if present, else initial), so this works transparently.

**Alternatives considered**: Modifying ABConnectTools to support initial_data updates — rejected because the upstream API does not support it.

## R2: Poppins font loading strategy

**Decision**: Add Google Fonts `<link>` to `base.html` `<head>` for Poppins weight 900 only.

**Rationale**: Single weight (900) keeps the payload minimal (~15KB woff2). Google Fonts CDN has global edge caching. No new npm/pip dependency.

**Implementation**:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@900&display=swap" rel="stylesheet">
```

**Alternatives considered**: Self-hosting the font file — rejected (adds asset management overhead for a single weight; CDN is simpler and faster).

## R3: Image gallery approach for the modal

**Decision**: CSS scroll-snap horizontal gallery with thumbnail strip navigation. No JS library.

**Rationale**: The current modal already displays `lot.image_links` as a simple flex grid. Converting to a horizontal scroll-snap gallery gives swipeable/scrollable behavior with pure CSS. A small thumbnail strip below (or dot indicators) lets the user jump to a specific image. This keeps the dependency count at zero.

**Implementation pattern**:
```css
.gallery { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; }
.gallery img { scroll-snap-align: start; flex-shrink: 0; width: 100%; }
```

**Alternatives considered**:
- Lightbox.js / Fancybox — rejected (new dependency for a simple feature)
- CSS-only with radio buttons — rejected (hacky, accessibility concerns)

## R4: Override styling redesign

**Decision**: Per-input left border accent instead of cell-wide yellow background.

**Rationale**: Current `.overridden { background: #fff3cd; }` applies to the entire `<td>`, which is visually heavy. With merged dimensions columns, highlighting the entire cell when only one value is overridden is misleading. A 2px left border on the individual `<input>` is subtle, precise, and doesn't interfere with readability.

**Implementation**:
```css
.lot-input-overridden { border-left: 2px solid #f59e0b; padding-left: 0.25rem; }
```

**Alternatives considered**:
- Colored text — rejected (reduces readability, conflicts with cpack colors)
- Bottom underline — rejected (interferes with input border styling on focus)
- Bold text — rejected (changes input width, causes layout jitter)

## R5: CPack color mapping

**Decision**: Five distinct colors from the existing design palette, sufficient contrast on white background.

| Code | Label | Color | CSS Variable |
|------|-------|-------|-------------|
| 1 | NF | Green `#16a34a` | `--cpack-nf` |
| 2 | LF | Blue `#2563eb` | `--cpack-lf` |
| 3 | F | Amber `#d97706` | `--cpack-f` |
| 4 | VF | Red `#dc2626` | `--cpack-vf` |
| PBO | PBO | Purple `#7c3aed` | `--cpack-pbo` |

**Rationale**: These colors are already used or adjacent to colors in the existing stylesheet (badges, buttons, links). They provide sufficient visual distinction and all pass WCAG AA contrast on white for 900-weight text.

## R6: Select-on-focus for dimension inputs

**Decision**: Use `onfocus="this.select()"` attribute on dimension `<input>` elements.

**Rationale**: Native browser support, zero JS overhead, works across all browsers. The `select()` method selects the entire value on focus, allowing immediate overwrite by typing.

**Alternatives considered**:
- JS event delegation with `document.body.addEventListener('focus', ...)` — works but unnecessary overhead for a native feature.

## R7: Description/Notes save flow in modal (UPDATED post-clarification)

**Decision**: Add merge-on-save logic to `save_lot_override` in `services.py`. Modal text saves use a new dedicated endpoint (`/panels/lots/<id>/text-save/`) that submits only the changed text field(s). The merge logic in `save_lot_override` fetches existing override values and overlays new fields on top, preventing clobbering.

**Rationale**: The clarification session established auto-save-on-blur for modal text fields. Each textarea fires `hx-trigger="change"` (on blur-if-changed) and POSTs only its own field (description OR notes) to the text-save endpoint. The merge-on-save pattern in `save_lot_override` ensures that submitting only `description` preserves existing `wgt`, `cpack`, etc. overrides — and vice versa for inline row saves preserving text overrides.

**Implementation**:
- `save_lot_override` fetches `lot.overriden_data[0]`, extracts non-None values as a base dict, overlays the new `override_data` on top, then creates `LotDataDto` from the merged result.
- New view `lot_text_save` in `panels.py` accepts POST with `description` and/or `notes`, calls `save_lot_override` with merge, returns OOB swap of the table row.
- The old full-form edit modal approach (`OverrideForm` with all fields) is replaced by auto-save per field.

**Alternatives considered**:
- Keep the existing full-form POST with all fields pre-populated — rejected because auto-save-on-blur means individual fields save independently, not as a full form.
- Client-side merge (JS collects all current override values before POSTing) — rejected because server-side merge is more reliable and prevents race conditions.

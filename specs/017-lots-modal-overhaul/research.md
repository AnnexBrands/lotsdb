# Research: Lots Modal Overhaul

**Branch**: `017-lots-modal-overhaul` | **Date**: 2026-02-14

## R1: Modal Centering Approach

**Decision**: Retain HTML5 `<dialog>` element with `showModal()` — already centers both axes natively.

**Rationale**: The existing `dialog.showModal()` call in `shell.html:128` handles centering automatically. Browser-native dialog centering is more reliable and accessible than CSS flexbox/grid centering hacks. The `::backdrop` pseudo-element handles the overlay. No changes needed for centering itself.

**Alternatives considered**:
- CSS `position: fixed` + `transform: translate(-50%, -50%)` — fragile, doesn't handle overflow well
- Flexbox body centering — conflicts with existing SPA shell layout
- **Keep existing approach** — zero risk, already works

## R2: Two-Column Hero Layout Strategy

**Decision**: Replace the current sequential layout (gallery → text → detail table) inside `lot_detail_modal.html` with a CSS Grid two-column layout: gallery left (45%), info + override form right (55%).

**Rationale**: The mockup (`m6-full-composite.html`) uses `grid-template-columns: 45% 1fr` for the `.lot-hero` section. CSS Grid is already used throughout the SPA shell layout. This is the simplest approach that matches the mockup exactly. The gallery fills the left column with main image + thumbnail strip. The right column stacks: lot title/description, notes, and inline override form.

**Alternatives considered**:
- CSS Flexbox — less control over column sizing with overflow content
- Two separate HTMX fragments — unnecessary complexity, adds round-trips
- **CSS Grid** — matches mockup, existing pattern, responsive with `@media` fallback to single column

## R3: Inline Override Form in Modal (Replacing Two-Step Edit Flow)

**Decision**: Replace the current two-step detail → edit flow with a single unified view. The override form fields (qty, L, W, H, wgt, cpack, force_crate, do_not_tip) render directly in the modal's right column, matching the lots table row form layout. Remove the separate `lot_edit_modal.html` template from the feature's scope.

**Rationale**: The spec requires "same as lots table" override form in the modal. The current modal shows a read-only detail table and requires clicking "Edit Details" to switch to a generic Django form. The new layout embeds the compact inline form (identical field layout to `lots_table_row.html`) directly in the hero section. This eliminates a navigation step and lets operators edit while viewing images.

**Key implementation details**:
- The modal override form POSTs to the existing `/panels/lots/{id}/detail/` endpoint (same as current edit form)
- The backend `lot_detail_panel()` POST handler already handles OverrideForm validation and returns OOB table row updates
- The new template builds form fields manually (like `lots_table_row.html`) rather than using Django's generic `{{ form.field }}` rendering
- Initial values shown below inputs use `lot.initial_data` attributes; override indicator uses same `lot-input-overridden` class

**Alternatives considered**:
- Keep two-step flow but restyle — doesn't satisfy spec FR-005 (same fields as lots table)
- Auto-save in modal (like table row 15s timer) — too complex for initial version; explicit Save button is clearer in modal context
- Separate HTMX form endpoint — unnecessary; existing endpoint works

## R4: Modal Width Increase

**Decision**: Increase `dialog#lot-modal` max-width from 700px to 840px to accommodate the two-column hero layout.

**Rationale**: The mockup uses `max-width: 840px`. The current 700px is too narrow for a meaningful 45/55 split with gallery + form side by side. 840px provides comfortable space for image display (~378px) and form fields (~462px) without horizontal scrolling.

**Alternatives considered**:
- Keep 700px — too cramped for two-column layout, inputs would be uncomfortably narrow
- Full viewport width — too wide on large screens, loses modal feel
- **840px** — matches mockup, tested in reference HTML

## R5: Recommendation Engine Section (Placeholder)

**Decision**: Add a static HTML section below the hero with three cards (Minimum, Recommended, Oversize). Content is hardcoded placeholder data with a "Quoter Pending" badge. No backend integration.

**Rationale**: The spec (P2) explicitly states this is placeholder UI. The ABConnectTools `Quoter.py` module handles freight quoting, not box sizing — there is no existing backend service for sizing recommendations. Building the UI shell now allows future integration without layout changes.

**Structure**: Three-card CSS Grid (`grid-template-columns: 1fr 1fr 1fr`), matching the mockup's `.quoter-grid` class. Middle card gets `.recommended` visual treatment.

## R6: Related Lots Card Stacks (Placeholder)

**Decision**: Add a static HTML section below the recommendation engine with three columns of stacked cards. Content is hardcoded placeholder data with a "Similarity Matching" badge. No backend integration.

**Rationale**: The spec (P3) explicitly states this is placeholder UI. No similarity matching or related lots API exists in ABConnectTools. The card stack UI requires vanilla JS for navigation (cycling cards via `data-pos` attributes), matching the mockup's stack pattern.

**Structure**: Three-column grid with stacked cards using CSS `position: absolute` + `transform: translateY()` for the layered effect. Each column has up/down navigation buttons and a counter.

## R7: Backend View Changes

**Decision**: Modify `lot_detail_panel()` in `panels.py` to pass field-level override data (matching the `row.fields` dict structure from `build_lot_table_rows()`) to the unified modal template. The GET handler no longer needs the `?edit=1` branch for this feature — the form is always visible.

**Rationale**: The current modal detail view passes `rows` (label/initial/override tuples for a read-only table) and separate `lot_description`/`lot_notes` strings. The new template needs the same `fields` dict structure used by `lots_table_row.html` — `{field_name: {value, changed, original}}` — to render the inline form with override indicators. The existing `build_lot_table_rows()` helper already produces this structure; we can reuse it.

**Key changes**:
- GET handler builds `fields` dict (reusing logic from `build_lot_table_rows()`)
- Template receives `lot`, `fields`, `lot_description`, `lot_notes`
- POST handler unchanged (OverrideForm validation + OOB row update)
- `?edit=1` branch kept for backward compatibility but no longer linked from the new template

## R8: JavaScript Changes

**Decision**: Add gallery navigation JS for the new main-image + thumbnail layout in the modal. Add card stack navigation JS for the related lots section. Both are self-contained within the modal body's rendered HTML or event-delegated from shell.html.

**Rationale**: The current gallery uses horizontal scroll-snap. The new gallery (per mockup) uses a main image area with thumbnail clicks swapping the `src`. The card stack navigation needs up/down button handlers to cycle `data-pos` attributes. Both can use event delegation from the existing `htmx:afterSwap` handler pattern.

**Key changes**:
- Gallery: `selectThumb(el)` function updates main image `src` from clicked thumbnail
- Card stacks: Navigation buttons cycle `data-pos` on `.stack-card` elements within each column
- "Accept" button: Copies dimension values from card data attributes into the override form inputs

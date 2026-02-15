# Implementation Plan: Lots Modal Overhaul

**Branch**: `017-lots-modal-overhaul` | **Date**: 2026-02-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/017-lots-modal-overhaul/spec.md`

## Summary

Redesign the lot detail modal from a sequential read-only view into a two-column layout with image gallery (left), description + notes + inline override form (right), followed by a recommendation engine section (3 sizing cards) and a related lots gallery (3-column card stacks). The override form matches the lots table inline form fields exactly. Modal is centered both horizontally and vertically. Recommendation engine and related lots sections are placeholder UI for future backend integration.

## Technical Context

**Language/Version**: Python 3.14, Django 5
**Primary Dependencies**: HTMX 2.0.4 (CDN), ABConnectTools 0.2.1 (editable install)
**Storage**: No new storage — all data from ABConnect API; SQLite3 for sessions only
**Testing**: pytest with Django test client
**Target Platform**: Web (SPA shell with HTMX)
**Project Type**: Web application (Django monolith with HTMX partials)
**Performance Goals**: Modal content loads within existing page response time (no new API calls beyond current `get_lot()`)
**Constraints**: No new backend dependencies; recommendation + related lots sections are placeholder HTML only
**Scale/Scope**: Single modal template + CSS + JS changes; one view function update; 5 files modified

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Artifact Harmony | PASS | Spec, plan, contracts, data model, quickstart all created together |
| II. Executable Knowledge | PASS | Quickstart defines manual test procedures; contract tests planned |
| III. Contracted Boundaries | PASS | Endpoint contract documented in `contracts/lot-detail-panel.md` |
| IV. Versioned Traceability | PASS | Feature branch `017-lots-modal-overhaul` created from main |
| V. Communicable Truth | PASS | Quickstart.md documents how to run and verify the feature |
| Governance: Complexity | PASS | No new abstractions, patterns, or dependencies |

### Post-Design Gate

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Artifact Harmony | PASS | Template, CSS, JS, view, and tests all change together |
| II. Executable Knowledge | PASS | Each acceptance scenario maps to a testable manual or automated check |
| III. Contracted Boundaries | PASS | `lot_detail_panel` endpoint contract specifies new context shape |
| IV. Versioned Traceability | PASS | All changes on feature branch with descriptive commits |
| V. Communicable Truth | PASS | Quickstart covers all P1/P2/P3 verification steps |
| Governance: Complexity | PASS | Reuses existing `build_lot_table_rows()` field structure; no new patterns |

## Project Structure

### Documentation (this feature)

```text
specs/017-lots-modal-overhaul/
├── spec.md                  # Feature specification
├── plan.md                  # This file
├── research.md              # Phase 0: research decisions
├── data-model.md            # Phase 1: data model (no new entities)
├── quickstart.md            # Phase 1: manual testing guide
├── contracts/
│   └── lot-detail-panel.md  # Phase 1: endpoint contract
└── checklists/
    └── requirements.md      # Spec quality checklist
```

### Source Code (repository root)

```text
src/
├── catalog/
│   ├── views/
│   │   └── panels.py                          # MODIFY: lot_detail_panel() GET context
│   ├── templates/catalog/
│   │   ├── shell.html                         # MODIFY: add modal JS for gallery, stacks, accept
│   │   └── partials/
│   │       └── lot_detail_modal.html          # REWRITE: new two-column hero + sections
│   └── static/catalog/
│       └── styles.css                         # MODIFY: add hero grid, override form, card styles
tests/
├── contract/
│   └── test_panels.py                         # MODIFY: update lot detail panel tests
```

**Structure Decision**: Existing Django monolith structure. All changes are within the `catalog` app — no new files, no new apps, no new directories.

## Implementation Approach

### Phase 1: Backend View Update (panels.py)

**Goal**: Update `lot_detail_panel()` GET handler to pass the `fields` dict (same structure as `lots_table_row.html`) instead of the read-only `rows` list.

**Changes to `lot_detail_panel()` in `panels.py`**:

1. Extract the field-building logic from `build_lot_table_rows()` into a reusable helper or call `build_lot_table_rows()` directly and use the first result's `fields` dict.
2. Replace the GET response context:
   - Remove: `rows`, `has_override`
   - Add: `fields` (dict of `{field_name: {value, changed, original}}`)
   - Keep: `lot`, `lot_description`, `lot_notes`
3. POST handler: No changes needed (OverrideForm validation + OOB row update already works).
4. Keep `?edit=1` branch for backward compatibility (will serve the old template if someone hits it directly).

**Existing code to reuse**: `build_lot_table_rows()` at `panels.py:43-74` already builds the exact `fields` dict needed. Call it with `[lot]` and extract `result[0].fields` or factor out the field-comparison logic.

### Phase 2: Modal Template Rewrite (lot_detail_modal.html)

**Goal**: Replace the entire template with the new two-column hero layout + recommendation section + related lots section.

**Template structure**:

```
<div data-lot-title="Lot {{ lot.catalogs.0.lot_number }}">

  <!-- HERO: Gallery + Info + Override Form -->
  <div class="lot-hero">
    <div class="lot-gallery">
      <div class="lot-gallery-main"><img id="modal-main-img" ...></div>
      <div class="lot-gallery-thumbs">{% for img %}...{% endfor %}</div>
    </div>
    <div class="lot-info">
      <div class="lot-desc-title">{{ lot_description }}</div>
      <div class="lot-desc-notes">{{ lot_notes }}</div>
      <form class="override-row" hx-post="..." hx-target="#lot-modal-body">
        {% csrf_token %}
        <div class="lot-dims">
          <!-- Qty, L, W, H, Wgt inputs with initial refs -->
          <!-- CPack dropdown -->
        </div>
        <div class="override-controls">
          <!-- Force Crate, Do Not Tip checkboxes -->
          <!-- Save button -->
        </div>
      </form>
    </div>
  </div>

  <!-- RECOMMENDATION ENGINE (placeholder) -->
  <div class="section">
    <h3>Box Sizing & Pack Options <span class="placeholder-badge">Quoter Pending</span></h3>
    <div class="quoter-grid">
      <!-- 3 cards: Minimum, Recommended, Oversize -->
    </div>
  </div>

  <!-- RELATED LOTS (placeholder) -->
  <div class="section">
    <h3>Related Lots <span class="future-badge">Similarity Matching</span></h3>
    <div class="stacks-grid">
      <!-- 3 columns: Q25, Q50, Q75 with card stacks -->
    </div>
  </div>

</div>
```

**Override form fields** (matching `lots_table_row.html` exactly):
- `qty` — number input
- `l`, `w`, `h` — number inputs with `step="any"`
- `wgt` — number input with `step="any"`
- `cpack` — select dropdown (—, NF, LF, F, VF, PBO)
- `force_crate` — checkbox
- `do_not_tip` — checkbox

Each dimension input shows the initial (parsed) value below it as a reference. Changed values get `initial-changed` class (amber text). The `lot-input-overridden` class marks fields where override differs from initial.

**HTMX configuration for the form**:
- `hx-post="/panels/lots/{{ lot.id }}/detail/"`
- `hx-target="#lot-modal-body"`
- `hx-swap="innerHTML"`
- `hx-headers='{"X-CSRFToken":"{{ csrf_token }}"}'`

### Phase 3: CSS Additions (styles.css)

**Goal**: Add styles for the new modal layout sections.

**New CSS classes** (adapted from `m6-full-composite.html` mockup):

1. **Hero grid**: `.lot-hero` — `grid-template-columns: 45% 1fr` with `@media` fallback to `1fr`
2. **Gallery**: `.lot-gallery-main` (centered main image), thumbs (reuse existing)
3. **Info section**: `.lot-info` (flex column with padding)
4. **Override form**: `.override-row` (form row with dims and controls)
5. **Dims layout**: Reuse existing `.lot-dims`, `.lot-dims-field`, `.lot-dims-label` classes from lots table
6. **Initial refs**: `.initial-ref` (tiny text below inputs showing parsed values)
7. **Modal width**: Update `dialog#lot-modal` max-width from 700px to 840px
8. **Section dividers**: `.section` (padding + border-top)
9. **Quoter cards**: `.quoter-grid`, `.quoter-card`, `.quoter-card.recommended`
10. **Card stacks**: `.stacks-grid`, `.card-stack`, `.stack-card[data-pos]` with transforms
11. **Badges**: `.placeholder-badge`, `.future-badge`
12. **Stack navigation**: `.stack-nav`, `.stack-nav-btn`, `.stack-counter`

### Phase 4: JavaScript Updates (shell.html)

**Goal**: Add event-delegated handlers for the new modal components.

**New JS functions**:

1. **Gallery thumbnail click** — Update main image `src` and active thumbnail state
   ```js
   // Event delegated on modal body
   // Click .lot-gallery-thumb → update #modal-main-img src
   ```

2. **Card stack navigation** — Cycle `data-pos` attributes on stack cards
   ```js
   // Click .stack-nav-btn[data-dir="up"|"down"] within .stack-column
   // Update data-pos on sibling .stack-card elements
   // Update .stack-counter text
   ```

3. **Accept button** — Copy related lot values into override form
   ```js
   // Click .stack-card-accept within .stack-card
   // Read data-l, data-w, data-h, data-wgt, data-cpack from card
   // Write values into modal form inputs
   ```

All handlers use event delegation from `document.body` to handle dynamically loaded modal content (same pattern as existing auto-save listeners).

### Phase 5: Tests

**Goal**: Update contract tests for the modified endpoint context.

**Test cases**:
1. `test_lot_detail_panel_returns_fields_context` — Verify GET response contains `fields` dict with expected structure
2. `test_lot_detail_panel_fields_show_override_diff` — Verify `changed` flag is True when override differs from initial
3. `test_lot_detail_panel_post_saves_override` — Existing test (verify still passes)
4. `test_lot_detail_panel_description_notes_context` — Verify `lot_description` and `lot_notes` passed correctly

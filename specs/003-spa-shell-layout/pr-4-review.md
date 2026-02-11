# PR #4 Review — SPA Shell Layout

## Scope
Review target: commit `4bde7d1` (`Add three-panel SPA shell layout with HTMX navigation`).

Primary references:
- `specs/003-spa-shell-layout/spec.md`
- `specs/003-spa-shell-layout/plan.md`
- Runtime implementation under `src/catalog/`
- Contract tests under `tests/contract/test_panels.py`

---

## Spec Adherence Review (FR-by-FR)

### ✅ Fully honored
- **FR-001** (three-panel shell on home): Implemented via `catalog/shell.html` with `panel-left1`, `panel-left2`, `panel-main` regions and wired route `/` in `seller_list`.
- **FR-002 / FR-003** (HTMX panel loading): Seller and event row interactions correctly use `hx-get` and panel targets for incremental updates.
- **FR-005** (clear downstream panel): Seller→events response includes out-of-band (`hx-swap-oob`) reset of lots panel.
- **FR-006 / FR-012** (logo + preserved top nav controls): Navbar retains logo, search, import link, dropzone, and user controls.
- **FR-007 / FR-008 / FR-009 / FR-013** (scrolling, pagination, empty states, fragment endpoints): Implemented with panel CSS, shared panel pagination partial, placeholder empty states, and dedicated fragment endpoints.
- **FR-011** (preserve existing deep links): Lot cards use normal href links to existing lot detail route; full-page routes remain intact.

### ⚠️ Partially honored / gaps
- **FR-004** (selected seller/event highlighting):
  - Templates rely on `selected_seller_id` and `selected_event_id` for `.active` state.
  - `sellers_panel` does not pass `selected_seller_id`, and `seller_events_panel` does not pass `selected_event_id`.
  - Result: highlight behavior is structurally prepared but not functionally wired for persisted selected state.

- **FR-010** (loading indicator while HTMX request in-flight):
  - Left2/Main include `.htmx-indicator` markup in shell.
  - Left1 content updates (pagination via `/panels/sellers/`) have no in-panel indicator tied to panel-content swaps.
  - Indicator support is therefore inconsistent across panel interactions.

---

## Project Harmony & Flywheel Assessment

### What is working well
- **Artifact harmony is strong**: spec, plan, contracts, tasks, implementation, and tests all landed in one change set and map to the same feature objective.
- **Low-complexity posture maintained**: no JS framework adoption, no new persistence, and no dependency sprawl.
- **Contract-first discipline preserved**: dedicated fragment endpoints are covered by contract tests and align with planned boundaries.

### Flywheel impact
This PR improves the product flywheel in three ways:
1. **Operator efficiency**: seller→event→lots navigation now reduces context switching.
2. **Visual baseline**: introduces a reusable panel component system and style language for future FRs.
3. **Delivery velocity**: partial endpoints + reusable panel pagination create extension points for future filters and state handling.

Risk to flywheel momentum: unresolved selection-state wiring (FR-004) weakens perceived responsiveness and trust in active context.

---

## Technology Debt Identified

1. **Selection state is not server-propagated consistently**
   - Current templates support active classes, but views do not provide selected IDs needed to render them.
   - Debt category: UX correctness / interaction state.

2. **HTMX loading affordance is not uniformly applied**
   - Left panel updates can occur without visible in-flight indicator.
   - Debt category: UX consistency / perceived performance.

3. **Unvalidated query parsing for panel endpoints**
   - `page` and `page_size` are parsed via raw `int()` without defensive handling.
   - Bad query strings can raise `ValueError` and return 500.
   - Debt category: robustness / defensive input handling.

4. **Contract tests are present but environment bootstrap is brittle**
   - Local test execution currently errors when ABConnect package is unavailable.
   - Debt category: test portability / CI-local parity.

---

## Prioritized Next FRs (Recommended)

### FR Priority 1 — Complete selection-state UX (close FR-004)
**Why first:** Active context is essential for trust and rapid navigation in multi-panel UIs.

Recommended acceptance additions:
- Persist selected seller in Left1 after loading events.
- Persist selected event in Left2 after loading lots.
- Ensure selected classes survive panel pagination transitions.

### FR Priority 2 — Normalize panel loading/error ergonomics (close FR-010 parity)
**Why second:** Consistent feedback patterns improve perceived speed and reduce operator uncertainty.

Recommended acceptance additions:
- Add visible loading indicators for Left1 requests.
- Unify indicator behavior for all panel swaps and retry actions.
- Add error-state retry telemetry hooks (or minimal logging conventions).

### FR Priority 3 — URL-addressable shell state (seller/event/page)
**Why third:** Enables shareable links, better back/forward behavior, and improved external-customer readiness.

Recommended acceptance additions:
- Querystring synchronization (`?seller=<id>&event=<id>&...`) with progressive enhancement.
- Hydrate shell from URL on initial page load.
- Preserve pagination state per panel when practical.

### FR Priority 4 — Mobile/narrow viewport interaction model
**Why fourth:** Edge-case already identified in spec; currently no explicit responsive panel-navigation behavior is documented in implementation.

Recommended acceptance additions:
- Stacked/switchable panel mode under 768px.
- Explicit keyboard and focus management for accessibility.

---

## Suggested Definition-of-Done Addendum for Follow-up PRs
- Every FR with “selected/active state” language must include a contract test that asserts the active CSS class in returned fragment HTML.
- Every panel endpoint must reject invalid pagination params gracefully (HTTP 400 or clamped defaults).
- Every HTMX targetable panel must expose consistent loading and error affordances.

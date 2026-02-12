# PR #5 Review — Shell Interaction Polish

## Scope
Review target: commit `a4768f1` (`Add shell interaction polish: selection state, URL sync, loading indicators, mobile layout`).

Primary references:
- `specs/004-shell-interaction-polish/spec.md`
- `specs/004-shell-interaction-polish/plan.md`
- `specs/004-shell-interaction-polish/tasks.md`
- Runtime implementation under `src/catalog/`
- Contract tests under `tests/contract/test_panels.py`

---

## Executive Assessment

**Overall:** PR #5 delivers substantial progress on all four prioritized stories from PR #4 and keeps product direction coherent.

**Flywheel harmony status:** **Partially honored**.
- **Honored at planning/execution level**: spec → tasks → implementation → tests are strongly aligned and traceable.
- **Not fully honored at runtime level**: several interaction-path regressions/edge-case gaps reduce reliability of the shell “speed + confidence” loop, especially under hydration and mobile transitions.

---

## Spec Adherence Review (Story-by-Story)

### User Story 1 — Active Selection Highlighting (P1)

#### ✅ Delivered
- Sellers panel now accepts `selected` and applies `selected_seller_id` in template rendering.
- Seller click path re-renders seller list OOB with the active class retained.
- Event click path re-renders events list OOB with active event class retained.
- Contract coverage exists for selected-class behavior in both seller and event flows.

#### ⚠️ Gaps / risks
1. **Cross-entity validation gap in hydration path**
   - `/?seller=X&event=Y` hydrates lots for event `Y` without validating that event `Y` belongs to seller `X`.
   - This can produce a mismatch where seller highlight and lots content represent different entities.

2. **Selection persistence is coupled to OOB payload correctness**
   - Active-state continuity depends on OOB payloads carrying complete pagination context and stable endpoint URLs.
   - This is brittle where URL/pagination context is currently incomplete (see US3 issues).

---

### User Story 2 — Consistent Loading Indicators (P2)

#### ✅ Delivered
- `.htmx-indicator` markup is now present in all three shell panels.
- CSS provides spinner and dimmed-content styles.
- Contract test asserts indicator presence in all three panels.

#### ⚠️ Gaps / risks
1. **Potential trigger mismatch between HTMX request class and indicator DOM placement**
   - Current CSS expects `.htmx-request .htmx-indicator`, but requesting elements are nested items/links while indicators are panel-level siblings.
   - Without explicit `hx-indicator` wiring or request-class propagation to panel containers, indicators may not appear consistently during in-flight swaps.

2. **Error-state parity not fully tested**
   - Spec called for retry/error behavior consistency; current tests focus on static presence, not runtime indicator clear/reset behavior after failures.

---

### User Story 3 — URL-Addressable Shell State (P3)

#### ✅ Delivered
- `seller_events_panel` sets `HX-Push-Url` to `/?seller=<id>`.
- `event_lots_panel` sets `HX-Push-Url` to `/?seller=<sid>&event=<eid>` when seller is resolvable.
- Home shell reads `seller`/`event` params and conditionally hydrates events/lots.
- Contract tests exist for push headers and hydration behavior.

#### ❌ Material issues
1. **Hydrated panel pagination URLs are empty (`pagination_url=""`)**
   - Hydrated include of `events_panel.html` uses blank `pagination_url`, causing pagination links to become `?page=N` rather than panel fragment endpoints.
   - Hydrated include of `lots_panel.html` has the same issue.

2. **OOB events refresh after event click also uses blank `pagination_url`**
   - OOB include in `lots_panel.html` hardcodes `pagination_url=""`.
   - Result: after selecting an event, events-panel pagination routes to the wrong endpoint format.

3. **Root handler parses `page`/`page_size` before shell-path branch**
   - `seller_list` does raw `int(...)` parsing up-front.
   - On `/`, malformed `page` or `page_size` can still throw before shell render logic, which is inconsistent with the “silently ignore invalid params” posture used elsewhere.

---

### User Story 4 — Mobile/Narrow Viewport Layout (P4)

#### ✅ Delivered
- `data-mobile-panel` and `data-panel` attributes added.
- Mobile back button and ARIA live region added.
- Mobile CSS switches to one-panel-at-a-time display under `767px`.
- JS handles panel switching on HTMX swaps and back-button navigation.
- Contract test verifies required shell attributes/elements exist.

#### ⚠️ Gaps / risks
1. **Desktop resize does not fully reset mobile panel state**
   - Resize handler hides back button but does not restore `data-mobile-panel="sellers"`.
   - Returning from desktop to mobile can reopen in prior subpanel (events/lots), which conflicts with predictable “start at sellers” behavior.

2. **Behavioral contract gap**
   - Tests verify markup presence, not interactive semantics (panel progression, back stack behavior, focus management) under real viewport transitions.

---

## Flywheel Harmony Assessment

### What is working well
- **Spec-to-code traceability is excellent**: this PR clearly implements the exact backlog generated by PR #4 review.
- **Delivery mechanism is coherent**: endpoint contracts, template OOB strategy, and shell-level interaction model are aligned.
- **Test intent is feature-centered**: contract tests were expanded to encode new promises around selection, push-url, hydration, mobile markup, and parsing safety.

### Where harmony breaks
- **Operator confidence loop is not fully closed** due to pagination URL regressions in hydrated/OOB contexts.
- **Perceived responsiveness loop is uncertain** because indicator runtime coupling may not reliably fire.
- **Context integrity loop is vulnerable** when seller/event query params can hydrate mismatched entities.

**Conclusion:** Flywheel harmony is **directionally honored, but not yet production-grade honored**.

---

## Technical Debt & Issue Register

### P0 / High
1. **Broken pagination endpoints in hydrated and OOB panel includes**
   - `pagination_url=""` appears in hydrated shell includes and OOB events include.
   - Impact: panel pagination can call the wrong URL shape and break fragment navigation.

2. **Hydration context consistency not enforced (`seller` vs `event`)**
   - Missing verification that selected event belongs to selected seller.
   - Impact: inconsistent UI state and misleading operator context.

### P1 / Medium
3. **Indicator activation coupling may not match HTMX request class placement**
   - CSS selector relies on DOM relationship that may not hold for all triggers.
   - Impact: inconsistent loading feedback, especially on nested trigger elements.

4. **Root view defensive parsing inconsistency**
   - `/` path still performs unsafe int parsing for generic pagination params before shell branch.
   - Impact: avoidable 500s for malformed query strings.

5. **Mobile state reset logic is incomplete**
   - Back button visibility resets; panel state does not.
   - Impact: confusing re-entry behavior after viewport changes.

### P2 / Low
6. **Behavioral tests do not validate interactive runtime semantics**
   - Most new tests are structural/contract-level HTML assertions.
   - Impact: regressions in focus handling, panel transitions, and indicator runtime could slip through.

---

## Logical Next Steps (Prioritized)

### Next PR #1 — Fix URL/pagination correctness in all hydrated/OOB panel paths
- Pass concrete `pagination_url` values everywhere partials are rendered (`shell.html` hydration includes and `lots_panel.html` OOB include).
- Add contract tests asserting generated pagination links point to panel fragment endpoints after:
  1. initial hydration
  2. event click OOB refresh

### Next PR #2 — Harden shell hydration integrity
- Validate `event` belongs to `seller` when both query params are present.
- If mismatch, either:
  - ignore event and hydrate seller-only state, or
  - normalize URL and state to a consistent canonical pair.
- Add explicit tests for mismatch handling.

### Next PR #3 — Make loading indicators runtime-reliable
- Use explicit `hx-indicator` attributes (or equivalent class strategy) per panel trigger so spinner binding is deterministic.
- Add integration/UI tests that assert indicator visibility during request lifecycle.

### Next PR #4 — Complete defensive query parsing and mobile-state polish
- Move/guard all int parsing in root shell path to non-throwing helpers.
- On resize-to-desktop, also reset mobile panel state to sellers for predictable re-entry.
- Add viewport-transition behavior tests (Playwright or equivalent).

---

## Definition-of-Done Addendum (Recommended)

For follow-up shell PRs, require:
1. **Every partial render path** (normal, OOB, hydration include) must preserve valid endpoint URLs for pagination actions.
2. **Every URL-hydration pair** (`seller`, `event`) must be consistency-validated.
3. **Every indicator promise** must be validated in runtime (not markup-only) tests.
4. **Every responsive interaction promise** must include at least one viewport behavior test, not only static HTML assertions.

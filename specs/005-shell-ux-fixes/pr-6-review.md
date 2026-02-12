# PR #6 Review — Shell UX Fixes Follow-up

## Scope
Reviewed current branch head `f6445da` with focus on lots-by-event correctness in shell flows.

## Executive Summary
The PR improves URL semantics, indicators, and hydration behavior, but the core lots-per-event reliability issue appears **not fully fixed**.

### Primary Concern (High)
`event_lots_panel` still fetches lots through `services.list_lots_by_catalog(..., customer_catalog_id=...)`, even though this PR's own spec/contract/tasks explicitly require using the expanded catalog payload (`event.lots`) because the lots list endpoint is unreliable for event scoping.

This mismatch is likely the root cause of operators seeing incorrect/missing lots when selecting events.

---

## Findings

### 1) Lots panel still uses the unreliable lots list endpoint
- In `event_lots_panel`, the code path is:
  1. `event = services.get_catalog(request, event_id)`
  2. `result = services.list_lots_by_catalog(request, event.customer_catalog_id, ...)`
- This directly contradicts the requirement to use embedded catalog lots (`event.lots`) with local pagination.
- If backend filtering by `customer_catalog_id` is weak/inconsistent, lots can appear incomplete, stale, or cross-event.

**Impact:** High, user-facing data trust issue.

### 2) Hydration path repeats the same risky lots query
- In `/` shell hydration (`seller_list`), when both `seller` and `event` are present and validated, lots are again fetched by `services.list_lots_by_catalog(..., event.customer_catalog_id, ...)`.
- So deep-linked URLs can reproduce the same incorrect lots behavior as interactive clicks.

**Impact:** High, bug remains in both live panel flow and deep-link flow.

### 3) Test coverage appears misaligned with stated acceptance criteria
- Current contract tests assert that `event_lots_panel` calls `list_lots_by_catalog` with a given catalog ID.
- But the spec and tasks say the implementation should **stop using** that endpoint and instead page `event.lots`.
- This means tests are currently locking in the old behavior rather than guarding the intended fix.

**Impact:** Medium-High; prevents catching the real regression.

---

## Spec/Task Alignment Check
- **Spec FR-204 / AC-8:** lots panel must use expanded catalog response (`event.lots`).
- **Task T014:** explicitly says to switch `event_lots_panel` to embedded lots + local pagination.
- **Implementation:** still calls `list_lots_by_catalog`.

Result: **Not aligned** on the most critical data-correctness requirement.

---

## Recommended Fix (next patch)
1. In `event_lots_panel`, derive lots from `event.lots` and build local pagination metadata.
2. In root hydration (`seller_list`), use the same embedded-lots strategy after `get_catalog`.
3. Update tests to assert:
   - `list_lots_by_catalog` is **not** called for lots panel rendering.
   - lots shown are exactly from `event.lots`.
   - empty embedded lots produce "No lots in this event".
4. Keep URL/push behavior unchanged.

---

## Verdict
I would request changes before merge on data correctness grounds. The lot-loading implementation still follows the path identified as unreliable, which is the likely cause of "loading lots per event" not working correctly.

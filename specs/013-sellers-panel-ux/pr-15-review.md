# PR #15 Review: Sellers Panel UX

## Findings

1. **High**: Mixed-type sort key can raise a runtime `TypeError` when an event has no start date.
   - File: `src/catalog/views/panels.py:167`
   - Code currently sorts with `key=lambda e: e.start_date or ""`.
   - If `start_date` is a `datetime/date` (normal API shape) for some events and `None` for others, keys become a mix of `datetime/date` and `str`, which is not comparable in Python 3 and can 500 the panel request.
   - Example: `sorted([datetime(...), None], key=lambda d: d or "", reverse=True)` raises `TypeError`.
   - Recommended fix: normalize keys to a single type (for example, tuple-based key with explicit null handling) before sorting.

2. **Medium**: Seller filter form can now trigger native form submit on Enter, causing a full-page navigation path.
   - File: `src/catalog/templates/catalog/partials/seller_list_panel.html:2`
   - `hx-get` was removed from `<form>` and moved to `<input>`, but the form submit path is not prevented.
   - This creates a non-HTMX fallback submit on Enter that can bypass the intended debounced UX and cause an unexpected full reload.
   - Recommended fix: prevent native submit (`onsubmit`/`hx-on:submit`) or keep the form HTMX-controlled while still debouncing on the input.

3. **Medium**: Events are sorted only within the already-paginated page, not globally.
   - Files: `src/catalog/views/panels.py:156`, `src/catalog/views/panels.py:167`
   - The code paginates via `services.list_catalogs(... page=..., page_size=...)` first, then sorts `result.items`.
   - This does not guarantee FR-011 (“most recent first”) across the full result set when backend ordering differs from desired ordering.
   - Recommended fix: request server-side sort if supported by the API, or sort before pagination.

## Residual Risks / Test Gaps

1. New events-sort tests use string dates only; there is no contract test covering `datetime/date` + `None` values.
2. No test covers pressing Enter in the seller filter input to ensure no full-page submit regression.
3. Existing suite still has one unrelated pre-existing failure in shell hydration (`tests/contract/test_panels.py::TestShellHydrationContract::test_shell_with_invalid_seller_param_renders_default`).

## Verification

- `pytest -q tests/contract/test_panels.py -k 'RealtimeFilterContract or EventsSortContract'` -> `5 passed`
- `pytest -q tests/contract/test_panels.py` -> `59 passed, 1 failed` (the existing unrelated shell hydration failure noted above)

## Verdict

Request changes before merge.

# PR #16 Review: Lots Skeleton UX

## Findings

1. **Medium**: PR requirements are not covered by automated tests.
   - Files: `src/catalog/templates/catalog/shell.html`, `src/catalog/views/panels.py`
   - This PR adds new runtime behavior for lots skeleton injection and OOB event sorting, but there are no corresponding test additions.
   - `git diff main...HEAD` contains no `tests/...` changes, so regressions in trigger behavior and sort stability are not guarded.

2. **Medium**: Lots-skeleton trigger condition is broader than the contract and may over-fire as the panel evolves.
   - File: `src/catalog/templates/catalog/shell.html:288`
   - Contract intent is to trigger on event item clicks (`.panel-item`) in left2, but implementation currently matches any requester inside `#panel-left2` when target is `#panel-main-content`.
   - This is correct for current markup, but permissive enough to accidentally apply skeleton behavior to future left2 controls that target main.

## Residual Risks / Test Gaps

1. No contract test verifies lots skeleton injection on event click (`htmx:beforeRequest` path) and replacement by response content.
2. No regression test verifies seller click still shows main empty state and never lots skeleton.
3. No test verifies event-list order remains stable after event click OOB refresh in `event_lots_panel`.

## Verification

- `pytest -q tests/contract/test_panels.py` -> `59 passed, 1 failed` (existing unrelated shell hydration test failure due to live API lookup path).
- `pytest -q tests/unit/test_authorization.py tests/unit/test_login_bridge.py tests/integration/test_middleware_auth.py` -> `37 passed`.

## Verdict

Approve with follow-up: add targeted contract tests for lots skeleton trigger behavior and OOB event sort stability.

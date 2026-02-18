# Specification Analysis Report: Import Hardening (020)

**Date**: 2026-02-17
**Artifacts analyzed**: spec.md, plan.md, tasks.md, constitution.md

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | HIGH | tasks.md T014 (Phase 2), T030 (Phase 4) | FR-015 (deep-link redirect) is split across two phases — T014 already modifies `upload_catalog` redirect for merge path, T030 re-modifies it for both paths. Risk of merge conflict or partial overwrite. | Consolidate: move new-catalog redirect logic entirely to T030 and limit T014 to only adding `recovery_url` + passing `seller_display_id`/`customer_catalog_id` through the return dict. Or move all redirect logic to T014 and remove T030's redirect portion. |
| C1 | Coverage Gap | HIGH | spec.md FR-023, tasks.md T001 | Events panel cache fix (T001/FR-023) has no corresponding test task. plan.md notes `test_cache.py` as "no changes expected", but the fix changes cache semantics (store all events, filter at return). | Add a unit test task (e.g., T001b) in `tests/unit/test_cache.py` to verify `list_catalogs` returns all events when `future_only=False` and only future events when `future_only=True` on cache hit. |
| C2 | Coverage Gap | MEDIUM | spec.md FR-022, tasks.md T034-T035 | Cpack indicator fix (T034, T035) has no test task. Two template files are modified but no contract or integration test verifies the `<span class="initial-ref">` renders correctly. | Add a test (integration or template render test) that asserts `initial-changed` class appears when cpack is overridden. Could be combined with existing lots table tests. |
| I2 | Inconsistency | MEDIUM | tasks.md T018, T027 | Two different toast-passing mechanisms: T018 uses server-side `request.session['pending_toast']` for search redirects, T027 uses client-side `sessionStorage` for upload redirects. Dual mechanisms increase complexity. | Document this as intentional: server-side session for server-initiated redirects (search view), client-side sessionStorage for JS-initiated redirects (dropzone). Add a brief comment in both task descriptions clarifying why each mechanism is used. |
| U1 | Underspecification | MEDIUM | tasks.md T036 | "Debug and fix inline save persistence" — root cause unknown per research R8. No acceptance criterion beyond "fix whatever is found". Task may produce no code change if the bug isn't reproducible. | Accept as investigative task. Add a fallback acceptance criterion: "If root cause is not found, document investigation findings in a comment and mark FR-020 as deferred." |
| D1 | Duplication | LOW | spec.md FR-015, FR-016 | FR-015 (deep-link redirect after import) and FR-016 (toast visible on destination) overlap in scope — both describe post-upload navigation behavior. They are distinct but coupled. | No action needed — they test different aspects (URL vs toast). Current separation is fine for traceability. |
| I3 | Inconsistency | LOW | spec.md, data-model.md, tasks.md | Terminology "event" (user-facing) vs "customer_catalog_id" (code) vs "catalog_id" (internal). Consistent within each context but could confuse spec readers. | No action needed — this is existing project convention. The spec correctly uses "event" in user-facing language and technical identifiers in requirements. |
| U2 | Underspecification | LOW | spec.md Edge Cases | "Search returns the first match" when item belongs to multiple catalogs — no specification of which catalog is "first" (by ID? by date? by API order?). | Accept API ordering (first result from `lots.list`). Add a note: "first match = first result returned by the API, typically most recent catalog." |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 cache-failed-payloads | Yes | T006, T007 | |
| FR-002 recovery-page-listing | Yes | T009, T010 | |
| FR-003 check-server-state | Yes | T009, T012 | |
| FR-004 retry-failed-lot | Yes | T009, T011 | |
| FR-005 detect-existing-lot | Yes | T009, T011 | |
| FR-006 cache-namespace-ttl | Yes | T006 | |
| FR-007 recovery-link-response | Yes | T014 | |
| FR-008 search-input-navbar | Yes | T020 | |
| FR-009 resolve-item-id | Yes | T017 | |
| FR-010 redirect-deep-link | Yes | T018 | |
| FR-011 not-found-toast | Yes | T018 | |
| FR-012 item-param-selects-lot | Yes | T021, T022 | |
| FR-013 compute-correct-page | Yes | T021 | |
| FR-014 active-highlight-style | Yes | T022, T023 | |
| FR-015 deep-link-redirect | Yes | T014, T030 | Split across phases (see I1) |
| FR-016 toast-persistence | Yes | T027 | |
| FR-017 100pct-failure-detection | Yes | T028 | |
| FR-018 file-size-limit | Yes | T029 | |
| FR-019 dropzone-animation | Yes | T031 | |
| FR-020 inline-save-persistence | Yes | T036 | Investigative (see U1) |
| FR-021 dnt-persistence | Yes | T037 | UAT verification only |
| FR-022 cpack-indicator | Yes | T034, T035 | No test task (see C2) |
| FR-023 events-panel-no-regression | Yes | T001 | No test task (see C1) |
| FR-024 remove-dead-code | Yes | T003 | |
| FR-025 100pct-failure-reraise | Yes | T002 | |
| FR-026 css-reformat | Yes | T004 | |
| FR-027 extract-mock-fixture | Yes | T005 | |

## Constitution Alignment

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Artifact Harmony | PASS | All artifact types present and synchronized |
| II. Executable Knowledge | PASS | Tests included for all user stories (minor gaps C1/C2 are MEDIUM not CRITICAL) |
| III. Contracted Boundaries | PASS | contracts/api.yaml defines all new endpoints before implementation |
| IV. Versioned Traceability | PASS | Feature branch with full artifact set |
| V. Communicable Truth | PASS | quickstart.md covers all 4 user stories |

**Unmapped Tasks:** None. All 38 tasks map to at least one requirement.

## Metrics

| Metric | Value |
|--------|-------|
| Total Requirements | 27 |
| Total Tasks | 38 |
| Coverage % | 100% (27/27 requirements have >=1 task) |
| Ambiguity Count | 2 (U1, U2) |
| Duplication Count | 1 (D1) |
| Critical Issues | 0 |
| High Issues | 2 (I1, C1) |
| Medium Issues | 3 (C2, I2, U1) |
| Low Issues | 3 (D1, I3, U2) |

## Next Actions

No CRITICAL issues. Two HIGH issues are addressable with minor edits:

1. **I1** — Clarify the split of FR-015 between T014 and T030 to avoid merge conflicts in `imports.py`. Recommend consolidating redirect logic in T030 and limiting T014 to recovery_url only.
2. **C1** — Add a test for the `list_catalogs` cache fix (T001). This is the most impactful foundational change and should have test coverage per Principle II.

**Recommendation**: These issues are minor enough to address during implementation rather than requiring a spec/tasks rewrite. Proceed to `/speckit.implement`.

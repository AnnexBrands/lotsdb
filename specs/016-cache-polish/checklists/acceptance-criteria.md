# Acceptance Criteria Checklist: Cache Polish

**Purpose**: Validate acceptance criteria quality — completeness, clarity, measurability, and scenario coverage across all 6 user stories
**Created**: 2026-02-14
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [ ] CHK001 - Are acceptance scenarios defined for both cache-hit AND cache-miss paths in every user story that involves caching? [Completeness, Spec §US1, §US6]
- [ ] CHK002 - Is the data subset served from cache explicitly defined — cache holds future-only events for fast display; the fresh server fetch returns ALL events (past + future) and replaces the panel? [Clarity, Gap — SPEC+IMPL MISMATCH: current spec/code filters future-only on both paths]
- [ ] CHK003 - Are acceptance criteria defined for the cache-write path (what gets stored and when) or only the cache-read path? [Completeness, Spec §US1]
- [ ] CHK004 - Is there an acceptance scenario for the SWR transition moment — user sees future-only events from cache, then ALL events (past + future) from server replace the panel and hydrate cache? [Completeness, Spec §US6 — CLARIFIED: fresh fetch must return all events, not just future]
- [ ] CHK005 - Are acceptance criteria defined for null start_date events in the cached path, or only mentioned as an edge case without testable criteria? [Completeness, Spec §Edge Cases]
- [ ] CHK006 - Does US5 (skeleton rows) specify both events panel AND lots table skeleton counts, or only one? [Completeness, Spec §US5]

## Requirement Clarity

- [ ] CHK007 - Is "sufficient type fidelity" in FR-001 quantified — does the spec state the exact type (datetime) or only describe the visual outcome? [Clarity, Spec §FR-001]
- [ ] CHK008 - Is "sensible default" in FR-003 defined with the specific default value and port, or left ambiguous? [Clarity, Spec §FR-003]
- [ ] CHK009 - Is "seamlessly replace" in FR-009 defined — does it mean no visible flicker, no scroll position change, no UI flash? [Ambiguity, Spec §FR-009]
- [ ] CHK010 - Is "instantly" in SC-006 quantified with a specific threshold (e.g., <100ms), or is the "under 100ms" metric the sole definition? [Clarity, Spec §SC-006]
- [ ] CHK011 - Is "identical pagination metadata" in FR-002 defined — same field names, same types, same edge-case behavior at page boundaries? [Clarity, Spec §FR-002]
- [ ] CHK012 - Is "no error shown to the user" in FR-010 clear — does cached content stay as-is, or is any indication of the failure allowed (e.g., subtle icon, console log)? [Ambiguity, Spec §FR-010]

## Scenario Coverage

- [ ] CHK013 - Are acceptance scenarios defined for a seller whose cache contains zero future events (empty list, not cache miss)? [Coverage, Gap]
- [ ] CHK014 - Are acceptance scenarios defined for concurrent SWR refreshes (user clicks same seller rapidly)? [Coverage, Gap]
- [ ] CHK015 - Are acceptance scenarios defined for the filter-active path in SWR — does the spec state that filters bypass cache and skip the auto-refresh trigger? [Coverage, Spec §US6]
- [ ] CHK016 - Are acceptance scenarios defined for pagination interaction with SWR — if the user is on page 2 when the fresh response arrives, which page is displayed? [Coverage, Gap]
- [ ] CHK017 - Is the relationship between US1 (date fidelity) and US6 (SWR) explicitly addressed — does the SWR cache-read path also parse dates correctly? [Coverage, Spec §US1 + §US6]
- [ ] CHK018 - Are acceptance scenarios defined for what happens when the fresh fetch returns identical data to the cache — is a swap still performed? [Coverage, Gap]

## Acceptance Criteria Measurability

- [ ] CHK019 - Can "event dates display identically" in SC-001 be objectively measured — is the expected format specified (e.g., "M j, Y")? [Measurability, Spec §SC-001]
- [ ] CHK020 - Can "correct page slices and metadata" in SC-002 be verified without implementation knowledge — are the exact metadata fields listed? [Measurability, Spec §SC-002]
- [ ] CHK021 - Can "within one deployment cycle" in SC-003 be measured — is "deployment cycle" defined? [Measurability, Spec §SC-003]
- [ ] CHK022 - Can "fills the visible panel area" in SC-005 be verified — is it tied to a specific row count (15) or to viewport height? [Measurability, Spec §SC-005]
- [ ] CHK023 - Can "within the normal server response time" in SC-007 be measured — is a threshold defined or is it intentionally relative? [Measurability, Spec §SC-007]

## Consistency

- [ ] CHK024 - Do the cache-read parsing steps in the view layer (panels.py SWR path) and service layer (services.py cache-hit path) describe the same transformation, or could they diverge? [Consistency, Spec §US1 + §US6]
- [ ] CHK025 - Are the OOB swap requirements consistent between initial load and SWR fresh responses — does the spec define which OOB elements are included/excluded for each? [Consistency, Spec §US6]
- [ ] CHK026 - Is the skeleton behavior consistent between events panel and lots table — both 15 rows, both suppressed during SWR? [Consistency, Spec §US5 + §US6]

## Edge Case Coverage

- [ ] CHK027 - Is the behavior specified when Redis becomes unavailable mid-session — does the SWR path degrade to normal (non-cached) behavior? [Edge Case, Spec §FR-005]
- [ ] CHK028 - Is the behavior specified when cache TTL expires between the cache-hit render and the fresh fetch — is this a normal expected scenario? [Edge Case, Gap]
- [ ] CHK029 - Is the behavior specified for the URL bar state during SWR — does `HX-Push-Url` fire only on the initial cached render, not on the fresh swap? [Edge Case, Spec §US6]
- [ ] CHK030 - Are requirements defined for browser back/forward navigation interacting with SWR-populated panels? [Edge Case, Gap]

## Notes

- **CHK002 + CHK004 CLARIFIED**: Expected SWR behavior is: (1) cache stores **future-only** events for instant display; (2) async server fetch retrieves **ALL events** (past + future); (3) fresh response replaces panel with full event list and updates cache. This is a **spec + implementation gap** — current code filters future-only on both paths (`list_catalogs()` always applies `start_date >= today`). Fixing this requires:
  - Spec update: US6 acceptance scenarios, FR-008 to specify "all events" on fresh path
  - Code update: fresh fetch path in `services.py` must skip the future-date filter
  - Cache update: fresh fetch should hydrate cache with the full event list (or keep future-only cache for next instant load — decision needed)
- CHK016 (pagination + SWR interaction) is a real gap — the current implementation always swaps innerHTML regardless of pagination state.
- Items reference spec.md sections using §US[n] for user stories, §FR-[n] for functional requirements, §SC-[n] for success criteria.

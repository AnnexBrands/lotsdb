---
description: "Run UAT protocol to validate artifact harmony before merge. (v0.1 stub)"
handoffs:
  - label: Return to Stabilization
    agent: speckit.implement
    prompt: "UAT found issues — address the FIX items from the UAT report."
  - label: Close Cycle
    agent: speckit.overview
    prompt: "UAT passed. Check cycle status."
---

<!-- STUB: v0.1 — MVP. Most steps require human judgment.
     Automation is best-effort (test scanning, path validation).
     Iterate on this skill as the team's UAT patterns stabilize. -->

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Execute the UAT (User Acceptance Testing) protocol defined in FEATURE_CYCLE.md
Section 12. Walk through each of the 6 UAT steps, presenting findings for
user review, collecting per-step verdicts (PASS/FAIL) with optional comments,
and producing a final SHIP or FIX verdict persisted in `uat-report.md`.

This command writes a single artifact (`uat-report.md`) and is otherwise
**non-destructive** to spec/plan/tasks/code files.

**Stub notice**: This is v0.1. Automated checks (test execution, doc path
validation) are best-effort. Manual verification steps are presented for
human judgment. Iterate on automation coverage as patterns stabilize.

## Operating Constraints

- **Single artifact output**: Only writes/overwrites `FEATURE_DIR/uat-report.md`
- **Non-destructive**: Does NOT modify spec.md, plan.md, tasks.md, or code files
- **Interactive**: Requires user input at each step for verdict
- **Idempotent**: Re-running overwrites the previous uat-report.md (prior comments are loaded first for re-check)

## Execution Steps

### 1. Setup

1a. Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

1b. Derive paths:

- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md
- QUICKSTART = FEATURE_DIR/quickstart.md
- CONTRACTS = FEATURE_DIR/contracts/
- DATA_MODEL = FEATURE_DIR/data-model.md
- UAT_REPORT = FEATURE_DIR/uat-report.md

Abort with an error message if SPEC, PLAN, or TASKS is missing (instruct the user which prior step to run).

1c. **Check for prior UAT report**:

- If `uat-report.md` exists in FEATURE_DIR, read it and extract per-step verdicts and comments from the prior run.
- Parse by finding `## Step N` headings, then extracting `**Verdict**:` and `**Comment**:` values under each.
- Store prior FAIL verdicts + comments keyed by step number.
- Present a summary: "Prior UAT report found with N FAIL item(s) from previous run. These will be re-checked during this UAT pass."

1d. **Verify PR status**:

```bash
gh pr list --head <branch-name> --state open --json number,title,reviewDecision
```

- If a PR exists with `reviewDecision = APPROVED`: proceed normally.
- If no approved PR: WARN "UAT typically runs after PR approval. Proceeding anyway, but consider completing review first."
- If `gh` is unavailable or not authenticated: report "PR status unavailable" and continue.

1e. **Load all artifacts** into working memory:

- Read spec.md — extract FRs, NFRs, user stories, edge cases
- Read plan.md — architecture, tech stack
- Read tasks.md — task completion status
- Read contracts/ (if exists) — API shapes
- Read data-model.md (if exists) — entities and relationships
- Read quickstart.md (if exists) — manual test steps and file paths

### 2. UAT Protocol — Step-by-Step Interactive Walkthrough

Present each of the 6 steps sequentially. For each step:

1. Display the step name and purpose
2. Show automated findings (tables, counts)
3. If prior FAIL comments exist for this step, display them under **"Prior findings to re-check:"**
4. Prompt the user for verdict: **PASS** or **FAIL**, with optional comment
5. Wait for user response before proceeding to the next step
6. Record verdict + comment

**User response format** — flexible:

- `PASS` or `FAIL` — plain verdict
- `FAIL - missing contract for FR-003` — verdict with comment
- `PASS, looks good` — verdict with comment
- If ambiguous (no clear PASS/FAIL), ask: "Please confirm: is that a PASS or FAIL for this step?"

---

#### Step 1 — Specs & Contracts

**Purpose**: Verify understanding and cross-reference alignment across spec, contracts, and data model.

**Automated analysis**:

- List all FRs from spec.md (count and IDs if available)
- List all contracts in contracts/ directory (or note "no contracts/ directory")
- List all entities from data-model.md (or note "no data-model.md")
- Cross-reference: for each FR, check if a corresponding contract or data model entity exists (keyword/reference matching — best-effort)
- Report any FRs with no apparent contract or data model coverage

Present findings as:

```markdown
| FR / Requirement | Contract Coverage | Data Model Support | Status |
|-----------------|-------------------|-------------------|--------|
| FR-001: ...     | contract-x.md     | Entity Y          | Covered |
| FR-003: ...     | —                 | —                 | Gap    |
```

Prompt: **"Step 1 — Specs & Contracts: Do you confirm understanding and cross-reference alignment? (PASS/FAIL) [optional comment]"**

---

#### Step 2 — Derive Expected Tests

**Purpose**: For each requirement, derive what a test SHOULD verify.

**Automated analysis**:

- For each FR in spec.md, derive a one-line description of what a test should verify
- For each contract endpoint (if contracts/ exists), list expected request/response test cases
- For each edge case in spec.md, identify expected test scenario

Present findings as:

```markdown
| Source | ID | Expected Test Description |
|--------|-----|--------------------------|
| FR     | FR-001 | Verify catalog loads with correct seller filter |
| Contract | POST /lots | Verify 400 on invalid payload |
| Edge Case | Empty list | Verify empty state renders correctly |
```

Prompt: **"Step 2 — Expected Test Coverage: Are the derived expected tests reasonable and complete? (PASS/FAIL) [optional comment]"**

---

#### Step 3 — Compare Expected vs Actual Tests

**Purpose**: Identify gaps between expected and actual test coverage.

**Automated analysis**:

- Scan test files: find files matching `tests/**/*.py`, `test_*.py`, `*_test.py` patterns in the repository
- For each expected test from Step 2, attempt to find a matching actual test (keyword/function-name matching — best-effort)
- Report gaps: expected tests with no apparent actual test
- Report orphans: actual tests not mapped to any FR (informational only)

Present findings as:

```markdown
| Expected Test | Actual Test File:Function | Match | Gap? |
|--------------|--------------------------|-------|------|
| FR-001 catalog load | tests/test_panels.py:test_catalog_load | High | No |
| Edge: empty state   | —                                      | None | Yes |
```

If gaps found, note: "Gaps found — if these are critical, consider returning to stabilization before proceeding."

Prompt: **"Step 3 — Test Coverage Comparison: Are coverage gaps acceptable? (PASS/FAIL) [optional comment]"**

---

#### Step 4 — Run Tests

**Purpose**: Execute automated tests and linting.

**Automated execution**:

- Run `pytest` from the project (per CLAUDE.md conventions: `cd src && python -m pytest ../tests/ -v` or equivalent)
- Capture exit code, pass/fail/skip counts
- Run `ruff check .` from `src/`
- Capture exit code, error count

Present results as:

```markdown
| Check | Result | Details |
|-------|--------|---------|
| pytest | PASS/FAIL | N passed, M failed, K skipped |
| ruff check | PASS/FAIL | N errors found |
```

If any tests fail or lint errors exist, strongly suggest FAIL — but the user has final say.
If any tests are skipped, list them for justification review.

Prompt: **"Step 4 — Test Execution: All tests and linting passing? (PASS/FAIL) [optional comment]"**

---

#### Step 5 — Documentation Review

**Purpose**: Validate that quickstart.md and other docs are accurate.

**Automated analysis**:

- If quickstart.md exists:
  - Extract all file paths mentioned in quickstart.md (patterns like `src/...`, `tests/...`, `specs/...`)
  - Check each path exists in the repository
  - Count manual test steps (numbered items)
  - Report missing/invalid paths
- If quickstart.md does not exist: note its absence
- Spot-check terminology: extract 5-10 key terms from spec.md, check presence in quickstart.md (best-effort)

Present results as:

```markdown
| Doc Check | Status | Details |
|-----------|--------|---------|
| quickstart.md exists | YES/NO | |
| File paths valid | N/M valid | [list invalid paths] |
| Manual steps present | N steps | |
| Key terms consistent | best-effort | [any mismatches] |
```

Prompt: **"Step 5 — Documentation Review: Are docs accurate and reproducible? (PASS/FAIL) [optional comment]"**

---

#### Step 6 — Final Verdict

**Purpose**: Aggregate step results and render final decision.

Present a summary table of all step verdicts collected so far:

```markdown
| Step | Verdict | Comment |
|------|---------|---------|
| 1. Specs & Contracts | PASS/FAIL | ... |
| 2. Expected Tests | PASS/FAIL | ... |
| 3. Test Comparison | PASS/FAIL | ... |
| 4. Run Tests | PASS/FAIL | ... |
| 5. Docs Review | PASS/FAIL | ... |
```

Decision guidance:
- If ALL steps are PASS: Recommend **SHIP**
- If ANY step is FAIL: Recommend **FIX**

Prompt: **"Final Verdict: Based on the above, your verdict is: SHIP (proceed to merge/deploy) or FIX (return to stabilization)? [optional overall comment]"**

---

### 3. Generate UAT Report

After collecting all verdicts:

1. Load the template structure from `.specify/templates/uat-report-template.md`
2. Fill in all placeholders:
   - Feature name (from branch name)
   - Branch name
   - Current date
   - Per-step verdicts, comments, and findings
   - Prior comments re-checked (from step 1c)
   - Final verdict and overall comment
3. Write to `FEATURE_DIR/uat-report.md` (overwrites any prior report)

### 4. Report Completion

Output a completion summary:

```markdown
## UAT Complete

**Report**: [absolute path to uat-report.md]
**Final Verdict**: **SHIP** / **FIX**
**Steps**: N/6 PASS

[If FIX]:
Failing steps:
- Step N: [comment]
- Step M: [comment]

Recommended: Address the above items, then re-run `/speckit.uat`.
Prior FAIL comments will be surfaced for re-check.

[If SHIP]:
All steps passed. Proceed to merge/deploy.
Run `/speckit.overview` to confirm cycle position.
```

## Reference

- UAT Protocol: FEATURE_CYCLE.md Section 11
- Template: `.specify/templates/uat-report-template.md`
- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh`

## Context

$ARGUMENTS

# Feature Cycle

**Version**: 3.0.0 | **Applies to**: Everard / lotsdb | **Last updated**: 2026-02-16

This document defines the full lifecycle of a feature from inception through
production. Every change — large or small — follows the same cycle. For small
changes the steps are brief; for complex features they are thorough. The cycle
also describes the between-cycle hygiene that keeps `main` clean.

Run `/speckit.overview` at any time to see where you are in the cycle.

---

## Cycle Overview

```mermaid
graph TD
    A["Between Cycles<br/><i>/speckit.overview</i>"]
    A --> B["Specify<br/><i>/speckit.specify</i>"]
    B --> C["Clarify<br/><i>/speckit.clarify</i>"]
    C --> D["Plan<br/><i>/speckit.plan</i>"]
    D --> E["Tasks<br/><i>/speckit.tasks</i>"]
    E --> F["Analyze<br/><i>/speckit.analyze</i>"]
    F -->|Issues| E
    F -->|Clean| G["Checklist<br/><i>/speckit.checklist</i>"]
    G --> H["Implement Phase<br/><i>/speckit.implement</i>"]
    H --> I["PR + Codex Review<br/><i>gh pr create</i>"]
    I --> J{"Stabilize"}
    J -->|Fix needed| H
    J -->|Stable| K["UAT<br/><i>/speckit.uat</i>"]
    K -->|Fails| J
    K -->|"More phases"| H
    K -->|"All phases done"| TAG
    TAG["Tag & Deploy<br/><i>git tag, /deploy</i>"]
    TAG --> A
```

---

## 1. Between Cycles — Clean Slate

Before starting any new feature, the repository must be in a known-good state.
Run `/speckit.overview` to check readiness.

**Checklist:**

- [ ] On `main` branch, working tree clean
- [ ] All feature branches merged via squash-merge and deleted (local + remote)
- [ ] `git fetch --prune` run; no stale remote refs
- [ ] All specs in `specs/` reflect delivered state (no lingering `[ ]` tasks)
- [ ] `CLAUDE.md` auto-generated section is current (run update-agent-context if needed)
- [ ] Tag the release point: `git tag vN.N.N`

> **Suggested tooling:** Consider creating a `/speckit.housekeep` skill that:
> prunes merged remote branches, validates all `tasks.md` files are complete,
> tags the release, and updates `CLAUDE.md`.

---

### 2. Specify — Define the Feature

| | |
|---|---|
| **Skill** | `/speckit.specify <feature description>` |
| **Input** | Natural language feature description |
| **Output** | `specs/NNN-feature-name/spec.md`, feature branch, quality checklist |
| **References** | [Constitution &sect;III Contracted Boundaries], [Spec Template] |

Creates the feature branch (`NNN-feature-name`), generates the specification,
runs quality validation, and surfaces up to 3 clarification questions.

The spec is the **source of truth for intent**. It must be stakeholder-readable,
technology-agnostic, and testable.

---

### 3. Clarify — Reduce Ambiguity

| | |
|---|---|
| **Skill** | `/speckit.clarify` |
| **Input** | Active feature branch with `spec.md` |
| **Output** | Updated `spec.md` with clarifications integrated |
| **References** | [Constitution &sect;I Artifact Harmony], [Constitution &sect;III Contracted Boundaries] |

Interactive sequential questioning (max 5) targeting the highest-impact
ambiguities. Each accepted answer is integrated inline into the spec
immediately. Skip if the spec emerged clean from `/speckit.specify`.

---

### 4. Plan — Design the Solution

| | |
|---|---|
| **Skill** | `/speckit.plan` |
| **Input** | Clarified `spec.md` |
| **Output** | `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md` |
| **References** | [Constitution &sect;II Executable Knowledge], [Constitution &sect;III Contracted Boundaries], [Plan Template] |

Generates the full technical design: architecture, data model, API contracts,
and research decisions. Contracts are defined **before** implementation begins
(Constitution &sect;III). The agent context file (`CLAUDE.md`) is updated with
new technologies.

---

### 5. Tasks — Break Down the Work

| | |
|---|---|
| **Skill** | `/speckit.tasks` |
| **Input** | `plan.md` + `spec.md` + design artifacts |
| **Output** | `tasks.md` — dependency-ordered, user-story-organized task list |
| **References** | [Constitution &sect;IV Versioned Traceability], [Tasks Template] |

Every task gets a checkbox, sequential ID, story label, parallel marker, and
file path. Phases: Setup, Foundational, User Stories (priority order), Polish.

---

### 6. Analyze — Cross-Artifact Consistency Check

| | |
|---|---|
| **Skill** | `/speckit.analyze` |
| **Input** | `spec.md` + `plan.md` + `tasks.md` |
| **Output** | Read-only analysis report (no file modifications) |
| **References** | [Constitution &sect;I Artifact Harmony], [Constitution — all principles] |

Detects duplications, ambiguities, coverage gaps, terminology drift, and
constitution violations across the three core artifacts. Severity levels:
CRITICAL / HIGH / MEDIUM / LOW.

If CRITICAL issues exist, loop back to `/speckit.tasks` or `/speckit.plan` to
resolve before proceeding.

---

### 7. Checklist — Domain-Specific Quality Gates

| | |
|---|---|
| **Skill** | `/speckit.checklist <domain>` |
| **Input** | Feature context + domain focus (ux, api, security, etc.) |
| **Output** | `specs/NNN-feature-name/checklists/<domain>.md` |
| **References** | [Constitution &sect;II Executable Knowledge], [Checklist Template] |

Checklists are **unit tests for requirements** — they validate the quality of
the spec, not the implementation. Generate as many domain checklists as needed
before implementation begins.

---

### 8. Implement — Execute the Plan

| | |
|---|---|
| **Skill** | `/speckit.implement` |
| **Input** | Complete `tasks.md` + all design artifacts |
| **Output** | Working code, tests passing, tasks marked `[X]` |
| **References** | [Constitution &sect;I Artifact Harmony], [Constitution &sect;II Executable Knowledge] |

Phase-by-phase execution following the task plan. TDD approach when tests are
specified. Checklist completion is validated before starting. Each completed
task is marked off in `tasks.md`.

#### Multi-Phase Implementation

For large features, implementation can be split across multiple phases. Each
phase implements a subset of tasks from `tasks.md` (e.g., Phase 1 = US1 + US2,
Phase 2 = US3 + US4).

Each phase:

1. Implements its subset of tasks
2. Creates its own PR (see Section 9)
3. Goes through Codex review and stabilization (Section 10)
4. Passes UAT (Section 11)
5. Gets squash-merged into `main`
6. Next phase begins back at this step (Implement)

All phases share the same feature branch, spec artifacts, and final tag.
The feature is not "done" until all phases have merged.

---

### 9. PR + Codex Review — External Stabilization

| | |
|---|---|
| **Tool** | `gh pr create`, then Codex agent review |
| **Input** | Feature branch with phase implementation complete |
| **Output** | Pull request with structured review |
| **References** | [Constitution — PR Review Protocol], [Constitution &sect;IV Versioned Traceability] |

After `/speckit.implement` completes a phase:

1. **Create the PR** using `gh pr create` with a summary referencing the spec.
   For multi-phase features, include the phase in the title:
   `Feature NNN: phase M of N — <description>`
2. **Codex reviews the PR** against the PR Review Protocol (Constitution &sect;PR Review Protocol):
   - Step 0: Locate artifacts in `specs/NNN-feature-name/`
   - Step 1: Spec ↔ Code (every FR has code, no undocumented behavior)
   - Step 2: Contract ↔ Code (schemas match)
   - Step 3: Tests ↔ Spec (acceptance scenarios covered)
   - Step 4: Docs ↔ Code (quickstart paths accurate)
   - Step 5: Tasks ↔ Completion (all tasks `[X]` for this phase)
   - Step 6: Cross-artifact consistency
3. **Codex produces a verdict**: APPROVE / REQUEST CHANGES / APPROVE WITH NOTES

> **Suggested tooling:** Consider creating a `/speckit.review` skill that
> automates the PR Review Protocol as a structured checklist, producing a
> formatted review comment.

---

### 10. Stabilization & Hardening Loop

```mermaid
graph LR
    PR["PR Created"] --> CR["Codex Review"]
    CR -->|REQUEST CHANGES| FIX["Fix Issues"]
    FIX --> PUSH["Push Fixes"]
    PUSH --> CR
    CR -->|APPROVE| UAT["Proceed to UAT"]
```

This is an iterative loop between implementation and review:

1. **Codex identifies issues** via PR Review Protocol
2. **Fixes are applied** (back to `/speckit.implement` or manual edits)
3. **Push and re-review** until APPROVE verdict
4. **Regression check**: run full test suite after each fix round

The loop exits only when Codex produces APPROVE or APPROVE WITH NOTES (with
all notes acknowledged).

> **Suggested tooling:** Consider a `/speckit.stabilize` skill that:
> reads the latest PR review comments, extracts actionable findings, creates
> fix tasks in `tasks.md`, executes fixes, and pushes — automating the
> fix-push-review cycle.

---

### 11. UAT — Enforce Harmony

User Acceptance Testing validates that all artifacts are in harmony before
merging. This is the constitution's prime directive (Principle I) made
operational.

#### UAT Protocol: The Harmony Enforcement Pipeline

```mermaid
graph TD
    S1["1. Specs & Contracts<br/><i>Read and understand</i>"]
    S2["2. Derive Expected Tests<br/><i>What SHOULD tests verify?</i>"]
    S3["3. Compare to Actual Tests<br/><i>Would gaps reveal issues?</i>"]
    S4["4. Run Tests<br/><i>All pass?</i>"]
    S5["5. Docs Review<br/><i>Sphinx / quickstart accurate?</i>"]
    S6["6. Verdict<br/><i>SHIP or FIX</i>"]

    S1 --> S2
    S2 --> S3
    S3 -->|Gaps found| FAIL["Back to Stabilize"]
    S3 -->|Coverage OK| S4
    S4 -->|Failures| FAIL
    S4 -->|All green| S5
    S5 -->|Inaccurate| FAIL
    S5 -->|Accurate| S6
```

#### After UAT Passes

- **More phases remaining?** Loop back to Section 8 (Implement) for the next phase
- **All phases done?** Proceed to Section 12 (Deploy)

#### UAT Template

For each feature (or phase), complete this checklist before merging:

**Step 1 — Understand Specs & Contracts**
- [ ] Read `spec.md` — all FRs understood
- [ ] Read `contracts/` — all API shapes understood
- [ ] Read `data-model.md` — all entities and relationships understood
- [ ] Cross-reference: contracts implement spec FRs, data model supports contracts

**Step 2 — Derive Expected Test Coverage**
- [ ] For each FR, list what a test SHOULD verify
- [ ] For each contract endpoint, list expected request/response test cases
- [ ] For each edge case in spec, identify expected test scenario
- [ ] Document any gap between "what should be tested" and "what is tested"

**Step 3 — Evaluate Actual Tests Against Expectations**
- [ ] Every FR has at least one corresponding test
- [ ] Every contract has at least one contract test
- [ ] Edge cases from spec have test coverage
- [ ] Tests assert behavior (not just "runs without error")
- [ ] Any coverage gaps are documented and justified

**Step 4 — Run Tests**
- [ ] `pytest` passes (zero failures)
- [ ] `ruff check .` passes (zero lint errors)
- [ ] No skipped tests without documented justification

**Step 5 — Documentation Review**
- [ ] `quickstart.md` file paths match actual project structure
- [ ] Manual test steps in quickstart are accurate and reproducible
- [ ] Sphinx docs (if present) build without warnings
- [ ] Terminology in docs matches spec and code

**Step 6 — Verdict**
- [ ] **SHIP**: All steps pass — proceed to deploy (or next phase)
- [ ] **FIX**: Issues found — return to Stabilization Loop (Section 10)

**Tooling:** Run `/speckit.uat` to execute this protocol interactively —
it automates findings, prompts for per-step verdicts, and persists results
in `uat-report.md`.

---

### 12. Deploy

| | |
|---|---|
| **Skill** | `/deploy` |
| **Input** | `main` branch, up to date with origin |
| **Output** | Production updated and service restarted |

Deploys by SSH into the production server, pulling latest `main`, and
restarting the service.

---

### 13. Close Cycle — Merge, Prune, Tag

After successful deploy, close the cycle. For multi-phase features, this
happens once after **all** phases have merged — not per-phase.

1. **Squash-merge** the feature branch into `main` (if not already done via PR)
2. **Delete** the feature branch locally and remotely:
   ```
   git branch -d NNN-feature-name
   git push origin --delete NNN-feature-name
   ```
3. **Prune** stale remote refs: `git fetch --prune`
4. **Tag** the release: `git tag vN.N.N` (one tag per feature, regardless of phase count)
5. **Verify** clean state: `git status` shows clean working tree on `main`
6. **Update agent context**: run `.specify/scripts/bash/update-agent-context.sh claude`

> **Suggested tooling:** The `/speckit.housekeep` skill suggested in
> Section 1 would handle this.

---

## Quick Reference: Skills & Tools by Phase

| Phase | Skill / Tool | Exists? |
|-------|-------------|---------|
| Overview (any time) | `/speckit.overview` | Yes |
| Between Cycles | — | No. See: `/speckit.housekeep` |
| Specify | `/speckit.specify` | Yes |
| Clarify | `/speckit.clarify` | Yes |
| Plan | `/speckit.plan` | Yes |
| Tasks | `/speckit.tasks` | Yes |
| Analyze | `/speckit.analyze` | Yes |
| Checklist | `/speckit.checklist` | Yes |
| Implement | `/speckit.implement` | Yes |
| PR Creation | `gh pr create` | Yes (CLI) |
| Codex Review | — | No. See: `/speckit.review` |
| Stabilization | — | No. See: `/speckit.stabilize` |
| UAT | `/speckit.uat` | Yes |
| Deploy | `/deploy` | Yes |
| Close Cycle | — | No. See: `/speckit.housekeep` |
| Tasks to Issues | `/speckit.taskstoissues` | Yes |
| Constitution | `/speckit.constitution` | Yes |

---

## Artifact References

| Artifact | Location | Authority |
|----------|----------|-----------|
| Constitution | `.specify/memory/constitution.md` | Governance — supersedes all other practices |
| Spec Template | `.specify/templates/spec-template.md` | Structure for all `spec.md` files |
| Plan Template | `.specify/templates/plan-template.md` | Structure for all `plan.md` files |
| Tasks Template | `.specify/templates/tasks-template.md` | Structure for all `tasks.md` files |
| Checklist Template | `.specify/templates/checklist-template.md` | Structure for all checklist files |
| Constitution Template | `.specify/templates/constitution-template.md` | Base template for constitution |
| PR Review Protocol | Constitution &sect;PR Review Protocol | 6-step review process |
| The Flywheel | Constitution &sect;The Flywheel | Artifact harmony reinforcement loop |

---

## Amendments

Changes to this cycle document follow the same governance as the constitution:

1. Documented rationale
2. Review approval
3. Version bump (this document follows semver independently)

When a new skill is created to fill a gap identified in this document, update
the Quick Reference table and remove the "Suggested tooling" note from the
relevant section.

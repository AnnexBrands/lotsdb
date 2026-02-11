<!--
  Sync Impact Report
  ==================
  Version change: 1.0.0 → 1.1.0 (MINOR)
  Modified principles: None
  Added sections:
    - PR Review Protocol (new section between The Flywheel and Governance)
  Removed sections: None
  Rationale: Governance stated "All PRs and reviews MUST verify compliance"
    but provided no actionable process. Reviewers had to re-derive the
    verification steps from abstract principles each time. This amendment
    adds a concrete, step-by-step protocol that a reviewer can follow
    independently using only the speckit artifacts in the feature branch.
  Templates requiring updates:
    ✅ plan-template.md — No update needed (protocol references specs/ artifacts generically)
    ✅ spec-template.md — No update needed
    ✅ tasks-template.md — No update needed
  Follow-up TODOs: None
-->

# Everard Constitution

## Core Principles

### I. Artifact Harmony (NON-NEGOTIABLE)

Specs/PRDs, examples, tests, docs, and code MUST evolve together.
Any change that alters behavior, APIs, data shape, or operator
expectations MUST update the full artifact set in the same changeset.

- No PR or commit may modify one artifact class without updating
  all affected counterparts.
- Drift between artifacts is treated as a defect.
- This is the prime directive — all other principles serve it.

### II. Executable Knowledge

Examples and tests MUST validate reality. Knowledge that cannot be
executed is not trusted.

- Examples MUST be runnable when technically feasible.
- Examples cover happy-path and key edge cases.
- Tests enforce behavioral contracts: contract tests for boundaries,
  integration tests for flows, unit tests for logic.
- If an example or test cannot reproduce the documented behavior,
  the artifact set is broken.

### III. Contracted Boundaries

Specs define boundaries and expectations. Every interface, API, data
shape, and operator-facing behavior MUST have a corresponding spec
or contract that declares what MUST be true.

- Specs are the source of truth for intent and expected behavior.
- Contracts (API schemas, data models, interface definitions) MUST
  exist before implementation begins.
- Changes to contracts MUST flow through spec amendments first.

### IV. Versioned Traceability

All changes MUST be reviewable and traceable. The evolution of every
artifact MUST be captured in version control.

- Every behavioral change MUST be tied to a reviewable changeset.
- Commit history MUST tell the story of why changes were made.
- Breaking changes MUST be explicitly documented and versioned.

### V. Communicable Truth

Docs MUST transfer intent and operational truth. Documentation is not
supplementary — it is a first-class artifact that enables others to
understand, use, and operate the system.

- Docs MUST explain how the system works, how to use it, and how
  to run it.
- Docs MUST be updated whenever the behavior they describe changes.
- Operational docs (runbooks, quickstarts) MUST be validated against
  the running system.

## Core Artifacts

These artifacts are first-class and MUST stay in sync:

| Artifact | Role | Contains |
|----------|------|----------|
| **PRD / Spec** | Intent + contract | What MUST be true, what users/operators expect |
| **Examples** | Canonical usage | Happy-path and key edge cases, runnable when possible |
| **Tests** | Verification | Contract, integration, and unit tests that enforce behavior |
| **Docs** | Explanation + operations | How it works, how to use it, how to run it |
| **Code** | Implementation | The machinery that MUST conform to the above |

## The Flywheel

The Artifact Harmony Flywheel describes how synchronized artifacts
reinforce each other and prevent drift:

1. **Spec drives examples** — Specs define what canonical usage looks like.
2. **Examples become test fixtures** — Canonical examples seed test data.
3. **Spec drives contract tests** — Declared boundaries become automated checks.
4. **Tests guard against drift** — Failing tests surface spec violations.
5. **Code updates require spec touch** — Implementation changes trigger spec review.
6. **Docs expose mismatches** — Writing operational docs reveals gaps between
   intent and reality.

The flywheel is self-sustaining: each artifact strengthens the next,
and any break in the chain surfaces as a visible failure.

## PR Review Protocol

Every PR that introduces or modifies a feature MUST be reviewed against
the speckit artifacts in the feature's `specs/###-feature-name/` directory.
A reviewer who has never seen the code should be able to complete this
protocol using only the PR diff and the artifacts.

### Step 0: Locate Artifacts

Identify the feature branch name (e.g., `002-catalog-dropzone`) and
confirm the following exist in `specs/<branch>/`:

| Artifact | File | Required? |
|----------|------|-----------|
| Specification | `spec.md` | YES |
| Plan | `plan.md` | YES |
| Tasks | `tasks.md` | YES |
| Contracts | `contracts/` | If feature has APIs/interfaces |
| Data Model | `data-model.md` | If feature has data entities |
| Research | `research.md` | No (informational) |
| Quickstart | `quickstart.md` | If feature has operational steps |
| Checklists | `checklists/` | If generated pre-implementation |

**BLOCK** if spec.md, plan.md, or tasks.md are missing.

### Step 1: Spec ↔ Code (Principle I + III)

Walk each functional requirement (FR-xxx) in `spec.md`:

- [ ] Every FR has corresponding code in the PR diff
- [ ] No code in the PR introduces behavior not described in a FR
- [ ] Spec status reflects current state (Draft → Implemented)
- [ ] Acceptance scenarios are all addressable by the implementation

**BLOCK** if any FR has no corresponding code, or if code introduces
undocumented behavior.

### Step 2: Contract ↔ Code (Principle III)

If `contracts/` exists, for each endpoint/interface defined:

- [ ] Request shape in code matches the contract schema
- [ ] Response shape in code matches the contract schema
- [ ] HTTP methods and status codes match
- [ ] Error responses match the contract's error schema

**BLOCK** if code deviates from a contract without a spec amendment.

### Step 3: Tests ↔ Spec (Principle II)

- [ ] Every acceptance scenario in spec.md has at least one test that
      exercises it (contract test, integration test, or unit test)
- [ ] Edge cases listed in spec.md are covered by tests
- [ ] All tests pass (`pytest` or equivalent)
- [ ] Tests actually assert the behavior described (not just "runs
      without error")

**BLOCK** if an acceptance scenario has zero test coverage. **WARN** if
edge cases lack coverage.

### Step 4: Docs ↔ Code (Principle V)

- [ ] `quickstart.md` file paths match actual file locations in the PR
- [ ] Manual test steps in quickstart.md are accurate for the
      implemented behavior
- [ ] Programmatic test commands in quickstart.md work when run
- [ ] Any referenced URLs, endpoints, or config match reality

**BLOCK** if docs reference files, paths, or behavior that don't exist.

### Step 5: Tasks ↔ Completion (Principle IV)

- [ ] All tasks in `tasks.md` are marked `[X]` (complete)
- [ ] No task is left `[ ]` without explanation
- [ ] Files listed in task descriptions exist in the PR diff

**WARN** if incomplete tasks exist. **BLOCK** if core tasks are skipped.

### Step 6: Cross-Artifact Consistency

- [ ] Terminology is consistent across spec, contracts, code, tests,
      and docs (same names for the same concepts)
- [ ] Data shapes in `data-model.md` match both contracts and code
- [ ] Plan's "Project Structure" section matches the actual files
      changed in the PR

**WARN** on terminology drift. **BLOCK** on structural contradictions.

### Verdict

| Result | Criteria |
|--------|----------|
| **APPROVE** | All steps pass with no BLOCKs and no unresolved WARNs |
| **REQUEST CHANGES** | One or more BLOCKs, or WARNs the author cannot justify |
| **APPROVE WITH NOTES** | No BLOCKs, WARNs exist but are acknowledged with rationale |

The reviewer MUST include which steps passed and which produced findings
in their review comment. A one-line "LGTM" does not satisfy this protocol.

## Governance

- This constitution supersedes all other development practices in this
  repository. When a conflict exists, the constitution wins.
- Amendments require: (1) documented rationale, (2) review approval,
  (3) migration plan for existing artifacts if principles change.
- All PRs and reviews MUST follow the PR Review Protocol above.
- Complexity MUST be justified — if a simpler approach satisfies the
  artifact harmony requirement, prefer it.
- Constitution versioning follows semantic versioning:
  - MAJOR: Principle removal or backward-incompatible redefinition.
  - MINOR: New principle or materially expanded guidance.
  - PATCH: Clarifications, wording, non-semantic refinements.

**Version**: 1.1.0 | **Ratified**: 2026-02-10 | **Last Amended**: 2026-02-11

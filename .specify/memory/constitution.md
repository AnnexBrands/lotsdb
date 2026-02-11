<!--
  Sync Impact Report
  ==================
  Version change: template → 1.0.0
  Modified principles: N/A (initial ratification)
  Added sections:
    - Core Principles (5 principles derived from Soul doctrine)
    - Core Artifacts (first-class artifact definitions)
    - The Flywheel (artifact reinforcement cycle)
    - Governance
  Removed sections: None
  Templates requiring updates:
    ✅ plan-template.md — Constitution Check section is generic; no update needed
    ✅ spec-template.md — User stories and requirements align with Contracted Boundaries; no update needed
    ✅ tasks-template.md — Phase structure supports incremental artifact delivery; no update needed
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

## Governance

- This constitution supersedes all other development practices in this
  repository. When a conflict exists, the constitution wins.
- Amendments require: (1) documented rationale, (2) review approval,
  (3) migration plan for existing artifacts if principles change.
- All PRs and reviews MUST verify compliance with these principles.
- Complexity MUST be justified — if a simpler approach satisfies the
  artifact harmony requirement, prefer it.
- Constitution versioning follows semantic versioning:
  - MAJOR: Principle removal or backward-incompatible redefinition.
  - MINOR: New principle or materially expanded guidance.
  - PATCH: Clarifications, wording, non-semantic refinements.

**Version**: 1.0.0 | **Ratified**: 2026-02-10 | **Last Amended**: 2026-02-10

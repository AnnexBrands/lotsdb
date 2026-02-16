---
description: Show current position in the feature cycle with artifact status, task progress, and recommended next step.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Provide a comprehensive diagnostic view of where you are in the feature cycle.
This command is **STRICTLY READ-ONLY** — it does not modify any files. It
produces a structured status report and recommends the next action.

Reference: `FEATURE_CYCLE.md` at repository root defines the full lifecycle.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Output a structured status
report only. No file writes, no git commits, no state changes.

## Execution Steps

### 1. Determine Context

Detect whether you are between cycles or working on a feature:

```bash
git rev-parse --abbrev-ref HEAD
```

- If branch matches `^[0-9]{3}-` → **Feature mode** (go to Step 3)
- If branch is `main` or any other non-feature name → **Between-cycles mode** (go to Step 2)

### 2. Between-Cycles Report

Gather the following data using git commands and file system inspection.
Do **NOT** call `check-prerequisites.sh` — it will fail on non-feature branches.

**2a. Repository hygiene:**

| Check | How to detect |
|-------|--------------|
| Working tree state | `git status --porcelain` — empty = clean |
| Stale remote branches | `git branch -r --merged main` — exclude `origin/main`, `origin/HEAD` |
| Unmerged remote branches | `git branch -r --no-merged main` — these are active work |
| Last tag | `git describe --tags --abbrev=0 2>/dev/null` — or "No tags yet" |
| Commits since tag | `git rev-list <tag>..HEAD --count` (if tag exists) |

**2b. Lingering specs:**

Scan each `specs/*/tasks.md` file. For each, count lines matching `- [ ]`
(incomplete tasks). Any feature with incomplete tasks is "lingering".

**2c. Produce the between-cycles report:**

```markdown
## Feature Cycle Overview — Between Cycles

**Branch**: main
**Working tree**: Clean | Dirty (N files modified)
**Last tag**: vN.N.N (M commits since) | No tags yet

### Repository Hygiene

| Check | Status | Details |
|-------|--------|---------|
| Working tree | PASS/FAIL | N modified files |
| Stale branches | PASS/WARN | List branches to prune |
| Lingering specs | PASS/WARN | N specs with incomplete tasks |

### Stale Branches to Prune
(list merged remote branches, or "None — all clean")

### Readiness
**[READY / NOT READY]** for next feature cycle.

### Recommended Next Steps
1. (context-dependent actions: prune, tag, then /speckit.specify)
```

**2d. Skip to Step 5** (output the report).

### 3. Feature Report — Gather Data

You are on a feature branch. Gather data in this order:

**3a. Get feature paths:**

```bash
.specify/scripts/bash/check-prerequisites.sh --json --paths-only
```

Parse JSON for `FEATURE_DIR`, `FEATURE_SPEC`, `IMPL_PLAN`, `TASKS`.

**3b. Artifact existence scan:**

Check which files exist in `FEATURE_DIR`:

| Artifact | Path | Check |
|----------|------|-------|
| spec.md | `FEATURE_SPEC` | file exists? |
| plan.md | `IMPL_PLAN` | file exists? |
| tasks.md | `TASKS` | file exists? |
| research.md | `FEATURE_DIR/research.md` | file exists? |
| data-model.md | `FEATURE_DIR/data-model.md` | file exists? |
| quickstart.md | `FEATURE_DIR/quickstart.md` | file exists? |
| contracts/ | `FEATURE_DIR/contracts/` | directory exists with files? |
| checklists/ | `FEATURE_DIR/checklists/` | directory exists with files? |

**3c. Task completion** (if `tasks.md` exists):

Count lines matching:
- `^- \[ \]` → incomplete tasks
- `^- \[[Xx]\]` → completed tasks
- Calculate percentage: `completed / (completed + incomplete) * 100`

Also parse per-phase breakdown by finding lines matching `^## Phase` or
`^### Phase` and counting tasks between each phase heading.

**3d. Checklist completion** (if `checklists/` exists):

For each `.md` file in `checklists/`:
- Count `- [ ]` (incomplete) and `- [X]` or `- [x]` (complete) lines
- Report per-checklist and aggregate status

**3e. PR status:**

```bash
gh pr list --head <branch-name> --state all --json number,title,state,url,reviewDecision
```

If `gh` is not available or not authenticated, report "PR status unavailable"
and continue. Do not fail.

**3f. Detect Fast-Forward vs Full Cycle mode:**

- If `spec.md` does NOT exist AND the branch has commits beyond `main`:
  → Likely **Fast-Forward mode**
- If `spec.md` exists → **Full Cycle mode**
- If no commits beyond `main` and no spec.md → **Just started** (mode undetermined)

### 4. Feature Report — Detect Phase and Next Step

Use this decision tree to determine the current phase:

```
if spec.md does not exist:
    if branch has commits beyond main:
        PHASE = "Fast-Forward: PR pending"
        NEXT  = "Push and run: gh pr create"
    else:
        PHASE = "Specify"
        NEXT  = "/speckit.specify <description>"

elif plan.md does not exist:
    # Check if spec has [NEEDS CLARIFICATION] markers
    if spec contains "[NEEDS CLARIFICATION":
        PHASE = "Clarify"
        NEXT  = "/speckit.clarify"
    else:
        PHASE = "Plan"
        NEXT  = "/speckit.plan"

elif tasks.md does not exist:
    PHASE = "Tasks"
    NEXT  = "/speckit.tasks"

elif task completion = 0%:
    if no checklists/ directory:
        PHASE = "Analyze"
        NEXT  = "/speckit.analyze"
    elif checklists exist but are incomplete:
        PHASE = "Checklist"
        NEXT  = "Complete checklists, then /speckit.implement"
    else:
        PHASE = "Implement"
        NEXT  = "/speckit.implement"

elif task completion > 0% and < 100%:
    PHASE = "Implement (in progress)"
    NEXT  = "/speckit.implement (continue)"

elif task completion = 100%:
    if no PR exists for this branch:
        PHASE = "PR Creation"
        NEXT  = "gh pr create"
    elif PR exists with reviewDecision = CHANGES_REQUESTED:
        PHASE = "Stabilization"
        NEXT  = "Address review feedback, push fixes"
    elif PR exists with reviewDecision = APPROVED:
        PHASE = "UAT"
        NEXT  = "Run UAT protocol (FEATURE_CYCLE.md Section 12)"
    elif PR state = MERGED:
        # Check if more tasks remain for multi-phase
        PHASE = "Close Cycle"
        NEXT  = "Delete branch, prune, tag (FEATURE_CYCLE.md Section 14)"
    else:
        PHASE = "Awaiting Review"
        NEXT  = "Wait for Codex review on PR"
```

Map the detected phase to the FEATURE_CYCLE.md section number for reference.

### 5. Produce Formatted Report

**For feature branches, use this format:**

```markdown
## Feature Cycle Overview — [BRANCH_NAME]

**Branch**: NNN-feature-name
**Feature dir**: specs/NNN-feature-name/
**Mode**: Full Cycle | Fast-Forward
**Current phase**: [Phase Name]
**Cycle reference**: FEATURE_CYCLE.md Section N

### Artifact Status

| Artifact | Status |
|----------|--------|
| spec.md | Present / Missing |
| plan.md | Present / Missing |
| tasks.md | Present — N/M complete (P%) / Missing |
| research.md | Present / Missing |
| data-model.md | Present / Missing |
| quickstart.md | Present / Missing |
| contracts/ | Present (N files) / Missing |
| checklists/ | Present (N files) / Missing |

### Task Progress
(only if tasks.md exists)

**Overall**: N/M tasks (P%)

| Phase | Done / Total | Status |
|-------|-------------|--------|
| Phase 1: Setup | 2/2 | Complete |
| Phase 3: US1 | 3/4 | In Progress |
| ... | ... | ... |

### Checklist Status
(only if checklists/ exists)

| Checklist | Done / Total | Status |
|-----------|-------------|--------|
| requirements.md | 8/8 | PASS |
| ux.md | 5/7 | INCOMPLETE |

### Pull Requests
(only if gh available)

| PR | Title | State | Review |
|----|-------|-------|--------|
| #20 | Feature 019: phase 1 | merged | approved |
| #21 | Feature 019: phase 2 | open | pending |

(or: No PRs found for this branch.)

### Next Step

**Recommended**: [skill or action]
**Cycle reference**: FEATURE_CYCLE.md Section N
```

## Phase Detection Reference

| Phase | Indicators | Next Skill | Cycle Section |
|-------|-----------|------------|---------------|
| Between Cycles | On main, no feature branch | `/speckit.specify` | 1 |
| Specify | Feature branch, no spec.md, no commits | `/speckit.specify` | 3 |
| FF: PR pending | Feature branch, no spec.md, has commits | `gh pr create` | 2 |
| Clarify | spec.md with NEEDS CLARIFICATION | `/speckit.clarify` | 4 |
| Plan | spec.md exists, no plan.md | `/speckit.plan` | 5 |
| Tasks | plan.md exists, no tasks.md | `/speckit.tasks` | 6 |
| Analyze | tasks.md at 0%, no checklists | `/speckit.analyze` | 7 |
| Checklist | Post-analyze, pre-implement | `/speckit.checklist` | 8 |
| Implement | tasks 0-99% complete | `/speckit.implement` | 9 |
| PR Creation | tasks 100%, no PR | `gh pr create` | 10 |
| Stabilization | PR open, changes requested | Fix + push | 11 |
| UAT | PR approved | UAT protocol | 12 |
| Close Cycle | PR merged | Prune + tag | 14 |

## Context

$ARGUMENTS

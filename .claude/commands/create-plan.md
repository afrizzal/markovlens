---
description: Create a detailed implementation plan in docs/planning/
argument-hint: <feature description>
---

# Create Plan: $ARGUMENTS

Create a detailed implementation plan for the requested feature/change.

**Note:** For substantive phase-level work, prefer `/gsd:plan-phase N` instead. Use this command for ad-hoc plans that don't fit the GSD phase structure.

## Plan Document Structure

Create file at `docs/planning/plans/<short-name>-plan.md`:

```markdown
# Plan: <Feature Name>

**Date:** <YYYY-MM-DD>
**Author:** Claude (via Opus brainstorm)
**Status:** Draft / Approved / In Progress / Done

## Context

<Why is this needed? What problem does it solve?>

## Goal

<One-line outcome statement>

## Non-Goals

<What this explicitly does NOT include>

## Approach

<Chosen approach with rationale>

### Architecture

<Component diagram or text description>

### Data Flow

<Step-by-step what happens>

## Tasks

- [ ] Task 1 (file: `path/to/file.py`)
- [ ] Task 2 (file: `path/to/other.py`)
- [ ] Task 3 (tests)
- [ ] Task 4 (docs update)

## Acceptance Criteria

- [ ] Criterion 1 (testable)
- [ ] Criterion 2
- [ ] All tests pass
- [ ] Docs updated (README/manual-book/CLAUDE.md as applicable)

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| ... | Low/Med/High | Low/Med/High | ... |

## Alternatives Considered

1. **Approach A** — rejected because X
2. **Approach B** — rejected because Y

## Estimate

<Hours or days — be honest>

## References

- [Link to related docs/issues/papers]
```

## Steps

1. Confirm understanding of the request with the user (1 clarifying question max if needed)
2. Read relevant existing code (don't assume — Read tool first)
3. Draft the plan document
4. Save to `docs/planning/plans/<short-name>-plan.md`
5. Update `docs/planning/README.md` index with link
6. Present a 5-sentence summary to user + ask for approval

Do NOT start implementing until user approves.

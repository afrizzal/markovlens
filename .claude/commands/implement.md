---
description: Execute an approved plan step by step
argument-hint: <plan-path>
---

# Implement: $ARGUMENTS

Execute the approved plan at `$ARGUMENTS`.

**Note:** For GSD-tracked phase work, prefer `/gsd:execute-phase N` instead. Use this command for ad-hoc plans created via `/create-plan`.

## Pre-flight Checks

1. **Read the plan file** at `$ARGUMENTS`
2. **Verify status:** must be "Approved" — if "Draft", ask user to approve first
3. **Read all files mentioned** in the Tasks section
4. **Check git status:** working tree should be clean (or user explicitly OKs uncommitted changes)

## Execution Loop

For each unchecked task in the plan:

1. **Mark as in-progress** in the plan file
2. **Implement** the change (Edit/Write/etc.)
3. **Run quality checks** for the touched files:
   ```bash
   uv run ruff check <path>
   uv run mypy <path>
   uv run pytest <relevant-test-path>
   ```
4. **If checks pass:**
   - Mark task as `[x]` in plan
   - Atomic commit: `rtk git commit -m "<conventional message>"`
5. **If checks fail:**
   - Diagnose, fix, retry
   - If stuck: pause and surface to user, do NOT skip

## Post-Execution

1. **Verify acceptance criteria** — check each one
2. **Run full test suite:** `uv run pytest`
3. **Update docs:**
   - `docs/planning/task-progress.md` — mark feature Done with commit hashes
   - `docs/planning/decisions.md` — add ADR if technical decision made
   - `CLAUDE.md` / `README.md` / `manual-book.md` — as applicable
4. **Update plan status** to "Done"
5. **Summarize for user:** what was changed, what was committed, what to verify manually

---
name: workflow-two-terminal
description: User runs two Claude Code terminals — Opus for brainstorming/planning, Sonnet for execution. Token-saving pattern.
metadata:
  type: feedback
---

afrizzal runs **two Claude Code terminals simultaneously**:

- **Terminal 1 (Opus)** — brainstorming, planning, architecture decisions, design reviews
- **Terminal 2 (Sonnet)** — code execution, file writes, tests, debugging

**Why:** Cost optimization — Opus is expensive but high-quality for thinking; Sonnet is cheaper for executing well-specified tasks.

**How to apply:**
- When in Opus terminal: focus on architecture, design, planning. Don't burn tokens on boilerplate writes. Output should be specs/plans that Sonnet can execute from.
- When in Sonnet terminal: assume specs/plans were prepared by Opus. Execute crisply with minimal back-and-forth.
- Both terminals share the same project state via files (CLAUDE.md, docs/planning/, .planning/).

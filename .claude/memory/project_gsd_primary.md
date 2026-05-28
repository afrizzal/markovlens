---
name: project-gsd-primary
description: GSD is the primary planning system. Custom plans live in docs/planning/. Never edit .planning/ files manually.
metadata:
  type: project
---

MarkovLens uses **GSD (Get Shit Done)** as primary planning system.

**Why:** Already battle-tested by afrizzal in social-media-ai (production app). GSD provides milestone → roadmap → phase → plan → execute workflow with state tracking.

**How to apply:**
- `.planning/` is GSD-owned — `STATE.md`, `PROJECT.md`, `ROADMAP.md`, `phases/**` managed by `/gsd:*` commands, never manually edited
- Custom/ad-hoc plans go in `docs/planning/plans/` via `/create-plan` command
- For new phase work: `/gsd:plan-phase N` then `/gsd:execute-phase N`
- For bug investigation: `/gsd:debug`
- For trivial work: `/gsd:fast <desc>`

User chose GSD over Spec Kit and claude-code-spec-workflow because GSD already covers their workflow (see initial brainstorming session 2026-05-28).

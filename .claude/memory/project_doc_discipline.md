---
name: project-doc-discipline
description: Documentation discipline — README, manual-book, CLAUDE.md, decisions.md, task-progress.md must be updated after every coding session
metadata:
  type: project
---

afrizzal expects **rigorous documentation discipline** modeled after his social-media-ai project.

**After every coding session, the assistant MUST update:**
1. `docs/planning/task-progress.md` — move task to Done + commit hash
2. `docs/planning/decisions.md` — if new technical decision was made (ADR format)
3. `CLAUDE.md` — if new feature/page/module (App Pages table)
4. `README.md` — if user-visible change shipped
5. `manual-book.md` — if user workflow changed (both English + Indonesian sections)

**Why:** User wants this project to serve as portfolio piece for hiring — recruiters and other developers should be able to onboard from these docs without asking. Same standard he applies professionally.

**How to apply:** Treat doc updates as mandatory, not optional. Refuse to mark a task "done" until docs are updated.

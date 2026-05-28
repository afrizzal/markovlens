---
description: Initialize a new session with full project context awareness
---

# Prime Session

Load full MarkovLens context before starting any work.

## Steps

1. **Read primary context files (in this order):**
   - `CLAUDE.md` — main project guide
   - `docs/planning/master-plan.md` — vision + architecture
   - `docs/planning/task-progress.md` — current state
   - `docs/planning/decisions.md` — past decisions
   - `.claude/memory/MEMORY.md` — cross-session memory

2. **Check GSD state (if `.planning/` exists):**
   - `.planning/STATE.md`
   - `.planning/PROJECT.md`
   - Active phase docs

3. **Summarize for the user:**
   - Current project status (1-2 sentences)
   - What was last worked on
   - What's the next logical action
   - Any blockers or open questions

4. **Suggest next action:**
   - If a phase is in progress → suggest resuming
   - If no active phase → suggest planning next phase or backlog review
   - If everything's done → suggest verification or deploy

## Output Format

```
## MarkovLens — Session Context Loaded

**Project status:** <1-2 sentences>

**Last activity:** <what was done most recently>

**Suggested next action:** <specific command or task>

**Open items:**
- <bullet 1>
- <bullet 2>
```

Do NOT start coding yet — wait for user to confirm direction.

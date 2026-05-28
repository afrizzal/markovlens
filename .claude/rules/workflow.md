# Workflow — Before & After Coding

## BEFORE Starting Any Coding Session

Execute these steps in order:

### 1. Read Primary Context

```
CLAUDE.md                                → main entry: tech stack, structure, workflow
docs/planning/master-plan.md             → vision, architecture, agreed patterns
docs/planning/task-progress.md           → what's done, in progress, pending, blocked
docs/planning/decisions.md               → past technical decisions
.claude/memory/MEMORY.md                 → cross-session memory index
```

### 2. Read Task-Specific Files

Before editing any file:
- Read the file you'll modify with the `Read` tool
- Read connected files (import chain) to understand context
- Identify existing patterns — do not refactor without reason

### 3. Check GSD State (for phase work)

```
.planning/STATE.md                       → current GSD position + critical context
.planning/PROJECT.md                     → project goals + requirements
.planning/phases/NN-*/                   → active phase docs
```

### 4. For library/framework questions

Use **context7 MCP** first — see [context7.md](context7.md).

## DURING Coding

- **One task at a time** — finish before starting next
- **Use GSD entry points** appropriate to the work:
  - `/gsd:fast <desc>` — trivial inline change
  - `/gsd:quick <desc>` — small fix, 1-3 files
  - `/gsd:debug` — bug investigation
  - `/gsd:plan-phase N` — new phase planning
  - `/gsd:execute-phase N` — execute planned phase
- **Multi-file edits**: identify dependency order first
- **Atomic commits** — one logical change per commit
- **Always prefix bash with `rtk`** — token savings (60-90%)
- **Always type-hint** Python — even in small scripts
- **Validate invariants in `core/`** — assert matrix properties, value bounds

## AFTER Coding (Mandatory Updates)

### 1. Update Tracking Docs

- **`docs/planning/task-progress.md`**
  - Move task from Pending → Done
  - Add commit hash
  - Note if a deploy is required

- **`docs/planning/decisions.md`** (if new technical decision)
  - Format: `## YYYY-MM-DD — Decision Title`
  - Sections: Context, Decision, Why, Impact, Alternatives Considered

- **`CLAUDE.md`** (if applicable)
  - New page → update App Pages table
  - New module → add section
  - Tech stack change → update Tech Stack section

- **`README.md`** (if user-visible)
  - New feature highlighted
  - Updated roadmap status

- **`manual-book.md`** (if workflow changed)
  - Update relevant section (English + Indonesian)

### 2. Quality Checks

```bash
uv run ruff check .                      # Lint
uv run ruff format .                     # Format
uv run mypy core/ domains/               # Type check
uv run pytest                            # All tests pass
```

### 3. Commit

```bash
rtk git add <specific-files>             # Never `git add .`
rtk git commit -m "feat(brand-share): add monte carlo fan chart"
```

## Additional Rules

### Don't refactor without reason

- Bug fix = fix the bug only, no surrounding cleanup
- Feature add = add only what's requested
- Three similar lines > premature abstraction

### Don't add unnecessary error handling

- Validate at boundaries only (user input, external APIs, file I/O)
- Trust internal contracts + library guarantees
- Don't handle impossible cases

### Don't create planning files outside designated locations

- All planning notes → `docs/planning/`
- If unsure → `docs/planning/archive/temp-review/`
- GSD artifacts → `.planning/` (managed automatically, never edit manually)

## Quick GSD Command Reference

| Command | When |
|---|---|
| `/gsd:fast <desc>` | Trivial one-liner |
| `/gsd:quick <desc>` | 1-3 file change |
| `/gsd:debug` | Bug investigation with scientific method |
| `/gsd:plan-phase N` | Create plan for new phase |
| `/gsd:execute-phase N` | Execute all plans in phase |
| `/gsd:progress` | Check status + route to next action |
| `/gsd:add-backlog` | Add idea to backlog |
| `/gsd:resume-work` | Resume mid-session work |
| `/gsd:audit-uat` | Cross-phase verification audit |

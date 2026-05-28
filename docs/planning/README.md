# Planning Index

This folder contains living planning documents — updated continuously as the project evolves.

## Documents

| File | Purpose | Update frequency |
|---|---|---|
| [master-plan.md](master-plan.md) | Vision, architecture, agreed patterns, roadmap | Per architecture change |
| [task-progress.md](task-progress.md) | Current task status (Done/In-Progress/Pending/Blocked) | After every task |
| [decisions.md](decisions.md) | ADR-style technical decisions log | When new decision made |
| [plans/](plans/) | Ad-hoc plans created by `/create-plan` command | As needed |
| [archive/](archive/) | Old/superseded docs kept for history | When archiving |

## Related (Not Here)

| File | Where |
|---|---|
| Project vision/PROJECT.md | [.planning/PROJECT.md](../../.planning/PROJECT.md) (GSD-owned) |
| Roadmap | [.planning/ROADMAP.md](../../.planning/ROADMAP.md) (GSD-owned) |
| Active phase docs | `.planning/phases/NN-*/` (GSD-owned) |
| Tech reference docs | [../](.. ) (DATABASE, MARKOV-MODELS, MONTE-CARLO, etc.) |
| Public docs | [README.md](../../README.md), [manual-book.md](../../manual-book.md) |

## Conventions

- All planning notes go HERE — not into other folders
- If unsure where a doc belongs: drop into `archive/temp-review/`
- Never manually edit GSD-managed files in `.planning/`
- Use `/gsd:plan-phase N` for phase-level planning (preferred over ad-hoc plans)
- Use `/create-plan <desc>` for ad-hoc plans that don't fit a phase

## Workflow

1. **Before starting work:** read `master-plan.md`, `task-progress.md`, `decisions.md`
2. **After finishing work:** update `task-progress.md` (move to Done + commit hash), `decisions.md` (if new decision)
3. **When making architecture-level changes:** update `master-plan.md`

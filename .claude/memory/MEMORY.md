# MarkovLens — Cross-Session Memory Index

> One-line entries pointing to memory files. Keep < 200 lines.
> Each memory file lives in this same directory (`.claude/memory/`).

## User Profile

- [User Role](user_role.md) — afrizzal, IT at Miracle Aesthetic Clinic, building MarkovLens as BA/BI portfolio piece

## Workflow Preferences

- [Two-Terminal Workflow](workflow_two_terminal.md) — Opus for brainstorming, Sonnet for execution to save tokens
- [Token Optimization](workflow_token_optimization.md) — always prefix `rtk`, use context7 over WebSearch, prefer skills for repeated patterns

## Project Conventions

- [GSD as Primary Workflow](project_gsd_primary.md) — GSD owns `.planning/`; all custom plans live in `docs/planning/`
- [Documentation Discipline](project_doc_discipline.md) — README/manual-book/CLAUDE.md/decisions.md updated after every coding session

## Technical Decisions (Stable)

- [DuckDB Chosen](decision_duckdb.md) — embedded analytical DB for storage layer
- [uv Chosen](decision_uv.md) — modern Python package manager replacing pip/poetry
- [Streamlit Chosen](decision_streamlit.md) — fastest path to BA-grade dashboards

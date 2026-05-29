# Task Progress

> Living document. Updated after every coding session.
>
> Last updated: 2026-05-29

## Conventions

- **Done** — task complete, commit referenced
- **In Progress** — actively being worked on
- **Pending** — planned, not started
- **Blocked** — has a blocker (note what + who)

Format per row: `<task>` — `<status>` — `<commit hash if Done>` — `<notes>`

---

## Phase 00 — Scaffold + Foundation

| Task | Status | Commit | Notes |
|---|---|---|---|
| Create directory structure | ✅ Done | _scaffold_ | core/, domains/, app/, tests/, docs/, .claude/, data/ |
| pyproject.toml + uv config | ✅ Done | _scaffold_ | Python 3.12, all deps declared |
| .gitignore | ✅ Done | _scaffold_ | Python + UV + Streamlit + data/ + reports/ |
| LICENSE (MIT) | ✅ Done | _scaffold_ | |
| .mcp.json (context7) | ✅ Done | _scaffold_ | Same key as social-media-ai |
| .streamlit/config.toml | ✅ Done | _scaffold_ | Light theme, primary #4338CA |
| README.md (hero + quickstart) | ✅ Done | _scaffold_ | Includes badges, roadmap, ack |
| CLAUDE.md | ✅ Done | _scaffold_ | Full Claude Code guide |
| CONTRIBUTING.md | ✅ Done | _scaffold_ | uv setup, branching, commits |
| manual-book.md (bilingual) | ✅ Done | _scaffold_ | English + Bahasa Indonesia |
| 8 .claude/rules/ files | ✅ Done | _scaffold_ | python, markov, streamlit, data, coding, context7, workflow, project |
| 3 .claude/commands/ files | ✅ Done | _scaffold_ | prime, create-plan, implement |
| 4 .claude/skills/ scaffolds | ✅ Done | _scaffold_ | markov-validator, monte-carlo-runner, streamlit-page-scaffolder, dataset-prepper |
| .claude/memory/MEMORY.md + 6 entries | ✅ Done | _scaffold_ | User, workflow, decisions |
| .claude/settings.local.json | ✅ Done | _scaffold_ | Bash allowlist for uv/rtk/git |
| docs/planning/ — all 4 files | ✅ Done | _scaffold_ | README, master-plan, task-progress, decisions |
| docs/ technical refs | 🚧 In Progress | — | DATABASE, MARKOV-MODELS substantive; others skeleton |
| Code skeleton (core/, app/, tests/) | 🟡 Pending | — | Stubs with TODO |
| git init + initial commit | 🟡 Pending | — | User runs manually |
| Run `uv sync` | 🟡 Pending | — | User runs manually after uv install |
| Run `/gsd:new-project` | 🟡 Pending | — | User runs manually in Sonnet terminal |

---

## Phase 01 — Markov Engine Core

> Plan via `/gsd:plan-phase 01` after Phase 00 completes.

| Task | Status | Commit | Notes |
|---|---|---|---|
| Implement m1 (Homogeneous Markov) | 🟡 Pending | — | core/models.py |
| Implement m2 (Time-varying Markov) | 🟡 Pending | — | core/models.py |
| Implement m3 (Extended time-varying) | 🟡 Pending | — | core/models.py |
| Implement Monte Carlo simulator | 🟡 Pending | — | core/simulation.py |
| Implement longshot calibration | 🟡 Pending | — | core/simulation.py |
| Implement validation (rows sum, sparsity) | 🟡 Pending | — | core/models.py |
| Implement metrics (MAPE, Brier) | 🟡 Pending | — | core/metrics.py |
| Implement walk-forward validation | 🟡 Pending | — | core/validation.py |
| Unit tests for all of above | 🟡 Pending | — | tests/unit/ |

---

## Phase 02 — Storage + Data Ingestion

| Task | Status | Commit | Notes |
|---|---|---|---|
| DuckDB schema (schema.sql) | ✅ Done | abb74af | datasets, transitions, matrices, sim_runs, forecasts, scenarios |
| Connection singleton | ✅ Done | abb74af | core/db/connection.py — get_connection() + init_schema() |
| Query helpers | ✅ Done | — | register_dataset, list_datasets, get_dataset, load_transitions, bulk_insert_transitions, build_transition_matrix |
| Dataset registration | ✅ Done | 2eb18b0 | validate_transitions_df in core/io/loaders.py |
| Kaggle e-commerce brand-share seed | ✅ Done | — | Synthetic FMCG DGP — 5 brands × 24 periods, 600 rows |
| Kaggle Telco churn seed | ✅ Done | — | IBM Telco CSV → 4 states (active/at_risk/inactive/churned), 7032 rows |
| Integration tests | ✅ Done | — | tests/integration/test_queries.py — 3 pass |

---

## Phase 03 — Brand Share Domain

| Task | Status | Commit | Notes |
|---|---|---|---|
| Service layer | 🟡 Pending | — | domains/brand_share/service.py |
| Transforms | 🟡 Pending | — | domains/brand_share/transforms.py |
| Streamlit page | 🟡 Pending | — | app/pages/1_Brand_Share.py |
| Transition heatmap | 🟡 Pending | — | app/components/transition_heatmap.py |
| Monte Carlo fan chart | 🟡 Pending | — | app/components/monte_carlo_fan.py |
| Model comparison view | 🟡 Pending | — | tabs within page |
| Companion notebook | 🟡 Pending | — | notebooks/brand_share_case_study.ipynb |

---

## Phase 04 — Customer Churn Domain

| Task | Status | Commit | Notes |
|---|---|---|---|
| State design (Active, At-Risk, etc.) | 🟡 Pending | — | docs/MARKOV-MODELS.md update |
| Service layer | 🟡 Pending | — | domains/churn/service.py |
| Sankey component | 🟡 Pending | — | app/components/sankey.py |
| Streamlit page | 🟡 Pending | — | app/pages/2_Churn.py |
| What-if simulator | 🟡 Pending | — | sub-tab on Churn page |
| Companion notebook | 🟡 Pending | — | notebooks/churn_case_study.ipynb |

---

## Phase 05 — UI Polish

| Task | Status | Commit | Notes |
|---|---|---|---|
| Claude Design mockup → tokens | 🟡 Pending | — | Extract from React artifact |
| theme.css (CSS variables) | 🟡 Pending | — | app/styles/theme.css |
| Plotly theme template | 🟡 Pending | — | app/styles/plotly_theme.py |
| Custom components (KPI, etc.) | 🟡 Pending | — | app/components/ |
| Empty states + loading states | 🟡 Pending | — | All pages |

---

## Phase 06 — Reports & Export

| Task | Status | Commit | Notes |
|---|---|---|---|
| PDF report builder | 🟡 Pending | — | core/io/exporters.py (ReportLab) |
| Reports page | 🟡 Pending | — | app/pages/3_Reports.py |
| Notebook export | 🟡 Pending | — | Generate reproducible .ipynb |
| CSV/PNG individual exports | 🟡 Pending | — | |

---

## Phase 07 — Deploy

| Task | Status | Commit | Notes |
|---|---|---|---|
| Streamlit Cloud account setup | 🟡 Pending | — | User manual step |
| GitHub repo + push | 🟡 Pending | — | User manual step |
| Connect Streamlit Cloud → repo | 🟡 Pending | — | User manual step |
| Secrets configuration | 🟡 Pending | — | If any env vars needed |
| Smoke test live URL | 🟡 Pending | — | All pages load, charts render |
| Custom domain (optional) | 🟡 Pending | — | markovlens.app or similar |
| Update README with live URL | 🟡 Pending | — | |
| Demo video + LinkedIn post | 🟡 Pending | — | User shipping motion |

---

## Blocked / Issues

_None currently._

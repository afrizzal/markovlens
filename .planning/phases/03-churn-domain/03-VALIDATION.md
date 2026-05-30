---
phase: 03
slug: churn-domain
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-31
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/unit/ -q` |
| **Full suite command** | `uv run pytest tests/ -q` |
| **Estimated runtime** | ~4 seconds (baseline 61 tests @ 3.53s) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/ -q`
- **After every plan wave:** Run `uv run pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~4 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-W0 | 01 | 0 | CH-01 | unit/integration stub | `uv run pytest tests/unit/test_churn_service.py -x` | ❌ W0 | ⬜ pending |
| 03-01-01 | 01 | 1 | CH-01 | unit | `uv run pytest tests/unit/test_churn_service.py -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | CH-01 | integration | `uv run pytest tests/integration/test_churn_service.py -x` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | CH-02 | unit | `uv run pytest tests/unit/test_churn_service.py -x` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 2 | CH-03 | integration | `uv run pytest tests/integration/test_churn_service.py -x` | ❌ W0 | ⬜ pending |
| 03-04-01 | 04 | 3 | CH-04 | unit (smoke) | `uv run pytest tests/unit/test_page_import.py -x` | ✅ (extend) | ⬜ pending |
| 03-99-Q | all | post | all | full suite | `uv run pytest tests/ -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_churn_service.py` — stubs for CH-01 (ChurnAnalysisResult shape, KPI formulas, simulate_scenario renorm, fundamental matrix compute_avg_lifetime)
- [ ] `tests/integration/test_churn_service.py` — stubs for CH-01 integration (seeded temp DuckDB, run_analysis end-to-end, simulate_scenario differs from baseline)
- [ ] `tests/unit/test_page_import.py` — extend existing file: add 2_Churn.py smoke import case (mirrors existing BS-06 pattern)
- [ ] `pyproject.toml` — add `"domains/churn/service.py" = ["N803", "N806"]` to `[tool.ruff.lint.per-file-ignores]`

*Existing infrastructure covers framework; only new test files needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Sankey ribbons visible in browser with correct colors | CH-02 | Plotly shapes rendering requires visual inspection | Open `/Churn`, run analysis, verify ribbon widths proportional to counts, Churned node at bottom in red |
| What-if sliders update chart live without button | CH-03 | Streamlit re-run behavior; no headless test | Open `/Churn`, move accordion slider, verify stacked-area chart updates immediately |
| Impact narrative changes with slider | CH-03 | String content dependent on data | Move "Active → At-Risk" slider, verify narrative shows "Reducing Active → At-Risk by Xpp saves N customers" |
| Time scrubber updates distribution bar | CH-02 | DOM update; requires visual check | Drag period slider, verify horizontal stacked bar changes |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

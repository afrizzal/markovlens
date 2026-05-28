---
phase: 01
slug: markov-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-29
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest tests/unit/ -m "not slow" --cov=core --cov-report=term-missing -q` |
| **Full suite command** | `uv run pytest --cov=core --cov-report=term-missing` |
| **Estimated runtime** | ~30 seconds (unit); ~60 seconds (full with integration) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/ -m "not slow" -q`
- **After every plan wave:** Run `uv run pytest --cov=core --cov-report=term-missing -q`
- **Before `/gsd:verify-work`:** Full suite must be green + `core/` coverage >= 80%
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-W0-01 | test scaffolding | Wave 0 | ENG-01..ENG-10, DATA-01..03 | scaffold | `uv run pytest tests/unit/ -q --co` | ❌ W0 | ⬜ pending |
| 01-01-01 | validate | 1 | ENG-01 | unit | `uv run pytest tests/unit/test_models.py -x -q` | ✅ (skipped) | ⬜ pending |
| 01-01-02 | M1 | 1 | ENG-02 | unit/regression | `uv run pytest tests/unit/test_models.py::test_m1_forecast_replicates_chan_2015_table3 -x` | ✅ (skipped) | ⬜ pending |
| 01-01-03 | M2 | 1 | ENG-03 | unit | `uv run pytest tests/unit/test_models.py -k "m2" -x -q` | ❌ W0 | ⬜ pending |
| 01-01-04 | M3 | 1 | ENG-04 | unit | `uv run pytest tests/unit/test_models.py -k "m3" -x -q` | ❌ W0 | ⬜ pending |
| 01-02-01 | MC | 2 | ENG-05 | unit | `uv run pytest tests/unit/test_simulation.py -k "monte_carlo" -x -q` | ❌ W0 | ⬜ pending |
| 01-02-02 | calibrate | 2 | ENG-06 | unit | `uv run pytest tests/unit/test_simulation.py -k "calibrate" -x -q` | ❌ W0 | ⬜ pending |
| 01-02-03 | quantile | 2 | ENG-07 | unit | `uv run pytest tests/unit/test_simulation.py -k "quantile" -x -q` | ❌ W0 | ⬜ pending |
| 01-02-04 | sparsity | 2 | ENG-08 | unit | `uv run pytest tests/unit/test_models.py -k "sparse" -x -q` | ❌ W0 | ⬜ pending |
| 01-02-05 | backtest | 2 | ENG-09 | unit | `uv run pytest tests/unit/test_simulation.py -k "walk_forward" -x -q` | ❌ W0 | ⬜ pending |
| 01-02-06 | metrics | 2 | ENG-10 | unit | `uv run pytest tests/unit/test_metrics.py -x -q` | ❌ W0 | ⬜ pending |
| 01-03-01 | serialization | 3 | DATA-03 (serialize) | unit | `uv run pytest tests/unit/test_serialization.py -x -q` | ❌ W0 | ⬜ pending |
| 01-03-02 | build_matrix | 3 | DATA-03 | integration | `uv run pytest -m integration tests/integration/test_queries.py -x -q` | ❌ W0 | ⬜ pending |
| 01-03-03 | loaders | 3 | DATA-01 | unit | `uv run pytest tests/unit/test_loaders.py -x -q` | ❌ W0 | ⬜ pending |
| 01-04-01 | seed_data | 4 | DATA-02 | integration | `uv run pytest -m integration tests/integration/test_queries.py -k "seed" -x -q` | ❌ W0 | ⬜ pending |
| 01-05-01 | coverage | 5 | QA gate | coverage | `uv run pytest --cov=core --cov-fail-under=80 -q` | ✅ (pytest-cov) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

These test files must be created (with skip-annotated stubs) before Wave 1 implementation tasks begin:

- [ ] `tests/unit/test_simulation.py` — stubs for ENG-05, ENG-06, ENG-07, ENG-09
- [ ] `tests/unit/test_metrics.py` — stubs for ENG-10 (MAPE, Brier, log-loss)
- [ ] `tests/unit/test_serialization.py` — stubs for DATA-03 serialization helpers
- [ ] `tests/unit/test_loaders.py` — stubs for DATA-01 (validate_transitions_df)
- [ ] `tests/integration/__init__.py` — create integration package
- [ ] `tests/integration/test_queries.py` — stubs for DATA-02/DATA-03 integration paths
- [ ] `tests/unit/test_models.py` — modify: remove `@pytest.mark.skip`, add 6 new test stubs

*All new tests start with `@pytest.mark.skip(reason="Wave 0 — not yet implemented")` and are un-skipped as tasks complete.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| seed_data.py downloads telco CSV | DATA-02 | File must exist at `data/seed/telco_churn.csv` before test | Confirm `data/seed/telco_churn.csv` is committed to repo; run `git ls-files data/seed/` |
| DuckDB populated with 5+ forecasts | DATA-02 | Requires running seed script against real DB | Run `uv run python scripts/seed_data.py` then `python -c "import duckdb; c=duckdb.connect('data/markovlens.duckdb'); print(c.execute('SELECT COUNT(*) FROM forecasts').fetchone())"` — verify count >= 5 |
| Chan (2015) REPL regression | ENG-02 | Success Criterion 1 from roadmap | `python -c "from core.models import M1Homogeneous; import numpy as np; ..."` — verify Table 3 values |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

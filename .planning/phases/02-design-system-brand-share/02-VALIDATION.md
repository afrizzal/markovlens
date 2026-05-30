---
phase: 02
slug: design-system-brand-share
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-30
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `02-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest tests/unit/ -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Coverage command** | `uv run pytest --cov=app --cov=domains -q` |
| **Estimated runtime** | ~30s quick / ~60s full |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/ -x -q`
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

Task IDs are assigned by the planner; rows below map each phase requirement to its
automated check and target wave (per RESEARCH.md). The planner MUST attach the matching
`<automated>` verify command to the task that delivers each requirement.

| Plan/Wave | Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-----------|-------------|----------|-----------|-------------------|-------------|--------|
| Wave 0 | UI-01 | `register_theme()` registers `markovlens`; default `streamlit+markovlens` | unit (smoke) | `uv run pytest tests/unit/test_plotly_theme.py -x -q` | ❌ W0 | ⬜ pending |
| Wave 0 | BS-05 | `compute_stationary` sums to 1.0 ± 1e-6; returns None when undefined | unit | `uv run pytest tests/unit/test_stationary.py -x -q` | ❌ W0 | ⬜ pending |
| Wave 1 | UI-02 | `transition_heatmap()` / `monte_carlo_fan()` render without raising | unit | `uv run pytest tests/unit/test_components.py -x -q` | ❌ W1 | ⬜ pending |
| Wave 1 | BS-02 | Heatmap colorscale fixed `[0,1]`; annotations present; sparsity markers for `<20` obs | unit | `uv run pytest tests/unit/test_components.py::test_transition_heatmap_sparsity -x` | ❌ W1 | ⬜ pending |
| Wave 1 | BS-03 | Fan chart bands P10/P50/P90; quantiles monotonic; separator + legend present | unit | `uv run pytest tests/unit/test_components.py::test_monte_carlo_fan_traces -x` | ❌ W1 | ⬜ pending |
| Wave 2 | BS-01 | `run_forecast()` returns `BrandShareForecastResult`, no Plotly objects; state_labels length == matrix dim | integration | `uv run pytest tests/integration/test_brand_share_service.py -x -q` | ❌ W2 | ⬜ pending |
| Wave 2 | BS-04 | Accuracy dict has `mape`/`brier`/`log_loss` per model; winner computed not hardcoded | integration | `uv run pytest tests/integration/test_brand_share_service.py::test_model_comparison -x` | ❌ W2 | ⬜ pending |
| Wave 3 | BS-06 | `1_Brand_Share.py` imports without raising (no top-level side effects) | unit | `uv run pytest tests/unit/test_page_import.py -x -q` | ❌ W3 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_plotly_theme.py` — smoke test for UI-01; fixture MUST `import streamlit` before `register_theme()` (Streamlit registers its base template on import)
- [ ] `tests/unit/test_stationary.py` — covers BS-05 `compute_stationary` + power-iteration fallback + undefined-matrix `None` case
- [ ] Reuse existing `tests/conftest.py` fixtures (`sample_2x2_matrix`, `temp_duckdb_path`) for component and service tests — no new framework install needed

---

## Manual-Only Verifications

Automated unit tests assert chart *structure* (trace count, colorscale range, annotations);
the final *visual* confirmation in a running Streamlit app is manual.

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Heatmap cells are color-coded and the `<20 obs` warning badge is visibly rendered | BS-02 | Visual rendering of color ramp + badge can't be asserted from figure JSON alone | Run `uv run streamlit run app/Home.py`, open `/Brand_Share`, select a dataset, confirm heatmap colors + badge appear |
| Fan chart bands and the historical/forecast vertical separator are visibly distinct | BS-03 | Visual band fill + separator position is a perceptual check | Click "Run Forecast", confirm three shaded bands + separator line + legend render |
| Stationary bar chart label reads "Long-run equilibrium (if these rates persist…)" and bars sum to 1.0 visibly | BS-05 | Label text + caveat subcaption is a visual/UX check | Open Overview tab, confirm bar chart label, caveat subcaption, and proportions |

---

## Validation Sign-Off

- [ ] All requirement rows have an `<automated>` verify command or a Wave 0 dependency
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING test references (`test_plotly_theme.py`, `test_stationary.py`)
- [ ] No watch-mode flags in any command
- [ ] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter (after planner attaches verifies)

**Approval:** approved 2026-05-30 (plan-checker VERIFICATION PASSED)

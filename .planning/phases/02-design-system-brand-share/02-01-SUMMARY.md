---
phase: "02"
plan: "01"
subsystem: "Design System Foundation"
tags: [plotly, css-tokens, stationary-distribution, ui-01, bs-05]
dependency_graph:
  requires: []
  provides:
    - "app/styles/plotly_theme.py::register_theme() — Plotly 6.x template registration"
    - "app/styles/theme.css — full design token CSS layer (light + dark)"
    - "core/models.py::compute_stationary() — stationary distribution helper"
  affects:
    - "All Phase 02 components (inherit Plotly template)"
    - "Brand Share page (uses stationary distribution panel)"
tech_stack:
  added: []
  patterns:
    - "Plotly Template composition: pio.templates['markovlens'] + streamlit+markovlens default"
    - "scipy.linalg.eig(P.T) + power-iteration fallback for stationary distribution"
    - "Full CSS token port from design-reference/markov.css verbatim"
key_files:
  created:
    - "app/styles/plotly_theme.py"
    - "tests/unit/test_plotly_theme.py"
    - "tests/unit/test_stationary.py"
  modified:
    - "app/styles/theme.css"
    - "app/styles/__init__.py"
    - "core/models.py"
decisions:
  - "compute_stationary placed in core/models.py (pure, no streamlit import) alongside model classes"
  - "register_theme() must be called after import streamlit due to Plotly template composition semantics"
  - "dict() -> dict literals to satisfy ruff C408; both patterns are functionally identical"
metrics:
  duration: "17min"
  completed_date: "2026-05-30"
  tasks_completed: 3
  files_modified: 6
---

# Phase 02 Plan 01: Design System Foundation Summary

Plotly 6.x theme template (UI-01) + full CSS design token port (UI-01) + stationary distribution helper (BS-05) — the dependency root for all Phase 02 components, the Brand Share service, and the page.

## Tasks Completed

| Task | Description | Commit | Status |
|------|-------------|--------|--------|
| 1 | Failing-first tests for UI-01 (Plotly theme) and BS-05 (stationary) | 977ae5d | GREEN |
| 2 | Port theme.css + create Plotly template | c463d81 | GREEN |
| 3 | Add compute_stationary() to core/models.py | 7e4d47d | GREEN |
| — | Fix ruff lint issues in test files | d47ef07 | Clean |

## Decisions Made

1. **compute_stationary location**: Placed in `core/models.py` alongside M1/M2/M3 — pure function, no streamlit import. Brand Share service calls it; page calls the service (no layer skip).

2. **register_theme() ordering**: Must execute after `import streamlit` has run. This is automatic in any Streamlit page; unit tests must `import streamlit` (or `import plotly.io`) before calling `register_theme()`. The 'streamlit' Plotly template is registered as a side effect of `import streamlit` — without it, `"streamlit+markovlens"` composition fails.

3. **dict literals over dict() calls**: Ruff C408 rule requires `{...}` syntax instead of `dict(...)` for Plotly layout properties. Functionally identical; dict literals are more idiomatic.

## Success Criteria Check

- [x] UI-01 smoke test green: `'markovlens' in pio.templates` and default is `'streamlit+markovlens'`
- [x] theme.css is the full markov.css port (light + dark, all utility classes, `--chart-seq-5` present)
- [x] No "Phase 05" comment remains in theme.css
- [x] BS-05 `compute_stationary` returns sum-to-1.0 vector for `[[0.7,0.3],[0.4,0.6]]` → `[4/7, 3/7]`
- [x] `compute_stationary` lives in core/models.py with no streamlit import
- [x] `uv run pytest -x -q` → 46/46 pass (no regressions to Phase 01)
- [x] `uv run ruff check` clean on all modified files
- [x] `uv run mypy core/` → no issues

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Ruff C408: dict() calls in plotly_theme.py**
- **Found during:** Task 3 verification (ruff check)
- **Issue:** Plotly template property assignment used `dict()` constructor instead of `{...}` literals; C408 rule violation in ruff config
- **Fix:** Rewrote all `dict(...)` calls as `{...}` literals in `plotly_theme.py`
- **Files modified:** `app/styles/plotly_theme.py`
- **Commit:** `7e4d47d` (included in Task 3 commit)

**2. [Rule 1 - Bug] RUF100: unused noqa directives in test files**
- **Found during:** Task 3 verification (ruff check)
- **Issue:** `# noqa: BLE001` directives in test files are invalid (BLE001 not in ruff config)
- **Fix:** Removed unused noqa directives from test files; fixed import order (I001) in test_plotly_theme.py
- **Files modified:** `tests/unit/test_plotly_theme.py`, `tests/unit/test_stationary.py`
- **Commit:** `d47ef07`

**3. [Rule 1 - Bug] mypy no-any-return in compute_stationary**
- **Found during:** Task 3 verification (mypy core/)
- **Issue:** `.astype(np.float64)` returns `Any` in numpy stubs; mypy flagged `no-any-return` on function typed as `StateVector | None`
- **Fix:** Added explicit `result: np.ndarray` and `result2: np.ndarray` intermediate type annotations
- **Files modified:** `core/models.py`
- **Commit:** `7e4d47d`

### Out-of-scope Issues Deferred

- `app/Home.py` N999 (invalid module name) — pre-existing before this plan; not caused by plan changes.

## Known Stubs

None. All implementations are complete and wired:
- `register_theme()` fully registers the Plotly template — no placeholder values
- `theme.css` is a complete verbatim port of `markov.css` — no stub content
- `compute_stationary()` is a complete implementation — no NotImplementedError

## Self-Check: PASSED

Files verified:
- FOUND: app/styles/plotly_theme.py
- FOUND: app/styles/theme.css
- FOUND: core/models.py
- FOUND: tests/unit/test_plotly_theme.py
- FOUND: tests/unit/test_stationary.py

Commits verified:
- 977ae5d: test(02-01) — failing tests
- c463d81: feat(02-01) — theme.css port + Plotly template
- 7e4d47d: feat(02-01) — compute_stationary()
- d47ef07: fix(02-01) — lint fixes

---
phase: 01-markov-engine
plan: 06
type: execute
wave: 5
depends_on:
  - 02
  - 03
  - 04
  - 05
files_modified:
  - tests/unit/test_models.py
  - tests/unit/test_simulation.py
  - tests/unit/test_metrics.py
  - tests/unit/test_serialization.py
  - tests/unit/test_loaders.py
  - tests/integration/test_queries.py
  - pyproject.toml
autonomous: true
requirements:
  - ENG-01
  - ENG-02
  - ENG-03
  - ENG-04
  - ENG-05
  - ENG-06
  - ENG-07
  - ENG-08
  - ENG-09
  - ENG-10
  - DATA-01
  - DATA-02
  - DATA-03
must_haves:
  truths:
    - "uv run pytest --cov=core --cov-fail-under=80 -q exits 0 (Roadmap Phase 01 Success Criterion 4)"
    - "Zero @pytest.mark.skip markers remain in any tests/ file (except those that depend on data/seed/telco_churn.csv being committed)"
    - "uv run ruff check core/ scripts/ tests/ exits 0"
    - "uv run mypy core/ exits 0 (or with only documented allowances)"
    - "No grep result for 'raise NotImplementedError' in core/ (every Phase 01 stub is implemented)"
    - "No grep result for 'import streamlit' in core/ or domains/"
  artifacts:
    - path: ".planning/phases/01-markov-engine/01-06-SUMMARY.md"
      provides: "Phase 01 closing report — coverage %, test count, regression evidence"
      contains: "coverage"
  key_links:
    - from: "pyproject.toml"
      to: "pytest-cov"
      via: "tool.pytest.ini_options addopts uses --cov flag (optional)"
      pattern: "pytest"
---

<objective>
Close Phase 01 with a verified quality gate: > 80% coverage on `core/`, zero skipped tests, ruff + mypy clean, all 13 phase requirements verifiably complete.

Purpose: Roadmap Success Criterion 4 explicitly requires `> 80% coverage for core/` with `all ENG-01..ENG-10 regression tests green`. The downstream Phase 02 trusts that every function in core/ is implemented and tested — without this gate, Phase 02 starts on quicksand.

Output:
- Coverage report ≥ 80% for `core/`
- Lint and type-check clean
- Final phase summary document
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-markov-engine/01-CONTEXT.md
@.planning/phases/01-markov-engine/01-RESEARCH.md
@.planning/phases/01-markov-engine/01-VALIDATION.md
@.planning/phases/01-markov-engine/01-01-SUMMARY.md
@.planning/phases/01-markov-engine/01-02-SUMMARY.md
@.planning/phases/01-markov-engine/01-03-SUMMARY.md
@.planning/phases/01-markov-engine/01-04-SUMMARY.md
@.planning/phases/01-markov-engine/01-05-SUMMARY.md
@core/models.py
@core/simulation.py
@core/metrics.py
@core/db/serialization.py
@core/db/queries.py
@core/io/loaders.py
@scripts/seed_data.py
@pyproject.toml
@.claude/rules/python-conventions.md
@.claude/rules/markov-patterns.md

<interfaces>
This plan does not introduce new interfaces — it audits the deliverables produced by Plans 01-05.

Coverage target (Roadmap SC 4): `core/` >= 80%. Run via:
```bash
uv run pytest --cov=core --cov-report=term-missing --cov-fail-under=80
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Confirm zero skipped tests + run full suite</name>
  <read_first>
    - tests/unit/test_models.py
    - tests/unit/test_simulation.py
    - tests/unit/test_metrics.py
    - tests/unit/test_serialization.py
    - tests/unit/test_loaders.py
    - tests/integration/test_queries.py
    - pyproject.toml (confirm the `integration` marker is registered under `[tool.pytest.ini_options].markers`)
  </read_first>
  <action>
**Step A: Audit skip markers.** Run:
```bash
grep -rn "@pytest.mark.skip" tests/
```
This MUST return zero hits across all test files. If any skip remains, locate it, confirm the corresponding function in `core/` is implemented per its target requirement (cross-reference VALIDATION.md `Per-Task Verification Map`), and remove the skip decorator. If a skip is intentional (e.g., requires manual data setup), record the rationale in this plan's SUMMARY and leave it — but Phase 01 has no such intentional skips.

**Step B: Verify integration marker is registered** in `pyproject.toml`. Look for the `[tool.pytest.ini_options]` table. If `markers` is not defined or does not include `integration`, add:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests that hit a real DuckDB instance",
]
```

**Step C: Run the full suite (without coverage first, to catch failures quickly):**
```bash
uv run pytest tests/ -v --tb=short
```
Every test must pass — no `skipped`, no `failed`, no `errored`. Expect approximately 11 + 12 + 5 + 4 + 3 + 5 = 40 tests to PASS.

If any test fails, STOP and report the failure to the user before continuing. Do NOT proceed to coverage analysis without a fully green test suite.
  </action>
  <verify>
    <automated>uv run pytest tests/ -q</automated>
  </verify>
  <acceptance_criteria>
    - `grep -rn "@pytest.mark.skip" tests/` returns zero matches.
    - `pyproject.toml` `[tool.pytest.ini_options].markers` list contains both `slow` and `integration` markers.
    - `uv run pytest tests/ -q` exits 0.
    - The pytest summary line reads `40 passed` (approximate — exact count is 40 ± 2 depending on whether stubs added extra cases). NO `skipped` or `failed` entries.
  </acceptance_criteria>
  <done>
    Full test suite green. Every Wave 0 stub has been un-skipped during its implementation plan. integration marker registered.
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Coverage audit (Roadmap SC 4 enforcement)</name>
  <read_first>
    - core/models.py
    - core/simulation.py
    - core/metrics.py
    - core/db/serialization.py
    - core/db/queries.py
    - core/io/loaders.py
    - .planning/phases/01-markov-engine/01-RESEARCH.md (Sampling Rate section — phase gate definition)
  </read_first>
  <action>
**Step A: Generate coverage report:**
```bash
uv run pytest --cov=core --cov-report=term-missing --cov-fail-under=80 -q
```

The command MUST exit 0. If coverage is below 80%, the command exits with code 1 — record the uncovered lines reported and proceed to Step B.

**Step B (only if Step A fails):** Add targeted tests for uncovered branches. Common gaps for this phase:
- `validate_transition_matrix` non-square-but-also-NaN combined error path (covered by passing a 1x3 NaN matrix).
- `M3Extended` 2D `G` (time-varying growth) path — add a test that passes G of shape (n_periods, n_states).
- `monte_carlo_simulate` distribution start (covered by `test_monte_carlo_accepts_distribution_start`).
- `walk_forward_backtest` early-return path when `len(periods) <= window` — add a test passing window > len(periods).
- `build_transition_matrix` empty result `ValueError` path — add a test that calls it with a dataset_id that has zero transitions.

For each remaining coverage gap, ADD a test (skip-annotated if Plans 02-05 missed something obvious; otherwise inline in this plan). Do NOT lower the 80% threshold under any circumstance.

**Step C: Re-run coverage** until `uv run pytest --cov=core --cov-fail-under=80 -q` exits 0.

**Step D: Manual Roadmap SC 1 check (Chan REPL):**
```bash
uv run python -c "
import numpy as np
from core.models import M1Homogeneous
P = np.array([
    [0.98230, 0.00753, 0.00464, 0.00552],
    [0.01158, 0.96161, 0.02489, 0.00192],
    [0.01442, 0.01105, 0.95721, 0.01732],
    [0.01978, 0.01122, 0.01364, 0.95536],
])
Y_1 = np.array([0.5878, 0.2830, 0.0585, 0.0708])
m = M1Homogeneous(P=P)
r = m.forecast(Y_1=Y_1, horizon=5)
print('forecast_array[1] =', np.round(r.forecast_array[1], 4).tolist())
print('Chan 2015 Table 3 expected = [0.5829, 0.278, 0.0667, 0.0724]')
"
```
Output must show line 1 approximately equal to line 2.

**Step E: Manual Roadmap SC 2 check (reproducibility):**
```bash
uv run python -c "
import numpy as np
from core.simulation import monte_carlo_simulate
P = np.array([[0.7, 0.3], [0.4, 0.6]])
a = monte_carlo_simulate(P, 0, n_steps=10, n_simulations=1000, seed=42)
b = monte_carlo_simulate(P, 0, n_steps=10, n_simulations=1000, seed=42)
c = monte_carlo_simulate(P, 0, n_steps=10, n_simulations=1000, seed=7)
print('same seed identical:', bool(np.array_equal(a, b)))
print('diff seed differs:', not bool(np.array_equal(a, c)))
print('dtype:', a.dtype)
"
```
All three lines must satisfy: `same seed identical: True`, `diff seed differs: True`, `dtype: int64`.

**Step F: Manual Roadmap SC 3 check (validator):**
```bash
uv run python -c "
import numpy as np
from core.models import validate_transition_matrix
from core.exceptions import InvalidTransitionMatrixError
try: validate_transition_matrix(np.array([[0.5, 0.6], [0.3, 0.3]]))
except InvalidTransitionMatrixError as e: print('row-sum:', 'OK')
try: validate_transition_matrix(np.array([[1.5, -0.5], [0.5, 0.5]]))
except InvalidTransitionMatrixError as e: print('negative:', 'OK')
try: validate_transition_matrix(np.array([[0.5, 0.5, 0.0]]))
except InvalidTransitionMatrixError as e: print('non-square:', 'OK')
validate_transition_matrix(np.array([[0.7, 0.3], [0.4, 0.6]]))
print('valid 3x3:', 'OK')
"
```
Output must show all four "OK" lines.
  </action>
  <verify>
    <automated>uv run pytest --cov=core --cov-report=term-missing --cov-fail-under=80 -q</automated>
  </verify>
  <acceptance_criteria>
    - `uv run pytest --cov=core --cov-report=term-missing --cov-fail-under=80 -q` exits 0 (Roadmap SC 4 enforcement).
    - Coverage report shows `core/` total coverage >= 80%.
    - Each individual file in `core/` shows >= 70% coverage (no single module is a black hole — record exceptions in SUMMARY if any).
    - Manual Step D output: forecast_array[1] within atol=1e-3 of [0.5829, 0.278, 0.0667, 0.0724] (Roadmap SC 1).
    - Manual Step E output: same seed identical=True, diff seed differs=True, dtype=int64 (Roadmap SC 2).
    - Manual Step F output: all 4 "OK" lines printed (Roadmap SC 3).
  </acceptance_criteria>
  <done>
    Coverage ≥ 80% for core/. Roadmap Success Criteria 1, 2, 3, 4 verified via manual REPL checks + automated pytest gate.
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Ruff + mypy clean pass + layer purity check</name>
  <read_first>
    - pyproject.toml (ruff config — 100 char line, target py312; mypy config — non-strict globally per Phase 01 RESEARCH.md)
    - core/ (all modules)
    - scripts/seed_data.py
    - .claude/rules/python-conventions.md (style requirements)
    - .claude/rules/markov-patterns.md (forbidden practices — including #2 legacy RNG)
  </read_first>
  <action>
**Step A: Ruff lint:**
```bash
uv run ruff check core/ scripts/ tests/
```
Must exit 0. Fix any reported issues — typically unused imports, line length, or unsorted imports. Use `uv run ruff check --fix core/ scripts/ tests/` for autofixable lints, then re-run plain `ruff check` to confirm.

**Step B: Ruff format check:**
```bash
uv run ruff format --check core/ scripts/ tests/
```
Must exit 0. If not, run `uv run ruff format core/ scripts/ tests/` and re-verify.

**Step C: Mypy type check on core/:**
```bash
uv run mypy core/
```
Per RESEARCH.md, mypy is NON-strict globally for Phase 01. The command must exit 0 (or with only documented allowances such as `Untyped def` warnings that existed pre-Phase-01). Address any new type errors introduced by Phase 01 implementations.

**Step D: Layer purity check (project rule #12):**
```bash
grep -rn "import streamlit" core/ domains/ || echo "OK — no streamlit in core/ or domains/"
```
Must print "OK". If any match found, refactor to move the Streamlit usage out of core/ and into app/.

**Step E: NumPy modern RNG check (markov-patterns.md forbidden practice #2):**
```bash
grep -rn "np.random.seed" core/ scripts/
```
Must return zero matches. Modern API is `np.random.default_rng(seed)`.

**Step F: Forbidden raw SQL in non-queries paths (data-storage.md rule):**
```bash
grep -rEn "execute\\(.*WHERE|execute\\(.*INSERT INTO" scripts/ | grep -v "queries.py" | grep -v "conn.execute"
```
Manual review: any raw SQL outside `core/db/queries.py` or `core/db/connection.py` should either be in `scripts/seed_data.py` (allowed per data-storage.md exemption for ingestion scripts) or refactored into `core/db/queries.py`. This is an informational check, not a hard fail.
  </action>
  <verify>
    <automated>uv run ruff check core/ scripts/ tests/ && uv run ruff format --check core/ scripts/ tests/ && uv run mypy core/</automated>
  </verify>
  <acceptance_criteria>
    - `uv run ruff check core/ scripts/ tests/` exits 0.
    - `uv run ruff format --check core/ scripts/ tests/` exits 0.
    - `uv run mypy core/` exits 0 (Phase 01 non-strict per RESEARCH.md).
    - `grep -rn "import streamlit" core/ domains/` returns 0 matches.
    - `grep -rn "np.random.seed" core/ scripts/` returns 0 matches.
    - `grep -c "raise NotImplementedError" core/models.py core/simulation.py core/metrics.py core/db/queries.py core/io/loaders.py` returns 2 (the two Phase 02 loader stubs `load_brand_share_csv` and `load_churn_csv` — every Phase 01 stub is implemented).
  </acceptance_criteria>
  <done>
    Code style and type-check clean. Layer purity preserved. No legacy RNG usage. Phase 01 implementation is production-quality.
  </done>
</task>

</tasks>

<verification>
End-of-phase audit one-liner:
```bash
uv run pytest --cov=core --cov-report=term-missing --cov-fail-under=80 -q && \
uv run ruff check core/ scripts/ tests/ && \
uv run ruff format --check core/ scripts/ tests/ && \
uv run mypy core/ && \
test -z "$(grep -rn 'import streamlit' core/ domains/)" && \
test -z "$(grep -rn 'np.random.seed' core/ scripts/)" && \
test -z "$(grep -rn '@pytest.mark.skip' tests/)" && \
echo "Phase 01 closing gate PASSED"
```
Must print `Phase 01 closing gate PASSED`.

Roadmap Success Criteria status:
| SC | Description | Verified by |
|----|-------------|-------------|
| 1 | M1 reproduces Chan 2015 Table 3 in REPL | Plan 02 + Plan 06 Task 2 Step D |
| 2 | monte_carlo_simulate bit-reproducible with seed | Plan 03 + Plan 06 Task 2 Step E |
| 3 | validate_transition_matrix raises on bad input | Plan 02 + Plan 06 Task 2 Step F |
| 4 | core/ coverage > 80%, regression tests green | Plan 06 Task 2 |
| 5 | seed script produces >= 5 forecast rows | Plan 05 + integration tests |
</verification>

<success_criteria>
- pytest --cov=core --cov-fail-under=80 exits 0 (Roadmap SC 4).
- Every Roadmap Success Criterion (1-5) for Phase 01 verified.
- ruff and mypy pass clean.
- Zero `@pytest.mark.skip` in tests/.
- Zero `import streamlit` in core/ or domains/.
- Zero `raise NotImplementedError` in Phase 01 scope (Phase 02 stubs remain in `core/io/loaders.py` for `load_brand_share_csv` and `load_churn_csv` — those are out of scope for Phase 01).
- Phase summary document `01-06-SUMMARY.md` written with final coverage %, test count, and gate pass evidence.
</success_criteria>

<output>
After completion, create `.planning/phases/01-markov-engine/01-06-SUMMARY.md` documenting:
- Coverage breakdown per module (e.g. `core/models.py: 95%, core/simulation.py: 88%, core/metrics.py: 100%`)
- Total test count and pass/skip/fail breakdown
- Verification of all 5 Roadmap Phase 01 Success Criteria with evidence
- All 13 requirement IDs (ENG-01..ENG-10, DATA-01..03) marked complete
- Phase 01 closing statement: "Phase 01 is gate-clean and Phase 02 may proceed."
</output>

---
phase: 01-markov-engine
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tests/unit/test_models.py
  - tests/unit/test_simulation.py
  - tests/unit/test_metrics.py
  - tests/unit/test_serialization.py
  - tests/unit/test_loaders.py
  - tests/integration/test_queries.py
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
    - "Every requirement (ENG-01..ENG-10, DATA-01..03) has at least one named pytest test stub that can be referenced by downstream plans"
    - "All 4 existing tests in tests/unit/test_models.py have their @pytest.mark.skip decorator removed and are blocked only by NotImplementedError, not by skip metadata"
    - "uv run pytest --collect-only tests/ exits 0 listing all newly added test names"
    - "No test file imports a module path that does not exist (collection must succeed)"
  artifacts:
    - path: "tests/unit/test_simulation.py"
      provides: "Skip-annotated stubs for ENG-05, ENG-06, ENG-07, ENG-09"
      contains: "def test_monte_carlo_same_seed_reproducible"
    - path: "tests/unit/test_metrics.py"
      provides: "Skip-annotated stubs for ENG-10 (MAPE, Brier, log-loss)"
      contains: "def test_mape_known_value"
    - path: "tests/unit/test_serialization.py"
      provides: "Skip-annotated stubs for DATA-03 serialization round-trip"
      contains: "def test_ndarray_json_roundtrip"
    - path: "tests/unit/test_loaders.py"
      provides: "Skip-annotated stubs for DATA-01"
      contains: "def test_validate_transitions_df_missing_col"
    - path: "tests/integration/test_queries.py"
      provides: "Skip-annotated integration stubs for DATA-02, DATA-03"
      contains: "def test_build_transition_matrix_normalized"
  key_links:
    - from: "tests/unit/test_models.py"
      to: "core.models.validate_transition_matrix"
      via: "from core.models import"
      pattern: "from core.models import"
    - from: "tests/unit/test_simulation.py"
      to: "core.simulation"
      via: "from core.simulation import"
      pattern: "from core.simulation import"
---

<objective>
Scaffold every test file Phase 01 needs BEFORE any implementation work begins.

Purpose: Implementations in Waves 2-5 must have a named test stub waiting for them so the executor can simply remove `@pytest.mark.skip` after writing the code and re-run pytest. This decouples the Nyquist verification cycle from "scavenger hunt" test-discovery.

Output:
- 5 new test files with skip-annotated stubs covering every requirement
- 1 modified test file (tests/unit/test_models.py) with skips removed from 4 existing tests + 7 new stubs added
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
@tests/conftest.py
@tests/unit/test_models.py
@.claude/rules/markov-patterns.md

<interfaces>
The test stubs in this plan reference these existing fixtures and types (already present, do not redefine):

From tests/conftest.py:
```python
@pytest.fixture
def sample_2x2_matrix() -> np.ndarray:
    return np.array([[0.7, 0.3], [0.4, 0.6]])

@pytest.fixture
def sample_4x4_chan_matrix() -> np.ndarray:
    # Chan 2015 Table 1 — see file for values

@pytest.fixture
def temp_duckdb_path(tmp_path: Path) -> Path:
    return tmp_path / "test.duckdb"
```

From core/exceptions.py (already exists):
```python
class InvalidTransitionMatrixError(MarkovLensError): ...
```

From core/simulation.py (already exists):
```python
@dataclass(frozen=True)
class SimulationResult:
    final_distribution: np.ndarray
    quantile_paths: dict[float, np.ndarray]
    raw_probability: float
    calibrated_probability: float
    n_simulations: int
    n_steps: int
    seed: int | None

LONGSHOT_CALIBRATION: dict[float, float] = { 0.01: 0.0043, 0.05: 0.0418, ... }
```

Modules that downstream tests will import (NOT YET implemented — that is the point of stubs):
```python
from core.models import validate_transition_matrix, M1Homogeneous, M2TimeVarying, M3Extended
from core.simulation import monte_carlo_simulate, calibrate_probability, compute_quantile_bands
from core.metrics import mape, brier_score, log_loss
from core.db.serialization import ndarray_to_json, json_to_ndarray  # NEW MODULE — Wave 3
from core.db.queries import build_transition_matrix
from core.io.loaders import validate_transitions_df  # NEW FUNCTION — Wave 3
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Unskip and extend tests/unit/test_models.py</name>
  <read_first>
    - tests/unit/test_models.py (current 4 skipped tests — KEEP these tests, only remove the skip decorators and add new ones)
    - tests/conftest.py (sample_2x2_matrix, sample_4x4_chan_matrix fixtures)
    - .planning/phases/01-markov-engine/01-RESEARCH.md (section "Phase Requirements → Test Map" — exact test names)
    - .planning/phases/01-markov-engine/01-VALIDATION.md (Wave 0 Requirements section)
  </read_first>
  <action>
Modify `tests/unit/test_models.py` to:

1. **Remove `@pytest.mark.skip(reason="TODO Phase 01 — implementation pending")` from all 4 existing tests** (keep test bodies intact):
   - `test_validate_transition_matrix_accepts_valid`
   - `test_validate_transition_matrix_rejects_non_square`
   - `test_validate_transition_matrix_rejects_unnormalized`
   - `test_m1_forecast_replicates_chan_2015_table3`

   After removal, these 4 tests will FAIL with `NotImplementedError` until Plan 02 implements the functions — that is correct.

2. **Add 7 new skip-annotated test stubs** at the bottom of the file. Use the EXACT names from VALIDATION.md so verification commands match. Each stub body should just be `pass` or a single assertion comment. Add this skip reason on every NEW test: `@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")`.

```python
@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_validate_rejects_negative():
    from core.exceptions import InvalidTransitionMatrixError
    from core.models import validate_transition_matrix
    with pytest.raises(InvalidTransitionMatrixError):
        validate_transition_matrix(np.array([[1.5, -0.5], [0.5, 0.5]]))


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_validate_rejects_wrong_dtype():
    from core.exceptions import InvalidTransitionMatrixError
    from core.models import validate_transition_matrix
    P = np.array([[0.7, 0.3], [0.4, 0.6]], dtype=np.float32)
    with pytest.raises(InvalidTransitionMatrixError):
        validate_transition_matrix(P)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_validate_warns_sparse_cells(caplog):
    from core.models import validate_transition_matrix
    P = np.array([[0.7, 0.3], [0.4, 0.6]])
    counts = np.array([[100, 100], [5, 5]])  # row 1 sparse
    with caplog.at_level("WARNING"):
        validate_transition_matrix(P, transition_counts=counts)
    assert any("sparsity" in r.message.lower() or "sparse" in r.message.lower() for r in caplog.records)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_m1_forecast_shape(sample_2x2_matrix):
    from core.models import M1Homogeneous
    model = M1Homogeneous(P=sample_2x2_matrix)
    Y_1 = np.array([0.6, 0.4])
    result = model.forecast(Y_1=Y_1, horizon=5)
    assert result.forecast_array.shape == (5, 2)
    assert result.model_type == "m1"
    assert result.horizon == 5


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_m2_forecast_shape():
    from core.models import M2TimeVarying
    P_t = np.array([
        [[0.7, 0.3], [0.4, 0.6]],
        [[0.6, 0.4], [0.5, 0.5]],
        [[0.8, 0.2], [0.3, 0.7]],
    ], dtype=np.float64)
    model = M2TimeVarying(P_t_sequence=P_t)
    Y_1 = np.array([0.6, 0.4])
    result = model.forecast(Y_1=Y_1, horizon=3)
    assert result.forecast_array.shape == (3, 2)
    assert result.model_type == "m2"


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_m2_holds_last_pt_at_horizon():
    from core.models import M2TimeVarying
    P_t = np.array([
        [[0.7, 0.3], [0.4, 0.6]],
        [[0.6, 0.4], [0.5, 0.5]],
    ], dtype=np.float64)
    model = M2TimeVarying(P_t_sequence=P_t)
    Y_1 = np.array([0.6, 0.4])
    result_4 = model.forecast(Y_1=Y_1, horizon=4)
    # After step 2, P_t[-1] must be reused — verify by manually computing
    Y2 = Y_1 @ P_t[0]
    Y3 = Y2 @ P_t[1]
    Y4 = Y3 @ P_t[1]  # held last
    Y5 = Y4 @ P_t[1]  # held last
    np.testing.assert_allclose(result_4.forecast_array[3], Y5, atol=1e-9)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_m3_forecast_replicates_chan_2015(sample_4x4_chan_matrix):
    """Verify M3 forecast matches Chan 2015 m3 table within reasonable tolerance.

    From RESEARCH.md Code Examples:
    G = [1.0315, 1.0561, 0.9029, 1.0897]
    Q_1 = [0.5878, 0.2830, 0.0585, 0.0708]
    Expected at t=2: [0.5799, 0.2847, 0.0603, 0.0751] (per docs/MARKOV-MODELS.md m3 table)
    """
    from core.models import M3Extended
    P_t = np.tile(sample_4x4_chan_matrix[None, :, :], (5, 1, 1))  # repeat 5 times
    G = np.array([1.0315, 1.0561, 0.9029, 1.0897])
    Q_1 = np.array([0.5878, 0.2830, 0.0585, 0.0708])
    model = M3Extended(P_t_sequence=P_t, G=G)
    result = model.forecast(Q_1=Q_1, horizon=5)
    expected_t2 = np.array([0.5799, 0.2847, 0.0603, 0.0751])
    np.testing.assert_allclose(result.forecast_array[0], expected_t2, atol=1e-2)
```

**IMPORTANT:** the existing 4 tests are NOT changed in body — only the skip decorator is removed. The 7 NEW tests are skip-annotated so collection passes cleanly.
  </action>
  <verify>
    <automated>uv run pytest tests/unit/test_models.py --collect-only -q</automated>
  </verify>
  <acceptance_criteria>
    - `tests/unit/test_models.py` collection lists exactly 11 tests (4 existing + 7 new): `test_validate_transition_matrix_accepts_valid`, `test_validate_transition_matrix_rejects_non_square`, `test_validate_transition_matrix_rejects_unnormalized`, `test_m1_forecast_replicates_chan_2015_table3`, `test_validate_rejects_negative`, `test_validate_rejects_wrong_dtype`, `test_validate_warns_sparse_cells`, `test_m1_forecast_shape`, `test_m2_forecast_shape`, `test_m2_holds_last_pt_at_horizon`, `test_m3_forecast_replicates_chan_2015`. Acceptance: count of collected items in test_models.py == 11.
    - `grep -c "@pytest.mark.skip(reason=\"TODO Phase 01" tests/unit/test_models.py` returns 0 (the original skip marker text is gone from all 4 existing tests).
    - `grep -c "@pytest.mark.skip(reason=\"Wave 0 stub" tests/unit/test_models.py` returns 7 (the 7 new stubs all carry the Wave 0 marker — test_validate_rejects_negative, test_validate_rejects_wrong_dtype, test_validate_warns_sparse_cells, test_m1_forecast_shape, test_m2_forecast_shape, test_m2_holds_last_pt_at_horizon, test_m3_forecast_replicates_chan_2015).
    - `uv run pytest tests/unit/test_models.py --collect-only -q` exits 0 (no import errors during collection).
  </acceptance_criteria>
  <done>
    Test file collects 11 tests total. 4 existing tests are no longer skipped (will fail with NotImplementedError until Plan 02). 7 new tests are skip-annotated and will be un-skipped wave-by-wave.
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Create tests/unit/test_simulation.py, test_metrics.py, test_loaders.py, test_serialization.py</name>
  <read_first>
    - tests/conftest.py (fixture names)
    - core/simulation.py (SimulationResult dataclass and LONGSHOT_CALIBRATION values)
    - core/metrics.py (mape, brier_score, log_loss signatures + docstring examples)
    - .planning/phases/01-markov-engine/01-RESEARCH.md (section "Phase Requirements → Test Map" — exact test names)
  </read_first>
  <action>
Create 4 new test files. Every test starts with `@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")` so collection passes.

**File 1: `tests/unit/test_simulation.py`** (covers ENG-05, ENG-06, ENG-07, ENG-09)

```python
"""Stubs for Monte Carlo, calibration, quantile bands, walk-forward backtest."""
from __future__ import annotations

import numpy as np
import pytest


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_monte_carlo_same_seed_reproducible(sample_2x2_matrix):
    from core.simulation import monte_carlo_simulate
    P = sample_2x2_matrix.astype(np.float64)
    paths_a = monte_carlo_simulate(P, start_state=0, n_steps=10, n_simulations=1_000, seed=42)
    paths_b = monte_carlo_simulate(P, start_state=0, n_steps=10, n_simulations=1_000, seed=42)
    np.testing.assert_array_equal(paths_a, paths_b)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_monte_carlo_different_seeds_differ(sample_2x2_matrix):
    from core.simulation import monte_carlo_simulate
    P = sample_2x2_matrix.astype(np.float64)
    paths_a = monte_carlo_simulate(P, start_state=0, n_steps=10, n_simulations=1_000, seed=42)
    paths_c = monte_carlo_simulate(P, start_state=0, n_steps=10, n_simulations=1_000, seed=7)
    assert not np.array_equal(paths_a, paths_c)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_monte_carlo_output_shape(sample_2x2_matrix):
    from core.simulation import monte_carlo_simulate
    P = sample_2x2_matrix.astype(np.float64)
    paths = monte_carlo_simulate(P, start_state=0, n_steps=12, n_simulations=500, seed=1)
    assert paths.shape == (500, 13)  # n_steps + 1


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_monte_carlo_dtype_int64(sample_2x2_matrix):
    from core.simulation import monte_carlo_simulate
    P = sample_2x2_matrix.astype(np.float64)
    paths = monte_carlo_simulate(P, start_state=0, n_steps=5, n_simulations=100, seed=1)
    assert paths.dtype == np.int64


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_monte_carlo_accepts_distribution_start():
    """D-13: start_state may be an np.ndarray initial distribution."""
    from core.simulation import monte_carlo_simulate
    P = np.array([[0.7, 0.3], [0.4, 0.6]], dtype=np.float64)
    init_dist = np.array([0.5, 0.5])
    paths = monte_carlo_simulate(P, start_state=init_dist, n_steps=5, n_simulations=2_000, seed=42)
    initial_states = paths[:, 0]
    # With seed=42, roughly half the paths should start in each state
    state_0_frac = (initial_states == 0).mean()
    assert 0.4 < state_0_frac < 0.6


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_monte_carlo_no_drift_to_zero_for_last_state():
    """D-12 regression: cum_matrix[:, -1] = 1.0 fix must keep last state reachable."""
    from core.simulation import monte_carlo_simulate
    # Matrix where state 0 -> state 2 has nonzero probability
    P = np.array([
        [0.5, 0.3, 0.2],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=np.float64)
    paths = monte_carlo_simulate(P, start_state=0, n_steps=1, n_simulations=10_000, seed=42)
    next_states = paths[:, 1]
    # Last state (index 2) must be reachable with probability ~0.2
    state_2_frac = (next_states == 2).mean()
    assert state_2_frac > 0.15


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_calibrate_anchor_points():
    from core.simulation import calibrate_probability
    assert calibrate_probability(0.05) == pytest.approx(0.0418, abs=1e-6)
    assert calibrate_probability(0.50) == pytest.approx(0.500, abs=1e-6)
    assert calibrate_probability(0.95) == pytest.approx(0.958, abs=1e-6)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_calibrate_interpolates():
    from core.simulation import calibrate_probability
    midpoint = calibrate_probability(0.025)
    assert midpoint == pytest.approx((0.0043 + 0.0418) / 2, abs=1e-3)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_calibrate_boundary_clamps():
    from core.simulation import calibrate_probability
    assert calibrate_probability(0.0) == pytest.approx(0.0043, abs=1e-6)
    assert calibrate_probability(1.0) == pytest.approx(0.958, abs=1e-6)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_quantile_bands_shape():
    from core.simulation import compute_quantile_bands
    paths = np.random.default_rng(42).integers(0, 4, size=(1000, 13))
    bands = compute_quantile_bands(paths, target_extractor=lambda p: p.astype(np.float64))
    assert 0.10 in bands and 0.50 in bands and 0.90 in bands
    assert bands[0.50].shape == (13,)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_quantile_bands_target_extractor_applied():
    """ENG-07: target_extractor must be applied BEFORE percentile, not after."""
    from core.simulation import compute_quantile_bands
    paths = np.array([[0, 1, 2], [1, 2, 3], [2, 3, 4]], dtype=np.int64)
    bands = compute_quantile_bands(paths, target_extractor=lambda p: p * 2.0, quantiles=(0.5,))
    np.testing.assert_allclose(bands[0.5], [2.0, 4.0, 6.0])


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_walk_forward_no_leakage():
    """ENG-09: backtest must only use past data to fit matrix at each step."""
    from core.simulation import walk_forward_backtest
    import pandas as pd
    df = pd.DataFrame({
        "period": list(range(1, 13)),
        "from_state": ["A"] * 6 + ["B"] * 6,
        "to_state":   ["A"] * 5 + ["B"] * 7,
        "entity_id":  ["e1"] * 12,
        "dataset_id": ["ds_test"] * 12,
        "weight":     [1.0] * 12,
    })
    results = walk_forward_backtest(df, window=3)
    assert isinstance(results, list)
    assert len(results) > 0
    assert all("period" in r for r in results)
```

**File 2: `tests/unit/test_metrics.py`** (covers ENG-10)

```python
"""Stubs for MAPE, Brier score, log-loss."""
from __future__ import annotations

import numpy as np
import pytest


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_mape_known_value():
    from core.metrics import mape
    actual = np.array([100.0, 200.0])
    forecast = np.array([110.0, 190.0])
    # (|10|/100 + |10|/200) / 2 * 100 = (0.1 + 0.05) / 2 * 100 = 7.5
    assert mape(actual, forecast) == pytest.approx(7.5, abs=1e-9)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_mape_skips_zero_actual(caplog):
    from core.metrics import mape
    actual = np.array([0.0, 100.0, 200.0])
    forecast = np.array([5.0, 110.0, 190.0])
    with caplog.at_level("WARNING"):
        result = mape(actual, forecast)
    # only rows 1 and 2 counted: (10/100 + 10/200)/2 * 100 = 7.5
    assert result == pytest.approx(7.5, abs=1e-9)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_brier_known_value():
    from core.metrics import brier_score
    forecast_prob = np.array([[0.7, 0.3], [0.4, 0.6]])
    actual = np.array([[1, 0], [0, 1]])
    # ((0.7-1)^2 + (0.3-0)^2)/2 + ((0.4-0)^2 + (0.6-1)^2)/2 — then mean
    # = (0.09 + 0.09)/2 + (0.16 + 0.16)/2 = 0.09 + 0.16 = 0.25 — mean over rows = 0.125
    assert brier_score(forecast_prob, actual) == pytest.approx(0.125, abs=1e-6)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_log_loss_known_value():
    from core.metrics import log_loss
    forecast_prob = np.array([[0.9, 0.1], [0.2, 0.8]])
    actual = np.array([[1, 0], [0, 1]])
    # -mean(log(0.9) + log(0.8))
    expected = -(np.log(0.9) + np.log(0.8)) / 2
    assert log_loss(forecast_prob, actual) == pytest.approx(expected, abs=1e-6)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_log_loss_clips_zeros():
    from core.metrics import log_loss
    forecast_prob = np.array([[1.0, 0.0]])
    actual = np.array([[0, 1]])  # predicted prob 0 for true class
    result = log_loss(forecast_prob, actual)
    assert np.isfinite(result)  # must not blow up to inf
```

**File 3: `tests/unit/test_loaders.py`** (covers DATA-01)

```python
"""Stubs for core/io/loaders.py validate_transitions_df."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_validate_transitions_df_missing_col():
    from core.io.loaders import validate_transitions_df
    df = pd.DataFrame({"entity_id": ["a"], "period": [1], "from_state": ["x"]})
    # missing 'to_state'
    with pytest.raises(ValueError, match="to_state"):
        validate_transitions_df(df)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_validate_transitions_df_accepts_valid():
    from core.io.loaders import validate_transitions_df
    df = pd.DataFrame({
        "entity_id": ["a", "b"],
        "period":    [1, 1],
        "from_state":["x", "y"],
        "to_state":  ["y", "x"],
    })
    validate_transitions_df(df)  # should not raise


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_validate_transitions_df_rejects_nan_entity():
    from core.io.loaders import validate_transitions_df
    df = pd.DataFrame({
        "entity_id": [np.nan, "b"],
        "period":    [1, 1],
        "from_state":["x", "y"],
        "to_state":  ["y", "x"],
    })
    with pytest.raises(ValueError):
        validate_transitions_df(df)
```

**File 4: `tests/unit/test_serialization.py`** (covers DATA-03 serialization)

```python
"""Stubs for core/db/serialization.py ndarray↔JSON helpers."""
from __future__ import annotations

import numpy as np
import pytest


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_ndarray_json_roundtrip():
    from core.db.serialization import ndarray_to_json, json_to_ndarray
    arr = np.array([[0.1, 0.9], [0.5, 0.5]], dtype=np.float64)
    s = ndarray_to_json(arr)
    arr_back = json_to_ndarray(s)
    np.testing.assert_array_equal(arr, arr_back)
    assert arr_back.dtype == np.float64


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_ndarray_json_roundtrip_3d():
    from core.db.serialization import ndarray_to_json, json_to_ndarray
    arr = np.random.default_rng(42).random((4, 3, 3))
    s = ndarray_to_json(arr)
    arr_back = json_to_ndarray(s)
    np.testing.assert_allclose(arr, arr_back)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_serializer_rejects_nan():
    from core.db.serialization import ndarray_to_json
    arr = np.array([0.5, np.nan, 0.5])
    with pytest.raises(ValueError, match="NaN|Inf"):
        ndarray_to_json(arr)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_serializer_rejects_inf():
    from core.db.serialization import ndarray_to_json
    arr = np.array([0.5, np.inf, 0.5])
    with pytest.raises(ValueError, match="NaN|Inf"):
        ndarray_to_json(arr)
```
  </action>
  <verify>
    <automated>uv run pytest tests/unit/test_simulation.py tests/unit/test_metrics.py tests/unit/test_loaders.py tests/unit/test_serialization.py --collect-only -q</automated>
  </verify>
  <acceptance_criteria>
    - File `tests/unit/test_simulation.py` exists and contains `def test_monte_carlo_same_seed_reproducible`, `def test_monte_carlo_no_drift_to_zero_for_last_state` (D-12 regression), `def test_calibrate_anchor_points`, `def test_quantile_bands_target_extractor_applied`, `def test_walk_forward_no_leakage`.
    - File `tests/unit/test_metrics.py` exists and contains `def test_mape_known_value`, `def test_mape_skips_zero_actual`, `def test_brier_known_value`, `def test_log_loss_known_value`, `def test_log_loss_clips_zeros`.
    - File `tests/unit/test_loaders.py` exists and contains `def test_validate_transitions_df_missing_col`, `def test_validate_transitions_df_accepts_valid`, `def test_validate_transitions_df_rejects_nan_entity`.
    - File `tests/unit/test_serialization.py` exists and contains `def test_ndarray_json_roundtrip`, `def test_serializer_rejects_nan`, `def test_serializer_rejects_inf`.
    - Every test in these 4 files carries `@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")`. Verify via: `grep -c "@pytest.mark.skip(reason=\"Wave 0 stub" tests/unit/test_simulation.py tests/unit/test_metrics.py tests/unit/test_loaders.py tests/unit/test_serialization.py` returns >= 22 (the total stub count across all four files).
    - `uv run pytest tests/unit/test_simulation.py tests/unit/test_metrics.py tests/unit/test_loaders.py tests/unit/test_serialization.py --collect-only -q` exits 0 (no collection-time import errors despite implementations being missing — imports are inside test bodies, deferred until skip clears).
  </acceptance_criteria>
  <done>
    All 4 new unit test files exist with skip-annotated stubs. pytest can collect them without errors. Every stub references the correct function path that Wave 2-3 implementations will provide.
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Create tests/integration/test_queries.py</name>
  <read_first>
    - tests/conftest.py (temp_duckdb_path fixture)
    - core/db/schema.sql (verify table column names referenced in tests are correct)
    - core/db/connection.py (init_schema function signature)
    - pyproject.toml (verify `integration` marker is declared)
    - .planning/phases/01-markov-engine/01-VALIDATION.md (integration test names)
  </read_first>
  <action>
Create `tests/integration/test_queries.py` covering DATA-02 (seed idempotency) and DATA-03 (build_transition_matrix integration). Every test must use `@pytest.mark.integration` AND `@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")`.

```python
"""Integration tests for core/db/queries.py and seed script paths."""
from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pytest


@pytest.mark.integration
@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_build_transition_matrix_normalized(temp_duckdb_path: Path):
    """DATA-03: matrix returned must have rows summing to 1.0."""
    from core.db.connection import init_schema
    from core.db.queries import build_transition_matrix

    conn = duckdb.connect(str(temp_duckdb_path))
    init_schema(conn)
    conn.execute(
        "INSERT INTO datasets (id, domain, name, source_path, row_count, n_states) "
        "VALUES ('ds_test', 'churn', 'test', 'test.csv', 4, 2)"
    )
    conn.execute("INSERT INTO transitions VALUES "
                 "('ds_test','e1',1,'A','A',1.0), "
                 "('ds_test','e1',1,'A','B',1.0), "
                 "('ds_test','e2',1,'B','A',1.0), "
                 "('ds_test','e2',1,'B','B',3.0)")
    matrix, counts = build_transition_matrix(conn, dataset_id="ds_test")
    assert matrix.shape == (2, 2)
    np.testing.assert_allclose(matrix.sum(axis=1), [1.0, 1.0], atol=1e-9)
    conn.close()


@pytest.mark.integration
@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_build_transition_matrix_counts(temp_duckdb_path: Path):
    """DATA-03: counts array returned with correct values."""
    from core.db.connection import init_schema
    from core.db.queries import build_transition_matrix

    conn = duckdb.connect(str(temp_duckdb_path))
    init_schema(conn)
    conn.execute(
        "INSERT INTO datasets (id, domain, name, source_path, row_count, n_states) "
        "VALUES ('ds_test', 'churn', 'test', 'test.csv', 4, 2)"
    )
    conn.execute("INSERT INTO transitions VALUES "
                 "('ds_test','e1',1,'A','A',7.0), "
                 "('ds_test','e1',1,'A','B',3.0), "
                 "('ds_test','e2',1,'B','A',4.0), "
                 "('ds_test','e2',1,'B','B',6.0)")
    matrix, counts = build_transition_matrix(conn, dataset_id="ds_test")
    assert counts.shape == (2, 2)
    assert counts.sum() == 20
    conn.close()


@pytest.mark.integration
@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_build_transition_matrix_filters_dataset(temp_duckdb_path: Path):
    """DATA-03: only rows matching dataset_id are aggregated."""
    from core.db.connection import init_schema
    from core.db.queries import build_transition_matrix

    conn = duckdb.connect(str(temp_duckdb_path))
    init_schema(conn)
    conn.execute(
        "INSERT INTO datasets (id, domain, name, source_path, row_count, n_states) "
        "VALUES ('ds_a', 'churn', 'a', 'a.csv', 2, 2), "
        "('ds_b', 'churn', 'b', 'b.csv', 2, 2)"
    )
    conn.execute("INSERT INTO transitions VALUES "
                 "('ds_a','e1',1,'A','A',1.0), "
                 "('ds_a','e1',1,'A','B',1.0), "
                 "('ds_b','e2',1,'A','A',99.0)")
    matrix, counts = build_transition_matrix(conn, dataset_id="ds_a")
    assert counts.sum() == 2  # not 101
    conn.close()


@pytest.mark.integration
@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_seed_idempotency(temp_duckdb_path: Path, monkeypatch):
    """DATA-02: running seed twice produces identical row counts (D-23)."""
    monkeypatch.setenv("DUCKDB_PATH", str(temp_duckdb_path))
    # Reload settings so DUCKDB_PATH change takes effect
    import importlib
    from core import config as cfg
    importlib.reload(cfg)
    from core.db import connection as cn
    importlib.reload(cn)
    cn.close_connection()

    from scripts import seed_data
    seed_data.main()
    conn1 = duckdb.connect(str(temp_duckdb_path))
    count_a_transitions = conn1.execute("SELECT COUNT(*) FROM transitions").fetchone()[0]
    count_a_forecasts = conn1.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]
    conn1.close()

    cn.close_connection()
    seed_data.main()
    conn2 = duckdb.connect(str(temp_duckdb_path))
    count_b_transitions = conn2.execute("SELECT COUNT(*) FROM transitions").fetchone()[0]
    count_b_forecasts = conn2.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]
    conn2.close()

    assert count_a_transitions == count_b_transitions
    assert count_a_forecasts == count_b_forecasts


@pytest.mark.integration
@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_seed_produces_reference_forecasts(temp_duckdb_path: Path, monkeypatch):
    """DATA-02: forecasts table populated with >= 5 rows after seed (cold-start KPI requirement)."""
    monkeypatch.setenv("DUCKDB_PATH", str(temp_duckdb_path))
    import importlib
    from core import config as cfg
    importlib.reload(cfg)
    from core.db import connection as cn
    importlib.reload(cn)
    cn.close_connection()

    from scripts import seed_data
    seed_data.main()

    conn = duckdb.connect(str(temp_duckdb_path))
    count = conn.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]
    conn.close()
    assert count >= 5
```

Note: `tests/integration/__init__.py` already exists (verified — `tests\integration\__init__.py` is in the glob output). Do not recreate.

**Verify the `integration` marker is registered** in `pyproject.toml`:
```bash
grep -A 5 "ini_options" pyproject.toml | grep -i "markers\|integration"
```
If `integration` marker is not declared in `[tool.pytest.ini_options].markers`, add it. The codebase TESTING.md confirms this marker is in use.
  </action>
  <verify>
    <automated>uv run pytest tests/integration/test_queries.py --collect-only -q</automated>
  </verify>
  <acceptance_criteria>
    - File `tests/integration/test_queries.py` exists.
    - File contains exactly 5 test functions: `test_build_transition_matrix_normalized`, `test_build_transition_matrix_counts`, `test_build_transition_matrix_filters_dataset`, `test_seed_idempotency`, `test_seed_produces_reference_forecasts`.
    - Every test is decorated with BOTH `@pytest.mark.integration` AND `@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")`. Verify via: `grep -c "@pytest.mark.integration" tests/integration/test_queries.py` returns 5 AND `grep -c "@pytest.mark.skip(reason=\"Wave 0 stub" tests/integration/test_queries.py` returns 5.
    - `uv run pytest tests/integration/test_queries.py --collect-only -q` exits 0 (no collection-time errors).
    - `uv run pytest tests/integration/test_queries.py -m integration -q` reports `5 skipped` (proves integration marker is recognized).
  </acceptance_criteria>
  <done>
    Integration test file scaffolded with 5 skip-annotated stubs. DATA-02 and DATA-03 verification paths are named and will be activated by Plans 04 and 05.
  </done>
</task>

</tasks>

<verification>
Run after every task: `uv run pytest tests/ --collect-only -q` — must exit 0.

Full plan completion check:
```bash
uv run pytest tests/ -m "not slow" -q
```
Expected: ~30 tests skipped (Wave 0 stubs), 4 tests fail (existing un-skipped tests blocked by NotImplementedError — that is the desired state, not a regression).

Coverage gate not yet applicable — implementations land in Plans 02-05.
</verification>

<success_criteria>
- Every requirement (ENG-01..ENG-10, DATA-01..03) has at least one named test stub referencing the function it will eventually test.
- All Wave 0 test files declared in VALIDATION.md `Wave 0 Requirements` checklist exist on disk.
- `tests/unit/test_models.py` original 4 tests have NO skip marker; they fail with NotImplementedError (expected — Plan 02 lifts that).
- `uv run pytest tests/ --collect-only` exits 0 (collection passes — no test file has an import error blocking discovery).
</success_criteria>

<output>
After completion, create `.planning/phases/01-markov-engine/01-01-SUMMARY.md` documenting:
- Files created (with paths)
- Test stub counts per file
- Confirmation that 4 existing tests are now un-skipped
- Note: subsequent plans (02-05) lift `@pytest.mark.skip(reason="Wave 0 stub...")` from the corresponding stub when implementing the function.
</output>

# Architecture Research

**Project:** MarkovLens
**Researched:** 2026-05-29
**Overall confidence:** HIGH — based on direct codebase analysis; all claims grounded in the scaffolded code at `core/`, `domains/`, `tests/`, and the schema at `core/db/schema.sql`.

---

## Summary

MarkovLens has a well-structured 3-layer architecture that is fully scaffolded but ~0% implemented in the logic layer. The critical path is Phase 01 (core engine) because every downstream layer — domain services, Streamlit pages, DB caching, and tests — depends on `validate_transition_matrix()` and the three `forecast()` methods being functional. Within Phase 01 itself, there is a strict internal dependency order: validation must come before models, models before simulation, and simulation before metrics. Domain services and UI pages can be built in parallel once core is working, but each domain's service must be wired to core before its UI page can be useful. The two architectural risks that need most attention are the DuckDB singleton in a Streamlit multi-page context (race-free because Streamlit is single-threaded, but the module-level global breaks test isolation unless `close_connection()` is called), and the JSON column serialization contract between `simulation_runs` / `transition_matrices` and the NumPy arrays stored in them.

---

## Build Order Recommendation

### Phase 01 — Core Engine (must be strictly sequential internally)

**Step 1: validate_transition_matrix() first, alone.**
Every model constructor calls it on `__init__`. Until it's implemented, `M1Homogeneous(P)`, `M2TimeVarying(P_list)`, and `M3Extended(P_list, G)` all explode before reaching the `forecast()` stub. This is not just a logical dependency — it is a Python import-time crash. No test in `test_models.py` can even execute `from core.models import M1Homogeneous` followed by construction without it.

Implementation note: raise `InvalidTransitionMatrixError` (already in `core/exceptions.py`), not `AssertionError`. Tests at lines 16–22 in `test_models.py` expect `InvalidTransitionMatrixError`. The sparsity check (counts parameter) should emit a warning via `logging.warning()` rather than raising — sparse data is a signal, not a hard error for all callers.

**Step 2: M1Homogeneous.forecast() — the foundational model.**
M1 is Y_{t+1} = Y_1 · P^t. This is a single matrix power call: `scipy.linalg.matrix_power(P, t)` or iterative `np.dot`. The Chan 2015 Table 3 test in `test_models.py` gives an exact ground-truth regression test. Implement M1 first, unlock that test, and use it as the validation anchor for M2 and M3.

**Step 3: M2TimeVarying.forecast() — extend M1.**
M2 is Y_{t+1} = Y_1 · ∏ P_t (product of time-varying matrices). M2 reduces to M1 if all P_t are identical. Build M2 on top of the same matrix-product machinery used in M1 rather than from scratch.

**Step 4: M3Extended.forecast() — extend M2.**
M3 adds element-wise growth: Q_{t+1} = (G ⊙ Q_t) · P_t. G is a per-state growth multiplier vector. This requires re-normalization after each step because applying G breaks row-sum = 1. This is the only model where the "state vector" is a population count, not a probability distribution — do not confuse them.

**Step 5: monte_carlo_simulate() + calibrate_probability() + compute_quantile_bands().**
These depend only on a valid transition matrix input, not on the forecast classes. They can be implemented in parallel with Step 3–4, but the test suite skips are in `test_models.py` only — there are no simulation unit tests yet. Add them to `tests/unit/test_simulation.py` (new file needed).

**Step 6: build_transition_matrix() in core/db/queries.py.**
This is the DuckDB GROUP BY → NumPy path. It depends on `validate_transition_matrix()` (Step 1) for post-build validation. It also depends on the `transitions` table existing with the correct schema. Implement after Steps 1–5 so it can be immediately validated with real data.

**Step 7: core/metrics.py — MAPE, Brier, log-loss.**
Depends on having working forecasts to measure against. Implement last in Phase 01. The walk-forward backtest function also belongs here conceptually (it assembles forecasts and metrics together).

**Phase 01 internal dependency order:**
```
validate_transition_matrix()
    ↓
M1Homogeneous.forecast()
    ↓
M2TimeVarying.forecast()
    ↓
M3Extended.forecast()

(parallel track):
monte_carlo_simulate()
    → calibrate_probability()
    → compute_quantile_bands()

(after all above):
build_transition_matrix() [queries.py]
core/io/loaders.py + scripts/seed_data.py
core/metrics.py + walk_forward_backtest()
```

### Phase 02 — Brand Share UI (mostly parallel after core is done)

**Must be sequential:**
1. `domains/brand_share/service.py` — wire `run_forecast()` to core. Must come before any UI work.
2. `app/styles/plotly_theme.py` — must exist before chart components are built, so charts are themed from the start rather than retroactively restyled.
3. `app/pages/1_Brand_Share.py` — the page. Builds on service and theme.

**Can be done in any order within the page build:**
- Transition matrix heatmap component
- Monte Carlo fan chart component
- KPI strip (already has `kpi_card.py` stub)
- Model comparison tab

The `app/Home.py` dashboard KPI wiring (currently a placeholder) should also happen in Phase 02, since it reads from the `forecasts` and `simulation_runs` tables which only get populated when brand share forecasting runs.

**Dataset seeding (scripts/seed_data.py) must be done before any real UI testing.** The UI can be built against mocked/hardcoded data but must be validated with real Kaggle CSVs before the phase is considered done.

### Phase 03 — Churn UI (same pattern as Phase 02, independent)

`domains/churn/service.py` → `app/pages/2_Churn.py`. The Sankey diagram is the visually distinguishing component. The what-if simulator (`simulate_scenario()`) is the highest-complexity piece because it requires a UI slider panel that modifies transition probabilities and re-runs forecast in near real-time — implement the basic Sankey view first, add the what-if panel as a second pass within the phase.

**Phases 02 and 03 can run in parallel** if there are two developers. For a solo developer, Phase 02 first is lower risk because Brand Share maps more directly to the core engine's output types (ForecastResult, confidence bands) while the Churn Sankey requires additional data wrangling for the flow representation.

---

## Core Engine Design

### Model abstraction: separate classes, not a base class

The three classes already defined (`M1Homogeneous`, `M2TimeVarying`, `M3Extended`) are the right abstraction. Do NOT introduce an abstract base class. The reasons:

1. The three models have incompatible constructor signatures. M1 takes a single `TransitionMatrix`; M2 takes a `list[TransitionMatrix]`; M3 takes a `list[TransitionMatrix]` plus a `np.ndarray` growth vector. A shared `__init__` would either be wrong or force artificial uniformity.
2. The `forecast()` method signatures differ by return semantics: M1/M2 return probability distributions (shares), M3 returns population counts. A shared abstract `forecast()` would paper over a meaningful semantic difference.
3. The existing `ForecastResult` dataclass already provides a uniform output contract. The service layer in `domains/brand_share/service.py` can dispatch to the right class based on `model_type: str` parameter, which is cleaner than polymorphism here.

**Dispatch pattern in the service layer:**
```python
def _build_model(model_type: str, matrices: list[np.ndarray], G: np.ndarray | None):
    if model_type == "m1":
        return M1Homogeneous(matrices[0])
    elif model_type == "m2":
        return M2TimeVarying(matrices)
    elif model_type == "m3":
        if G is None:
            raise UnsupportedModelError("M3 requires a growth vector G")
        return M3Extended(matrices, G)
    raise UnsupportedModelError(f"Unknown model_type: {model_type!r}")
```

### build_transition_matrix() — DuckDB GROUP BY approach

The right implementation is a two-step SQL + NumPy pipeline:

**Step 1 (SQL):** Aggregate raw transitions to counts per `(from_state, to_state)`. DuckDB GROUP BY on an indexed column set is columnar and very fast even for millions of rows.

```sql
SELECT from_state, to_state, SUM(weight) AS n
FROM transitions
WHERE dataset_id = ?
  AND (period BETWEEN ? AND ? OR ? IS NULL)
GROUP BY from_state, to_state
ORDER BY from_state, to_state
```

**Step 2 (NumPy):** Pivot the result into an (n_states × n_states) counts matrix, normalize rows, then run sparsity detection and `validate_transition_matrix()`.

The state label-to-index mapping must be deterministic. Build it from `datasets.metadata_json` or, if not present, from the sorted unique values of `from_state` and `to_state` combined. Store the mapping alongside the matrix in `transition_matrices.matrix_json` (as `{"labels": [...], "matrix": [[...]]}`).

**Critical implementation note:** `from_state` and `to_state` in the schema are `VARCHAR`, not integers. The state-to-index mapping is not implicit — it must be an explicit sorted list stored in the matrix JSON. This becomes important when deserializing from cache; the labels array must always be deserialized together with the matrix values.

For time-varying (M2/M3): run the GROUP BY with a `period = ?` filter for each time step, producing one matrix per period. The sequence of matrices becomes the `P_t_sequence` list passed to `M2TimeVarying` or `M3Extended`.

### Monte Carlo architecture for Streamlit Cloud (1GB RAM)

The existing `monte_carlo_simulate()` signature is correct. The implementation must be vectorized — no Python loop over simulations.

**Recommended implementation (fully vectorized via inverse-CDF):**

```python
def monte_carlo_simulate(matrix, start_state, n_steps=12, n_simulations=10_000, seed=42):
    rng = np.random.default_rng(seed)
    n_states = matrix.shape[0]
    
    # Precompute cumulative sum rows for inverse-CDF sampling
    cdf = np.cumsum(matrix, axis=1)  # shape (n_states, n_states)
    
    # All paths, all steps in one array
    paths = np.empty((n_simulations, n_steps + 1), dtype=np.int32)
    paths[:, 0] = start_state
    
    for step in range(n_steps):
        current_states = paths[:, step]             # shape (n_simulations,)
        u = rng.random(n_simulations)               # uniform samples
        # Vectorized: for each sim, find argmax of cdf[state] > u
        paths[:, step + 1] = (cdf[current_states] > u[:, None]).argmax(axis=1)
    
    return paths
```

**Memory analysis for Streamlit Cloud:**
- `paths` array: 10,000 sims × 13 steps × 4 bytes (int32) = 520 KB. Trivial.
- `cdf` array: 10 states × 10 states × 8 bytes (float64) = 800 bytes. Trivial.
- `u` per step: 10,000 × 8 bytes = 80 KB per step allocation. GC'd immediately.
- Peak intermediate: `cdf[current_states]` broadcast is 10,000 × 10 × 8 bytes = 800 KB.

Total peak: well under 5 MB for default parameters. Even at 30 states and 24 steps, peak stays under 200 MB. **No memory risk on 1GB Streamlit Cloud.**

The loop over `n_steps` (12–24 iterations) is unavoidable because step t+1 depends on step t. This is not a performance bottleneck — 24 iterations of vectorized NumPy ops over 10k rows is sub-millisecond.

**Do NOT use the pattern of running 10,000 separate Python `rng.choice()` loops.** That is 100–1000x slower and would make cold starts noticeable.

`@st.cache_data` on the calling service function handles the Streamlit side. The DB-level `simulation_runs` cache handles repeated identical requests across sessions.

---

## DuckDB Caching Strategy

### Two-level caching

The schema defines two caches: `transition_matrices` and `simulation_runs`. They serve different purposes and need different invalidation logic.

**Level 1 — transition_matrices cache**

Cache key: `(dataset_id, model_type, period)` — already indexed in the schema.

Invalidation triggers:
- New rows inserted into `transitions` for the same `dataset_id`. Simplest detection: store a `row_count_at_cache_time` field in `transition_matrices`. Compare against current `COUNT(*)` in `transitions WHERE dataset_id = ?` before serving cache. If count changed, recompute.
- `model_type` changes are a different key, not an invalidation event.
- For M1 (single aggregate matrix): `period = NULL` is the cache key. For M2/M3 (per-period matrices): each period gets its own row.

**The schema already has `n_observations INTEGER`** — use this as the row count sentinel. On lookup, if `n_observations != current_count`, treat as cache miss and recompute.

**Level 2 — simulation_runs cache**

Cache key: `matrix_id` (FK to `transition_matrices.id`) + `start_state` + `n_steps` + `n_simulations` + `seed`.

Invalidation: purely by `matrix_id` — if the parent matrix is recomputed (new row with new ID), the simulation cache for the old matrix_id becomes orphaned but not invalid (still correct for historical queries). No explicit deletion needed; just query for the latest `matrix_id` for a given `(dataset_id, model_type)`.

**The calibration table versioning gap** (noted in CONCERNS.md) is a real risk. The `simulation_runs` table has no `calibration_version` column. If `LONGSHOT_CALIBRATION` is ever updated, old cached `calibrated_probability` values become stale silently. Mitigation: add a `calibration_hash VARCHAR` column to `simulation_runs` that stores a short hash of the calibration dict. On read, compare against the current hash; if mismatch, recompute calibrated probability (the raw simulation can be reused — only the calibration step needs to re-run, which is microseconds).

### When to skip DuckDB cache entirely

Use Streamlit-level `@st.cache_data` as the primary cache for any given user session. DuckDB caching is only needed for cross-session persistence. The pattern:

```python
@st.cache_data
def get_forecast(dataset_id: str, model_type: str, horizon: int) -> ForecastResult:
    # This is the hot path — only runs once per session per unique input combo
    return service.run_forecast(dataset_id, model_type, horizon)
```

The domain service layer is responsible for consulting the DuckDB cache before calling `core/models.py`. The page layer never touches DuckDB directly — it calls the service, which handles cache lookup/write internally.

### Recommended cache lookup flow in service.py

```
1. Check simulation_runs in DuckDB for (dataset_id, model_type, horizon, seed)
2. If hit and calibration_hash matches → return deserialized SimulationResult
3. If miss → check transition_matrices for (dataset_id, model_type, period)
4. If matrix miss → call build_transition_matrix() → insert into transition_matrices
5. Run monte_carlo_simulate() → insert into simulation_runs → return result
```

---

## Domain Service Contracts

### What flows across the core/domains boundary

The domain service (`domains/brand_share/service.py`) is the translation layer between:
- Streamlit's string-based inputs (dataset_id as string, model_type as "m1"/"m2"/"m3")
- Core's typed NumPy world (TransitionMatrix arrays, StateVector arrays, ForecastResult)

**Service → Core call contract:**

The service assembles all NumPy inputs before calling core. Core functions never touch DuckDB directly (per the architecture rules). The service calls `core/db/queries.py` to get data, transforms it to NumPy, then calls `core/models.py`.

```python
# In domains/brand_share/service.py:

def run_forecast(dataset_id: str, model_type: str, horizon: int) -> BrandShareForecastResult:
    # 1. Fetch raw transitions from DB
    transitions_df: pd.DataFrame = queries.load_transitions(dataset_id)
    
    # 2. Build matrices (returns np.ndarray + state_labels)
    matrix, labels, counts = build_transition_matrix(transitions_df, ...)
    
    # 3. Dispatch to correct model class
    model = _build_model(model_type, [matrix], G=None)
    
    # 4. Get initial state vector from most recent period
    Y_1: np.ndarray = _get_initial_state_vector(transitions_df, labels)
    
    # 5. Forecast
    forecast_result: ForecastResult = model.forecast(Y_1=Y_1, horizon=horizon)
    
    # 6. Run Monte Carlo for confidence bands
    sim_result: SimulationResult = service_simulate(matrix, ...)
    
    # 7. Assemble chart-ready output (Plotly dicts, KPI values)
    return _build_output(forecast_result, sim_result, labels)
```

**The existing `BrandShareForecastResult` has a design gap:**
`forecast_chart_json: dict` stores a Plotly figure dict. This is convenient but couples the domain service to Plotly. A cleaner contract is to return structured data (the forecast array, confidence bands as arrays, state labels) and let the page/component layer build the Plotly figure. The chart-building belongs in `app/components/`, not in `domains/`. The existing stub has `BrandShareForecastResult` with `forecast_chart_json: dict` — this should be replaced with structured arrays before implementation begins.

**Recommended revised BrandShareForecastResult:**
```python
@dataclass(frozen=True)
class BrandShareForecastResult:
    state_labels: list[str]
    forecast_array: np.ndarray       # shape (horizon, n_states)
    confidence_bands: dict[float, np.ndarray]  # quantile -> shape (horizon, n_states)
    transition_matrix: np.ndarray    # shape (n_states, n_states)
    kpis: dict[str, float]           # e.g. {"steady_state_leader": "BrandA", "entropy": 1.23}
    accuracy_metrics: dict[str, float] | None
```

The Plotly figure dicts are built in the page (`app/pages/1_Brand_Share.py`) using a component function that takes `BrandShareForecastResult` as input.

**ChurnAnalysisResult has the same coupling problem** — `sankey_chart_json: dict` should be replaced with `state_distribution_per_period: list[dict[str, float]]` and `flow_matrix: np.ndarray`. The Sankey figure construction belongs in the app layer.

---

## Streamlit Multi-Page Patterns

### DuckDB singleton across pages

The module-level `_connection` global in `core/db/connection.py` is safe for Streamlit's single-threaded execution model (Streamlit runs one script execution at a time per user session — there is no true multi-threading). The risk is test pollution, not production concurrency.

**The correct Streamlit pattern:**
```python
# In any Streamlit page that needs DB access:
import streamlit as st
from core.db.connection import get_connection

@st.cache_resource
def _get_db():
    return get_connection()
```

`@st.cache_resource` ensures one connection per Streamlit server process, not one per page re-run. Since `get_connection()` already memoizes at the module level, calling it from `@st.cache_resource` is redundant but harmless — `@st.cache_resource` adds the important guarantee that it survives across page navigations and hot-reloads in development.

The domain services should NOT call `get_connection()` directly. They call `core/db/queries.py` functions, which call `get_connection()` internally. The page layer never touches the connection. This layering is already correctly defined in the architecture.

**Session state naming:** Per the existing streamlit-conventions.md, prefix all `st.session_state` keys with the page name:
```python
# In 1_Brand_Share.py
st.session_state["brand_share.selected_dataset"] = dataset_id
st.session_state["brand_share.last_forecast"] = forecast_result

# In 2_Churn.py
st.session_state["churn.selected_cohort"] = cohort_id
```

This prevents key collisions between pages sharing the same session state dict.

### st.cache_data invalidation for forecast results

`@st.cache_data` uses the function arguments as the cache key. The signature `get_forecast(dataset_id, model_type, horizon)` will auto-invalidate when any of these change. This is correct behavior.

**One gotcha:** `np.ndarray` arguments are NOT hashable by `@st.cache_data` by default — it hashes the bytes of the array, which works but is slow for large arrays. The service functions should accept primitive types (strings, ints, floats) as arguments, with NumPy arrays assembled inside the function. The existing service stub signatures already follow this pattern (all string/int arguments).

**Memory leak risk on Streamlit Cloud:** `@st.cache_data` accumulates cached results in memory across all user interactions for the session. For a portfolio demo with limited traffic this is fine. For production, set `max_entries` and `ttl` parameters:
```python
@st.cache_data(max_entries=20, ttl=3600)  # 20 cached calls, 1-hour TTL
def get_forecast(...): ...
```

### Multi-page navigation and component state

Streamlit's multi-page app re-runs the active page script on every widget interaction. This means:
- Any non-`st.session_state` variable is recomputed on every click.
- `@st.cache_data` and `@st.cache_resource` survive page re-runs within a session.
- Navigating between pages does NOT clear `st.session_state`.

The recommended pattern for the Brand Share page: store the last `ForecastResult` in `st.session_state["brand_share.last_forecast"]` so switching between tabs (Overview / Matrix / Monte Carlo / Comparison) doesn't re-trigger the forecast computation.

---

## Risks and Mitigations

### Risk 1: validate_transition_matrix() raises wrong exception type

**What:** Tests in `test_models.py` assert `InvalidTransitionMatrixError` is raised. If implementation uses `AssertionError` or `ValueError` instead (a natural temptation), tests fail in a confusing way.

**Mitigation:** `InvalidTransitionMatrixError` is already imported in `core/models.py`. Raise it explicitly. Reserve `AssertionError` for internal invariants never intended to reach users.

### Risk 2: Matrix serialization round-trip losing shape or dtype

**What:** `transition_matrices.matrix_json` stores the matrix as JSON. JSON does not preserve NumPy dtype (`float64` vs `float32`) or array shape. Deserializing with `np.array(json.loads(matrix_json))` without specifying dtype produces `float64` by default (fine), but loses the `labels` list unless it is co-stored.

**Mitigation:** Always serialize as `{"labels": list[str], "values": list[list[float]]}`. Deserialize with explicit `dtype=np.float64` and reconstruct the label-to-index mapping. This round-trip contract must be established once in `core/db/queries.py` and never duplicated.

### Risk 3: M3 state vector semantic mismatch

**What:** M3 operates on population counts (`Q`, absolute numbers), while M1/M2 operate on probability distributions (`Y`, shares summing to 1). If the Brand Share service passes a probability vector as `Q_1` to M3Extended, the model silently produces wrong results — the growth multiplier G applies to fractions instead of counts, producing non-sensical scaled fractions rather than projected customer/market counts.

**Mitigation:** `M3Extended.forecast()` should check `Q_1.sum()` and if it is approximately 1.0 (within tolerance), log a warning: "Q_1 appears to be a probability distribution; M3 expects absolute population counts." Do not raise — the caller may intentionally be using normalized counts. But log loudly.

### Risk 4: DuckDB singleton breaks test isolation

**What:** `core/db/connection.py` uses a module-level `_connection`. If two integration tests call `get_connection()`, they share the same connection and the same DB file (default path from `settings.duckdb_path`). Tests that insert data will pollute subsequent tests.

**Mitigation:** The `temp_duckdb_path` fixture in `conftest.py` provides a per-test path, but tests must call `close_connection()` and then override `settings.duckdb_path` before calling `get_connection()`. The cleanest pattern is a `test_db` fixture in `conftest.py` that:
1. Sets `settings.duckdb_path = tmp_path / "test.duckdb"`
2. Calls `close_connection()` to clear the global
3. Yields the connection from `get_connection()`
4. Calls `close_connection()` in teardown

Without this, integration tests that run after a test that modified the default DB will see unexpected data.

### Risk 5: Plotly figure dicts in service return types (existing coupling)

**What:** The current `BrandShareForecastResult.forecast_chart_json: dict` and `ChurnAnalysisResult.sankey_chart_json: dict` couple domain logic to Plotly. If the Plotly theme changes, service tests break. If the service layer is unit-tested, tests need Plotly installed and configured.

**Mitigation:** As described in Domain Service Contracts above, replace chart dicts with structured arrays in the service result types before implementing the service. This is a design change that is much harder to make after the service and UI are wired together.

### Risk 6: walk_forward_backtest future-data leakage

**What:** The `walk_forward_backtest()` function is not yet implemented. If naively implemented by slicing the full transitions DataFrame by period index, off-by-one errors can let t+1 data leak into the training window.

**Mitigation:** The train/holdout split must be: `train = df[df["period"] < t]`, `holdout = df[df["period"] == t]`. The `<` strictly excludes the holdout period. Never use `<=` for the train window or `>` for the holdout.

### Risk 7: streamlit-shadcn-ui API instability

**What:** CONCERNS.md flags `streamlit-shadcn-ui 0.1.18+` as beta. The `.streamlit/config.toml` already configures the primary color (#4338CA), which means basic Streamlit theming is available as a fallback.

**Mitigation:** Use `streamlit-shadcn-ui` only for the KPI card and button styling. All charts use Plotly with the project theme template. All layout uses native Streamlit columns/containers. If `streamlit-shadcn-ui` breaks on a version bump, the impact is limited to cosmetic card styling, not functional charts or data.

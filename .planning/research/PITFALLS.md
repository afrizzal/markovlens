# Pitfalls Research — MarkovLens

**Domain:** Markov chain analytics + Streamlit portfolio project + DuckDB embedded DB
**Researched:** 2026-05-29
**Confidence:** HIGH — grounded in codebase analysis, established numerical computing patterns, and well-documented Streamlit/DuckDB behavior. Web access was unavailable; findings are based on domain expertise and direct codebase inspection. Confidence is HIGH for math pitfalls (deterministic), HIGH for Streamlit pitfalls (well-documented official behavior), MEDIUM for DuckDB-specific version notes (verified against schema and connection code).

---

## Summary — Top 3 Most Critical Pitfalls

**1. Column-stochastic confusion in the Monte Carlo inverse-CDF path.**
The docs/MONTE-CARLO.md vectorized example uses `cum_matrix = matrix.cumsum(axis=1)` — correct for row-stochastic `P`. But if `build_transition_matrix()` is ever constructed with the convention `P[j, i]` = probability of i → j (column-stochastic, common in textbooks), the entire simulation silently runs the wrong model. No exception is thrown; results look plausible but are wrong. This is the single most common way Markov implementations produce subtly incorrect results that pass visual inspection.

**2. Monte Carlo state-index paths fed directly to `compute_quantile_bands()` without a target extractor.**
`paths` is a `(n_sims, n_steps+1)` integer array of state indices. Taking `np.percentile(paths, q, axis=0)` produces "average state index" quantiles — a meaningless number that looks like a real confidence band. The correct pattern is to extract a scalar metric per path first (market share, probability of membership in a target set, etc.). The current `compute_quantile_bands()` stub has `target_extractor: callable` in the signature, which is the right design — but it's easy to implement wrong or to call incorrectly from `domains/*/service.py`.

**3. DuckDB singleton connection shared across Streamlit reruns without `@st.cache_resource` guard.**
Streamlit re-executes the entire page script on every widget interaction. A module-level `get_connection()` that returns the same `_connection` works fine in a normal Python process, but if that connection is ever closed (e.g., `close_connection()` called in a test, or between sessions), the next `get_connection()` recreates it — but Streamlit's `@st.cache_resource` may still hold a reference to the old closed connection object. The symptom is "connection closed" errors mid-session that disappear on page refresh.

---

## Markov Chain Math Pitfalls

### CRITICAL: Row-Stochastic vs Column-Stochastic Orientation

**What goes wrong:**
`P[i, j]` = probability of transitioning FROM state `i` TO state `j`. This is row-stochastic — each row sums to 1. The formula is `Y_{t+1} = Y_t · P` (row vector on left). Many textbooks instead define `P[i, j]` as FROM `j` TO `i` (column-stochastic), where `Y_{t+1} = P · Y_t` (column vector).

If `build_transition_matrix()` is implemented with `pd.crosstab(from_state, to_state)` but then normalized as `df.div(df.sum(axis=0))` (column sums) instead of `df.div(df.sum(axis=1), axis=0)` (row sums), you get the transpose of the correct matrix. Chan (2015) is explicitly row-stochastic; the validated examples in `tests/conftest.py` (`sample_4x4_chan_matrix`) confirm this.

**Warning sign:**
- Run the Chan 2015 Table 3 test (`test_m1_forecast_replicates_chan_2015_table3`). If `Y_{t+2}` moves in the wrong direction (e.g., Incumbent grows instead of declining), orientation is wrong.
- `P.sum(axis=1)` all equal 1.0 but `P.sum(axis=0)` do NOT — correct.
- `P.sum(axis=0)` all equal 1.0 but `P.sum(axis=1)` do NOT — transposed.

**Prevention:**
- `validate_transition_matrix()` checks `P.sum(axis=1) ≈ 1.0`. It does NOT check `axis=0`. This is intentional and correct — a column-stochastic matrix would fail the axis=1 check.
- In `build_transition_matrix()`, always normalize with `df.div(df.sum(axis=1), axis=0)` and assert after normalization.
- The existing `validate_transition_matrix()` is the correct firewall once implemented.

**Phase:** Phase 01 (ENG-01 + DATA-03). The `build_transition_matrix()` implementation is where this goes wrong.

---

### CRITICAL: Sparsity Silently Producing Noise-Dominated Probability Estimates

**What goes wrong:**
A cell `P[i, j]` estimated from 3 observations has a confidence interval of ±40%+ (Wilson interval for n=3). With `MIN_OBSERVATIONS_PER_CELL = 20` undefined in practice, a matrix built from a sparse 10-state dataset might have rows with only 2-5 observations. The matrix passes `validate_transition_matrix()` (rows sum to 1) and Monte Carlo runs normally. The output is presented to the user as a credible forecast — but it is just amplified noise.

**Warning sign:**
- Kaggle churn datasets often have highly asymmetric state distributions: "Active" may have 5,000 customers, "Reactivated" may have 12. The `Reactivated → Active` and `Reactivated → Churned` cells will be estimated from ~6 observations each.
- Any cell with `n < 20` that feeds into a Monte Carlo forecast.

**Prevention:**
- ENG-08 (sparsity detection) must be implemented alongside ENG-01, not deferred.
- `validate_transition_matrix(P, transition_counts=counts)` already accepts `transition_counts` in the signature — use it.
- Display a per-cell sparsity overlay on the transition heatmap in the UI. Color cells with n < 20 in orange; n < 5 in red.
- For the Kaggle churn dataset, consider merging rare states before building the matrix (e.g., merge "Reactivated" into "At-Risk" if n < 100).

**Phase:** Phase 01 (ENG-08) and Phase 02 (UI heatmap overlay, DATA-03 sparsity check in loader).

---

### CRITICAL: State-Index Paths Confused With Metric Values in Quantile Bands

**What goes wrong:**
`paths` is shape `(n_sims, n_steps+1)` of integer state indices (0, 1, 2, ..., n_states-1). The naive mistake is:

```python
# WRONG — percentile of state indices, not of a business metric
bands = np.percentile(paths, [10, 50, 90], axis=0)
```

State 3 is not "better" than state 2 in an ordinal sense for most domains. For brand share, state indices represent brands, not values. For churn, states are categorical (Active, At-Risk, Churned, Reactivated) — taking percentile of their index numbers is meaningless.

The correct approach: apply `target_extractor` first to convert each path to a scalar time series, then take percentiles of that series.

```python
# CORRECT
metric_paths = np.apply_along_axis(target_extractor, 1, paths)  # (n_sims, n_steps+1)
bands = np.percentile(metric_paths, [10, 50, 90], axis=0)
```

**Warning sign:**
- Fan chart confidence bands that appear implausibly smooth or that stay constant across steps.
- Band values that are non-integer but bounded in [0, n_states-1].

**Prevention:**
- The `compute_quantile_bands()` stub already requires `target_extractor: callable` — enforce this contract in the implementation.
- For brand share: `target_extractor = lambda path: (path == target_brand_idx).astype(float)` gives P(in that state) at each step.
- For churn: `target_extractor = lambda path: (path == CHURNED_STATE_IDX).astype(float)`.
- Add a test: verify that band values are in [0, 1] for probability extractors.

**Phase:** Phase 01 (ENG-07) and Phase 02 (SVC-01 integration).

---

### M2 vs M3 Semantic Confusion: Market Share vs Customer Count

**What goes wrong:**
m1 and m2 operate on `Y_t` (market share vectors, sum to 1). m3 operates on `Q_t` (absolute customer counts, do NOT sum to 1 — sum is total market size). A developer implementing m3 who passes `Y_1` (normalized shares) instead of `Q_1` (raw counts) gets plausible-looking output because the math still runs — but the growth multiplier `G` distorts shares by the wrong base.

Concretely: if `Q_1 = [1,627,300, 780,300, 130,000, 173,200]` but you pass `Y_1 = [0.5878, 0.2830, 0.0585, 0.0708]`, the G multiplier `[1.0315, 1.0561, 0.9029, 1.0897]` grows each provider's count by 3-8%... but operating on fractions instead of absolute numbers, so the final result is neither meaningful shares nor meaningful counts.

**Warning sign:**
- m3 forecast outputs values that sum close to 1.0 across all steps (should not — should grow over time).
- m3 output for the Chan 2015 example doesn't match Table 4 in MARKOV-MODELS.md (first row should be 2,904,830 total at t=2, not approximately 1.0).

**Prevention:**
- The type alias `PopulationVector` is already defined for m3 — use it consistently to signal the semantic difference.
- Add to `M3Extended.__init__`: `if Q_1.sum() <= 2.0: raise ValueError("Q_1 looks like a normalized share vector (sums ≤ 2). M3 requires absolute customer counts.")` as a soft guard.
- The Chan 2015 worked example values in `docs/MARKOV-MODELS.md` are the canonical regression test — reproduce them in `test_m3_replicates_chan_2015_table4`.

**Phase:** Phase 01 (ENG-04, TEST-01).

---

### M2 Time-Varying P Estimation: Future-Leak in Per-Period Matrix Construction

**What goes wrong:**
For m2, each `P_t` is estimated from transitions observed in period `t`. But if `build_transition_matrix()` for period `t` uses ALL transitions up to that period (cumulative), it leaks information about future periods into earlier matrices. This inflates apparent accuracy on backtests.

**Warning sign:**
- m2 MAPE on backtest is significantly lower than m1 (suspicious if data is truly stable).
- Backtest accuracy improves over time with no clear business explanation.

**Prevention:**
- `build_transition_matrix()` for m2 must accept a `period` parameter and filter `WHERE period = ?` (not `WHERE period <= ?`).
- Walk-forward validation must re-build ALL `P_t` sequences using only past periods at each step.
- This is separate from the training/test split: even within the "training" window, each `P_t` should only use data from that specific period.

**Phase:** Phase 01 (ENG-09) and DATA-03 (build_transition_matrix).

---

### M1 Matrix Power Accumulation: Floating-Point Drift Over Long Horizons

**What goes wrong:**
For long forecasts (horizon > 20 steps), computing `P^t` via repeated matrix multiplication accumulates floating-point rounding errors. After 50 iterations, row sums may drift to `1.000000001` or similar. The valid implementation uses `np.linalg.matrix_power(P, t)` which uses binary exponentiation (O(log t) multiplications), not a loop.

**Warning sign:**
- `forecast_array[t].sum()` drifts from 1.0 beyond step 20 in m1.
- Rows of the cumulative product in m2 drift from 1.0.

**Prevention:**
- Implement m1 as `Y_1 @ np.linalg.matrix_power(P, t)` per horizon step, not `Y_prev @ P` in a loop.
- Alternatively, renormalize `Y_t` after each step: `Y_t = Y_t / Y_t.sum()`.
- Test: `forecast_array.sum(axis=1)` should be `np.ones(horizon)` within 1e-6 for all horizons.

**Phase:** Phase 01 (ENG-02).

---

### Monte Carlo Vectorization Bug: `argmax` Tie-Breaking

**What goes wrong:**
The vectorized inverse-CDF sampler in MONTE-CARLO.md uses:
```python
paths[:, t + 1] = (u[:, None] < cum_probs).argmax(axis=1)
```
`argmax` returns the index of the FIRST `True` value. If `u` is exactly 0.0 (probability `1/2^53` but still possible over 10,000 sims), `u < cum_probs[0]` is True for the very first cumulative bin, returning state 0 regardless of the actual probabilities. More importantly, if a row has a zero-probability entry at position 0 (P[i, 0] = 0), `cum_probs[0] = 0`, `u < 0` is always False, and `argmax` correctly finds the first non-zero cumulative — this is fine. The real edge case is when `u` falls exactly on a boundary between two states due to floating-point.

**Prevention:**
- Use `np.searchsorted` instead of `argmax` — it handles edge cases correctly:
  ```python
  for t in range(n_steps):
      u = rng.random(n_simulations)
      current_states = paths[:, t]
      for sim_idx in range(n_simulations):
          paths[sim_idx, t+1] = np.searchsorted(cum_matrix[current_states[sim_idx]], u[sim_idx])
  ```
  Or vectorized with advanced indexing. `searchsorted` is the canonical correct approach for inverse-CDF sampling.
- This is a LOW severity issue (affects < 0.001% of paths) but it is the kind of thing that triggers a "did you think about edge cases?" question in a code review — important for a portfolio piece.

**Phase:** Phase 01 (ENG-05).

---

### Calibration Applied to Mean Shares (Not Just Tail Probabilities)

**What goes wrong:**
`calibrate_probability()` applies the Becker (2026) longshot-bias table. MONTE-CARLO.md correctly notes this should only be applied to `P(state in target set)` — binary probability questions. If a developer applies it to `Y_t[brand_A]` (mean forecast share), the calibration distorts the continuous value. For example, a 0.20 share forecast becomes 0.181 after calibration — wrong for a continuous forecast.

**Warning sign:**
- `m1.forecast_array` values are all slightly compressed toward 0.5 compared to the analytical prediction.
- Brand share forecasts show values that don't match the Chan 2015 analytical benchmark.

**Prevention:**
- Never call `calibrate_probability()` on entries from `forecast_array` (market share vectors).
- Only call `calibrate_probability()` on `raw_probability` outputs from Monte Carlo: `P(brand_A is market leader at horizon)`.
- Add a clear docstring note: "For mean forecasts, use `forecast_array` directly. For tail probability forecasts, use `calibrated_probability`."

**Phase:** Phase 01 (ENG-06) and Phase 02 (SVC-01 — must wire correctly).

---

## Streamlit Portfolio Killers

### CRITICAL: Cold-Start Monte Carlo Without Caching

**What goes wrong:**
On Streamlit Cloud, the first page load after a cold start runs all initialization code. If `monte_carlo_simulate()` is called unconditionally on page load (not gated by a button click and not `@st.cache_data`), a recruiter clicking the URL for the first time watches the page spin for 3-10 seconds. At 10,000 simulations × 12 steps × 10 states, even the vectorized implementation takes 100-500ms on Streamlit Cloud's single CPU. On cold start, with Python import overhead + DuckDB initialization + NumPy loading, the real user experience is 5-15 seconds of a blank page.

**Warning sign:**
- Forecast computation happens outside a `if run:` button gate.
- `@st.cache_data` missing from functions calling `monte_carlo_simulate()`.

**Prevention:**
- Gate ALL computation behind a primary action button: `run = st.button("Run Forecast", type="primary")` → `if run: ...`
- Wrap the service call in `@st.cache_data`: `@st.cache_data def cached_forecast(dataset_id, model_type, horizon): return service.run_forecast(...)`
- On cold start, show the empty state component (already defined in `app/components/empty_state.py`) with a clear CTA.
- The DuckDB cache layer (checking `transition_matrices` and `simulation_runs` tables) provides the second layer of protection.

**Phase:** Phase 02 (UI-03) — enforce this pattern from the first page built.

---

### CRITICAL: Page-Link Navigation Breaks Because `app/pages/` Files Don't Exist Yet

**What goes wrong:**
`app/Home.py` already has:
```python
st.page_link("pages/1_Brand_Share.py", label="Run Brand Share Forecast", ...)
st.page_link("pages/2_Churn.py", label="Analyze Customer Churn", ...)
```
These links silently produce errors or broken navigation if the files don't exist. More importantly, the naming convention for Streamlit multi-page apps changed in Streamlit 1.30+: the file must be named with a numeric prefix (`1_Brand_Share.py`) AND registered via `st.navigation()` in the main `app/Home.py` OR discovered automatically via the `pages/` directory. If Streamlit's version on deployment uses the `st.navigation()` API (1.36+), the auto-discovery pattern may behave differently.

**Warning sign:**
- Sidebar shows no pages in the navigation drawer.
- Clicking page links raises `StreamlitAPIException` or produces 404-style blank pages.

**Prevention:**
- Create page files early (even as stubs with `st.title("Coming soon")`), before wiring the links.
- Verify the Streamlit version in `pyproject.toml` and confirm whether `st.navigation()` is the correct API or if directory-based auto-discovery is sufficient.
- Test locally: run `uv run streamlit run app/Home.py` and confirm sidebar shows all pages before proceeding to implement any page content.

**Phase:** Start of Phase 02 (UI-03) — create stubs immediately.

---

### Session State Namespace Collisions in Multi-Page Apps

**What goes wrong:**
Streamlit session state is global across all pages in a session. If `1_Brand_Share.py` uses `st.session_state["dataset_id"]` and `2_Churn.py` also uses `st.session_state["dataset_id"]`, navigating from Brand Share to Churn will silently carry the brand share dataset ID into the Churn page. The user sees stale data from the wrong domain.

**Warning sign:**
- After running a brand share forecast, navigating to Churn page shows data.
- Widget values on one page appear pre-populated when the user hasn't interacted with that page.

**Prevention:**
- Namespace all session state keys by page: `st.session_state["brand_share.dataset_id"]` and `st.session_state["churn.dataset_id"]`.
- This is already documented in `streamlit-conventions.md` — enforce it without exception.
- Initialize per-page defaults at the top of each page file: `if "brand_share.run_state" not in st.session_state: st.session_state["brand_share.run_state"] = None`.

**Phase:** Phase 02 (UI-03) and Phase 03 (UI-04).

---

### Missing Error Boundaries Causing White-Screen Crashes During Demo

**What goes wrong:**
`core/` functions raise `InvalidTransitionMatrixError`, `DatasetTooSparseError`, `NotImplementedError` (during development), and potentially uncaught NumPy exceptions (e.g., `ValueError: probabilities do not sum to 1` from `rng.choice`). If domain service calls in page files are not wrapped in `try/except`, any of these will crash the Streamlit page with a full Python traceback — shown in red to the user (and to a recruiter watching a live demo).

**Warning sign:**
- No `try/except` blocks in `app/pages/*.py`.
- Service calls made directly without error handling.

**Prevention:**
- Every domain service call in `app/` must be wrapped:
  ```python
  try:
      result = service.run_forecast(dataset_id, model_type, horizon)
  except DatasetTooSparseError as e:
      st.error(f"Insufficient data: {e}")
      st.info("Try selecting a longer date range or merging sparse states.")
      return
  except Exception as e:
      st.error(f"Unexpected error — please try again.")
      if st.session_state.get("dev_mode"):
          st.exception(e)
      return
  ```
- The `dev_mode` flag is valuable: full tracebacks in dev, clean error messages in production/demo.
- CONCERNS.md already flags this as "no error boundaries not enforced at build time" — it must be addressed as part of page construction, not deferred.

**Phase:** Phase 02 (all UI pages) and Phase 03.

---

### Plotly Fan Charts Rendered Without Theme Template

**What goes wrong:**
Without `pio.templates.default = "markovlens"`, every Plotly chart uses the default white/grey theme. On a dark Streamlit theme, the contrast is wrong. On light theme, the charts look generic. A recruiter seeing default Plotly colors alongside a custom CSS design system immediately reads "student project" — the design gap between styled HTML and unstyled charts is visually jarring.

**Warning sign:**
- Charts look different from the rest of the UI in terms of font, color palette, or background.
- Chart backgrounds are white when the rest of the page is not.

**Prevention:**
- Create `app/styles/plotly_theme.py` in Phase 02 UI setup (UI-01), BEFORE building any charts.
- Call `pio.templates.default = "markovlens"` once at app startup.
- The theme should at minimum: set background to match Streamlit's background color, use the `#4338CA` accent color for primary series, set consistent font family and size.
- Apply `use_container_width=True` to all `st.plotly_chart()` calls — fixed-width charts break on different screen sizes and look unpolished.

**Phase:** Phase 02, first task (UI-01) before any chart code.

---

### `st.metric` Delta Values That Always Show Zero or "—"

**What goes wrong:**
`app/Home.py` already has `st.metric("Last Forecast Accuracy", "—")`. This is a placeholder that will remain forever if not wired to real data. A recruiter clicking the home page and seeing three metrics showing "0" and "—" reads: "developer built a dashboard but never connected it to real data."

More subtly: `st.metric` with `delta=0.0` shows a grey arrow, not a positive/negative signal. If MAPE improves from 8.2% to 7.9%, the delta is `-0.3` (improvement — should be green), but without careful sign handling, it shows as grey zero.

**Warning sign:**
- Home page KPIs not updated after implementing forecast functionality.
- Delta values are hardcoded zeros.

**Prevention:**
- Wire home page KPIs to real DuckDB queries AFTER Phase 01-02 are complete (Phase 02, UI-02).
- Use negative delta for metrics where decrease is improvement (MAPE): `delta=-0.3, delta_color="inverse"`.
- The home page KPIs should be the last thing wired, not the first.

**Phase:** Phase 02, final step (UI-02 wiring).

---

### Widget State Resets on Every Rerun

**What goes wrong:**
Streamlit reruns the entire page script on every widget interaction. Sliders, selectboxes, and inputs default to their initial values on each rerun unless their state is explicitly persisted in `st.session_state`. A user who sets `horizon=18`, `model_type="m3"`, runs a forecast, then changes the dataset — loses their horizon and model settings, defaulting back to `horizon=12`, `model_type="m1"`. This feels broken to power users.

**Warning sign:**
- Widget parameters reset when an unrelated widget changes.
- The "Run" button triggers correct behavior, but unrelated widget changes cause visible state jumps.

**Prevention:**
- Use `key=` parameter on critical widgets: `st.slider("Months ahead", 1, 24, 12, key="brand_share.horizon")`.
- With a namespaced key, Streamlit automatically persists the value in `st.session_state["brand_share.horizon"]` across reruns.
- Initialize the key with a default if not already set.

**Phase:** Phase 02 (UI-03), during widget layout construction.

---

## DuckDB Pitfalls

### CRITICAL: Singleton Connection vs Streamlit's `@st.cache_resource` — Two Sources of Truth

**What goes wrong:**
`core/db/connection.py` manages a module-level `_connection` singleton. `streamlit-conventions.md` recommends wrapping `get_connection()` with `@st.cache_resource`. These two patterns conflict: if `@st.cache_resource` is applied at the Streamlit layer, Streamlit manages the connection lifetime. If `close_connection()` is called (e.g., from a test or from a page that tries to "reset"), the module-level `_connection` becomes `None`, but Streamlit's resource cache still holds the old (now closed) connection object.

The symptom is a cryptic `duckdb.InvalidInputException: Connection already closed` error that is non-deterministic — it only manifests if `close_connection()` is ever called during a session.

**Prevention:**
- Pick ONE pattern and enforce it consistently:
  - Option A (recommended): Wrap `get_connection()` in `@st.cache_resource` at the Streamlit boundary only (in `app/`), and NEVER call `close_connection()` in production code — only in tests using `temp_duckdb_path` fixture.
  - Option B: Don't use `@st.cache_resource` at all; rely purely on the module-level singleton. DuckDB connections are thread-safe for reads; Streamlit is single-threaded per user session, so this is safe.
- Never call `close_connection()` in page files. It exists for test teardown only.
- Add a comment to `close_connection()`: `# For test teardown only — do not call from app/ pages.`

**Phase:** Phase 01 (connection module) and Phase 02 (first Streamlit integration).

---

### JSON Column Serialization Roundtrip Precision Loss

**What goes wrong:**
`matrix_json`, `quantile_paths_json`, and `final_distribution_json` are stored as JSON in DuckDB. JSON uses 64-bit floats, but the default Python `json.dumps()` serialization may lose precision for NumPy arrays: `json.dumps(0.9123456789012345)` can produce `"0.9123456789012345"`, but some JSON serializers round to 15 significant digits. For a transition matrix element like `0.98230` this is fine. For calibration outputs stored to 6+ decimal places, round-trip precision may differ from in-memory computation.

More critically: `numpy.ndarray` is not JSON-serializable by default. If `matrix_json` is stored with `json.dumps(P.tolist())`, retrieval with `json.loads(row["matrix_json"])` returns a Python `list[list[float]]`, not a `numpy.ndarray`. Code in `core/` that expects `np.ndarray` will fail with `AttributeError: 'list' object has no attribute 'shape'`.

**Warning sign:**
- `queries.py` functions load matrices from JSON and pass them directly to `validate_transition_matrix()` or `M1Homogeneous()` without `np.array()` conversion.
- `AttributeError: 'list' has no attribute 'ndim'` during matrix validation after cache lookup.

**Prevention:**
- Always convert on storage: `json.dumps(P.tolist())`
- Always convert on retrieval: `P = np.array(json.loads(row["matrix_json"]))`
- Wrap this in helper functions in `core/db/queries.py`:
  ```python
  def _matrix_to_json(P: np.ndarray) -> str:
      return json.dumps(P.tolist())

  def _json_to_matrix(s: str) -> np.ndarray:
      return np.array(json.loads(s))
  ```
- Run `validate_transition_matrix()` after every JSON roundtrip to catch precision edge cases.

**Phase:** Phase 01 (DATA-03 build_transition_matrix and caching implementation).

---

### DuckDB Connection Not Thread-Safe for Multiple Writers

**What goes wrong:**
DuckDB's default connection mode (`duckdb.connect(path)`) supports multiple readers but only ONE writer at a time. If Streamlit ever runs two user sessions concurrently (unlikely for a portfolio demo but possible), both sessions sharing the same `_connection` module-level singleton can cause `CatalogException: Could not serialize access to catalog: Write conflict on table`.

**Warning sign:**
- Write errors when two browser tabs are open and both trigger forecasts simultaneously.

**Prevention:**
- For a portfolio demo (single user), this is LOW severity — document it in CONCERNS.md.
- If needed: use `duckdb.connect(path, read_only=False)` with connection-level locking, or open a separate connection per Streamlit session via `@st.cache_resource`.
- Do NOT switch to `read_only=True` globally — writes are needed for caching.

**Phase:** MEDIUM priority, can defer to after Phase 04. Document in CONCERNS.md.

---

### Schema Migration Without Explicit Versioning

**What goes wrong:**
`CREATE TABLE IF NOT EXISTS` means adding a new column to `schema.sql` does NOT apply to an existing database. If the DuckDB file exists from a previous run (e.g., development iteration), `init_schema()` is silently a no-op. The column is missing, queries that reference it fail with `CatalogException: Column not found`.

**Warning sign:**
- `CatalogException: Binder Error: Referenced column ... not found in FROM clause`
- Error only appears on developer machines that have existing DuckDB files; does not appear in CI (fresh DB per test).

**Prevention:**
- For additive changes (new column): add an explicit `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...` migration statement.
- For breaking changes: use numbered `scripts/migrate_001_add_column.py` scripts and record completion in a `_schema_version` table.
- The current design acknowledges this in CONCERNS.md ("manual migration scripts in scripts/migrate_*.py") — follow through: when `schema.sql` changes, create the migration script immediately.
- During development, document "if you get a CatalogException, delete `data/markovlens.duckdb` and re-run `scripts/seed_data.py`" in the README troubleshooting section.

**Phase:** Ongoing — relevant any time `schema.sql` changes.

---

### Kaggle Dataset State Column Is String, Not Integer — State Index Mapping

**What goes wrong:**
The `transitions` table uses `VARCHAR` for `from_state` and `to_state` (e.g., `"Active"`, `"At-Risk"`, `"Churned"`, `"Reactivated"`). NumPy transition matrices require integer indices. The mapping from state name → state index must be consistent, deterministic, and stored alongside the matrix.

If state mapping is derived at query time (e.g., alphabetical sort of distinct state values), adding a new dataset with a different set of states changes the mapping — invalidating all cached matrices.

**Warning sign:**
- Two different runs of `build_transition_matrix()` for the same dataset produce matrices where state 0 means different things.
- `P[0, 1]` in the DB-cached matrix is the probability of "Active → At-Risk", but after a reload it's "At-Risk → Churned" because alphabetical ordering changed.

**Prevention:**
- Store the state → index mapping in `datasets.metadata_json` at dataset registration time.
- Never re-derive it from `DISTINCT from_state` at query time.
- `build_transition_matrix()` must accept an explicit `state_order: list[str]` parameter and use it deterministically.

**Phase:** Phase 01 (DATA-03) and DATA-01 (loaders.py).

---

## BA/BI Portfolio Pitfalls

### Pitfall: Correct Math, Unreadable Output — "I Can't Tell What This Is Showing"

**What goes wrong:**
A forecast that produces correct numerical values but presents them with axis labels like `"State 0"`, `"State 1"`, `"State 2"` signals that the developer didn't complete the product. Similarly: a transition heatmap with probability values shown as `0.982301` instead of `98.2%` forces the recruiter to mentally parse numbers. A Monte Carlo fan chart without a clear "you are here" marker for the current period makes the time axis ambiguous.

**Warning sign:**
- State names in charts are integer indices or machine-readable IDs.
- Probability values displayed with 6 decimal places instead of 1-2 significant digits.
- No annotation showing what the "current period" is relative to the forecast horizon.

**Prevention:**
- Map state indices back to human names everywhere in the visualization layer.
- Format probabilities as percentages (`f"{p*100:.1f}%"`) in all chart labels and hover templates.
- Add a vertical "today" line on fan charts and a bold boundary between historical and forecast periods.

**Phase:** Phase 02 (UI-03) and Phase 03 (UI-04).

---

### Pitfall: Demo That Only Works on Ideal Data

**What goes wrong:**
A portfolio project tested only on the exact Kaggle CSV it was built for fails during a live demo if the recruiter asks "what if I upload my own data?" or if the seed data regeneration step produces even slightly different state counts. Real BA/BI work involves messy data — missing periods, imbalanced states, unusual state names with special characters.

**Warning sign:**
- `scripts/seed_data.py` is the only data path that has been tested.
- Upload flow errors are not handled gracefully.
- State names with slashes, spaces, or Unicode break the state → index mapping or the chart axis labels.

**Prevention:**
- Test `load_brand_share_csv()` and `load_churn_csv()` with at least two variants of the data (different column names, missing rows, extra states).
- Sanitize state names at ingestion: `state.strip().replace("/", "_")` or similar.
- Show a clear error message if the uploaded CSV doesn't have the required columns — not a Python traceback.
- Settings page (UI-06) dataset upload should have client-side validation before attempting to load.

**Phase:** Phase 01 (DATA-01 loaders) and Phase 04 (UI-06 Settings).

---

### Pitfall: No Academic Citation Traceable From UI

**What goes wrong:**
The project claims to implement Chan (2015) with Becker (2026) calibration. If a recruiter can't find this reference IN the deployed app (not just in the README), it looks like a marketing claim. Conversely, if the only evidence of quantitative rigor is in `docs/MARKOV-MODELS.md` that few will find, the methodology section of the app does the heavy lifting.

The existing `app/Home.py` already links to `docs/MARKOV-MODELS.md` and `docs/MONTE-CARLO.md`. This is good but depends on GitHub rendering working.

**Warning sign:**
- The running app has no visible reference to the academic sources.
- "Chan (2015)" appears only in code comments, not in the UI.

**Prevention:**
- Include a methodology footnote on the Brand Share and Churn pages: "Based on Chan (2015), IJICIC 11(4). Calibrated per Becker (2026)." — small but visible.
- The existing `st.expander("Methodology — how MarkovLens works")` in `app/Home.py` is the right pattern — replicate it on each analysis page.
- Include a "Backtest accuracy" metric in the UI that shows MAPE/Brier score for the dataset — a number that demonstrates the model was validated, not just implemented.

**Phase:** Phase 02 (UI-03) and Phase 03 (UI-04).

---

### Pitfall: Model Comparison Panel That Is Actually Just Three Tables

**What goes wrong:**
The project brief includes "SVC-03: Model comparison: run all three models, return accuracy metrics side-by-side." The pitfall is implementing this as three stacked tables of numbers (m1: MAPE=8.3%, m2: MAPE=7.1%, m3: MAPE=6.9%) without a visual comparison that makes the differences legible. A recruiter skims — they need to see "m3 visually outperforms m1 on this dataset" in under 5 seconds.

**Warning sign:**
- Model comparison is only a `st.dataframe()` or three separate `st.metric()` calls.
- No visual representation of which model is "winning" and why.

**Prevention:**
- Bar chart comparing MAPE/Brier across m1/m2/m3, with the best model highlighted in accent color.
- Overlay the three forecast lines on the same chart so the user can see the divergence.
- Include a one-sentence recommendation: "m3 best fits this dataset because market size grew 9.8% over the forecast period."

**Phase:** Phase 02 (UI-03, model comparison tab).

---

### Pitfall: GitHub README That Reads Like a Feature List, Not a Story

**What goes wrong:**
Most data portfolio projects have READMEs that say: "Features: Markov chain, Monte Carlo, DuckDB, Streamlit." This tells a recruiter nothing about the developer's thinking. The recruiter question is: "Why did you choose Markov chains for this problem? What does the output tell a business person?"

**Warning sign:**
- README starts with "Installation" before explaining what the project does.
- README lists technical dependencies but doesn't explain the business problem being solved.
- No demo screenshot or GIF showing the actual output.

**Prevention:**
- README should open with the business problem: "E-commerce market share can shift 5% in a quarter. How do you forecast which brand is gaining before it's obvious in the data?"
- Show a screenshot of the fan chart with real output — a visual that proves the app works.
- One section: "Why Markov chains?" — a 3-sentence business justification, not a textbook definition.
- The CLAUDE.md project goal is already framed correctly ("If the demo doesn't convince a senior recruiter...") — apply that standard to the README.

**Phase:** Phase 05 or final polish, after real output is generated. Do not write the story until you have the screenshots.

---

## Phase Mapping

| Pitfall | Severity | Phase to Address |
|---------|----------|-----------------|
| Row vs column stochastic in `build_transition_matrix()` | CRITICAL | Phase 01 (DATA-03) |
| Sparsity warnings not implemented alongside ENG-01 | CRITICAL | Phase 01 (ENG-08) — do not defer |
| State-index paths in `compute_quantile_bands()` | CRITICAL | Phase 01 (ENG-07) |
| M2 vs M3 semantic confusion (shares vs counts) | HIGH | Phase 01 (ENG-04, TEST-01) |
| Future-leak in per-period P_t construction | HIGH | Phase 01 (ENG-09) + DATA-03 |
| M1 matrix power accumulation over long horizons | MEDIUM | Phase 01 (ENG-02) |
| Monte Carlo `argmax` tie-breaking edge case | LOW | Phase 01 (ENG-05) |
| Calibration applied to continuous shares | HIGH | Phase 01 (ENG-06) + Phase 02 (SVC-01) |
| Cold-start Monte Carlo without caching | CRITICAL | Phase 02 (UI-03, first page built) |
| Page-link navigation to missing files | HIGH | Phase 02 (create stubs immediately) |
| Session state namespace collisions | HIGH | Phase 02 (UI-03) + Phase 03 (UI-04) |
| Missing error boundaries in pages | CRITICAL | Phase 02 (all pages) + Phase 03 |
| Plotly charts rendered without theme template | MEDIUM | Phase 02, first task (UI-01) |
| Home KPIs wired to real data | MEDIUM | Phase 02, final step (UI-02) |
| Widget state resets on rerun | MEDIUM | Phase 02 (UI-03) |
| DuckDB singleton vs `@st.cache_resource` conflict | HIGH | Phase 01 (connection) + Phase 02 (integration) |
| JSON roundtrip precision + list-not-ndarray bug | HIGH | Phase 01 (DATA-03 caching) |
| DuckDB concurrent writer conflict | LOW | Documented; defer after Phase 04 |
| Schema migration without versioning | MEDIUM | Ongoing — any `schema.sql` change |
| State name → integer index instability | HIGH | Phase 01 (DATA-03) + DATA-01 |
| Unreadable axis labels and raw indices in charts | HIGH | Phase 02 (UI-03) + Phase 03 (UI-04) |
| Demo only works on ideal seed data | MEDIUM | Phase 01 (DATA-01 loaders) + Phase 04 (UI-06) |
| No academic citation visible in running app | MEDIUM | Phase 02 (methodology expanders) |
| Model comparison as tables not visuals | MEDIUM | Phase 02 (model comparison tab) |
| GitHub README feature list, not story | MEDIUM | Final polish phase |

---

## Sources

**HIGH confidence (deterministic, verified against codebase):**
- `core/models.py`, `core/simulation.py` — direct code inspection
- `docs/MARKOV-MODELS.md`, `docs/MONTE-CARLO.md` — project mathematical reference
- `.planning/codebase/CONCERNS.md` — existing technical debt inventory
- NumPy RNG API: `np.random.default_rng()`, `np.searchsorted` — well-established NumPy 2.0 patterns (training data, August 2025 cutoff)

**HIGH confidence (well-documented Streamlit behavior):**
- Streamlit session state scoping, `@st.cache_data`, `@st.cache_resource`, multi-page app patterns — documented in official Streamlit docs and stable since Streamlit 1.28+

**MEDIUM confidence (DuckDB version-specific):**
- DuckDB JSON column behavior and concurrent connection limits — based on DuckDB 0.9-1.1 documentation (training data). Verify against the exact version pinned in `pyproject.toml` when implementing DATA-03.

**LOW confidence (BA/BI recruiter behavior):**
- "What makes a portfolio piece fail" claims — based on software industry hiring patterns, not empirical recruiter research. Treat as directional guidance, not ground truth.

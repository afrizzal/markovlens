# Phase 01: Markov Engine — Context

**Gathered:** 2026-05-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement every function in `core/` that currently raises `NotImplementedError`. Deliver:
- Three Markov model classes (M1, M2, M3) following Chan (2015) equations exactly
- Monte Carlo simulation engine with vectorized implementation
- Longshot-bias calibration (Becker 2026)
- Quantile band computation for fan charts
- Accuracy metrics: MAPE, Brier score, log-loss
- DuckDB data layer: schema init, `build_transition_matrix()`, serialization helpers
- Seed script populating both domains with reference data
- Regression tests achieving > 80% coverage for `core/`

Every downstream phase (02–05) calls into this layer. A `NotImplementedError` here blocks everything.

</domain>

<decisions>
## Implementation Decisions

### Brand Share Data Source (DATA-02)

- **D-01:** Brand share domain uses a **synthetic FMCG DGP** — a distinct domain from the Chan (2015) telecom example (not a mirror). Plausible parameters invented and documented in the seed script. Shows the engine generalises beyond the paper.
- **D-02:** Churn domain uses the **IBM Telco Customer Churn CSV committed to the repo** at `data/seed/telco_churn.csv` (NOT `data/raw/`). Source: IBM Watson sample data via Kaggle `blastchar/telco-customer-churn`.
- **D-03:** `.gitignore` amended: `data/raw/` and `data/*.duckdb` stay gitignored; `data/seed/*.csv` is tracked (small, publicly redistributable reference datasets).
- **D-04:** `data/SOURCES.md` must document: dataset origin, license context (effectively public domain — thousands of public GitHub repos redistribute this CSV), and why committed (deployment convenience for Streamlit Cloud cold start without credential friction).
- **D-05:** README attributes source and links to Kaggle page.

### M2 / M3 Forecast Extrapolation Beyond Training Window (ENG-03, ENG-04)

- **D-06:** `M2TimeVarying.forecast()` — when `horizon > len(P_t_sequence)`, **hold the last `P_t` constant** for remaining steps. Docstring must document this fallback. M2 degrades to M1-like behaviour beyond the observed window.
- **D-07:** `M3Extended.forecast()` — **same rule**: hold last `P_t` constant AND keep `G` constant beyond training data. Consistent with D-06.

### P_t / G Storage Format (ENG-03, ENG-04)

- **D-08:** `P_t_sequence` is stored as `np.ndarray` of shape `(n_periods, n_states, n_states)`, **NOT** `list[np.ndarray]`. Reasons: cleaner indexing (`P_t_sequence[t]` returns a matrix), NumPy-broadcasting-friendly, easier JSON serialization as a nested array.
- **D-09:** `G` is stored as `np.ndarray`:
  - Scalar growth per state: shape `(n_states,)` — the standard case
  - Time-varying growth: shape `(n_periods, n_states)` — supported if caller provides it
- **D-10:** Constructor validation must verify shape consistency: `P_t_sequence.shape[1] == P_t_sequence.shape[2]` (square), `G.shape[-1] == P_t_sequence.shape[1]` (compatible states).

### Monte Carlo Implementation (ENG-05)

- **D-11:** Algorithm — **vectorized cumsum + inverse-CDF**. Pre-compute `cum_matrix = matrix.cumsum(axis=1)`. Each step: draw `u = rng.random(n_simulations)`, look up `cum_matrix[current_states]`, resolve next state via `(u[:, None] < cum_probs).argmax(axis=1)`. Target: ~50ms for 10k×12 steps on 1 CPU. Pseudo-code in `docs/MONTE-CARLO.md` is the authoritative reference.
- **D-12:** **Float precision guard** — after `cumsum`, always set `cum_matrix[:, -1] = 1.0`. Without this, validator-tolerance drift (1e-9) can cause `u ≈ 0.9999999` to fail to match the last state. Silent correctness bug without this fix.
- **D-13:** **API signature** — `start_state` parameter accepts `Union[int, np.ndarray]`:
  - `int` → single starting state (used by Churn what-if simulator, CH-03)
  - `np.ndarray` shape `(n_states,)` → initial probability distribution (used by Brand Share fan chart, BS-03)
  - Internally normalize both to a probability vector before simulation begins.
- **D-14:** **Return shape** — `monte_carlo_simulate()` returns `np.ndarray` dtype `int64`, shape `(n_simulations, n_steps+1)`. Full paths, not just terminal distribution. `ENG-07 compute_quantile_bands()` consumes the full paths matrix for per-step bands. Memory: ~1 MB for 10k×13 paths — well within Streamlit Cloud 1 GB limit.
- **D-15:** **Reproducibility** — `rng = np.random.default_rng(seed)` only. **Never** legacy `np.random.seed()`. Test: same seed → bit-identical `paths` array; different seed → different array.
- **D-16:** **No threading or multiprocessing** — Streamlit Cloud is 1 CPU. Vectorized NumPy is the correct strategy. Parallelization adds complexity without speedup on 1 CPU and risks OOM from worker process array duplication.

### Calibration Implementation (ENG-06)

- **D-17:** `calibrate_probability()` uses **linear interpolation via `np.interp()`** on sorted `LONGSHOT_CALIBRATION` keys. Cubic spline and piecewise-constant approaches considered and rejected: linear is monotonic, has no overshoot, and is the standard practice for probability calibration. Becker's table is dense enough that interpolation method choice has negligible impact.
- **D-18:** **Calibration is applied AFTER simulation, never inside the loop.** `monte_carlo_simulate()` returns raw probabilities. `calibrate_probability()` (ENG-06) is called separately by the assembler. `SimulationResult` exposes both `raw_probability` and `calibrated_probability` fields.

### Test Strategy

- **D-19:** **Regression-first** — un-skip the 4 existing `@pytest.mark.skip` tests in `tests/unit/test_models.py`, add Chan (2015) Table 3 numerical regression (conftest already has `sample_4x4_chan_matrix`), write targeted tests to achieve > 80% coverage for `core/`. Phase 05 QA phase handles comprehensive parametric coverage.
- **D-20:** **DuckDB integration tests written in Phase 01** (not deferred to Phase 05 QA-02). `tests/conftest.py` already has `temp_duckdb_path` fixture. Integration tests cover `build_transition_matrix()` and seed script data paths. Phase 05 audits coverage, does not write from scratch.

### DuckDB Schema (DATA-03)

- **D-21:** **JSON storage confirmed** — `matrix_json`, `final_distribution_json`, `quantile_paths_json`, `forecast_json`, `accuracy_metrics_json` all remain `JSON` columns. No migration to native `DOUBLE[][]` arrays. `schema.sql` and `docs/DATABASE.md` are correct as-is.
- **D-22:** **`transitions` table has no composite PK** — append-only log semantics. Supports both per-entity (churn) and aggregate-weighted (brand share) data models. Duplicates detected at seed time, not enforced by DB.
- **D-23:** **Seed idempotency via `DELETE WHERE dataset_id` + `INSERT`** — not DB-level uniqueness constraints. Running `seed_data.py` twice must produce the same result, implemented by deleting existing rows for the dataset before re-inserting.
- **D-24:** **Serialization helpers centralized in `core/db/serialization.py`** — functions for `ndarray → JSON` and `JSON → ndarray` round-trips. NaN and Inf must be rejected at the boundary (raise `ValueError`). Covered by unit tests with round-trip assertions.

### Claude's Discretion

The following areas were not discussed — planner has full flexibility:

- Exact column count and period count for the synthetic FMCG DGP (planner decides realistic scale, e.g. 5 brands × 24 periods)
- ID generation strategy for DB PKs (UUID v4 via `uuid.uuid4()` is standard)
- MAPE edge-case handling when `actual == 0` (standard: skip zero-actual rows with a warning)
- Whether to split `tests/unit/` into per-module files (`test_models.py`, `test_simulation.py`, `test_metrics.py`) vs keep consolidated
- Whether `build_transition_matrix()` in `queries.py` also returns a sparsity mask or just the matrix + counts

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Markov Math
- `docs/MARKOV-MODELS.md` — Chan (2015) m1/m2/m3 equations, worked numerical example (Tables 1–3 values already in conftest), model selection guide. Every implementation must cite the relevant equation number.

### Monte Carlo & Calibration
- `docs/MONTE-CARLO.md` — Vectorized implementation pseudo-code (already written, use it directly), calibration function, walk-forward validation pattern, performance targets.

### Database Schema
- `core/db/schema.sql` — Idempotent schema. 6 tables. Confirmed as-is. Phase 01 adds `core/db/serialization.py` alongside this.
- `docs/DATABASE.md` — Full schema reference with column types, indexes, common query patterns.

### Coding Rules
- `.claude/rules/markov-patterns.md` — `validate_transition_matrix()` invariants, `MIN_OBSERVATIONS_PER_CELL=20`, forbidden practices (especially #2 legacy RNG and #4 raw slider values).
- `.claude/rules/data-storage.md` — DuckDB connection singleton pattern, parameterized queries, no raw SQL in app/.
- `.claude/rules/python-conventions.md` — Type hints, NumPy patterns, error handling conventions.

### Existing Stubs (fill these in)
- `core/models.py` — All class/function stubs with TODO(phase01). Type aliases and constants already defined.
- `core/simulation.py` — LONGSHOT_CALIBRATION hardcoded, SimulationResult dataclass complete. Functions need implementation.
- `core/metrics.py` — Three metric stubs with docstrings and examples. Need implementation.
- `tests/unit/test_models.py` — 4 tests, all `@pytest.mark.skip`. Un-skip and make them pass.
- `tests/conftest.py` — `sample_4x4_chan_matrix` (Chan 2015 P), `sample_2x2_matrix`, `temp_duckdb_path` fixtures ready.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `core/exceptions.py` — `InvalidTransitionMatrixError`, `DatasetTooSparseError`, `DatasetNotFoundError`, `UnsupportedModelError` — complete hierarchy, import and raise directly.
- `core/simulation.py::LONGSHOT_CALIBRATION` — already hardcoded as `dict[float, float]`. `calibrate_probability()` just needs `np.interp()` over its sorted keys.
- `core/simulation.py::SimulationResult` — frozen dataclass already complete with `final_distribution`, `quantile_paths`, `raw_probability`, `calibrated_probability`, `n_simulations`, `n_steps`, `seed` fields.
- `core/models.py::ForecastResult` — frozen dataclass with `forecast_array`, `confidence_bands`, `model_type`, `horizon`, `accuracy_metrics`.
- `tests/conftest.py::sample_4x4_chan_matrix` — the exact P from Chan (2015) Table 1. The Table 3 forecast values at t=2 (`[0.5829, 0.2780, 0.0667, 0.0724]`) are the regression target already embedded in `test_m1_forecast_replicates_chan_2015_table3`.

### Established Patterns
- All DB access via `core/db/connection.py` singleton — `get_connection()` returns `duckdb.DuckDBPyConnection`.
- Parameterized queries only: `conn.execute("... WHERE id = ?", [id])`.
- Functions return DataFrames at the DB boundary via `.df()`, then convert to NumPy within `core/`.
- `@dataclass(frozen=True)` for all result types — immutable value objects.

### Integration Points
- `core/db/queries.py` — `build_transition_matrix()` to be added here (DATA-03). Other functions (`register_dataset`, `list_datasets` etc.) are marked `# TODO(phase02)` — do not implement those in Phase 01.
- `core/io/loaders.py` — `load_brand_share_csv` and `load_churn_csv` are Phase 02. Phase 01 only needs a generic `validate_transitions_df()` helper if required by `build_transition_matrix()`.
- `scripts/seed_data.py` — new file, not a stub. Reads `data/seed/telco_churn.csv` and the synthetic DGP generator.

</code_context>

<specifics>
## Specific Ideas

- `cum_matrix[:, -1] = 1.0` after `np.cumsum` — explicit fix for float tolerance boundary drift. Not optional.
- `np.interp(raw_prob, sorted_keys, sorted_values)` is the exact call for calibration — 1-liner, no custom loop needed.
- `data/seed/telco_churn.csv` — IBM Watson sample, ~7k rows, ~21 columns. The relevant columns for churn modelling are: `customerID`, `tenure`, `Churn` (Yes/No). Seed script discretizes tenure into state bands (e.g. 0-12, 12-24, 24-48, 48+ months) to generate `from_state`/`to_state` transitions.
- `data/SOURCES.md` is a new file — create it in Phase 01 alongside the seed script.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 01 scope.

</deferred>

---

*Phase: 01-markov-engine*
*Context gathered: 2026-05-29*

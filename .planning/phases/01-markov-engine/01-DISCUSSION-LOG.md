# Phase 01: Markov Engine — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-29
**Phase:** 01-markov-engine
**Areas discussed:** Brand share data source, M2 forecast extrapolation, Test depth, DuckDB schema, Monte Carlo vectorization

---

## Brand Share Data Source

| Option | Description | Selected |
|--------|-------------|----------|
| Synthetic DGP (FMCG domain) | Generate realistic market share dataset with documented parameters, distinct domain from Chan 2015 telecom | ✓ |
| Mirror Chan 2015 telecom | Use the 4-provider telecom example from the paper as DGP | |
| Real Kaggle dataset | Find genuine market share CSV, requires API key or manual download | |
| Both: synthetic default + Kaggle optional | Seed uses synthetic by default, README documents swap-in path | |

**User's choice:** Synthetic FMCG DGP — distinct from Chan 2015 telecom, shows engine generalises
**Notes:** Churn domain separately uses IBM Telco Customer Churn CSV committed to repo at `data/seed/telco_churn.csv`. `.gitignore` amended to track `data/seed/*.csv`. `data/SOURCES.md` to be created documenting origin and license rationale.

---

## M2 Forecast Extrapolation

| Option | Description | Selected |
|--------|-------------|----------|
| Hold last P_t constant | Use most recent P_t for all steps beyond training window | ✓ |
| Average all P_t matrices | Compute mean(P_t) for extrapolation steps | |
| Raise ValueError | Strict mode: caller must supply enough matrices | |

**User's choice:** Hold last P_t constant (for both M2 and M3)
**Notes:** M3Extended follows same rule — hold last P_t, keep G constant. Both docstrings must note the fallback behavior explicitly.

---

## Test Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Regression-first (80% coverage) | Un-skip existing tests + Chan 2015 regression + targeted coverage | ✓ |
| Comprehensive parametric suite now | Full parameterized + property-based tests upfront | |

**User's choice:** Regression-first — Phase 05 QA handles comprehensive parametric coverage
**Notes:** DuckDB integration tests (DATA-02, DATA-03) written in Phase 01, not deferred. `temp_duckdb_path` fixture already in conftest.py.

---

## DuckDB Schema

| Option | Description | Selected |
|--------|-------------|----------|
| JSON columns as-is | Keep existing schema.sql JSON storage for matrices/arrays | ✓ |
| Migrate to DOUBLE[][] native | Replace JSON with DuckDB native array types | |
| No composite PK on transitions | Append-only log semantics | ✓ |
| Composite PK (dataset_id, entity_id, period) | DB-enforced dedup | |

**User's choice:** JSON confirmed as-is; transitions stays without PK
**Notes (user-added before CONTEXT.md):**
- Seed idempotency via `DELETE WHERE dataset_id` + `INSERT`, not DB uniqueness constraints
- `core/db/serialization.py` to be created with `ndarray ↔ JSON` helpers, NaN/Inf rejection at boundary, round-trip tests

---

## Monte Carlo Vectorization

| Option | Description | Selected |
|--------|-------------|----------|
| Vectorized cumsum + inverse-CDF | Pre-compute cum_matrix, vectorized argmax per step, ~50ms | ✓ |
| rng.multinomial per step | ~200ms, simpler code | |
| Naive loop | ~10s, unacceptable for demo | |
| Return raw paths (n_sims, n_steps+1) | Full paths array for downstream quantile computation | ✓ |
| Return SimulationResult directly | Assemble inside simulate() | |

**User's choice:** Vectorized cumsum + inverse-CDF; return raw paths
**Notes (user-added before CONTEXT.md):** Additional implementation safeguards specified:
1. `cum_matrix[:, -1] = 1.0` after cumsum (float boundary fix)
2. `start_state` accepts `Union[int, np.ndarray]` — int for single state, ndarray for initial distribution
3. Return dtype `int64`, shape `(n_sims, n_steps+1)`
4. `np.random.default_rng(seed)` only, never legacy
5. Calibration applied AFTER simulation, never inside loop
6. No threading/multiprocessing (Streamlit Cloud 1 CPU)

---

## Calibration Design

| Option | Description | Selected |
|--------|-------------|----------|
| Linear interpolation via np.interp() | Monotonic, no overshoot, standard practice | ✓ |
| Cubic spline | Smoother but can overshoot near extremes | |
| Piecewise constant (step function) | Simpler but discontinuous | |

**User's choice:** Linear interpolation via `np.interp()`
**Notes:** Table is dense enough that method choice has negligible impact on output.

---

## P_t / G Storage Format

| Option | Description | Selected |
|--------|-------------|----------|
| np.ndarray shape (n_periods, n_states, n_states) | Single 3D array, cleaner indexing, easier serialization | ✓ |
| list[np.ndarray] | Current stub signature accepts list | |

**User's choice:** 3D NumPy array for P_t_sequence; G as ndarray shape (n_states,) or (n_periods, n_states)

---

## Claude's Discretion

- Exact synthetic FMCG DGP parameters (brand count, period count, P values)
- ID generation for DB PKs
- MAPE edge-case handling for zero-actual rows
- Test file organization (per-module vs consolidated)
- Whether `build_transition_matrix()` returns a sparsity mask alongside matrix + counts

---

## Deferred Ideas

None — all discussion stayed within Phase 01 scope.

"""Seed local DuckDB with brand-share + churn datasets.

Per CONTEXT.md decisions:
- D-01: Brand share uses a synthetic FMCG data-generating process (5 brands x 24 periods).
- D-02: Churn uses the IBM Telco CSV committed at data/seed/telco_churn.csv with Contract
  type + tenure discretized into ['active', 'at_risk', 'inactive'] + absorbing 'churned' state.
- D-23: Idempotency via DELETE-WHERE-dataset_id before INSERT for every table.
- DATA-02 Roadmap SC 5: forecasts table must contain >= 5 reference rows after seed.

Churn state mapping (4 states, derived from Contract + tenure):
- 'inactive':  tenure <= 6 months (new customer, not yet engaged)
- 'at_risk':   Contract == 'Month-to-month' AND tenure > 6
- 'active':    Contract in ('One year', 'Two year') AND tenure > 6
- 'churned':   Churn == 'Yes' (absorbing terminal state)

Synthetic FMCG DGP parameters (Claude's Discretion):
- Brands: Alpha, Beta, Gamma, Delta, Epsilon (n=5)
- Periods: 24 (monthly, simulating ~2 years)
- Initial share: [0.35, 0.25, 0.20, 0.12, 0.08]
- Base P matrix: hand-crafted plausible m1-like row-stochastic 5x5 (see P_BASE_FMCG)
- Per-period variation: small Dirichlet noise around P_BASE (drives M2/M3 interest)
- Aggregate transitions = (share_t[i] * P_BASE[i,j]) scaled to integer 'weight' units

Run with:
    uv run python scripts/seed_data.py
"""

from __future__ import annotations

import logging
import sys
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.db.connection import get_connection, init_schema  # noqa: E402
from core.db.queries import (  # noqa: E402
    build_transition_matrix,
    bulk_insert_transitions,
    register_dataset,
)
from core.db.serialization import ndarray_to_json  # noqa: E402
from core.io.loaders import validate_transitions_df  # noqa: E402
from core.models import M1Homogeneous, M2TimeVarying  # noqa: E402

log = logging.getLogger(__name__)

BRAND_SHARE_DATASET_ID: str = "ds_brand_share_synthetic"
CHURN_DATASET_ID: str = "ds_churn_telco"

FMCG_BRANDS: list[str] = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
FMCG_N_PERIODS: int = 24
FMCG_INITIAL_SHARE: np.ndarray = np.array([0.35, 0.25, 0.20, 0.12, 0.08])
FMCG_TOTAL_MARKET_UNITS: int = 100_000
FMCG_DIRICHLET_CONCENTRATION: float = 200.0  # higher = less noise per period

P_BASE_FMCG: np.ndarray = np.array(
    [
        [0.90, 0.04, 0.03, 0.02, 0.01],
        [0.05, 0.85, 0.05, 0.03, 0.02],
        [0.04, 0.06, 0.82, 0.05, 0.03],
        [0.03, 0.05, 0.06, 0.80, 0.06],
        [0.02, 0.03, 0.05, 0.07, 0.83],
    ],
    dtype=np.float64,
)

# Churn state thresholds
INACTIVE_TENURE_THRESHOLD: int = 6  # months; <= this → 'inactive'
CHURNED_STATE: str = "churned"

REFERENCE_FORECAST_HORIZON: int = 12
RNG_SEED: int = 42


def _customer_state(tenure: float, contract: str) -> str:
    """Map tenure (months) + contract type to a churn state label.

    States:
    - 'inactive'  : tenure <= 6 (new customer, not yet engaged regardless of contract)
    - 'at_risk'   : Month-to-month contract AND tenure > 6
    - 'active'    : One year / Two year contract AND tenure > 6
    """
    if tenure <= INACTIVE_TENURE_THRESHOLD:
        return "inactive"
    if contract == "Month-to-month":
        return "at_risk"
    return "active"


def _delete_dataset_rows(conn, dataset_id: str) -> None:
    """D-23 idempotency: remove every row tied to a dataset_id across all tables."""
    conn.execute("DELETE FROM forecasts WHERE dataset_id = ?", [dataset_id])
    conn.execute(
        "DELETE FROM simulation_runs WHERE matrix_id IN "
        "(SELECT id FROM transition_matrices WHERE dataset_id = ?)",
        [dataset_id],
    )
    conn.execute("DELETE FROM transition_matrices WHERE dataset_id = ?", [dataset_id])
    conn.execute("DELETE FROM scenarios WHERE dataset_id = ?", [dataset_id])
    conn.execute("DELETE FROM transitions WHERE dataset_id = ?", [dataset_id])
    conn.execute("DELETE FROM datasets WHERE id = ?", [dataset_id])


def _generate_synthetic_fmcg(rng: np.random.Generator) -> tuple[pd.DataFrame, list[np.ndarray]]:
    """Generate synthetic FMCG transitions (long format) + per-period matrices.

    Returns
    -------
    transitions_df : pd.DataFrame
        Columns: entity_id, period, from_state, to_state, weight.
        entity_id is a synthetic aggregate id (one per brand) — weight encodes flow magnitude.
    P_t_list : list[np.ndarray]
        Per-period transition matrices (length FMCG_N_PERIODS), each shape (5, 5).
    """
    P_t_list: list[np.ndarray] = []
    rows: list[dict] = []
    share = FMCG_INITIAL_SHARE.copy()

    for period in range(1, FMCG_N_PERIODS + 1):
        P_t = np.array(
            [rng.dirichlet(P_BASE_FMCG[i] * FMCG_DIRICHLET_CONCENTRATION) for i in range(5)],
            dtype=np.float64,
        )
        P_t_list.append(P_t)

        for i, from_brand in enumerate(FMCG_BRANDS):
            for j, to_brand in enumerate(FMCG_BRANDS):
                flow = share[i] * P_t[i, j] * FMCG_TOTAL_MARKET_UNITS
                if flow >= 1:
                    rows.append(
                        {
                            "entity_id": f"fmcg_agg_{from_brand}",
                            "period": period,
                            "from_state": from_brand,
                            "to_state": to_brand,
                            "weight": float(round(flow)),
                        }
                    )
        share = share @ P_t
        share = share / share.sum()

    return pd.DataFrame(rows), P_t_list


def _load_telco_transitions(csv_path: Path) -> pd.DataFrame:
    """Parse data/seed/telco_churn.csv into long-format transitions.

    IBM Telco CSV has one row per customer with `tenure` (months), `Contract`,
    and `Churn` (Yes/No). We treat each customer as a single-period transition:
    - from_state: state inferred at (tenure - 1 months, same contract)
    - to_state:   'churned' if Churn == 'Yes', else state at current tenure

    Customers with tenure == 0 are excluded (no prior state).
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Telco CSV not found at {csv_path}. "
            "Copy WA_Fn-UseC_-Telco-Customer-Churn.csv → data/seed/telco_churn.csv"
        )
    raw = pd.read_csv(csv_path)
    raw = raw[raw["tenure"] > 0].copy()

    raw["from_state"] = raw.apply(
        lambda r: _customer_state(max(r["tenure"] - 1.0, 0.0), r["Contract"]),
        axis=1,
    )
    raw["to_state"] = raw.apply(
        lambda r: (
            CHURNED_STATE if r["Churn"] == "Yes" else _customer_state(r["tenure"], r["Contract"])
        ),
        axis=1,
    )
    return pd.DataFrame(
        {
            "entity_id": raw["customerID"].astype(str),
            "period": 1,
            "from_state": raw["from_state"],
            "to_state": raw["to_state"],
            "weight": 1.0,
        }
    )


def _store_transition_matrix(
    conn,
    dataset_id: str,
    model_type: str,
    matrix: np.ndarray,
    counts: np.ndarray,
    *,
    period: int | None = None,
) -> str:
    """Persist a computed matrix to transition_matrices, return its id."""
    matrix_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO transition_matrices "
        "(id, dataset_id, model_type, period, matrix_json, n_observations) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            matrix_id,
            dataset_id,
            model_type,
            period,
            ndarray_to_json(matrix),
            int(counts.sum()),
        ],
    )
    return matrix_id


def _store_forecast(
    conn,
    dataset_id: str,
    model_type: str,
    horizon: int,
    forecast_array: np.ndarray,
) -> None:
    """Insert one row into the forecasts table."""
    conn.execute(
        "INSERT INTO forecasts (id, dataset_id, model_type, horizon_steps, forecast_json) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            str(uuid.uuid4()),
            dataset_id,
            model_type,
            horizon,
            ndarray_to_json(forecast_array),
        ],
    )


def _seed_brand_share(conn, rng: np.random.Generator) -> None:
    """Seed FMCG brand share dataset: transitions + m1/m2 matrices + forecasts."""
    log.info("Seeding brand share dataset …")

    _delete_dataset_rows(conn, BRAND_SHARE_DATASET_ID)

    transitions_df, P_t_list = _generate_synthetic_fmcg(rng)
    validate_transitions_df(transitions_df)

    n_rows = len(transitions_df)
    register_dataset(
        conn,
        domain="brand_share",
        name="Synthetic FMCG 2024 (5 brands x 24 periods)",
        source_path="data/seed/synthetic",
        row_count=n_rows,
        n_states=len(FMCG_BRANDS),
        dataset_id=BRAND_SHARE_DATASET_ID,
        metadata={"brands": FMCG_BRANDS, "n_periods": FMCG_N_PERIODS},
    )
    bulk_insert_transitions(conn, BRAND_SHARE_DATASET_ID, transitions_df)
    log.info("  Inserted %d transition rows", n_rows)

    # m1 matrix (aggregate across all periods)
    m1_matrix, m1_counts = build_transition_matrix(conn, BRAND_SHARE_DATASET_ID)
    _store_transition_matrix(conn, BRAND_SHARE_DATASET_ID, "m1", m1_matrix, m1_counts)

    # m2 per-period matrices (one per period)
    for period in range(1, FMCG_N_PERIODS + 1):
        P_t, cnt_t = build_transition_matrix(conn, BRAND_SHARE_DATASET_ID, period=period)
        _store_transition_matrix(conn, BRAND_SHARE_DATASET_ID, "m2", P_t, cnt_t, period=period)

    # Reference forecasts (m1 and m2)
    Y_1 = FMCG_INITIAL_SHARE.copy()
    m1_model = M1Homogeneous(m1_matrix)
    m1_result = m1_model.forecast(Y_1, REFERENCE_FORECAST_HORIZON)
    _store_forecast(
        conn, BRAND_SHARE_DATASET_ID, "m1", REFERENCE_FORECAST_HORIZON, m1_result.forecast_array
    )

    P_t_sequence = np.stack(P_t_list)  # (n_periods, n_states, n_states)
    m2_model = M2TimeVarying(P_t_sequence)
    m2_result = m2_model.forecast(Y_1, REFERENCE_FORECAST_HORIZON)
    _store_forecast(
        conn, BRAND_SHARE_DATASET_ID, "m2", REFERENCE_FORECAST_HORIZON, m2_result.forecast_array
    )

    log.info("  Brand share seeding complete ✓")


def _seed_churn(conn) -> None:
    """Seed IBM Telco churn dataset: transitions + m1 matrix + forecasts."""
    log.info("Seeding churn dataset …")

    _delete_dataset_rows(conn, CHURN_DATASET_ID)

    csv_path = ROOT / "data" / "seed" / "telco_churn.csv"
    transitions_df = _load_telco_transitions(csv_path)

    n_rows = len(transitions_df)
    state_counts = transitions_df["from_state"].value_counts().to_dict()
    n_states = len(set(transitions_df["from_state"]) | set(transitions_df["to_state"]))

    register_dataset(
        conn,
        domain="churn",
        name="IBM Telco Customer Churn 2024",
        source_path="data/seed/telco_churn.csv",
        row_count=n_rows,
        n_states=n_states,
        dataset_id=CHURN_DATASET_ID,
        metadata={"source": "IBM Watson Sample Data", "state_counts": state_counts},
    )
    bulk_insert_transitions(conn, CHURN_DATASET_ID, transitions_df)
    log.info(
        "  Inserted %d transition rows (states: %s)",
        n_rows,
        sorted(set(transitions_df["from_state"]) | set(transitions_df["to_state"])),
    )

    # m1 matrix
    m1_matrix, m1_counts = build_transition_matrix(conn, CHURN_DATASET_ID)
    _store_transition_matrix(conn, CHURN_DATASET_ID, "m1", m1_matrix, m1_counts)

    # Reference forecasts (5 to satisfy DATA-02 SC 5)
    n_states_actual = m1_matrix.shape[0]
    state_labels = sorted(set(transitions_df["from_state"]) | set(transitions_df["to_state"]))
    active_idx = state_labels.index("active") if "active" in state_labels else 0

    Y_1 = np.zeros(n_states_actual, dtype=np.float64)
    Y_1[active_idx] = 1.0  # start from pure 'active' cohort

    m1_model = M1Homogeneous(m1_matrix)
    for horizon in [3, 6, 12, 18, 24]:
        result = m1_model.forecast(Y_1, horizon)
        _store_forecast(conn, CHURN_DATASET_ID, "m1", horizon, result.forecast_array)

    log.info("  Churn seeding complete ✓")


def main() -> None:
    """Seed DuckDB with all datasets. Idempotent — safe to re-run."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    log.info("Connecting to DuckDB …")
    conn = get_connection()
    init_schema(conn)

    rng = np.random.default_rng(RNG_SEED)

    _seed_brand_share(conn, rng)
    _seed_churn(conn)

    # Verify: count rows across key tables
    n_datasets = conn.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
    n_transitions = conn.execute("SELECT COUNT(*) FROM transitions").fetchone()[0]
    n_matrices = conn.execute("SELECT COUNT(*) FROM transition_matrices").fetchone()[0]
    n_forecasts = conn.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]

    log.info(
        "Seed complete — datasets=%d, transitions=%d, matrices=%d, forecasts=%d",
        n_datasets,
        n_transitions,
        n_matrices,
        n_forecasts,
    )
    assert n_forecasts >= 5, f"DATA-02 SC 5 failed: only {n_forecasts} forecast rows"


if __name__ == "__main__":
    main()

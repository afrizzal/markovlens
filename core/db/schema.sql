-- MarkovLens — DuckDB Schema
-- Idempotent: safe to re-run.
-- See docs/DATABASE.md for full reference.

CREATE TABLE IF NOT EXISTS datasets (
    id              VARCHAR PRIMARY KEY,
    domain          VARCHAR NOT NULL,
    name            VARCHAR NOT NULL,
    source_path     VARCHAR NOT NULL,
    row_count       BIGINT,
    n_states        INTEGER,
    metadata_json   JSON,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transitions (
    dataset_id      VARCHAR NOT NULL,
    entity_id       VARCHAR NOT NULL,
    period          INTEGER NOT NULL,
    from_state      VARCHAR NOT NULL,
    to_state        VARCHAR NOT NULL,
    weight          DOUBLE DEFAULT 1.0,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);

CREATE INDEX IF NOT EXISTS idx_transitions_dataset_period
    ON transitions (dataset_id, period);

CREATE INDEX IF NOT EXISTS idx_transitions_dataset_states
    ON transitions (dataset_id, from_state, to_state);

CREATE TABLE IF NOT EXISTS transition_matrices (
    id              VARCHAR PRIMARY KEY,
    dataset_id      VARCHAR NOT NULL,
    model_type      VARCHAR NOT NULL,
    period          INTEGER,
    matrix_json     JSON NOT NULL,
    n_observations  INTEGER,
    computed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);

CREATE INDEX IF NOT EXISTS idx_matrices_lookup
    ON transition_matrices (dataset_id, model_type, period);

CREATE TABLE IF NOT EXISTS simulation_runs (
    id                          VARCHAR PRIMARY KEY,
    matrix_id                   VARCHAR NOT NULL,
    start_state                 INTEGER NOT NULL,
    n_steps                     INTEGER NOT NULL,
    n_simulations               INTEGER NOT NULL,
    final_distribution_json     JSON,
    quantile_paths_json         JSON,
    raw_probability             DOUBLE,
    calibrated_probability      DOUBLE,
    seed                        INTEGER,
    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (matrix_id) REFERENCES transition_matrices(id)
);

CREATE TABLE IF NOT EXISTS forecasts (
    id                      VARCHAR PRIMARY KEY,
    dataset_id              VARCHAR NOT NULL,
    model_type              VARCHAR NOT NULL,
    horizon_steps           INTEGER NOT NULL,
    forecast_json           JSON NOT NULL,
    accuracy_metrics_json   JSON,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);

CREATE TABLE IF NOT EXISTS scenarios (
    id                          VARCHAR PRIMARY KEY,
    dataset_id                  VARCHAR NOT NULL,
    name                        VARCHAR NOT NULL,
    description                 TEXT,
    modified_transitions_json   JSON NOT NULL,
    result_json                 JSON,
    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);

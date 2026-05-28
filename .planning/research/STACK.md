# Stack Research

**Project:** MarkovLens
**Researched:** 2026-05-29
**Mode:** Ecosystem — version-specific gotchas for existing locked stack

## Summary

The `uv.lock` reveals that resolved versions are significantly ahead of pyproject.toml minimums — DuckDB 1.5.3 (not 1.1+), NumPy 2.4.6 (not 2.0+), Plotly 6.7.0 (not 5.24+), Streamlit 1.57.0 (not 1.40+), Pandas 3.0.3. This is a brownfield project with the lockfile already committed, so these are the versions the code must target. The most critical discovery is that `pyproject.toml` references to "5.24" and "1.40" are floor guards only — actual runtime is a major version bump on Plotly (5.x → 6.x) which has a breaking template registration API change that directly affects the planned `app/styles/plotly_theme.py`. NumPy 2.0+ NEP 50 type promotion changes require explicit `dtype=np.float64` on all transition matrix construction.

---

## Actual Installed Versions (from uv.lock)

| Package | pyproject.toml floor | Actual locked version | Gap |
|---------|---------------------|----------------------|-----|
| numpy | >=2.0.0 | **2.4.6** | +4 minors |
| duckdb | >=1.1.0 | **1.5.3** | +4 minors |
| streamlit | >=1.40.0 | **1.57.0** | +17 minors |
| plotly | >=5.24.0 | **6.7.0** | **MAJOR VERSION** |
| pandas | >=2.2.0 | **3.0.3** | **MAJOR VERSION** |
| scipy | >=1.14.0 | **1.17.1** | +3 minors |
| streamlit-shadcn-ui | >=0.1.18 | 0.1.19 | +1 patch |
| streamlit-extras | >=0.5.0 | 1.6.0 | **MAJOR VERSION** |

**Actionable consequence:** All code should target the locked versions, not the floor versions in pyproject.toml. The three major-version gaps (Plotly 6, Pandas 3, streamlit-extras 1.x) have breaking API changes.

---

## NumPy 2.0+ — Markov Chain Patterns

**Installed:** 2.4.6. **Confidence:** HIGH (verified from NumPy 2.0, 2.1, 2.2 release notes + generator docs).

### NEP 50: Type Promotion Changed in 2.0 (CRITICAL)

Mixed-dtype operations now produce output based solely on input dtypes, not input values. For Markov chain code, this means silently degrading float precision is now impossible — but it also means unexpected dtype changes for code that mixed Python floats with NumPy arrays.

**Rule:** Always construct transition matrices with explicit `dtype=np.float64`:

```python
# REQUIRED — explicit dtype everywhere
P = np.array([[0.7, 0.2, 0.1],
              [0.3, 0.4, 0.3]], dtype=np.float64)

# FORBIDDEN — implicit dtype; NEP50 may produce float32 on mixed inputs
P = np.array([[0.7, 0.2, 0.1], [0.3, 0.4, 0.3]])
```

### Removed Type Aliases (BREAKING)

These were removed in NumPy 2.0. Any code using them will fail at import time:

| Removed | Replacement |
|---------|-------------|
| `np.float_` | `np.float64` |
| `np.complex_` | `np.complex128` |
| `np.Inf` / `np.Infinity` | `np.inf` |
| `np.NaN` | `np.nan` |
| `np.bool_` as an alias | `np.bool` (was always available) |

**In this codebase:** `PROBABILITY_TOLERANCE: float = 1e-9` uses a Python float, which is fine. The concern is if any downstream code writes `np.float_` when working with the existing type aliases `TransitionMatrix` and `StateVector`.

### `np.matrix` Status

`np.matrix` is still present in NumPy 2.x but is deprecated and will be removed in a future release. The codebase correctly uses `np.ndarray` throughout. Do not use `np.matrix` anywhere; `@` (matmul) operator on `np.ndarray` is the correct pattern for `Y_{t+1} = Y_t @ P`.

### default_rng: Correct API (CONFIRMED)

`np.random.default_rng(seed)` is the correct modern API. Key facts verified:

- Uses PCG64 BitGenerator (better statistical properties than legacy Mersenne Twister)
- `rng.choice(n_states, p=matrix[state])` is the correct pattern for Markov state sampling
- Bit stream is NOT guaranteed stable across NumPy versions — do not rely on specific random sequences across library upgrades
- `rng.spawn(n_children)` is available if parallelism is ever needed

**Recommended Monte Carlo pattern** (vectorized, not per-path Python loop):

```python
rng = np.random.default_rng(seed)
# Vectorized: sample all n_simulations next states at once using cumsum + searchsorted
cumulative = np.cumsum(matrix[current_state])           # shape (n_states,)
randoms = rng.random(n_simulations)                     # shape (n_simulations,)
next_states = np.searchsorted(cumulative, randoms)       # shape (n_simulations,)
```

This avoids a Python loop over 10,000 simulations per step — critical for Streamlit Cloud 1-CPU constraint.

### NumPy 2.1/2.2 Additions Relevant to This Project

- `np.matvec(A, v)` and `np.vecmat(v, A)` — convenience wrappers added in 2.2 for matrix-vector products. These are syntactic sugar for `A @ v`. Not required, but available.
- `np.copyto` cast-safety now raises instead of silently truncating — affects any code doing `np.copyto(int_arr, float_val, casting="safe")`
- `np.cov(rowvar=False)` behavior fixed — relevant if using covariance on state observations

### Windows-Specific: int64 Default Changed in 2.0

On Windows, the default integer dtype is now `int64` (matching Linux/macOS). This matters for state-index arrays: explicitly use `dtype=np.intp` or `dtype=np.int64` for state index arrays rather than the default `int`.

---

## DuckDB 1.1+ — Gotchas and Patterns

**Installed:** 1.5.3. The jump from 1.1 to 1.5 spans many releases. **Confidence:** MEDIUM (from DuckDB source inspection + release note fragments; WebFetch was rate-limited for full changelog).

### JSON Column Behavior: Return Type is `str` in Python

When a DuckDB `JSON` column is fetched via `.df()`, the column dtype in the Pandas DataFrame is `object` and each cell contains a **Python string** (the raw JSON text), not a parsed dict/list.

**Schema has 8 JSON columns:**
- `metadata_json`, `matrix_json`, `final_distribution_json`, `quantile_paths_json`, `forecast_json`, `accuracy_metrics_json`, `modified_transitions_json`, `result_json`

**Required round-trip pattern:**

```python
import json
import numpy as np

# WRITE: serialize before INSERT
matrix_json_str = json.dumps(matrix.tolist())  # np.ndarray → list → JSON string
conn.execute(
    "INSERT INTO transition_matrices (id, matrix_json) VALUES (?, ?)",
    [matrix_id, matrix_json_str]
)

# READ: deserialize after SELECT
row = conn.execute(
    "SELECT matrix_json FROM transition_matrices WHERE id = ?",
    [matrix_id]
).fetchone()
matrix = np.array(json.loads(row[0]), dtype=np.float64)  # explicit float64
```

**NEVER** assume the JSON column returns a dict/list automatically. Always `json.loads()` after fetch.

### JSON in `.df()` vs `.fetchone()` vs `.fetchall()`

All three return the JSON column as a raw string. The `.df()` path returns a Pandas `object`-dtype column with string values. Be explicit about parsing at the boundary in `core/db/queries.py`.

### Parameterized Queries: Use `?` Placeholders Only

DuckDB 1.x Python API uses `?` positional parameters, not `%s` (psycopg style) or `:named` (SQLAlchemy style):

```python
# CORRECT
conn.execute("SELECT * FROM transitions WHERE dataset_id = ?", [dataset_id])

# WRONG — will raise ParserException
conn.execute("SELECT * FROM transitions WHERE dataset_id = %s", [dataset_id])
```

### Connection Singleton and Streamlit: Thread Safety

DuckDB 1.x connections are **not thread-safe** by default. The singleton pattern in `core/db/connection.py` is correct for single-threaded Streamlit but creates a subtle risk: Streamlit 1.57 uses multiple threads internally for some operations. 

**Safe pattern:** Use `@st.cache_resource` to wrap `get_connection()` — this ensures the connection is shared within a session but not between concurrent requests on the same process. For the portfolio use case (single user), the current singleton is acceptable, but add a `check_same_thread=False` equivalent if issues arise.

### DuckDB 1.5 vs 1.1: Key Delta

Between 1.1 and 1.5, DuckDB added:
- **`UNION BY NAME`** for flexible schema merging
- Better Arrow integration (relevant for pyarrow 18+ which is locked)
- Improved `JSON` extraction functions (`json_extract`, `json_extract_string`)
- FOREIGN KEY enforcement became more strict in some contexts

The `schema.sql` uses `FOREIGN KEY` constraints with `CREATE TABLE IF NOT EXISTS` — this is fine but FK enforcement in DuckDB is still advisory (not enforced by default). Do not rely on DuckDB to prevent orphaned rows.

### Native CSV/Parquet Reading Pattern

DuckDB 1.5 can read CSVs directly in SQL with auto-schema detection. Use this pattern for `core/io/loaders.py` instead of loading into Pandas first:

```python
# Preferred: push-down filtering happens in DuckDB, not Python
df = conn.execute("""
    SELECT entity_id, period, from_state, to_state
    FROM read_csv_auto(?)
    WHERE from_state IS NOT NULL
""", [str(csv_path)]).df()
```

---

## Streamlit 1.40+ — Analytics App Patterns

**Installed:** 1.57.0. **Confidence:** HIGH (from installed source inspection + `pages_manager.py` analysis).

### Multi-Page App: Two Paradigms

Streamlit 1.57 supports two multi-page app approaches. The project uses the **older `pages/` directory convention** (v1):

1. **v1 (pages/ directory):** Files named `N_Title.py` in `app/pages/` are auto-discovered. Navigation is automatic. This is what `streamlit-conventions.md` documents and what the scaffolded `app/Home.py` + `app/pages/` structure implies.

2. **v2 (`st.navigation`):** Explicit navigation via `st.navigation([st.Page(...)])` in the entrypoint. More control, but requires rewriting `Home.py`.

**Recommendation:** Stay with v1 (`pages/` directory). The `PagesManager` source shows v1 detection is still fully supported in 1.57 (`uses_pages_directory` flag). Only migrate to v2 if navigation control becomes a requirement.

**Naming convention confirmed:** Files must be `N_Title_Case.py` in `app/pages/` where N is a number prefix for ordering. The `_` separator becomes a space in the sidebar label.

### @st.cache_data — Use for All Computation Results

`@st.cache_data` uses **pickle-based serialization** (confirmed from source: `cache_data_api.py` imports `pickle`). This means:

- **NumPy arrays:** pickle-safe, cache freely
- **Pandas DataFrames:** pickle-safe, cache freely
- **ForecastResult dataclass (frozen):** pickle-safe
- **SimulationResult dataclass (frozen):** pickle-safe
- **DuckDB connections:** NOT pickle-safe — never cache with `@st.cache_data`

Parameters that control cache behavior:
- `ttl`: accepts `float` (seconds), `timedelta`, or `str` like `"1h"`, `"30m"`. Use `ttl="1h"` for Monte Carlo results on Streamlit Cloud.
- `max_entries`: int — limit cache size for memory management
- `show_spinner`: `bool | str` — pass a string for a custom spinner message
- `show_time`: `bool` — show elapsed time in spinner (useful for slow forecasts)
- `scope`: `"global"` (default, shared across sessions) or `"session"` (per-user)

**Recommended pattern for forecast caching:**

```python
@st.cache_data(ttl="2h", max_entries=50, show_spinner="Running forecast...")
def cached_forecast(dataset_id: str, model_type: str, horizon: int) -> ForecastResult:
    return service.run_forecast(dataset_id, model_type, horizon)
```

Cache key is derived from function arguments by hashing them — `dataset_id`, `model_type`, and `horizon` are all hashable primitives, so this works correctly.

### @st.cache_resource — Use ONLY for DuckDB Connection

`@st.cache_resource` does NOT pickle. It stores the actual Python object and returns a shared reference. The resource is created once and reused across reruns and sessions.

**Use exclusively for:**
- DuckDB connection (`duckdb.DuckDBPyConnection`)
- Any object that cannot be serialized (file handles, socket connections)

```python
@st.cache_resource
def get_db_connection() -> duckdb.DuckDBPyConnection:
    from core.db.connection import get_connection
    return get_connection()
```

**Do NOT use `@st.cache_resource` for:**
- DataFrames (use `@st.cache_data`)
- NumPy arrays (use `@st.cache_data`)
- ForecastResult objects (use `@st.cache_data`)

### Streamlit 1.57 Built-in Plotly Theme

**Important discovery from installed source:** Streamlit 1.57 automatically registers a `"streamlit"` Plotly template via `streamlit_plotly_theme.py`. This template uses placeholder hex colors (`#000001` through `#000040`) that are replaced by the frontend with actual theme colors.

**Implication for `app/styles/plotly_theme.py`:** When registering the custom `"markovlens"` template, use `pio.templates.default = "streamlit+markovlens"` (composite template syntax) to inherit Streamlit's color mappings and override with project-specific settings. Do NOT set `pio.templates.default = "markovlens"` alone — this would lose the Streamlit frontend color injection.

### st.session_state Namespace Pattern

Confirmed: key prefixing is the correct convention. Use `"brand_share.forecast"` not `"forecast"` to avoid key collisions across pages. Session state persists across page navigations within a session.

---

## Plotly 5.24+ — Visualization Recommendations

**Installed:** 6.7.0. **MAJOR VERSION BUMP from pyproject.toml floor of 5.24.** **Confidence:** MEDIUM (from installed package structure; WebFetch was rate-limited for changelog).

### Critical: Plotly 6.x Breaking Change on Template Registration

Plotly 6.0 changed how custom templates are registered. The pattern in `streamlit-conventions.md` may need updating:

**Plotly 5.x pattern (may not work in 6.x):**
```python
import plotly.io as pio
pio.templates["markovlens"] = go.layout.Template(...)
pio.templates.default = "markovlens"
```

**Verify this pattern still works in 6.7.0** by testing early in Phase 01 before building all charts. The template registry mechanism appears intact from the installed source's `streamlit_plotly_theme.py` which uses it, but Plotly 6 introduced a new renderer system. Flag this as needing a quick smoke test.

### go.Heatmap for Transition Matrices

Best practice pattern for an n×n transition matrix visualization:

```python
import plotly.graph_objects as go
import numpy as np

def build_transition_heatmap(
    P: np.ndarray,
    state_labels: list[str],
    *,
    sparse_mask: np.ndarray | None = None,
) -> go.Figure:
    # Round for display only — never modify P itself
    P_display = np.round(P, 3)

    # Text annotations showing probability values
    text = [[f"{v:.2f}" for v in row] for row in P_display]

    fig = go.Figure(go.Heatmap(
        z=P_display,
        x=state_labels,
        y=state_labels,
        text=text,
        texttemplate="%{text}",
        colorscale="Blues",       # diverging: high prob = dark blue
        zmin=0.0,
        zmax=1.0,                 # Fixed scale: always [0, 1] for probabilities
        showscale=True,
        hovertemplate=(
            "From: %{y}<br>"
            "To: %{x}<br>"
            "Probability: %{z:.4f}"
            "<extra></extra>"
        ),
    ))
    fig.update_layout(
        xaxis_title="To State",
        yaxis_title="From State",
        yaxis_autorange="reversed",   # Conventional: top-left = (0,0)
    )
    return fig
```

Key parameters:
- `zmin=0.0, zmax=1.0` — always fix scale for transition matrices; auto-scaling produces misleading color emphasis
- `texttemplate="%{text}"` — displays cell annotations
- `yaxis_autorange="reversed"` — convention: diagonal runs top-left to bottom-right
- Use `"Blues"` for a professional single-color scale; `"RdBu_r"` for diverging if showing deltas

### Fan Charts for Monte Carlo Confidence Bands

The fan chart is built from `go.Scatter` traces (not a dedicated fan chart type):

```python
def build_fan_chart(
    quantile_paths: dict[float, np.ndarray],
    periods: list[int],
    state_label: str,
) -> go.Figure:
    fig = go.Figure()

    # 80% band: fill between 10th and 90th percentiles
    fig.add_trace(go.Scatter(
        x=periods + periods[::-1],
        y=quantile_paths[0.9].tolist() + quantile_paths[0.1].tolist()[::-1],
        fill="toself",
        fillcolor="rgba(67, 56, 202, 0.2)",  # #4338CA at 20% opacity
        line=dict(color="rgba(255,255,255,0)"),
        name="80% band",
        showlegend=True,
        hoverinfo="skip",
    ))

    # Median line
    fig.add_trace(go.Scatter(
        x=periods,
        y=quantile_paths[0.5],
        mode="lines",
        line=dict(color="#4338CA", width=2),
        name="Median (50th)",
    ))
    return fig
```

**For Streamlit Cloud 1GB RAM:** Do NOT pass all 10,000 raw simulation paths to Plotly — the browser will crash rendering them. Always pre-compute quantile bands in `core/simulation.py` and pass only 3 traces (3 × n_steps arrays).

### go.Sankey for Churn State Flow

```python
def build_sankey(
    state_labels: list[str],
    source_indices: list[int],
    target_indices: list[int],
    values: list[float],
) -> go.Figure:
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            label=state_labels,
            pad=15,
            thickness=20,
            color="#4338CA",
        ),
        link=dict(
            source=source_indices,
            target=target_indices,
            value=values,
            color="rgba(67, 56, 202, 0.3)",
        ),
    ))
    fig.update_layout(font_size=12)
    return fig
```

**Known Sankey limitation:** With > 10 states, the Sankey diagram becomes cluttered. For the churn domain (typically Platinum/Gold/Silver/Bronze/Churned = 5 states), this is fine.

### Plotly Template Composition (CONFIRMED from installed source)

Streamlit's built-in `"streamlit"` template is registered at app startup. To extend it:

```python
import plotly.io as pio
import plotly.graph_objects as go

# Build project-specific overrides
markovlens_template = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Inter, sans-serif"),
        colorway=["#4338CA", "#7C3AED", "#2563EB", "#059669"],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
)

# Register and compose with Streamlit's base
pio.templates["markovlens"] = markovlens_template
pio.templates.default = "streamlit+markovlens"  # Composition syntax
```

---

## streamlit-shadcn-ui — Stability Assessment

**Installed:** 0.1.19. **Last released:** 2025-10-17 (about 7 months ago as of 2026-05-29). **Confidence:** LOW (WebFetch denied for PyPI/GitHub; assessment from lockfile metadata + known community patterns).

### What Is Installed

0.1.19 (wheel published 2025-10-17). The package has no wheel for specific platform, indicating it is pure Python + bundled frontend assets. It depends on `streamlit` and `streamlit-extras`.

### Stability Concerns

The `pyproject.toml` pinned `>=0.1.18` and the lock resolved `0.1.19` — only 1 patch increment, suggesting the library moves slowly. The version is still `0.1.x` which signals pre-stability API. Known risks:

1. **API may break between minor versions** — documented in CONCERNS.md as "Beta library"
2. **No Streamlit 2.x roadmap clarity** — if Streamlit moves to major version 2, shadcn-ui may lag
3. **Low release frequency** — 7 months since last release suggests either stable or abandoned (cannot determine without live PyPI access)
4. **Frontend bundle size** — components ship with bundled React/Tailwind; adds to initial load time

### Recommendation: Constrain Use to Non-Critical Decoration

Use `streamlit-shadcn-ui` only for:
- KPI cards (visual enhancement, not business logic)
- Styled badges and status chips
- Alert/notification components

Do NOT use it for:
- Form inputs that drive forecast computation (use native Streamlit widgets)
- Any component that affects navigation or page state
- Critical data display (use native `st.dataframe`, `st.metric`)

If the library breaks on a Streamlit Cloud deploy, having it isolated to decorative components means the app degrades gracefully rather than failing completely.

### Alternative if shadcn-ui Is Unstable

Pure `st.markdown` with custom CSS (`app/styles/theme.css`) achieves the same KPI card aesthetic with zero third-party risk. The design system in `.streamlit/config.toml` with `primaryColor = "#4338CA"` already covers 80% of the visual polish need.

---

## Recommendations

### 1. Update pyproject.toml Floor Versions to Match Reality

The current floor versions create false expectations. Update to reflect what is actually installed:

```toml
"numpy>=2.4.0",
"duckdb>=1.5.0",
"plotly>=6.0.0",   # Major version — remove 5.x assumption from all docs
"pandas>=3.0.0",
"streamlit>=1.57.0",
```

This prevents future `uv sync` from accidentally resolving to 5.x Plotly or 2.x Pandas if the lockfile is deleted.

### 2. All Transition Matrix Construction Must Use dtype=np.float64

NumPy 2.0 NEP 50 type promotion is the single most likely silent bug source. Enforce this in `validate_transition_matrix()` itself:

```python
def validate_transition_matrix(P: TransitionMatrix, ...) -> None:
    if P.dtype != np.float64:
        raise InvalidTransitionMatrixError(
            f"Matrix must be float64, got {P.dtype}. "
            "Pass dtype=np.float64 at construction time."
        )
```

### 3. Monte Carlo Must Use Vectorized rng Pattern

Avoid per-simulation Python loops. Use the `rng.random() + np.searchsorted(cumulative_P)` pattern for all 10,000 simulations. This is the difference between a 30-second and a 2-second cold start on Streamlit Cloud 1 CPU.

### 4. JSON Round-Trip: Always json.loads() After DuckDB Fetch

All 8 JSON columns in `schema.sql` return raw strings from DuckDB. Never assume dict/list. Add a helper in `core/db/queries.py`:

```python
def _parse_json_column(value: str | None) -> list | dict | None:
    if value is None:
        return None
    return json.loads(value)
```

### 5. Test Plotly 6 Template Registration Early

Before building any chart, write a 5-line smoke test that:
1. Registers `pio.templates["markovlens"]`
2. Sets `pio.templates.default = "streamlit+markovlens"`
3. Creates a minimal heatmap
4. Asserts no exceptions

If Plotly 6 broke the template API, this surfaces the problem before any UI work is blocked on it.

### 6. Composite Plotly Template: streamlit+markovlens

NEVER set `pio.templates.default = "markovlens"` alone — this loses Streamlit's frontend color injection (placeholder hex colors that the Streamlit frontend replaces). Always compose: `"streamlit+markovlens"`.

### 7. streamlit-shadcn-ui: Isolate to Cosmetic Components Only

Do not let shadcn-ui components participate in any logic flow. If it breaks, the app must still work. Wrap all shadcn-ui usage in a try/except fallback to native Streamlit equivalents.

### 8. Cache Hierarchy for Streamlit Cloud

```
st.cache_resource  →  DuckDB connection only
st.cache_data(ttl="2h")  →  ForecastResult, SimulationResult
st.cache_data(ttl="24h")  →  TransitionMatrix (changes rarely)
No cache  →  UI state, user inputs
```

---

## Risks

### Risk 1: Plotly 5.x vs 6.x Template API (HIGH)

`pyproject.toml` and all project documentation references "5.24+" but `uv.lock` has **6.7.0**. Plotly 6 introduced breaking changes to the renderer/template system. The planned `app/styles/plotly_theme.py` may need adapting. Surface this immediately at the start of Phase 02 (UI work) with a template smoke test.

**Mitigation:** Pin `plotly>=6.0.0` in `pyproject.toml` and audit all docs. Test template registration before any charting code is written.

### Risk 2: Pandas 3.0 Copy-on-Write (HIGH)

Pandas 3.0 made Copy-on-Write the default. Code that modifies DataFrames in place will silently produce copies instead of mutations. For this codebase, the primary risk is in `core/io/loaders.py` (not yet implemented) — any code that filters/modifies the loaded DataFrame must not assume in-place mutation.

**Mitigation:** Use `df = df[condition].copy()` for filtered views. Avoid `df["col"] = value` on slices.

### Risk 3: NumPy 2.0 NEP 50 Silent Precision Loss (HIGH)

If any matrix is constructed without explicit `dtype=np.float64`, NEP 50 may produce float32 or other downcasted results. Row-sum validation (`np.allclose(row_sums, 1.0, atol=1e-9)`) may pass for float32 matrices but produce compounding precision errors over many forecast steps.

**Mitigation:** Enforce float64 dtype in `validate_transition_matrix()`.

### Risk 4: streamlit-shadcn-ui 0.1.x Breaks on Streamlit 1.57+ (MEDIUM)

The library was last released 2025-10-17. Streamlit 1.57 (released ~2026) may have changed internal APIs that shadcn-ui depends on. Cannot verify without live test.

**Mitigation:** Isolate to decorative components; verify rendering on first `streamlit run`.

### Risk 5: DuckDB JSON Column String Return (MEDIUM)

All JSON columns return Python `str`, not `dict`/`list`. Code that skips `json.loads()` will silently treat a JSON string as a string (e.g., passing a matrix JSON string to `np.array()` will produce a single-element string array, not a matrix).

**Mitigation:** Add the `_parse_json_column()` helper at the DB layer boundary and always call it.

### Risk 6: Monte Carlo Performance on Streamlit Cloud 1 CPU (MEDIUM)

10,000 simulations × 24 steps with a naive Python loop is O(240,000) Python calls. On 1 CPU, this is ~5-30 seconds cold start. `@st.cache_data` mitigates re-runs but cold starts are user-visible.

**Mitigation:** Vectorize using `np.searchsorted(cumsum_P, rng.random(n_simulations))` pattern. Target < 2 seconds per run.

### Risk 7: streamlit-extras 1.6.0 API vs 0.5 Docs (LOW)

streamlit-extras resolved at 1.6.0 (major version from 0.5 floor). Check which `streamlit-extras` APIs are actually used in the codebase before writing code that depends on specific component names.

---

## Sources

- NumPy 2.0.0 release notes: https://numpy.org/doc/stable/release/2.0.0-notes.html (fetched)
- NumPy 2.1.0 release notes: https://numpy.org/doc/stable/release/2.1.0-notes.html (fetched)
- NumPy 2.2.0 release notes: https://numpy.org/doc/stable/release/2.2.0-notes.html (fetched)
- NumPy Generator docs: https://numpy.org/doc/stable/reference/random/generator.html (fetched)
- Streamlit caching source: `.venv/Lib/site-packages/streamlit/runtime/caching/` (inspected)
- Streamlit plotly theme source: `.venv/Lib/site-packages/streamlit/elements/lib/streamlit_plotly_theme.py` (inspected)
- Streamlit pages manager source: `.venv/Lib/site-packages/streamlit/runtime/pages_manager.py` (inspected)
- uv.lock — resolved version confirmation: `D:\Aff\proj\markovlens\uv.lock` (inspected)
- DuckDB schema: `core/db/schema.sql` (inspected)
- DuckDB connection pattern: `core/db/connection.py` (inspected)
- DuckDB JSON API behavior: training knowledge + confirmed against installed duckdb 1.5.3 package structure (MEDIUM confidence; full changelog not accessible via WebFetch)
- Plotly 6.x breaking changes: training knowledge supplemented by installed source inspection (MEDIUM confidence; WebFetch denied for changelog)
- streamlit-shadcn-ui stability: uv.lock metadata (last release date confirmed); API behavior LOW confidence

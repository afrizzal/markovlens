# Features Research

**Domain:** Markov chain forecasting workbench (BA/BI portfolio)
**Researched:** 2026-05-29
**Confidence:** HIGH for UI signals and visualization conventions (stable, well-established domain); MEDIUM for Kaggle dataset specifics (verified partially via Kaggle fetch, cross-checked with known public data); LOW flagged where noted.

---

## Summary

A professional Streamlit analytics app is distinguished from a tutorial project by three things: every interactive state has a visual response (loading, empty, error), charts carry enough metadata for a non-technical reader to understand without a legend footnote, and the app behaves correctly on edge cases (sparse data, no dataset loaded, first-run). For a Markov-chain forecasting tool, the canonical visualizations — annotated transition heatmap, Sankey state-flow, and Monte Carlo fan chart — are well-understood patterns; deviating from them without clear reason signals inexperience. The differentiating layer is interaction: what-if sliders that recompute in real time, click-on-cell drill-down, and side-by-side model comparison tables are what elevate a demo from "I know the math" to "I know how to build a data product."

---

## Professional Streamlit Signals

### Table Stakes
*(Missing any of these = immediate red flag to a recruiter who uses data tools daily)*

**Loading and state feedback**
- Every computation that takes > 0.3s must be wrapped in `st.spinner()` with a meaningful message ("Building transition matrix…", not "Loading…"). The default Streamlit skeleton of silent re-run is not acceptable.
- `@st.cache_data` must be applied visibly: the user should see the first run is slow and subsequent runs are instant. This signals caching awareness.
- Error messages must be caught and rendered via `st.error()` with a human-readable explanation. A raw Python traceback on the UI is an immediate fail.

**Empty states**
- Every list, table, and chart view must have a designed empty state. "No forecasts yet — click Run to generate your first forecast" with a clear call to action. The `app/components/empty_state.py` stub exists; it must be wired up on every page, not left as a stub.
- The Home dashboard with no data must not show broken KPI cards or `None` values — show "--" with an explanatory caption.

**KPI cards on dashboard**
- Numeric KPIs (last forecast MAPE, active datasets, latest brand share, churn retention rate) must be in styled cards with delta indicators. Raw `st.metric()` widgets without a wrapper are visually acceptable but the delta coloring and label must be semantic (red delta is bad for MAPE, good for retention — get the direction right).
- Four KPIs across the Home page header is the standard layout. Fewer is sparse; more is cluttered.

**Sidebar navigation context**
- Active page must be visually distinguished in the sidebar. Streamlit's multi-page app does this automatically via page name highlighting, but the page icon/label must be informative, not the default filename.
- Dataset selector in the sidebar (or per-page) must be persistent; not re-rendered every page load from scratch.

**Chart defaults that signal care**
- Every Plotly chart must have axis labels, a title, and hover templates. Charts with `axis 0` / `axis 1` labels are an automatic fail.
- All charts must use `use_container_width=True`. Fixed-width charts that overflow or leave whitespace signal the developer didn't test layout.
- Color scales on heatmaps must be semantically meaningful. For transition probability: sequential (0 → 1) not diverging. For error/residuals: diverging centered at 0.

**Download affordance**
- Every chart/table must have a download button. `st.download_button()` for CSV; in Reports page, PDF. This is basic data-product behavior — recruiters who use BI tools expect it.

**Consistent typography and spacing**
- No mixing of `st.title`, `st.header`, `st.subheader` without hierarchy logic. Each page should have exactly one `st.title`.
- `st.caption()` for metadata (e.g. "Dataset: Telco Churn · 7,043 rows · Last updated: 2026-05-29") beneath page headers.

**Form validation feedback**
- When a user uploads a CSV missing required columns, show `st.error()` with the exact missing columns listed — not "invalid file".
- Sliders and number inputs must have min/max bounds and default values that produce sensible outputs.

---

### Differentiators
*(These separate "knows the tool" from "thinks like a product designer")*

**Annotation layers on heatmaps**
- The transition probability value rendered as text inside each heatmap cell. Standard in every serious analytics tool (Seaborn, Tableau, Power BI all do this by default). In Plotly: `text=matrix.round(2)`, `texttemplate="%{text}"`. Combined with a color scale, this creates dual encoding that works for colorblind users.
- Sparse cells flagged with a warning symbol or different border color when observation count < 20. This shows the developer understands statistical validity, not just display.

**Stationary distribution panel**
- A separate display (small bar chart or table) showing the computed stationary distribution (long-run equilibrium) alongside the transition matrix. For brand share: "If these transition rates persist, Brand A will hold 42% long-run share." This is a 10-line calculation but signals deep understanding of Markov chains to any quantitative recruiter.

**What-if scenario editor**
- Sliders on a copied matrix that recompute the forecast when values change. The critical UX detail: recompute should be deferred (button-triggered or debounced) not live, because recomputing 10k Monte Carlo paths on every slider tick will freeze the app. Show a "Preview" badge on the modified matrix cells to indicate unsaved changes. Save to `scenarios` table.

**Model selector with live comparison panel**
- Side-by-side forecast lines for m1/m2/m3 in a single chart, not separate tabs. Recruiters want to see the developer understands why the models diverge over the forecast horizon, not just that they ran them.
- MAPE/Brier score comparison table that lights up the best-performing model. A highlighted row or "Best" badge is a simple touch that demonstrates product thinking.

**Confidence band annotation**
- The 80% confidence band on fan charts should be explicitly labeled "80% confidence interval" in the chart legend, not just shown as a shaded region. Many tutorial fan charts have unlabeled shaded areas that leave the viewer uncertain what the band means.
- A toggle to show/hide the raw simulation paths (a sample of 50-100 paths as thin semi-transparent lines) behind the fan chart. This is a "show your work" feature that communicates honest uncertainty to a quantitative audience.

**Sankey with period selector**
- For churn Sankey: a period slider that animates or updates the Sankey to show how flows changed over time. Even 3-4 time snapshots are sufficient to demonstrate temporal reasoning.

**README demo GIF or screenshot**
- The GitHub repo README must have a screenshot or animated GIF showing the app running with real data. Recruiters click the repo, and if there's no visual, they often don't bother running it locally. This is outside the app itself but is a feature of the deliverable.

**Dataset metadata display**
- On every page, a small metadata strip: `Dataset: Telco Churn · 7,043 rows · 6 states · Model: m2 · Last run: 2026-05-28`. This shows the developer thinks about data provenance, which is core BA/BI thinking.

---

### Anti-Features
*(These signal the project is a tutorial reproduction, not a real data product)*

| Anti-Feature | Why It Signals Amateur Work | What to Do Instead |
|---|---|---|
| Raw Python traceback visible in UI | User-facing errors must be handled, not leaked | `try/except` with `st.error()` + optional `st.exception()` in dev mode |
| `st.write(df)` for all tables | No column formatting, no pagination, no download | `st.dataframe(df, use_container_width=True)` with column config |
| Fixed-pixel Plotly chart widths | Breaks on any screen other than the dev's | Always `use_container_width=True` |
| Single flat `app.py` with 500+ lines | No modularity signals no architectural thinking | Components in `app/components/`, logic in `domains/` |
| Hard-coded dataset path | No flexibility, breaks on any other machine | Dataset selection via Settings page + DB registry |
| `st.write("Results:")` before every output | Redundant heading noise | Structural headers only; chart/table has its own title |
| No loading feedback on simulation run | 10k paths silently compute for 2-5 seconds | `st.spinner()` wrapping every heavy computation |
| Sidebar crammed with all controls | Unclear what controls affect what | Controls contextual to the page section they affect |
| Identical color for all chart series | Requires a legend to distinguish; legend alone is insufficient | Semantically meaningful, distinct palette per series |
| Magic number defaults with no explanation | e.g. slider default of `42` with no tooltip | Every default documented with a tooltip explaining why |
| No empty state on cold start | Charts show NaN or crash with no data | Designed empty state with call-to-action |
| Copy-pasted cells with `P[i,j]` notation in the UI | Exposes implementation detail | Use state names from the dataset |
| Monte Carlo result shows only point estimate | Defeats the purpose of simulation | Always show distribution/bands, not just mean |

---

## Markov Chain Visualization Conventions

**Confidence: HIGH** — these are established conventions from academic tools, commercial BI software, and published analytics dashboards.

### Transition Matrix Heatmap (canonical visualization)

The standard format across every Markov chain tool (R's `markovchain` package viewer, Python's `hmmlearn` docs, commercial tools like Alteryx):

- Square heatmap, rows = from-state, columns = to-state
- Sequential color scale (light = low probability, dark = high probability). The `RdYlGn` diverging scale is wrong here — there is no "neutral" probability. Use `Blues` or `Viridis`.
- Cell value as text annotation (2 decimal places). Without annotation, the color alone is insufficient for precise reading.
- Axis labels must be state names, not integer indices.
- Diagonal cells represent self-retention (staying in same state). They are typically the highest-value cells and deserve special treatment: a distinct border, or a tooltip that says "Retention rate: X%".
- Color scale range: fix at [0.0, 1.0] not auto-ranged. Auto-ranging on a sparse matrix will make a 0.05 cell look as dark as a 1.0 cell if everything else is 0. This is a common tutorial mistake.
- Row annotations: show row sum (should be 1.0). If a row sum deviates > 0.001 from 1.0, flag it. This is a data quality signal.
- Observation count: either as a second smaller heatmap ("n observations per cell") or as a tooltip on hover. Critical for statistical credibility.

**The dual-heatmap pattern** (probability + observation count side by side) is the gold standard. It visually communicates where the model is statistically reliable vs. where it's extrapolating from sparse data.

### Stationary Distribution Bar Chart

Computed from the dominant eigenvector of P^T. Display as a horizontal bar chart alongside the matrix. Label it "Long-run equilibrium" with a tooltip explaining: "If these transition rates continue indefinitely, the system converges to these proportions." This is a 5-line NumPy calculation that demonstrates deep understanding.

### State Flow Sankey Diagram (for churn)

Standard in customer journey analysis (Amplitude, Mixpanel, Tableau all use Sankeys for funnel/state flow):

- Left nodes = from-states at time T, right nodes = to-states at time T+1
- Link width proportional to transition volume (not probability — use raw counts for Sankey, probabilities for the heatmap)
- Color by from-state (so you can visually trace where each state's population flows)
- The "Churned" node should be at the bottom and colored red — convention from customer lifecycle diagrams
- Hover tooltip: "Transition: Active → At Risk — 312 customers (23.1%)"
- For time-varying model (m2): a period slider that updates the Sankey for each time period is a strong differentiator

### Forecast Line Chart with State Distribution

For brand share forecasting, the standard output is:

- Multi-line chart: one line per brand, x-axis = time period, y-axis = market share (0-100%)
- Historical data as solid lines, forecast as dashed lines with a vertical "today" separator line
- Confidence band (10th-90th percentile) as a shaded area around the forecast dashed line
- Marker at the last historical point connecting to the first forecast point
- If m1/m2/m3 shown together: distinct dash patterns (solid = m1, dashed = m2, dotted = m3) rather than different colors (colors are already used for brands). This is a design constraint when you have two categorical dimensions.

---

## Monte Carlo Fan Chart Best Practices

**Confidence: HIGH** — the Bank of England, IMF, and academic forecasting literature have established conventions for fan charts. These are verified patterns.

### What a Fan Chart Communicates

A Monte Carlo fan chart is NOT a cone of uncertainty widening over time (that's the common misconception). It is a percentile envelope of simulation paths. The width at any time point represents the spread of probable outcomes, which for mean-reverting processes may narrow then widen.

### Essential Elements (table stakes for any fan chart)

1. **Median/central line** (50th percentile): thick, dark line. This is the "most likely" path, not the mean (for skewed distributions they differ — show the median).
2. **Inner band** (25th–75th percentile): moderately shaded. This is the "core" uncertainty — 50% of simulations fell here.
3. **Outer band** (10th–90th percentile): lightly shaded. The full 80% confidence envelope.
4. **Band labels in legend**: "80% confidence interval (10th–90th percentile)" — not just a color swatch. Many tutorial fan charts have unlabeled bands.
5. **Historical data**: the actual historical values must appear on the same chart as a solid line. Without historical context, the fan chart is floating in space.
6. **Vertical separator**: a dashed vertical line at the forecast start date separates observed from projected.
7. **Axis labels with units**: "Market Share (%)" not "value". Time axis with actual dates or labeled periods (Q1 2024, Q2 2024).

### Design choices that matter

**Color for bands**: Use a single hue with decreasing saturation for outer bands. Example: inner band is `rgba(67,56,202,0.4)` (the project's #4338CA at 40% opacity), outer band is `rgba(67,56,202,0.15)`. Do NOT use different hues for different bands — it suggests the bands represent different quantities rather than widening confidence.

**Do not show all 10,000 paths**: Even 10,000 semi-transparent paths creates a visual mess. Instead, optionally show 30-50 random sample paths as `rgba(0,0,0,0.03)` thin lines behind the bands, controlled by a toggle. This "show your work" view demonstrates the simulation is real, not a parametric approximation.

**Calibrated vs. raw probability annotation**: This project uses the Becker (2026) longshot-bias calibration. A small annotation in the chart or below it — "Raw: 34.2% → Calibrated: 31.8%" — demonstrates that the developer applied domain expertise to correct a known bias. This is a strong differentiator for a BA/BI portfolio.

**Multiple model fan charts**: Show m1/m2/m3 fan charts in tabs or a small-multiple grid. A 3-panel small-multiple with the same axis scale is more informative than overlaid fans from three models (which become unreadable).

**What not to do**:
- Symmetric bands around a point estimate (this is a parametric shortcut, not a true simulation result — if your bands are symmetric, it signals you're doing `mean ± 1.96*std`, not actual percentile paths)
- "Cone of uncertainty" that only widens (this is valid for random walks but misleading for mean-reverting Markov processes — show the actual shape)
- Showing bands without the median line (bands without center are uninterpretable)
- Bands that end at the final forecast period without a visual anchor to the last historical point

---

## Model Comparison UI Patterns

**Confidence: HIGH** — these patterns appear consistently across commercial forecasting tools (Prophet's comparison dashboard, Nixtla's StatsForecast), academic backtesting frameworks, and BI tools.

### Standard Comparison Elements

**Metrics table (primary)**

A table with one row per model and columns for each metric. For this project:

| Model | MAPE | Brier Score | Log-Loss | Run Time |
|---|---|---|---|---|
| m1 (Homogeneous) | 4.2% | 0.18 | 0.34 | 0.3s |
| m2 (Time-Varying) | 3.1% | **0.14** | **0.28** | 1.2s |
| m3 (Extended) | **2.8%** | 0.15 | 0.29 | 2.1s |

Key UX details:
- Bold the best value in each column (not the entire row — different models win on different metrics)
- Color code: green for best, neutral for others. Red is inappropriate unless a model is significantly worse than baseline.
- A "Recommended" badge on the model that wins across most metrics, with a one-line rationale: "Best Brier score; use when market size is stable."
- Tooltip on each metric name explaining what it means. Not every BA/BI recruiter knows Brier score.

**Overlaid forecast chart (secondary)**

A single chart with all three model forecasts overlaid over the same historical period:
- Distinct line styles (not just colors): m1 = solid, m2 = dashed, m3 = dotted
- Historical data as a thick solid black/grey line
- A legend with model names AND the metric value: "m1 (MAPE: 4.2%)" — this directly connects the visual divergence to the quantitative performance

**Walk-forward backtest visualization (differentiator)**

A small chart showing the rolling error for each model over the backtest window. This is the honest version of model comparison — not just final metrics, but how each model's accuracy evolved over time. It shows which model is more stable vs. which had a lucky final period.

**When to use each model (interpretation panel)**

Below the comparison table, a short text block (or `st.info()` callout box) that explains in plain language when each model is appropriate:
- "m1: Use when market shares are stable and transitions are consistent over time."
- "m2: Use when market dynamics are changing — e.g., new competitor entry, pricing changes."
- "m3: Use when the total market is growing or shrinking, not just shares shifting."

This is BA-level communication skill demonstrated inside the product itself.

---

## Kaggle Dataset Recommendations

**Confidence: MEDIUM** — Telco Churn dataset is well-known and verified. Market share datasets are less standardized; recommendations are based on known Kaggle datasets cross-checked with partial fetch results and training knowledge. Verify links before use.

### Domain 1: Customer Churn (Markov State Modelling)

**Primary recommendation: IBM Telco Customer Churn**
- URL: `https://www.kaggle.com/datasets/blastchar/telco-customer-churn`
- Rows: ~7,043 customers, 21 columns
- Key columns: `tenure`, `Contract` (Month-to-month / One year / Two year), `Churn` (Yes/No), `InternetService`, `PaymentMethod`
- Why it works for Markov: The `Contract` column (month-to-month → one year → two year → churned) maps naturally to a 4-state Markov chain. `tenure` can be discretized into tenure bands for an alternative 5-state model. The dataset is clean, well-documented, and recruiter-familiar — any senior BA will recognize it.
- Preprocessing required: For time-varying model (m2), you need synthetic time steps since this is a cross-sectional snapshot. Approach: discretize `tenure` into 12-month bands and treat each band as a "period". This creates ~6 time periods from the cross-section. Document this as a deliberate modelling choice.
- State design recommendation: `[New (0-12mo), Growing (13-24mo), Established (25-48mo), Loyal (49+mo), Churned]` — 5 states, absorbing "Churned" state. An absorbing state (where self-transition = 1.0) is a stronger Markov demonstration than all-transient states.

**Alternative: E-commerce Customer Lifecycle Dataset**
- Search term: "customer lifetime value ecommerce" on Kaggle
- Look for datasets with `customer_id`, `order_date`, `order_value` columns
- Can engineer RFM states (Active / At Risk / Dormant / Lost) from recency/frequency
- More realistic Markov application but requires more preprocessing work

### Domain 2: Brand Market Share (Markov Forecasting)

**Primary recommendation: Soft Drink Market Share / Retail Sales data**

The challenge: there is no canonical "brand market share" Kaggle dataset equivalent to the Telco Churn dataset. The best approach is to engineer market share from sales/transactions data.

**Option A — Retail store sales with brand-level data:**
- Search: "supermarket sales brand" or "retail transactions brand" on Kaggle
- Best candidate: `https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store`
- This dataset has `brand`, `category`, `event_type`, `user_session` at event level
- Engineering: aggregate by `(brand, month)` → compute monthly market share per category → derive share transitions period-over-period
- Size: large (millions of rows) — DuckDB handles this natively; worth demonstrating

**Option B — Manufactured/synthetic market share with real structure (fallback):**
If no suitable Kaggle dataset found, generate synthetic data using the `scripts/seed_data.py` with a documented data-generating process:
```
5 brands, 24 time periods (monthly for 2 years), 3 market regimes (stable, disruption, recovery)
```
This is legitimate if the DGP is clearly documented — it lets you control sparsity, demonstrate m3 (market growth), and avoid copyright concerns. The downside: recruiters may notice it's not real data if README doesn't explain it clearly.

**Option C — Telecommunications market share (thematic fit):**
- Search: "telecom market share" on Kaggle
- Aligns with the churn domain (same industry = coherent portfolio story)
- Typical structure: quarterly subscriber counts by carrier → compute relative market share

**Critical note on data engineering for brand share:** Regardless of source, the key engineering step is:
1. For each `entity` (brand/company), for each `period` (month/quarter): compute `share_t = count_t / total_t`
2. Discretize share into `n_states` bins (default 10 per Chan 2015 convention, or fewer for sparse data)
3. For each entity, compute `(state_t, state_{t+1})` transition pairs
4. Build the transition matrix from these pairs

This engineering step is itself a demonstration of BA skill. Document it in the README and in a `scripts/seed_data.py` notebook section.

### Dataset for seed_data.py Strategy

The strongest approach for a portfolio is:
1. **Primary demo data**: Use Telco Churn for the churn domain (well-known, clean, no disputes)
2. **Brand share**: Use the e-commerce multi-category store dataset OR generate synthetic data with a documented DGP
3. **Both**: The `scripts/seed_data.py` should show how raw real-world data gets cleaned, discretized, and loaded — this pipeline is itself a portfolio artifact

### What Makes a Dataset "Work" for Markov Demonstration

For a recruiter, the convincing dataset is one where:
- There are at least 4-6 distinct states (too few = trivial; too many = sparse matrix)
- The transition matrix has interesting off-diagonal structure (some cross-state movement)
- The stationary distribution is not trivially obvious from the data
- At least 20-30 transitions per cell (per the min-observations rule already in the codebase)
- Enough time periods for m2 (time-varying) to show meaningfully different P_t matrices across periods (at least 6 periods)

---

## Feature Priority for 4-Week Timeline

Given the project constraint of 4 weeks and recruiter-first audience:

**Must-have by launch (table stakes for portfolio)**
1. Annotated transition heatmap with cell values (not just color) — 2 hours
2. Monte Carlo fan chart with labeled confidence bands — 4 hours
3. `st.spinner()` on all heavy operations — 1 hour
4. Empty states on all pages — 2 hours
5. Download button (CSV) on every data table — 1 hour
6. Model comparison metrics table (MAPE, Brier) — 3 hours
7. Stationary distribution panel — 2 hours

**High-value differentiators (if time allows)**
1. Sparsity flagging on heatmap cells — 3 hours
2. What-if scenario editor (deferred compute) — 6 hours
3. Sankey with period selector — 4 hours
4. Walk-forward backtest chart — 4 hours

**Skip entirely (not worth the time)**
1. Real-time streaming data
2. User authentication
3. Multi-model animated transitions
4. Custom CSS beyond what theme.css already provides

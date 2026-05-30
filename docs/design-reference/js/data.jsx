/* ============================================================================
   Mock data — realistic, demonstration-grade
   Brand share: Indonesian e-commerce. Churn: telco state model.
   ========================================================================== */

/* ---- Brand share: 6 e-commerce players ---- */
const BRANDS = [
  { name: 'Shopee',     color: 'var(--chart-1)' },
  { name: 'Tokopedia',  color: 'var(--chart-2)' },
  { name: 'Lazada',     color: 'var(--chart-3)' },
  { name: 'TikTok Shop',color: 'var(--chart-4)' },
  { name: 'Blibli',     color: 'var(--chart-5)' },
  { name: 'Bukalapak',  color: 'var(--chart-6)' },
];

/* Historical shares (12 periods) + forecast (12 periods), each row sums ~1 */
function buildShareSeries() {
  // start shares
  let cur = [0.34, 0.30, 0.13, 0.10, 0.08, 0.05];
  const drift = [0.004, -0.001, -0.004, 0.006, -0.002, -0.003]; // per-period tendency
  const hist = [];
  for (let t = 0; t < 12; t++) {
    const noise = drift.map((d, i) => d + (Math.sin(t * 1.3 + i) * 0.004));
    cur = cur.map((v, i) => Math.max(0.01, v + noise[i]));
    const s = cur.reduce((a, b) => a + b, 0);
    cur = cur.map(v => v / s);
    hist.push([...cur]);
  }
  const fc = [], lo = [], hi = [];
  let f = [...cur];
  for (let t = 0; t < 12; t++) {
    f = f.map((v, i) => Math.max(0.01, v + drift[i] * 1.1));
    const s = f.reduce((a, b) => a + b, 0); f = f.map(v => v / s);
    fc.push([...f]);
    const band = 0.012 + t * 0.0042;
    lo.push(f.map(v => Math.max(0, v - band)));
    hi.push(f.map(v => v + band));
  }
  return { hist, fc, lo, hi };
}
const SHARE = buildShareSeries();

/* ---- Transition matrix (6x6) with observation counts ---- */
function buildMatrix() {
  const stick = [0.78, 0.74, 0.66, 0.71, 0.63, 0.58];
  const M = [], OBS = [];
  for (let i = 0; i < 6; i++) {
    const row = new Array(6).fill(0);
    row[i] = stick[i];
    let rem = 1 - stick[i];
    const others = [...Array(6).keys()].filter(j => j !== i);
    let weights = others.map((j) => 0.4 + Math.abs(Math.sin(i * 2 + j)) );
    const ws = weights.reduce((a, b) => a + b, 0);
    others.forEach((j, k) => { row[j] = +(rem * weights[k] / ws).toFixed(4); });
    M.push(row);
    OBS.push(row.map((p, j) => Math.round(p * (i === j ? 9000 : (i > 3 ? 60 : 900)) * (0.5 + Math.random()))));
  }
  // force a couple sparse cells
  OBS[5][2] = 11; OBS[4][5] = 8; OBS[2][5] = 14;
  return { M, OBS };
}
const MATRIX = buildMatrix();

/* ---- Monte Carlo fan chart for a single brand (Shopee) ---- */
function buildFan() {
  const p10 = [], p50 = [], p90 = [];
  let m = 0.355;
  for (let t = 0; t <= 12; t++) {
    m = m + 0.0035 + Math.sin(t) * 0.0008;
    const spread = 0.006 + t * 0.0052;
    p50.push(m); p10.push(m - spread); p90.push(m + spread);
  }
  const paths = [];
  for (let k = 0; k < 5; k++) {
    let v = 0.355; const path = [];
    for (let t = 0; t <= 12; t++) { v += 0.0035 + (Math.sin(k * 3 + t) * 0.012); path.push(v); }
    paths.push(path);
  }
  return { p10, p50, p90, paths };
}
const FAN = buildFan();
const FINAL_DIST = [
  { label: '32-34%', v: 0.06 }, { label: '34-36%', v: 0.14 }, { label: '36-38%', v: 0.27 },
  { label: '38-40%', v: 0.29 }, { label: '40-42%', v: 0.16 }, { label: '42-44%', v: 0.06 }, { label: '44%+', v: 0.02 },
];
const CALIB = [
  { bucket: 'P(Shopee > 40%)',   raw: 0.71, cal: 0.67 },
  { bucket: 'P(Tokopedia gains)',raw: 0.44, cal: 0.46 },
  { bucket: 'P(TikTok > 12%)',   raw: 0.58, cal: 0.55 },
  { bucket: 'P(Blibli < 6%)',    raw: 0.29, cal: 0.33 },
  { bucket: 'P(Lazada flat)',    raw: 0.81, cal: 0.74 },
];

/* ---- Model comparison ---- */
const MODELS = [
  { id: 'm1', name: 'Homogeneous', desc: 'Constant transition matrix P. Y₍ₜ₊₁₎ = Yₜ·P', mape: 2.34, brier: 0.041, bestFor: 'Stable markets', recommended: false },
  { id: 'm2', name: 'Time-varying', desc: 'Per-step matrix Pₜ. Y₍ₜ₊₁₎ = Yₜ·Pₜ', mape: 1.87, brier: 0.033, bestFor: 'Dynamic markets', recommended: true },
  { id: 'm3', name: 'Extended', desc: 'Growth multiplier G. Q₍ₜ₊₁₎ = (G⊙Qₜ)·Pₜ', mape: 2.05, brier: 0.038, bestFor: 'Growing markets', recommended: false },
];
function miniForecast(seed) {
  const out = []; let v = 0.34;
  for (let i = 0; i < 14; i++) { v += 0.004 + Math.sin(seed + i * 0.6) * 0.006; out.push(v); }
  return out;
}
const BACKTEST = Array.from({ length: 12 }, (_, i) => {
  const actual = 0.34 + i * 0.004 + Math.sin(i) * 0.003;
  return {
    period: `P${i + 1}`,
    actual,
    m1: actual + (Math.sin(i * 1.4) * 0.012),
    m2: actual + (Math.sin(i * 1.4) * 0.005),
    m3: actual + (Math.sin(i * 1.4) * 0.009),
  };
});

/* ---- Recent forecasts (dashboard) ---- */
const RECENT = [
  { date: 'May 28', dataset: 'Consumer E-commerce 2024', model: 'm2', mape: 1.87, traj: [0.31,0.32,0.33,0.34,0.35,0.36,0.37], domain: 'brand' },
  { date: 'May 27', dataset: 'Telco Cohort 2024 Q1', model: 'm3', mape: 2.41, traj: [0.88,0.86,0.84,0.83,0.82,0.81,0.80], domain: 'churn' },
  { date: 'May 24', dataset: 'Consumer E-commerce 2024', model: 'm1', mape: 2.34, traj: [0.30,0.30,0.31,0.31,0.32,0.32,0.33], domain: 'brand' },
  { date: 'May 21', dataset: 'Telco Cohort 2023 Q1', model: 'm2', mape: 2.02, traj: [0.91,0.89,0.87,0.86,0.85,0.84,0.83], domain: 'churn' },
  { date: 'May 19', dataset: 'Consumer E-commerce 2024', model: 'm3', mape: 2.05, traj: [0.33,0.34,0.34,0.35,0.36,0.37,0.38], domain: 'brand' },
];

/* ---- Churn states + Sankey + cohort KPIs ---- */
const CHURN_STATES = [
  { key: 'active',      label: 'Active',      color: 'var(--state-active)' },
  { key: 'atrisk',      label: 'At-Risk',     color: 'var(--state-atrisk)' },
  { key: 'inactive',    label: 'Inactive',    color: 'var(--state-inactive)' },
  { key: 'reactivated', label: 'Reactivated', color: 'var(--state-reactivated)' },
  { key: 'churned',     label: 'Churned',     color: 'var(--state-churned)' },
];
/* state distribution over 12 periods (each sums to 1) */
function buildChurnDist() {
  const dist = [[1, 0, 0, 0, 0]];
  let cur = [1, 0, 0, 0, 0];
  // rows: active, atrisk, inactive, reactivated, churned
  const P = [
    [0.86, 0.09, 0.03, 0.00, 0.02], // from active
    [0.28, 0.45, 0.18, 0.00, 0.09], // from atrisk
    [0.05, 0.12, 0.55, 0.10, 0.18], // from inactive
    [0.60, 0.20, 0.10, 0.05, 0.05], // from reactivated
    [0.00, 0.00, 0.00, 0.02, 0.98], // from churned
  ];
  for (let t = 0; t < 12; t++) {
    const next = [0, 0, 0, 0, 0];
    for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) next[j] += cur[i] * P[i][j];
    cur = next; dist.push([...cur]);
  }
  return { dist, P };
}
const CHURN = buildChurnDist();
const COHORT_KPIS = {
  retention: 0.802, lifetime: 28.4, expectedChurn: 1840, revenueAtRisk: 1240000000,
};

/* ---- Datasets (settings) ---- */
const DATASETS = [
  { name: 'Consumer E-commerce 2024', domain: 'Brand Share', rows: 12480, states: 6, created: 'May 12, 2026' },
  { name: 'Telco Cohort 2024 Q1', domain: 'Customer Churn', rows: 48200, states: 5, created: 'May 09, 2026' },
];

Object.assign(window, {
  BRANDS, SHARE, MATRIX, FAN, FINAL_DIST, CALIB, MODELS, miniForecast, BACKTEST,
  RECENT, CHURN_STATES, CHURN, COHORT_KPIS, DATASETS,
});

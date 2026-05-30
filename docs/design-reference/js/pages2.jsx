/* ============================================================================
   Pages 4-8 — Home Dashboard · Brand Share (Landing, Matrix, Monte Carlo,
   Model Comparison). Rendered inside AppShell.
   ========================================================================== */

/* shared: brand-share sub-tab bar */
function BrandTabs({ page, setPage }) {
  const map = { Overview: 5, 'Transition Matrix': 6, 'Monte Carlo': 7, 'Model Comparison': 8 };
  const cur = Object.keys(map).find(k => map[k] === page);
  return <Tabs tabs={Object.keys(map)} value={cur} onChange={t => setPage(map[t])} />;
}
function PageHeader({ title, desc, actions }) {
  return (
    <div className="row wrap" style={{ justifyContent: 'space-between', gap: 'var(--space-4)', alignItems: 'flex-end' }}>
      <div className="col" style={{ gap: 4 }}><h1 className="t-h1">{title}</h1>{desc && <p className="t-sm t-sec">{desc}</p>}</div>
      {actions && <div className="row gap-2 wrap">{actions}</div>}
    </div>
  );
}

/* ====== PAGE 4 — Home / Dashboard ====== */
function PageDashboard({ setPage }) {
  return (
    <div className="col" style={{ gap: 'var(--space-6)' }}>
      <PageHeader title="Home" desc="Overview of your forecasting workbench." actions={<><Button variant="secondary" icon="upload">Import dataset</Button><Button variant="primary" icon="play" onClick={() => setPage(5)}>Run forecast</Button></>} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-4)' }}>
        <KPICard label="Active Models" value="3" tooltip="m1 Homogeneous, m2 Time-varying, m3 Extended (Chan 2015)" icon="box" accent="var(--chart-1)" />
        <KPICard label="Datasets Registered" value="2" icon="database" accent="var(--chart-2)" />
        <KPICard label="Last Forecast (MAPE)" value="1.87" unit="%" delta={-0.47} deltaSuffix="pp" accent="var(--chart-4)" />
        <KPICard label="Simulations Run (30d)" value="48" sparkline={[2,4,3,6,5,8,7,9,11,10,13,12]} accent="var(--chart-6)" />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.5fr) minmax(0, 1fr)', gap: 'var(--space-5)' }}>
        <ChartContainer title="Recent Forecasts" subtitle="Last 5 runs across both domains" actions={<Button variant="ghost" size="sm" iconRight="arrowRight">View all</Button>}>
          <div className="col">
            {RECENT.map((r, i) => (
              <div key={i} className="row gap-4" style={{ padding: '14px 0', borderBottom: i < RECENT.length - 1 ? '1px solid var(--color-border-subtle)' : 'none', alignItems: 'center' }}>
                <div style={{ width: 34, height: 34, borderRadius: 'var(--radius-sm)', display: 'grid', placeItems: 'center', background: r.domain === 'brand' ? 'var(--color-primary-subtle)' : 'var(--color-success-subtle)', color: r.domain === 'brand' ? 'var(--color-primary)' : 'var(--color-success)', flex: '0 0 auto' }}><Icon name={r.domain === 'brand' ? 'trendingUp' : 'users'} size={17} /></div>
                <div className="col" style={{ gap: 2, flex: 1, minWidth: 0 }}><span className="t-sm" style={{ fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.dataset}</span><span className="t-xs t-ter mono">{r.date} · model {r.model}</span></div>
                <Sparkline data={r.traj} color={r.domain === 'brand' ? 'var(--chart-1)' : 'var(--chart-2)'} width={80} />
                <Badge variant={r.mape < 2 ? 'success' : 'warning'}>{r.mape}% MAPE</Badge>
              </div>
            ))}
          </div>
        </ChartContainer>
        <div className="col gap-4">
          <span className="t-label">Quick actions</span>
          {[['play', 'Run new forecast', 'Project shares forward', 5, 'var(--chart-1)'],
            ['upload', 'Import dataset', 'CSV with entity, period, state', 12, 'var(--chart-2)'],
            ['gitBranch', 'Compare models', 'm1 vs m2 vs m3 by MAPE', 8, 'var(--chart-4)']].map(([ic, t, d, pg, c]) => (
            <button key={t} onClick={() => setPage(pg)} className="card card-pad row gap-4" style={{ cursor: 'pointer', textAlign: 'left', border: '1px solid var(--color-border-subtle)', transition: 'box-shadow var(--dur-micro) var(--ease), transform var(--dur-micro) var(--ease)' }}
              onMouseEnter={e => { e.currentTarget.style.boxShadow = 'var(--shadow-raised)'; e.currentTarget.style.transform = 'translateY(-1px)'; }} onMouseLeave={e => { e.currentTarget.style.boxShadow = ''; e.currentTarget.style.transform = ''; }}>
              <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-sm)', display: 'grid', placeItems: 'center', background: c, color: '#fff', flex: '0 0 auto' }}><Icon name={ic} size={20} /></div>
              <div className="col" style={{ gap: 2, flex: 1 }}><span className="t-sm" style={{ fontWeight: 600 }}>{t}</span><span className="t-xs t-ter">{d}</span></div>
              <Icon name="arrowRight" size={17} style={{ color: 'var(--color-text-tertiary)' }} />
            </button>
          ))}
        </div>
      </div>
      <Card accent="var(--color-primary)" className="card-pad">
        <div className="row gap-3" style={{ marginBottom: 16 }}><Icon name="sparkles" size={18} style={{ color: 'var(--color-primary)' }} /><h3 className="t-h3">How MarkovLens works</h3><a href="#" className="t-xs" style={{ color: 'var(--color-primary)', marginLeft: 'auto' }}>Read the docs →</a></div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-5)' }}>
          {[['Build matrix', 'Estimate transition probabilities from historical state changes.'],
            ['Run simulation', 'Forecast with m1/m2/m3 or 10,000 Monte Carlo paths.'],
            ['Calibrate', 'Apply Becker (2026) longshot calibration before reporting.']].map(([t, d], i) => (
            <div key={t} className="col gap-2"><div className="row gap-2"><span className="mono t-sm" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>0{i+1}</span><span className="t-sm" style={{ fontWeight: 600 }}>{t}</span></div><p className="t-xs t-sec" style={{ textWrap: 'pretty' }}>{d}</p></div>
          ))}
        </div>
      </Card>
    </div>
  );
}

/* ====== PAGE 5 — Brand Share Landing ====== */
function PageBrandLanding({ page, setPage, theme }) {
  const [model, setModel] = useState('m2');
  const [horizon, setHorizon] = useState(12);
  const fcLast = SHARE.fc[SHARE.fc.length - 1];
  const histLast = SHARE.hist[SHARE.hist.length - 1];
  const ranked = BRANDS.map((b, i) => ({ ...b, share: fcLast[i], delta: (fcLast[i] - histLast[i]) * 100 }));
  const leader = [...ranked].sort((a, b) => b.share - a.share)[0];
  const gainer = [...ranked].sort((a, b) => b.delta - a.delta)[0];
  const loser = [...ranked].sort((a, b) => a.delta - b.delta)[0];
  return (
    <div className="col" style={{ gap: 'var(--space-5)' }}>
      <PageHeader title="Brand Share Forecaster" desc="Predict e-commerce market share evolution from consumer switching data." />
      {/* control strip */}
      <Card className="card-pad">
        <div className="row wrap gap-5" style={{ alignItems: 'flex-end' }}>
          <div className="col gap-2" style={{ minWidth: 240 }}>
            <label className="field-label">Dataset</label>
            <Select value="ec" onChange={() => {}} options={[{ value: 'ec', label: 'Consumer E-commerce 2024' }, { value: 'tel', label: 'Telco Cohort 2024 Q1' }]} />
            <span className="t-xs t-ter mono">12,480 transitions · 12 periods · 6 states</span>
          </div>
          <div className="col gap-2"><label className="field-label">Model</label><Tooltip body={MODELS.find(m => m.id === model).desc}><Segmented options={['m1','m2','m3']} value={model} onChange={setModel} /></Tooltip></div>
          <div className="col gap-2" style={{ minWidth: 200, flex: 1, maxWidth: 280 }}><Slider label="Time horizon" value={horizon} min={1} max={24} onChange={setHorizon} format={x => `${x} months`} /></div>
          <Button variant="primary" icon="play">Run Forecast</Button>
        </div>
      </Card>
      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-4)' }}>
        <KPICard label="Forecasted leader" value={leader.name} accent={leader.color} icon="trendingUp" />
        <KPICard label="Biggest gainer" value={gainer.name} delta={gainer.delta} deltaSuffix="pp" accent="var(--chart-2)" />
        <KPICard label="Biggest loser" value={loser.name} delta={loser.delta} deltaSuffix="pp" accent="var(--chart-5)" />
      </div>
      <BrandTabs page={page} setPage={setPage} />
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 320px', gap: 'var(--space-5)' }}>
        <ChartContainer title="Market share forecast" subtitle={`Historical (solid) + ${horizon}-month forecast (dashed) with confidence band · model ${model}`}
          actions={<Button variant="ghost" size="sm" icon="download" />}>
          <StackedArea theme={theme} />
          <Legend items={BRANDS} style={{ marginTop: 16, justifyContent: 'center' }} />
        </ChartContainer>
        <Card accent="var(--color-primary)" className="card-pad col gap-4" style={{ alignSelf: 'start' }}>
          <div className="row gap-2"><Icon name="sparkles" size={17} style={{ color: 'var(--color-primary)' }} /><h3 className="t-h3">Model insights</h3></div>
          {[['P(Shopee > 40% by Q4)', '67%', 'success'],
            ['Most likely scenario', 'Shopee flat, TikTok +3pp', null],
            ['Lazada trajectory', 'Gradual decline -2.1pp', 'warning'],
            ['Market concentration', 'HHI rising · top-2 = 62%', null]].map(([l, v, badge], i) => (
            <div key={i} className="col gap-1" style={{ paddingBottom: 12, borderBottom: i < 3 ? '1px solid var(--color-border-subtle)' : 'none' }}>
              <span className="t-xs t-ter">{l}</span>
              {badge ? <Badge variant={badge}>{v}</Badge> : <span className="t-sm" style={{ fontWeight: 600 }}>{v}</span>}
            </div>
          ))}
          <div style={{ background: 'var(--color-primary-subtle)', borderRadius: 'var(--radius-sm)', padding: 12 }}><p className="t-xs" style={{ color: 'var(--color-primary)', textWrap: 'pretty' }}>Calibrated with Becker (2026) longshot adjustment — tail probabilities pulled toward base rates.</p></div>
        </Card>
      </div>
    </div>
  );
}

/* ====== PAGE 6 — Transition Matrix Explorer ====== */
function PageMatrix({ page, setPage, theme }) {
  const [selected, setSelected] = useState([0, 1]);
  const [smoothing, setSmoothing] = useState('Off');
  const [filter, setFilter] = useState('all');
  const labels = BRANDS.map(b => b.name);
  const [i, j] = selected; const prob = MATRIX.M[i][j]; const obs = MATRIX.OBS[i][j];
  return (
    <div className="col" style={{ gap: 'var(--space-5)' }}>
      <PageHeader title="Transition Matrix Explorer" desc="Brand-to-brand switching probabilities. Diagonal = stickiness." />
      <BrandTabs page={page} setPage={setPage} />
      <div className="row wrap gap-4" style={{ justifyContent: 'space-between' }}>
        <div className="row gap-3" style={{ alignItems: 'center' }}><span className="t-label">Smoothing</span><Segmented options={['Off', 'Laplace', 'Bayesian']} value={smoothing} onChange={setSmoothing} /></div>
        <div className="row gap-2">{[['all', 'Show all'], ['diag', 'Diagonal only'], ['sparse', 'Hide sparse']].map(([v, l]) => (
          <button key={v} onClick={() => setFilter(v)} className="badge" style={{ cursor: 'pointer', border: '1px solid', borderColor: filter === v ? 'var(--color-primary)' : 'var(--color-border-visible)', background: filter === v ? 'var(--color-primary-subtle)' : 'var(--color-surface)', color: filter === v ? 'var(--color-primary)' : 'var(--color-text-secondary)', padding: '5px 12px' }}>{l}</button>
        ))}</div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 320px', gap: 'var(--space-5)' }}>
        <ChartContainer title="Transition probabilities" subtitle="Rows = from-state · Columns = to-state · click a cell for detail">
          <Heatmap theme={theme} onCell={setSelected} selected={selected} hideSparse={filter === 'sparse'} diagOnly={filter === 'diag'} />
          <div className="row gap-4 wrap" style={{ marginTop: 16, justifyContent: 'space-between' }}>
            <div className="row gap-2"><span className="t-xs t-ter">Low</span><div className="row" style={{ width: 120, height: 12, borderRadius: 999, overflow: 'hidden' }}>{[1,2,3,4,5].map(k => <div key={k} style={{ flex: 1, background: `var(--chart-seq-${k})` }} />)}</div><span className="t-xs t-ter">High</span></div>
            <span className="row gap-2 t-xs t-ter"><Icon name="alertTriangle" size={13} style={{ color: 'var(--color-warning)' }} /> Fewer than 20 observations</span>
          </div>
        </ChartContainer>
        <Card accent="var(--color-primary)" className="card-pad col gap-4" style={{ alignSelf: 'start' }}>
          <span className="t-label">Cell detail</span>
          <div className="row gap-2" style={{ alignItems: 'center' }}>
            <span className="badge badge-primary">{labels[i]}</span><Icon name="arrowRight" size={16} style={{ color: 'var(--color-text-tertiary)' }} /><span className="badge badge-primary">{labels[j]}</span>
          </div>
          <div className="col gap-1"><span className="mono" style={{ fontSize: 'var(--fs-48)', fontWeight: 700, lineHeight: 1, color: 'var(--color-primary)' }}>{(prob * 100).toFixed(1)}%</span><span className="t-xs t-sec">transition probability</span></div>
          <div className="col gap-3" style={{ borderTop: '1px solid var(--color-border-subtle)', paddingTop: 16 }}>
            <div className="row" style={{ justifyContent: 'space-between' }}><span className="t-sm t-sec">Observations</span><span className="mono t-sm" style={{ fontWeight: 600 }}>{fmt.fmtNum(obs)}</span></div>
            <div className="row" style={{ justifyContent: 'space-between' }}><span className="t-sm t-sec">Over periods</span><span className="mono t-sm" style={{ fontWeight: 600 }}>12</span></div>
            <div className="row" style={{ justifyContent: 'space-between' }}><span className="t-sm t-sec">Confidence interval</span><span className="mono t-sm" style={{ fontWeight: 600 }}>±{(obs < 20 ? 6.4 : 2.1).toFixed(1)}pp</span></div>
          </div>
          {obs < 20 && <div className="row gap-2" style={{ background: 'var(--color-warning-subtle)', borderRadius: 'var(--radius-sm)', padding: 12 }}><Icon name="alertTriangle" size={16} style={{ color: 'var(--color-warning)', flex: '0 0 auto' }} /><span className="t-xs" style={{ color: 'var(--color-warning)' }}>Sparse cell — estimate is noisy. Consider merging states or gathering more data.</span></div>}
          {i === j && <div className="row gap-2" style={{ background: 'var(--color-primary-subtle)', borderRadius: 'var(--radius-sm)', padding: 12 }}><Icon name="info" size={16} style={{ color: 'var(--color-primary)', flex: '0 0 auto' }} /><span className="t-xs" style={{ color: 'var(--color-primary)' }}>Self-transition — measures brand stickiness / retention.</span></div>}
        </Card>
      </div>
    </div>
  );
}

/* ====== PAGE 7 — Monte Carlo Simulator ====== */
function PageMonteCarlo({ page, setPage, theme }) {
  const [horizon, setHorizon] = useState(12);
  const [nsims, setNsims] = useState(10000);
  const [seed, setSeed] = useState(42);
  return (
    <div className="col" style={{ gap: 'var(--space-5)' }}>
      <PageHeader title="Monte Carlo Simulator" desc="Distribution of possible futures for Shopee market share." />
      <BrandTabs page={page} setPage={setPage} />
      <Card className="card-pad">
        <div className="row wrap gap-5" style={{ alignItems: 'flex-end' }}>
          <div className="col gap-2" style={{ minWidth: 180 }}><label className="field-label">Start state</label><Select value="shopee" onChange={() => {}} options={BRANDS.map(b => ({ value: b.name.toLowerCase(), label: b.name }))} /></div>
          <div className="col gap-2" style={{ minWidth: 180, flex: 1, maxWidth: 240 }}><Slider label="Time horizon" value={horizon} min={1} max={24} onChange={setHorizon} format={x => `${x} mo`} /></div>
          <div className="col gap-2" style={{ minWidth: 200, flex: 1, maxWidth: 260 }}><Slider label="Simulations" value={nsims} min={1000} max={50000} step={1000} onChange={setNsims} format={x => `${(x/1000)}k`} note="more = smoother, slower" /></div>
          <div className="col gap-2" style={{ width: 130 }}><label className="field-label">Seed</label><div className="row gap-2"><Input value={seed} onChange={e => setSeed(e.target.value)} style={{ width: 70 }} /><Button variant="secondary" icon="refresh" onClick={() => setSeed(Math.floor(Math.random() * 999))} /></div></div>
          <Button variant="primary" icon="play">Run Simulation</Button>
        </div>
      </Card>
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 320px', gap: 'var(--space-5)' }}>
        <ChartContainer title="Forecast fan chart" subtitle={`${fmt.fmtNum(nsims)} simulated paths · P10 / P50 / P90 bands · seed ${seed}`} actions={<Button variant="ghost" size="sm" icon="download" />}>
          <FanChart />
        </ChartContainer>
        <ChartContainer title="Final state distribution" subtitle={`Where Shopee lands at +${horizon}mo`}>
          <Histogram data={FINAL_DIST} />
        </ChartContainer>
      </div>
      <ChartContainer title="Raw vs calibrated probabilities" subtitle="Becker (2026) longshot adjustment pulls tail estimates toward base rates"
        actions={<Tooltip body="Longshot bias: extreme probabilities are systematically overestimated. Calibration corrects this."><Icon name="helpCircle" size={17} style={{ color: 'var(--color-text-tertiary)' }} /></Tooltip>}>
        <table className="tbl">
          <thead><tr><th>Outcome</th><th className="num">Raw probability</th><th className="num">Calibrated</th><th className="num">Δ</th></tr></thead>
          <tbody>{CALIB.map((r, i) => { const d = (r.cal - r.raw) * 100; return (
            <tr key={i}><td>{r.bucket}</td><td className="num">{(r.raw*100).toFixed(1)}%</td><td className="num" style={{ fontWeight: 600 }}>{(r.cal*100).toFixed(1)}%</td><td className="num" style={{ color: d >= 0 ? 'var(--color-success)' : 'var(--color-danger)' }}>{d >= 0 ? '+' : ''}{d.toFixed(1)}pp</td></tr>
          ); })}</tbody>
        </table>
      </ChartContainer>
    </div>
  );
}

/* ====== PAGE 8 — Model Comparison ====== */
function PageModelCompare({ page, setPage }) {
  const minErr = (r) => Math.min(Math.abs(r.m1 - r.actual), Math.abs(r.m2 - r.actual), Math.abs(r.m3 - r.actual));
  const errColor = (e) => { const t = Math.min(1, e / 0.015); return `color-mix(in srgb, var(--color-danger-subtle) ${t*100}%, transparent)`; };
  return (
    <div className="col" style={{ gap: 'var(--space-5)' }}>
      <PageHeader title="Model Comparison" desc="Same dataset, three Markov formulations. Pick by MAPE / Brier." />
      <BrandTabs page={page} setPage={setPage} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 'var(--space-5)' }}>
        {MODELS.map((m, i) => (
          <Card key={m.id} className="card-pad col gap-4" style={m.recommended ? { boxShadow: '0 0 0 2px var(--color-primary)', position: 'relative' } : {}}>
            {m.recommended && <div style={{ position: 'absolute', top: -10, right: 16 }}><Badge variant="success" icon="check">Best fit</Badge></div>}
            <div className="row" style={{ justifyContent: 'space-between' }}><div className="col gap-1"><span className="mono t-h3" style={{ color: m.recommended ? 'var(--color-primary)' : 'var(--color-text-tertiary)' }}>{m.id}</span><span className="t-sm" style={{ fontWeight: 600 }}>{m.name}</span></div><Badge variant="neutral">{m.bestFor}</Badge></div>
            <p className="t-xs t-sec mono" style={{ textWrap: 'pretty' }}>{m.desc}</p>
            <div style={{ height: 80, background: 'var(--color-surface-sunken)', borderRadius: 'var(--radius-sm)', padding: 8 }}><MiniForecast data={miniForecast(i + 1)} color={m.recommended ? 'var(--chart-1)' : 'var(--color-text-tertiary)'} height={64} /></div>
            <div className="row gap-5" style={{ borderTop: '1px solid var(--color-border-subtle)', paddingTop: 16 }}>
              <div className="col"><span className="mono" style={{ fontSize: 28, fontWeight: 700, color: m.recommended ? 'var(--color-success)' : 'var(--color-text-primary)' }}>{m.mape}%</span><span className="t-xs t-ter">MAPE ↓</span></div>
              <div className="col"><span className="mono" style={{ fontSize: 18, fontWeight: 600 }}>{m.brier}</span><span className="t-xs t-ter">Brier ↓</span></div>
            </div>
          </Card>
        ))}
      </div>
      <ChartContainer title="Walk-forward backtest" subtitle="12-period validation · cell shading = error magnitude" actions={<Button variant="ghost" size="sm" icon="download" />}>
        <table className="tbl">
          <thead><tr><th>Period</th><th className="num">Actual</th><th className="num">m1</th><th className="num">m2</th><th className="num">m3</th></tr></thead>
          <tbody>{BACKTEST.map((r, i) => (
            <tr key={i}>
              <td className="mono">{r.period}</td>
              <td className="num" style={{ fontWeight: 600 }}>{(r.actual*100).toFixed(1)}%</td>
              {['m1','m2','m3'].map(mk => { const e = Math.abs(r[mk] - r.actual); return <td key={mk} className="num" style={{ background: errColor(e), borderRadius: 4 }}>{(r[mk]*100).toFixed(1)}%</td>; })}
            </tr>
          ))}</tbody>
        </table>
      </ChartContainer>
    </div>
  );
}

Object.assign(window, { PageDashboard, PageBrandLanding, PageMatrix, PageMonteCarlo, PageModelCompare, BrandTabs, PageHeader });

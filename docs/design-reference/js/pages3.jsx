/* ============================================================================
   Pages 9-12 — Customer Churn (Landing, What-If) · Reports · Settings
   ========================================================================== */

function ChurnTabs({ page, setPage }) {
  const map = { Overview: 9, 'What-If Simulator': 10 };
  const cur = Object.keys(map).find(k => map[k] === page) || 'Overview';
  return <Tabs tabs={['Overview', 'State Journey', 'What-If Simulator']} value={cur} onChange={t => { if (map[t]) setPage(map[t]); }} />;
}

/* ====== PAGE 9 — Customer Churn Landing ====== */
function PageChurnLanding({ page, setPage }) {
  const [period, setPeriod] = useState(12);
  const k = COHORT_KPIS;
  return (
    <div className="col" style={{ gap: 'var(--space-5)' }}>
      <PageHeader title="Customer Churn States" desc="Model customers as Active → At-Risk → Churned and forecast retention." />
      <Card className="card-pad">
        <div className="row wrap gap-5" style={{ alignItems: 'flex-end' }}>
          <div className="col gap-2" style={{ minWidth: 220 }}><label className="field-label">Cohort</label><Select value="2024q1" onChange={() => {}} options={[{ value: '2024q1', label: '2024 Q1 cohort · 24,000 customers' }, { value: '2023q1', label: '2023 Q1 cohort · 19,400 customers' }]} /></div>
          <Button variant="primary" icon="play">Run Analysis</Button>
        </div>
      </Card>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 'var(--space-4)' }}>
        <KPICard label="Retention Rate" value={(k.retention*100).toFixed(1)} unit="%" delta={-1.8} deltaSuffix="pp" accent="var(--state-active)" icon="users" />
        <KPICard label="Avg Customer Lifetime" value={k.lifetime} unit="mo" delta={2.3} accent="var(--chart-4)" icon="clock" />
        <KPICard label="Expected Churn (30d)" value={fmt.fmtNum(k.expectedChurn)} delta={5.2} accent="var(--state-churned)" icon="trendingUp" />
        <KPICard label="Revenue at Risk" value={fmt.fmtRp(k.revenueAtRisk)} accent="var(--state-atrisk)" icon="dollar" tooltip="Projected lost revenue from churn over the next 30 days." />
      </div>
      <ChurnTabs page={page} setPage={setPage} />
      <ChartContainer title="Customer state flow" subtitle="Each ribbon = customers moving between states · hover for counts" accent="var(--state-active)" actions={<Button variant="ghost" size="sm" icon="download" />}>
        <Legend items={CHURN_STATES} style={{ marginBottom: 16 }} />
        <Sankey periods={8} highlight={period < 8 ? null : null} />
        {/* time scrubber */}
        <div className="col gap-3" style={{ marginTop: 20, borderTop: '1px solid var(--color-border-subtle)', paddingTop: 16 }}>
          <div className="row" style={{ justifyContent: 'space-between' }}><span className="t-label">Distribution at period {period}</span><span className="t-xs t-ter mono">drag to scrub</span></div>
          <Slider value={period} min={0} max={12} onChange={setPeriod} format={x => `P${x}`} />
          <div className="row" style={{ height: 30, borderRadius: 'var(--radius-sm)', overflow: 'hidden', border: '1px solid var(--color-border-subtle)' }}>
            {CHURN.dist[period].map((v, i) => v > 0.001 && (
              <Tooltip key={i} body={`${CHURN_STATES[i].label}: ${(v*100).toFixed(1)}%`}>
                <div style={{ width: `${v*100}%`, height: 28, background: CHURN_STATES[i].color, display: 'grid', placeItems: 'center' }}>{v > 0.08 && <span className="mono" style={{ fontSize: 11, color: '#fff', fontWeight: 600 }}>{(v*100).toFixed(0)}%</span>}</div>
              </Tooltip>
            ))}
          </div>
        </div>
      </ChartContainer>
    </div>
  );
}

/* ====== PAGE 10 — What-If Simulator ====== */
const WHATIF_GROUPS = [
  { from: 'From Active', rows: [['→ At-Risk', 9], ['→ Inactive', 3], ['→ Churned', 2]] },
  { from: 'From At-Risk', rows: [['→ Active', 28], ['→ Inactive', 18], ['→ Churned', 9]] },
  { from: 'From Inactive', rows: [['→ Reactivated', 10], ['→ Churned', 18]] },
];
function PageWhatIf({ page, setPage }) {
  const baseline = { '0': 9, '1': 3, '2': 2, '3': 28, '4': 18, '5': 9, '6': 10, '7': 18 };
  const [vals, setVals] = useState({ ...baseline });
  const [open, setOpen] = useState({ 'From Active': true, 'From At-Risk': true, 'From Inactive': false });
  const [drawer, setDrawer] = useState(false);
  const [modal, setModal] = useState(false);
  let idx = 0;
  // impact: reduction in Active->At-Risk vs baseline drives saved customers
  const a2r = vals['0'], base = baseline['0'];
  const saved = Math.round((base - a2r) * 0.01 * 24000 * 1.05);
  const revenue = saved * 510000;
  const dirty = JSON.stringify(vals) !== JSON.stringify(baseline);
  return (
    <div className="col" style={{ gap: 'var(--space-5)', position: 'relative' }}>
      <PageHeader title="What-If Simulator" desc="Adjust transition probabilities, see retention impact in real time." actions={<Button variant="secondary" icon="bookmark" onClick={() => setDrawer(true)}>Saved scenarios</Button>} />
      <ChurnTabs page={page} setPage={setPage} />
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 2fr) minmax(0, 3fr)', gap: 'var(--space-5)', alignItems: 'start' }}>
        {/* left: sliders */}
        <Card className="card-pad col gap-4">
          <div className="row" style={{ justifyContent: 'space-between' }}><span className="t-label">Transition probabilities</span><Button variant="ghost" size="sm" icon="refresh" onClick={() => setVals({ ...baseline })} disabled={!dirty}>Reset all</Button></div>
          {WHATIF_GROUPS.map(g => {
            const isOpen = open[g.from];
            return (
              <div key={g.from} className="col" style={{ border: '1px solid var(--color-border-subtle)', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
                <button onClick={() => setOpen(o => ({ ...o, [g.from]: !o[g.from] }))} className="row" style={{ justifyContent: 'space-between', padding: '10px 14px', border: 'none', background: 'var(--color-surface-sunken)', cursor: 'pointer', color: 'var(--color-text-primary)' }}>
                  <span className="t-sm" style={{ fontWeight: 600 }}>{g.from}</span><Icon name="chevronDown" size={16} style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform var(--dur-micro) var(--ease)' }} />
                </button>
                {isOpen && <div className="col gap-4" style={{ padding: 14 }}>
                  {g.rows.map(([lbl]) => { const key = String(idx++); return (
                    <Slider key={key} label={lbl} value={vals[key]} baseline={baseline[key]} min={0} max={60} onChange={v => setVals(s => ({ ...s, [key]: v }))} format={x => `${x}%`} accent={key === '0' ? 'var(--state-atrisk)' : undefined} />
                  ); })}
                </div>}
              </div>
            );
          })}
          <span className="t-xs t-ter row gap-2"><span style={{ width: 2, height: 10, background: 'var(--color-text-tertiary)', display: 'inline-block' }} /> ghost marker = baseline value</span>
        </Card>
        {/* right: live forecast */}
        <div className="col gap-5">
          <Card accent={dirty ? 'var(--color-success)' : 'var(--color-text-tertiary)'} className="card-pad col gap-3">
            <span className="t-label">Projected impact · 12 months</span>
            {dirty ? (
              <p className="t-h2" style={{ fontWeight: 600, textWrap: 'pretty', lineHeight: 1.3 }}>
                {a2r < base ? 'Reducing' : 'Increasing'} Active → At-Risk by <span style={{ color: 'var(--color-primary)' }} className="mono">{Math.abs(base - a2r)}pp</span> {saved >= 0 ? 'saves' : 'costs'} <span className="mono" style={{ color: 'var(--color-success)' }}>{fmt.fmtNum(Math.abs(saved))} customers</span> and <span className="mono" style={{ color: 'var(--color-success)' }}>{fmt.fmtRp(Math.abs(revenue))}</span>.
              </p>
            ) : <p className="t-h3 t-sec" style={{ fontWeight: 400 }}>Adjust a slider to model a retention scenario.</p>}
            <Button variant="primary" icon="save" style={{ alignSelf: 'flex-start' }} disabled={!dirty} onClick={() => setModal(true)}>Save scenario</Button>
          </Card>
          <ChartContainer title="Retention forecast" subtitle="Baseline (translucent) vs modified scenario (solid)">
            <WhatIfChart shift={(base - a2r) / 100} />
            <Legend items={CHURN_STATES} style={{ marginTop: 16 }} />
          </ChartContainer>
        </div>
      </div>
      {/* saved scenarios drawer */}
      {drawer && (
        <>
          <div onClick={() => setDrawer(false)} style={{ position: 'fixed', inset: 0, background: 'var(--color-overlay)', zIndex: 150 }} />
          <div className="card" style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: 'min(360px, 90vw)', zIndex: 160, borderRadius: 0, boxShadow: 'var(--shadow-floating)', display: 'flex', flexDirection: 'column' }}>
            <div className="row" style={{ justifyContent: 'space-between', padding: 16, borderBottom: '1px solid var(--color-border-subtle)' }}><h3 className="t-h3">Saved scenarios</h3><Button variant="ghost" size="sm" icon="x" onClick={() => setDrawer(false)} /></div>
            <div className="col gap-3 scroll-area" style={{ padding: 16, overflow: 'auto' }}>
              {[['Aggressive retention', '+412 customers', [0.86,0.87,0.88,0.89,0.9,0.91]], ['CFO baseline', '+0 customers', [0.86,0.85,0.84,0.83,0.82,0.81]], ['Win-back push', '+247 customers', [0.86,0.865,0.87,0.875,0.88,0.885]]].map(([t, d, traj], i) => (
                <button key={i} className="card card-pad row gap-3" style={{ cursor: 'pointer', border: '1px solid var(--color-border-subtle)', textAlign: 'left' }} onMouseEnter={e => e.currentTarget.style.background = 'var(--color-surface-sunken)'} onMouseLeave={e => e.currentTarget.style.background = ''}>
                  <Sparkline data={traj} color="var(--state-active)" width={64} />
                  <div className="col" style={{ gap: 2, flex: 1 }}><span className="t-sm" style={{ fontWeight: 600 }}>{t}</span><span className="t-xs" style={{ color: 'var(--color-success)' }}>{d}</span></div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
      {/* save modal */}
      {modal && (
        <div onClick={() => setModal(false)} style={{ position: 'fixed', inset: 0, background: 'var(--color-overlay)', zIndex: 170, display: 'grid', placeItems: 'center', padding: 24 }}>
          <div onClick={e => e.stopPropagation()} className="card card-raised" style={{ width: 'min(420px, 100%)', boxShadow: 'var(--shadow-floating)', borderRadius: 'var(--radius-lg)' }}>
            <div className="row" style={{ justifyContent: 'space-between', padding: '18px 20px', borderBottom: '1px solid var(--color-border-subtle)' }}><h3 className="t-h3">Save scenario</h3><Button variant="ghost" size="sm" icon="x" onClick={() => setModal(false)} /></div>
            <div className="col gap-3" style={{ padding: 20 }}>
              <div><label className="field-label">Scenario name</label><Input placeholder="e.g. Aggressive retention" autoFocus /></div>
              <div className="row gap-2" style={{ justifyContent: 'flex-end' }}><Button variant="ghost" onClick={() => setModal(false)}>Cancel</Button><Button variant="primary" icon="save" onClick={() => setModal(false)}>Save</Button></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
/* small stacked-area for what-if (active/atrisk/inactive/churned over 12mo) */
function WhatIfChart({ shift }) {
  const W = 600, H = 280, PL = 36, PR = 12, PT = 12, PB = 24; const iw = W-PL-PR, ih = H-PT-PB;
  const N = 13;
  const seriesBase = CHURN.dist.map(d => [d[0], d[1]+d[3], d[2], d[4]]); // active, atrisk(+react), inactive, churned
  // modified: shift improves active retention
  const seriesMod = CHURN.dist.map((d, t) => { const boost = shift * (t/12) * 0.5; return [Math.min(1, d[0]+boost), d[1]+d[3], d[2], Math.max(0, d[4]-boost)]; });
  const x = i => PL + (i/(N-1))*iw; const y = v => PT + (1-v)*ih;
  const colors = ['var(--state-active)','var(--state-atrisk)','var(--state-inactive)','var(--state-churned)'];
  const stackPath = (series, bi) => { const cum = series.map(r => { let c=0; return r.map(v => c+=v); }); const top=[],bot=[]; for(let i=0;i<N;i++){ top.push([x(i),y(cum[i][bi])]); bot.push([x(i),y(bi===0?0:cum[i][bi-1])]); } return `M${top.map(p=>p.join(' ')).join(' L')} L${bot.reverse().map(p=>p.join(' ')).join(' L')} Z`; };
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
      {[0,0.5,1].map(g => <line key={g} x1={PL} x2={W-PR} y1={y(g)} y2={y(g)} stroke="var(--color-border-subtle)" />)}
      {[0,1,2,3].map(bi => <path key={'b'+bi} d={stackPath(seriesBase, bi)} fill={colors[bi]} opacity="0.18" />)}
      {[0,1,2,3].map(bi => <path key={'m'+bi} d={stackPath(seriesMod, bi)} fill={colors[bi]} opacity="0.8" />)}
      {[0,0.5,1].map(g => <text key={'t'+g} x={PL-6} y={y(g)+4} textAnchor="end" fontSize="10" fill="var(--color-text-tertiary)" className="mono">{Math.round(g*100)}%</text>)}
      {[0,4,8,12].map(i => <text key={'x'+i} x={x(i)} y={H-6} textAnchor="middle" fontSize="10" fill="var(--color-text-tertiary)" className="mono">P{i}</text>)}
    </svg>
  );
}

/* ====== PAGE 11 — Reports ====== */
const REPORT_BLOCKS = [['barChart', 'KPI card'], ['activity', 'Chart'], ['table', 'Table'], ['text', 'Text'], ['minus', 'Page break']];
function PageReports() {
  const [tpl, setTpl] = useState('exec');
  const [blocks, setBlocks] = useState([{ id: 1, type: 'Text', label: 'Title & summary' }, { id: 2, type: 'KPI card', label: 'Retention KPIs' }, { id: 3, type: 'Chart', label: 'Share forecast' }]);
  const [sel, setSel] = useState(1);
  const [format, setFormat] = useState('PDF');
  const addBlock = (t) => setBlocks(b => [...b, { id: Date.now(), type: t, label: t }]);
  const selBlock = blocks.find(b => b.id === sel);
  return (
    <div className="col" style={{ gap: 'var(--space-5)' }}>
      <PageHeader title="Reports" desc="Generate exportable artifacts from your forecasts." />
      <div className="col gap-3">
        <span className="t-label">Templates</span>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-4)' }}>
          {[['exec', 'Executive Summary', '1-page · key metrics', 'fileText'], ['tech', 'Technical Deep-Dive', 'Multi-page · methodology', 'box'], ['comp', 'Comparison Report', 'm1 vs m2 vs m3', 'gitBranch']].map(([id, t, d, ic]) => (
            <button key={id} onClick={() => setTpl(id)} className="card card-pad col gap-3" style={{ cursor: 'pointer', textAlign: 'left', boxShadow: tpl === id ? '0 0 0 2px var(--color-primary)' : 'var(--shadow-resting)', border: '1px solid var(--color-border-subtle)' }}>
              <div className="row" style={{ justifyContent: 'space-between' }}><div style={{ width: 36, height: 36, borderRadius: 'var(--radius-sm)', background: 'var(--color-primary-subtle)', display: 'grid', placeItems: 'center', color: 'var(--color-primary)' }}><Icon name={ic} size={18} /></div>{tpl === id && <Icon name="check" size={18} style={{ color: 'var(--color-primary)' }} />}</div>
              <div className="col gap-1"><span className="t-sm" style={{ fontWeight: 600 }}>{t}</span><span className="t-xs t-ter">{d}</span></div>
              <div className="row gap-1" style={{ height: 40, padding: 6, background: 'var(--color-surface-sunken)', borderRadius: 6 }}>{[0,1,2].map(k => <div key={k} style={{ flex: 1, background: 'var(--color-border-subtle)', borderRadius: 2 }} />)}</div>
            </button>
          ))}
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '180px minmax(0,1fr) 240px', gap: 'var(--space-4)', alignItems: 'start' }}>
        {/* palette */}
        <Card className="card-pad col gap-2"><span className="t-label" style={{ marginBottom: 4 }}>Blocks</span>
          {REPORT_BLOCKS.map(([ic, t]) => (
            <button key={t} onClick={() => addBlock(t)} className="row gap-3" style={{ border: '1px dashed var(--color-border-visible)', background: 'var(--color-surface)', borderRadius: 'var(--radius-sm)', padding: '9px 12px', cursor: 'grab', color: 'var(--color-text-secondary)', fontSize: 13 }} onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--color-primary)'} onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--color-border-visible)'}>
              <Icon name={ic} size={16} />{t}<Icon name="plus" size={14} style={{ marginLeft: 'auto', color: 'var(--color-text-tertiary)' }} />
            </button>
          ))}
          <span className="t-xs t-ter" style={{ marginTop: 6, textWrap: 'pretty' }}>Click to add to canvas. Drag to reorder in production.</span>
        </Card>
        {/* A4 canvas */}
        <div style={{ display: 'grid', placeItems: 'center', background: 'var(--color-surface-sunken)', borderRadius: 'var(--radius-md)', padding: 'var(--space-5)', border: '1px solid var(--color-border-subtle)' }}>
          <div style={{ width: 'min(440px, 100%)', aspectRatio: '1 / 1.414', background: '#fff', boxShadow: 'var(--shadow-raised)', borderRadius: 4, padding: 28, overflow: 'auto' }}>
            <div style={{ borderBottom: '2px solid #4338CA', paddingBottom: 10, marginBottom: 14 }}><div style={{ fontSize: 16, fontWeight: 700, color: '#0A0A0A' }}>MarkovLens — {tpl === 'exec' ? 'Executive Summary' : tpl === 'tech' ? 'Technical Deep-Dive' : 'Comparison Report'}</div><div style={{ fontSize: 10, color: '#52525B', fontFamily: 'var(--font-mono)' }}>Consumer E-commerce 2024 · May 28, 2026</div></div>
            <div className="col gap-3">
              {blocks.map(b => (
                <div key={b.id} onClick={() => setSel(b.id)} style={{ border: sel === b.id ? '1.5px solid #4338CA' : '1px solid #E4E4E7', borderRadius: 6, padding: 12, cursor: 'pointer', background: sel === b.id ? '#EEF2FF' : '#fff' }}>
                  <div style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: '#A1A1AA', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>{b.type}</div>
                  {b.type === 'KPI card' ? <div style={{ display: 'flex', gap: 8 }}>{[0,1,2].map(k => <div key={k} style={{ flex: 1 }}><div style={{ fontSize: 8, color: '#52525B' }}>Metric</div><div style={{ fontSize: 15, fontWeight: 700, color: '#0A0A0A', fontFamily: 'var(--font-mono)' }}>{['80.2%','28mo','Rp 1.2B'][k]}</div></div>)}</div>
                  : b.type === 'Chart' ? <div style={{ height: 60 }}><MiniForecast data={miniForecast(2)} color="#4338CA" height={60} /></div>
                  : b.type === 'Table' ? <div className="col gap-1">{[0,1,2].map(k => <div key={k} style={{ height: 8, background: '#F4F4F5', borderRadius: 2 }} />)}</div>
                  : b.type === 'Page break' ? <div style={{ borderTop: '1px dashed #A1A1AA', textAlign: 'center', fontSize: 8, color: '#A1A1AA' }}>— page break —</div>
                  : <div className="col gap-1"><div style={{ height: 7, background: '#F4F4F5', borderRadius: 2, width: '90%' }} /><div style={{ height: 7, background: '#F4F4F5', borderRadius: 2, width: '70%' }} /></div>}
                </div>
              ))}
            </div>
          </div>
        </div>
        {/* properties */}
        <Card className="card-pad col gap-4"><span className="t-label">Properties</span>
          {selBlock ? <>
            <div><label className="field-label">Block type</label><Select value={selBlock.type} onChange={t => setBlocks(b => b.map(x => x.id === sel ? { ...x, type: t } : x))} options={REPORT_BLOCKS.map(r => r[1])} /></div>
            <div><label className="field-label">Label</label><Input value={selBlock.label} onChange={e => setBlocks(b => b.map(x => x.id === sel ? { ...x, label: e.target.value } : x))} /></div>
            <div className="row" style={{ justifyContent: 'space-between' }}><span className="t-sm">Show border</span><Toggle on={true} onChange={() => {}} /></div>
            <Button variant="danger" size="sm" icon="trash" onClick={() => { setBlocks(b => b.filter(x => x.id !== sel)); }}>Remove block</Button>
          </> : <span className="t-sm t-ter">Select a block to edit.</span>}
        </Card>
      </div>
      <Card className="card-pad row wrap gap-4" style={{ justifyContent: 'flex-end', alignItems: 'center' }}>
        <span className="t-xs t-ter grow">{blocks.length} blocks · {tpl === 'exec' ? '1 page' : '3 pages'}</span>
        <div className="row gap-2"><span className="t-sm t-sec">Format</span><Segmented options={['PDF','PNG','CSV','Notebook']} value={format} onChange={setFormat} /></div>
        <Button variant="primary" icon="download">Generate {format}</Button>
      </Card>
    </div>
  );
}

/* ====== PAGE 12 — Settings ====== */
function PageSettings({ theme, setTheme }) {
  const [tab, setTab] = useState('Datasets');
  const [drawer, setDrawer] = useState(false);
  return (
    <div className="col" style={{ gap: 'var(--space-5)', position: 'relative' }}>
      <PageHeader title="Settings" desc="Manage datasets, appearance and forecasting defaults." />
      <div style={{ display: 'grid', gridTemplateColumns: '180px minmax(0,1fr)', gap: 'var(--space-5)', alignItems: 'start' }}>
        <Card className="card-pad col gap-1" style={{ padding: 8 }}>
          {[['Datasets','database'],['Appearance','palette'],['Preferences','sliders'],['About','info']].map(([t, ic]) => (
            <button key={t} onClick={() => setTab(t)} className="row gap-3" style={{ border: 'none', background: tab === t ? 'var(--color-primary-subtle)' : 'transparent', color: tab === t ? 'var(--color-primary)' : 'var(--color-text-secondary)', padding: '9px 12px', borderRadius: 8, fontSize: 14, fontWeight: tab === t ? 600 : 500, cursor: 'pointer' }}><Icon name={ic} size={17} />{t}</button>
          ))}
        </Card>
        <div className="col gap-5">
          {tab === 'Datasets' && <>
            <div className="row" style={{ justifyContent: 'space-between' }}><h3 className="t-h3">Registered datasets</h3><Button variant="primary" icon="upload" onClick={() => setDrawer(true)}>Upload new dataset</Button></div>
            <Card style={{ overflow: 'hidden' }}>
              <table className="tbl">
                <thead><tr><th>Name</th><th>Domain</th><th className="num">Rows</th><th className="num">States</th><th>Created</th><th></th></tr></thead>
                <tbody>{DATASETS.map((d, i) => (
                  <tr key={i}><td style={{ fontWeight: 600 }}>{d.name}</td><td><Badge variant={d.domain === 'Brand Share' ? 'primary' : 'success'}>{d.domain}</Badge></td><td className="num">{fmt.fmtNum(d.rows)}</td><td className="num">{d.states}</td><td className="t-sec">{d.created}</td>
                  <td><div className="row gap-1" style={{ justifyContent: 'flex-end' }}><Button variant="ghost" size="sm" icon="eye" /><Button variant="ghost" size="sm" icon="trash" /></div></td></tr>
                ))}</tbody>
              </table>
            </Card>
          </>}
          {tab === 'Appearance' && <Card className="card-pad col gap-5">
            <div className="col gap-3"><span className="t-label">Theme</span><div className="row gap-3 wrap">
              {['Light','Dark','System'].map(t => { const on = (t === 'Dark') === (theme === 'dark') && t !== 'System'; return (
                <button key={t} onClick={() => t !== 'System' && setTheme(t.toLowerCase())} className="card card-pad col gap-2" style={{ cursor: 'pointer', width: 120, boxShadow: on ? '0 0 0 2px var(--color-primary)' : 'var(--shadow-resting)', alignItems: 'center', border: '1px solid var(--color-border-subtle)' }}>
                  <div style={{ width: '100%', height: 44, borderRadius: 6, background: t === 'Light' ? '#FAFAFA' : t === 'Dark' ? '#0A0A0F' : 'linear-gradient(90deg,#FAFAFA 50%,#0A0A0F 50%)', border: '1px solid var(--color-border-subtle)' }} />
                  <span className="t-sm">{t}</span>
                </button>
              ); })}
            </div></div>
            <div className="col gap-3" style={{ borderTop: '1px solid var(--color-border-subtle)', paddingTop: 20 }}><span className="t-label">Accent color</span>
              <div className="row gap-3">{['#4338CA','#059669','#0891B2','#7C3AED'].map((c, i) => <button key={c} style={{ width: 36, height: 36, borderRadius: 8, background: c, border: i === 0 ? '2px solid var(--color-text-primary)' : 'none', cursor: 'pointer' }} />)}</div>
              <span className="t-xs t-ter">Locked to indigo for v1.</span>
            </div>
          </Card>}
          {tab === 'Preferences' && <Card className="card-pad col gap-5">
            <PrefRow label="Default simulations" value="10,000" hint="Monte Carlo paths per run" />
            <PrefRow label="Default seed" value="42" hint="For reproducible simulations" />
            <PrefRow label="Default horizon" value="12 months" hint="Forecast steps ahead" />
          </Card>}
          {tab === 'About' && <Card className="card-pad col gap-4">
            <div className="row gap-3"><div style={{ width: 40, height: 40, borderRadius: 10, background: 'var(--color-primary)', display: 'grid', placeItems: 'center' }}><Icon name="layers" size={22} style={{ color: 'var(--color-on-primary)' }} /></div><div className="col"><span style={{ fontWeight: 600, fontSize: 16 }}>MarkovLens</span><span className="t-xs t-ter mono">v0.1.0 · MIT License</span></div></div>
            <p className="t-sm t-sec" style={{ textWrap: 'pretty' }}>A multi-domain Markov chain forecasting workbench. Built on Chan (2015) IJICIC and Becker (2026) longshot calibration.</p>
            <div className="row gap-2 wrap">{[['github','GitHub'],['fileText','Docs'],['helpCircle','Manual Book']].map(([ic, l]) => <Button key={l} variant="secondary" size="sm" icon={ic} iconRight="externalLink">{l}</Button>)}</div>
          </Card>}
        </div>
      </div>
      {drawer && <>
        <div onClick={() => setDrawer(false)} style={{ position: 'fixed', inset: 0, background: 'var(--color-overlay)', zIndex: 150 }} />
        <div className="card" style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: 'min(420px, 92vw)', zIndex: 160, borderRadius: 0, boxShadow: 'var(--shadow-floating)', display: 'flex', flexDirection: 'column' }}>
          <div className="row" style={{ justifyContent: 'space-between', padding: 16, borderBottom: '1px solid var(--color-border-subtle)' }}><h3 className="t-h3">Upload dataset</h3><Button variant="ghost" size="sm" icon="x" onClick={() => setDrawer(false)} /></div>
          <div className="col gap-4 scroll-area" style={{ padding: 16, overflow: 'auto' }}>
            <div className="col gap-2" style={{ alignItems: 'center', justifyContent: 'center', border: '2px dashed var(--color-border-visible)', borderRadius: 'var(--radius-md)', padding: 32, textAlign: 'center' }}><Icon name="upload" size={28} style={{ color: 'var(--color-text-tertiary)' }} /><span className="t-sm" style={{ fontWeight: 600 }}>Drop CSV here</span><span className="t-xs t-ter">columns: entity_id, period, state</span></div>
            <div><label className="field-label">Dataset name</label><Input placeholder="My dataset 2026" /></div>
            <div><label className="field-label">Domain</label><Select value="brand" onChange={() => {}} options={[{ value: 'brand', label: 'Brand Share' }, { value: 'churn', label: 'Customer Churn' }]} /></div>
            <span className="t-label" style={{ marginTop: 8 }}>Schema mapping</span>
            {['entity_id', 'period', 'state'].map(c => <div key={c} className="row gap-3" style={{ alignItems: 'center' }}><span className="mono t-xs" style={{ width: 80 }}>{c}</span><Icon name="arrowRight" size={14} style={{ color: 'var(--color-text-tertiary)' }} /><Select value={c} onChange={() => {}} options={['column_a', 'column_b', c]} style={{ flex: 1 }} /></div>)}
            <Button variant="primary" icon="check" style={{ marginTop: 8 }} onClick={() => setDrawer(false)}>Register dataset</Button>
          </div>
        </div>
      </>}
    </div>
  );
}
function PrefRow({ label, value, hint }) {
  return <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center', paddingBottom: 16, borderBottom: '1px solid var(--color-border-subtle)' }}>
    <div className="col gap-1"><span className="t-sm" style={{ fontWeight: 600 }}>{label}</span><span className="t-xs t-ter">{hint}</span></div>
    <Input value={value} onChange={() => {}} style={{ width: 140 }} />
  </div>;
}

Object.assign(window, { PageChurnLanding, PageWhatIf, PageReports, PageSettings, ChurnTabs });

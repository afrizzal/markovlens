/* ============================================================================
   Pages 0-2 — Design System Showcase · Marketing Landing · Login
   ========================================================================== */

/* ---------- shared section helpers ---------- */
function DSSection({ title, desc, children }) {
  return (
    <section className="col" style={{ gap: 'var(--space-4)' }}>
      <div className="col" style={{ gap: 2 }}>
        <h3 className="t-h3">{title}</h3>
        {desc && <p className="t-sm t-sec">{desc}</p>}
      </div>
      {children}
    </section>
  );
}
function Swatch({ name, varName, hex }) {
  return (
    <div className="col" style={{ gap: 6 }}>
      <div style={{ height: 56, borderRadius: 'var(--radius-sm)', background: `var(${varName})`, border: '1px solid var(--color-border-subtle)' }} />
      <div className="col" style={{ gap: 1 }}><span className="t-xs" style={{ fontWeight: 600 }}>{name}</span><span className="t-xs t-ter mono">{hex}</span></div>
    </div>
  );
}

/* ====== PAGE 0 — Design System Showcase ====== */
function PageDesignSystem({ theme }) {
  const colorsLight = [
    ['bg', '#FAFAFA'], ['surface', '#FFFFFF'], ['text-primary', '#0A0A0A'], ['text-secondary', '#52525B'],
    ['text-tertiary', '#A1A1AA'], ['primary', '#4338CA'], ['primary-subtle', '#EEF2FF'], ['success', '#059669'],
    ['warning', '#D97706'], ['danger', '#DC2626'], ['border-subtle', '#E4E4E7'], ['border-visible', '#D4D4D8'],
  ];
  const typeScale = [
    ['Display / 48', 48, 700], ['Heading 1 / 32', 32, 600], ['Heading 2 / 24', 24, 600],
    ['Heading 3 / 18', 18, 600], ['Body / 16', 16, 400], ['Small / 14', 14, 400], ['Caption / 12', 12, 500],
  ];
  return (
    <div className="col" style={{ gap: 'var(--space-7)' }}>
      <header className="col" style={{ gap: 8 }}>
        <Badge variant="primary" icon="palette">Page 0 · Reference</Badge>
        <h1 className="t-h1">Design System</h1>
        <p className="t-body t-sec" style={{ maxWidth: 640 }}>Every token below maps to a CSS variable in <span className="mono t-sm">styles/markov.css</span>. Toggle the theme in the top bar to inspect both modes; extract values directly for the Streamlit theme.</p>
      </header>

      <DSSection title="Color — semantic tokens" desc="Light & dark resolve from the same variable names. Currently showing the active theme.">
        <Card className="card-pad"><div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: 'var(--space-4)' }}>
          {colorsLight.map(([n, h]) => <Swatch key={n} name={n} varName={`--color-${n}`} hex={theme === 'dark' ? '' : h} />)}
        </div></Card>
      </DSSection>

      <DSSection title="Chart palette" desc="Categorical (6 series, priority order) + sequential ramp for matrix heatmaps.">
        <div className="row gap-5 wrap">
          <Card className="card-pad col gap-3" style={{ flex: 1, minWidth: 280 }}>
            <span className="t-label">Categorical</span>
            <div className="row gap-3 wrap">{[1,2,3,4,5,6].map(i => (
              <div key={i} className="col" style={{ gap: 4, alignItems: 'center' }}><div style={{ width: 44, height: 44, borderRadius: 'var(--radius-sm)', background: `var(--chart-${i})` }} /><span className="t-xs t-ter mono">chart-{i}</span></div>
            ))}</div>
          </Card>
          <Card className="card-pad col gap-3" style={{ flex: 1, minWidth: 280 }}>
            <span className="t-label">Sequential</span>
            <div className="row" style={{ borderRadius: 'var(--radius-sm)', overflow: 'hidden', height: 44 }}>{[1,2,3,4,5].map(i => <div key={i} style={{ flex: 1, background: `var(--chart-seq-${i})` }} />)}</div>
            <span className="t-xs t-ter">Low probability → high probability</span>
          </Card>
        </div>
      </DSSection>

      <DSSection title="Typography" desc="Geist for UI, JetBrains Mono for all numerals (tabular-nums always).">
        <Card className="card-pad col" style={{ gap: 'var(--space-4)' }}>
          {typeScale.map(([l, s, w]) => (
            <div key={l} className="row gap-5" style={{ alignItems: 'baseline', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 12 }}>
              <span className="t-xs t-ter mono" style={{ width: 120, flex: '0 0 120px' }}>{l}</span>
              <span style={{ fontSize: s, fontWeight: w, letterSpacing: s >= 24 ? '-0.01em' : 0 }}>Forecasting that makes sense</span>
            </div>
          ))}
          <div className="row gap-5" style={{ alignItems: 'baseline' }}>
            <span className="t-xs t-ter mono" style={{ width: 120, flex: '0 0 120px' }}>Numerals / mono</span>
            <span className="mono" style={{ fontSize: 24, fontWeight: 600 }}>1,247.32 · 67.4% · Rp 1.2B</span>
          </div>
        </Card>
      </DSSection>

      <DSSection title="Buttons" desc="Four variants × states. Consistent height, radius and motion.">
        <Card className="card-pad col" style={{ gap: 'var(--space-5)' }}>
          {[['Primary', 'primary'], ['Secondary', 'secondary'], ['Ghost', 'ghost'], ['Destructive', 'danger']].map(([l, v]) => (
            <div key={v} className="row gap-4 wrap" style={{ alignItems: 'center' }}>
              <span className="t-xs t-ter" style={{ width: 90, flex: '0 0 90px' }}>{l}</span>
              <Button variant={v} icon="play">Run Forecast</Button>
              <Button variant={v}>Default</Button>
              <Button variant={v} disabled>Disabled</Button>
              <Button variant={v} size="sm">Small</Button>
              <Button variant={v} icon="plus" />
            </div>
          ))}
        </Card>
      </DSSection>

      <DSSection title="Form controls">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 'var(--space-4)' }}>
          <Card className="card-pad col gap-4">
            <div><label className="field-label">Text input</label><Input icon="search" placeholder="Search datasets…" /></div>
            <div><label className="field-label">Select</label><Select value="m2" onChange={() => {}} options={[{value:'m1',label:'m1 — Homogeneous'},{value:'m2',label:'m2 — Time-varying'},{value:'m3',label:'m3 — Extended'}]} /></div>
            <SliderDemo />
          </Card>
          <Card className="card-pad col gap-4">
            <div className="row gap-3" style={{ justifyContent: 'space-between' }}><span className="t-sm">Segmented</span><Segmented options={['m1','m2','m3']} value="m2" onChange={()=>{}} /></div>
            <ControlsDemo />
          </Card>
        </div>
      </DSSection>

      <DSSection title="KPI cards" desc="With / without delta and sparkline. Optional accent bar in section color.">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-4)' }}>
          <KPICard label="With delta + spark" value="1,247" delta={12.3} sparkline={[3,5,4,6,7,6,8,9,8,10]} accent="var(--chart-1)" />
          <KPICard label="Delta only" value="67.4" unit="%" delta={-2.1} accent="var(--chart-2)" />
          <KPICard label="Value only" value="42" icon="database" />
          <KPICard label="Empty / no data" value="—" tooltip="No forecast has been run yet." />
        </div>
      </DSSection>

      <DSSection title="Status badges">
        <Card className="card-pad row gap-3 wrap">
          <Badge variant="success" icon="check">Success</Badge><Badge variant="warning" icon="alertTriangle">Warning</Badge>
          <Badge variant="danger" icon="x">Danger</Badge><Badge variant="info" icon="info">Info</Badge><Badge variant="neutral">Neutral</Badge>
          <Badge variant="primary" icon="sparkles">Best fit</Badge>
        </Card>
      </DSSection>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-5)' }}>
        <DSSection title="Spacing — 4px base">
          <Card className="card-pad col gap-3">{[1,2,3,4,5,6,7,8].map(i => { const px = [4,8,12,16,24,32,48,64][i-1]; return (
            <div key={i} className="row gap-3" style={{ alignItems: 'center' }}><span className="t-xs t-ter mono" style={{ width: 64 }}>space-{i}</span><div style={{ height: 12, width: px, background: 'var(--color-primary)', borderRadius: 3 }} /><span className="t-xs t-ter mono">{px}px</span></div>
          ); })}</Card>
        </DSSection>
        <DSSection title="Radius & shadow">
          <Card className="card-pad col gap-5">
            <div className="row gap-4">{[['sm',6],['md',12],['lg',20],['pill',999]].map(([n,r]) => (
              <div key={n} className="col gap-2" style={{ alignItems: 'center' }}><div style={{ width: 56, height: 44, background: 'var(--color-surface-sunken)', border: '1px solid var(--color-border-visible)', borderRadius: r }} /><span className="t-xs t-ter mono">{n}</span></div>
            ))}</div>
            <div className="row gap-4">{[['resting','var(--shadow-resting)'],['raised','var(--shadow-raised)'],['floating','var(--shadow-floating)']].map(([n,s]) => (
              <div key={n} className="col gap-2" style={{ alignItems: 'center' }}><div style={{ width: 64, height: 44, background: 'var(--color-surface)', borderRadius: 'var(--radius-sm)', boxShadow: s }} /><span className="t-xs t-ter mono">{n}</span></div>
            ))}</div>
          </Card>
        </DSSection>
      </div>
    </div>
  );
}
function SliderDemo() { const [v, setV] = useState(12); return <Slider label="Time horizon" value={v} min={1} max={24} onChange={setV} format={x => `${x} mo`} />; }
function ControlsDemo() {
  const [t, setT] = useState(true); const [c, setC] = useState(true); const [r, setR] = useState('a');
  return (
    <div className="col gap-4">
      <div className="row gap-3" style={{ justifyContent: 'space-between' }}><span className="t-sm">Toggle</span><Toggle on={t} onChange={setT} /></div>
      <div className="row gap-3" style={{ justifyContent: 'space-between' }}><span className="t-sm">Checkbox</span><Checkbox on={c} onChange={setC} /></div>
      <div className="row gap-4"><span className="t-sm">Radio</span><div className="row gap-4">{['a','b'].map(o => <span key={o} className="row gap-2"><Checkbox radio on={r===o} onChange={()=>setR(o)} /><span className="t-sm t-sec">Option {o.toUpperCase()}</span></span>)}</div></div>
    </div>
  );
}

/* ====== PAGE 1 — Marketing Landing ====== */
function PageLanding({ setPage, theme, setTheme }) {
  return (
    <div className="col" style={{ minHeight: '100%', background: 'var(--color-bg)' }}>
      <nav className="row" style={{ justifyContent: 'space-between', padding: '18px max(24px, 5vw)', maxWidth: 1200, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
        <div className="row gap-2"><div style={{ width: 28, height: 28, borderRadius: 8, background: 'var(--color-primary)', display: 'grid', placeItems: 'center' }}><Icon name="layers" size={17} style={{ color: 'var(--color-on-primary)' }} /></div><span style={{ fontWeight: 600, fontSize: 17 }}>MarkovLens</span></div>
        <div className="row gap-2">
          <Button variant="ghost" size="sm" icon={theme === 'dark' ? 'sun' : 'moon'} onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
          <Button variant="ghost" size="sm" icon="github">GitHub</Button>
          <Button variant="primary" size="sm" onClick={() => setPage(4)}>Try Demo</Button>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,440px)', gap: 'var(--space-7)', alignItems: 'center', maxWidth: 1200, margin: '0 auto', padding: '4vh max(24px, 5vw) 6vh', width: '100%', boxSizing: 'border-box' }}>
        <div className="col" style={{ gap: 'var(--space-5)' }}>
          <Badge variant="primary" icon="sparkles">Markov chain forecasting workbench</Badge>
          <h1 className="t-display" style={{ fontSize: 'clamp(36px, 5vw, 56px)' }}>Forecasting that<br />makes sense.</h1>
          <p className="t-body t-sec" style={{ maxWidth: 460, textWrap: 'pretty' }}>Apply Markov chain models to brand share and customer churn — built on Chan (2015) IJICIC math and Becker (2026) longshot calibration. Rigorous probability, calm interface.</p>
          <div className="row gap-3 wrap">
            <Button variant="primary" size="lg" icon="play" onClick={() => setPage(4)}>Try Demo</Button>
            <Button variant="secondary" size="lg" icon="github">View on GitHub</Button>
          </div>
          <div className="row gap-3" style={{ marginTop: 8 }}>
            <Badge variant="neutral" icon="bookmark">Chan (2015) · IJICIC Vol. 11</Badge>
            <span className="t-xs t-ter">Peer-reviewed academic foundation</span>
          </div>
        </div>
        <Card raised className="card-pad" style={{ display: 'grid', placeItems: 'center', background: 'var(--color-surface)', aspectRatio: '1 / 1' }}>
          <div className="col" style={{ gap: 16, alignItems: 'center' }}>
            <span className="t-label">Transition matrix · live</span>
            <AnimatedMatrix n={5} cell={52} />
            <span className="t-xs t-ter mono">P[i,j] = P(state i → state j)</span>
          </div>
        </Card>
      </section>

      {/* Two domains */}
      <section style={{ maxWidth: 1200, margin: '0 auto', padding: '0 max(24px, 5vw) 6vh', width: '100%', boxSizing: 'border-box' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--space-5)' }}>
          {[
            { t: 'Brand Share Forecasting', d: 'Predict how e-commerce market shares evolve from consumer switching data. Stacked-area forecasts, transition heatmaps, Monte Carlo.', accent: 'var(--chart-1)', icon: 'trendingUp', page: 5, prev: 'brand' },
            { t: 'Customer Churn Modeling', d: 'Model customers as Active → At-Risk → Churned states. Sankey flow diagrams and a what-if retention simulator.', accent: 'var(--chart-2)', icon: 'users', page: 9, prev: 'churn' },
          ].map(c => (
            <Card key={c.t} accent={c.accent} className="card-pad col gap-4" raised>
              <div className="row gap-3"><div style={{ width: 40, height: 40, borderRadius: 'var(--radius-sm)', background: c.accent, display: 'grid', placeItems: 'center', color: '#fff' }}><Icon name={c.icon} size={20} /></div><h3 className="t-h3">{c.t}</h3></div>
              <p className="t-sm t-sec" style={{ textWrap: 'pretty' }}>{c.d}</p>
              <div style={{ height: 120, borderRadius: 'var(--radius-sm)', overflow: 'hidden', background: 'var(--color-surface-sunken)', padding: 8 }}>
                {c.prev === 'brand' ? <MiniForecast data={miniForecast(1)} color={c.accent} height={104} /> : <Sankey periods={5} />}
              </div>
              <Button variant="secondary" iconRight="arrowRight" onClick={() => setPage(c.page)}>Open {c.prev === 'brand' ? 'Brand Share' : 'Churn'}</Button>
            </Card>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section style={{ maxWidth: 1200, margin: '0 auto', padding: '0 max(24px, 5vw) 7vh', width: '100%', boxSizing: 'border-box' }}>
        <div className="col gap-5" style={{ alignItems: 'center', textAlign: 'center', marginBottom: 'var(--space-6)' }}><span className="t-label">How it works</span><h2 className="t-h1">Three steps, one engine</h2></div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--space-5)' }}>
          {[['grid', 'Build the matrix', 'Estimate transition probabilities from your historical state-to-state data.'],
            ['activity', 'Run simulation', 'Project shares forward with m1/m2/m3, or run 10,000 Monte Carlo paths.'],
            ['target', 'Calibrate & forecast', 'Apply longshot calibration, then read confidence-banded forecasts.']].map(([ic, t, d], i) => (
            <Card key={t} className="card-pad col gap-3">
              <div className="row gap-3"><span className="mono t-h3" style={{ color: 'var(--color-text-tertiary)' }}>0{i+1}</span><div style={{ width: 36, height: 36, borderRadius: 'var(--radius-sm)', background: 'var(--color-primary-subtle)', display: 'grid', placeItems: 'center', color: 'var(--color-primary)' }}><Icon name={ic} size={19} /></div></div>
              <h3 className="t-h3">{t}</h3><p className="t-sm t-sec" style={{ textWrap: 'pretty' }}>{d}</p>
            </Card>
          ))}
        </div>
      </section>

      <footer style={{ borderTop: '1px solid var(--color-border-subtle)', padding: '24px max(24px, 5vw)', background: 'var(--color-surface)' }}>
        <div className="row wrap gap-4" style={{ justifyContent: 'space-between', maxWidth: 1200, margin: '0 auto' }}>
          <span className="t-xs t-ter">© 2026 MarkovLens · Built on Chan (2015) IJICIC</span>
          <div className="row gap-5">{['GitHub', 'Docs', 'Manual Book'].map(l => <a key={l} className="t-xs t-sec" href="#">{l}</a>)}</div>
        </div>
      </footer>
    </div>
  );
}

/* ====== PAGE 2 — Login ====== */
function PageLogin({ setPage, theme }) {
  const [mode, setMode] = useState('signin');
  const [show, setShow] = useState(false);
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', minHeight: '100%' }}>
      <div style={{ display: 'grid', placeItems: 'center', padding: 'var(--space-6)', background: theme === 'dark' ? 'var(--color-bg)' : 'linear-gradient(135deg, #FAFAFA 0%, #EEF2FF 100%)' }}>
        <div className="col" style={{ gap: 'var(--space-5)', width: 'min(360px, 100%)' }}>
          <div className="row gap-2" style={{ justifyContent: 'center' }}><div style={{ width: 32, height: 32, borderRadius: 8, background: 'var(--color-primary)', display: 'grid', placeItems: 'center' }}><Icon name="layers" size={19} style={{ color: 'var(--color-on-primary)' }} /></div><span style={{ fontWeight: 600, fontSize: 19 }}>MarkovLens</span></div>
          <Card raised className="card-pad col" style={{ gap: 'var(--space-4)' }}>
            <div className="col gap-1"><h2 className="t-h2">{mode === 'signin' ? 'Welcome back' : 'Create account'}</h2><p className="t-sm t-sec">{mode === 'signin' ? 'Sign in to your workbench' : 'Start forecasting in seconds'}</p></div>
            <Segmented options={[{value:'signin',label:'Sign in'},{value:'signup',label:'Create account'}]} value={mode} onChange={setMode} />
            <div className="col gap-2">
              <Button variant="secondary" icon="google">Continue with Google</Button>
              <Button variant="secondary" icon="github">Continue with GitHub</Button>
            </div>
            <div className="row gap-3" style={{ alignItems: 'center' }}><div style={{ flex: 1, height: 1, background: 'var(--color-border-subtle)' }} /><span className="t-xs t-ter">or</span><div style={{ flex: 1, height: 1, background: 'var(--color-border-subtle)' }} /></div>
            <div className="col gap-3">
              <div><label className="field-label">Email</label><Input icon="mail" type="email" placeholder="you@company.com" /></div>
              <div><label className="field-label">Password</label>
                <div style={{ position: 'relative' }}><Input icon="lock" type={show ? 'text' : 'password'} placeholder="••••••••" /><button onClick={() => setShow(s => !s)} style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', border: 'none', background: 'transparent', cursor: 'pointer', color: 'var(--color-text-tertiary)' }}><Icon name="eye" size={16} /></button></div>
              </div>
              {mode === 'signin' && <a href="#" className="t-xs" style={{ color: 'var(--color-primary)', alignSelf: 'flex-end' }}>Forgot password?</a>}
            </div>
            <Button variant="primary" onClick={() => setPage(4)}>{mode === 'signin' ? 'Sign in' : 'Create account'}</Button>
          </Card>
          <div className="col gap-1" style={{ alignItems: 'center' }}><span className="t-xs t-ter">Built on Chan (2015) · IJICIC Vol. 11</span><span className="t-xs t-ter mono">v0.1.0</span></div>
        </div>
      </div>
      <div style={{ display: 'grid', placeItems: 'center', background: 'var(--color-primary)', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 70% 30%, rgba(255,255,255,0.12), transparent 60%)' }} />
        <div className="col" style={{ gap: 24, alignItems: 'center', zIndex: 1, color: '#fff', textAlign: 'center', padding: 24 }}>
          <div style={{ padding: 24, borderRadius: 'var(--radius-lg)', background: 'rgba(255,255,255,0.08)', backdropFilter: 'blur(4px)', border: '1px solid rgba(255,255,255,0.16)' }}><AnimatedMatrix n={5} cell={48} /></div>
          <div className="col gap-2" style={{ maxWidth: 360 }}><h2 style={{ color: '#fff', fontSize: 22 }}>Same math, different stories</h2><p style={{ color: 'rgba(255,255,255,0.78)', fontSize: 14 }}>Markov chains applied to real business decisions — brand share and customer retention.</p></div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { PageDesignSystem, PageLanding, PageLogin });

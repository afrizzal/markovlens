/* ============================================================================
   App — top-nav page switcher (design-contract chrome), theme state,
   page routing. Marketing pages render full-bleed; app pages wrap in AppShell.
   ========================================================================== */

const PAGES = [
  { id: 0, name: 'Design System', short: 'Design System', kind: 'doc' },
  { id: 1, name: 'Landing', short: 'Landing', kind: 'full' },
  { id: 2, name: 'Login', short: 'Login', kind: 'full' },
  { id: 3, name: 'App Shell', short: 'App Shell', kind: 'shell', crumb: ['Home'] },
  { id: 4, name: 'Dashboard', short: 'Dashboard', kind: 'shell', crumb: ['Home'] },
  { id: 5, name: 'Brand Share', short: 'Brand Share', kind: 'shell', crumb: ['Brand Share', 'Overview'] },
  { id: 6, name: 'Transition Matrix', short: 'Matrix', kind: 'shell', crumb: ['Brand Share', 'Transition Matrix'] },
  { id: 7, name: 'Monte Carlo', short: 'Monte Carlo', kind: 'shell', crumb: ['Brand Share', 'Monte Carlo'] },
  { id: 8, name: 'Model Comparison', short: 'Compare', kind: 'shell', crumb: ['Brand Share', 'Model Comparison'] },
  { id: 9, name: 'Customer Churn', short: 'Churn', kind: 'shell', crumb: ['Customer Churn', 'Overview'] },
  { id: 10, name: 'What-If Simulator', short: 'What-If', kind: 'shell', crumb: ['Customer Churn', 'What-If Simulator'] },
  { id: 11, name: 'Reports', short: 'Reports', kind: 'shell', crumb: ['Reports'] },
  { id: 12, name: 'Settings', short: 'Settings', kind: 'shell', crumb: ['Settings'] },
];

function ShellDemo() {
  return (
    <div className="col" style={{ gap: 'var(--space-6)' }}>
      <PageHeader title="App Shell" desc="The master template that wraps every in-product page (4–12)." />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--space-4)' }}>
        {[['panelLeft', 'Collapsible sidebar', '240px → 64px. Nav grouped Forecasting / Output / System, with a user chip pinned to the bottom.'],
          ['search', 'Command palette', '⌘K opens a fuzzy launcher to jump to any page or action.'],
          ['grid', 'Breadcrumb topbar', '56px bar with breadcrumb, centered search, theme toggle, notifications and avatar menu.'],
          ['box', 'Content area', 'max-width 1440px, 32px padding, with a soft fade-in on page change.']].map(([ic, t, d]) => (
          <Card key={t} accent="var(--color-primary)" className="card-pad col gap-3">
            <div style={{ width: 36, height: 36, borderRadius: 'var(--radius-sm)', background: 'var(--color-primary-subtle)', display: 'grid', placeItems: 'center', color: 'var(--color-primary)' }}><Icon name={ic} size={19} /></div>
            <span className="t-sm" style={{ fontWeight: 600 }}>{t}</span><p className="t-xs t-sec" style={{ textWrap: 'pretty' }}>{d}</p>
          </Card>
        ))}
      </div>
      <Card className="card-pad row gap-3" style={{ alignItems: 'center' }}>
        <Icon name="info" size={18} style={{ color: 'var(--color-primary)' }} />
        <span className="t-sm t-sec">You're looking at the shell right now — the sidebar, topbar and palette here are the same components inherited by every page below. Try <span className="badge badge-neutral mono" style={{ fontSize: 11 }}>⌘K</span> or collapse the sidebar.</span>
      </Card>
    </div>
  );
}

function App() {
  const [theme, setThemeRaw] = useState(() => localStorage.getItem('ml-theme') || 'light');
  const [page, setPageRaw] = useState(() => Number(localStorage.getItem('ml-page') || 0));
  const setTheme = (t) => { setThemeRaw(t); localStorage.setItem('ml-theme', t); };
  const setPage = (p) => { setPageRaw(p); localStorage.setItem('ml-page', String(p)); };
  useEffect(() => { document.documentElement.setAttribute('data-theme', theme); }, [theme]);

  const meta = PAGES[page];
  let content;
  if (page === 0) content = <PageDesignSystem theme={theme} />;
  else if (page === 1) content = <PageLanding setPage={setPage} theme={theme} setTheme={setTheme} />;
  else if (page === 2) content = <PageLogin setPage={setPage} theme={theme} />;
  else {
    let inner;
    if (page === 3) inner = <ShellDemo />;
    else if (page === 4) inner = <PageDashboard setPage={setPage} />;
    else if (page === 5) inner = <PageBrandLanding page={page} setPage={setPage} theme={theme} />;
    else if (page === 6) inner = <PageMatrix page={page} setPage={setPage} theme={theme} />;
    else if (page === 7) inner = <PageMonteCarlo page={page} setPage={setPage} theme={theme} />;
    else if (page === 8) inner = <PageModelCompare page={page} setPage={setPage} />;
    else if (page === 9) inner = <PageChurnLanding page={page} setPage={setPage} />;
    else if (page === 10) inner = <PageWhatIf page={page} setPage={setPage} />;
    else if (page === 11) inner = <PageReports />;
    else if (page === 12) inner = <PageSettings theme={theme} setTheme={setTheme} />;
    content = <AppShell page={page} setPage={setPage} breadcrumb={meta.crumb} theme={theme} setTheme={setTheme}>{inner}</AppShell>;
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* design-contract chrome */}
      <div className="row" style={{ flex: '0 0 auto', height: 46, borderBottom: '1px solid var(--color-border-subtle)', background: 'var(--color-surface)', padding: '0 12px', gap: 12 }}>
        <div className="row gap-2" style={{ flex: '0 0 auto' }}>
          <Icon name="command" size={15} style={{ color: 'var(--color-text-tertiary)' }} />
          <span className="t-xs" style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>Design Contract</span>
          <span className="badge badge-neutral mono" style={{ fontSize: 10 }}>12 pages</span>
        </div>
        <div className="row gap-1 scroll-area" style={{ flex: 1, overflowX: 'auto', overflowY: 'hidden', padding: '0 4px' }}>
          {PAGES.map(p => (
            <button key={p.id} onClick={() => setPage(p.id)} className="row gap-2" style={{ flex: '0 0 auto', border: '1px solid', borderColor: page === p.id ? 'var(--color-primary)' : 'transparent', background: page === p.id ? 'var(--color-primary-subtle)' : 'transparent', color: page === p.id ? 'var(--color-primary)' : 'var(--color-text-secondary)', borderRadius: 'var(--radius-pill)', padding: '5px 11px', fontSize: 12, fontWeight: 500, cursor: 'pointer', whiteSpace: 'nowrap' }}
              onMouseEnter={e => { if (page !== p.id) e.currentTarget.style.background = 'var(--color-surface-sunken)'; }} onMouseLeave={e => { if (page !== p.id) e.currentTarget.style.background = 'transparent'; }}>
              <span className="mono" style={{ opacity: 0.55, fontSize: 11 }}>{p.id}</span>{p.short}
            </button>
          ))}
        </div>
        <div className="row gap-1" style={{ flex: '0 0 auto' }}>
          <Button variant="ghost" size="sm" icon="chevronLeft" onClick={() => setPage(Math.max(0, page - 1))} />
          <Button variant="ghost" size="sm" icon="chevronRight" onClick={() => setPage(Math.min(12, page + 1))} />
          <Button variant="ghost" size="sm" icon={theme === 'dark' ? 'sun' : 'moon'} onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
        </div>
      </div>
      {/* page area */}
      <div style={{ flex: 1, minHeight: 0, overflow: meta.kind === 'shell' ? 'hidden' : 'auto', background: 'var(--color-bg)' }}>
        {meta.kind === 'shell' ? content
          : meta.kind === 'doc' ? <div className="page-enter" key={page} style={{ maxWidth: 1100, margin: '0 auto', padding: 'var(--space-7) var(--space-6)' }}>{content}</div>
          : <div className="page-enter" key={page} style={{ minHeight: '100%' }}>{content}</div>}
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);

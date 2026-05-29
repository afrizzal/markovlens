/* ============================================================================
   App Shell — collapsible sidebar + topbar. Wraps pages 4-12.
   ========================================================================== */

const NAV_GROUPS = [
  { label: 'Forecasting', items: [
    { id: 'home', page: 4, label: 'Home', icon: 'home' },
    { id: 'brand', page: 5, label: 'Brand Share', icon: 'trendingUp' },
    { id: 'churn', page: 9, label: 'Customer Churn', icon: 'users' },
  ]},
  { label: 'Output', items: [
    { id: 'reports', page: 11, label: 'Reports', icon: 'fileText' },
  ]},
  { label: 'System', items: [
    { id: 'settings', page: 12, label: 'Settings', icon: 'settings' },
  ]},
];

/* which nav item is active for a given page */
function activeNavFor(page) {
  if (page >= 5 && page <= 8) return 'brand';
  if (page === 9 || page === 10) return 'churn';
  if (page === 4) return 'home';
  if (page === 11) return 'reports';
  if (page === 12) return 'settings';
  return null;
}

function CommandPalette({ open, onClose, setPage }) {
  const [q, setQ] = useState('');
  const cmds = [
    { label: 'Go to Home', page: 4, icon: 'home' },
    { label: 'Run Brand Share forecast', page: 5, icon: 'trendingUp' },
    { label: 'Open Transition Matrix', page: 6, icon: 'grid' },
    { label: 'Monte Carlo Simulator', page: 7, icon: 'activity' },
    { label: 'Compare models', page: 8, icon: 'gitBranch' },
    { label: 'Customer Churn analysis', page: 9, icon: 'users' },
    { label: 'What-If Simulator', page: 10, icon: 'sliders' },
    { label: 'Generate a report', page: 11, icon: 'fileText' },
    { label: 'Settings', page: 12, icon: 'settings' },
  ];
  const filtered = cmds.filter(c => c.label.toLowerCase().includes(q.toLowerCase()));
  useEffect(() => { if (open) setQ(''); }, [open]);
  if (!open) return null;
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 200, background: 'var(--color-overlay)', display: 'flex', alignItems: 'flex-start', justifyContent: 'center', paddingTop: '12vh', backdropFilter: 'blur(2px)' }}>
      <div onClick={e => e.stopPropagation()} className="card card-raised" style={{ width: 'min(560px, 92vw)', boxShadow: 'var(--shadow-floating)', overflow: 'hidden' }}>
        <div className="row gap-3" style={{ padding: '14px 16px', borderBottom: '1px solid var(--color-border-subtle)' }}>
          <Icon name="search" size={18} style={{ color: 'var(--color-text-tertiary)' }} />
          <input autoFocus value={q} onChange={e => setQ(e.target.value)} placeholder="Search pages and actions…" style={{ flex: 1, border: 'none', outline: 'none', background: 'transparent', color: 'var(--color-text-primary)', fontSize: 15, fontFamily: 'inherit' }} />
          <span className="badge badge-neutral mono">ESC</span>
        </div>
        <div className="col" style={{ maxHeight: 340, overflow: 'auto', padding: 8 }}>
          {filtered.map((c, i) => (
            <button key={i} onClick={() => { setPage(c.page); onClose(); }} className="row gap-3" style={{ border: 'none', background: 'transparent', padding: '10px 12px', borderRadius: 8, color: 'var(--color-text-primary)', textAlign: 'left', fontSize: 14 }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--color-surface-sunken)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              <Icon name={c.icon} size={17} style={{ color: 'var(--color-text-secondary)' }} />{c.label}
            </button>
          ))}
          {!filtered.length && <div className="t-sm t-ter" style={{ padding: 16, textAlign: 'center' }}>No matches</div>}
        </div>
      </div>
    </div>
  );
}

function AppShell({ page, setPage, breadcrumb, theme, setTheme, children }) {
  const [collapsed, setCollapsed] = useState(false);
  const [palette, setPalette] = useState(false);
  const [menu, setMenu] = useState(false);
  const active = activeNavFor(page);
  useEffect(() => {
    const h = e => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPalette(p => !p); } if (e.key === 'Escape') setPalette(false); };
    window.addEventListener('keydown', h); return () => window.removeEventListener('keydown', h);
  }, []);
  const sw = collapsed ? 'var(--sidebar-w-collapsed)' : 'var(--sidebar-w)';
  return (
    <div style={{ display: 'flex', minHeight: '100%', height: '100%' }}>
      {/* Sidebar */}
      <aside style={{ width: sw, flex: `0 0 ${sw}`, transition: 'width var(--dur-trans) var(--ease), flex-basis var(--dur-trans) var(--ease)', background: 'var(--color-surface)', borderRight: '1px solid var(--color-border-subtle)', display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div className="row" style={{ height: 'var(--topbar-h)', padding: collapsed ? '0' : '0 18px', justifyContent: collapsed ? 'center' : 'flex-start', gap: 10, borderBottom: '1px solid var(--color-border-subtle)' }}>
          <div style={{ width: 28, height: 28, borderRadius: 8, background: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: '0 0 auto' }}>
            <Icon name="layers" size={17} style={{ color: 'var(--color-on-primary)' }} />
          </div>
          {!collapsed && <span style={{ fontWeight: 600, fontSize: 16, letterSpacing: '-0.01em' }}>MarkovLens</span>}
        </div>
        <nav className="col" style={{ padding: collapsed ? '12px 8px' : '12px 12px', gap: 16, flex: 1, overflow: 'auto' }}>
          {NAV_GROUPS.map(g => (
            <div key={g.label} className="col" style={{ gap: 2 }}>
              {!collapsed && <div className="t-label" style={{ padding: '4px 12px', fontSize: 11 }}>{g.label}</div>}
              {g.items.map(it => {
                const on = active === it.id;
                return (
                  <button key={it.id} onClick={() => setPage(it.page)} title={it.label}
                    className="row gap-3" style={{ border: 'none', background: on ? 'var(--color-primary-subtle)' : 'transparent', color: on ? 'var(--color-primary)' : 'var(--color-text-secondary)', padding: collapsed ? '10px' : '9px 12px', borderRadius: 8, fontSize: 14, fontWeight: on ? 600 : 500, justifyContent: collapsed ? 'center' : 'flex-start', transition: 'background var(--dur-micro) var(--ease), color var(--dur-micro) var(--ease)' }}
                    onMouseEnter={e => { if (!on) e.currentTarget.style.background = 'var(--color-surface-sunken)'; }} onMouseLeave={e => { if (!on) e.currentTarget.style.background = 'transparent'; }}>
                    <Icon name={it.icon} size={19} />{!collapsed && it.label}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>
        {/* user chip */}
        <div style={{ borderTop: '1px solid var(--color-border-subtle)', padding: collapsed ? 10 : 12 }}>
          <div className="row gap-3" style={{ padding: collapsed ? 0 : '6px 6px', justifyContent: collapsed ? 'center' : 'flex-start' }}>
            <div style={{ width: 30, height: 30, borderRadius: 8, background: 'linear-gradient(135deg, var(--chart-1), var(--chart-6))', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 600, flex: '0 0 auto' }}>AR</div>
            {!collapsed && <div className="col" style={{ gap: 1, overflow: 'hidden' }}><span className="t-sm" style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>Afriza R.</span><span className="t-xs t-ter" style={{ whiteSpace: 'nowrap' }}>Business Analyst</span></div>}
          </div>
        </div>
      </aside>

      {/* Main column */}
      <div className="col" style={{ flex: 1, minWidth: 0, height: '100%' }}>
        {/* Topbar */}
        <header className="row" style={{ height: 'var(--topbar-h)', flex: '0 0 var(--topbar-h)', borderBottom: '1px solid var(--color-border-subtle)', background: 'var(--color-surface)', padding: '0 16px', gap: 16 }}>
          <Button variant="ghost" size="sm" icon="panelLeft" onClick={() => setCollapsed(c => !c)} />
          <div className="row gap-2 t-sm" style={{ color: 'var(--color-text-secondary)', minWidth: 0 }}>
            {breadcrumb.map((b, i) => (
              <React.Fragment key={i}>
                {i > 0 && <Icon name="chevronRight" size={14} style={{ color: 'var(--color-text-tertiary)' }} />}
                <span style={{ color: i === breadcrumb.length - 1 ? 'var(--color-text-primary)' : 'inherit', fontWeight: i === breadcrumb.length - 1 ? 600 : 400, whiteSpace: 'nowrap' }}>{b}</span>
              </React.Fragment>
            ))}
          </div>
          <button onClick={() => setPalette(true)} className="row gap-2" style={{ flex: 1, maxWidth: 380, margin: '0 auto', height: 34, border: '1px solid var(--color-border-visible)', borderRadius: 'var(--radius-sm)', background: 'var(--color-bg)', color: 'var(--color-text-tertiary)', padding: '0 10px', fontSize: 13 }}>
            <Icon name="search" size={15} /><span style={{ flex: 1, textAlign: 'left' }}>Search or jump to…</span><span className="badge badge-neutral mono" style={{ fontSize: 11 }}>⌘K</span>
          </button>
          <div className="row gap-1">
            <Button variant="ghost" size="sm" icon={theme === 'dark' ? 'sun' : 'moon'} onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
            <div style={{ position: 'relative' }}>
              <Button variant="ghost" size="sm" icon="bell" />
              <span style={{ position: 'absolute', top: 4, right: 4, minWidth: 15, height: 15, padding: '0 3px', borderRadius: 999, background: 'var(--color-danger)', color: '#fff', fontSize: 10, fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1.5px solid var(--color-surface)' }}>3</span>
            </div>
            <div style={{ position: 'relative' }}>
              <button onClick={() => setMenu(m => !m)} style={{ border: 'none', background: 'transparent', cursor: 'pointer', padding: 2, borderRadius: 8 }}>
                <div style={{ width: 30, height: 30, borderRadius: 8, background: 'linear-gradient(135deg, var(--chart-1), var(--chart-6))', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 600 }}>AR</div>
              </button>
              {menu && (
                <>
                  <div onClick={() => setMenu(false)} style={{ position: 'fixed', inset: 0, zIndex: 90 }} />
                  <div className="card card-raised" style={{ position: 'absolute', right: 0, top: 40, width: 200, zIndex: 100, boxShadow: 'var(--shadow-floating)', padding: 6 }}>
                    <div style={{ padding: '8px 10px', borderBottom: '1px solid var(--color-border-subtle)', marginBottom: 4 }}><div className="t-sm" style={{ fontWeight: 600 }}>Afriza R.</div><div className="t-xs t-ter">afriza@markovlens.app</div></div>
                    {[['user', 'Profile'], ['settings', 'Settings'], ['helpCircle', 'Manual Book']].map(([ic, l]) => (
                      <button key={l} onClick={() => { if (l === 'Settings') setPage(12); setMenu(false); }} className="row gap-3" style={{ width: '100%', border: 'none', background: 'transparent', padding: '8px 10px', borderRadius: 6, fontSize: 14, color: 'var(--color-text-primary)' }} onMouseEnter={e => e.currentTarget.style.background = 'var(--color-surface-sunken)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}><Icon name={ic} size={16} style={{ color: 'var(--color-text-secondary)' }} />{l}</button>
                    ))}
                    <button onClick={() => setPage(2)} className="row gap-3" style={{ width: '100%', border: 'none', background: 'transparent', padding: '8px 10px', borderRadius: 6, fontSize: 14, color: 'var(--color-danger)', borderTop: '1px solid var(--color-border-subtle)', marginTop: 4 }}><Icon name="logout" size={16} />Sign out</button>
                  </div>
                </>
              )}
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="scroll-area" style={{ flex: 1, overflow: 'auto', background: 'var(--color-bg)' }}>
          <div className="page-enter" key={page} style={{ maxWidth: 1440, margin: '0 auto', padding: 'var(--space-6)' }}>{children}</div>
        </main>
      </div>
      <CommandPalette open={palette} onClose={() => setPalette(false)} setPage={setPage} />
    </div>
  );
}

Object.assign(window, { AppShell, NAV_GROUPS, activeNavFor });

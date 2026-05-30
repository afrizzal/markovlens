/* ============================================================================
   UI Primitives — Button, Badge, Card, KPICard, ChartContainer, Tabs,
   Segmented, Slider, Toggle, Select, Input, Sparkline, Tooltip, Delta
   ========================================================================== */
/* React hooks are exposed as globals in the host HTML (window.useState etc.) */

/* ---- formatting helpers ---- */
const fmtPct = (x, d = 1) => `${(x * 100).toFixed(d)}%`;
const fmtPctRaw = (x, d = 1) => `${x.toFixed(d)}%`;
const fmtNum = (x) => x.toLocaleString('en-US');
const fmtRp = (x) => {
  if (x >= 1e9) return `Rp ${(x / 1e9).toFixed(1)}B`;
  if (x >= 1e6) return `Rp ${(x / 1e6).toFixed(1)}M`;
  if (x >= 1e3) return `Rp ${(x / 1e3).toFixed(0)}K`;
  return `Rp ${x}`;
};
window.fmt = { fmtPct, fmtPctRaw, fmtNum, fmtRp };

/* ====== Button ====== */
function Button({ variant = 'secondary', size, icon, iconRight, children, className = '', ...rest }) {
  const cls = ['btn', `btn-${variant}`, size ? `btn-${size}` : '', !children ? 'btn-icon' : '', className].filter(Boolean).join(' ');
  return (
    <button className={cls} {...rest}>
      {icon && <Icon name={icon} size={size === 'sm' ? 15 : 17} />}
      {children}
      {iconRight && <Icon name={iconRight} size={size === 'sm' ? 15 : 17} />}
    </button>
  );
}

/* ====== Badge ====== */
function Badge({ variant = 'neutral', icon, children }) {
  return <span className={`badge badge-${variant}`}>{icon && <Icon name={icon} size={12} />}{children}</span>;
}

/* ====== Delta (up/down indicator) ====== */
function Delta({ value, suffix = '%', size = 12 }) {
  const up = value >= 0;
  const color = up ? 'var(--color-success)' : 'var(--color-danger)';
  return (
    <span className="row mono" style={{ gap: 2, color, fontSize: size, fontWeight: 500 }}>
      <Icon name={up ? 'arrowUp' : 'arrowDown'} size={size + 1} />
      {Math.abs(value).toFixed(1)}{suffix}
    </span>
  );
}

/* ====== Card ====== */
function Card({ raised, accent, className = '', style = {}, children, ...rest }) {
  return (
    <div className={`card ${raised ? 'card-raised' : ''} ${accent ? 'accent-card' : ''} ${className}`}
      style={{ ...(accent ? { '--accent': accent } : {}), ...style }} {...rest}>
      {children}
    </div>
  );
}

/* ====== ChartContainer (AccentCard) ====== */
function ChartContainer({ title, subtitle, accent = 'var(--color-primary)', actions, height, children, bodyStyle = {} }) {
  return (
    <Card accent={accent} className="col" style={{ overflow: 'hidden' }}>
      <div className="chart-head">
        <div className="col" style={{ gap: 2 }}>
          <div className="t-h3">{title}</div>
          {subtitle && <div className="t-xs t-ter">{subtitle}</div>}
        </div>
        {actions && <div className="row gap-2">{actions}</div>}
      </div>
      <div style={{ padding: 'var(--space-5)', height, ...bodyStyle }}>{children}</div>
    </Card>
  );
}

/* ====== Sparkline ====== */
function Sparkline({ data, width = 96, height = 28, color = 'var(--color-primary)', fill = true, strokeWidth = 1.5 }) {
  const min = Math.min(...data), max = Math.max(...data);
  const span = max - min || 1;
  const pts = data.map((v, i) => [(i / (data.length - 1)) * width, height - 2 - ((v - min) / span) * (height - 4)]);
  const line = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ');
  const area = `${line} L${width} ${height} L0 ${height} Z`;
  const id = useMemo(() => 'sp' + Math.random().toString(36).slice(2, 8), []);
  return (
    <svg width={width} height={height} style={{ display: 'block', overflow: 'visible' }}>
      {fill && (
        <>
          <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={color} stopOpacity="0.18" />
            <stop offset="1" stopColor={color} stopOpacity="0" />
          </linearGradient></defs>
          <path d={area} fill={`url(#${id})`} />
        </>
      )}
      <path d={line} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ====== KPI Card ====== */
function KPICard({ label, value, unit, delta, deltaSuffix = '%', sparkline, sparkColor, accent, tooltip, icon }) {
  return (
    <Card accent={accent} className="col" style={{ padding: 'var(--space-5)', gap: 'var(--space-3)' }}>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <span className="t-label row gap-1">
          {label}
          {tooltip && (
            <span className="tip"><Icon name="info" size={13} style={{ color: 'var(--color-text-tertiary)' }} />
              <span className="tip-body">{tooltip}</span></span>
          )}
        </span>
        {icon && <Icon name={icon} size={18} style={{ color: 'var(--color-text-tertiary)' }} />}
      </div>
      <div className="row" style={{ alignItems: 'baseline', gap: 6 }}>
        <span className="mono" style={{ fontSize: 'var(--fs-32)', fontWeight: 600, letterSpacing: '-0.02em' }}>{value}</span>
        {unit && <span className="t-sm t-ter mono">{unit}</span>}
      </div>
      <div className="row" style={{ justifyContent: 'space-between', minHeight: 28 }}>
        {delta != null ? <Delta value={delta} suffix={deltaSuffix} /> : <span className="t-xs t-ter">—</span>}
        {sparkline && <Sparkline data={sparkline} color={sparkColor || accent || 'var(--color-primary)'} />}
      </div>
    </Card>
  );
}

/* ====== Tabs ====== */
function Tabs({ tabs, value, onChange }) {
  return (
    <div className="tabs">
      {tabs.map(t => (
        <button key={t} className="tab" data-on={value === t} onClick={() => onChange(t)}>{t}</button>
      ))}
    </div>
  );
}

/* ====== Segmented control ====== */
function Segmented({ options, value, onChange }) {
  return (
    <div className="segmented">
      {options.map(o => {
        const val = typeof o === 'string' ? o : o.value;
        const lbl = typeof o === 'string' ? o : o.label;
        return <button key={val} data-on={value === val} onClick={() => onChange(val)}>{lbl}</button>;
      })}
    </div>
  );
}

/* ====== Slider w/ label + value + optional ghost baseline ====== */
function Slider({ label, value, min, max, step = 1, onChange, format = (v) => v, baseline, note, accent }) {
  const pct = ((value - min) / (max - min)) * 100;
  const basePct = baseline != null ? ((baseline - min) / (max - min)) * 100 : null;
  return (
    <div className="col" style={{ gap: 'var(--space-2)' }}>
      {label && (
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <span className="t-sm">{label}</span>
          <span className="mono t-sm" style={{ color: accent || 'var(--color-text-primary)', fontWeight: 600 }}>{format(value)}</span>
        </div>
      )}
      <div style={{ position: 'relative' }}>
        {basePct != null && (
          <span title="baseline" style={{ position: 'absolute', left: `calc(${basePct}% - 1px)`, top: -3, width: 2, height: 10,
            background: 'var(--color-text-tertiary)', borderRadius: 2, zIndex: 1, opacity: 0.7 }} />
        )}
        <input className="slider" type="range" min={min} max={max} step={step} value={value}
          onChange={e => onChange(Number(e.target.value))}
          style={{ background: `linear-gradient(90deg, ${accent || 'var(--color-primary)'} ${pct}%, var(--color-border-visible) ${pct}%)` }} />
      </div>
      {note && <span className="t-xs t-ter">{note}</span>}
    </div>
  );
}

/* ====== Toggle ====== */
function Toggle({ on, onChange }) {
  return <button className="toggle" data-on={on} onClick={() => onChange(!on)} aria-pressed={on} />;
}

/* ====== Select ====== */
function Select({ value, onChange, options, style }) {
  return (
    <div style={{ position: 'relative', ...style }}>
      <select className="select" value={value} onChange={e => onChange(e.target.value)} style={{ appearance: 'none', paddingRight: 32 }}>
        {options.map(o => {
          const val = typeof o === 'string' ? o : o.value;
          const lbl = typeof o === 'string' ? o : o.label;
          return <option key={val} value={val}>{lbl}</option>;
        })}
      </select>
      <Icon name="chevronDown" size={16} style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: 'var(--color-text-tertiary)' }} />
    </div>
  );
}

/* ====== Input ====== */
function Input({ icon, ...rest }) {
  if (!icon) return <input className="input" {...rest} />;
  return (
    <div style={{ position: 'relative' }}>
      <Icon name={icon} size={16} style={{ position: 'absolute', left: 11, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-tertiary)' }} />
      <input className="input" style={{ paddingLeft: 34 }} {...rest} />
    </div>
  );
}

/* ====== Checkbox ====== */
function Checkbox({ on, onChange, radio }) {
  return (
    <button className={`check ${radio ? 'radio' : ''}`} data-on={on} onClick={() => onChange(!on)}>
      {on && !radio && <Icon name="check" size={13} strokeWidth={2.5} />}
      {on && radio && <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#fff' }} />}
    </button>
  );
}

/* ====== Tooltip wrapper ====== */
function Tooltip({ body, children }) {
  return <span className="tip">{children}<span className="tip-body">{body}</span></span>;
}

/* ====== Empty state ====== */
function EmptyState({ icon = 'box', title, desc, action }) {
  return (
    <div className="col" style={{ alignItems: 'center', textAlign: 'center', gap: 'var(--space-3)', maxWidth: 480, margin: '0 auto', padding: 'var(--space-7) var(--space-5)' }}>
      <div className="row" style={{ width: 56, height: 56, borderRadius: 'var(--radius-md)', background: 'var(--color-surface-sunken)', justifyContent: 'center', color: 'var(--color-text-tertiary)' }}>
        <Icon name={icon} size={26} />
      </div>
      <div className="t-h3">{title}</div>
      <div className="t-sm t-sec" style={{ textWrap: 'pretty' }}>{desc}</div>
      {action}
    </div>
  );
}

Object.assign(window, {
  Button, Badge, Delta, Card, ChartContainer, Sparkline, KPICard, Tabs,
  Segmented, Slider, Toggle, Select, Input, Checkbox, Tooltip, EmptyState,
});

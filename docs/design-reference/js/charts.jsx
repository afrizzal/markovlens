/* ============================================================================
   Charts — hand-built responsive SVG. Theme-aware via CSS variables.
   StackedArea · FanChart · Heatmap · Sankey · Histogram · MiniForecast
   · AnimatedMatrix (marketing)
   ========================================================================== */

/* read a CSS var to a concrete value (for JS color math) */
function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
function hexToRgb(h) {
  h = h.replace('#', ''); if (h.length === 3) h = h.split('').map(c => c + c).join('');
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}
function lerp(a, b, t) { return a + (b - a) * t; }
function mix(c1, c2, t) {
  const a = hexToRgb(c1), b = hexToRgb(c2);
  return `rgb(${Math.round(lerp(a[0], b[0], t))},${Math.round(lerp(a[1], b[1], t))},${Math.round(lerp(a[2], b[2], t))})`;
}
function lum(rgbStr) {
  const m = rgbStr.match(/\d+/g).map(Number);
  return (0.299 * m[0] + 0.587 * m[1] + 0.114 * m[2]) / 255;
}
/* sequential ramp from 5 css seq stops */
function seqRamp(t, theme) {
  const stops = ['--chart-seq-1', '--chart-seq-2', '--chart-seq-3', '--chart-seq-4', '--chart-seq-5'].map(cssVar);
  const seg = Math.min(3.999, t * 4); const i = Math.floor(seg);
  const bg = mix(stops[i], stops[i + 1], seg - i);
  return { bg, text: lum(bg) > 0.55 ? '#0A0A0A' : '#FFFFFF' };
}

/* smooth path through points (Catmull-Rom -> bezier) */
function smoothPath(pts) {
  if (pts.length < 2) return '';
  let d = `M${pts[0][0]} ${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
    const c1x = p1[0] + (p2[0] - p0[0]) / 6, c1y = p1[1] + (p2[1] - p0[1]) / 6;
    const c2x = p2[0] - (p3[0] - p1[0]) / 6, c2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += ` C${c1x.toFixed(1)} ${c1y.toFixed(1)} ${c2x.toFixed(1)} ${c2y.toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
  }
  return d;
}

/* ====== StackedArea (brand share + forecast) ====== */
function StackedArea({ theme }) {
  const W = 780, H = 360, PL = 44, PR = 16, PT = 16, PB = 28;
  const iw = W - PL - PR, ih = H - PT - PB;
  const hist = SHARE.hist, fc = SHARE.fc;
  const all = [...hist, ...fc]; const N = all.length; // 24
  const todayIdx = hist.length - 1;
  const x = i => PL + (i / (N - 1)) * iw;
  const y = v => PT + (1 - v) * ih;
  // cumulative stacks (brand 0 bottom)
  const cum = all.map(row => { let c = 0; return row.map(v => (c += v)); });
  const bandPath = (bi, from, to) => {
    const top = [], bot = [];
    for (let i = from; i <= to; i++) { top.push([x(i), y(cum[i][bi])]); bot.push([x(i), y(bi === 0 ? 0 : cum[i][bi - 1])]); }
    return `M${top.map(p => p.join(' ')).join(' L')} L${bot.reverse().map(p => p.join(' ')).join(' L')} Z`;
  };
  const [hover, setHover] = useState(null);
  return (
    <div style={{ position: 'relative' }}>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}
        onMouseMove={e => { const r = e.currentTarget.getBoundingClientRect(); const px = (e.clientX - r.left) / r.width * W; const i = Math.round((px - PL) / iw * (N - 1)); if (i >= 0 && i < N) setHover(i); }}
        onMouseLeave={() => setHover(null)}>
        {[0, 0.25, 0.5, 0.75, 1].map(g => (
          <g key={g}>
            <line x1={PL} x2={W - PR} y1={y(g)} y2={y(g)} stroke="var(--color-border-subtle)" strokeWidth="1" />
            <text x={PL - 8} y={y(g) + 4} textAnchor="end" fontSize="11" fill="var(--color-text-tertiary)" className="mono">{Math.round(g * 100)}%</text>
          </g>
        ))}
        {/* forecast region tint */}
        <rect x={x(todayIdx)} y={PT} width={x(N - 1) - x(todayIdx)} height={ih} fill="var(--color-text-primary)" opacity="0.03" />
        {BRANDS.map((b, bi) => (
          <g key={bi}>
            <path d={bandPath(bi, 0, todayIdx)} fill={b.color} opacity="0.92" />
            <path d={bandPath(bi, todayIdx, N - 1)} fill={b.color} opacity="0.4" />
          </g>
        ))}
        {/* dashed forecast separators (top of each band) */}
        {BRANDS.map((b, bi) => {
          const pts = []; for (let i = todayIdx; i < N; i++) pts.push([x(i), y(cum[i][bi])]);
          return <polyline key={bi} points={pts.map(p => p.join(',')).join(' ')} fill="none" stroke={b.color} strokeWidth="1.5" strokeDasharray="4 3" opacity="0.9" />;
        })}
        <line x1={x(todayIdx)} x2={x(todayIdx)} y1={PT} y2={PT + ih} stroke="var(--color-text-secondary)" strokeWidth="1" strokeDasharray="3 3" />
        <text x={x(todayIdx)} y={PT - 4} textAnchor="middle" fontSize="10" fill="var(--color-text-secondary)" className="mono" style={{ textTransform: 'uppercase', letterSpacing: '0.06em' }}>today</text>
        {hover != null && <line x1={x(hover)} x2={x(hover)} y1={PT} y2={PT + ih} stroke="var(--color-text-primary)" strokeWidth="1" opacity="0.25" />}
        {[0, 6, 11, 17, 23].map(i => <text key={i} x={x(i)} y={H - 8} textAnchor="middle" fontSize="10" fill="var(--color-text-tertiary)" className="mono">{i <= todayIdx ? `M${i + 1}` : `+${i - todayIdx}`}</text>)}
      </svg>
      {hover != null && (
        <div style={{ position: 'absolute', top: 8, left: `${(x(hover) / W) * 100}%`, transform: 'translateX(-50%)', pointerEvents: 'none', background: 'var(--color-surface)', border: '1px solid var(--color-border-visible)', borderRadius: 'var(--radius-sm)', boxShadow: 'var(--shadow-floating)', padding: '8px 10px', minWidth: 150 }}>
          <div className="t-xs t-ter mono" style={{ marginBottom: 4 }}>{hover <= todayIdx ? `Month ${hover + 1} · actual` : `+${hover - todayIdx} · forecast`}</div>
          {BRANDS.map((b, bi) => (
            <div key={bi} className="row" style={{ justifyContent: 'space-between', gap: 12, fontSize: 12 }}>
              <span className="row gap-2"><span style={{ width: 8, height: 8, borderRadius: 2, background: b.color }} />{b.name}</span>
              <span className="mono" style={{ fontWeight: 600 }}>{(all[hover][bi] * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ====== Legend ====== */
function Legend({ items, style }) {
  return (
    <div className="row wrap gap-4" style={style}>
      {items.map((it, i) => (
        <span key={i} className="row gap-2 t-xs t-sec"><span style={{ width: 10, height: 10, borderRadius: 3, background: it.color }} />{it.name}</span>
      ))}
    </div>
  );
}

/* ====== FanChart (Monte Carlo) ====== */
function FanChart({ showPaths = true }) {
  const W = 780, H = 360, PL = 44, PR = 16, PT = 16, PB = 28;
  const iw = W - PL - PR, ih = H - PT - PB;
  const { p10, p50, p90, paths } = FAN;
  const allV = [...p10, ...p90]; const lo = Math.min(...allV) - 0.01, hi = Math.max(...allV) + 0.01;
  const N = p50.length;
  const x = i => PL + (i / (N - 1)) * iw;
  const y = v => PT + (1 - (v - lo) / (hi - lo)) * ih;
  const todayIdx = 0;
  const band = (a, b) => {
    const top = a.map((v, i) => [x(i), y(v)]); const bot = b.map((v, i) => [x(i), y(v)]).reverse();
    return `M${top.map(p => p.join(' ')).join(' L')} L${bot.map(p => p.join(' ')).join(' L')} Z`;
  };
  const inner = p50.map((m, i) => (m + p90[i]) / 2);
  const innerLo = p50.map((m, i) => (m + p10[i]) / 2);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
      {[0, 0.25, 0.5, 0.75, 1].map(g => { const v = lo + g * (hi - lo); return (
        <g key={g}><line x1={PL} x2={W - PR} y1={y(v)} y2={y(v)} stroke="var(--color-border-subtle)" />
          <text x={PL - 8} y={y(v) + 4} textAnchor="end" fontSize="11" fill="var(--color-text-tertiary)" className="mono">{(v * 100).toFixed(0)}%</text></g>); })}
      <path d={band(p90, p10)} fill="var(--chart-1)" opacity="0.13" />
      <path d={band(inner, innerLo)} fill="var(--chart-1)" opacity="0.16" />
      {showPaths && paths.map((p, k) => (
        <path key={k} d={smoothPath(p.map((v, i) => [x(i), y(v)]))} fill="none" stroke="var(--chart-1)" strokeWidth="1" opacity="0.32" />
      ))}
      <path d={smoothPath(p50.map((v, i) => [x(i), y(v)]))} fill="none" stroke="var(--chart-1)" strokeWidth="2.5" />
      <line x1={x(todayIdx)} x2={x(todayIdx)} y1={PT} y2={PT + ih} stroke="var(--color-text-secondary)" strokeDasharray="3 3" />
      <text x={x(todayIdx) + 4} y={PT + 12} fontSize="10" fill="var(--color-text-secondary)" className="mono">today</text>
      {[2, 4, 6, 8, 10, 12].map(i => <text key={i} x={x(i)} y={H - 8} textAnchor="middle" fontSize="10" fill="var(--color-text-tertiary)" className="mono">+{i}</text>)}
      {[['P90', p90], ['P50', p50], ['P10', p10]].map(([lab, arr], k) => (
        <text key={lab} x={x(N - 1) - 2} y={y(arr[N - 1]) + (k === 1 ? -6 : 12)} textAnchor="end" fontSize="10" fill="var(--chart-1)" className="mono" fontWeight="600">{lab}</text>
      ))}
    </svg>
  );
}

/* ====== Heatmap (transition matrix) ====== */
function Heatmap({ theme, onCell, selected, hideSparse, diagOnly }) {
  const { M, OBS } = MATRIX; const n = M.length;
  const labels = BRANDS.map(b => b.name);
  const [hover, setHover] = useState(null);
  return (
    <div style={{ position: 'relative' }}>
      <div style={{ display: 'grid', gridTemplateColumns: `90px repeat(${n}, 1fr)`, gap: 3 }}>
        <div />
        {labels.map((l, j) => <div key={j} className="t-xs t-ter" style={{ textAlign: 'center', paddingBottom: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{l}</div>)}
        {M.map((row, i) => (
          <React.Fragment key={i}>
            <div className="t-xs t-sec" style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', paddingRight: 8, fontWeight: 500 }}>{labels[i]}</div>
            {row.map((p, j) => {
              const sparse = OBS[i][j] < 20;
              const dim = (diagOnly && i !== j) || (hideSparse && sparse);
              const { bg, text } = seqRamp(Math.min(1, p / 0.8), theme);
              const sel = selected && selected[0] === i && selected[1] === j;
              return (
                <button key={j} onClick={() => onCell && onCell([i, j])}
                  onMouseEnter={() => setHover([i, j])} onMouseLeave={() => setHover(null)}
                  style={{ position: 'relative', aspectRatio: '1.6 / 1', minHeight: 44, border: sel ? '2px solid var(--color-primary)' : (i === j ? '1.5px solid var(--color-border-visible)' : 'none'),
                    borderRadius: 6, background: dim ? 'var(--color-surface-sunken)' : bg, color: dim ? 'var(--color-text-tertiary)' : text,
                    cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, opacity: dim ? 0.4 : 1, transition: 'transform 120ms var(--ease)', transform: (hover && hover[0] === i && hover[1] === j) ? 'scale(1.04)' : 'none' }}>
                  {(p * 100).toFixed(p < 0.1 ? 1 : 0)}
                  {sparse && !dim && <Icon name="alertTriangle" size={11} style={{ position: 'absolute', top: 2, right: 2, color: 'var(--color-warning)' }} />}
                </button>
              );
            })}
          </React.Fragment>
        ))}
      </div>
      {hover && (
        <div style={{ position: 'absolute', bottom: 6, left: '50%', transform: 'translateX(-50%)', pointerEvents: 'none', background: 'var(--color-text-primary)', color: 'var(--color-bg)', borderRadius: 6, padding: '6px 10px', fontSize: 12, boxShadow: 'var(--shadow-floating)', whiteSpace: 'nowrap' }}>
          <span className="mono">{labels[hover[0]]} → {labels[hover[1]]}: {(M[hover[0]][hover[1]] * 100).toFixed(1)}%</span>
          <span className="mono" style={{ opacity: 0.7 }}> · {fmt.fmtNum(OBS[hover[0]][hover[1]])} obs</span>
        </div>
      )}
    </div>
  );
}

/* ====== Sankey (churn flow over periods) ====== */
function Sankey({ periods = 7, highlight }) {
  const W = 820, H = 380, PT = 10, PB = 10;
  const cols = periods; const colW = 13; const ih = H - PT - PB;
  const gap = 7; // px between nodes
  const x = c => 8 + (c / (cols - 1)) * (W - 16 - colW);
  const states = CHURN_STATES; const ns = states.length;
  // layout nodes per column
  const layout = [];
  for (let c = 0; c < cols; c++) {
    const d = CHURN.dist[c]; const active = d.map((v, i) => ({ i, v })).filter(o => o.v > 0.002);
    const totalGap = gap * (active.length - 1);
    let yy = PT; const nodes = {};
    active.forEach(o => { const h = o.v * (ih - totalGap); nodes[o.i] = { y0: yy, y1: yy + h, v: o.v }; yy += h + gap; });
    layout.push(nodes);
  }
  // edges
  const edges = [];
  const cohortSize = 24000;
  for (let c = 0; c < cols - 1; c++) {
    const d = CHURN.dist[c];
    const srcOff = {}, tgtOff = {};
    for (let i = 0; i < ns; i++) {
      if (!layout[c][i]) continue;
      for (let j = 0; j < ns; j++) {
        const flow = d[i] * CHURN.P[i][j];
        if (flow < 0.0015 || !layout[c + 1][j]) continue;
        const sH = (layout[c][i].y1 - layout[c][i].y0); const tH = (layout[c + 1][j].y1 - layout[c + 1][j].y0);
        const sScale = sH / (d[i] || 1); const tScale = tH / (CHURN.dist[c + 1][j] || 1);
        const sy0 = layout[c][i].y0 + (srcOff[i] || 0); const sy1 = sy0 + flow * sScale;
        const ty0 = layout[c + 1][j].y0 + (tgtOff[j] || 0); const ty1 = ty0 + flow * tScale;
        srcOff[i] = (srcOff[i] || 0) + flow * sScale; tgtOff[j] = (tgtOff[j] || 0) + flow * tScale;
        edges.push({ c, i, j, flow, sy0, sy1, ty0, ty1, count: Math.round(flow * cohortSize) });
      }
    }
  }
  const [hover, setHover] = useState(null);
  const xr = c => x(c) + colW; const xl = c => x(c);
  return (
    <div style={{ position: 'relative' }}>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }} onMouseLeave={() => setHover(null)}>
        {edges.map((e, k) => {
          const x1 = xr(e.c), x2 = xl(e.c + 1); const mx = (x1 + x2) / 2;
          const d = `M${x1} ${e.sy0} C${mx} ${e.sy0} ${mx} ${e.ty0} ${x2} ${e.ty0} L${x2} ${e.ty1} C${mx} ${e.ty1} ${mx} ${e.sy1} ${x1} ${e.sy1} Z`;
          const hl = highlight != null ? e.c === highlight : true;
          const isHover = hover === k;
          return <path key={k} d={d} fill={states[e.i].color} opacity={isHover ? 0.55 : (hl ? 0.24 : 0.07)} onMouseEnter={() => setHover(k)} style={{ transition: 'opacity 120ms' }} />;
        })}
        {layout.map((nodes, c) => Object.entries(nodes).map(([i, nd]) => (
          <g key={c + '-' + i}>
            <rect x={x(c)} y={nd.y0} width={colW} height={Math.max(2, nd.y1 - nd.y0)} rx="3" fill={states[i].color} opacity={highlight == null || highlight === c || highlight === c - 1 ? 1 : 0.5} />
          </g>
        )))}
        {Array.from({ length: cols }).map((_, c) => (
          <text key={c} x={x(c) + colW / 2} y={H - 0} textAnchor="middle" fontSize="9.5" fill="var(--color-text-tertiary)" className="mono">P{c}</text>
        ))}
      </svg>
      {hover != null && edges[hover] && (
        <div style={{ position: 'absolute', top: 4, left: '50%', transform: 'translateX(-50%)', background: 'var(--color-text-primary)', color: 'var(--color-bg)', borderRadius: 6, padding: '6px 10px', fontSize: 12, boxShadow: 'var(--shadow-floating)', pointerEvents: 'none', whiteSpace: 'nowrap' }} className="mono">
          {fmt.fmtNum(edges[hover].count)} customers · {states[edges[hover].i].label} → {states[edges[hover].j].label} · P{edges[hover].c}→P{edges[hover].c + 1}
        </div>
      )}
    </div>
  );
}

/* ====== Histogram ====== */
function Histogram({ data, color = 'var(--chart-1)' }) {
  const max = Math.max(...data.map(d => d.v));
  return (
    <div className="col gap-2">
      {data.map((d, i) => (
        <div key={i} className="row gap-3" style={{ alignItems: 'center' }}>
          <span className="t-xs t-ter mono" style={{ width: 52, textAlign: 'right' }}>{d.label}</span>
          <div style={{ flex: 1, height: 18, background: 'var(--color-surface-sunken)', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{ width: `${(d.v / max) * 100}%`, height: '100%', background: color, borderRadius: 4, transition: 'width 400ms var(--ease)' }} />
          </div>
          <span className="t-xs mono" style={{ width: 34, textAlign: 'right', fontWeight: 600 }}>{(d.v * 100).toFixed(0)}%</span>
        </div>
      ))}
    </div>
  );
}

/* ====== MiniForecast (model cards) ====== */
function MiniForecast({ data, color = 'var(--chart-1)', height = 80 }) {
  const W = 240, H = height; const min = Math.min(...data), max = Math.max(...data); const span = max - min || 1;
  const pts = data.map((v, i) => [(i / (data.length - 1)) * W, H - 6 - ((v - min) / span) * (H - 12)]);
  const split = Math.floor(data.length * 0.6);
  const id = useMemo(() => 'mf' + Math.random().toString(36).slice(2, 7), []);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height, display: 'block' }}>
      <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={color} stopOpacity="0.16" /><stop offset="1" stopColor={color} stopOpacity="0" /></linearGradient></defs>
      <path d={`${smoothPath(pts)} L${W} ${H} L0 ${H} Z`} fill={`url(#${id})`} />
      <path d={smoothPath(pts.slice(0, split + 1))} fill="none" stroke={color} strokeWidth="2" />
      <path d={smoothPath(pts.slice(split))} fill="none" stroke={color} strokeWidth="2" strokeDasharray="4 3" opacity="0.7" />
    </svg>
  );
}

/* ====== AnimatedMatrix (marketing hero / login) ====== */
function AnimatedMatrix({ n = 5, cell = 46, gap = 6 }) {
  const [tick, setTick] = useState(0);
  useEffect(() => { const id = setInterval(() => setTick(t => t + 1), 1400); return () => clearInterval(id); }, []);
  const vals = useMemo(() => Array.from({ length: n * n }, (_, k) => {
    const i = Math.floor(k / n), j = k % n;
    const base = i === j ? 0.75 : 0.12;
    return Math.max(0.02, Math.min(0.95, base + Math.sin(tick * 0.9 + i * 1.7 + j * 0.6) * 0.18));
  }), [tick, n]);
  return (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${n}, ${cell}px)`, gap }}>
      {vals.map((v, k) => {
        const { bg, text } = seqRamp(v, 'x');
        return <div key={k} style={{ width: cell, height: cell, borderRadius: 8, background: bg, color: text, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, transition: 'background 1200ms var(--ease), color 1200ms var(--ease)' }}>{v.toFixed(2).slice(1)}</div>;
      })}
    </div>
  );
}

Object.assign(window, { StackedArea, FanChart, Heatmap, Sankey, Histogram, MiniForecast, AnimatedMatrix, Legend, seqRamp, smoothPath });

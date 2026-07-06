import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { listGraphs, listReleases, getGraph, iccChart, releaseIccChart } from './api.js'

const H = 1600        // chart height (px, scroll)
const COLW = 132
const AXIS = 64
const HEADER = 22

// Prefer official ICS color (band.color); if absent, fall back to slug hash (lightness varies by rank).
const hue = (s) => { let h = 7; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360; return h }
// rank_n: 1 Eon · 2 Era · 3 Period · 4 Subperiod · 5 Epoch · 6 Age (fallback unused when color exists)
const bandColor = (b, rank) => b.color || `hsl(${hue(b.slug)} 48% ${[60, 60, 70, 74, 78, 82][rank - 1] || 80}%)`

// Set label to black/white depending on background brightness.
const textOn = (hex) => {
  if (!hex || hex[0] !== '#' || hex.length < 7) return '#23202a'
  const r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16)
  return (0.299 * r + 0.587 * g + 0.114 * b) > 150 ? '#23202a' : '#fff'
}

// Render outputs as nested Eon/Era/Period(/Epoch/Age) columns (ICC style). oldest=bottom, most recent=top.
export default function IccChart() {
  const [source, setSource] = useState('release')     // 'release' (published bake) | 'graph' (live merge output)
  const [graphs, setGraphs] = useState([])
  const [releases, setReleases] = useState([])
  const [graphId, setGraphId] = useState(null)
  const [releaseId, setReleaseId] = useState(null)
  const [mergeNodes, setMergeNodes] = useState([])    // group==null merge nodes (terminal + column merges)
  const [nodeKey, setNodeKey] = useState(null)        // which merge's geometry to view
  const [data, setData] = useState(null)
  const [scale, setScale] = useState('log')           // 'log' (zoom recent) | 'linear' (proportional)
  const [showUnc, setShowUnc] = useState(false)        // uncertainty (±pm) band overlay
  const [zoom, setZoom] = useState(1)                  // chart zoom (viewBox scale); scroll = pan
  const [status, setStatus] = useState('Loading…')
  const [error, setError] = useState(null)
  const scrollRef = useRef(null)
  const pendingScroll = useRef(null)                   // scroll to apply after a zoom re-render (keep cursor point fixed)

  async function loadGraph(id, node) {
    setError(null); setStatus('Loading…')
    try {
      const d = await iccChart(id, node)
      setData(d)
      setStatus(`${d.graph}${d.node ? ` · ${d.node}` : ''} · max ${d.max_ma} Ma`)
    } catch (e) { setError(e.data || String(e)); setStatus('Failed') }
  }

  // Enter graph mode: fetch its merge nodes (terminal + column merges), view the terminal by default.
  async function selectGraphSource(id) {
    setSource('graph')
    const g = await getGraph(id).catch(() => null)
    const ms = (g?.nodes || []).filter((n) => n.node_type === 'merge' && !n.group)
    const ordered = [...ms.filter((n) => n.key === 'icc-chart'), ...ms.filter((n) => n.key !== 'icc-chart')]
    setMergeNodes(ordered)
    const k = ordered[0]?.key || null
    setNodeKey(k)
    loadGraph(id, k)
  }
  const nodeLabel = (n) => n.key === 'icc-chart' ? 'Full chart (all columns)' : (n.label?.split('\n')[0] || n.key)
  async function loadRelease(id) {
    setError(null); setStatus('Loading…')
    try { const d = await releaseIccChart(id); setData(d); setStatus(`${d.release} · max ${d.max_ma} Ma`) }
    catch (e) { setError(e.data || String(e)); setStatus('Failed') }
  }

  useEffect(() => {
    (async () => {
      try {
        const [gs, rs] = await Promise.all([listGraphs(), listReleases()])
        setGraphs(gs); setReleases(rs)
        const gp = gs.find((g) => g.slug === 'example-icc-partial') || gs[0]
        const rp = rs.find((r) => r.version === 'ICS-2024/12') || rs[0]
        if (gp) setGraphId(gp.id)
        if (rp) { setReleaseId(rp.id); loadRelease(rp.id) } else if (gp) { selectGraphSource(gp.id) }
      } catch (e) { setError(e.data || String(e)); setStatus('Failed') }
    })()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const max = data?.max_ma || 1
  const y = useMemo(() => {
    if (scale === 'log') { const lm = Math.log10(max + 1); return (age) => (Math.log10(age + 1) / lm) * H }
    return (age) => (age / max) * H
  }, [scale, max])

  const ticks = scale === 'log' ? [0, 50, 200, 540, 1000, 2500, max] : [0, 1000, 2000, 3000, 4000, max]
  const nCol = data?.levels.length || 0

  // Symmetric error (±pm) per boundary. A boundary is shared by multiple ranks → dedup by base.
  const uncBoundaries = useMemo(() => {
    if (!data) return []
    const m = new Map()
    data.levels.forEach((lv) => lv.bands.forEach((b) => {
      if (b.pm > 0 && !m.has(b.bottom)) m.set(b.bottom, { age: b.bottom, pm: b.pm, name: b.name })
    }))
    return [...m.values()]
  }, [data])

  // --- zoom (viewBox scale) + pan (scroll) ---
  const W = AXIS + nCol * COLW + 8
  const Hh = H + HEADER + 10
  const clampZoom = (z) => Math.min(6, Math.max(0.15, z))
  // Zoom keeping the (clientX,clientY) point fixed on screen by adjusting scroll after re-render.
  function zoomAt(clientX, clientY, factor) {
    const el = scrollRef.current
    const nz = clampZoom(zoom * factor)
    if (el) {
      const rect = el.getBoundingClientRect()
      const ox = clientX - rect.left, oy = clientY - rect.top
      const px = el.scrollLeft + ox, py = el.scrollTop + oy
      pendingScroll.current = { left: px * (nz / zoom) - ox, top: py * (nz / zoom) - oy }
    }
    setZoom(nz)
  }
  function zoomCenter(factor) {
    const el = scrollRef.current
    if (!el) { setZoom((z) => clampZoom(z * factor)); return }
    const rect = el.getBoundingClientRect()
    zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, factor)
  }
  function onWheelZoom(e) {
    if (!(e.ctrlKey || e.metaKey)) return   // plain wheel = scroll/pan; ctrl/⌘+wheel = zoom
    e.preventDefault()
    zoomAt(e.clientX, e.clientY, e.deltaY < 0 ? 1.15 : 1 / 1.15)
  }
  function fitHeight() {
    const el = scrollRef.current
    if (!el) return
    pendingScroll.current = { left: 0, top: 0 }
    setZoom(clampZoom((el.clientHeight - 12) / Hh))
  }
  useLayoutEffect(() => {
    if (pendingScroll.current && scrollRef.current) {
      scrollRef.current.scrollLeft = pendingScroll.current.left
      scrollRef.current.scrollTop = pendingScroll.current.top
      pendingScroll.current = null
    }
  }, [zoom])

  return (
    <div className="iccchart">
      <div className="iccchart-controls">
        <div className="scale-toggle">
          <button className={source === 'release' ? 'active' : ''}
                  onClick={() => { setSource('release'); if (releaseId) loadRelease(releaseId) }}>Published ICC</button>
          <button className={source === 'graph' ? 'active' : ''}
                  onClick={() => { if (graphId) selectGraphSource(graphId) }}>Graph (merge)</button>
        </div>
        {source === 'release' ? (
          <label>Release
            <select value={releaseId || ''} onChange={(e) => { const id = Number(e.target.value); setReleaseId(id); loadRelease(id) }}>
              {releases.map((r) => <option key={r.id} value={r.id}>{r.version}</option>)}
            </select>
          </label>
        ) : (
          <>
            <label>Graph
              <select value={graphId || ''} onChange={(e) => { const id = Number(e.target.value); setGraphId(id); selectGraphSource(id) }}>
                {graphs.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
              </select>
            </label>
            {mergeNodes.length > 0 && (
              <label>Merge
                <select value={nodeKey || ''} onChange={(e) => { const k = e.target.value; setNodeKey(k); loadGraph(graphId, k) }}>
                  {mergeNodes.map((n) => <option key={n.key} value={n.key}>{nodeLabel(n)}</option>)}
                </select>
              </label>
            )}
          </>
        )}
        <div className="scale-toggle">
          <button className={scale === 'log' ? 'active' : ''} onClick={() => setScale('log')}>Log (zoom recent)</button>
          <button className={scale === 'linear' ? 'active' : ''} onClick={() => setScale('linear')}>Linear (proportional)</button>
        </div>
        <button className={`unc-toggle${showUnc ? ' active' : ''}`} onClick={() => setShowUnc((v) => !v)}
                title="Symmetric error (±) band on boundary ages. GSSA agreed values have no error.">± Uncertainty</button>
        <div className="scale-toggle zoom-ctrl" title="Ctrl/⌘ + wheel to zoom toward the cursor; scroll to pan">
          <button onClick={() => zoomCenter(1 / 1.25)}>−</button>
          <button onClick={() => { pendingScroll.current = null; setZoom(1) }}>{Math.round(zoom * 100)}%</button>
          <button onClick={() => zoomCenter(1.25)}>+</button>
          <button onClick={fitHeight}>Fit</button>
        </div>
        <span className="iccchart-status">{status}</span>
      </div>

      {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}

      {data && (
        <div className="iccchart-scroll" ref={scrollRef} onWheel={onWheelZoom}>
          <svg width={W * zoom} height={Hh * zoom} viewBox={`0 0 ${W} ${Hh}`}>
            <g transform={`translate(0,${HEADER})`}>
              {ticks.map((t) => (
                <g key={t}>
                  <line x1={AXIS} x2={AXIS + nCol * COLW} y1={y(t)} y2={y(t)} stroke="#e9e9f0" />
                  <text x={AXIS - 6} y={y(t) + 3} textAnchor="end" className="icc-axis">{t}</text>
                </g>
              ))}
              {data.levels.map((lv, ci) => (
                <text key={lv.rank} x={AXIS + ci * COLW + COLW / 2} y={-7} textAnchor="middle" className="icc-colhdr">
                  {lv.rank}
                </text>
              ))}
              {data.levels.map((lv, ci) => lv.bands.map((b) => {
                const yt = y(b.top), h = Math.max(y(b.bottom) - yt, 0)
                return (
                  <g key={lv.rank + b.slug}>
                    <rect x={AXIS + ci * COLW + 1} y={yt} width={COLW - 2} height={h}
                          fill={bandColor(b, lv.rank_n)} stroke="#fff" strokeWidth="0.6">
                      <title>{`${b.name} · ${b.top}–${b.bottom} Ma${b.pm > 0 ? ` · lower boundary ± ${b.pm} Ma` : b.pm === 0 ? ' · agreed value' : ''}`}</title>
                    </rect>
                    {h > 13 && (
                      <text x={AXIS + ci * COLW + COLW / 2} y={yt + h / 2 + 3} textAnchor="middle"
                            className="icc-band" fill={textOn(b.color)}>
                        {b.name}
                      </text>
                    )}
                  </g>
                )
              }))}
              {showUnc && uncBoundaries.map((u) => {
                const ya = y(u.age - u.pm), yb = y(u.age + u.pm)
                const top = Math.min(ya, yb), hgt = Math.max(Math.abs(yb - ya), 2)
                return (
                  <rect key={`unc-${u.age}`} className="icc-unc" x={AXIS} width={nCol * COLW} y={top} height={hgt}>
                    <title>{`${u.name} lower boundary: ${u.age} ± ${u.pm} Ma`}</title>
                  </rect>
                )
              })}
            </g>
          </svg>
        </div>
      )}
      <p className="iccchart-note">
        Nested columns (ICC style) tiling base ages per rank. oldest=bottom · most recent=top. Ma scale on the left.
        <b> Published ICC</b> (ICS-2024/12) reads a baked release. <b>Graph (merge)</b> is the live output of the graph's
        terminal merge node (evaluate → tile); pick a <b>Merge</b> to view a single column merge's partial chart.
        When labels overlap on log scale, hover a band (age-range tooltip).
        <b> Zoom</b>: Ctrl/⌘ + mouse wheel zooms toward the cursor (or use −/+/Fit); scroll to pan.
        <b> ± Uncertainty</b> toggle shows the symmetric error band of each lower boundary (GSSP derived-age error) — GSSA agreed values have no error.
      </p>
    </div>
  )
}

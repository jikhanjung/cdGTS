import { useEffect, useMemo, useState } from 'react'
import { listGraphs, listReleases, iccChart, releaseIccChart } from './api.js'

const H = 1600        // 차트 높이(px, 스크롤)
const COLW = 132
const AXIS = 64
const HEADER = 22

// 공식 ICS 색(band.color) 우선, 없으면 slug 해시 폴백(rank 로 명도 차등).
const hue = (s) => { let h = 7; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360; return h }
const bandColor = (b, rank) => b.color || `hsl(${hue(b.slug)} 48% ${[60, 60, 70, 76, 82][rank - 1] || 78}%)`

// 배경색 밝기에 따라 라벨을 검/흰으로.
const textOn = (hex) => {
  if (!hex || hex[0] !== '#' || hex.length < 7) return '#23202a'
  const r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16)
  return (0.299 * r + 0.587 * g + 0.114 * b) > 150 ? '#23202a' : '#fff'
}

// 산출물을 Eon/Era/Period(/Epoch/Age) 중첩 컬럼(ICC식)으로. 오래된=아래, 최근=위.
export default function IccChart() {
  const [source, setSource] = useState('release')     // 'release'(공표, 5컬럼) | 'graph'(bake, 3컬럼)
  const [graphs, setGraphs] = useState([])
  const [releases, setReleases] = useState([])
  const [graphId, setGraphId] = useState(null)
  const [releaseId, setReleaseId] = useState(null)
  const [data, setData] = useState(null)
  const [scale, setScale] = useState('log')           // 'log'(최근 확대) | 'linear'(비례)
  const [status, setStatus] = useState('로딩 중…')
  const [error, setError] = useState(null)

  async function loadGraph(id) {
    setError(null); setStatus('불러오는 중…')
    try { const d = await iccChart(id); setData(d); setStatus(`${d.graph} · 최고 ${d.max_ma} Ma`) }
    catch (e) { setError(e.data || String(e)); setStatus('실패') }
  }
  async function loadRelease(id) {
    setError(null); setStatus('불러오는 중…')
    try { const d = await releaseIccChart(id); setData(d); setStatus(`${d.release} · 최고 ${d.max_ma} Ma`) }
    catch (e) { setError(e.data || String(e)); setStatus('실패') }
  }

  useEffect(() => {
    (async () => {
      try {
        const [gs, rs] = await Promise.all([listGraphs(), listReleases()])
        setGraphs(gs); setReleases(rs)
        const gp = gs.find((g) => g.slug === 'example-icc-partial') || gs[0]
        const rp = rs.find((r) => r.version === 'ICS-2024/12') || rs[0]
        if (gp) setGraphId(gp.id)
        if (rp) { setReleaseId(rp.id); loadRelease(rp.id) } else if (gp) { setSource('graph'); loadGraph(gp.id) }
      } catch (e) { setError(e.data || String(e)); setStatus('실패') }
    })()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const max = data?.max_ma || 1
  const y = useMemo(() => {
    if (scale === 'log') { const lm = Math.log10(max + 1); return (age) => (Math.log10(age + 1) / lm) * H }
    return (age) => (age / max) * H
  }, [scale, max])

  const ticks = scale === 'log' ? [0, 50, 200, 540, 1000, 2500, max] : [0, 1000, 2000, 3000, 4000, max]
  const nCol = data?.levels.length || 0

  return (
    <div className="iccchart">
      <div className="iccchart-controls">
        <div className="scale-toggle">
          <button className={source === 'release' ? 'active' : ''}
                  onClick={() => { setSource('release'); if (releaseId) loadRelease(releaseId) }}>공표 ICC</button>
          <button className={source === 'graph' ? 'active' : ''}
                  onClick={() => { setSource('graph'); if (graphId) loadGraph(graphId) }}>그래프 bake</button>
        </div>
        {source === 'release' ? (
          <label>릴리스
            <select value={releaseId || ''} onChange={(e) => { const id = Number(e.target.value); setReleaseId(id); loadRelease(id) }}>
              {releases.map((r) => <option key={r.id} value={r.id}>{r.version}</option>)}
            </select>
          </label>
        ) : (
          <label>그래프
            <select value={graphId || ''} onChange={(e) => { const id = Number(e.target.value); setGraphId(id); loadGraph(id) }}>
              {graphs.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
            </select>
          </label>
        )}
        <div className="scale-toggle">
          <button className={scale === 'log' ? 'active' : ''} onClick={() => setScale('log')}>로그 (최근 확대)</button>
          <button className={scale === 'linear' ? 'active' : ''} onClick={() => setScale('linear')}>선형 (비례)</button>
        </div>
        <span className="iccchart-status">{status}</span>
      </div>

      {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}

      {data && (
        <div className="iccchart-scroll">
          <svg width={AXIS + nCol * COLW + 8} height={H + HEADER + 10}>
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
                      <title>{`${b.name} · ${b.top}–${b.bottom} Ma`}</title>
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
            </g>
          </svg>
        </div>
      )}
      <p className="iccchart-note">
        rank 별로 base 연대를 타일링한 중첩 컬럼(ICC식). 오래된=아래 · 최근=위. Ma 눈금은 좌측.
        <b> 공표 ICC</b>(ICS-2024/12)는 Age 까지 5 컬럼, <b>그래프 bake</b>는 네트웍(period+) 3 컬럼.
        로그 스케일에서 라벨이 겹치면 밴드에 hover(연대범위 툴팁).
      </p>
    </div>
  )
}

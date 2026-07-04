import { useEffect, useMemo, useState } from 'react'
import { listGraphs, iccChart } from './api.js'

const H = 1600        // 차트 높이(px, 스크롤)
const COLW = 152
const AXIS = 64
const HEADER = 22

// 공식 ICS 색(band.color) 우선, 없으면 slug 해시 폴백(rank 로 명도 차등).
const hue = (s) => { let h = 7; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360; return h }
const bandColor = (b, rank) => b.color || `hsl(${hue(b.slug)} 48% ${rank === 1 ? 60 : rank === 2 ? 70 : 80}%)`

// 배경색 밝기에 따라 라벨을 검/흰으로.
const textOn = (hex) => {
  if (!hex || hex[0] !== '#' || hex.length < 7) return '#23202a'
  const r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16)
  return (0.299 * r + 0.587 * g + 0.114 * b) > 150 ? '#23202a' : '#fff'
}

// 그래프 산출물을 Eon/Era/Period 중첩 컬럼(ICC식)으로. 오래된=아래, 최근=위.
export default function IccChart() {
  const [graphs, setGraphs] = useState([])
  const [graphId, setGraphId] = useState(null)
  const [data, setData] = useState(null)
  const [scale, setScale] = useState('log')      // 'log'(최근 확대) | 'linear'(비례)
  const [status, setStatus] = useState('로딩 중…')
  const [error, setError] = useState(null)

  async function load(id) {
    setError(null); setStatus('불러오는 중…')
    try { const d = await iccChart(id); setData(d); setStatus(`${d.graph} · 최고 ${d.max_ma} Ma`) }
    catch (e) { setError(e.data || String(e)); setStatus('실패') }
  }

  useEffect(() => {
    (async () => {
      try {
        const gs = await listGraphs(); setGraphs(gs)
        const pref = gs.find((g) => g.slug === 'example-icc-partial') || gs[0]
        if (pref) { setGraphId(pref.id); load(pref.id) } else setStatus('그래프 없음')
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
        <label>그래프
          <select value={graphId || ''} onChange={(e) => { const id = Number(e.target.value); setGraphId(id); load(id) }}>
            {graphs.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
          </select>
        </label>
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
        Precambrian 은 Period 가 없어 그 컬럼이 비는데(Ediacaran 제외) 실제 ICC 와 같음.
      </p>
    </div>
  )
}

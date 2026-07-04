import { useEffect, useState } from 'react'
import { listGraphs, bakeGraph } from './api.js'
import { summarizeDist } from './ResultsPanel.jsx'

const fmt = (x) => (x == null ? '—' : `${Number(x.toPrecision(7))}`)

// distribution → 불확실성 표시 텍스트 (fidelity 별).
function uncertaintyText(dist) {
  const s = summarizeDist(dist)
  if (!s) return '—'
  if (s.kind === 'exact') return '오차 없음'
  if (s.lo != null && s.hi != null) return `95% HPD [${fmt(s.lo)}, ${fmt(s.hi)}]`
  if (s.pm != null) return `± ${fmt(s.pm)}${s.sigma ? ` (${s.sigma}σ)` : ''}`
  return '—'
}

// 그래프를 bake 해 게이트웨이 출력을 ICC 테이블(경계 스냅샷)로 보여준다.
export default function IccTable() {
  const [graphs, setGraphs] = useState([])
  const [graphId, setGraphId] = useState(null)
  const [release, setRelease] = useState(null)
  const [status, setStatus] = useState('로딩 중…')
  const [error, setError] = useState(null)

  async function bake(id) {
    setError(null)
    setStatus('bake 중…')
    try {
      const res = await bakeGraph(id)
      setRelease(res.release)
      setStatus(`bake 완료 · ${res.baked} 경계`)
    } catch (e) {
      setError(e.data || String(e))
      setStatus('bake 실패')
    }
  }

  useEffect(() => {
    (async () => {
      try {
        const gs = await listGraphs()
        setGraphs(gs)
        const pref = gs.find((g) => g.slug === 'example-icc-partial') || gs[0]
        if (pref) { setGraphId(pref.id); bake(pref.id) } else setStatus('그래프 없음')
      } catch (e) { setError(e.data || String(e)); setStatus('로드 실패') }
    })()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const rows = (release?.records || []).slice()
    .sort((a, b) => (b.value_ma ?? -Infinity) - (a.value_ma ?? -Infinity))   // 오래된(큰 Ma)→젊은
  const curSlug = graphs.find((g) => g.id === graphId)?.slug

  return (
    <div className="icc">
      <div className="icc-controls">
        <label>그래프
          <select
            value={graphId || ''}
            onChange={(e) => { const id = Number(e.target.value); setGraphId(id); bake(id) }}
          >
            {graphs.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
          </select>
        </label>
        <button onClick={() => graphId && bake(graphId)}>다시 bake</button>
        <span className="icc-status">{status}</span>
      </div>

      {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}

      {rows.length === 0 ? (
        <p className="icc-empty">
          게이트웨이(경계 출력)가 있는 그래프를 고르세요. 그래프를 bake 하면 게이트웨이 출력이 ICC 테이블로 얼려집니다.
        </p>
      ) : (
        <>
          <table className="icctable">
            <thead>
              <tr>
                <th>경계</th><th>정의</th><th className="num">연대 (Ma)</th>
                <th>불확실성</th><th>출처</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.boundary}>
                  <td className="mono">{r.boundary}</td>
                  <td><span className={`deftype ${r.definition_type}`}>{r.definition_type || '—'}</span></td>
                  <td className="num">{fmt(r.value_ma)}</td>
                  <td className="unc">{uncertaintyText(r.uncertainty)}</td>
                  <td className="mono prov">{r.provenance_ref || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="icc-note">
            <b>bake</b> = 그래프 게이트웨이 출력을 얼린 ICC 스냅샷. 릴리스 <code>graph:{curSlug}</code> 로
            저장되어 <b>릴리스 Diff</b> 에서 다른 버전과 비교할 수 있습니다.
          </p>
        </>
      )}
    </div>
  )
}

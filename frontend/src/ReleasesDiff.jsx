import { useEffect, useMemo, useState } from 'react'
import { listReleases, bakeRelease, diffReleases } from './api.js'

// 두 릴리스 간 값 diff(같은 경계의 연대 이동)와 토폴로지 diff(배선: 추가/삭제/retype)를
// 직교 축으로 보여준다. 백엔드: GET /api/releases/diff/?a=&b= (releases/services.diff_releases).

const fmtMa = (v) => (v == null ? '—' : `${Number(v).toFixed(3)} Ma`)
const deltaClass = (d) => (d == null ? '' : d > 0 ? 'up' : d < 0 ? 'down' : '')

export default function ReleasesDiff() {
  const [releases, setReleases] = useState([])
  const [a, setA] = useState('')
  const [b, setB] = useState('')
  const [diff, setDiff] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    const rs = await listReleases()
    setReleases(rs)
    return rs
  }

  useEffect(() => {
    (async () => {
      try {
        const rs = await refresh()
        if (rs.length >= 2) { setA(String(rs[0].id)); setB(String(rs[rs.length - 1].id)) }
        else if (rs.length === 1) { setA(String(rs[0].id)); setB(String(rs[0].id)) }
      } catch (e) { setError(e.data || String(e)) }
      finally { setLoading(false) }
    })()
  }, [])

  useEffect(() => {
    if (!a || !b) { setDiff(null); return }
    (async () => {
      try { setError(null); setDiff(await diffReleases(a, b)) }
      catch (e) { setError(e.data || String(e)); setDiff(null) }
    })()
  }, [a, b])

  const relMap = useMemo(() => Object.fromEntries(releases.map((r) => [String(r.id), r])), [releases])

  const onBake = async (id) => {
    setError(null)
    try {
      await bakeRelease(id)
      await refresh()
      if (a && b) setDiff(await diffReleases(a, b))
    } catch (e) { setError(e.data || String(e)) }
  }

  if (loading) return <div className="diff"><p className="hint">로딩 중…</p></div>

  if (releases.length === 0) {
    return (
      <div className="diff">
        <h2>릴리스 Diff</h2>
        <p className="empty">
          릴리스가 없습니다. 시드 <code>example_releases</code> 를 로드하거나,
          릴리스를 만들어 bake 하면 여기서 비교할 수 있습니다.
        </p>
      </div>
    )
  }

  const relA = relMap[a]
  const relB = relMap[b]

  return (
    <div className="diff">
      <div className="diff-controls">
        <label>기준 A
          <select value={a} onChange={(e) => setA(e.target.value)}>
            {releases.map((r) => <option key={r.id} value={r.id}>{r.version}</option>)}
          </select>
        </label>
        <span className="arrow">→</span>
        <label>대상 B
          <select value={b} onChange={(e) => setB(e.target.value)}>
            {releases.map((r) => <option key={r.id} value={r.id}>{r.version}</option>)}
          </select>
        </label>
        <span className="diff-meta">
          {relA && `${relA.records?.length ?? 0}개 경계`} → {relB && `${relB.records?.length ?? 0}개 경계`}
        </span>
      </div>

      {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}

      {relA && (relA.records?.length ?? 0) === 0 && (
        <p className="none">
          A(<code>{relA.version}</code>)에 bake 된 레코드가 없습니다.
          <button className="link" onClick={() => onBake(relA.id)}>bake</button>
        </p>
      )}

      {diff && (
        <>
          <section className="diff-section">
            <h3>값 diff <small>value_diff · 같은 경계의 연대 이동</small></h3>
            {diff.value_diff.length === 0 ? <p className="none">변화 없음</p> : (
              <table className="difftable">
                <thead><tr><th>경계</th><th>A</th><th>B</th><th>Δ (Myr)</th></tr></thead>
                <tbody>
                  {diff.value_diff.map((d) => (
                    <tr key={d.boundary}>
                      <td className="mono">{d.boundary}</td>
                      <td className="num">{fmtMa(d.from)}</td>
                      <td className="num">{fmtMa(d.to)}</td>
                      <td className={`num delta ${deltaClass(d.delta)}`}>
                        {d.delta == null ? '—' : `${d.delta > 0 ? '+' : ''}${d.delta}`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <section className="diff-section">
            <h3>토폴로지 diff <small>topology_diff · 배선(경계 추가·삭제·retype)</small></h3>
            {diff.topology_diff.length === 0 ? <p className="none">변화 없음</p> : (
              <ul className="topolist">
                {diff.topology_diff.map((t, i) => (
                  <li key={i} className={`topo topo-${t.op}`}>
                    <span className="op">{t.op}</span>
                    <span className="mono">{t.boundary}</span>
                    {t.op === 'retype' && <span className="retype">{t.from || '∅'} → {t.to || '∅'}</span>}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  )
}

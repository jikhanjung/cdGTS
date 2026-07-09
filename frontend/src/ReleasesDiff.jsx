import { useEffect, useMemo, useState } from 'react'
import { listReleases, bakeRelease, diffReleases } from './api.js'

// Shows the value diff (age shifts of the same boundary) and topology diff (wiring: add/remove/retype)
// between two releases along orthogonal axes. Backend: GET /api/releases/diff/?a=&b= (releases/services.diff_releases).

const fmtMa = (v) => (v == null ? '—' : `${Number(v).toFixed(3)} Ma`)
const deltaClass = (d) => (d == null ? '' : d > 0 ? 'up' : d < 0 ? 'down' : '')

export default function ReleasesDiff({ initialA } = {}) {
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
        const first = initialA != null ? String(initialA) : (rs[0] ? String(rs[0].id) : '')
        if (rs.length >= 2) { setA(first); setB(String(rs[rs.length - 1].id)) }
        else if (rs.length === 1) { setA(first); setB(String(rs[0].id)) }
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

  if (loading) return <div className="diff"><p className="hint">Loading…</p></div>

  if (releases.length === 0) {
    return (
      <div className="diff">
        <h2>Releases Diff</h2>
        <p className="empty">
          No releases. Load the seed <code>example_releases</code>, or
          create a release and bake it to compare them here.
        </p>
      </div>
    )
  }

  const relA = relMap[a]
  const relB = relMap[b]

  return (
    <div className="diff">
      <div className="diff-controls">
        <label>Base A
          <select value={a} onChange={(e) => setA(e.target.value)}>
            {releases.map((r) => <option key={r.id} value={r.id}>{r.version}</option>)}
          </select>
        </label>
        <span className="arrow">→</span>
        <label>Target B
          <select value={b} onChange={(e) => setB(e.target.value)}>
            {releases.map((r) => <option key={r.id} value={r.id}>{r.version}</option>)}
          </select>
        </label>
        <span className="diff-meta">
          {relA && `${relA.record_count ?? 0} boundaries`} → {relB && `${relB.record_count ?? 0} boundaries`}
        </span>
      </div>

      {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}

      {relA && (relA.record_count ?? 0) === 0 && (
        <p className="none">
          A (<code>{relA.version}</code>) has no baked records.
          <button className="link" onClick={() => onBake(relA.id)}>bake</button>
        </p>
      )}

      {diff && (
        <>
          <section className="diff-section">
            <h3>Value diff <small>value_diff · age shift of the same boundary</small></h3>
            {diff.value_diff.length === 0 ? <p className="none">No changes</p> : (
              <table className="difftable">
                <thead><tr><th>Boundary</th><th>A</th><th>B</th><th>Δ (Myr)</th></tr></thead>
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
            <h3>Shape diff <small>shape_diff · the value&apos;s shape (exact ↔ distribution)</small></h3>
            {(diff.shape_diff || []).length === 0 ? <p className="none">No changes</p> : (
              <ul className="topolist">
                {diff.shape_diff.map((s, i) => (
                  <li key={i} className="topo topo-reshape">
                    <span className="op">reshape</span>
                    <span className="mono">{s.boundary}</span>
                    <span className="retype">{s.from} → {s.to}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="diff-section">
            <h3>Topology diff <small>topology_diff · wiring (boundary add · remove · retype)</small></h3>
            {diff.topology_diff.length === 0 ? <p className="none">No changes</p> : (
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

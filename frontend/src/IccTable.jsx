import { useEffect, useState } from 'react'
import { listGraphs, bakeGraph, getRelease } from './api.js'
import { summarizeDist } from './ResultsPanel.jsx'

const fmt = (x) => (x == null ? '—' : `${Number(x.toPrecision(7))}`)

// distribution → uncertainty display text (per fidelity).
function uncertaintyText(dist) {
  const s = summarizeDist(dist)
  if (!s) return '—'
  if (s.kind === 'exact') return 'No error'
  if (s.lo != null && s.hi != null) return `95% HPD [${fmt(s.lo)}, ${fmt(s.hi)}]`
  if (s.pm != null) return `± ${fmt(s.pm)}${s.sigma ? ` (${s.sigma}σ)` : ''}`
  return '—'
}

// Show a release's boundary records as an ICC table. Embedded in the Vault (embedReleaseId), or standalone
// where it bakes a chosen graph into a scratch release first.
export default function IccTable({ embedReleaseId } = {}) {
  const embedded = embedReleaseId != null
  const [graphs, setGraphs] = useState([])
  const [graphId, setGraphId] = useState(null)
  const [release, setRelease] = useState(null)
  const [status, setStatus] = useState('Loading…')
  const [error, setError] = useState(null)

  async function bake(id) {
    setError(null)
    setStatus('Baking…')
    try {
      const res = await bakeGraph(id)
      setRelease(res.release)
      setStatus(`Bake complete · ${res.baked} boundaries`)
    } catch (e) {
      setError(e.data || String(e))
      setStatus('Bake failed')
    }
  }

  useEffect(() => {
    if (embedded) return
    (async () => {
      try {
        const gs = await listGraphs()
        setGraphs(gs)
        const pref = gs.find((g) => g.slug === 'example-icc-partial') || gs[0]
        if (pref) { setGraphId(pref.id); bake(pref.id) } else setStatus('No graph')
      } catch (e) { setError(e.data || String(e)); setStatus('Load failed') }
    })()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Embedded: render the selected release's baked records directly.
  useEffect(() => {
    if (embedReleaseId == null) return
    setError(null); setStatus('Loading…')
    getRelease(embedReleaseId)
      .then((r) => { setRelease(r); setStatus(`${r.version} · ${r.records.length} boundaries`) })
      .catch((e) => { setError(e.data || String(e)); setStatus('Failed') })
  }, [embedReleaseId])

  const rows = (release?.records || []).slice()
    .sort((a, b) => (b.value_ma ?? -Infinity) - (a.value_ma ?? -Infinity))   // oldest (large Ma) → youngest
  const curSlug = graphs.find((g) => g.id === graphId)?.slug

  return (
    <div className="icc">
      <div className="icc-controls">
        {!embedded && (
          <>
            <label>Graph
              <select
                value={graphId || ''}
                onChange={(e) => { const id = Number(e.target.value); setGraphId(id); bake(id) }}
              >
                {graphs.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
              </select>
            </label>
            <button onClick={() => graphId && bake(graphId)}>Re-bake</button>
          </>
        )}
        <span className="icc-status">{status}</span>
      </div>

      {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}

      {rows.length === 0 ? (
        <p className="icc-empty">
          Choose a graph that has gateways (boundary outputs). Baking a graph freezes its gateway outputs into an ICC table.
        </p>
      ) : (
        <>
          <table className="icctable">
            <thead>
              <tr>
                <th>Boundary</th><th>Definition</th><th className="num">Age (Ma)</th>
                <th>Uncertainty</th><th>Source</th>
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
          {!embedded && (
            <p className="icc-note">
              <b>bake</b> = an ICC snapshot freezing the graph's gateway outputs. Saved as release <code>graph:{curSlug}</code>,
              so you can compare it against other versions in <b>Release Diff</b>.
            </p>
          )}
        </>
      )}
    </div>
  )
}

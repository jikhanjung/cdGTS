import { useEffect, useState } from 'react'
import { releaseCandidates, setReleaseOverride } from './api.js'

// P05.5 — per-boundary candidate overrides on a sandbox release. Swap the competing model that wins for a
// boundary; the release re-bakes server-side. Diff it against its base (Diff mode) to see the effect.
export default function Overrides({ releaseId, onChanged }) {
  const [rows, setRows] = useState([])
  const [status, setStatus] = useState('Loading…')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(null)   // boundary being written

  const load = () => releaseCandidates(releaseId)
    .then((d) => { setRows(d.boundaries); setStatus(`${d.boundaries.length} overridable boundaries`) })
    .catch((e) => { setError(e.data || String(e)); setStatus('Failed') })
  useEffect(() => { load() }, [releaseId])   // eslint-disable-line

  const change = async (boundary, candidate) => {
    setBusy(boundary); setError(null)
    try {
      await setReleaseOverride(releaseId, boundary, candidate || null)
      await load()
      if (onChanged) onChanged()
    } catch (e) { setError(e.data?.detail || e.data || String(e)) }
    finally { setBusy(null) }
  }

  return (
    <div className="overrides">
      <p className="hint">Pick which competing candidate wins for each boundary. “baseline” = the published pick.</p>
      {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}
      {rows.length === 0 ? (
        <p className="vault-empty">No boundary has a competing candidate to override.</p>
      ) : (
        <table className="ov-table">
          <thead><tr><th>Boundary</th><th>Candidate (winner)</th><th>Baseline</th></tr></thead>
          <tbody>
            {rows.map((r) => {
              const overridden = r.selected !== r.baseline
              return (
                <tr key={r.boundary} className={overridden ? 'ov-changed' : ''}>
                  <td className="mono">{r.boundary}</td>
                  <td>
                    <select value={r.selected || ''} disabled={busy === r.boundary}
                            onChange={(e) => change(r.boundary, e.target.value)}>
                      {r.options.map((o) => <option key={o} value={o}>{o}{o === r.baseline ? ' (baseline)' : ''}</option>)}
                    </select>
                    {overridden && (
                      <button className="ov-reset" disabled={busy === r.boundary}
                              onClick={() => change(r.boundary, null)} title="Reset to baseline">↺</button>
                    )}
                  </td>
                  <td className="mono ov-base">{r.baseline || '—'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
      <p className="ov-status">{status}</p>
    </div>
  )
}

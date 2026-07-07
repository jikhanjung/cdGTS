import { useEffect, useState } from 'react'
import { listReleases } from './api.js'
import IccChart from './IccChart.jsx'
import IccTable from './IccTable.jsx'
import Narrate from './Narrate.jsx'
import ReleasesDiff from './ReleasesDiff.jsx'

// Vault = the artifact hub. Lists baked Releases (published + user bakes) and renders a selected one
// as a Chart / Table / Narrative, or diffs two of them. The Editor bakes into here.
const MODES = [['chart', 'Chart'], ['table', 'Table'], ['narrative', 'Narrative'], ['diff', 'Diff']]
const fmtDate = (s) => (s ? new Date(s).toLocaleDateString() : '')

export default function Vault({ initialReleaseId } = {}) {
  const [releases, setReleases] = useState([])
  const [selId, setSelId] = useState(initialReleaseId ?? null)
  const [mode, setMode] = useState('chart')
  const [status, setStatus] = useState('Loading…')
  const [error, setError] = useState(null)

  useEffect(() => {
    (async () => {
      try {
        const rs = await listReleases()
        setReleases(rs)
        setStatus(`${rs.length} release${rs.length === 1 ? '' : 's'}`)
        setSelId((cur) => cur ?? (rs.find((r) => r.version === 'ICS-2024/12') || rs[0])?.id ?? null)
      } catch (e) { setError(e.data || String(e)); setStatus('Failed') }
    })()
  }, [])

  // A freshly baked release id (from the Editor) → select it.
  useEffect(() => { if (initialReleaseId != null) setSelId(initialReleaseId) }, [initialReleaseId])

  return (
    <div className="vault">
      <aside className="vault-rail">
        <h2>Vault</h2>
        <p className="vault-hint">Baked artifacts — pick one to view, or Diff two.</p>
        <ul className="vault-list">
          {releases.map((r) => (
            <li key={r.id} className={`vault-item${r.id === selId ? ' selected' : ''}`}
                onClick={() => setSelId(r.id)} title={r.note}>
              <span className="vault-ver">{r.version}</span>
              <span className="vault-metaline">
                <span className={`vault-kind ${r.kind}`}>{r.is_baseline ? 'baseline' : r.kind}</span>
                {r.source_graph && <span className="vault-src">⑂ {r.source_graph}</span>}
                <span className="vault-count">{r.record_count} bd</span>
                {r.created_at && <span className="vault-date">{fmtDate(r.created_at)}</span>}
              </span>
            </li>
          ))}
        </ul>
        {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}
      </aside>

      <main className="vault-main">
        <div className="vault-modes">
          {MODES.map(([m, label]) => (
            <button key={m} className={mode === m ? 'active' : ''} onClick={() => setMode(m)}>{label}</button>
          ))}
          <span className="vault-status">{status}</span>
        </div>
        <div className="vault-view">
          {selId == null ? (
            <p className="vault-empty">No release selected.</p>
          ) : mode === 'chart' ? <IccChart key={selId} embedReleaseId={selId} />
            : mode === 'table' ? <IccTable key={selId} embedReleaseId={selId} />
            : mode === 'narrative' ? <Narrate key={selId} embedReleaseId={selId} />
            : <ReleasesDiff key={selId} initialA={selId} />}
        </div>
      </main>
    </div>
  )
}

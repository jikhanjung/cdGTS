import { useEffect, useState } from 'react'
import { listReleases, createSandbox } from './api.js'
import IccChart from './IccChart.jsx'
import IccTable from './IccTable.jsx'
import Narrate from './Narrate.jsx'
import ReleasesDiff from './ReleasesDiff.jsx'
import Overrides from './Overrides.jsx'
import Clamps from './Clamps.jsx'
import Bibliography from './Bibliography.jsx'

// Vault = the artifact hub. Lists baked Releases (published · user bakes · your sandboxes) and renders a selected
// one as Chart / Table / Narrative / Clamps / Overrides, or diffs two. The Editor bakes into here; sandboxes override here.
const MODES = [['chart', 'Chart'], ['table', 'Table'], ['narrative', 'Narrative'], ['clamps', 'Clamps'], ['references', 'References'], ['diff', 'Diff']]
const fmtDate = (s) => (s ? new Date(s).toLocaleDateString() : '')

export default function Vault({ initialReleaseId, user } = {}) {
  const [releases, setReleases] = useState([])
  const [selId, setSelId] = useState(initialReleaseId ?? null)
  const [mode, setMode] = useState('chart')
  const [status, setStatus] = useState('Loading…')
  const [error, setError] = useState(null)
  const [nonce, setNonce] = useState(0)   // bump to force re-render of embedded views after an override

  const refresh = async (keepSel) => {
    const rs = await listReleases()
    setReleases(rs)
    setStatus(`${rs.length} release${rs.length === 1 ? '' : 's'}`)
    if (keepSel == null) setSelId((cur) => cur ?? (rs.find((r) => r.version === 'ICS-2024/12') || rs[0])?.id ?? null)
    return rs
  }
  useEffect(() => { refresh().catch((e) => { setError(e.data || String(e)); setStatus('Failed') }) }, [])   // eslint-disable-line
  useEffect(() => { if (initialReleaseId != null) setSelId(initialReleaseId) }, [initialReleaseId])

  const selected = releases.find((r) => r.id === selId)
  const authed = !!user?.authenticated
  const isMySandbox = selected?.kind === 'sandbox' && (selected.owner === user?.username || user?.is_staff)
  const canSandbox = authed && selected && selected.kind !== 'sandbox' && selected.kind !== 'transient'
  const modes = isMySandbox ? [...MODES, ['overrides', 'Overrides']] : MODES

  const onSandbox = async () => {
    setError(null)
    try {
      const sb = await createSandbox(selId)
      await refresh(true)
      setSelId(sb.id); setMode('overrides')
      setStatus(`Sandbox → ${sb.version}`)
    } catch (e) { setError(e.data?.detail || e.data || String(e)) }
  }
  const afterOverride = () => { setNonce((n) => n + 1); refresh(true).catch(() => {}) }

  return (
    <div className="vault">
      <aside className="vault-rail">
        <h2>Vault</h2>
        <p className="vault-hint">Baked artifacts — pick one to view, Diff two, or sandbox a baseline.</p>
        <ul className="vault-list">
          {releases.map((r) => (
            <li key={r.id} className={`vault-item${r.id === selId ? ' selected' : ''}`}
                onClick={() => { setSelId(r.id); if (mode === 'overrides' && r.kind !== 'sandbox') setMode('chart') }} title={r.note}>
              <span className="vault-ver">{r.version}</span>
              <span className="vault-metaline">
                <span className={`vault-kind ${r.kind}`}>{r.is_baseline ? 'baseline' : r.kind}</span>
                {r.source_graph && <span className="vault-src">⑂ {r.source_graph}</span>}
                {r.base && <span className="vault-src">◇ {r.base}</span>}
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
          {modes.map(([m, label]) => (
            <button key={m} className={mode === m ? 'active' : ''} onClick={() => setMode(m)}>{label}</button>
          ))}
          {canSandbox && <button className="vault-sandbox" onClick={onSandbox} title="Fork this baseline into a private sandbox you can override">Sandbox this →</button>}
          <span className="vault-status">{status}</span>
        </div>
        <div className="vault-view">
          {selId == null ? (
            <p className="vault-empty">No release selected.</p>
          ) : mode === 'chart' ? <IccChart key={`${selId}.${nonce}`} embedReleaseId={selId} />
            : mode === 'table' ? <IccTable key={`${selId}.${nonce}`} embedReleaseId={selId} />
            : mode === 'narrative' ? <Narrate key={`${selId}.${nonce}`} embedReleaseId={selId} />
            : mode === 'clamps' ? <Clamps key={`${selId}.${nonce}`} embedReleaseId={selId} user={user} />
            : mode === 'references' ? <Bibliography key={`${selId}.${nonce}`} embedReleaseId={selId} />
            : mode === 'overrides' ? <Overrides releaseId={selId} onChanged={afterOverride} />
            : <ReleasesDiff key={`${selId}.${nonce}`} initialA={selId} />}
        </div>
      </main>
    </div>
  )
}

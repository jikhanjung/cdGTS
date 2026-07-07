import { useEffect, useState } from 'react'
import { listReleases, narrateRelease } from './api.js'

// The counterpart to bake (frozen table) — renders a release as a "narrated book" by rank. Oldest to youngest.
export default function Narrate({ embedReleaseId } = {}) {
  const embedded = embedReleaseId != null
  const [releases, setReleases] = useState([])
  const [releaseId, setReleaseId] = useState(null)
  const [doc, setDoc] = useState(null)
  const [status, setStatus] = useState('Loading…')
  const [error, setError] = useState(null)

  async function load(id) {
    setError(null); setStatus('Generating narrative…')
    try {
      const d = await narrateRelease(id); setDoc(d)
      const n = d.sections.reduce((a, s) => a + s.entries.length, 0)
      setStatus(`${d.release} · ${n} boundaries narrated`)
    } catch (e) { setError(e.data || String(e)); setStatus('Failed') }
  }

  useEffect(() => {
    if (embedded) return
    (async () => {
      try {
        const rs = await listReleases(); setReleases(rs)
        const rp = rs.find((r) => r.version === 'ICS-2024/12') || rs[0]
        if (rp) { setReleaseId(rp.id); load(rp.id) } else setStatus('No releases')
      } catch (e) { setError(e.data || String(e)); setStatus('Failed') }
    })()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Embedded (Vault): narrate the selected release.
  useEffect(() => {
    if (embedReleaseId == null) return
    setReleaseId(embedReleaseId); load(embedReleaseId)
  }, [embedReleaseId]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="narrate">
      <div className="narrate-controls">
        {!embedded && (
          <label>Release
            <select value={releaseId || ''} onChange={(e) => { const id = Number(e.target.value); setReleaseId(id); load(id) }}>
              {releases.map((r) => <option key={r.id} value={r.id}>{r.version}</option>)}
            </select>
          </label>
        )}
        <span className="narrate-status">{status}</span>
      </div>

      {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}

      {doc && (
        <div className="narrate-book">
          {doc.sections.map((s) => (
            <section key={s.rank}>
              <h3>{s.rank} <span className="narrate-count">{s.entries.length}</span></h3>
              {s.entries.map((e) => (
                <p key={e.boundary} className="narrate-entry">
                  <span className={`narrate-badge ${e.definition_type === 'GSSA' ? 'gssa' : 'gssp'}`}>
                    {e.definition_type || '—'}
                  </span>
                  {e.narrative}
                </p>
              ))}
            </section>
          ))}
        </div>
      )}
      <p className="narrate-note">
        The counterpart to bake (frozen table) — deterministically renders structured fields (definition, age, error, method, dual naming) <b>without inventing facts</b>.
        Each narrative is stored in <code>BoundaryRecord.narrative</code> (reproducible). By rank · oldest to youngest.
      </p>
    </div>
  )
}

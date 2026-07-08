import { useEffect, useState } from 'react'
import { releaseClamps, reconcileRelease } from './api.js'

// Vault "Clamps" view — authored governance clamps on a release + L3a verify (honored?), and staff L3b reconcile.
export default function Clamps({ embedReleaseId, user }) {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState(null)

  const load = () => releaseClamps(embedReleaseId).then(setData).catch((e) => setErr(e.data || String(e)))
  useEffect(() => { setData(null); setErr(null); setNote(null); load() }, [embedReleaseId])   // eslint-disable-line react-hooks/exhaustive-deps

  const reconcile = async () => {
    setBusy(true); setNote(null); setErr(null)
    try {
      const r = await reconcileRelease(embedReleaseId)
      setNote(`Reconciled — ${r.changed} boundary value(s) moved`
        + (r.conflicts.length ? ` · conflicts: ${r.conflicts.join(', ')}` : ''))
      load()
    } catch (e) { setErr(e.data?.detail || e.data || String(e)) } finally { setBusy(false) }
  }

  if (err) return <div className="clamps-view"><pre className="error">{JSON.stringify(err, null, 2)}</pre></div>
  if (!data) return <div className="clamps-view"><p className="muted">Loading…</p></div>
  const { clamps, violations } = data
  return (
    <div className="clamps-view">
      <div className="clamps-head">
        <span>Authored clamps <b>{clamps.length}</b> · violations{' '}
          <b className={violations.length ? 'bad' : 'ok'}>{violations.length}</b></span>
        {user?.is_staff && clamps.length > 0 && (
          <button disabled={busy} onClick={reconcile} title="Apply the clamps to boundary values (L3b — GTS contract, values move)">
            {busy ? 'Reconciling…' : 'Reconcile (L3b) →'}
          </button>
        )}
      </div>
      {note && <p className="u-note">{note}</p>}
      {clamps.length === 0 ? (
        <p className="muted">No authored governance clamps on this release. (Author them in /admin — Release → clamps.)</p>
      ) : (
        <div className="users-table-wrap">
          <table className="users-table">
            <thead><tr><th>Boundary</th><th>Kind</th><th>Value</th><th>Owner</th><th>L3a check</th></tr></thead>
            <tbody>
              {clamps.map((c) => {
                const viol = violations.find((v) => v.boundary === c.boundary && (v.kind === c.kind || v.kind === 'conflict'))
                return (
                  <tr key={c.slug}>
                    <td>{c.boundary || <span className="muted">—</span>}</td>
                    <td>{c.kind}</td>
                    <td>{JSON.stringify(c.value)}</td>
                    <td>{c.owner}</td>
                    <td>{viol
                      ? <span className="ustat off" title={viol.detail}>{viol.kind === 'conflict' ? 'conflict' : viol.detail}</span>
                      : <span className="ustat on">honored</span>}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
      <p className="clamps-note">L3a = verify only (values unchanged). Reconcile applies clamps (L3b): pin → exact, range → truncate; pin outranks range; same-rank clamps from different owners flag a conflict.</p>
    </div>
  )
}

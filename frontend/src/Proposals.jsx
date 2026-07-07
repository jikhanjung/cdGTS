import { useEffect, useState } from 'react'
import { listProposals, getProposal, ratifyProposal, rejectProposal } from './api.js'

// P05.4 — the CI review surface. Lists proposals; the detail reuses the verify diff (proposed vs baseline);
// authority members ratify (→ new published baseline) or reject (→ back to sandbox).
const fmt = (x) => (x == null ? '—' : `${Number(x.toPrecision(7))}`)

export default function Proposals({ user }) {
  const [items, setItems] = useState([])
  const [filter, setFilter] = useState('open')
  const [selId, setSelId] = useState(null)
  const [detail, setDetail] = useState(null)
  const [comment, setComment] = useState('')
  const [status, setStatus] = useState('Loading…')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const refresh = async () => {
    const rs = await listProposals(filter === 'all' ? '' : filter)
    setItems(rs); setStatus(`${rs.length} ${filter} proposal${rs.length === 1 ? '' : 's'}`)
    return rs
  }
  useEffect(() => { refresh().catch((e) => { setError(e.data || String(e)); setStatus('Failed') }) }, [filter])   // eslint-disable-line
  useEffect(() => {
    if (selId == null) { setDetail(null); return }
    getProposal(selId).then((d) => { setDetail(d); setComment('') }).catch((e) => setError(e.data || String(e)))
  }, [selId])

  const act = async (fn, verb) => {
    setBusy(true); setError(null)
    try {
      await fn(selId, comment)
      setStatus(`Proposal #${selId} ${verb}.`)
      await refresh()
      setDetail(await getProposal(selId))
    } catch (e) { setError(e.data || String(e)) }
    finally { setBusy(false) }
  }

  const diff = detail?.diff
  const s = diff?.summary

  return (
    <div className="vault">
      <aside className="vault-rail">
        <h2>Proposals</h2>
        <div className="prop-filter">
          {['open', 'merged', 'rejected', 'all'].map((f) => (
            <button key={f} className={filter === f ? 'active' : ''} onClick={() => { setFilter(f); setSelId(null) }}>{f}</button>
          ))}
        </div>
        <ul className="vault-list">
          {items.map((p) => (
            <li key={p.id} className={`vault-item${p.id === selId ? ' selected' : ''}`} onClick={() => setSelId(p.id)}>
              <span className="vault-ver">{p.graph_name}</span>
              <span className="vault-metaline">
                <span className={`prop-state ${p.state}`}>{p.state}</span>
                {p.author && <span>by {p.author}</span>}
                <span className="vault-count">{(p.affected || []).length} bd</span>
              </span>
            </li>
          ))}
        </ul>
        {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}
      </aside>

      <main className="vault-main">
        <div className="vault-modes"><span className="vault-status">{status}</span></div>
        <div className="vault-view">
          {!detail ? (
            <p className="vault-empty">Select a proposal to review.</p>
          ) : (
            <div className="prop-detail">
              <h3>{detail.graph_name} <span className={`prop-state ${detail.state}`}>{detail.state}</span></h3>
              <p className="prop-meta">
                vs baseline <code>{detail.baseline}</code> · by {detail.author || '—'}
                {detail.reviewer && ` · reviewed by ${detail.reviewer}`}
                {detail.result_release && ` · published ${detail.result_release}`}
              </p>
              {detail.comment && <p className="prop-comment">“{detail.comment}”</p>}

              {s && (
                <p className="prop-summary">
                  {s.moved} moved · max |Δ| {s.max_abs_delta} Ma · wiring ＋{s.added}/－{s.removed}/↺{s.retyped}
                </p>
              )}
              {diff?.value_diff?.length > 0 && (
                <table className="prop-diff">
                  <thead><tr><th>Boundary</th><th className="num">baseline</th><th className="num">proposed</th><th className="num">Δ Ma</th></tr></thead>
                  <tbody>
                    {diff.value_diff.map((v) => (
                      <tr key={v.boundary}>
                        <td className="mono">{v.boundary}</td>
                        <td className="num">{fmt(v.from)}</td>
                        <td className="num">{fmt(v.to)}</td>
                        <td className={`num ${v.delta > 0 ? 'pos' : v.delta < 0 ? 'neg' : ''}`}>{v.delta == null ? '—' : (v.delta > 0 ? '+' : '') + fmt(v.delta)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              {diff?.topology_diff?.length > 0 && (
                <ul className="prop-topo">
                  {diff.topology_diff.map((t, i) => (
                    <li key={i}><span className="mono">{t.boundary}</span> — {t.op}{t.from ? ` ${t.from}→${t.to}` : ''}</li>
                  ))}
                </ul>
              )}

              {detail.state === 'open' && (
                detail.can_ratify ? (
                  <div className="prop-review">
                    <input type="text" placeholder="Review comment (optional)" value={comment}
                           onChange={(e) => setComment(e.target.value)} disabled={busy} />
                    <button className="prop-ratify" disabled={busy} onClick={() => act(ratifyProposal, 'ratified')}>Ratify → publish</button>
                    <button className="prop-reject" disabled={busy} onClick={() => act(rejectProposal, 'rejected')}>Reject</button>
                  </div>
                ) : (
                  <p className="prop-note">{user?.authenticated ? 'You are not a ratifying authority member.' : 'Sign in as an authority member to ratify.'}</p>
                )
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { releaseReferences } from './api.js'

// Vault "References" view — a baked release's bibliography (cite provenance collected at bake),
// with which boundaries each source feeds. Backend: GET /api/releases/{id}/references/.
export default function Bibliography({ embedReleaseId }) {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    setData(null); setErr(null)
    releaseReferences(embedReleaseId).then(setData).catch((e) => setErr(e.data || String(e)))
  }, [embedReleaseId])

  if (err) return <div className="biblio-view"><pre className="error">{JSON.stringify(err, null, 2)}</pre></div>
  if (!data) return <div className="biblio-view"><p className="muted">Loading…</p></div>

  const { bibliography, by_boundary } = data
  // Invert by_boundary → which boundaries each reference feeds.
  const feeds = {}
  Object.entries(by_boundary || {}).forEach(([b, slugs]) => (slugs || []).forEach((s) => (feeds[s] || (feeds[s] = [])).push(b)))

  return (
    <div className="biblio-view">
      <div className="biblio-head">
        <span>Bibliography <b>{bibliography.length}</b> · source{bibliography.length === 1 ? '' : 's'} collected from cite edges at bake</span>
      </div>
      {bibliography.length === 0 ? (
        <p className="muted">
          No references. Add <code>reference</code> nodes in the Editor and wire their citation port
          to the data/model nodes they source, then re-bake.
        </p>
      ) : (
        <ul className="biblio-list">
          {bibliography.map((r) => (
            <li key={r.slug} className="biblio-item">
              <div className="biblio-cite">
                <span className="biblio-authors">{r.authors || r.slug}</span>
                {r.year ? <span className="biblio-year"> ({r.year})</span> : null}
                {r.title ? <span className="biblio-title"> — {r.title}</span> : null}
                {r.container ? <span className="biblio-container">, {r.container}</span> : null}
              </div>
              <div className="biblio-meta">
                {r.link
                  ? <a href={r.link} target="_blank" rel="noreferrer" className="biblio-link">{r.doi ? `doi:${r.doi}` : r.link} ↗</a>
                  : <span className="muted">no DOI / URL</span>}
                {feeds[r.slug]?.length ? <span className="biblio-feeds">feeds: {feeds[r.slug].join(', ')}</span> : null}
                {r.created_by ? <span className="biblio-by">added by {r.created_by}</span> : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

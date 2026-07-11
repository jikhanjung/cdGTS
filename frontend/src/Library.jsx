import { useEffect, useRef, useState } from 'react'
import { listReferences, createReference, updateReference, deleteReference, crossrefLookup } from './api.js'

// Top-level "Bibliography" surface — the whole reference registry (a global, DOI-centric library).
// List every entry; create new ones (auth); edit/delete your own (or any, if staff). A reference
// cited by any graph can't be deleted (backend 409). Per-release provenance lives in Vault → References.
const KINDS = [
  ['article', 'journal article'], ['book', 'book'], ['chapter', 'book chapter'],
  ['dataset', 'dataset'], ['report', 'report'], ['web', 'web'],
]

export default function Library({ user }) {
  const [refs, setRefs] = useState([])
  const [err, setErr] = useState(null)
  const [q, setQ] = useState('')
  const [edit, setEdit] = useState(null)   // reference being edited, or { _new: true } for a new entry

  const load = () => listReferences().then(setRefs).catch((e) => setErr(e.data || String(e)))
  useEffect(() => { load() }, [])

  const authed = !!user?.authenticated
  const canEdit = (r) => authed && (user.is_staff || (r.created_by && r.created_by === user.username))

  const needle = q.trim().toLowerCase()
  const shown = needle
    ? refs.filter((r) => [r.slug, r.doi, r.title, r.authors, r.container, r.year]
        .some((v) => String(v || '').toLowerCase().includes(needle)))
    : refs

  return (
    <div className="users-page biblio-page">
      <header className="users-head">
        <h2>Bibliography <b>{refs.length}</b></h2>
        <input className="biblio-search" placeholder="Search author / title / DOI…"
               value={q} onChange={(e) => setQ(e.target.value)} />
        {authed
          ? <button className="primary" onClick={() => setEdit({ _new: true })}>+ New reference</button>
          : <span className="muted">Sign in to add references.</span>}
      </header>
      {err && <pre className="error">{JSON.stringify(err, null, 2)}</pre>}
      <div className="users-table-wrap">
        <table className="users-table biblio-table">
          <thead>
            <tr><th>Source</th><th>DOI / URL</th><th>Kind</th><th>Added by</th><th></th></tr>
          </thead>
          <tbody>
            {shown.map((r) => (
              <tr key={r.id}>
                <td>
                  <span className="biblio-authors">{r.authors || r.slug}</span>
                  {r.year ? <span className="biblio-year"> ({r.year})</span> : null}
                  {r.title ? <span className="biblio-title"> — {r.title}</span> : null}
                  {r.container ? <span className="biblio-container">, {r.container}</span> : null}
                </td>
                <td>
                  {r.link
                    ? <a href={r.link} target="_blank" rel="noreferrer" className="biblio-link">{r.doi ? `doi:${r.doi}` : r.link} ↗</a>
                    : <span className="muted">—</span>}
                </td>
                <td>{r.kind}</td>
                <td>{r.created_by || <span className="muted">system</span>}</td>
                <td>
                  <button onClick={() => setEdit(r)}>{canEdit(r) ? 'Edit' : 'View'}</button>
                </td>
              </tr>
            ))}
            {shown.length === 0 && (
              <tr><td colSpan={5} className="muted" style={{ textAlign: 'center', padding: '1.5rem' }}>
                {refs.length ? 'No matches.' : 'No references yet.'}
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
      {edit && (
        <RefDialog reference={edit._new ? null : edit} canEdit={edit._new ? authed : canEdit(edit)}
                   onClose={() => setEdit(null)} onChanged={load} />
      )}
    </div>
  )
}

function RefDialog({ reference, canEdit, onClose, onChanged }) {
  const isNew = !reference
  const [d, setD] = useState({
    slug: reference?.slug || '', doi: reference?.doi || '', title: reference?.title || '',
    authors: reference?.authors || '', year: reference?.year || '', container: reference?.container || '',
    url: reference?.url || '', kind: reference?.kind || 'article', note: reference?.note || '',
  })
  const [busy, setBusy] = useState(false)
  const [fetching, setFetching] = useState(false)
  const [err, setErr] = useState(null)
  const [conflict, setConflict] = useState(null)   // { detail, cited_by } from a blocked delete
  const down = useRef(false)

  const set = (k, v) => setD((s) => ({ ...s, [k]: v }))

  const fetchDoi = async () => {
    if (!d.doi.trim()) { setErr('enter a DOI first'); return }
    setFetching(true); setErr(null)
    try {
      const m = await crossrefLookup(d.doi.trim())
      setD((s) => ({
        ...s,
        doi: m.doi || s.doi,
        title: m.title || s.title,
        authors: m.authors || s.authors,
        year: m.year != null ? String(m.year) : s.year,
        container: m.container || s.container,
        kind: m.kind || s.kind,
        slug: isNew ? (s.slug || m.suggested_slug || '') : s.slug,   // don't touch the slug of an existing entry (natural key)
      }))
    } catch (e) { setErr(e?.data?.detail || e?.data || 'Crossref lookup failed') }
    finally { setFetching(false) }
  }

  const save = async () => {
    setBusy(true); setErr(null)
    const body = {
      slug: d.slug.trim(), doi: d.doi.trim(), title: d.title.trim(), authors: d.authors.trim(),
      year: d.year === '' ? null : Number(d.year), container: d.container.trim(),
      url: d.url.trim(), kind: d.kind, note: d.note,
    }
    try {
      if (isNew) await createReference(body)
      else await updateReference(reference.id, body)
      onChanged(); onClose()
    } catch (e) { setErr(e.data || String(e)); setBusy(false) }
  }

  const remove = async () => {
    setBusy(true); setErr(null); setConflict(null)
    try { await deleteReference(reference.id); onChanged(); onClose() }
    catch (e) {
      if (e.status === 409) setConflict(e.data)
      else setErr(e.data || String(e))
      setBusy(false)
    }
  }

  return (
    <div className="modal-backdrop"
         onMouseDown={(e) => { down.current = e.target === e.currentTarget }}
         onClick={(e) => { if (!busy && down.current && e.target === e.currentTarget) onClose() }}>
      <div className="bake-dialog user-dialog">
        <h3>{isNew ? 'New reference' : (canEdit ? `Edit ${reference.slug}` : reference.slug)}</h3>
        <fieldset className="insp-fields" disabled={!canEdit || busy} style={{ border: 'none', padding: 0, margin: 0 }}>
          <label className="bake-name">Slug (natural key)
            <input value={d.slug} autoFocus={isNew} placeholder="cohen-2013-ics"
                   disabled={!isNew || !canEdit || busy} onChange={(e) => set('slug', e.target.value)} />
          </label>
          <label className="bake-name">Title
            <input value={d.title} onChange={(e) => set('title', e.target.value)} />
          </label>
          <div className="u-row">
            <label className="bake-name">Authors
              <input value={d.authors} placeholder="Cohen, Finney, Gibbard & Fan"
                     onChange={(e) => set('authors', e.target.value)} />
            </label>
            <label className="bake-name">Year
              <input type="number" value={d.year} style={{ width: '6rem' }}
                     onChange={(e) => set('year', e.target.value)} />
            </label>
          </div>
          <label className="bake-name">Container (journal / publisher)
            <input value={d.container} onChange={(e) => set('container', e.target.value)} />
          </label>
          <div className="u-row">
            <label className="bake-name">DOI <span className="hint">(without https://doi.org/)</span>
              <span className="lib-doi-row">
                <input value={d.doi} placeholder="10.1130/2012.gts" onChange={(e) => set('doi', e.target.value)} />
                {canEdit && (
                  <button type="button" className="lib-doi-fetch" onClick={fetchDoi} disabled={fetching || busy}
                          title="Autofill title·authors·year·container from Crossref">
                    {fetching ? '…' : 'Fetch'}
                  </button>
                )}
              </span>
            </label>
            <label className="bake-name">Kind
              <select value={d.kind} onChange={(e) => set('kind', e.target.value)}>
                {KINDS.map(([v, lbl]) => <option key={v} value={v}>{lbl}</option>)}
              </select>
            </label>
          </div>
          <label className="bake-name">URL <span className="hint">(fallback when no DOI)</span>
            <input value={d.url} placeholder="https://stratigraphy.org" onChange={(e) => set('url', e.target.value)} />
          </label>
          <label className="bake-name">Note
            <textarea value={d.note} rows={2} onChange={(e) => set('note', e.target.value)} />
          </label>
        </fieldset>

        {conflict && (
          <p className="u-note error small">
            {conflict.detail || 'Cited by a graph — cannot delete.'}
            {conflict.cited_by?.length ? <> Cited by: <b>{conflict.cited_by.join(', ')}</b>.</> : null}
          </p>
        )}
        {err && <pre className="error small">{typeof err === 'string' ? err : JSON.stringify(err, null, 2)}</pre>}
        <div className="bake-actions">
          {canEdit && !isNew && (
            <button className="danger" onClick={remove} disabled={busy} style={{ marginRight: 'auto' }}>Delete</button>
          )}
          <button onClick={onClose} disabled={busy}>Close</button>
          {canEdit && (
            <button className="primary" onClick={save} disabled={busy || !d.slug.trim() || !d.title.trim()}>
              {busy ? 'Saving…' : (isNew ? 'Create' : 'Save')}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

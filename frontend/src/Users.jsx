import { useEffect, useRef, useState } from 'react'
import {
  listUsers, listGovAuthorities, createUser, updateUser,
  setUserPassword, addMembership, removeMembership,
} from './api.js'

// Staff-only user administration: list · create · edit profile/staff/active · reset password · memberships (ratify).
export default function Users({ user }) {
  const [users, setUsers] = useState([])
  const [auths, setAuths] = useState([])
  const [err, setErr] = useState(null)
  const [edit, setEdit] = useState(null)   // user object being edited, or { _new: true } for a new account

  const load = () => listUsers().then(setUsers).catch((e) => setErr(e.data || String(e)))
  useEffect(() => { load(); listGovAuthorities().then(setAuths).catch(() => {}) }, [])

  if (!user?.is_staff) return <div className="users-page"><p className="users-empty">Staff only.</p></div>

  const gov = (u) => (u.memberships || []).filter((m) => m.kind !== 'fork')

  return (
    <div className="users-page">
      <header className="users-head">
        <h2>Users <b>{users.length}</b></h2>
        <button className="primary" onClick={() => setEdit({ _new: true })}>+ New user</button>
      </header>
      {err && <pre className="error">{JSON.stringify(err, null, 2)}</pre>}
      <div className="users-table-wrap">
        <table className="users-table">
          <thead>
            <tr><th>Username</th><th>Name</th><th>Email</th><th>Roles</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.username}{u.is_staff ? ' ★' : ''}</td>
                <td>{[u.first_name, u.last_name].filter(Boolean).join(' ') || <span className="muted">—</span>}</td>
                <td>{u.email || <span className="muted">—</span>}</td>
                <td>
                  {gov(u).length
                    ? gov(u).map((m) => <span key={m.id} className="role-chip">{m.authority_name} ({m.role})</span>)
                    : <span className="muted">—</span>}
                </td>
                <td>{u.is_active ? <span className="ustat on">active</span> : <span className="ustat off">disabled</span>}</td>
                <td><button onClick={() => setEdit(u)}>Edit</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {edit && (
        <UserDialog user={edit._new ? null : edit} authorities={auths}
                    onClose={() => setEdit(null)} onChanged={load} />
      )}
    </div>
  )
}

function UserDialog({ user, authorities, onClose, onChanged }) {
  const isNew = !user
  const [u, setU] = useState(user)   // live copy (membership edits refresh it)
  const [draft, setDraft] = useState({
    username: '', password: '',
    first_name: user?.first_name || '', last_name: user?.last_name || '',
    email: user?.email || '', is_staff: user?.is_staff || false, is_active: user?.is_active ?? true,
  })
  const [pw, setPw] = useState('')
  const [addAuth, setAddAuth] = useState(authorities[0]?.slug || '')
  const [addRole, setAddRole] = useState('chair')
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState(null)
  const [err, setErr] = useState(null)
  const down = useRef(false)

  const set = (k, v) => setDraft((d) => ({ ...d, [k]: v }))

  const save = async () => {
    setBusy(true); setErr(null)
    try {
      if (isNew) {
        await createUser({
          username: draft.username.trim(), password: draft.password,
          first_name: draft.first_name, last_name: draft.last_name, email: draft.email, is_staff: draft.is_staff,
        })
      } else {
        await updateUser(u.id, {
          first_name: draft.first_name, last_name: draft.last_name,
          email: draft.email, is_staff: draft.is_staff, is_active: draft.is_active,
        })
      }
      onChanged(); onClose()
    } catch (e) { setErr(e.data || String(e)); setBusy(false) }
  }

  const resetPw = async () => {
    if (pw.length < 6) { setNote('Password must be at least 6 characters.'); return }
    setBusy(true); setNote(null); setErr(null)
    try { await setUserPassword(u.id, pw); setPw(''); setNote('Password updated.') }
    catch (e) { setErr(e.data || String(e)) }
    finally { setBusy(false) }
  }

  const doAdd = async () => {
    if (!addAuth) return
    setBusy(true); setErr(null)
    try { const nu = await addMembership(u.id, addAuth, addRole); setU(nu); onChanged() }
    catch (e) { setErr(e.data || String(e)) }
    finally { setBusy(false) }
  }
  const doRemove = async (mid) => {
    setBusy(true); setErr(null)
    try { const nu = await removeMembership(u.id, mid); setU(nu); onChanged() }
    catch (e) { setErr(e.data || String(e)) }
    finally { setBusy(false) }
  }

  const gov = (u?.memberships || []).filter((m) => m.kind !== 'fork')

  return (
    <div className="modal-backdrop"
         onMouseDown={(e) => { down.current = e.target === e.currentTarget }}
         onClick={(e) => { if (!busy && down.current && e.target === e.currentTarget) onClose() }}>
      <div className="bake-dialog user-dialog">
        <h3>{isNew ? 'New user' : `Edit ${u.username}`}</h3>
        {isNew && (
          <>
            <label className="bake-name">Username
              <input value={draft.username} autoFocus disabled={busy}
                     onChange={(e) => set('username', e.target.value)} />
            </label>
            <label className="bake-name">Password
              <input type="password" value={draft.password} disabled={busy}
                     onChange={(e) => set('password', e.target.value)} />
            </label>
          </>
        )}
        <div className="u-row">
          <label className="bake-name">First name
            <input value={draft.first_name} disabled={busy} onChange={(e) => set('first_name', e.target.value)} />
          </label>
          <label className="bake-name">Last name
            <input value={draft.last_name} disabled={busy} onChange={(e) => set('last_name', e.target.value)} />
          </label>
        </div>
        <label className="bake-name">Email
          <input type="email" value={draft.email} disabled={busy} onChange={(e) => set('email', e.target.value)} />
        </label>
        <div className="u-flags">
          <label><input type="checkbox" checked={draft.is_staff} disabled={busy}
                        onChange={(e) => set('is_staff', e.target.checked)} /> staff (admin ★)</label>
          {!isNew && (
            <label><input type="checkbox" checked={draft.is_active} disabled={busy}
                          onChange={(e) => set('is_active', e.target.checked)} /> active</label>
          )}
        </div>

        {!isNew && (
          <>
            <div className="u-section">
              <h4>Memberships <span className="hint">— grant ratify via ICS / subcommission</span></h4>
              <div className="u-mems">
                {gov.length ? gov.map((m) => (
                  <span key={m.id} className="role-chip removable">
                    {m.authority_name} ({m.role})
                    <button disabled={busy} onClick={() => doRemove(m.id)} title="Remove">✕</button>
                  </span>
                )) : <span className="muted">No governance roles.</span>}
              </div>
              <div className="u-addmem">
                <select value={addAuth} disabled={busy || !authorities.length} onChange={(e) => setAddAuth(e.target.value)}>
                  {authorities.map((a) => <option key={a.slug} value={a.slug}>{a.name} ({a.kind})</option>)}
                </select>
                <select value={addRole} disabled={busy} onChange={(e) => setAddRole(e.target.value)}>
                  <option value="chair">chair</option>
                  <option value="member">member</option>
                </select>
                <button disabled={busy || !addAuth} onClick={doAdd}>Add</button>
              </div>
            </div>
            <div className="u-section">
              <h4>Reset password</h4>
              <div className="u-addmem">
                <input type="password" placeholder="New password" value={pw} disabled={busy}
                       onChange={(e) => setPw(e.target.value)} />
                <button disabled={busy || !pw} onClick={resetPw}>Set</button>
              </div>
            </div>
          </>
        )}

        {note && <p className="u-note">{note}</p>}
        {err && <pre className="error small">{typeof err === 'string' ? err : JSON.stringify(err, null, 2)}</pre>}
        <div className="bake-actions">
          <button onClick={onClose} disabled={busy}>Close</button>
          <button className="primary" onClick={save}
                  disabled={busy || (isNew && (!draft.username.trim() || draft.password.length < 6))}>
            {busy ? 'Saving…' : (isNew ? 'Create' : 'Save')}
          </button>
        </div>
      </div>
    </div>
  )
}

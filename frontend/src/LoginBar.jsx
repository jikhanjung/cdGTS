import { useState } from 'react'
import { login, logout } from './api.js'

// Session login control in the top nav. Invite-only (no signup) — accounts are created by an admin.
export default function LoginBar({ user, onChange }) {
  const [open, setOpen] = useState(false)
  const [u, setU] = useState('')
  const [p, setP] = useState('')
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setErr(null)
    try {
      const me = await login(u, p)
      onChange(me); setOpen(false); setU(''); setP('')
    } catch (e2) { setErr(e2.data?.detail || 'Login failed') }
    finally { setBusy(false) }
  }
  const doLogout = async () => { onChange(await logout()) }

  if (user?.authenticated) {
    return (
      <span className="loginbar">
        <span className="login-user"
              title={(user.memberships || []).map((m) => `${m.authority_name} (${m.role})`).join(', ')}>
          {user.username}{user.is_staff ? ' ★' : ''}
        </span>
        <button className="login-btn" onClick={doLogout}>Logout</button>
      </span>
    )
  }

  return (
    <span className="loginbar">
      <button className="login-btn" onClick={() => setOpen(true)}>Login</button>
      {open && (
        <div className="modal-backdrop" onClick={() => !busy && setOpen(false)}>
          <form className="bake-dialog login-dialog" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
            <h3>Sign in</h3>
            <label className="bake-name">Username
              <input value={u} autoFocus disabled={busy} onChange={(e) => setU(e.target.value)} />
            </label>
            <label className="bake-name">Password
              <input type="password" value={p} disabled={busy} onChange={(e) => setP(e.target.value)} />
            </label>
            {err && <p className="login-err">{err}</p>}
            <div className="bake-actions">
              <button type="button" onClick={() => setOpen(false)} disabled={busy}>Cancel</button>
              <button type="submit" className="primary" disabled={busy || !u || !p}>
                {busy ? 'Signing in…' : 'Sign in'}
              </button>
            </div>
          </form>
        </div>
      )}
    </span>
  )
}

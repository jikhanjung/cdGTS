import { useRef, useState } from 'react'
import { login, logout, updateProfile } from './api.js'

// Session login control in the top nav. Invite-only (no signup) — accounts are created by an admin.
export default function LoginBar({ user, onChange }) {
  const [open, setOpen] = useState(false)
  const [u, setU] = useState('')
  const [p, setP] = useState('')
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const [profile, setProfile] = useState(null)   // { first_name, last_name, email, busy } | null
  const downOnBackdrop = useRef(false)   // only dismiss when the press *started* on the backdrop (not a stray click/blur from the password field)

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
        <button className="login-user"
                title="Your profile — name, email"
                onClick={() => setProfile({ first_name: user.first_name || '', last_name: user.last_name || '', email: user.email || '', busy: false })}>
          {user.username}{user.is_staff ? ' ★' : ''}
        </button>
        <button className="login-btn" onClick={doLogout}>Logout</button>
        {profile && (
          <ProfileDialog user={user} profile={profile} setProfile={setProfile} onChange={onChange} />
        )}
      </span>
    )
  }

  return (
    <span className="loginbar">
      <button className="login-btn" onClick={() => setOpen(true)}>Login</button>
      {open && (
        <div className="modal-backdrop"
             onMouseDown={(e) => { downOnBackdrop.current = e.target === e.currentTarget }}
             onClick={(e) => { if (!busy && downOnBackdrop.current && e.target === e.currentTarget) setOpen(false) }}>
          <form className="bake-dialog login-dialog" onSubmit={submit}>
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

function ProfileDialog({ user, profile, setProfile, onChange }) {
  const [err, setErr] = useState(null)
  const down = useRef(false)
  const set = (k, v) => setProfile((p) => ({ ...p, [k]: v }))
  const close = () => setProfile(null)
  const save = async () => {
    setProfile((p) => ({ ...p, busy: true })); setErr(null)
    try {
      const me = await updateProfile({ first_name: profile.first_name, last_name: profile.last_name, email: profile.email })
      onChange(me); setProfile(null)
    } catch (e) { setErr(e.data?.detail || 'Save failed'); setProfile((p) => ({ ...p, busy: false })) }
  }
  return (
    <div className="modal-backdrop"
         onMouseDown={(e) => { down.current = e.target === e.currentTarget }}
         onClick={(e) => { if (!profile.busy && down.current && e.target === e.currentTarget) close() }}>
      <div className="bake-dialog">
        <h3>Your profile</h3>
        <p className="hint">Signed in as <b>{user.username}</b>{user.is_staff ? ' ★ (staff)' : ''}.</p>
        <div className="u-row">
          <label className="bake-name">First name
            <input value={profile.first_name} autoFocus disabled={profile.busy}
                   onChange={(e) => set('first_name', e.target.value)} />
          </label>
          <label className="bake-name">Last name
            <input value={profile.last_name} disabled={profile.busy}
                   onChange={(e) => set('last_name', e.target.value)} />
          </label>
        </div>
        <label className="bake-name">Email
          <input type="email" value={profile.email} disabled={profile.busy}
                 onChange={(e) => set('email', e.target.value)} />
        </label>
        {err && <p className="login-err">{err}</p>}
        <div className="bake-actions">
          <button onClick={close} disabled={profile.busy}>Cancel</button>
          <button className="primary" onClick={save} disabled={profile.busy}>
            {profile.busy ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

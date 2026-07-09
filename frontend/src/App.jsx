/* global __APP_VERSION__ */
import { useEffect, useState } from 'react'
import { ReactFlowProvider } from '@xyflow/react'
import Editor from './Editor.jsx'
import Vault from './Vault.jsx'
import Proposals from './Proposals.jsx'
import Library from './Library.jsx'
import Users from './Users.jsx'
import LoginBar from './LoginBar.jsx'
import { whoami } from './api.js'

// Surfaces: Editor (build/bake/propose a graph) · Vault (baked Release hub) · Proposals (CI review).
// Baking drops you into the Vault; proposing drops you into Proposals.
export default function App() {
  const [view, setView] = useState('editor')
  const [vaultReleaseId, setVaultReleaseId] = useState(null)
  const [user, setUser] = useState(null)   // whoami payload; primes the CSRF cookie for writes
  const [sysOpen, setSysOpen] = useState(false)
  const goVault = (release) => { setVaultReleaseId(release?.id ?? null); setView('vault') }

  useEffect(() => { whoami().then(setUser).catch(() => setUser({ authenticated: false })) }, [])

  return (
    <div className="app">
      <nav className="topnav">
        <span className="brand">cdGTS<span className="brand-ver">v{__APP_VERSION__}</span></span>
        <button className={view === 'editor' ? 'active' : ''} onClick={() => setView('editor')}>Editor</button>
        <button className={view === 'vault' ? 'active' : ''} onClick={() => setView('vault')}>Vault</button>
        <button className={view === 'proposals' ? 'active' : ''} onClick={() => setView('proposals')}>Proposals</button>
        <button className={view === 'library' ? 'active' : ''} onClick={() => setView('library')}>Bibliography</button>
        {user?.is_staff && (
          <span className="tb-menu nav-menu">
            <button className={`tb-menu-btn${sysOpen ? ' open' : ''}${view === 'users' ? ' active' : ''}`}
                    onClick={() => setSysOpen((v) => !v)}>System ▾</button>
            {sysOpen && (
              <>
                <div className="tb-menu-backdrop" onClick={() => setSysOpen(false)} />
                <div className="tb-menu-list" role="menu">
                  <button role="menuitem" onClick={() => { setSysOpen(false); setView('users') }}>User management</button>
                </div>
              </>
            )}
          </span>
        )}
        <LoginBar user={user} onChange={setUser} />
      </nav>
      <div className="view">
        {view === 'editor'
          ? <ReactFlowProvider><Editor onBaked={goVault} onProposed={() => setView('proposals')} user={user} /></ReactFlowProvider>
          : view === 'vault'
            ? <Vault initialReleaseId={vaultReleaseId} user={user} />
            : view === 'library'
              ? <Library user={user} />
              : view === 'users'
                ? <Users user={user} />
                : <Proposals user={user} />}
      </div>
    </div>
  )
}

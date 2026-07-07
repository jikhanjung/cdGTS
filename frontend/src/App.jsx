/* global __APP_VERSION__ */
import { useEffect, useState } from 'react'
import { ReactFlowProvider } from '@xyflow/react'
import Editor from './Editor.jsx'
import Vault from './Vault.jsx'
import LoginBar from './LoginBar.jsx'
import { whoami } from './api.js'

// Two surfaces: Editor (build/bake a graph) and Vault (the artifact hub — view/compare baked Releases).
// Baking in the Editor drops you into the Vault on the fresh Release.
export default function App() {
  const [view, setView] = useState('editor')
  const [vaultReleaseId, setVaultReleaseId] = useState(null)
  const [user, setUser] = useState(null)   // whoami payload; primes the CSRF cookie for writes
  const goVault = (release) => { setVaultReleaseId(release?.id ?? null); setView('vault') }

  useEffect(() => { whoami().then(setUser).catch(() => setUser({ authenticated: false })) }, [])

  return (
    <div className="app">
      <nav className="topnav">
        <span className="brand">cdGTS<span className="brand-ver">v{__APP_VERSION__}</span></span>
        <button className={view === 'editor' ? 'active' : ''} onClick={() => setView('editor')}>Editor</button>
        <button className={view === 'vault' ? 'active' : ''} onClick={() => setView('vault')}>Vault</button>
        <LoginBar user={user} onChange={setUser} />
      </nav>
      <div className="view">
        {view === 'editor'
          ? <ReactFlowProvider><Editor onBaked={goVault} /></ReactFlowProvider>
          : <Vault initialReleaseId={vaultReleaseId} />}
      </div>
    </div>
  )
}

/* global __APP_VERSION__ */
import { useState } from 'react'
import { ReactFlowProvider } from '@xyflow/react'
import Editor from './Editor.jsx'
import ReleasesDiff from './ReleasesDiff.jsx'
import IccTable from './IccTable.jsx'
import IccChart from './IccChart.jsx'
import Narrate from './Narrate.jsx'

// Top nav switches between Editor / Releases Diff. The useReactFlow hook must be inside a Provider, so only Editor is wrapped.
export default function App() {
  const [view, setView] = useState('editor')
  return (
    <div className="app">
      <nav className="topnav">
        <span className="brand">cdGTS<span className="brand-ver">v{__APP_VERSION__}</span></span>
        <button className={view === 'editor' ? 'active' : ''} onClick={() => setView('editor')}>Editor</button>
        <button className={view === 'icc' ? 'active' : ''} onClick={() => setView('icc')}>ICC Table</button>
        <button className={view === 'chart' ? 'active' : ''} onClick={() => setView('chart')}>ICC Chart</button>
        <button className={view === 'narrate' ? 'active' : ''} onClick={() => setView('narrate')}>ICC Narrative</button>
        <button className={view === 'diff' ? 'active' : ''} onClick={() => setView('diff')}>Releases Diff</button>
      </nav>
      <div className="view">
        {view === 'editor'
          ? <ReactFlowProvider><Editor /></ReactFlowProvider>
          : view === 'icc'
            ? <IccTable />
            : view === 'chart'
              ? <IccChart />
              : view === 'narrate'
                ? <Narrate />
                : view === 'diff'
                  ? <ReleasesDiff />
                  : null}
      </div>
    </div>
  )
}

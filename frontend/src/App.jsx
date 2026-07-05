import { useState } from 'react'
import { ReactFlowProvider } from '@xyflow/react'
import Editor from './Editor.jsx'
import ReleasesDiff from './ReleasesDiff.jsx'
import IccTable from './IccTable.jsx'
import IccChart from './IccChart.jsx'
import Narrate from './Narrate.jsx'

// 상단 nav 로 에디터 / 릴리스 Diff 전환. useReactFlow 훅은 Provider 안이어야 하므로 Editor 만 감싼다.
export default function App() {
  const [view, setView] = useState('editor')
  return (
    <div className="app">
      <nav className="topnav">
        <span className="brand">cdGTS</span>
        <button className={view === 'editor' ? 'active' : ''} onClick={() => setView('editor')}>에디터</button>
        <button className={view === 'icc' ? 'active' : ''} onClick={() => setView('icc')}>ICC 테이블</button>
        <button className={view === 'chart' ? 'active' : ''} onClick={() => setView('chart')}>ICC 차트</button>
        <button className={view === 'narrate' ? 'active' : ''} onClick={() => setView('narrate')}>ICC 서술</button>
        <button className={view === 'diff' ? 'active' : ''} onClick={() => setView('diff')}>릴리스 Diff</button>
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

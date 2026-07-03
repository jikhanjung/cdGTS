import { ReactFlowProvider } from '@xyflow/react'
import Editor from './Editor.jsx'

// useReactFlow 훅을 쓰려면 Provider 안이어야 함.
export default function App() {
  return (
    <ReactFlowProvider>
      <Editor />
    </ReactFlowProvider>
  )
}

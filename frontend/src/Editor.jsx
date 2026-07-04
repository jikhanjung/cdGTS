import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ReactFlow, Background, Controls, MiniMap,
  addEdge, useNodesState, useEdgesState, useReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import CdgtsNode, { CATEGORY_COLOR } from './CdgtsNode.jsx'
import Inspector from './Inspector.jsx'
import {
  listNodeTypes, listGraphs, getGraph, createGraph, saveGraph, evaluateGraph,
} from './api.js'

const nodeTypes = { cdgts: CdgtsNode }

// --- API ↔ React Flow 변환 ---
function apiToRF(graph, typeMap) {
  const nodes = graph.nodes.map((n) => {
    const t = typeMap[n.node_type] || { category: 'process', ports: [] }
    return {
      id: n.key, type: 'cdgts', position: { x: n.x, y: n.y },
      data: { nodeType: n.node_type, label: n.label, params: n.params, category: t.category, ports: t.ports },
    }
  })
  const edges = graph.edges.map((e) => ({
    id: `${e.source}:${e.source_port}->${e.target}:${e.target_port}`,
    source: e.source, target: e.target,
    sourceHandle: e.source_port, targetHandle: e.target_port,
    data: { kind: e.kind },
  }))
  return { nodes, edges }
}

function rfToApi(nodes, edges, viewport) {
  return {
    viewport,
    nodes: nodes.map((n) => ({
      key: n.id, node_type: n.data.nodeType, label: n.data.label || '',
      params: n.data.params || {}, x: Math.round(n.position.x), y: Math.round(n.position.y),
    })),
    edges: edges.map((e) => ({
      source: e.source, source_port: e.sourceHandle,
      target: e.target, target_port: e.targetHandle, kind: e.data?.kind || 'data',
    })),
  }
}

export default function Editor() {
  const [types, setTypes] = useState([])
  const [graphs, setGraphs] = useState([])
  const [graphId, setGraphId] = useState(null)
  const [graphName, setGraphName] = useState('')
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [status, setStatus] = useState('로딩 중…')
  const [error, setError] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const wrapperRef = useRef(null)
  const { screenToFlowPosition, getViewport, setViewport } = useReactFlow()

  const typeMap = useMemo(() => Object.fromEntries(types.map((t) => [t.slug, t])), [types])

  // 초기 로드: 타입 → 그래프(없으면 생성).
  useEffect(() => {
    (async () => {
      try {
        const ts = await listNodeTypes()
        setTypes(ts)
        const tmap = Object.fromEntries(ts.map((t) => [t.slug, t]))
        let graphs = await listGraphs()
        let g = graphs[0]
        if (!g) { g = await createGraph({ slug: 'sandbox', name: 'Sandbox', nodes: [], edges: [], viewport: {} }); graphs = [g] }
        setGraphs(graphs)
        const full = await getGraph(g.id)
        setGraphId(full.id)
        setGraphName(full.name)
        const { nodes: rn, edges: re } = apiToRF(full, tmap)
        setNodes(rn)
        setEdges(re)
        if (full.viewport && full.viewport.zoom) setViewport(full.viewport)
        setStatus(`불러옴: ${full.name} (노드 ${rn.length})`)
      } catch (e) {
        setError(e.data || String(e))
        setStatus('로드 실패')
      }
    })()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const onConnect = useCallback(
    (c) => setEdges((eds) => addEdge({ ...c, data: { kind: 'data' } }, eds)),
    [setEdges],
  )

  const onDragOver = useCallback((e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    const slug = e.dataTransfer.getData('application/cdgts')
    const t = typeMap[slug]
    if (!t) return
    const position = screenToFlowPosition({ x: e.clientX, y: e.clientY })
    const key = `${slug}#${Math.random().toString(36).slice(2, 7)}`
    setNodes((nds) => nds.concat({
      id: key, type: 'cdgts', position,
      data: { nodeType: slug, label: '', params: {}, category: t.category, ports: t.ports },
    }))
  }, [screenToFlowPosition, typeMap, setNodes])

  const loadGraph = useCallback(async (id) => {
    setError(null)
    try {
      const full = await getGraph(id)
      setGraphId(full.id)
      setGraphName(full.name)
      const { nodes: rn, edges: re } = apiToRF(full, typeMap)
      setNodes(rn.map((n) => ({ ...n, data: { ...n.data, result: null } })))
      setEdges(re)
      if (full.viewport && full.viewport.zoom) setViewport(full.viewport)
      setStatus(`불러옴: ${full.name} (노드 ${rn.length})`)
    } catch (e) {
      setError(e.data || String(e))
      setStatus('로드 실패')
    }
  }, [typeMap, setNodes, setEdges, setViewport])

  const onSave = useCallback(async () => {
    setError(null)
    try {
      await saveGraph(graphId, rfToApi(nodes, edges, getViewport()))
      setStatus(`저장됨 · ${new Date().toLocaleTimeString()}`)
    } catch (e) {
      setError(e.data || String(e))
      setStatus('저장 실패 (검증 오류?)')
    }
  }, [graphId, nodes, edges, getViewport])

  const onEvaluate = useCallback(async () => {
    setError(null)
    try {
      const run = await evaluateGraph(graphId)
      const byKey = Object.fromEntries(run.results.map((r) => [r.node_key, r]))
      setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, result: byKey[n.id] || null } })))
      const cert = run.certificate
      setStatus(
        `평가 run#${run.id} · computed ${run.stats.computed} / cached ${run.stats.cached}` +
        (cert ? ` · 정합성 ${cert.passed ? 'pass' : 'warn'}` : ''),
      )
    } catch (e) {
      setError(e.data || String(e))
    }
  }, [graphId, setNodes])

  // --- 선택 노드 속성 편집 (Inspector) ---
  const patchNodeData = useCallback((id, fn) => {
    setNodes((nds) => nds.map((n) => (n.id === id ? { ...n, data: fn(n.data) } : n)))
  }, [setNodes])

  const onLabel = useCallback((id, label) => {
    patchNodeData(id, (d) => ({ ...d, label }))
  }, [patchNodeData])

  const onParam = useCallback((id, key, value) => {
    patchNodeData(id, (d) => {
      const params = { ...(d.params || {}) }
      if (value === undefined) delete params[key]; else params[key] = value
      return { ...d, params }
    })
  }, [patchNodeData])

  const onDist = useCallback((id, key, subKey, value) => {
    patchNodeData(id, (d) => {
      const params = { ...(d.params || {}) }
      const dist = { ...(params[key] || {}) }
      if (subKey.startsWith('budget.')) {
        const bk = subKey.slice('budget.'.length)
        const budget = { ...(dist.budget || {}) }
        if (value === undefined) delete budget[bk]; else budget[bk] = value
        if (Object.keys(budget).length) dist.budget = budget; else delete dist.budget
      } else if (value === undefined) {
        delete dist[subKey]
      } else {
        dist[subKey] = value
      }
      params[key] = dist
      return { ...d, params }
    })
  }, [patchNodeData])

  const onReplaceParams = useCallback((id, params) => {
    patchNodeData(id, (d) => ({ ...d, params }))
  }, [patchNodeData])

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedId) || null,
    [nodes, selectedId],
  )
  const nodeKeys = useMemo(
    () => nodes.filter((n) => n.id !== selectedId)
      .map((n) => ({ id: n.id, label: n.data.label || n.data.nodeType })),
    [nodes, selectedId],
  )

  const grouped = useMemo(() => {
    const g = { data: [], process: [], clamp: [] }
    types.forEach((t) => (g[t.category] || (g[t.category] = [])).push(t))
    return g
  }, [types])

  return (
    <div className="editor">
      <aside className="palette">
        <h1>cdGTS</h1>
        <p className="hint">노드를 캔버스로 드래그</p>
        {['data', 'process', 'clamp'].map((cat) => (
          <div key={cat} className="palette-group">
            <h2 style={{ color: CATEGORY_COLOR[cat] }}>{cat}</h2>
            {(grouped[cat] || []).map((t) => (
              <div
                key={t.slug}
                className="palette-item"
                draggable
                onDragStart={(e) => {
                  e.dataTransfer.setData('application/cdgts', t.slug)
                  e.dataTransfer.effectAllowed = 'move'
                }}
                title={t.description}
                style={{ borderLeftColor: CATEGORY_COLOR[cat] }}
              >
                {t.name}
              </div>
            ))}
          </div>
        ))}
      </aside>

      <main className="canvas" ref={wrapperRef}>
        <div className="toolbar">
          <select
            className="graph-select"
            value={graphId || ''}
            onChange={(e) => loadGraph(Number(e.target.value))}
            title="그래프 선택"
          >
            {graphs.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
          </select>
          <button onClick={onSave}>저장 (PUT)</button>
          <button onClick={onEvaluate}>평가</button>
          <span className="status">{status}</span>
        </div>
        {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}
        <div className="flow" onDrop={onDrop} onDragOver={onDragOver}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onSelectionChange={({ nodes: sel }) => setSelectedId(sel[0]?.id ?? null)}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap pannable zoomable />
          </ReactFlow>
        </div>
      </main>

      <Inspector
        key={selectedNode?.id || 'none'}
        node={selectedNode}
        type={selectedNode ? typeMap[selectedNode.data.nodeType] : null}
        nodeKeys={nodeKeys}
        onLabel={(v) => onLabel(selectedNode.id, v)}
        onParam={(k, v) => onParam(selectedNode.id, k, v)}
        onDist={(k, sk, v) => onDist(selectedNode.id, k, sk, v)}
        onReplaceParams={(p) => onReplaceParams(selectedNode.id, p)}
      />
    </div>
  )
}

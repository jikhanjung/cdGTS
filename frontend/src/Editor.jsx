import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ReactFlow, Background, Controls, MiniMap, SelectionMode,
  applyNodeChanges, applyEdgeChanges, useNodesState, useEdgesState, useReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import CdgtsNode, { CATEGORY_COLOR } from './CdgtsNode.jsx'
import { GroupNode, StubNode } from './GroupNode.jsx'
import OrderNode from './OrderNode.jsx'
import Inspector from './Inspector.jsx'
import ResultsPanel from './ResultsPanel.jsx'
import {
  listNodeTypes, listGraphs, getGraph, createGraph, saveGraph, evaluateGraph,
} from './api.js'

const nodeTypes = { cdgts: CdgtsNode, cdgtsGroup: GroupNode, cdgtsStub: StubNode, cdgtsOrder: OrderNode }
const DEFAULT_NODE_WIDTH = 172   // 기본 폭(px). 사용자가 우측 핸들로 조정 가능.

// 주 포인터가 터치(폰/태블릿)인가 — 팬/선택 상호작용을 다르게(터치=드래그 팬·핀치줌).
const IS_TOUCH = typeof window !== 'undefined' && typeof window.matchMedia === 'function'
  && window.matchMedia('(pointer: coarse)').matches

// 노드타입 slug → React Flow 노드 컴포넌트 종류. order 는 세로 핸들 전용 컴포넌트.
const rfType = (slug) => (slug === 'order' ? 'cdgtsOrder' : 'cdgts')
const isRealNode = (t) => t === 'cdgts' || t === 'cdgtsOrder'

// --- API ↔ React Flow 변환 (nodes/edges 는 항상 '전체 실제' 집합; 뷰는 buildView 로 파생) ---
function apiToRF(graph, typeMap) {
  const nodes = graph.nodes.map((n) => {
    const t = typeMap[n.node_type] || { category: 'process', ports: [] }
    return {
      id: n.key, type: rfType(n.node_type), position: { x: n.x, y: n.y },
      width: n.width || DEFAULT_NODE_WIDTH,
      data: {
        nodeType: n.node_type, label: n.label, description: n.description || '',
        params: n.params, category: t.category, ports: t.ports, group: n.group || null,
      },
    }
  })
  const edges = graph.edges.map((e) => ({
    id: `${e.source}:${e.source_port}->${e.target}:${e.target_port}`,
    source: e.source, target: e.target,
    sourceHandle: e.source_port, targetHandle: e.target_port,
    data: { kind: e.kind },
  }))
  const groups = (graph.groups || []).map((g) => ({ ...g }))
  return { nodes, edges, groups }
}

function rfToApi(nodes, edges, groups, viewport) {
  return {
    viewport,
    nodes: nodes.map((n) => ({
      key: n.id, node_type: n.data.nodeType, label: n.data.label || '',
      description: n.data.description || '',
      params: n.data.params || {}, x: Math.round(n.position.x), y: Math.round(n.position.y),
      width: n.width ? Math.round(n.width) : null, group: n.data.group || null,
    })),
    edges: edges.map((e) => ({
      source: e.source, source_port: e.sourceHandle,
      target: e.target, target_port: e.targetHandle, kind: e.data?.kind || 'data',
    })),
    groups: groups.map((g) => ({
      key: g.key, name: g.name, collapsed: !!g.collapsed,
      x: Math.round(g.x), y: Math.round(g.y),
    })),
  }
}

// (nodes, edges, groups, activeGroup) → ReactFlow 에 넘길 {viewNodes, viewEdges}.
// 최상위: 그룹은 접힌 노드(경계 넘는 엣지 = 자동 입출력 핸들). 드릴인: 멤버 + 경계 스텁.
function buildView(nodes, edges, groups, activeGroup, labelMap, selGroups) {
  const groupOf = Object.fromEntries(nodes.map((n) => [n.id, n.data.group || null]))
  const lab = (id, port) => `${labelMap[id] || id}·${port}`

  if (activeGroup) {
    const members = nodes.filter((n) => n.data.group === activeGroup)
    const memberSet = new Set(members.map((n) => n.id))
    const viewNodes = [...members]
    const viewEdges = []
    const stubSeen = new Set()
    let ins = 0, outs = 0
    edges.forEach((e) => {
      const sIn = memberSet.has(e.source), tIn = memberSet.has(e.target)
      if (sIn && tIn) { viewEdges.push({ ...e, id: `v-${e.id}` }); return }
      if (tIn && !sIn) {
        // 그룹 입력 포트 = 멤버 쪽(e.target·targetHandle), 출처 = 외부(e.source·sourceHandle). 연결별 스텁.
        const sid = `stub-in:${e.source}:${e.sourceHandle}:${e.target}:${e.targetHandle}`
        if (!stubSeen.has(sid)) {
          stubSeen.add(sid)
          viewNodes.push({ id: sid, type: 'cdgtsStub', position: { x: -280, y: ins * 64 },
            data: { dir: 'in', port: lab(e.target, e.targetHandle), peer: lab(e.source, e.sourceHandle) },
            draggable: false, selectable: false })
          ins++
        }
        viewEdges.push({ ...e, id: `v-${e.id}`, source: sid, sourceHandle: 'out' })
      } else if (sIn && !tIn) {
        // 그룹 출력 포트 = 멤버 쪽(e.source·sourceHandle), 도착 = 외부(e.target·targetHandle). 연결별 스텁.
        const sid = `stub-out:${e.source}:${e.sourceHandle}:${e.target}:${e.targetHandle}`
        if (!stubSeen.has(sid)) {
          stubSeen.add(sid)
          viewNodes.push({ id: sid, type: 'cdgtsStub', position: { x: 760, y: outs * 64 },
            data: { dir: 'out', port: lab(e.source, e.sourceHandle), peer: lab(e.target, e.targetHandle) },
            draggable: false, selectable: false })
          outs++
        }
        viewEdges.push({ ...e, id: `v-${e.id}`, target: sid, targetHandle: 'in' })
      }
    })
    return { viewNodes, viewEdges }
  }

  // 최상위
  const viewNodes = nodes.filter((n) => !n.data.group)
  const groupById = {}
  groups.forEach((g) => {
    const gn = { id: `group:${g.key}`, type: 'cdgtsGroup', position: { x: g.x, y: g.y },
      selected: !!selGroups && selGroups.has(g.key),
      data: { key: g.key, name: g.name, inputs: [], outputs: [], count: 0 } }
    groupById[g.key] = gn
    viewNodes.push(gn)
  })
  nodes.forEach((n) => { if (n.data.group && groupById[n.data.group]) groupById[n.data.group].data.count++ })

  const viewEdges = []
  edges.forEach((e) => {
    const sg = groupOf[e.source], tg = groupOf[e.target]
    if (sg && tg && sg === tg) return          // 그룹 내부 엣지 → 최상위에선 숨김
    let src = e.source, srcH = e.sourceHandle, tgt = e.target, tgtH = e.targetHandle
    if (sg && groupById[sg]) {
      const hid = `out:${e.source}:${e.sourceHandle}`
      if (!groupById[sg].data.outputs.find((h) => h.id === hid))
        groupById[sg].data.outputs.push({ id: hid, port: e.sourceHandle, label: lab(e.source, e.sourceHandle) })
      src = `group:${sg}`; srcH = hid
    }
    if (tg && groupById[tg]) {
      const hid = `in:${e.target}:${e.targetHandle}`
      if (!groupById[tg].data.inputs.find((h) => h.id === hid))
        groupById[tg].data.inputs.push({ id: hid, port: e.targetHandle, label: lab(e.target, e.targetHandle) })
      tgt = `group:${tg}`; tgtH = hid
    }
    viewEdges.push({ ...e, id: `v-${e.id}`, source: src, sourceHandle: srcH, target: tgt, targetHandle: tgtH })
  })
  return { viewNodes, viewEdges }
}

export default function Editor() {
  const [types, setTypes] = useState([])
  const [graphs, setGraphs] = useState([])
  const [graphId, setGraphId] = useState(null)
  const [graphName, setGraphName] = useState('')
  const [nodes, setNodes] = useNodesState([])       // 전체 실제 노드
  const [edges, setEdges] = useEdgesState([])       // 전체 실제 엣지
  const [groups, setGroups] = useState([])          // 그룹 메타 [{key,name,collapsed,x,y}]
  const [activeGroup, setActiveGroup] = useState(null)   // null=최상위 / 그룹 key=드릴인
  const [status, setStatus] = useState('로딩 중…')
  const [error, setError] = useState(null)
  const [selectedIds, setSelectedIds] = useState([])          // 선택된 실제 노드
  const [selectedGroupKeys, setSelectedGroupKeys] = useState([])  // 선택된 그룹(접힌 노드)
  const [menu, setMenu] = useState(null)   // 우클릭 컨텍스트 메뉴 {x,y,kind,id?,groupKey?}
  const [gateways, setGateways] = useState([])
  const [outputs, setOutputs] = useState([])
  const [runMeta, setRunMeta] = useState(null)
  const [showResults, setShowResults] = useState(false)
  const [paletteOpen, setPaletteOpen] = useState(false)     // 폰: 팔레트 서랍
  const [inspectorOpen, setInspectorOpen] = useState(false) // 폰: 인스펙터 서랍
  const wrapperRef = useRef(null)
  const { screenToFlowPosition, getViewport, setViewport, fitView } = useReactFlow()

  const typeMap = useMemo(() => Object.fromEntries(types.map((t) => [t.slug, t])), [types])
  const labelMap = useMemo(
    () => Object.fromEntries(nodes.map((n) => [n.id, n.data.label || n.data.nodeType])),
    [nodes],
  )
  const { viewNodes, viewEdges } = useMemo(
    () => buildView(nodes, edges, groups, activeGroup, labelMap, new Set(selectedGroupKeys)),
    [nodes, edges, groups, activeGroup, labelMap, selectedGroupKeys],
  )

  const hydrate = useCallback((full, tmap) => {
    setGraphId(full.id)
    setGraphName(full.name)
    const { nodes: rn, edges: re, groups: rg } = apiToRF(full, tmap)
    setNodes(rn)
    setEdges(re)
    setGroups(rg)
    setActiveGroup(null)
    setSelectedIds([])
    setGateways(full.gateways || [])
    setOutputs([])
    setRunMeta(null)
    if (full.viewport && full.viewport.zoom) setViewport(full.viewport)
    setStatus(`불러옴: ${full.name} (노드 ${rn.length}${rg.length ? ` · 그룹 ${rg.length}` : ''})`)
  }, [setNodes, setEdges, setViewport])

  useEffect(() => {
    (async () => {
      try {
        const ts = await listNodeTypes()
        setTypes(ts)
        const tmap = Object.fromEntries(ts.map((t) => [t.slug, t]))
        let gs = await listGraphs()
        let g = gs[0]
        if (!g) { g = await createGraph({ slug: 'sandbox', name: 'Sandbox', nodes: [], edges: [], viewport: {} }); gs = [g] }
        setGraphs(gs)
        hydrate(await getGraph(g.id), tmap)
      } catch (e) { setError(e.data || String(e)); setStatus('로드 실패') }
    })()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const loadGraph = useCallback(async (id) => {
    setError(null)
    try { hydrate(await getGraph(id), typeMap) }
    catch (e) { setError(e.data || String(e)); setStatus('로드 실패') }
  }, [typeMap, hydrate])

  // 뷰 → 실제 상태 매핑. 실제 노드 변경만 반영, 그룹 노드는 위치만, 스텁은 무시.
  const onNodesChange = useCallback((changes) => {
    const real = []
    const gpos = []
    changes.forEach((c) => {
      const id = c.id
      if (id && id.startsWith('group:')) { if (c.type === 'position' && c.position) gpos.push({ key: id.slice(6), pos: c.position }) }
      else if (id && id.startsWith('stub-')) { /* 무시 */ }
      else real.push(c)
    })
    if (real.length) setNodes((nds) => applyNodeChanges(real, nds))
    if (gpos.length) setGroups((gs) => gs.map((g) => {
      const p = gpos.find((x) => x.key === g.key)
      return p ? { ...g, x: Math.round(p.pos.x), y: Math.round(p.pos.y) } : g
    }))
  }, [setNodes])

  const onEdgesChange = useCallback((changes) => {
    const real = changes.map((c) => (c.id && c.id.startsWith('v-') ? { ...c, id: c.id.slice(2) } : c))
    setEdges((eds) => applyEdgeChanges(real, eds))
  }, [setEdges])

  const onConnect = useCallback((c) => {
    let { source, sourceHandle, target, targetHandle } = c
    // 그룹 포트(접힌 노드의 위/아래 order 포트 등)에서/로 그리면 → 멤버 노드의 실제 포트로 환원.
    // 그룹 핸들 id 규약(buildView): 출력 `out:<member>:<port>` · 입력 `in:<member>:<port>`.
    if (source?.startsWith('group:') && sourceHandle?.startsWith('out:')) {
      const [, m, p] = sourceHandle.split(':'); source = m; sourceHandle = p
    }
    if (target?.startsWith('group:') && targetHandle?.startsWith('in:')) {
      const [, m, p] = targetHandle.split(':'); target = m; targetHandle = p
    }
    if (['group:', 'stub-'].some((p) => source?.startsWith(p) || target?.startsWith(p))) return
    const id = `${source}:${sourceHandle}->${target}:${targetHandle}`
    setEdges((eds) => eds.concat({
      id, source, target, sourceHandle, targetHandle, data: { kind: 'data' },
    }))
  }, [setEdges])

  const onDragOver = useCallback((e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move' }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    const slug = e.dataTransfer.getData('application/cdgts')
    const t = typeMap[slug]
    if (!t) return
    const position = screenToFlowPosition({ x: e.clientX, y: e.clientY })
    const key = `${slug}#${Math.random().toString(36).slice(2, 7)}`
    setNodes((nds) => nds.concat({
      id: key, type: rfType(slug), position, width: DEFAULT_NODE_WIDTH,
      data: { nodeType: slug, label: '', description: '', params: {}, category: t.category, ports: t.ports, group: activeGroup || null },
    }))
  }, [screenToFlowPosition, typeMap, setNodes, activeGroup])

  // --- 그룹 만들기 · 병합 / 해제 / 드릴인 ---
  // 실제 노드 + 그룹(접힌 노드)을 하나로. 그룹이 섞이면 그 멤버까지 흡수해 **병합**(단일 계층 유지),
  // 나머지 선택 그룹은 대상 그룹으로 합쳐지며 사라진다.
  const createOrMergeGroup = useCallback((realIds, groupKeys) => {
    if (activeGroup) return
    const memberIds = nodes.filter((n) => n.data.group && groupKeys.includes(n.data.group)).map((n) => n.id)
    const allIds = [...new Set([...realIds, ...memberIds])]
    if (!allIds.length) return
    const merging = groupKeys.length > 0
    let key, name
    if (merging) {
      key = groupKeys[0]
      name = groups.find((g) => g.key === key)?.name || key
    } else {
      key = `grp-${Math.random().toString(36).slice(2, 7)}`
      name = (window.prompt('그룹 이름', `Group ${groups.length + 1}`) || '').trim() || `Group ${groups.length + 1}`
    }
    const drop = new Set(groupKeys.slice(1))   // 대상으로 합쳐지며 사라지는 다른 그룹들
    const mem = nodes.filter((n) => allIds.includes(n.id))
    const cx = Math.round(mem.reduce((s, n) => s + n.position.x, 0) / mem.length)
    const cy = Math.round(mem.reduce((s, n) => s + n.position.y, 0) / mem.length)
    setNodes((nds) => nds.map((n) => (allIds.includes(n.id) ? { ...n, data: { ...n.data, group: key } } : n)))
    setGroups((gs) => {
      const next = gs.filter((g) => !drop.has(g.key))
      return merging ? next : next.concat({ key, name, collapsed: true, x: cx, y: cy })
    })
    setSelectedIds([]); setSelectedGroupKeys([])
    setStatus(`그룹 '${name}' ${merging ? '병합' : '생성'} (${allIds.length} 노드)`)
  }, [activeGroup, groups, nodes, setNodes])

  const onCreateGroup = useCallback(
    () => createOrMergeGroup(selectedIds, selectedGroupKeys),
    [createOrMergeGroup, selectedIds, selectedGroupKeys],
  )

  const removeFromGroup = useCallback((id) => {
    setNodes((nds) => nds.map((n) => (n.id === id ? { ...n, data: { ...n.data, group: null } } : n)))
    setStatus('노드를 그룹에서 뺐음')
  }, [setNodes])

  // 우클릭 대상 노드가 선택에 없으면 그 노드만, 있으면 현재 선택 전체를 그룹 대상으로.
  const groupTargets = useCallback((id) => {
    if (id && !selectedIds.includes(id)) return [id]
    return selectedIds.length ? selectedIds : (id ? [id] : [])
  }, [selectedIds])

  const closeMenu = useCallback(() => setMenu(null), [])
  const onNodeContextMenu = useCallback((e, node) => {
    e.preventDefault()
    if (node.type === 'cdgtsGroup') setMenu({ x: e.clientX, y: e.clientY, kind: 'group', groupKey: node.data.key })
    else if (isRealNode(node.type)) setMenu({ x: e.clientX, y: e.clientY, kind: 'node', id: node.id })
  }, [])
  const onPaneContextMenu = useCallback((e) => {
    e.preventDefault()
    setMenu({ x: e.clientX, y: e.clientY, kind: 'pane' })
  }, [])

  const onUngroup = useCallback((key) => {
    setNodes((nds) => nds.map((n) => (n.data.group === key ? { ...n, data: { ...n.data, group: null } } : n)))
    setGroups((gs) => gs.filter((g) => g.key !== key))
    if (activeGroup === key) setActiveGroup(null)
    setSelectedGroupKeys((ks) => ks.filter((k) => k !== key))
    setStatus('그룹 해제됨')
  }, [setNodes, activeGroup])

  const onUngroupSelected = useCallback(() => selectedGroupKeys.forEach(onUngroup), [selectedGroupKeys, onUngroup])

  const onNodeDoubleClick = useCallback((_e, node) => {
    if (node.type === 'cdgtsGroup') { setActiveGroup(node.data.key); setSelectedIds([]); setSelectedGroupKeys([]) }
  }, [])

  // 컨텍스트 전환 시 fit
  useEffect(() => { const id = setTimeout(() => fitView({ duration: 200 }), 0); return () => clearTimeout(id) }, [activeGroup, fitView])

  const onSelectionChange = useCallback(({ nodes: sel }) => {
    setSelectedIds(sel.filter((n) => isRealNode(n.type)).map((n) => n.id))
    setSelectedGroupKeys(sel.filter((n) => n.type === 'cdgtsGroup').map((n) => n.data.key))
  }, [])

  const onSave = useCallback(async () => {
    setError(null)
    try {
      await saveGraph(graphId, rfToApi(nodes, edges, groups, getViewport()))
      setStatus(`저장됨 · ${new Date().toLocaleTimeString()}`)
    } catch (e) { setError(e.data || String(e)); setStatus('저장 실패 (검증 오류?)') }
  }, [graphId, nodes, edges, groups, getViewport])

  const onEvaluate = useCallback(async () => {
    setError(null)
    try {
      const run = await evaluateGraph(graphId)
      const byKey = Object.fromEntries(run.results.map((r) => [r.node_key, r]))
      setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, result: byKey[n.id] || null } })))

      let rows
      if (gateways.length) {
        rows = gateways.map((gw) => ({ id: gw.node, title: gw.name || gw.node, boundary: gw.boundary, source: 'gateway' }))
      } else {
        const hasOut = new Set(edges.map((e) => e.source))
        rows = nodes.filter((n) => !hasOut.has(n.id))
          .map((n) => ({ id: n.id, title: n.data.label || n.data.nodeType, boundary: null, source: 'sink' }))
      }
      setOutputs(rows.map((r) => {
        const res = byKey[r.id]
        return { ...r, dist: res?.distribution || null, provenance: res?.provenance || [], missing: !res }
      }))
      setRunMeta({ id: run.id, stats: run.stats, certificate: run.certificate })
      setShowResults(true)
      const cert = run.certificate
      setStatus(`평가 run#${run.id} · computed ${run.stats.computed} / cached ${run.stats.cached}`
        + (cert ? ` · 정합성 ${cert.passed ? 'pass' : 'warn'}` : ''))
    } catch (e) { setError(e.data || String(e)) }
  }, [graphId, setNodes, gateways, nodes, edges])

  // --- Inspector (선택 실제 노드) ---
  const patchNodeData = useCallback((id, fn) => {
    setNodes((nds) => nds.map((n) => (n.id === id ? { ...n, data: fn(n.data) } : n)))
  }, [setNodes])
  const onLabel = useCallback((id, label) => patchNodeData(id, (d) => ({ ...d, label })), [patchNodeData])
  const onDescription = useCallback((id, description) => patchNodeData(id, (d) => ({ ...d, description })), [patchNodeData])
  const onParam = useCallback((id, key, value) => patchNodeData(id, (d) => {
    const params = { ...(d.params || {}) }
    if (value === undefined) delete params[key]; else params[key] = value
    return { ...d, params }
  }), [patchNodeData])
  const onDist = useCallback((id, key, subKey, value) => patchNodeData(id, (d) => {
    const params = { ...(d.params || {}) }
    const dist = { ...(params[key] || {}) }
    if (subKey.startsWith('budget.')) {
      const bk = subKey.slice('budget.'.length)
      const budget = { ...(dist.budget || {}) }
      if (value === undefined) delete budget[bk]; else budget[bk] = value
      if (Object.keys(budget).length) dist.budget = budget; else delete dist.budget
    } else if (value === undefined) { delete dist[subKey] } else { dist[subKey] = value }
    params[key] = dist
    return { ...d, params }
  }), [patchNodeData])
  const onReplaceParams = useCallback((id, params) => patchNodeData(id, (d) => ({ ...d, params })), [patchNodeData])

  const selectedId = selectedIds[0] ?? null
  const selectedNode = useMemo(() => nodes.find((n) => n.id === selectedId) || null, [nodes, selectedId])
  const nodeKeys = useMemo(
    () => nodes.filter((n) => n.id !== selectedId).map((n) => ({ id: n.id, label: n.data.label || n.data.nodeType })),
    [nodes, selectedId],
  )

  const grouped = useMemo(() => {
    const g = { data: [], process: [], clamp: [] }
    types.forEach((t) => (g[t.category] || (g[t.category] = [])).push(t))
    return g
  }, [types])

  const activeGroupObj = groups.find((g) => g.key === activeGroup)

  return (
    <div className="editor">
      {(paletteOpen || inspectorOpen) && (
        <div className="drawer-backdrop" onClick={() => { setPaletteOpen(false); setInspectorOpen(false) }} />
      )}
      <aside className={`palette${paletteOpen ? ' open' : ''}`}>
        <h1>cdGTS</h1>
        <p className="hint">노드를 캔버스로 드래그</p>
        {['data', 'process', 'clamp'].map((cat) => (
          <div key={cat} className="palette-group">
            <h2 style={{ color: CATEGORY_COLOR[cat] }}>{cat}</h2>
            {(grouped[cat] || []).map((t) => (
              <div key={t.slug} className="palette-item" draggable
                   onDragStart={(e) => { e.dataTransfer.setData('application/cdgts', t.slug); e.dataTransfer.effectAllowed = 'move' }}
                   title={t.description} style={{ borderLeftColor: CATEGORY_COLOR[cat] }}>
                {t.name}
              </div>
            ))}
          </div>
        ))}
      </aside>

      <main className="canvas" ref={wrapperRef}>
        <div className="toolbar">
          <button className="mobile-only drawer-toggle" onClick={() => { setPaletteOpen((v) => !v); setInspectorOpen(false) }} title="팔레트">☰</button>
          <select className="graph-select" value={graphId || ''} onChange={(e) => loadGraph(Number(e.target.value))} title="그래프 선택">
            {graphs.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
          </select>
          <button onClick={onSave}>저장 (PUT)</button>
          <button onClick={onEvaluate}>평가</button>
          {!activeGroup && (
            <button onClick={onCreateGroup}
                    disabled={!(selectedIds.length || selectedGroupKeys.length >= 2)}
                    title="선택한 노드·그룹을 하나의 그룹으로 (그룹이 섞이면 병합)">
              {selectedGroupKeys.length ? '그룹 병합' : '그룹 만들기'}
              {(selectedIds.length + selectedGroupKeys.length) ? ` (${selectedIds.length + selectedGroupKeys.length})` : ''}
            </button>
          )}
          {!activeGroup && selectedGroupKeys.length > 0 && (
            <button onClick={onUngroupSelected} title="선택한 그룹 해제">
              그룹 해제{selectedGroupKeys.length > 1 ? ` (${selectedGroupKeys.length})` : ''}
            </button>
          )}
          <button onClick={() => setShowResults((v) => !v)} className={showResults ? 'active' : ''} disabled={!runMeta} title="최종 노드 출력 보기">
            결과{outputs.length ? ` (${outputs.length})` : ''}
          </button>
          <button className="mobile-only drawer-toggle" onClick={() => { setInspectorOpen((v) => !v); setPaletteOpen(false) }} title="속성"
                  disabled={!selectedNode}>속성</button>
          <span className="status">{status}</span>
        </div>

        {(activeGroup || groups.length > 0) && (
          <div className="breadcrumb">
            <button className={activeGroup ? 'link' : 'link cur'} onClick={() => setActiveGroup(null)}>{graphName || 'graph'}</button>
            {activeGroup && (
              <>
                <span className="sep">›</span>
                <span className="cur">▤ {activeGroupObj?.name || activeGroup}</span>
                <span className="bc-hint">그룹 내부 — 멤버 편집 · 좌우 스텁 = 외부 입출력</span>
                <button className="ungroup" onClick={() => onUngroup(activeGroup)}>그룹 해제</button>
              </>
            )}
            {!activeGroup && <span className="bc-hint">그룹 더블클릭 → 내부 편집</span>}
          </div>
        )}

        {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}
        <div className="flow" onDrop={onDrop} onDragOver={onDragOver}>
          <ReactFlow
            nodes={viewNodes}
            edges={viewEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onSelectionChange={onSelectionChange}
            onNodeDoubleClick={onNodeDoubleClick}
            onNodeContextMenu={onNodeContextMenu}
            onPaneContextMenu={onPaneContextMenu}
            onPaneClick={closeMenu}
            nodeTypes={nodeTypes}
            selectionOnDrag={!IS_TOUCH}          // 데스크톱: 좌-드래그 = 선택 박스
            panOnDrag={IS_TOUCH ? true : [1]}    // 터치: 드래그 팬 / 데스크톱: 가운데버튼
            zoomOnPinch                          // 터치: 핀치 줌
            selectionMode={SelectionMode.Partial}
            multiSelectionKeyCode="Shift"        // Shift+클릭 = 추가 선택
            fitView
          >
            <Background />
            <Controls />
            <MiniMap pannable zoomable />
          </ReactFlow>
        </div>
        {showResults && <ResultsPanel outputs={outputs} meta={runMeta} onClose={() => setShowResults(false)} />}

        {menu && (
          <>
            <div className="ctx-backdrop" onClick={closeMenu}
                 onContextMenu={(e) => { e.preventDefault(); closeMenu() }} />
            <ul className="ctx-menu" style={{ left: menu.x, top: menu.y }}>
              {menu.kind === 'node' && !activeGroup && (
                <li onClick={() => { createOrMergeGroup(groupTargets(menu.id), selectedGroupKeys); closeMenu() }}>
                  {selectedGroupKeys.length ? '선택과 그룹 병합' : '선택 노드 그룹으로 묶기'} ({groupTargets(menu.id).length + selectedGroupKeys.length})
                </li>
              )}
              {menu.kind === 'node' && activeGroup && (
                <li onClick={() => { removeFromGroup(menu.id); closeMenu() }}>그룹에서 빼기</li>
              )}
              {menu.kind === 'group' && (
                <>
                  <li onClick={() => { setActiveGroup(menu.groupKey); closeMenu() }}>그룹 열기</li>
                  {(selectedIds.length || selectedGroupKeys.filter((k) => k !== menu.groupKey).length) > 0 && (
                    <li onClick={() => {
                      createOrMergeGroup(selectedIds, [menu.groupKey, ...selectedGroupKeys.filter((k) => k !== menu.groupKey)])
                      closeMenu()
                    }}>이 그룹에 선택 병합 ({selectedIds.length + selectedGroupKeys.filter((k) => k !== menu.groupKey).length})</li>
                  )}
                  <li onClick={() => { onUngroup(menu.groupKey); closeMenu() }}>그룹 해제</li>
                </>
              )}
              {menu.kind === 'pane' && !activeGroup && (
                (selectedIds.length || selectedGroupKeys.length >= 2)
                  ? <li onClick={() => { createOrMergeGroup(selectedIds, selectedGroupKeys); closeMenu() }}>
                      {selectedGroupKeys.length ? '선택 그룹·노드 병합' : '선택 노드 그룹으로 묶기'} ({selectedIds.length + selectedGroupKeys.length})
                    </li>
                  : <li className="disabled">노드/그룹을 선택한 뒤 우클릭</li>
              )}
              {menu.kind === 'pane' && activeGroup && (
                <li onClick={() => { setActiveGroup(null); closeMenu() }}>상위로 나가기</li>
              )}
            </ul>
          </>
        )}
      </main>

      <Inspector
        key={selectedNode?.id || 'none'}
        open={inspectorOpen}
        onClose={() => setInspectorOpen(false)}
        node={selectedNode}
        type={selectedNode ? typeMap[selectedNode.data.nodeType] : null}
        nodeKeys={nodeKeys}
        onLabel={(v) => onLabel(selectedNode.id, v)}
        onDescription={(v) => onDescription(selectedNode.id, v)}
        onParam={(k, v) => onParam(selectedNode.id, k, v)}
        onDist={(k, sk, v) => onDist(selectedNode.id, k, sk, v)}
        onReplaceParams={(p) => onReplaceParams(selectedNode.id, p)}
      />
    </div>
  )
}

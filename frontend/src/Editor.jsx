import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ReactFlow, Background, Controls, MiniMap, Panel, SelectionMode,
  applyNodeChanges, applyEdgeChanges, useNodesState, useEdgesState, useReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import CdgtsNode, { CATEGORY_COLOR } from './CdgtsNode.jsx'
import { GroupNode, StubNode } from './GroupNode.jsx'
import GroupIoNode from './GroupIoNode.jsx'
import BoundNode from './BoundNode.jsx'
import OrderNode from './OrderNode.jsx'
import Inspector from './Inspector.jsx'
import ResultsPanel from './ResultsPanel.jsx'
import VerifyPanel from './VerifyPanel.jsx'
import {
  listNodeTypes, listGraphs, getGraph, createGraph, saveGraph, evaluateGraph, verifyGraph,
} from './api.js'

const nodeTypes = { cdgts: CdgtsNode, cdgtsGroup: GroupNode, cdgtsStub: StubNode,
  cdgtsGroupIo: GroupIoNode, cdgtsBound: BoundNode, cdgtsOrder: OrderNode }
const DEFAULT_NODE_WIDTH = 172   // Default width (px). User can adjust via the right handle.

// Is the primary pointer touch (phone/tablet)? — pan/selection interactions differ (touch = drag pan · pinch zoom).
const IS_TOUCH = typeof window !== 'undefined' && typeof window.matchMedia === 'function'
  && window.matchMedia('(pointer: coarse)').matches

// node type slug → React Flow node component kind. order is a vertical-handle-only component.
const rfType = (slug) => (slug === 'order' ? 'cdgtsOrder' : 'cdgts')
const isRealNode = (t) => t === 'cdgts' || t === 'cdgtsOrder'
// order nodes are fixed at 40px via CSS (.order-node). Giving an explicit width makes React Flow compute bounds·hit-test
// with that value, so selection is judged wider than the on-screen 40px → omit width so the measured (40px) is used. data/process
// use .cdgts-node{width:100%}, so the wrapper needs a width; give them the default width.
const nodeWidth = (slug, w) => (rfType(slug) === 'cdgtsOrder' ? undefined : (w || DEFAULT_NODE_WIDTH))

// order edge = boundary vertical port connection (ordering constraint) — shown dashed/purple, distinct from data flow.
const ORDER_EDGE_STYLE = { className: 'order-edge', style: { stroke: '#8b5cf6', strokeDasharray: '4 3' } }
// order ports are the vertical younger(source,top)/older(target,bottom) handles; a younger→older connection is an order edge.
const isOrderConn = (srcH, tgtH) => srcH === 'younger' && tgtH === 'older'

// --- API ↔ React Flow conversion (nodes/edges are always the 'full real' set; the view is derived via buildView) ---
function apiToRF(graph, typeMap) {
  const nodes = graph.nodes.map((n) => {
    const t = typeMap[n.node_type] || { category: 'process', ports: [] }
    return {
      id: n.key, type: rfType(n.node_type), position: { x: n.x, y: n.y },
      width: nodeWidth(n.node_type, n.width),
      data: {
        nodeType: n.node_type, nature: n.nature || 'generic',
        label: n.label, description: n.description || '',
        params: n.params, category: t.category, ports: t.ports, group: n.group || null,
      },
    }
  })
  const edges = graph.edges.map((e) => ({
    id: `${e.source}:${e.source_port}->${e.target}:${e.target_port}`,
    source: e.source, target: e.target,
    sourceHandle: e.source_port, targetHandle: e.target_port,
    data: { kind: e.kind },
    ...(e.kind === 'order' ? ORDER_EDGE_STYLE : {}),
  }))
  const groups = (graph.groups || []).map((g) => ({ ...g }))
  return { nodes, edges, groups }
}

function rfToApi(nodes, edges, groups, viewport) {
  return {
    viewport,
    nodes: nodes.map((n) => ({
      key: n.id, node_type: n.data.nodeType, nature: n.data.nature || 'generic',
      label: n.data.label || '', description: n.data.description || '',
      params: n.data.params || {}, x: Math.round(n.position.x), y: Math.round(n.position.y),
      width: n.width ? Math.round(n.width) : null, group: n.data.group || null,
    })),
    edges: edges.map((e) => ({
      source: e.source, source_port: e.sourceHandle,
      target: e.target, target_port: e.targetHandle, kind: e.data?.kind || 'data',
    })),
    groups: groups.map((g) => ({
      key: g.key, name: g.name, collapsed: !!g.collapsed,
      x: Math.round(g.x), y: Math.round(g.y), parent: g.parent || null,
      // span group meta — prevent loss on save (boundary·unit references).
      kind: g.kind || 'container', unit: g.unit || null,
      lower: g.lower || null, upper: g.upper || null,
    })),
  }
}

// (nodes, edges, groups, activeGroup) → structure view {nodeRep, groupNodes, ioNodes, viewEdges}.
// Nesting support: at one level (activeGroup=group key or null=top level), only **direct nodes + direct subgroups (collapsed nodes)** are shown.
// A subgroup represents its entire subtree. Edges crossing a subtree boundary → group port (peer within the same subtree) or stub (outside the current subtree).
// This does not handle selection·real-node positions — the caller overlays them lightly, and this function reruns only on topology changes
// (avoids a full rebuild during rubber-band selection/drag to prevent frame degradation on large graphs).
function buildView(nodes, edges, groups, activeGroup) {
  const labelMap = Object.fromEntries(nodes.map((n) => [n.id, n.data.label || n.data.nodeType]))
  const lab = (id, port) => `${labelMap[id] || id}·${port}`
  const parentOf = Object.fromEntries(groups.map((g) => [g.key, g.parent || null]))
  const groupByKey = Object.fromEntries(groups.map((g) => [g.key, g]))
  const level = activeGroup || null

  // node group key → current-level representative: 'node' (direct) | {kind:'group',key} | 'external' (outside the current subtree)
  const repOf = (gk) => {
    if (gk === level) return { kind: 'node' }
    let g = gk
    while (g != null) {
      if (parentOf[g] === level) return { kind: 'group', key: g }
      g = parentOf[g]
    }
    return { kind: 'external' }
  }
  const nodeRep = Object.fromEntries(nodes.map((n) => [n.id, repOf(n.data.group || null)]))

  const subtreeCount = {}                          // per-group subtree node count (badge)
  nodes.forEach((n) => {
    let g = n.data.group || null
    while (g != null) { subtreeCount[g] = (subtreeCount[g] || 0) + 1; g = parentOf[g] }
  })

  const groupNodes = []                            // direct subgroups = collapsed nodes (selected is overlaid)
  const groupById = {}
  groups.forEach((g) => {
    if (parentOf[g.key] !== level) return
    const gn = { id: `group:${g.key}`, type: 'cdgtsGroup', position: { x: g.x, y: g.y },
      data: { key: g.key, name: g.name, kind: g.kind || 'container', inputs: [], outputs: [], count: subtreeCount[g.key] || 0 } }
    groupById[g.key] = gn
    groupNodes.push(gn)
  })

  // Drilling into a unit (interval) group shows that span's upper/lower bounding boundaries as fixed frames at top (upper)·bottom (lower).
  // An order frame separate from the left/right Group I/O — no matter which nested interval you drill into, that interval's upper/lower boundaries are shown consistently.
  const activeUnit = level ? groupByKey[level] : null
  const isUnit = !!activeUnit && activeUnit.kind === 'unit'
  const lowerKey = isUnit ? (activeUnit.lower || null) : null
  const upperKey = isUnit ? (activeUnit.upper || null) : null
  // Wrap 4 frames around the bounding box of the inner (direct member) nodes: left input · right output · top younger · bottom older.
  let cnt = 0, minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  nodes.forEach((n) => {
    if (repOf(n.data.group || null).kind !== 'node') return
    cnt += 1
    if (n.position.x < minX) minX = n.position.x
    if (n.position.x > maxX) maxX = n.position.x
    if (n.position.y < minY) minY = n.position.y
    if (n.position.y > maxY) maxY = n.position.y
  })
  if (!cnt) { minX = 0; maxX = 400; minY = 0; maxY = 400 }
  const cx = Math.round((minX + maxX) / 2)
  const cy = Math.round((minY + maxY) / 2)
  const boundUpper = { id: 'bound:upper', type: 'cdgtsBound', position: { x: cx, y: minY - 120 },
    data: { side: 'upper', label: upperKey ? (labelMap[upperKey] || upperKey) : null } }
  const boundLower = { id: 'bound:lower', type: 'cdgtsBound', position: { x: cx, y: maxY + 90 },
    data: { side: 'lower', label: lowerKey ? (labelMap[lowerKey] || lowerKey) : null } }

  // Blender-style interface nodes — aggregate the drilled-in group's external **data** connections into **one node** each for input/output.
  // Placed left/right relative to the inner-node bounding box (vertically centered). Position is overridden by the caller's ioPos overlay.
  const ioIn = { id: 'gio:in', type: 'cdgtsGroupIo', position: { x: minX - 340, y: cy },
    data: { dir: 'in', ports: [] } }
  const ioOut = { id: 'gio:out', type: 'cdgtsGroupIo', position: { x: maxX + 240, y: cy },
    data: { dir: 'out', ports: [] } }
  const portSeen = new Set()
  const viewEdges = []
  edges.forEach((e) => {
    const rs = nodeRep[e.source], rt = nodeRep[e.target]
    if (!rs || !rt) return
    if (rs.kind === 'group' && rt.kind === 'group' && rs.key === rt.key) return   // within the same subgroup → hide
    if (rs.kind === 'external' && rt.kind === 'external') return                   // outside the current subtree → hide
    const isOrder = e.data?.kind === 'order'
    let src = e.source, srcH = e.sourceHandle, tgt = e.target, tgtH = e.targetHandle
    if (rs.kind === 'group') {
      const hid = `out:${e.source}:${e.sourceHandle}`, gd = groupById[rs.key].data
      if (!gd.outputs.find((h) => h.id === hid))
        gd.outputs.push({ id: hid, port: e.sourceHandle, label: lab(e.source, e.sourceHandle) })
      src = `group:${rs.key}`; srcH = hid
    } else if (rs.kind === 'external' && isOrder && e.source === lowerKey) {
      src = 'bound:lower'; srcH = e.sourceHandle   // order rising from the lower boundary
    } else if (rs.kind === 'external' && isOrder && e.source === upperKey) {
      src = 'bound:upper'; srcH = e.sourceHandle
    } else if (rs.kind === 'external') {
      const pid = `gin:${e.source}:${e.sourceHandle}:${e.target}:${e.targetHandle}`
      if (!portSeen.has(pid)) {
        portSeen.add(pid)
        ioIn.data.ports.push({ id: pid, label: lab(e.target, e.targetHandle), peer: lab(e.source, e.sourceHandle) })
      }
      src = 'gio:in'; srcH = pid
    }
    if (rt.kind === 'group') {
      const hid = `in:${e.target}:${e.targetHandle}`, gd = groupById[rt.key].data
      if (!gd.inputs.find((h) => h.id === hid))
        gd.inputs.push({ id: hid, port: e.targetHandle, label: lab(e.target, e.targetHandle) })
      tgt = `group:${rt.key}`; tgtH = hid
    } else if (rt.kind === 'external' && isOrder && e.target === upperKey) {
      tgt = 'bound:upper'; tgtH = e.targetHandle   // order rising to the upper boundary
    } else if (rt.kind === 'external' && isOrder && e.target === lowerKey) {
      tgt = 'bound:lower'; tgtH = e.targetHandle
    } else if (rt.kind === 'external') {
      const pid = `gout:${e.source}:${e.sourceHandle}:${e.target}:${e.targetHandle}`
      if (!portSeen.has(pid)) {
        portSeen.add(pid)
        ioOut.data.ports.push({ id: pid, label: lab(e.source, e.sourceHandle), peer: lab(e.target, e.targetHandle) })
      }
      tgt = 'gio:out'; tgtH = pid
    }
    viewEdges.push({ ...e, id: `v-${e.id}`, source: src, sourceHandle: srcH, target: tgt, targetHandle: tgtH })
  })

  // Persist the order interface on collapsed unit groups: the younger(top)/older(bottom) ports are otherwise derived
  // from the crossing order edge, so deleting that edge would drop the port with no way to reconnect. Anchor them to the
  // group's boundary-most internal order nodes (youngest = internal-order target with no internal source; oldest = vice
  // versa) — derived from the *internal* chain, which survives deleting the external boundary edge.
  groups.forEach((g) => {
    if (parentOf[g.key] !== level || (g.kind || 'container') !== 'unit') return
    const gd = groupById[g.key]?.data
    if (!gd) return
    const srcs = new Set(), tgts = new Set()
    edges.forEach((e) => {
      if (e.data?.kind !== 'order') return
      const rs = nodeRep[e.source], rt = nodeRep[e.target]
      if (rs?.kind === 'group' && rt?.kind === 'group' && rs.key === g.key && rt.key === g.key) {
        srcs.add(e.source); tgts.add(e.target)
      }
    })
    // Always expose both order ports on a unit group (even where there is no bounding boundary yet, e.g. Quaternary's
    // younger side at the top of the chart) so the interface is stable and reconnectable.
    const youngest = [...tgts].find((n) => !srcs.has(n))   // younger end of the internal chain → group's upper order out
    const oldest = [...srcs].find((n) => !tgts.has(n))     // older end → group's lower order in
    if (youngest) {
      const hid = `out:${youngest}:younger`
      if (!gd.outputs.find((h) => h.id === hid)) gd.outputs.push({ id: hid, port: 'younger', label: lab(youngest, 'younger') })
    }
    if (oldest) {
      const hid = `in:${oldest}:older`
      if (!gd.inputs.find((h) => h.id === hid)) gd.inputs.push({ id: hid, port: 'older', label: lab(oldest, 'older') })
    }
  })

  const ioNodes = []
  if (ioIn.data.ports.length) ioNodes.push(ioIn)
  if (ioOut.data.ports.length) ioNodes.push(ioOut)
  const boundNodes = []
  if (isUnit && upperKey) boundNodes.push(boundUpper)
  if (isUnit && lowerKey) boundNodes.push(boundLower)
  return { nodeRep, groupNodes, ioNodes, boundNodes, viewEdges }
}

export default function Editor() {
  const [types, setTypes] = useState([])
  const [graphs, setGraphs] = useState([])
  const [graphId, setGraphId] = useState(null)
  const [graphName, setGraphName] = useState('')
  const [nodes, setNodes] = useNodesState([])       // all real nodes
  const [edges, setEdges] = useEdgesState([])       // all real edges
  const [groups, setGroups] = useState([])          // group meta [{key,name,collapsed,x,y}]
  const [activeGroup, setActiveGroup] = useState(null)   // null=top level / group key=drilled in
  const [ioPos, setIoPos] = useState({})   // per-drill-in interface node positions { [group]: { 'gio:in':{x,y}, 'gio:out':{x,y} } }
  const [status, setStatus] = useState('Loading…')
  const [error, setError] = useState(null)
  const [selectedIds, setSelectedIds] = useState([])          // selected real nodes
  const [selectedGroupKeys, setSelectedGroupKeys] = useState([])  // selected groups (collapsed nodes)
  const [menu, setMenu] = useState(null)   // right-click context menu {x,y,kind,id?,groupKey?}
  const [gateways, setGateways] = useState([])
  const [outputs, setOutputs] = useState([])
  const [runMeta, setRunMeta] = useState(null)
  const [savedSig, setSavedSig] = useState('')   // signature of the last saved/loaded graph → drives the unsaved (dirty) indicator
  const [showResults, setShowResults] = useState(false)
  const [verifyData, setVerifyData] = useState(null)        // Science CI: diff against the published baseline
  const [paletteOpen, setPaletteOpen] = useState(false)     // phone: palette drawer
  const [inspectorOpen, setInspectorOpen] = useState(false) // phone: inspector drawer
  const [inspectorCollapsed, setInspectorCollapsed] = useState(false) // desktop: hide the right properties panel
  const [pending, setPending] = useState(null)              // tap-to-add: node slug awaiting placement
  const wrapperRef = useRef(null)
  const lpRef = useRef(null)                                // long-press timer
  const lpFiredRef = useRef(false)                          // swallow the one click right after a long press
  const { screenToFlowPosition, getViewport, setViewport, fitView } = useReactFlow()

  const typeMap = useMemo(() => Object.fromEntries(types.map((t) => [t.slug, t])), [types])

  // Structural signature (nodes·edges·groups, excluding viewport and evaluation results) → compare against the last
  // saved/loaded snapshot to know if there are unsaved edits.
  const graphSig = useCallback((ns, es, gs) => {
    const a = rfToApi(ns, es, gs, null)
    return JSON.stringify({ nodes: a.nodes, edges: a.edges, groups: a.groups })
  }, [])
  const dirty = useMemo(
    () => graphId != null && graphSig(nodes, edges, groups) !== savedSig,
    [graphId, nodes, edges, groups, savedSig, graphSig],
  )

  // topology signature — captures only the structure (node existence·group membership·label / edge wiring), excluding selection·position.
  // buildView (group/stub/edge routing) reruns only when this changes → during rubber-band selection or node drag,
  // structure·edges are not rebuilt, eliminating the issue where pointermove backed up and the selection box froze on dense large graphs.
  const topoSig = useMemo(
    () => nodes.map((n) => `${n.id}~${n.data.group || ''}~${n.data.label || n.data.nodeType || ''}`).join('|'),
    [nodes],
  )
  const edgeSig = useMemo(
    () => edges.map((e) => `${e.id}~${e.source}~${e.sourceHandle}~${e.target}~${e.targetHandle}`).join('|'),
    [edges],
  )
  const struct = useMemo(
    () => buildView(nodes, edges, groups, activeGroup),
    // nodes·edges are latest via closure; the rerun trigger is only the structure signature (cache kept on selection/position changes).
    [topoSig, edgeSig, groups, activeGroup], // eslint-disable-line react-hooks/exhaustive-deps
  )
  // selection overlay (lightweight) — direct real nodes stay as-is (selection reflected); only selected is layered onto groups·edges.
  const viewNodes = useMemo(() => {
    const selG = new Set(selectedGroupKeys)
    const out = nodes.filter((n) => struct.nodeRep[n.id]?.kind === 'node')
    struct.groupNodes.forEach((gn) => out.push(selG.has(gn.data.key) ? { ...gn, selected: true } : gn))
    // interface nodes (gio:in/out) — overlay the per-drill-in remembered position (fall back to buildView default).
    const pos = ioPos[activeGroup || ''] || {}
    struct.ioNodes.forEach((io) => out.push(pos[io.id] ? { ...io, position: pos[io.id] } : io))
    // bound frames (upper/lower boundary) — selectable·draggable, position remembered per drill-in (same as gio).
    struct.boundNodes.forEach((bn) => out.push(pos[bn.id] ? { ...bn, position: pos[bn.id] } : bn))
    return out
  }, [nodes, struct, selectedGroupKeys, ioPos, activeGroup])
  const viewEdges = useMemo(() => {
    const selById = new Map(edges.map((e) => [e.id, !!e.selected]))
    return struct.viewEdges.map((ve) => {
      const sel = selById.get(ve.id.slice(2)) || false   // viewEdge id = 'v-' + original id
      return ve.selected === sel ? ve : { ...ve, selected: sel }
    })
  }, [struct, edges])

  const hydrate = useCallback((full, tmap) => {
    setGraphId(full.id)
    setGraphName(full.name)
    const { nodes: rn, edges: re, groups: rg } = apiToRF(full, tmap)
    setNodes(rn)
    setEdges(re)
    setGroups(rg)
    setSavedSig(graphSig(rn, re, rg))   // freshly loaded = clean baseline
    setActiveGroup(null)
    setSelectedIds([])
    setGateways(full.gateways || [])
    setOutputs([])
    setRunMeta(null)
    if (full.viewport && full.viewport.zoom) setViewport(full.viewport)
    setStatus(`Loaded: ${full.name} (nodes ${rn.length}${rg.length ? ` · groups ${rg.length}` : ''})`)
  }, [setNodes, setEdges, setViewport, graphSig])

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
      } catch (e) { setError(e.data || String(e)); setStatus('Load failed') }
    })()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const loadGraph = useCallback(async (id) => {
    setError(null)
    try { hydrate(await getGraph(id), typeMap) }
    catch (e) { setError(e.data || String(e)); setStatus('Load failed') }
  }, [typeMap, hydrate])

  // view → real state mapping. Apply only real node changes; group nodes position only; interface nodes remember position per drill-in.
  const onNodesChange = useCallback((changes) => {
    const real = []
    const gpos = []
    const gsel = []
    const iopos = []
    changes.forEach((c) => {
      const id = c.id
      if (id && id.startsWith('group:')) {
        // group nodes are derived (rebuilt each view) — reflect their position AND selection into real state.
        if (c.type === 'position' && c.position) gpos.push({ key: id.slice(6), pos: c.position })
        else if (c.type === 'select') gsel.push({ key: id.slice(6), selected: c.selected })
      }
      else if (id && (id === 'gio:in' || id === 'gio:out' || id === 'bound:upper' || id === 'bound:lower')) { if (c.type === 'position' && c.position) iopos.push({ id, pos: c.position }) }
      else if (id && id.startsWith('stub-')) { /* stub — ignore */ }
      else real.push(c)
    })
    if (real.length) setNodes((nds) => applyNodeChanges(real, nds))
    if (gsel.length) setSelectedGroupKeys((prev) => {
      const set = new Set(prev)
      gsel.forEach(({ key, selected }) => { if (selected) set.add(key); else set.delete(key) })
      return [...set]
    })
    if (gpos.length) setGroups((gs) => gs.map((g) => {
      const p = gpos.find((x) => x.key === g.key)
      return p ? { ...g, x: Math.round(p.pos.x), y: Math.round(p.pos.y) } : g
    }))
    if (iopos.length) setIoPos((prev) => {
      const k = activeGroup || ''
      const cur = { ...(prev[k] || {}) }
      iopos.forEach(({ id, pos }) => { cur[id] = { x: Math.round(pos.x), y: Math.round(pos.y) } })
      return { ...prev, [k]: cur }
    })
  }, [setNodes, activeGroup])

  const onEdgesChange = useCallback((changes) => {
    const real = changes.map((c) => (c.id && c.id.startsWith('v-') ? { ...c, id: c.id.slice(2) } : c))
    setEdges((eds) => applyEdgeChanges(real, eds))
  }, [setEdges])

  const onConnect = useCallback((c) => {
    let { source, sourceHandle, target, targetHandle } = c
    // Drawing from/to a group port (e.g. a collapsed node's upper/lower order port) → resolve to the member node's real port.
    // Group handle id convention (buildView): output `out:<member>:<port>` · input `in:<member>:<port>`.
    if (source?.startsWith('group:') && sourceHandle?.startsWith('out:')) {
      const [, m, p] = sourceHandle.split(':'); source = m; sourceHandle = p
    }
    if (target?.startsWith('group:') && targetHandle?.startsWith('in:')) {
      const [, m, p] = targetHandle.split(':'); target = m; targetHandle = p
    }
    if (['group:', 'stub-'].some((p) => source?.startsWith(p) || target?.startsWith(p))) return
    const isOrder = isOrderConn(sourceHandle, targetHandle)
    const id = `${source}:${sourceHandle}->${target}:${targetHandle}`
    setEdges((eds) => eds.concat({
      id, source, target, sourceHandle, targetHandle,
      data: { kind: isOrder ? 'order' : 'data' },
      ...(isOrder ? ORDER_EDGE_STYLE : {}),
    }))
  }, [setEdges])

  // shared node creation — used by both desktop drop and touch tap-to-add.
  const addNodeAt = useCallback((slug, position) => {
    const t = typeMap[slug]
    if (!t) return
    const key = `${slug}#${Math.random().toString(36).slice(2, 7)}`
    // boundary/published-age → boundary-point (0-cell) by default: renders as the compact ◈ boundary style (like the Base of … nodes).
    const nature = (slug === 'boundary' || slug === 'published-age') ? 'boundary' : 'generic'
    setNodes((nds) => nds.concat({
      id: key, type: rfType(slug), position, width: nodeWidth(slug),
      data: { nodeType: slug, nature, label: '', description: '', params: {}, category: t.category, ports: t.ports, group: activeGroup || null },
    }))
    setStatus(`${t.name} added`)
  }, [typeMap, setNodes, activeGroup])

  const onDragOver = useCallback((e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move' }, [])
  const onDrop = useCallback((e) => {
    e.preventDefault()
    const slug = e.dataTransfer.getData('application/cdgts')
    if (typeMap[slug]) addNodeAt(slug, screenToFlowPosition({ x: e.clientX, y: e.clientY }))
  }, [screenToFlowPosition, typeMap, addNodeAt])

  // touch: tap a palette item → await placement (pending), tap the canvas → create at that spot.
  const armPending = useCallback((slug) => { setPending(slug); setPaletteOpen(false); setStatus('Tap the canvas to place · tap again to cancel') }, [])
  // swallow the one synthetic click right after a long press (prevents the menu from closing immediately).
  const swallowLongPressClick = useCallback(() => {
    if (lpFiredRef.current) { lpFiredRef.current = false; return true }
    return false
  }, [])
  const onPaneClick = useCallback((e) => {
    if (swallowLongPressClick()) return
    if (pending) { addNodeAt(pending, screenToFlowPosition({ x: e.clientX, y: e.clientY })); setPending(null); return }
    setMenu(null)
  }, [swallowLongPressClick, pending, addNodeAt, screenToFlowPosition])

  // touch: long press (≈0.5s, if no movement) → context menu. Use elementFromPoint to detect node/group/empty area.
  const cancelLongPress = useCallback(() => { if (lpRef.current) { clearTimeout(lpRef.current); lpRef.current = null } }, [])
  const onTouchStartFlow = useCallback((e) => {
    if (!IS_TOUCH || e.touches.length !== 1) return
    const { clientX: x, clientY: y } = e.touches[0]
    cancelLongPress()
    lpFiredRef.current = false
    lpRef.current = setTimeout(() => {
      lpRef.current = null
      lpFiredRef.current = true
      const nodeEl = document.elementFromPoint(x, y)?.closest?.('.react-flow__node')
      const id = nodeEl?.getAttribute('data-id')
      if (id?.startsWith('group:')) setMenu({ x, y, kind: 'group', groupKey: id.slice(6) })
      else if (id && !id.startsWith('stub-')) setMenu({ x, y, kind: 'node', id })
      else setMenu({ x, y, kind: 'pane' })
    }, 500)
  }, [cancelLongPress])

  // --- create · merge / ungroup / drill-in groups ---
  // Combine real nodes + groups (collapsed nodes) into one. If groups are mixed in, absorb their members too and **merge** (single hierarchy kept);
  // the remaining selected groups are folded into the target group and disappear.
  const createOrMergeGroup = useCallback((realIds, groupKeys) => {
    // Also works inside activeGroup → creates a **subgroup** within it (nesting). New group parent = current level.
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
      name = (window.prompt('Group name', `Group ${groups.length + 1}`) || '').trim() || `Group ${groups.length + 1}`
    }
    const drop = new Set(groupKeys.slice(1))   // other groups that merge into the target and disappear
    const mem = nodes.filter((n) => allIds.includes(n.id))
    const cx = Math.round(mem.reduce((s, n) => s + n.position.x, 0) / (mem.length || 1))
    const cy = Math.round(mem.reduce((s, n) => s + n.position.y, 0) / (mem.length || 1))
    setNodes((nds) => nds.map((n) => (allIds.includes(n.id) ? { ...n, data: { ...n.data, group: key } } : n)))
    setGroups((gs) => {
      let next = gs
        .filter((g) => !drop.has(g.key))                                 // groups that merge away and disappear
        .map((g) => (drop.has(g.parent) ? { ...g, parent: key } : g))    // subgroups of a removed group → reparent to the target
      if (!merging) next = next.concat({ key, name, collapsed: true, x: cx, y: cy, parent: activeGroup || null })
      return next
    })
    setSelectedIds([]); setSelectedGroupKeys([])
    setStatus(`Group '${name}' ${merging ? 'merged' : 'created'} (${allIds.length} nodes)`)
  }, [activeGroup, groups, nodes, setNodes])

  const onCreateGroup = useCallback(
    () => createOrMergeGroup(selectedIds, selectedGroupKeys),
    [createOrMergeGroup, selectedIds, selectedGroupKeys],
  )

  const removeFromGroup = useCallback((id) => {
    const up = groups.find((g) => g.key === activeGroup)?.parent || null   // to the current group's parent
    setNodes((nds) => nds.map((n) => (n.id === id ? { ...n, data: { ...n.data, group: up } } : n)))
    setStatus('Node moved out to the parent level')
  }, [setNodes, activeGroup, groups])

  // If the right-clicked node is not in the selection, target just that node; otherwise target the whole current selection.
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
  const onEdgeContextMenu = useCallback((e, edge) => {
    e.preventDefault()
    setMenu({ x: e.clientX, y: e.clientY, kind: 'edge', id: edge.id, edgeKind: edge.data?.kind })
  }, [])
  // view edge id is `v-<realid>`; strip it to remove the underlying real edge (works for order & rewired boundary/group edges too).
  const onDeleteEdge = useCallback((viewId) => {
    const realId = viewId?.startsWith('v-') ? viewId.slice(2) : viewId
    setEdges((eds) => eds.filter((e) => e.id !== realId))
    setStatus('Edge deleted')
  }, [setEdges])

  // Delete node(s) and any edges incident to them.
  const onDeleteNodes = useCallback((ids) => {
    if (!ids?.length) return
    const set = new Set(ids)
    setNodes((nds) => nds.filter((n) => !set.has(n.id)))
    setEdges((eds) => eds.filter((e) => !set.has(e.source) && !set.has(e.target)))
    setSelectedIds((s) => s.filter((id) => !set.has(id)))
    setStatus(ids.length > 1 ? `${ids.length} nodes deleted` : 'Node deleted')
  }, [setNodes, setEdges])

  const onUngroup = useCallback((key) => {
    const up = groups.find((g) => g.key === key)?.parent || null      // on ungroup, contents go up to the parent level
    setNodes((nds) => nds.map((n) => (n.data.group === key ? { ...n, data: { ...n.data, group: up } } : n)))
    setGroups((gs) => gs
      .filter((g) => g.key !== key)
      .map((g) => (g.parent === key ? { ...g, parent: up } : g)))     // subgroups are promoted to the parent
    if (activeGroup === key) setActiveGroup(up)
    setSelectedGroupKeys((ks) => ks.filter((k) => k !== key))
    setStatus('Group ungrouped')
  }, [setNodes, activeGroup, groups])

  const onUngroupSelected = useCallback(() => selectedGroupKeys.forEach(onUngroup), [selectedGroupKeys, onUngroup])

  const onNodeDoubleClick = useCallback((_e, node) => {
    if (node.type === 'cdgtsGroup') { setActiveGroup(node.data.key); setSelectedIds([]); setSelectedGroupKeys([]) }
  }, [])

  // fit on context switch
  useEffect(() => { const id = setTimeout(() => fitView({ duration: 200 }), 0); return () => clearTimeout(id) }, [activeGroup, fitView])

  // Real-node selection tracked here; group-node selection is driven by onNodesChange 'select' changes
  // (groups are derived nodes — routing their selection through onSelectionChange too caused a stale-empty
  //  report to clobber the just-made selection, so it took two clicks). See onNodesChange gsel.
  const onSelectionChange = useCallback(({ nodes: sel }) => {
    setSelectedIds(sel.filter((n) => isRealNode(n.type)).map((n) => n.id))
  }, [])

  // Evaluate the graph (server-side, on the *saved* state) and attach per-node result distributions. `silent` = auto-run
  // (after load / save): fill node·Inspector values without opening the Results panel or surfacing errors.
  const runEvaluation = useCallback(async ({ silent = false } = {}) => {
    if (!graphId) return
    if (!silent) setError(null)
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
      if (!silent) setShowResults(true)
      const cert = run.certificate
      setStatus(`${silent ? 'Auto-evaluated' : `Evaluation run#${run.id}`} · computed ${run.stats.computed} / cached ${run.stats.cached}`
        + (cert ? ` · consistency ${cert.passed ? 'pass' : 'warn'}` : ''))
    } catch (e) { if (!silent) setError(e.data || String(e)); else setStatus('Auto-evaluate failed — press Evaluate') }
  }, [graphId, setNodes, gateways, nodes, edges])

  const onEvaluate = useCallback(() => runEvaluation(), [runEvaluation])

  const onSave = useCallback(async () => {
    setError(null)
    try {
      await saveGraph(graphId, rfToApi(nodes, edges, groups, getViewport()))
      setSavedSig(graphSig(nodes, edges, groups))   // saved = new clean baseline
      setStatus(`Saved · ${new Date().toLocaleTimeString()}`)
      runEvaluation({ silent: true })               // refresh results against the just-saved state
    } catch (e) { setError(e.data || String(e)); setStatus('Save failed (validation error?)') }
  }, [graphId, nodes, edges, groups, getViewport, graphSig, runEvaluation])

  // Auto-evaluate on load / graph switch (local == DB → results are correct). Keyed on graphId so edits don't retrigger.
  useEffect(() => {
    if (graphId) runEvaluation({ silent: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphId])

  // Science CI — re-bake, then diff against the published baseline. (Safer to save first before editing.)
  const onVerify = useCallback(async () => {
    setError(null)
    try {
      const d = await verifyGraph(graphId)
      setVerifyData(d); setShowResults(false)
      const s = d.summary || {}
      setStatus(`vs published: ${s.moved} moved · max |Δ| ${s.max_abs_delta} Ma · wiring ＋${s.added}/－${s.removed}/↺${s.retyped}`)
    } catch (e) { setError(e.data || String(e)) }
  }, [graphId])

  // --- Inspector (selected real node) ---
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

  // --- Inspector (selected node group) — when no real node is selected, show the selected group's info ---
  const onGroupName = useCallback(
    (key, name) => setGroups((gs) => gs.map((g) => (g.key === key ? { ...g, name } : g))),
    [setGroups],
  )
  const selectedGroup = useMemo(
    () => (selectedNode ? null : groups.find((g) => g.key === selectedGroupKeys[0]) || null),
    [selectedNode, groups, selectedGroupKeys],
  )
  const groupExtra = useMemo(() => {
    if (!selectedGroup) return null
    const parentOf = Object.fromEntries(groups.map((g) => [g.key, g.parent || null]))
    let count = 0
    nodes.forEach((n) => {
      let g = n.data.group || null
      while (g != null) { if (g === selectedGroup.key) { count += 1; break } g = parentOf[g] }
    })
    const labelOf = (id) => { const n = nodes.find((x) => x.id === id); return n ? (n.data.label || n.data.nodeType) : id }
    return {
      count,
      subgroups: groups.filter((g) => g.parent === selectedGroup.key).length,
      lowerLabel: selectedGroup.lower ? labelOf(selectedGroup.lower) : null,
      upperLabel: selectedGroup.upper ? labelOf(selectedGroup.upper) : null,
    }
  }, [selectedGroup, groups, nodes])

  const grouped = useMemo(() => {
    const g = { data: [], process: [], clamp: [] }
    types.forEach((t) => (g[t.category] || (g[t.category] = [])).push(t))
    return g
  }, [types])

  const activeGroupObj = groups.find((g) => g.key === activeGroup)
  // nesting path: top level → … → current group (breadcrumb)
  const activeGroupPath = useMemo(() => {
    const byKey = Object.fromEntries(groups.map((g) => [g.key, g]))
    const path = []
    let k = activeGroup
    while (k && byKey[k] && !path.includes(byKey[k])) { path.unshift(byKey[k]); k = byKey[k].parent || null }
    return path
  }, [groups, activeGroup])

  return (
    <div className="editor">
      {(paletteOpen || inspectorOpen) && (
        <div className="drawer-backdrop" onClick={() => { setPaletteOpen(false); setInspectorOpen(false) }} />
      )}
      <aside className={`palette${paletteOpen ? ' open' : ''}`}>
        <h1>cdGTS</h1>
        <p className="hint">{IS_TOUCH ? 'Tap a node → tap the canvas to place' : 'Drag a node onto the canvas'}</p>
        {['data', 'process', 'clamp'].map((cat) => (
          <div key={cat} className="palette-group">
            <h2 style={{ color: CATEGORY_COLOR[cat] }}>{cat}</h2>
            {(grouped[cat] || []).map((t) => (
              <div key={t.slug} className={`palette-item${pending === t.slug ? ' armed' : ''}`} draggable
                   onDragStart={(e) => { e.dataTransfer.setData('application/cdgts', t.slug); e.dataTransfer.effectAllowed = 'move' }}
                   onClick={() => { if (IS_TOUCH) armPending(t.slug) }}
                   title={t.description} style={{ borderLeftColor: CATEGORY_COLOR[cat] }}>
                {t.name}
              </div>
            ))}
          </div>
        ))}
      </aside>

      <main className="canvas" ref={wrapperRef}>
        <div className="toolbar">
          <button className="mobile-only drawer-toggle" onClick={() => { setPaletteOpen((v) => !v); setInspectorOpen(false) }} title="Palette">☰</button>
          <select className="graph-select" value={graphId || ''} onChange={(e) => loadGraph(Number(e.target.value))} title="Select graph">
            {graphs.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
          </select>
          <button onClick={onSave} className={dirty ? 'save-btn dirty' : 'save-btn'}
                  title={dirty ? 'Unsaved changes — click to save' : 'No changes since last save'}>
            Save (PUT)
          </button>
          <span className={`save-state ${dirty ? 'dirty' : 'clean'}`}
                title={dirty ? 'This graph has edits not yet saved to the server' : 'All edits saved'}>
            {dirty ? '● Unsaved' : '✓ Saved'}
          </span>
          <button onClick={onEvaluate}>Evaluate</button>
          <button onClick={onVerify} title="Science CI — re-bake, then diff against the published baseline (save before editing recommended)">Verify vs published</button>
          <button onClick={onCreateGroup}
                  disabled={!(selectedIds.length || selectedGroupKeys.length >= 2)}
                  title={activeGroup ? 'Nest the selection as a subgroup inside this group' : 'Combine the selected nodes·groups into one group (merges if groups are mixed in)'}>
            {selectedGroupKeys.length ? 'Merge groups' : (activeGroup ? 'Make subgroup' : 'Make group')}
            {(selectedIds.length + selectedGroupKeys.length) ? ` (${selectedIds.length + selectedGroupKeys.length})` : ''}
          </button>
          {selectedGroupKeys.length > 0 && (
            <button onClick={onUngroupSelected} title="Ungroup the selected group">
              Ungroup{selectedGroupKeys.length > 1 ? ` (${selectedGroupKeys.length})` : ''}
            </button>
          )}
          <button onClick={() => setShowResults((v) => !v)} className={showResults ? 'active' : ''} disabled={!runMeta} title="View final node outputs">
            Results{outputs.length ? ` (${outputs.length})` : ''}
          </button>
          <button className="mobile-only drawer-toggle" onClick={() => { setInspectorOpen((v) => !v); setPaletteOpen(false) }} title="Properties"
                  disabled={!selectedNode}>Properties</button>
          <button className="desktop-only" onClick={() => setInspectorCollapsed((v) => !v)}
                  title={inspectorCollapsed ? 'Show the properties panel' : 'Hide the properties panel'}>
            {inspectorCollapsed ? 'Properties ▸' : 'Properties ◂'}
          </button>
          <span className="status">{status}</span>
        </div>

        {(activeGroup || groups.length > 0) && (
          <div className="breadcrumb">
            <button className={activeGroup ? 'link' : 'link cur'} onClick={() => setActiveGroup(null)}>{graphName || 'graph'}</button>
            {activeGroupPath.map((g, i) => {
              const last = i === activeGroupPath.length - 1
              return (
                <span key={g.key}>
                  <span className="sep">›</span>
                  {last
                    ? <span className="cur">▤ {g.name || g.key}</span>
                    : <button className="link" onClick={() => setActiveGroup(g.key)}>▤ {g.name || g.key}</button>}
                </span>
              )
            })}
            {activeGroup && (
              <>
                <span className="bc-hint">Inside group — edit members·subgroups · left/right stubs = external I/O</span>
                <button className="ungroup" onClick={() => onUngroup(activeGroup)}>Ungroup</button>
              </>
            )}
            {!activeGroup && <span className="bc-hint">Double-click a group → edit inside</span>}
          </div>
        )}

        {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}
        {pending && (
          <div className="place-banner">
            ▶ <b>{typeMap[pending]?.name || pending}</b> — tap the canvas to place
            <button onClick={() => setPending(null)}>Cancel</button>
          </div>
        )}
        <div className="flow" onDrop={onDrop} onDragOver={onDragOver}
             onTouchStart={onTouchStartFlow} onTouchMove={cancelLongPress} onTouchEnd={cancelLongPress}>
          <ReactFlow
            nodes={viewNodes}
            edges={viewEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onSelectionChange={onSelectionChange}
            onNodeDoubleClick={onNodeDoubleClick}
            onNodeContextMenu={onNodeContextMenu}
            onEdgeContextMenu={onEdgeContextMenu}
            onPaneContextMenu={onPaneContextMenu}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            selectionOnDrag={!IS_TOUCH}          // desktop: left-drag = selection box
            autoPanOnSelection                   // auto-pan when the selection box reaches the viewport edge (reach off-screen nodes). Box start is anchored in flow coords upstream, so it no longer jumps.
            panOnDrag={IS_TOUCH ? true : [1]}    // touch: drag pan / desktop: middle button
            zoomOnPinch                          // touch: pinch zoom
            selectionMode={SelectionMode.Full}  // select only fully enclosed nodes — prevents the box growing when a wide node is barely grazed and released
            multiSelectionKeyCode="Shift"        // Shift+click = add to selection
            fitView
          >
            {activeGroup && (
              <Panel position="top-left">
                <button className="exit-parent" onClick={() => setActiveGroup(activeGroupObj?.parent || null)}
                        title="Exit to parent (same as right-click → Exit to parent)">
                  ↰ {activeGroupObj?.parent ? 'Parent' : 'Top level'}
                </button>
              </Panel>
            )}
            <Background />
            <Controls />
            <MiniMap pannable zoomable />
          </ReactFlow>
        </div>
        {showResults && <ResultsPanel outputs={outputs} meta={runMeta} onClose={() => setShowResults(false)} />}
        {verifyData && <VerifyPanel diff={verifyData} onClose={() => setVerifyData(null)} />}

        {menu && (
          <>
            <div className="ctx-backdrop" onClick={() => { if (!swallowLongPressClick()) closeMenu() }}
                 onContextMenu={(e) => { e.preventDefault(); closeMenu() }} />
            <ul className="ctx-menu" style={{ left: menu.x, top: menu.y }}>
              {menu.kind === 'node' && (
                <li onClick={() => { createOrMergeGroup(groupTargets(menu.id), selectedGroupKeys); closeMenu() }}>
                  {selectedGroupKeys.length ? 'Merge selection with group' : (activeGroup ? 'Group selection into a subgroup' : 'Group selected nodes')} ({groupTargets(menu.id).length + selectedGroupKeys.length})
                </li>
              )}
              {menu.kind === 'node' && activeGroup && (
                <li onClick={() => { removeFromGroup(menu.id); closeMenu() }}>Move out to parent level</li>
              )}
              {menu.kind === 'node' && (() => {
                const targets = groupTargets(menu.id)
                return (
                  <li className="danger" onClick={() => { onDeleteNodes(targets); closeMenu() }}>
                    Delete {targets.length > 1 ? `${targets.length} nodes` : 'node'}
                  </li>
                )
              })()}
              {menu.kind === 'group' && (
                <>
                  <li onClick={() => { setActiveGroup(menu.groupKey); closeMenu() }}>Open group</li>
                  {(selectedIds.length || selectedGroupKeys.filter((k) => k !== menu.groupKey).length) > 0 && (
                    <li onClick={() => {
                      createOrMergeGroup(selectedIds, [menu.groupKey, ...selectedGroupKeys.filter((k) => k !== menu.groupKey)])
                      closeMenu()
                    }}>Merge selection into this group ({selectedIds.length + selectedGroupKeys.filter((k) => k !== menu.groupKey).length})</li>
                  )}
                  <li onClick={() => { onUngroup(menu.groupKey); closeMenu() }}>Ungroup</li>
                </>
              )}
              {menu.kind === 'pane' && (
                (selectedIds.length || selectedGroupKeys.length >= 2)
                  ? <li onClick={() => { createOrMergeGroup(selectedIds, selectedGroupKeys); closeMenu() }}>
                      {selectedGroupKeys.length ? 'Merge selected groups·nodes' : (activeGroup ? 'Group selection into a subgroup' : 'Group selected nodes')} ({selectedIds.length + selectedGroupKeys.length})
                    </li>
                  : <li className="disabled">Select nodes/groups, then right-click</li>
              )}
              {menu.kind === 'pane' && activeGroup && (
                <li onClick={() => { setActiveGroup(activeGroupObj?.parent || null); closeMenu() }}>Exit to parent</li>
              )}
              {menu.kind === 'edge' && (
                <li className="danger" onClick={() => { onDeleteEdge(menu.id); closeMenu() }}>
                  Delete {menu.edgeKind === 'order' ? 'order (younger/older) edge' : 'edge'}
                </li>
              )}
            </ul>
          </>
        )}
      </main>

      {!inspectorCollapsed && (
      <Inspector
        key={selectedNode?.id || (selectedGroup && `group:${selectedGroup.key}`) || 'none'}
        open={inspectorOpen}
        onClose={() => setInspectorOpen(false)}
        onHide={() => setInspectorCollapsed(true)}
        node={selectedNode}
        type={selectedNode ? typeMap[selectedNode.data.nodeType] : null}
        group={selectedGroup}
        groupExtra={groupExtra}
        onGroupName={(v) => selectedGroup && onGroupName(selectedGroup.key, v)}
        nodeKeys={nodeKeys}
        onLabel={(v) => onLabel(selectedNode.id, v)}
        onDescription={(v) => onDescription(selectedNode.id, v)}
        onParam={(k, v) => onParam(selectedNode.id, k, v)}
        onDist={(k, sk, v) => onDist(selectedNode.id, k, sk, v)}
        onReplaceParams={(p) => onReplaceParams(selectedNode.id, p)}
      />
      )}
    </div>
  )
}

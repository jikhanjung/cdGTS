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
import EditorMenu from './EditorMenu.jsx'
import {
  rfType, isRealNode, nodeWidth, isOrderConn, isCiteConn, edgeStyleFor,
  apiToRF, rfToApi, buildView,
} from './graphView.js'
import {
  listNodeTypes, listGraphs, getGraph, createGraph, saveGraph, evaluateGraph, getEvalJob, verifyGraph,
  bakeGraph, suggestBakeName, forkGraph, updateGraphInfo, proposeGraph,
  listReferences, createReference,
} from './api.js'

const nodeTypes = { cdgts: CdgtsNode, cdgtsGroup: GroupNode, cdgtsStub: StubNode,
  cdgtsGroupIo: GroupIoNode, cdgtsBound: BoundNode, cdgtsOrder: OrderNode }

// Is the primary pointer touch (phone/tablet)? — pan/selection interactions differ (touch = drag pan · pinch zoom).
const IS_TOUCH = typeof window !== 'undefined' && typeof window.matchMedia === 'function'
  && window.matchMedia('(pointer: coarse)').matches

export default function Editor({ onBaked, onProposed, user } = {}) {
  const [types, setTypes] = useState([])
  const [references, setReferences] = useState([])   // provenance registry (DOI-centric)
  const [graphs, setGraphs] = useState([])
  const [graphId, setGraphId] = useState(null)
  const [graphName, setGraphName] = useState('')
  const [nodes, setNodes] = useNodesState([])       // all real nodes
  const [edges, setEdges] = useEdgesState([])       // all real edges
  const [groups, setGroups] = useState([])          // group meta [{key,name,collapsed,x,y}]
  const [activeGroup, setActiveGroup] = useState(null)   // null=top level / group key=drilled in
  const [ioPos, setIoPos] = useState({})   // per-drill-in interface node positions { [group]: { 'gio:in':{x,y}, 'gio:out':{x,y} } }
  const [ioSel, setIoSel] = useState(() => new Set())   // selected synthetic nodes (gio:in/out, bound:upper/lower) — derived per view, so selection is held here for the ring
  const synthRef = useRef(new Map())   // id → { sig, node }: stable object refs for derived nodes (group/gio/bound) so React Flow keeps them measured across rebuilds
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
  const shouldFitRef = useRef(false)                        // set on load when the graph has no saved viewport → fit once
  const dlgDownRef = useRef(false)                          // modal dismiss: only close when the press started on the backdrop (not a drag-select out of an input)
  const lpRef = useRef(null)                                // long-press timer
  const lpFiredRef = useRef(false)                          // swallow the one click right after a long press
  const { screenToFlowPosition, getViewport, setViewport, fitView } = useReactFlow()

  const typeMap = useMemo(() => Object.fromEntries(types.map((t) => [t.slug, t])), [types])
  const refMap = useMemo(() => Object.fromEntries(references.map((r) => [r.slug, r])), [references])

  // P05.2 ownership: only the owner (or staff) may edit/save. Others get a read-only view (no canvas/inspector edits).
  const currentGraph = graphs.find((g) => g.id === graphId)
  const authed = !!user?.authenticated
  const canEdit = authed && (currentGraph?.owner === user.username || user.is_staff)

  // Add a reference to the registry (inspector quick-add). Returns the created reference.
  const onCreateReference = useCallback(async (body) => {
    const created = await createReference(body)
    setReferences((rs) => [...rs.filter((r) => r.slug !== created.slug), created])
    return created
  }, [])

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
  // synthetic nodes only exist within a given drill-in → clear their selection when the level changes.
  useEffect(() => { setIoSel(new Set()) }, [activeGroup])

  const viewNodes = useMemo(() => {
    // Derived nodes (group/gio/bound) are rebuilt fresh by buildView on every `nodes` change (e.g. selecting a real node
    // during a rubber-band). Handing React Flow a brand-new object each time makes it treat the node as unmeasured
    // (handleBounds null / measured.height 0 → area 0), and getNodesInside then force-selects it even when it's outside
    // the selection box. Keep a stable object reference while the node's content is unchanged so it stays measured.
    const stable = (node) => {
      const sig = JSON.stringify({ p: node.position, s: !!node.selected, w: node.width, d: node.data })
      const hit = synthRef.current.get(node.id)
      if (hit && hit.sig === sig) return hit.node
      synthRef.current.set(node.id, { sig, node })
      return node
    }
    const selG = new Set(selectedGroupKeys)
    const out = nodes.filter((n) => struct.nodeRep[n.id]?.kind === 'node')
    struct.groupNodes.forEach((gn) => out.push(stable(selG.has(gn.data.key) ? { ...gn, selected: true } : gn)))
    // interface nodes (gio:in/out) — overlay the per-drill-in remembered position (fall back to buildView default).
    const pos = ioPos[activeGroup || ''] || {}
    struct.ioNodes.forEach((io) => out.push(stable({ ...(pos[io.id] ? { ...io, position: pos[io.id] } : io), selected: ioSel.has(io.id) })))
    // bound frames (upper/lower boundary) — selectable·draggable, position remembered per drill-in (same as gio).
    struct.boundNodes.forEach((bn) => out.push(stable({ ...(pos[bn.id] ? { ...bn, position: pos[bn.id] } : bn), selected: ioSel.has(bn.id) })))
    return out
  }, [nodes, struct, selectedGroupKeys, ioPos, ioSel, activeGroup])
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
    // Restore the saved pan/zoom if there is one; otherwise fit-to-graph on load (see the graphId effect below).
    if (full.viewport && full.viewport.zoom) { setViewport(full.viewport); shouldFitRef.current = false }
    else { shouldFitRef.current = true }
    setStatus(`Loaded: ${full.name} (nodes ${rn.length}${rg.length ? ` · groups ${rg.length}` : ''})`)
  }, [setNodes, setEdges, setViewport, graphSig])

  useEffect(() => {
    (async () => {
      try {
        const ts = await listNodeTypes()
        setTypes(ts)
        listReferences().then(setReferences).catch(() => {})   // provenance registry (non-fatal)
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

  // Keep reference nodes' shown citation resolved against the registry (covers late-loaded refs and inspector picks).
  const refSig = useMemo(
    () => nodes.filter((n) => n.data.category === 'reference')
      .map((n) => `${n.id}:${n.data.params?.reference || ''}`).join('|'),
    [nodes],
  )
  useEffect(() => {
    setNodes((nds) => nds.map((n) => {
      if (n.data.category !== 'reference') return n
      const info = refMap[n.data.params?.reference] || null
      return n.data.referenceInfo === info ? n : { ...n, data: { ...n.data, referenceInfo: info } }
    }))
  }, [refMap, refSig, setNodes])

  // Fork the current graph into a sandbox you own (P05.3), then switch to editing it.
  const [forkDialog, setForkDialog] = useState(null)   // { name, busy } | null
  const onOpenFork = useCallback(() => {
    setError(null)
    if (!authed) {                          // fork = a new graph you own → requires sign-in
      setStatus('Sign in to fork — a fork is a new graph you own and can edit.')
      setError({ detail: 'Sign in to fork this graph (creates your own editable copy).' })
      return
    }
    setForkDialog({ name: `${graphName || 'graph'} (fork)`, busy: false })
  }, [graphName, authed])
  const onConfirmFork = useCallback(async () => {
    const name = (forkDialog?.name || '').trim()
    setForkDialog((d) => d && ({ ...d, busy: true }))
    try {
      const g = await forkGraph(graphId, name)
      setGraphs((gs) => [g, ...gs.filter((x) => x.id !== g.id)])
      hydrate(await getGraph(g.id), typeMap)
      setForkDialog(null)
      setStatus(`Forked → ${g.name} · yours to edit`)
    } catch (e) { setError(e.data || String(e)); setForkDialog((d) => d && ({ ...d, busy: false })); setStatus('Fork failed') }
  }, [forkDialog, graphId, typeMap, hydrate])

  // view → real state mapping. Apply only real node changes; group nodes position only; interface nodes remember position per drill-in.
  const onNodesChange = useCallback((changes) => {
    const real = []
    const gpos = []
    const gsel = []
    const iopos = []
    const iosel = []
    changes.forEach((c) => {
      const id = c.id
      if (id && id.startsWith('group:')) {
        // group nodes are derived (rebuilt each view) — reflect their position AND selection into real state.
        if (c.type === 'position' && c.position) gpos.push({ key: id.slice(6), pos: c.position })
        else if (c.type === 'select') gsel.push({ key: id.slice(6), selected: c.selected })
      }
      else if (id && (id === 'gio:in' || id === 'gio:out' || id === 'bound:upper' || id === 'bound:lower')) {
        // synthetic nodes are derived per view — hold position AND selection (for the ring) outside the derived state.
        if (c.type === 'position' && c.position) iopos.push({ id, pos: c.position })
        else if (c.type === 'select') iosel.push({ id, selected: c.selected })
      }
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
    if (iosel.length) setIoSel((prev) => {
      const set = new Set(prev)
      iosel.forEach(({ id, selected }) => { if (selected) set.add(id); else set.delete(id) })
      return set
    })
  }, [setNodes, activeGroup])

  const onEdgesChange = useCallback((changes) => {
    const real = changes.map((c) => (c.id && c.id.startsWith('v-') ? { ...c, id: c.id.slice(2) } : c))
    setEdges((eds) => applyEdgeChanges(real, eds))
  }, [setEdges])

  const onConnect = useCallback((c) => {
    if (!canEdit) return
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
    const kind = isOrderConn(sourceHandle, targetHandle) ? 'order'
      : isCiteConn(sourceHandle, targetHandle) ? 'cite' : 'data'
    const id = `${source}:${sourceHandle}->${target}:${targetHandle}`
    setEdges((eds) => eds.concat({
      id, source, target, sourceHandle, targetHandle,
      data: { kind },
      ...edgeStyleFor(kind),
    }))
  }, [setEdges, canEdit])

  // shared node creation — used by both desktop drop and touch tap-to-add.
  const addNodeAt = useCallback((slug, position) => {
    if (!canEdit) return
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
  }, [typeMap, setNodes, activeGroup, canEdit])

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
    // read-only users still get the long-press menu — it's their only path to drill into a group (no double-click on touch).
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
      else if (canEdit && id && !id.startsWith('stub-')) setMenu({ x, y, kind: 'node', id })
      else if (canEdit || activeGroup) setMenu({ x, y, kind: 'pane' })   // read-only: pane menu only inside a group (Exit)
    }, 500)
  }, [cancelLongPress, canEdit, activeGroup])

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
    // read-only: still offer the group menu (view-only "Open group"); no menu on real nodes.
    if (node.type === 'cdgtsGroup') setMenu({ x: e.clientX, y: e.clientY, kind: 'group', groupKey: node.data.key })
    else if (canEdit && isRealNode(node.type)) setMenu({ x: e.clientX, y: e.clientY, kind: 'node', id: node.id })
  }, [canEdit])
  const onPaneContextMenu = useCallback((e) => {
    e.preventDefault()
    if (!canEdit && !activeGroup) return       // read-only at top level: nothing to offer
    setMenu({ x: e.clientX, y: e.clientY, kind: 'pane' })
  }, [canEdit, activeGroup])
  const onEdgeContextMenu = useCallback((e, edge) => {
    e.preventDefault()
    if (!canEdit) return
    setMenu({ x: e.clientX, y: e.clientY, kind: 'edge', id: edge.id, edgeKind: edge.data?.kind })
  }, [canEdit])
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

  // fit-to-graph once when a graph is loaded *without* a saved viewport (nodes need a beat to mount + measure first)
  useEffect(() => {
    if (!graphId || !shouldFitRef.current) return
    shouldFitRef.current = false
    const id = setTimeout(() => fitView({ duration: 300, padding: 0.15 }), 80)
    return () => clearTimeout(id)
  }, [graphId, fitView])

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
      let run = await evaluateGraph(graphId)
      // Async path (P06.4a): joint/cyclic graphs return a queued EvalJob — poll the worker until done.
      if (run && run.status !== undefined && !run.results) {
        const jobId = run.id
        run = null
        for (let i = 0; i < 120 && !run; i++) {           // ~120 × 1s cap
          const job = await getEvalJob(jobId)
          if (job.status === 'done') { run = job.run; break }
          if (job.status === 'failed') throw Object.assign(new Error('평가 실패'), { data: job.error })
          setStatus(`Evaluating… (job#${jobId} ${job.status})`)
          await new Promise((r) => setTimeout(r, 1000))
        }
        if (!run) throw new Error('평가 시간 초과 — 워커가 실행 중인지 확인하세요')
      }
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
      const certWord = cert
        ? (!cert.passed ? 'fail' : (Object.entries(cert.checks || {}).some(([k, v]) => k !== 'notes' && v === 'warn') ? 'warn' : 'pass'))
        : null
      setStatus(`${silent ? 'Auto-evaluated' : `Evaluation run#${run.id}`} · computed ${run.stats.computed} / cached ${run.stats.cached}`
        + (certWord ? ` · consistency ${certWord}` : ''))
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

  // Bake — freeze the current graph's gateway outputs into a new immutable Release (Vault artifact).
  // Saves first (bake evaluates the server-side graph), then opens a dialog with an editable suggested name.
  const [bakeDialog, setBakeDialog] = useState(null)   // { name, busy } | null
  const onOpenBake = useCallback(async () => {
    setError(null)
    try {
      if (dirty) {
        await saveGraph(graphId, rfToApi(nodes, edges, groups, getViewport()))
        setSavedSig(graphSig(nodes, edges, groups))
      }
      const { suggested } = await suggestBakeName(graphId)
      setBakeDialog({ name: suggested, busy: false })
    } catch (e) { setError(e.data || String(e)); setStatus('Bake preparation failed') }
  }, [dirty, graphId, nodes, edges, groups, getViewport, graphSig])

  const onConfirmBake = useCallback(async () => {
    const name = (bakeDialog?.name || '').trim()
    setBakeDialog((d) => d && ({ ...d, busy: true }))
    try {
      const { baked, release } = await bakeGraph(graphId, name)
      setBakeDialog(null)
      setStatus(`Baked → ${release.version} (${baked} boundaries) · saved to Vault`)
      if (onBaked) onBaked(release)
    } catch (e) { setError(e.data || String(e)); setBakeDialog((d) => d && ({ ...d, busy: false })) }
  }, [bakeDialog, graphId, onBaked])

  // Propose (P05.4) — save, then submit this sandbox graph for review against the published baseline.
  const onPropose = useCallback(async () => {
    setError(null)
    try {
      if (dirty) {
        await saveGraph(graphId, rfToApi(nodes, edges, groups, getViewport()))
        setSavedSig(graphSig(nodes, edges, groups))
      }
      const { proposal } = await proposeGraph(graphId)
      setStatus(`Proposed → #${proposal.id} (${(proposal.affected || []).length} boundaries) · review in Proposals`)
      if (onProposed) onProposed(proposal)
    } catch (e) { setError(e.data?.detail || e.data || String(e)); setStatus('Propose failed') }
  }, [dirty, graphId, nodes, edges, groups, getViewport, graphSig, onProposed])

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
  // Auto-show the properties panel (desktop) when the selection changes to a node/group. Keyed on the selection ids
  // (not the node objects) so hiding the panel while a node stays selected isn't undone by unrelated edits/evals.
  useEffect(() => {
    if (selectedId || selectedGroupKeys[0]) setInspectorCollapsed(false)
  }, [selectedId, selectedGroupKeys])
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

  // any signed-in user may bake a readable graph; propose needs edit rights on a sandbox.
  const canBake = authed
  const canPropose = canEdit && currentGraph?.status === 'sandbox'
  const [actionsOpen, setActionsOpen] = useState(false)

  const [infoDialog, setInfoDialog] = useState(null)   // { name, description, busy } | null
  const onOpenInfo = useCallback(() => {
    setError(null)
    setInfoDialog({ name: currentGraph?.name || graphName || '', description: currentGraph?.description || '', busy: false })
  }, [currentGraph, graphName])
  const onSaveInfo = useCallback(async () => {
    if (!infoDialog || !infoDialog.name.trim()) return
    setInfoDialog((d) => d && ({ ...d, busy: true }))
    try {
      const g = await updateGraphInfo(graphId, { name: infoDialog.name.trim(), description: infoDialog.description })
      setGraphs((gs) => gs.map((x) => (x.id === g.id ? { ...x, name: g.name, description: g.description } : x)))
      setGraphName(g.name)
      setInfoDialog(null)
      setStatus(`Graph info saved · ${g.name}`)
    } catch (e) { setError(e.data || String(e)); setInfoDialog((d) => d && ({ ...d, busy: false })) }
  }, [infoDialog, graphId])

  // Reload the visible graph list when auth identity changes (login reveals your graphs; logout hides them).
  useEffect(() => {
    if (user === null) return               // whoami not resolved yet
    listGraphs().then(setGraphs).catch(() => {})
  }, [user?.authenticated, user?.username])

  return (
    <div className="editor">
      {(paletteOpen || inspectorOpen) && (
        <div className="drawer-backdrop" onClick={() => { setPaletteOpen(false); setInspectorOpen(false) }} />
      )}
      {forkDialog && (
        <div className="modal-backdrop"
             onMouseDown={(e) => { dlgDownRef.current = e.target === e.currentTarget }}
             onClick={(e) => { if (!forkDialog.busy && dlgDownRef.current && e.target === e.currentTarget) setForkDialog(null) }}>
          <div className="bake-dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Fork this graph</h3>
            <p className="hint">Creates an independent copy in your own sandbox — edit it without touching the original.</p>
            <label className="bake-name">
              Name
              <input type="text" value={forkDialog.name} autoFocus disabled={forkDialog.busy}
                     onChange={(e) => setForkDialog((d) => ({ ...d, name: e.target.value }))}
                     onKeyDown={(e) => { if (e.key === 'Enter' && forkDialog.name.trim()) onConfirmFork() }} />
            </label>
            <div className="bake-actions">
              <button onClick={() => setForkDialog(null)} disabled={forkDialog.busy}>Cancel</button>
              <button className="fork-btn primary" onClick={onConfirmFork}
                      disabled={forkDialog.busy || !forkDialog.name.trim()}>
                {forkDialog.busy ? 'Forking…' : 'Fork'}
              </button>
            </div>
          </div>
        </div>
      )}
      {infoDialog && (
        <div className="modal-backdrop"
             onMouseDown={(e) => { dlgDownRef.current = e.target === e.currentTarget }}
             onClick={(e) => { if (!infoDialog.busy && dlgDownRef.current && e.target === e.currentTarget) setInfoDialog(null) }}>
          <div className="bake-dialog info-dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Graph info</h3>
            <label className="bake-name">
              Name
              <input type="text" value={infoDialog.name} autoFocus disabled={infoDialog.busy || !canEdit}
                     onChange={(e) => setInfoDialog((d) => ({ ...d, name: e.target.value }))} />
            </label>
            <label className="bake-name">
              Description
              <textarea rows={4} value={infoDialog.description} disabled={infoDialog.busy || !canEdit}
                        placeholder={canEdit ? 'What is this graph / branch for?' : ''}
                        onChange={(e) => setInfoDialog((d) => ({ ...d, description: e.target.value }))} />
            </label>
            <dl className="info-meta">
              <div><dt>Status</dt><dd>{currentGraph?.status || '—'}</dd></div>
              <div><dt>Owner</dt><dd>{currentGraph?.owner || 'System / demo'}</dd></div>
              <div><dt>Forked from</dt><dd>{currentGraph?.forked_from || '—'}</dd></div>
              <div><dt>Slug</dt><dd>{currentGraph?.slug || '—'}</dd></div>
            </dl>
            <div className="bake-actions">
              <button onClick={() => setInfoDialog(null)} disabled={infoDialog.busy}>{canEdit ? 'Cancel' : 'Close'}</button>
              {canEdit && (
                <button className="bake-btn primary" onClick={onSaveInfo}
                        disabled={infoDialog.busy || !infoDialog.name.trim()}>
                  {infoDialog.busy ? 'Saving…' : 'Save'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
      {bakeDialog && (
        <div className="modal-backdrop"
             onMouseDown={(e) => { dlgDownRef.current = e.target === e.currentTarget }}
             onClick={(e) => { if (!bakeDialog.busy && dlgDownRef.current && e.target === e.currentTarget) setBakeDialog(null) }}>
          <div className="bake-dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Bake a Release</h3>
            <p className="hint">Freezes this graph's current boundary outputs into an immutable artifact kept in the Vault.</p>
            <label className="bake-name">
              Name
              <input type="text" value={bakeDialog.name} autoFocus disabled={bakeDialog.busy}
                     onChange={(e) => setBakeDialog((d) => ({ ...d, name: e.target.value }))}
                     onKeyDown={(e) => { if (e.key === 'Enter' && bakeDialog.name.trim()) onConfirmBake() }} />
            </label>
            <div className="bake-actions">
              <button onClick={() => setBakeDialog(null)} disabled={bakeDialog.busy}>Cancel</button>
              <button className="bake-btn primary" onClick={onConfirmBake}
                      disabled={bakeDialog.busy || !bakeDialog.name.trim()}>
                {bakeDialog.busy ? 'Baking…' : 'Bake'}
              </button>
            </div>
          </div>
        </div>
      )}
      <aside className={`palette${paletteOpen ? ' open' : ''}${canEdit ? '' : ' readonly'}`}>
        <h1>cdGTS</h1>
        <p className="hint">{!canEdit ? '🔒 Read-only — you can view but not edit this graph'
          : (IS_TOUCH ? 'Tap a node → tap the canvas to place' : 'Drag a node onto the canvas')}</p>
        {['data', 'process', 'clamp', 'reference'].map((cat) => (
          <div key={cat} className="palette-group">
            <h2 style={{ color: CATEGORY_COLOR[cat] }}>{cat}</h2>
            {(grouped[cat] || []).map((t) => (
              <div key={t.slug} className={`palette-item${pending === t.slug ? ' armed' : ''}${canEdit ? '' : ' disabled'}`}
                   draggable={canEdit}
                   onDragStart={(e) => { if (!canEdit) { e.preventDefault(); return } e.dataTransfer.setData('application/cdgts', t.slug); e.dataTransfer.effectAllowed = 'move' }}
                   onClick={() => { if (IS_TOUCH && canEdit) armPending(t.slug) }}
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
          <button className="info-btn" onClick={onOpenInfo} disabled={!graphId}
                  title="Graph info — name, description, lineage">ⓘ</button>
          <button onClick={onSave} className={dirty ? 'save-btn dirty' : 'save-btn'} disabled={!canEdit}
                  title={!canEdit
                    ? (authed ? 'Read-only — not your graph (fork to edit)' : 'Sign in to edit your own graphs')
                    : (dirty ? 'Unsaved changes — click to save' : 'No changes since last save')}>
            Save
          </button>
          {canEdit ? (
            <span className={`save-state ${dirty ? 'dirty' : 'clean'}`}
                  title={dirty ? 'This graph has edits not yet saved to the server' : 'All edits saved'}>
              {dirty ? '● Unsaved' : '✓ Saved'}
            </span>
          ) : (
            <>
              <span className="save-state readonly" title={currentGraph?.owner ? `Owned by ${currentGraph.owner}` : 'System / demo graph'}>
                🔒 Read-only
              </span>
              <button className="fork-to-edit" onClick={onOpenFork} disabled={!graphId}
                      title={authed ? 'Copy this graph into a sandbox you own, then edit it' : 'Sign in to fork this graph into your own editable copy'}>
                {authed ? 'Fork to edit →' : 'Sign in to fork'}
              </button>
            </>
          )}
          <div className="tb-menu">
            <button className={`tb-menu-btn${actionsOpen ? ' open' : ''}`} onClick={() => setActionsOpen((v) => !v)}
                    disabled={!graphId} title="Graph actions — evaluate, verify, bake, propose, fork">Actions ▾</button>
            {actionsOpen && (
              <>
                <div className="tb-menu-backdrop" onClick={() => setActionsOpen(false)} />
                <div className="tb-menu-list" role="menu">
                  <button role="menuitem" disabled={dirty} onClick={() => { setActionsOpen(false); onEvaluate() }}
                          title={dirty ? 'Save first — Evaluate runs on the saved graph, not your unsaved edits' : 'Re-run the graph and attach per-node results'}>Evaluate</button>
                  <button role="menuitem" disabled={dirty} onClick={() => { setActionsOpen(false); onVerify() }}
                          title={dirty ? 'Save first — Verify runs on the saved graph, not your unsaved edits' : 'Science CI — re-bake, then diff against the published baseline'}>Verify vs published</button>
                  <div className="tb-menu-sep" />
                  <button role="menuitem" disabled={!graphId || !canBake} onClick={() => { setActionsOpen(false); onOpenBake() }}
                          title={canBake ? 'Freeze outputs into a new immutable Release kept in the Vault' : 'Sign in to bake a Release'}>Bake…</button>
                  {canEdit && (
                    <button role="menuitem" className="propose-item" disabled={!canPropose} onClick={() => { setActionsOpen(false); onPropose() }}
                            title={canPropose ? 'Propose this graph for review against the published baseline (CI)'
                                              : (currentGraph?.status !== 'sandbox' ? `Already ${currentGraph?.status}` : 'Propose')}>
                      {currentGraph?.status === 'proposed' ? 'Proposed ✓' : 'Propose…'}
                    </button>
                  )}
                  <div className="tb-menu-sep" />
                  <button role="menuitem" disabled={!graphId} onClick={() => { setActionsOpen(false); onOpenFork() }}
                          title={authed ? 'Copy this graph into a new sandbox you own' : 'Sign in to fork this graph into your own editable copy'}>Fork…</button>
                </div>
              </>
            )}
          </div>
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
          <div className="tb-spacer" />
          <button onClick={() => setShowResults((v) => !v)} className={showResults ? 'active' : ''} disabled={!runMeta} title="View final node outputs">
            Results{outputs.length ? ` (${outputs.length})` : ''}
          </button>
          <button className="mobile-only drawer-toggle" onClick={() => { setInspectorOpen((v) => !v); setPaletteOpen(false) }} title="Properties"
                  disabled={!selectedNode}>Properties</button>
          <button className="desktop-only" onClick={() => setInspectorCollapsed((v) => !v)}
                  title={inspectorCollapsed ? 'Show the properties panel' : 'Hide the properties panel'}>
            {inspectorCollapsed ? 'Properties ▸' : 'Properties ◂'}
          </button>
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
                <span className="bc-hint">Inside group — {canEdit ? 'edit' : 'view'} members·subgroups · left/right stubs = external I/O</span>
                {canEdit && <button className="ungroup" onClick={() => onUngroup(activeGroup)}>Ungroup</button>}
              </>
            )}
            {!activeGroup && <span className="bc-hint">Double-click a group → open inside{canEdit ? ' (edit)' : ' (view)'}</span>}
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
            nodesDraggable={canEdit}             // read-only: can't move nodes
            nodesConnectable={canEdit}           // read-only: can't wire edges
            deleteKeyCode={canEdit ? ['Backspace', 'Delete'] : null}   // read-only: delete key does nothing
            selectionOnDrag={!IS_TOUCH}          // desktop: left-drag = selection box
            autoPanOnSelection                   // auto-pan when the selection box reaches the viewport edge (reach off-screen nodes). Box start is anchored in flow coords upstream, so it no longer jumps.
            panOnDrag={IS_TOUCH ? true : [1]}    // touch: drag pan / desktop: middle button
            zoomOnPinch                          // touch: pinch zoom
            selectionMode={SelectionMode.Full}  // select only fully enclosed nodes — prevents the box growing when a wide node is barely grazed and released
            multiSelectionKeyCode="Shift"        // Shift+click = add to selection
            selectionKeyCode={null}              // box-select is already on plain drag (selectionOnDrag); free Shift for multi-add only (avoid the Shift/Shift conflict)
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

        <div className="editor-statusbar" title="Latest editor status">
          <span className={`sb-dot ${dirty ? 'dirty' : 'clean'}`} />
          <span className="sb-text">{status || 'Ready'}</span>
        </div>

        <EditorMenu
          menu={menu} canEdit={canEdit} activeGroup={activeGroup} activeGroupObj={activeGroupObj}
          selectedIds={selectedIds} selectedGroupKeys={selectedGroupKeys}
          swallowLongPressClick={swallowLongPressClick} closeMenu={closeMenu}
          groupTargets={groupTargets} createOrMergeGroup={createOrMergeGroup}
          removeFromGroup={removeFromGroup} onDeleteNodes={onDeleteNodes} onUngroup={onUngroup}
          onDeleteEdge={onDeleteEdge} setActiveGroup={setActiveGroup}
        />
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
        references={references}
        onCreateReference={onCreateReference}
        readOnly={!canEdit}
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

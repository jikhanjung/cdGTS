// Pure view/conversion layer for the node editor — extracted from Editor.jsx (R02: decompose Editor.jsx).
// No React, no component state: (API graph ⇆ React Flow) conversion + the derived structure view (buildView).
// Kept pure so it is independently testable and reruns only on topology changes.

const DEFAULT_NODE_WIDTH = 172   // Default width (px). User can adjust via the right handle.
const GROUP_NODE_WIDTH = 200     // Collapsed group node width (px). Fixed so long I/O labels ellipsis instead of stretching the node.
const GROUP_IO_WIDTH = 200       // Group Input/Output interface node width (px). Fixed so long port labels ellipsis instead of stretching the node.

// node type slug → React Flow node component kind. order is a vertical-handle-only component.
export const rfType = (slug) => (slug === 'order' ? 'cdgtsOrder' : 'cdgts')
export const isRealNode = (t) => t === 'cdgts' || t === 'cdgtsOrder'
// order nodes are fixed at 40px via CSS (.order-node). Giving an explicit width makes React Flow compute bounds·hit-test
// with that value, so selection is judged wider than the on-screen 40px → omit width so the measured (40px) is used. data/process
// use .cdgts-node{width:100%}, so the wrapper needs a width; give them the default width.
export const nodeWidth = (slug, w) => (rfType(slug) === 'cdgtsOrder' ? undefined : (w || DEFAULT_NODE_WIDTH))

// order edge = boundary vertical port connection (ordering constraint) — shown dashed/purple, distinct from data flow.
const ORDER_EDGE_STYLE = { className: 'order-edge', style: { stroke: '#8b5cf6', strokeDasharray: '4 3' } }
// order ports are the vertical younger(source,top)/older(target,bottom) handles; a younger→older connection is an order edge.
export const isOrderConn = (srcH, tgtH) => srcH === 'younger' && tgtH === 'older'
// cite edge = reference node's citation(out) → any node's cited(in) handle. Provenance annotation, not data flow (amber dashed).
const CITE_EDGE_STYLE = { className: 'cite-edge', style: { stroke: '#c0842e', strokeDasharray: '2 3' } }
export const isCiteConn = (srcH, tgtH) => srcH === 'citation' && tgtH === 'cited'
export const edgeStyleFor = (kind) => (kind === 'order' ? ORDER_EDGE_STYLE : kind === 'cite' ? CITE_EDGE_STYLE : {})

// --- API ↔ React Flow conversion (nodes/edges are always the 'full real' set; the view is derived via buildView) ---
export function apiToRF(graph, typeMap, refMap = {}) {
  const nodes = graph.nodes.map((n) => {
    const t = typeMap[n.node_type] || { category: 'process', ports: [] }
    return {
      id: n.key, type: rfType(n.node_type), position: { x: n.x, y: n.y },
      width: nodeWidth(n.node_type, n.width),
      data: {
        nodeType: n.node_type, nature: n.nature || 'generic',
        label: n.label, description: n.description || '',
        params: n.params, category: t.category, ports: t.ports, group: n.group || null,
        referenceInfo: t.category === 'reference' ? refMap[n.params?.reference] || null : undefined,
      },
    }
  })
  const edges = graph.edges.map((e) => ({
    id: `${e.source}:${e.source_port}->${e.target}:${e.target_port}`,
    source: e.source, target: e.target,
    sourceHandle: e.source_port, targetHandle: e.target_port,
    data: { kind: e.kind },
    ...edgeStyleFor(e.kind),
  }))
  const groups = (graph.groups || []).map((g) => ({ ...g }))
  return { nodes, edges, groups }
}

export function rfToApi(nodes, edges, groups, viewport) {
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
export function buildView(nodes, edges, groups, activeGroup) {
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
    const gn = { id: `group:${g.key}`, type: 'cdgtsGroup', position: { x: g.x, y: g.y }, width: GROUP_NODE_WIDTH,
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
  const ioIn = { id: 'gio:in', type: 'cdgtsGroupIo', position: { x: minX - 340, y: cy }, width: GROUP_IO_WIDTH,
    data: { dir: 'in', ports: [] } }
  const ioOut = { id: 'gio:out', type: 'cdgtsGroupIo', position: { x: maxX + 240, y: cy }, width: GROUP_IO_WIDTH,
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

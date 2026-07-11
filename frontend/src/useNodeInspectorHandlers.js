import { useCallback } from 'react'

// Inspector field handlers, extracted from Editor.jsx (R02: decompose Editor.jsx, phase 2).
// A clean seam: these depend ONLY on setNodes/setGroups — thin patchers over a selected node's data
// (label/description/params/distribution) or a group's name. No entanglement with view/selection state.
export function useNodeInspectorHandlers(setNodes, setGroups) {
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

  const onGroupName = useCallback(
    (key, name) => setGroups((gs) => gs.map((g) => (g.key === key ? { ...g, name } : g))),
    [setGroups],
  )

  return { patchNodeData, onLabel, onDescription, onParam, onDist, onReplaceParams, onGroupName }
}

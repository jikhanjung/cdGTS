// Right-click / long-press context menu for the node editor — extracted from Editor.jsx (R02 decompose).
// Presentational: driven entirely by the `menu` descriptor + handlers passed down. Renders nothing when closed.
export default function EditorMenu({
  menu, canEdit, activeGroup, activeGroupObj, selectedIds, selectedGroupKeys,
  swallowLongPressClick, closeMenu, groupTargets, createOrMergeGroup,
  removeFromGroup, onDeleteNodes, onUngroup, onDeleteEdge, setActiveGroup,
}) {
  if (!menu) return null
  return (
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
            {canEdit && (selectedIds.length || selectedGroupKeys.filter((k) => k !== menu.groupKey).length) > 0 && (
              <li onClick={() => {
                createOrMergeGroup(selectedIds, [menu.groupKey, ...selectedGroupKeys.filter((k) => k !== menu.groupKey)])
                closeMenu()
              }}>Merge selection into this group ({selectedIds.length + selectedGroupKeys.filter((k) => k !== menu.groupKey).length})</li>
            )}
            {canEdit && <li onClick={() => { onUngroup(menu.groupKey); closeMenu() }}>Ungroup</li>}
          </>
        )}
        {menu.kind === 'pane' && canEdit && (
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
  )
}

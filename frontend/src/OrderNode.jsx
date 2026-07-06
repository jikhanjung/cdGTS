import { Handle, Position } from '@xyflow/react'

// Temporal ordering constraint (check). Two inputs stacked vertically: top=younger (smaller Ma) / bottom=older (larger Ma, below on ICC).
// Compact — a vertical inequality shows only 'which side is larger' (opens toward the larger side). Details (gap/Δ/mode) in the tooltip/inspector.
export default function OrderNode({ data, selected }) {
  const res = data.result?.distribution
  const ok = res && res.kind === 'order' ? res.ok : undefined
  const gap = res?.gap
  const dmin = data.params?.min_gap ?? 0
  const mode = data.params?.mode || 'hard'
  const hasGap = typeof gap === 'number'
  // Rotate the inequality 90° so it opens toward the larger value: gap≥0 → bottom (older) is larger → opens downward (-90°).
  const rot = hasGap ? (gap >= 0 ? -90 : 90) : 0
  const cls = `order-node${selected ? ' selected' : ''}${ok === false ? ' violated' : ''}${ok === true ? ' ok' : ''}`
  const tip = [
    'Temporal order: bottom (older) ≥ top (younger) + Δ',
    `Δ ≥ ${dmin} Ma · ${mode}`,
    hasGap ? `gap ${gap} ${ok ? '≥' : '<'} ${dmin} → ${ok ? 'pass' : 'violation'}` : 'input required',
  ].join('\n')

  return (
    <div className={cls} title={tip}>
      <Handle type="target" position={Position.Top} id="younger" />
      <span className={`order-node__ineq${hasGap ? '' : ' none'}`} style={{ transform: `rotate(${rot}deg)` }}>
        ≥
      </span>
      <Handle type="target" position={Position.Bottom} id="older" />
    </div>
  )
}

import { Handle, Position } from '@xyflow/react'

const ORDER_COLOR = '#8b5cf6'

// When a unit (span) group is drilled into, pin its upper/lower bounding boundaries at the top (upper) and bottom (lower) of the span.
// An order frame separate from the left/right Group Input/Output (data I/O). Because a boundary is a pass-through
// constraint through which values enter and leave, it has both input and output character (younger=source·top, older=target·bottom). Not validated (enforced) yet.
export default function BoundNode({ data }) {
  const upper = data.side === 'upper'
  return (
    <div className={`bound-node ${data.side}`}
         title={`${upper ? 'upper (younger)' : 'lower (older)'} boundary · ${data.label || ''}`}>
      <span className="bound-tag">{upper ? '▲ upper' : '▼ lower'}</span>
      <span className="bound-label">{data.label || '—'}</span>
      {/* order vertical ports — both input and output character: younger(source·top) / older(target·bottom) */}
      <Handle id="younger" type="source" position={Position.Top} className="vport" style={{ background: ORDER_COLOR }} />
      <Handle id="older" type="target" position={Position.Bottom} className="vport" style={{ background: ORDER_COLOR }} />
    </div>
  )
}

import { Handle, Position } from '@xyflow/react'

// order-participating vertical ports: younger=top / older=bottom (same convention as CdgtsNode).
const VPORT = { younger: Position.Top, older: Position.Bottom }
const ORDER_COLOR = '#8b5cf6'
const isV = (h) => h.port in VPORT
// If there are multiple top/bottom ports, spread them horizontally (mirrors topPct for left/right ports).
const leftPct = (i, n) => `${((i + 1) / (n + 1)) * 100}%`

// A collapsed node group = represented as a single node. Edges crossing the boundary automatically become I/O handles (automatic I/O matching).
// Double-click → drill into the group (handled by Editor).
export function GroupNode({ data, selected }) {
  const { name, inputs = [], outputs = [], count = 0 } = data
  const hIn = inputs.filter((h) => !isV(h))    // left inputs
  const hOut = outputs.filter((h) => !isV(h))  // right outputs
  // order vertical ports: input=target, output=source. Split into top/bottom and spread horizontally on each axis.
  const vAll = [
    ...inputs.filter(isV).map((h) => ({ ...h, htype: 'target' })),
    ...outputs.filter(isV).map((h) => ({ ...h, htype: 'source' })),
  ]
  const vTop = vAll.filter((h) => VPORT[h.port] === Position.Top)
  const vBot = vAll.filter((h) => VPORT[h.port] === Position.Bottom)
  const rows = Math.max(hIn.length, hOut.length, 1)
  return (
    <div className={`group-node${selected ? ' selected' : ''}`} style={{ minHeight: 40 + rows * 20 }}
         title="Double-click: open group">
      <div className="group-node__bar">
        <span className="group-node__icon">▤</span>
        <span className="group-node__name">{name}</span>
        <span className="group-node__count">{count}</span>
      </div>
      <div className="group-node__io">
        <ul className="gio in">{hIn.map((h) => <li key={h.id} title={h.label}>▸ {h.label}</li>)}</ul>
        <ul className="gio out">{hOut.map((h) => <li key={h.id} title={h.label}>{h.label} ▸</li>)}</ul>
      </div>
      {hIn.map((h, i) => (
        <Handle key={h.id} id={h.id} type="target" position={Position.Left}
                style={{ top: 40 + i * 20 }} />
      ))}
      {hOut.map((h, i) => (
        <Handle key={h.id} id={h.id} type="source" position={Position.Right}
                style={{ top: 40 + i * 20 }} />
      ))}
      {vTop.map((h, i) => (
        <Handle key={h.id} id={h.id} type={h.htype} position={Position.Top}
                className="vport" title={`${h.port} (order)`}
                style={{ left: leftPct(i, vTop.length), background: ORDER_COLOR }} />
      ))}
      {vBot.map((h, i) => (
        <Handle key={h.id} id={h.id} type={h.htype} position={Position.Bottom}
                className="vport" title={`${h.port} (order)`}
                style={{ left: leftPct(i, vBot.length), background: ORDER_COLOR }} />
      ))}
    </div>
  )
}

// Read-only interface stub that shows boundary-crossing connections inside a drill-in.
// Shows the group port (member side) together with the external source/destination: input `port ← peer`, output `port → peer`.
export function StubNode({ data }) {
  const inp = data.dir === 'in'
  const arrow = inp ? '←' : '→'
  return (
    <div className={`stub-node ${data.dir}`} title={`${data.port} ${arrow} ${data.peer}`}>
      <span className="stub-tag">{inp ? 'in' : 'out'}</span>
      <span className="stub-port">{data.port}</span>
      <span className="stub-arrow">{arrow}</span>
      <span className="stub-peer">{data.peer}</span>
      <Handle id={inp ? 'out' : 'in'} type={inp ? 'source' : 'target'}
              position={inp ? Position.Right : Position.Left} />
    </div>
  )
}

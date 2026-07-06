import { Handle, Position } from '@xyflow/react'

// Like the Group Input / Group Output of a Blender node group, aggregate the external connections of a drilled-in group into **a single node**.
// Input node = incoming external connections exposed as (multiple) right-side output ports; output node = outgoing internal connections exposed as
// (multiple) left-side input ports. Selectable/movable like a node (position remembered per drill-in by Editor).
export default function GroupIoNode({ data, selected }) {
  const inp = data.dir === 'in'
  const ports = data.ports || []
  return (
    <div className={`group-io-node ${data.dir}${selected ? ' selected' : ''}`}
         style={{ minHeight: 28 + ports.length * 22 }}
         title={inp ? 'Group Input (external → internal)' : 'Group Output (internal → external)'}>
      <div className="group-io__bar">{inp ? '⇥ Group Input' : 'Group Output ⇥'}</div>
      <ul className="group-io__ports">
        {ports.map((p) => (
          <li key={p.id} title={p.peer ? `${p.label} · ${p.peer}` : p.label}>
            {inp ? <>{p.label} <span className="a">▸</span></> : <><span className="a">▸</span> {p.label}</>}
          </li>
        ))}
      </ul>
      {ports.map((p, i) => (
        <Handle key={p.id} id={p.id} type={inp ? 'source' : 'target'}
                position={inp ? Position.Right : Position.Left}
                style={{ top: 30 + i * 22 }} />
      ))}
    </div>
  )
}

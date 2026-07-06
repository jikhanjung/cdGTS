import { Handle, Position, NodeResizeControl } from '@xyflow/react'

export const CATEGORY_COLOR = {
  data: '#2d7d46',      // observation leaf
  process: '#3b6fb0',   // transform·model
  clamp: '#a24bd8',     // governance gate
}

// Spread ports vertically (i-th / (n+1)).
const topPct = (i, n) => `${((i + 1) / (n + 1)) * 100}%`

// order vertical ports: younger=top (source, goes up to the younger neighbor) / older=bottom (target, comes down from the older neighbor).
// order edge = older boundary.younger(source) → younger boundary.older(target). Value is the same as out; position acts as a 'point on the time axis'.
const VPORT = { younger: Position.Top, older: Position.Bottom }
const VTYPE = { younger: 'source', older: 'target' }
const ORDER_COLOR = '#8b5cf6'

const BOUNDARY_COLOR = '#8b5cf6'   // order/boundary purple — distinguishes the skeleton (boundary points) from the machinery (data/process).
const UNIT_COLOR = '#a142f4'       // time span (unit) — same lavender family as node groups (Age subdivisions) for column consistency.

export default function CdgtsNode({ data, selected }) {
  const ports = data.ports || []
  const inputs = ports.filter((p) => p.direction === 'in')
  const outputs = ports.filter((p) => p.direction === 'out' && !(p.name in VPORT))
  const vports = ports.filter((p) => p.name in VPORT)
  const isBoundary = data.nature === 'boundary'
  const isUnit = data.nodeType === 'unit'
  const color = isBoundary ? BOUNDARY_COLOR : isUnit ? UNIT_COLOR : (CATEGORY_COLOR[data.category] || '#888')
  const rows = Math.max(inputs.length, outputs.length, 1)

  return (
    <div className={`cdgts-node${isBoundary ? ' boundary' : ''}${isUnit ? ' unit' : ''}`} style={{ borderColor: color }}>
      {selected && (
        <NodeResizeControl
          className="cdgts-resize" position="right" minWidth={140} maxWidth={440}
          style={{ background: 'transparent', border: 'none' }}
        />
      )}
      <div className="cdgts-node__header" style={{ background: color }}>
        <span className="cdgts-node__title" title={data.description || undefined}>
          {data.label || data.nodeType}
        </span>
        <span className="cdgts-node__cat">{isBoundary ? '◈ boundary' : isUnit ? '▭ time period' : data.category}</span>
      </div>
      {/* boundary shows title only (half height). Hide port labels and result but keep the handles. */}
      {!isBoundary && (
        <div className="cdgts-node__body" style={{ minHeight: rows * 22 }}>
          <ul className="ports in">
            {inputs.map((p) => (
              <li key={p.name} className={`port ${p.datatype}`}>{p.name}{p.multiple ? ' *' : ''}</li>
            ))}
          </ul>
          <ul className="ports out">
            {outputs.map((p) => (
              <li key={p.name} className={`port ${p.datatype}`}>{p.name}</li>
            ))}
          </ul>
        </div>
      )}
      {!isBoundary && data.result && (
        <div className="cdgts-node__result" title={data.result.cached ? 'cache reuse' : 'recomputed'}>
          {data.result.distribution && data.result.distribution.value_ma != null
            ? `${data.result.distribution.value_ma} Ma`
            : '—'}
          {data.result.cached && <span className="cached">•</span>}
        </div>
      )}

      {inputs.map((p, i) => (
        <Handle
          key={`in-${p.name}`}
          type="target"
          position={Position.Left}
          id={p.name}
          style={{ top: topPct(i, inputs.length), background: color }}
        />
      ))}
      {outputs.map((p, i) => (
        <Handle
          key={`out-${p.name}`}
          type="source"
          position={Position.Right}
          id={p.name}
          style={{ top: topPct(i, outputs.length), background: color }}
        />
      ))}
      {vports.map((p) => (
        <Handle
          key={`v-${p.name}`}
          type={VTYPE[p.name]}
          position={VPORT[p.name]}
          id={p.name}
          title={`${p.name} (order)`}
          className="vport"
          style={{ background: ORDER_COLOR }}
        />
      ))}
    </div>
  )
}

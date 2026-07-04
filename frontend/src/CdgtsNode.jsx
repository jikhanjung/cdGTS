import { Handle, Position, NodeResizeControl } from '@xyflow/react'

export const CATEGORY_COLOR = {
  data: '#2d7d46',      // 관측 leaf
  process: '#3b6fb0',   // 변환·모델
  clamp: '#a24bd8',     // 거버넌스 게이트
}

// 포트를 세로로 분산 배치 (i번째 / (n+1)).
const topPct = (i, n) => `${((i + 1) / (n + 1)) * 100}%`

export default function CdgtsNode({ data, selected }) {
  const ports = data.ports || []
  const inputs = ports.filter((p) => p.direction === 'in')
  const outputs = ports.filter((p) => p.direction === 'out')
  const color = CATEGORY_COLOR[data.category] || '#888'
  const rows = Math.max(inputs.length, outputs.length, 1)

  return (
    <div className="cdgts-node" style={{ borderColor: color }}>
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
        <span className="cdgts-node__cat">{data.category}</span>
      </div>
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
      {data.result && (
        <div className="cdgts-node__result" title={data.result.cached ? '캐시 재사용' : '재계산'}>
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
    </div>
  )
}

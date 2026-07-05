import { Handle, Position, NodeResizeControl } from '@xyflow/react'

export const CATEGORY_COLOR = {
  data: '#2d7d46',      // 관측 leaf
  process: '#3b6fb0',   // 변환·모델
  clamp: '#a24bd8',     // 거버넌스 게이트
}

// 포트를 세로로 분산 배치 (i번째 / (n+1)).
const topPct = (i, n) => `${((i + 1) / (n + 1)) * 100}%`

// order 참여용 세로 포트(위=older, 아래=younger). 값 자체는 side 'out' 과 동일 —
// 위치가 '시간축 위의 점' 역할을 표현. 위=older 는 위쪽(younger 이웃) order 로 올라가기 때문.
const VPORT = { older: Position.Top, younger: Position.Bottom }
const ORDER_COLOR = '#a24bd8'

export default function CdgtsNode({ data, selected }) {
  const ports = data.ports || []
  const inputs = ports.filter((p) => p.direction === 'in')
  const outputs = ports.filter((p) => p.direction === 'out' && !(p.name in VPORT))
  const vouts = ports.filter((p) => p.direction === 'out' && p.name in VPORT)
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
      {vouts.map((p) => (
        <Handle
          key={`v-${p.name}`}
          type="source"
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

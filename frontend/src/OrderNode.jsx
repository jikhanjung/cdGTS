import { Handle, Position } from '@xyflow/react'

// 시간적 선후 제약(검사). 입력 2개를 세로로: 위=younger(작은 Ma) / 아래=older(큰 Ma, ICC 아래).
// 값을 흘리지 않는 sink — 몸통에 판정(✓/⚠ + gap)을 인라인 표시. 판정은 coherence certificate 로도 감.
export default function OrderNode({ data, selected }) {
  const res = data.result?.distribution
  const ok = res && res.kind === 'order' ? res.ok : undefined
  const gap = res?.gap
  const dmin = data.params?.min_gap ?? 0
  const mode = data.params?.mode || 'hard'
  const cls = `order-node${selected ? ' selected' : ''}${ok === false ? ' violated' : ''}${ok === true ? ' ok' : ''}`

  return (
    <div className={cls} title="시간적 선후 제약 (아래=older ≥ 위=younger + Δ)">
      <Handle type="target" position={Position.Top} id="younger" />
      <div className="order-node__port top">younger ⌃</div>
      <div className="order-node__body">
        <div className="order-node__title">⧗ {data.label || 'order'}</div>
        <div className="order-node__rule">Δ ≥ {dmin} Ma · {mode}</div>
        {ok !== undefined && ok !== null && (
          <div className={`order-node__verdict ${ok ? 'good' : 'bad'}`}>
            {ok ? '✓' : '⚠'} gap {gap} {ok ? '≥' : '<'} {dmin}
          </div>
        )}
        {ok === null && <div className="order-node__verdict none">입력 필요</div>}
      </div>
      <div className="order-node__port bottom">older ⌄ (ICC 아래)</div>
      <Handle type="target" position={Position.Bottom} id="older" />
    </div>
  )
}

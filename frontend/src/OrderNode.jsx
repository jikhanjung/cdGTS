import { Handle, Position } from '@xyflow/react'

// 시간적 선후 제약(검사). 입력 2개를 세로로: 위=younger(작은 Ma) / 아래=older(큰 Ma, ICC 아래).
// 컴팩트 — 세로 부등호로 '어느 쪽이 큰지' 만 표시(큰 쪽으로 열림). 상세(gap/Δ/mode)는 툴팁·인스펙터.
export default function OrderNode({ data, selected }) {
  const res = data.result?.distribution
  const ok = res && res.kind === 'order' ? res.ok : undefined
  const gap = res?.gap
  const dmin = data.params?.min_gap ?? 0
  const mode = data.params?.mode || 'hard'
  const hasGap = typeof gap === 'number'
  // 부등호를 90° 회전해 큰 값 쪽으로 열림: gap≥0 → 아래(older) 큼 → 아래로 열림(-90°).
  const rot = hasGap ? (gap >= 0 ? -90 : 90) : 0
  const cls = `order-node${selected ? ' selected' : ''}${ok === false ? ' violated' : ''}${ok === true ? ' ok' : ''}`
  const tip = [
    '시간적 선후: 아래(older) ≥ 위(younger) + Δ',
    `Δ ≥ ${dmin} Ma · ${mode}`,
    hasGap ? `gap ${gap} ${ok ? '≥' : '<'} ${dmin} → ${ok ? '통과' : '위반'}` : '입력 필요',
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

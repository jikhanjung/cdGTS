import { Handle, Position } from '@xyflow/react'

// order 참여 세로 포트: 위=older / 아래=younger (CdgtsNode·OrderNode 와 동일 규약).
const VPORT = { older: Position.Top, younger: Position.Bottom }
const ORDER_COLOR = '#a24bd8'
const isV = (h) => h.port in VPORT
// 상/하 포트가 여러 개면 가로로 분산 (좌/우 포트의 topPct 대응).
const leftPct = (i, n) => `${((i + 1) / (n + 1)) * 100}%`

// 접힌 노드그룹 = 하나의 노드로 표현. 경계를 넘는 엣지가 자동으로 입출력 핸들이 된다(입출력 자동 정합).
// 더블클릭 → 그룹 내부로 드릴인(Editor 가 처리).
export function GroupNode({ data, selected }) {
  const { name, inputs = [], outputs = [], count = 0 } = data
  const hIn = inputs.filter((h) => !isV(h))    // 좌측 입력
  const hOut = outputs.filter((h) => !isV(h))  // 우측 출력
  // order 세로 포트: 입력=target, 출력=source. 위/아래로 나눠 각 축에서 가로 분산.
  const vAll = [
    ...inputs.filter(isV).map((h) => ({ ...h, htype: 'target' })),
    ...outputs.filter(isV).map((h) => ({ ...h, htype: 'source' })),
  ]
  const vTop = vAll.filter((h) => VPORT[h.port] === Position.Top)
  const vBot = vAll.filter((h) => VPORT[h.port] === Position.Bottom)
  const rows = Math.max(hIn.length, hOut.length, 1)
  return (
    <div className={`group-node${selected ? ' selected' : ''}`} style={{ minHeight: 40 + rows * 20 }}
         title="더블클릭: 그룹 열기">
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

// 드릴인 내부에서 경계를 넘는 연결을 보여주는 읽기전용 인터페이스 스텁.
// 그룹 포트(멤버 쪽) + 외부 출처/도착을 함께 표기: 입력 `port ← peer`, 출력 `port → peer`.
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

import { Handle, Position } from '@xyflow/react'

// 접힌 노드그룹 = 하나의 노드로 표현. 경계를 넘는 엣지가 자동으로 입출력 핸들이 된다(입출력 자동 정합).
// 더블클릭 → 그룹 내부로 드릴인(Editor 가 처리).
export function GroupNode({ data, selected }) {
  const { name, inputs = [], outputs = [], count = 0 } = data
  const rows = Math.max(inputs.length, outputs.length, 1)
  return (
    <div className={`group-node${selected ? ' selected' : ''}`} style={{ minHeight: 40 + rows * 20 }}
         title="더블클릭: 그룹 열기">
      <div className="group-node__bar">
        <span className="group-node__icon">▤</span>
        <span className="group-node__name">{name}</span>
        <span className="group-node__count">{count}</span>
      </div>
      <div className="group-node__io">
        <ul className="gio in">{inputs.map((h) => <li key={h.id} title={h.label}>▸ {h.label}</li>)}</ul>
        <ul className="gio out">{outputs.map((h) => <li key={h.id} title={h.label}>{h.label} ▸</li>)}</ul>
      </div>
      {inputs.map((h, i) => (
        <Handle key={h.id} id={h.id} type="target" position={Position.Left}
                style={{ top: 40 + i * 20 }} />
      ))}
      {outputs.map((h, i) => (
        <Handle key={h.id} id={h.id} type="source" position={Position.Right}
                style={{ top: 40 + i * 20 }} />
      ))}
    </div>
  )
}

// 드릴인 내부에서 경계를 넘는 연결을 보여주는 읽기전용 인터페이스 스텁(외부 노드 대리 표시).
export function StubNode({ data }) {
  const inp = data.dir === 'in'
  return (
    <div className={`stub-node ${data.dir}`} title={data.label}>
      {inp ? '▸ ' : ''}{data.label}{inp ? '' : ' ▸'}
      <Handle id={inp ? 'out' : 'in'} type={inp ? 'source' : 'target'}
              position={inp ? Position.Right : Position.Left} />
    </div>
  )
}

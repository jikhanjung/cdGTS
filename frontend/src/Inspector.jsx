import { useState } from 'react'
import { CATEGORY_COLOR } from './CdgtsNode.jsx'

// distribution 충실도 사다리 (nodes/distribution.py FIDELITY_LADDER 와 동기).
const FIDELITY = ['exact', 'sym', 'decomposed', 'shape', 'joint', 'full']
const BUDGET_KEYS = ['analytical', 'systematic', 'model']

const numOrUndef = (v) => (v === '' || v == null ? undefined : Number(v))

// --- 개별 파라미터 컨트롤 ---
function ParamField({ name, spec, value, nodeKeys, onParam, onDist }) {
  const help = spec.help
  const label = (
    <label className="insp-label" title={help || ''}>
      {name}{help && <span className="insp-help"> ⓘ</span>}
    </label>
  )

  switch (spec.type) {
    case 'number':
      return (
        <div className="insp-field">
          {label}
          <input
            type="number" step="any" className="insp-input"
            defaultValue={value ?? ''}
            onChange={(e) => onParam(name, numOrUndef(e.target.value))}
          />
        </div>
      )

    case 'string':
      return (
        <div className="insp-field">
          {label}
          <input
            type="text" className="insp-input"
            defaultValue={value ?? ''}
            onChange={(e) => onParam(name, e.target.value === '' ? undefined : e.target.value)}
          />
        </div>
      )

    case 'enum':
      return (
        <div className="insp-field">
          {label}
          <select
            className="insp-input"
            value={value ?? spec.default ?? ''}
            onChange={(e) => onParam(name, e.target.value === '' ? undefined : e.target.value)}
          >
            <option value="">—</option>
            {(spec.choices || []).map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      )

    case 'multi-enum': {
      const arr = Array.isArray(value) ? value : []
      return (
        <div className="insp-field">
          {label}
          <div className="insp-checks">
            {(spec.choices || []).map((c) => (
              <label key={c} className="insp-check">
                <input
                  type="checkbox" checked={arr.includes(c)}
                  onChange={(e) => {
                    const next = e.target.checked ? [...arr, c] : arr.filter((x) => x !== c)
                    onParam(name, next.length ? next : undefined)
                  }}
                />
                {c}
              </label>
            ))}
          </div>
        </div>
      )
    }

    case 'node_ref':
      return (
        <div className="insp-field">
          {label}
          <select
            className="insp-input"
            value={value ?? ''}
            onChange={(e) => onParam(name, e.target.value === '' ? undefined : e.target.value)}
          >
            <option value="">—</option>
            {nodeKeys.map((k) => <option key={k.id} value={k.id}>{k.label}</option>)}
          </select>
        </div>
      )

    case 'distribution':
      return <DistributionField name={name} value={value || {}} onDist={onDist} />

    default:
      return (
        <div className="insp-field">
          {label}
          <div className="insp-note">지원하지 않는 타입 <code>{spec.type}</code> — 아래 JSON 에서 편집.</div>
        </div>
      )
  }
}

// distribution 값 객체 서브폼 (자주 쓰는 필드만; 깊은 필드는 고급 JSON).
function DistributionField({ name, value, onDist }) {
  const isExact = value.fidelity === 'exact'
  return (
    <fieldset className="insp-dist">
      <legend>{name} · distribution</legend>
      <div className="insp-field">
        <label className="insp-label">fidelity</label>
        <select
          className="insp-input" value={value.fidelity ?? ''}
          onChange={(e) => onDist(name, 'fidelity', e.target.value || undefined)}
        >
          <option value="">—</option>
          {FIDELITY.map((f) => <option key={f} value={f}>{f}</option>)}
        </select>
      </div>
      <div className="insp-field">
        <label className="insp-label">value_ma</label>
        <input
          type="number" step="any" className="insp-input"
          defaultValue={value.value_ma ?? ''}
          onChange={(e) => onDist(name, 'value_ma', numOrUndef(e.target.value))}
        />
      </div>
      {!isExact && (
        <>
          <div className="insp-field">
            <label className="insp-label">sigma (1|2)</label>
            <select
              className="insp-input" value={value.sigma ?? ''}
              onChange={(e) => onDist(name, 'sigma', numOrUndef(e.target.value))}
            >
              <option value="">—</option>
              <option value="1">1</option>
              <option value="2">2</option>
            </select>
          </div>
          {BUDGET_KEYS.map((bk) => (
            <div className="insp-field" key={bk}>
              <label className="insp-label">budget.{bk}</label>
              <input
                type="number" step="any" className="insp-input"
                defaultValue={value.budget?.[bk] ?? ''}
                onChange={(e) => onDist(name, `budget.${bk}`, numOrUndef(e.target.value))}
              />
            </div>
          ))}
        </>
      )}
      <div className="insp-field">
        <label className="insp-label">note</label>
        <input
          type="text" className="insp-input"
          defaultValue={value.note ?? ''}
          onChange={(e) => onDist(name, 'note', e.target.value || undefined)}
        />
      </div>
    </fieldset>
  )
}

// --- 인스펙터 패널 ---
export default function Inspector({ node, type, nodeKeys, open, onClose, onLabel, onDescription, onParam, onDist, onReplaceParams }) {
  const cls = `inspector${open ? ' open' : ''}`
  if (!node) {
    return <aside className={`${cls} empty`}><p className="hint">노드를 선택하면 속성이 여기 표시됩니다.</p></aside>
  }

  const params = node.data.params || {}
  const schema = (type && type.params_schema) || {}
  const schemaKeys = Object.keys(schema)
  const color = CATEGORY_COLOR[node.data.category] || '#888'

  return (
    <aside className={cls}>
      <div className="insp-head" style={{ borderTopColor: color }}>
        <div className="insp-type">{node.data.nodeType} <span className="insp-cat">{node.data.category}</span></div>
        <button className="mobile-only insp-close" onClick={onClose} title="닫기">✕</button>
      </div>

      {node.data.result?.distribution?.kind === 'order' && (
        <div className={`insp-verdict ${node.data.result.distribution.ok ? 'good'
          : node.data.result.distribution.ok === false ? 'bad' : 'none'}`}>
          {node.data.result.distribution.ok == null
            ? '입력 필요'
            : `아래(older) ≥ 위(younger): gap ${node.data.result.distribution.gap} `
              + `${node.data.result.distribution.ok ? '≥' : '<'} ${params.min_gap ?? 0} `
              + `→ ${node.data.result.distribution.ok ? '통과' : '위반'}`}
        </div>
      )}

      <div className="insp-field">
        <label className="insp-label">label</label>
        <input
          type="text" className="insp-input"
          defaultValue={node.data.label ?? ''} placeholder={node.data.nodeType}
          onChange={(e) => onLabel(e.target.value)}
        />
      </div>

      <div className="insp-field">
        <label className="insp-label">description</label>
        <textarea
          className="insp-input insp-desc" rows={3}
          defaultValue={node.data.description ?? ''}
          placeholder="상세 설명 — 제목은 짧게, 여기 자세히 (노드 제목 툴팁에 표시)"
          onChange={(e) => onDescription(e.target.value)}
        />
      </div>

      {schemaKeys.length === 0
        ? <p className="insp-note">이 노드 타입은 정의된 파라미터가 없습니다.</p>
        : schemaKeys.map((k) => (
            <ParamField
              key={k} name={k} spec={schema[k]} value={params[k]}
              nodeKeys={nodeKeys} onParam={onParam} onDist={onDist}
            />
          ))}

      <RawJson params={params} onReplaceParams={onReplaceParams} />

      <p className="insp-foot">변경 후 툴바의 <b>저장</b> 을 눌러 반영하세요.</p>
    </aside>
  )
}

// 폼에 없는 깊은 필드(shape·shared_components 등) 편집용 원본 JSON.
function RawJson({ params, onReplaceParams }) {
  const [err, setErr] = useState(null)
  return (
    <details className="insp-raw">
      <summary>고급: 원본 JSON</summary>
      <textarea
        className="insp-json" spellCheck={false}
        defaultValue={JSON.stringify(params, null, 2)}
        onChange={(e) => {
          try {
            const obj = JSON.parse(e.target.value)
            setErr(null)
            onReplaceParams(obj)
          } catch (ex) {
            setErr(String(ex.message || ex))
          }
        }}
      />
      {err && <div className="insp-json-err">{err}</div>}
    </details>
  )
}

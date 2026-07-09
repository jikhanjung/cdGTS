import { useState } from 'react'
import { CATEGORY_COLOR } from './CdgtsNode.jsx'

// distribution fidelity ladder (kept in sync with nodes/distribution.py FIDELITY_LADDER).
const FIDELITY = ['exact', 'sym', 'decomposed', 'shape', 'joint', 'full']
const BUDGET_KEYS = ['analytical', 'systematic', 'model']

const numOrUndef = (v) => (v === '' || v == null ? undefined : Number(v))

// --- Individual parameter controls ---
function ParamField({ name, spec, value, nodeKeys, references, onCreateReference, onParam, onDist }) {
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

    case 'reference':
      return (
        <ReferenceField
          name={name} value={value} references={references || []}
          onParam={onParam} onCreateReference={onCreateReference}
        />
      )

    case 'distribution':
      return <DistributionField name={name} value={value || {}} onDist={onDist} />

    default:
      return (
        <div className="insp-field">
          {label}
          <div className="insp-note">Unsupported type <code>{spec.type}</code> — edit in the JSON below.</div>
        </div>
      )
  }
}

// distribution value-object subform (common fields only; deep fields use the advanced JSON).
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

// reference param — pick a source from the DOI-centric registry, or add a new one inline.
function ReferenceField({ name, value, references, onParam, onCreateReference }) {
  const [adding, setAdding] = useState(false)
  const current = references.find((r) => r.slug === value)
  return (
    <div className="insp-field">
      <label className="insp-label">{name} · source</label>
      <select
        className="insp-input" value={value ?? ''}
        onChange={(e) => onParam(name, e.target.value || undefined)}
      >
        <option value="">—</option>
        {references.map((r) => (
          <option key={r.slug} value={r.slug}>
            {(r.authors || r.slug)}{r.year ? ` (${r.year})` : ''}
          </option>
        ))}
      </select>
      {current && (
        <div className="insp-ref-meta">
          <div className="insp-ref-title">{current.title}</div>
          {current.link
            ? <a href={current.link} target="_blank" rel="noreferrer" className="insp-ref-link">
                {current.doi ? `doi:${current.doi}` : current.link} ↗
              </a>
            : <span className="insp-note">no DOI / URL</span>}
        </div>
      )}
      {adding
        ? <NewReferenceForm
            onCreate={async (body) => { const r = await onCreateReference(body); onParam(name, r.slug); setAdding(false) }}
            onCancel={() => setAdding(false)}
          />
        : <button type="button" className="insp-linkbtn" onClick={() => setAdding(true)}>＋ new reference</button>}
    </div>
  )
}

function NewReferenceForm({ onCreate, onCancel }) {
  const [f, setF] = useState({ slug: '', doi: '', title: '', authors: '', year: '' })
  const [err, setErr] = useState(null)
  const set = (k) => (e) => setF((prev) => ({ ...prev, [k]: e.target.value }))
  const submit = async () => {
    if (!f.slug || !f.title) { setErr('slug and title are required'); return }
    try {
      await onCreate({
        slug: f.slug, doi: f.doi || '', title: f.title,
        authors: f.authors || '', year: f.year ? Number(f.year) : null,
      })
      setErr(null)
    } catch (ex) { setErr(ex?.data ? JSON.stringify(ex.data) : String(ex.message || ex)) }
  }
  return (
    <div className="insp-newref">
      <input className="insp-input" placeholder="slug (e.g. cohen-2013)" value={f.slug} onChange={set('slug')} />
      <input className="insp-input" placeholder="DOI (10.xxxx/…)" value={f.doi} onChange={set('doi')} />
      <input className="insp-input" placeholder="title" value={f.title} onChange={set('title')} />
      <input className="insp-input" placeholder="authors" value={f.authors} onChange={set('authors')} />
      <input className="insp-input" type="number" placeholder="year" value={f.year} onChange={set('year')} />
      {err && <div className="insp-json-err">{err}</div>}
      <div className="insp-newref-actions">
        <button type="button" onClick={submit}>Add</button>
        <button type="button" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  )
}

// --- Inspector panel ---
export default function Inspector({ node, type, group, groupExtra, nodeKeys, references, onCreateReference, open, onClose, onHide, onLabel, onDescription, onParam, onDist, onReplaceParams, onGroupName }) {
  const cls = `inspector${open ? ' open' : ''}`
  if (!node && group) {
    return <GroupInspector cls={cls} group={group} extra={groupExtra} onClose={onClose} onHide={onHide} onGroupName={onGroupName} />
  }
  if (!node) {
    return (
      <aside className={`${cls} empty`}>
        <button className="desktop-only insp-close insp-hide" onClick={onHide} title="Hide panel">✕</button>
        <p className="hint">Select a node or group to see its properties here.</p>
      </aside>
    )
  }

  const params = node.data.params || {}
  const schema = (type && type.params_schema) || {}
  const schemaKeys = Object.keys(schema)
  const color = CATEGORY_COLOR[node.data.category] || '#888'

  return (
    <aside className={cls}>
      <div className="insp-head" style={{ borderTopColor: color }}>
        <div className="insp-type">{node.data.nodeType} <span className="insp-cat">{node.data.category}</span></div>
        <button className="mobile-only insp-close" onClick={onClose} title="Close">✕</button>
        <button className="desktop-only insp-close" onClick={onHide} title="Hide panel">✕</button>
      </div>

      {node.data.result?.distribution?.value_ma != null && (
        <div className="insp-result" title={node.data.result.cached ? 'cache reuse' : 'recomputed'}>
          <span className="insp-result-lbl">result age</span>
          <span className="insp-result-val">{node.data.result.distribution.value_ma} Ma</span>
          {node.data.result.cached && <span className="insp-result-cached">•</span>}
        </div>
      )}

      {node.data.result?.distribution?.kind === 'order' && (
        <div className={`insp-verdict ${node.data.result.distribution.ok ? 'good'
          : node.data.result.distribution.ok === false ? 'bad' : 'none'}`}>
          {node.data.result.distribution.ok == null
            ? 'Input required'
            : `below (older) ≥ above (younger): gap ${node.data.result.distribution.gap} `
              + `${node.data.result.distribution.ok ? '≥' : '<'} ${params.min_gap ?? 0} `
              + `→ ${node.data.result.distribution.ok ? 'pass' : 'violation'}`}
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
          placeholder="Detailed description — keep the title short, put details here (shown in the node title tooltip)"
          onChange={(e) => onDescription(e.target.value)}
        />
      </div>

      {schemaKeys.length === 0
        ? <p className="insp-note">This node type has no defined parameters.</p>
        : schemaKeys.map((k) => (
            <ParamField
              key={k} name={k} spec={schema[k]} value={params[k]}
              nodeKeys={nodeKeys} references={references} onCreateReference={onCreateReference}
              onParam={onParam} onDist={onDist}
            />
          ))}

      <RawJson params={params} onReplaceParams={onReplaceParams} />

      <p className="insp-foot">After making changes, click <b>Save</b> in the toolbar to apply them.</p>
    </aside>
  )
}

// --- Group inspector (shown when a node group / collapsed group node is selected) ---
function GroupInspector({ cls, group, extra, onClose, onHide, onGroupName }) {
  const isUnit = group.kind === 'unit'
  const color = '#a142f4'   // lavender — matches the group node
  return (
    <aside className={cls}>
      <div className="insp-head" style={{ borderTopColor: color }}>
        <div className="insp-type">node group <span className="insp-cat">{group.kind || 'container'}</span></div>
        <button className="mobile-only insp-close" onClick={onClose} title="Close">✕</button>
        <button className="desktop-only insp-close" onClick={onHide} title="Hide panel">✕</button>
      </div>

      <div className="insp-field">
        <label className="insp-label">name</label>
        <input
          type="text" className="insp-input"
          defaultValue={group.name ?? ''} placeholder={group.key}
          onChange={(e) => onGroupName(e.target.value)}
        />
      </div>

      <dl className="insp-meta">
        <dt>key</dt><dd><code>{group.key}</code></dd>
        <dt>members</dt>
        <dd>{extra?.count ?? 0}{extra?.subgroups ? ` · ${extra.subgroups} subgroup${extra.subgroups > 1 ? 's' : ''}` : ''}</dd>
        <dt>collapsed</dt><dd>{group.collapsed ? 'yes' : 'no'}</dd>
        {isUnit && (
          <>
            <dt>unit</dt><dd>{group.unit ? <code>{group.unit}</code> : '—'}</dd>
            <dt>upper · younger</dt><dd>{extra?.upperLabel || '—'}</dd>
            <dt>lower · older</dt><dd>{extra?.lowerLabel || '—'}</dd>
          </>
        )}
      </dl>

      {isUnit && (
        <p className="insp-note">
          Time-span group (1-cell): bounded by its lower/older and upper/younger boundary nodes,
          and bound to a canonical chrono unit. Its bounding boundaries stay visible when you drill in.
        </p>
      )}
      <p className="insp-foot">After making changes, click <b>Save</b> in the toolbar to apply them.</p>
    </aside>
  )
}

// Raw JSON for editing deep fields not in the form (shape, shared_components, etc.).
function RawJson({ params, onReplaceParams }) {
  const [err, setErr] = useState(null)
  return (
    <details className="insp-raw">
      <summary>Advanced: raw JSON</summary>
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

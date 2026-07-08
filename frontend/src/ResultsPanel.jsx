// Readable summary of the distributions of the final outputs (gateway / terminal nodes) from an evaluation.

// distribution value object → display summary (matches the nodes/distribution.py ladder).
export function summarizeDist(dist) {
  if (!dist) return null
  const f = dist.fidelity
  const v = dist.value_ma
  const budget = dist.budget || {}
  const combined = Math.sqrt(
    Object.values(budget).reduce((s, x) => s + (Number(x) || 0) ** 2, 0),
  )

  if (f === 'exact') return { value: v, kind: 'exact' }
  if (f === 'shape' && dist.shape && Array.isArray(dist.shape.hpd95)) {
    const [lo, hi] = dist.shape.hpd95
    const med = dist.shape.median ?? v
    return { value: med, lo, hi, kind: 'shape' }
  }
  if (combined > 0) {
    return { value: v, pm: combined, sigma: dist.sigma, kind: f || 'sym', budget }
  }
  return { value: v, kind: f || 'unknown' }
}

const fmt = (x) => (x == null ? '—' : `${Number(x.toPrecision(7))}`)

function Uncertainty({ s }) {
  if (!s) return null
  if (s.kind === 'exact') return <span className="rc-unc exact">exact · no error</span>
  if (s.kind === 'shape' && s.lo != null && s.hi != null) {
    return <span className="rc-unc">95% HPD [{fmt(s.lo)}, {fmt(s.hi)}]</span>
  }
  if (s.pm != null) {
    return <span className="rc-unc">± {fmt(s.pm)}{s.sigma ? ` (${s.sigma}σ)` : ''} Myr</span>
  }
  return <span className="rc-unc muted">no uncertainty information</span>
}

function ResultCard({ out }) {
  const s = summarizeDist(out.dist)
  const hasVal = s && s.value != null
  return (
    <div className={`result-card ${out.source}`}>
      <div className="rc-head">
        <span className="rc-title" title={out.title}>{out.title}</span>
        {out.boundary && <span className="rc-boundary">{out.boundary}</span>}
        <span className={`rc-src ${out.source}`}>{out.source === 'gateway' ? 'gateway' : 'terminal'}</span>
      </div>

      {out.missing ? (
        <div className="rc-empty">No evaluation result — run <b>Evaluate</b>.</div>
      ) : hasVal ? (
        <>
          <div className="rc-value">{fmt(s.value)} <span className="rc-ma">Ma</span></div>
          <Uncertainty s={s} />
          <div className="rc-meta">
            {s.kind && <span className="rc-fidelity">{s.kind}</span>}
            {out.provenance?.length > 0 && <span className="rc-prov">{out.provenance.length} source nodes</span>}
          </div>
          {out.dist?.note && <div className="rc-note" title={out.dist.note}>{out.dist.note}</div>}
        </>
      ) : (
        <div className="rc-empty">No numeric output (signal / no-data node).</div>
      )}
    </div>
  )
}

const CERT_ORDER = ['L0', 'L1', 'L1b', 'L2', 'L3']
const CERT_LABEL = { L0: 'structure', L1: 'order', L1b: 'order 2σ', L2: 'duration', L3: 'reconcile' }

function certStatus(cert) {
  const c = cert.checks || {}
  if (!cert.passed) return 'fail'
  return CERT_ORDER.some((k) => c[k] === 'warn') ? 'warn' : 'pass'
}

export default function ResultsPanel({ outputs, meta, onClose }) {
  const cert = meta?.certificate
  const checks = cert?.checks || {}
  const notes = checks.notes || []
  return (
    <section className="results">
      <header className="results-head">
        <span className="results-title">Results <b>{outputs.length}</b></span>
        {meta?.stats && (
          <span className="results-stats">
            run#{meta.id} · computed {meta.stats.computed} / cached {meta.stats.cached}
          </span>
        )}
        {cert && (
          <span className={`results-cert ${certStatus(cert)}`}>
            consistency {certStatus(cert)}
            {CERT_ORDER.filter((k) => checks[k] && checks[k] !== 'skip').map((k) => (
              <span key={k} className={`cert-chip ${checks[k]}`} title={`${CERT_LABEL[k]} — ${checks[k]}`}>{k}</span>
            ))}
          </span>
        )}
        <button className="results-close" onClick={onClose} title="Close">✕</button>
      </header>
      {notes.length > 0 && (
        <div className="results-notes">{notes.map((n, i) => <div key={i}>⚠ {n}</div>)}</div>
      )}
      {outputs.length === 0 ? (
        <div className="results-empty">No output nodes. Designate a gateway or connect a terminal node.</div>
      ) : (
        <div className="results-cards">
          {outputs.map((out) => <ResultCard key={out.id} out={out} />)}
        </div>
      )}
    </section>
  )
}

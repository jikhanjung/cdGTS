// 평가 결과에서 최종 출력(gateway/말단 노드)의 분포를 읽기 좋게 요약.

// distribution 값 객체 → 표시용 요약 (nodes/distribution.py 사다리 대응).
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
  if (s.kind === 'exact') return <span className="rc-unc exact">exact · 오차 없음</span>
  if (s.kind === 'shape' && s.lo != null && s.hi != null) {
    return <span className="rc-unc">95% HPD [{fmt(s.lo)}, {fmt(s.hi)}]</span>
  }
  if (s.pm != null) {
    return <span className="rc-unc">± {fmt(s.pm)}{s.sigma ? ` (${s.sigma}σ)` : ''} Myr</span>
  }
  return <span className="rc-unc muted">불확실성 정보 없음</span>
}

function ResultCard({ out }) {
  const s = summarizeDist(out.dist)
  const hasVal = s && s.value != null
  return (
    <div className={`result-card ${out.source}`}>
      <div className="rc-head">
        <span className="rc-title" title={out.title}>{out.title}</span>
        {out.boundary && <span className="rc-boundary">{out.boundary}</span>}
        <span className={`rc-src ${out.source}`}>{out.source === 'gateway' ? '게이트웨이' : '말단'}</span>
      </div>

      {out.missing ? (
        <div className="rc-empty">평가 결과 없음 — <b>평가</b> 를 실행하세요.</div>
      ) : hasVal ? (
        <>
          <div className="rc-value">{fmt(s.value)} <span className="rc-ma">Ma</span></div>
          <Uncertainty s={s} />
          <div className="rc-meta">
            {s.kind && <span className="rc-fidelity">{s.kind}</span>}
            {out.provenance?.length > 0 && <span className="rc-prov">출처 노드 {out.provenance.length}</span>}
          </div>
          {out.dist?.note && <div className="rc-note" title={out.dist.note}>{out.dist.note}</div>}
        </>
      ) : (
        <div className="rc-empty">수치 출력 없음 (신호/무데이터 노드).</div>
      )}
    </div>
  )
}

export default function ResultsPanel({ outputs, meta, onClose }) {
  const cert = meta?.certificate
  return (
    <section className="results">
      <header className="results-head">
        <span className="results-title">결과 <b>{outputs.length}</b></span>
        {meta?.stats && (
          <span className="results-stats">
            run#{meta.id} · computed {meta.stats.computed} / cached {meta.stats.cached}
          </span>
        )}
        {cert && (
          <span className={`results-cert ${cert.passed ? 'pass' : 'warn'}`}>
            정합성 {cert.passed ? 'pass' : 'warn'}
          </span>
        )}
        <button className="results-close" onClick={onClose} title="닫기">✕</button>
      </header>
      {outputs.length === 0 ? (
        <div className="results-empty">출력 노드가 없습니다. 게이트웨이를 지정하거나 말단 노드를 연결하세요.</div>
      ) : (
        <div className="results-cards">
          {outputs.map((out) => <ResultCard key={out.id} out={out} />)}
        </div>
      )}
    </section>
  )
}

// Science CI — 그래프 재bake 결과를 공표 기준 릴리스와 비교한 diff 요약.
// value_diff.delta = 내 그래프 − 공표 (내 편집이 경계를 얼마나 이동시켰나). topology = 배선 변화.

const fmtMa = (v) => (v == null ? '—' : Number(v).toFixed(3))
const deltaClass = (d) => (d == null ? '' : Math.abs(d) < 0.01 ? 'noise' : d > 0 ? 'up' : 'down')
const OP = { added: '＋', removed: '－', retype: '↺' }

export default function VerifyPanel({ diff, onClose }) {
  const s = diff.summary || {}
  const moved = [...(diff.value_diff || [])].sort(
    (a, b) => Math.abs(b.delta ?? 0) - Math.abs(a.delta ?? 0),
  )
  const topo = diff.topology_diff || []
  const clean = (s.moved || 0) === 0 && ((s.added || 0) + (s.removed || 0) + (s.retyped || 0)) === 0

  return (
    <section className="results verify">
      <header className="results-head">
        <span className="results-title">Science CI · <b>{diff.from}</b> → {diff.to}</span>
        <span className="results-stats">
          {s.moved} 이동 · 최대 |Δ| {fmtMa(s.max_abs_delta)} Ma · ＋{s.added}/－{s.removed}/↺{s.retyped}
        </span>
        <span className={`results-cert ${clean ? 'pass' : 'warn'}`}>
          {clean ? '공표와 동일' : '공표와 상이'}
        </span>
        <button className="results-close" onClick={onClose} title="닫기">✕</button>
      </header>

      <div className="verify-body">
        {topo.length > 0 && (
          <ul className="verify-topo">
            {topo.map((t, i) => (
              <li key={i} className={`topo-${t.op}`}>
                {OP[t.op] || '•'} {t.boundary}{t.op === 'retype' ? ` (${t.from || '—'}→${t.to || '—'})` : ''}
              </li>
            ))}
          </ul>
        )}

        {moved.length === 0 && topo.length === 0 ? (
          <div className="results-empty">공표 기준과 값·토폴로지가 모두 일치합니다.</div>
        ) : moved.length > 0 && (
          <div className="verify-tablewrap">
            <table className="verify-table">
              <thead><tr><th>경계</th><th>공표</th><th>내 그래프</th><th>Δ (Ma)</th></tr></thead>
              <tbody>
                {moved.map((x) => (
                  <tr key={x.boundary}>
                    <td className="vt-b">{x.boundary}</td>
                    <td>{fmtMa(x.from)}</td>
                    <td>{fmtMa(x.to)}</td>
                    <td className={`vt-d ${deltaClass(x.delta)}`}>
                      {x.delta == null ? '—' : `${x.delta > 0 ? '+' : ''}${Number(x.delta.toPrecision(3))}`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}

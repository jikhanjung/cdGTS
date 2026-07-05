import { useEffect, useState } from 'react'
import { listReleases, narrateRelease } from './api.js'

// bake(얼린 표)의 짝 — 릴리스를 rank 별 '서술한 책'으로. 오래된→젊은 순.
export default function Narrate() {
  const [releases, setReleases] = useState([])
  const [releaseId, setReleaseId] = useState(null)
  const [doc, setDoc] = useState(null)
  const [status, setStatus] = useState('로딩 중…')
  const [error, setError] = useState(null)

  async function load(id) {
    setError(null); setStatus('서술 생성 중…')
    try {
      const d = await narrateRelease(id); setDoc(d)
      const n = d.sections.reduce((a, s) => a + s.entries.length, 0)
      setStatus(`${d.release} · ${n}개 경계 서술`)
    } catch (e) { setError(e.data || String(e)); setStatus('실패') }
  }

  useEffect(() => {
    (async () => {
      try {
        const rs = await listReleases(); setReleases(rs)
        const rp = rs.find((r) => r.version === 'ICS-2024/12') || rs[0]
        if (rp) { setReleaseId(rp.id); load(rp.id) } else setStatus('릴리스 없음')
      } catch (e) { setError(e.data || String(e)); setStatus('실패') }
    })()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="narrate">
      <div className="narrate-controls">
        <label>릴리스
          <select value={releaseId || ''} onChange={(e) => { const id = Number(e.target.value); setReleaseId(id); load(id) }}>
            {releases.map((r) => <option key={r.id} value={r.id}>{r.version}</option>)}
          </select>
        </label>
        <span className="narrate-status">{status}</span>
      </div>

      {error && <pre className="error">{JSON.stringify(error, null, 2)}</pre>}

      {doc && (
        <div className="narrate-book">
          {doc.sections.map((s) => (
            <section key={s.rank}>
              <h3>{s.rank} <span className="narrate-count">{s.entries.length}</span></h3>
              {s.entries.map((e) => (
                <p key={e.boundary} className="narrate-entry">
                  <span className={`narrate-badge ${e.definition_type === 'GSSA' ? 'gssa' : 'gssp'}`}>
                    {e.definition_type || '—'}
                  </span>
                  {e.narrative}
                </p>
              ))}
            </section>
          ))}
        </div>
      )}
      <p className="narrate-note">
        bake(얼린 표)의 짝 — 구조화 필드(정의·연대·오차·방법·이중명명)를 <b>사실 창작 없이</b> 결정적으로 렌더.
        각 서술은 <code>BoundaryRecord.narrative</code> 에 저장(재현 가능). rank 별 · 오래된→젊은 순.
      </p>
    </div>
  )
}

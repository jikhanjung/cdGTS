// 백엔드 REST 왕복. dev 는 vite 프록시(/api → :8000).

async function j(resp) {
  const text = await resp.text()
  const data = text ? JSON.parse(text) : null
  if (!resp.ok) throw Object.assign(new Error('API error'), { status: resp.status, data })
  return data
}

const jsonHeaders = { 'Content-Type': 'application/json' }

export const listNodeTypes = () => fetch('/api/node-types/').then(j)
export const listGraphs = () => fetch('/api/graphs/').then(j)
export const getGraph = (id) => fetch(`/api/graphs/${id}/`).then(j)

export const createGraph = (body) =>
  fetch('/api/graphs/', { method: 'POST', headers: jsonHeaders, body: JSON.stringify(body) }).then(j)

export const saveGraph = (id, body) =>
  fetch(`/api/graphs/${id}/`, { method: 'PUT', headers: jsonHeaders, body: JSON.stringify(body) }).then(j)

export const evaluateGraph = (id) =>
  fetch(`/api/graphs/${id}/evaluate/`, { method: 'POST', headers: jsonHeaders }).then(j)

// 그래프 → ICC 테이블 bake (게이트웨이 출력 스냅샷 → 릴리스 graph:<slug>).
export const bakeGraph = (id) =>
  fetch(`/api/graphs/${id}/bake/`, { method: 'POST', headers: jsonHeaders }).then(j)

// 그래프 산출물 → ICC식 중첩 컬럼 차트 데이터 (Eon/Era/Period 밴드).
export const iccChart = (id) => fetch(`/api/graphs/${id}/icc-chart/`).then(j)

// 공표 릴리스 → 전 rank(Eon~Age) ICC 차트 데이터.
export const releaseIccChart = (id) => fetch(`/api/releases/${id}/icc-chart/`).then(j)

// --- 릴리스 / diff ---
export const listReleases = () => fetch('/api/releases/').then(j)
export const getRelease = (id) => fetch(`/api/releases/${id}/`).then(j)
export const bakeRelease = (id) =>
  fetch(`/api/releases/${id}/bake/`, { method: 'POST', headers: jsonHeaders }).then(j)
export const diffReleases = (a, b) =>
  fetch(`/api/releases/diff/?a=${a}&b=${b}`).then(j)

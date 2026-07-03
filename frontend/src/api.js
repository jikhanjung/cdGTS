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

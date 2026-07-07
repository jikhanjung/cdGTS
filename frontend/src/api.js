// Backend REST round-trips. In dev, vite proxies (/api → :8000).

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

// Bake graph → a new immutable Release (kind=bake) kept in the Vault. Optional label; else server auto-names it.
export const bakeGraph = (id, label) =>
  fetch(`/api/graphs/${id}/bake/`, {
    method: 'POST', headers: jsonHeaders,
    body: JSON.stringify(label ? { label } : {}),
  }).then(j)

// Editable default name for the Bake dialog → { suggested }.
export const suggestBakeName = (id) => fetch(`/api/graphs/${id}/bake/`).then(j)

// Science CI — re-bake, then diff against the published baseline. {from,to,value_diff,topology_diff,summary}.
export const verifyGraph = (id) =>
  fetch(`/api/graphs/${id}/verify/`, { method: 'POST', headers: jsonHeaders }).then(j)

// Graph output → ICC-style nested column chart data (Eon/Era/Period bands).
export const iccChart = (id, node) =>
  fetch(`/api/graphs/${id}/icc-chart/${node ? `?node=${encodeURIComponent(node)}` : ''}`).then(j)

// Published release → ICC chart data across all ranks (Eon–Age).
export const releaseIccChart = (id) => fetch(`/api/releases/${id}/icc-chart/`).then(j)

// Release narrate — counterpart to bake. Per-rank narrative documents + saved narrative.
export const narrateRelease = (id) =>
  fetch(`/api/releases/${id}/narrate/`, { method: 'POST', headers: jsonHeaders }).then(j)

// --- releases / diff ---
export const listReleases = () => fetch('/api/releases/').then(j)
export const getRelease = (id) => fetch(`/api/releases/${id}/`).then(j)
export const bakeRelease = (id) =>
  fetch(`/api/releases/${id}/bake/`, { method: 'POST', headers: jsonHeaders }).then(j)
export const diffReleases = (a, b) =>
  fetch(`/api/releases/diff/?a=${a}&b=${b}`).then(j)

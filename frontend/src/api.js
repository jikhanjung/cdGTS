// Backend REST round-trips. In dev, vite proxies (/api → :8000).

async function j(resp) {
  const text = await resp.text()
  const data = text ? JSON.parse(text) : null
  if (!resp.ok) throw Object.assign(new Error('API error'), { status: resp.status, data })
  return data
}

const jsonHeaders = { 'Content-Type': 'application/json' }

// Django session auth enforces CSRF on writes: send the csrftoken cookie back as a header.
function getCookie(name) {
  const m = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]*)'))
  return m ? decodeURIComponent(m[2]) : null
}
const csrfHeaders = () => ({ ...jsonHeaders, 'X-CSRFToken': getCookie('csrftoken') || '' })

// --- auth (P05.1) ---
export const whoami = () => fetch('/api/auth/whoami/').then(j)
export const login = (username, password) =>
  fetch('/api/auth/login/', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ username, password }) }).then(j)
export const logout = () =>
  fetch('/api/auth/logout/', { method: 'POST', headers: csrfHeaders() }).then(j)

// Edit your own profile (first/last name, email). Returns the refreshed whoami payload.
export const updateProfile = (patch) =>
  fetch('/api/auth/me/', { method: 'PATCH', headers: csrfHeaders(), body: JSON.stringify(patch) }).then(j)

// --- staff user management ---
export const listUsers = () => fetch('/api/users/').then(j)
export const listGovAuthorities = () => fetch('/api/users/authorities/').then(j)
export const createUser = (body) =>
  fetch('/api/users/', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(body) }).then(j)
export const updateUser = (id, patch) =>
  fetch(`/api/users/${id}/`, { method: 'PATCH', headers: csrfHeaders(), body: JSON.stringify(patch) }).then(j)
export const setUserPassword = (id, password) =>
  fetch(`/api/users/${id}/set_password/`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ password }) }).then(j)
export const addMembership = (id, authority, role) =>
  fetch(`/api/users/${id}/add_membership/`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ authority, role }) }).then(j)
export const removeMembership = (id, membership_id) =>
  fetch(`/api/users/${id}/remove_membership/`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ membership_id }) }).then(j)

// --- references (provenance registry, DOI-centric) ---
export const listReferences = () => fetch('/api/references/').then(j)
export const createReference = (body) =>
  fetch('/api/references/', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(body) }).then(j)
// This graph's bibliography — references cited by its `reference` nodes (+ per-boundary attribution).
export const graphReferences = (id) => fetch(`/api/graphs/${id}/references/`).then(j)
// A baked release's bibliography — references snapshotted at bake (+ which boundary each feeds).
export const releaseReferences = (id) => fetch(`/api/releases/${id}/references/`).then(j)

export const listNodeTypes = () => fetch('/api/node-types/').then(j)
export const listGraphs = () => fetch('/api/graphs/').then(j)
export const getGraph = (id) => fetch(`/api/graphs/${id}/`).then(j)

export const createGraph = (body) =>
  fetch('/api/graphs/', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(body) }).then(j)

// Fork a readable graph into a new sandbox you own (P05.3). Optional name; else "<source> (fork)". Returns the new graph.
export const forkGraph = (id, name) =>
  fetch(`/api/graphs/${id}/fork/`, {
    method: 'POST', headers: csrfHeaders(),
    body: JSON.stringify(name ? { name } : {}),
  }).then(j)

export const saveGraph = (id, body) =>
  fetch(`/api/graphs/${id}/`, { method: 'PUT', headers: csrfHeaders(), body: JSON.stringify(body) }).then(j)

// Edit graph metadata (name/description) without touching topology — partial PATCH.
export const updateGraphInfo = (id, patch) =>
  fetch(`/api/graphs/${id}/`, { method: 'PATCH', headers: csrfHeaders(), body: JSON.stringify(patch) }).then(j)

// Evaluate a graph. Fast (analytic) graphs return a full run synchronously; graphs with a
// joint/cyclic cluster return a queued EvalJob (has `.status`, no `.results`) processed by a worker.
export const evaluateGraph = (id) =>
  fetch(`/api/graphs/${id}/evaluate/`, { method: 'POST', headers: csrfHeaders() }).then(j)

// Poll an async EvalJob (P06.4a). When status==='done', `.run` holds the full EvalRun.
export const getEvalJob = (jobId) => fetch(`/api/eval-jobs/${jobId}/`).then(j)

// Bake graph → a new immutable Release (kind=bake) kept in the Vault. Optional label; else server auto-names it.
export const bakeGraph = (id, label) =>
  fetch(`/api/graphs/${id}/bake/`, {
    method: 'POST', headers: csrfHeaders(),
    body: JSON.stringify(label ? { label } : {}),
  }).then(j)

// Editable default name for the Bake dialog → { suggested }.
export const suggestBakeName = (id) => fetch(`/api/graphs/${id}/bake/`).then(j)

// P06.3 authored clamps — L3a verify (GET) / L3b reconcile (POST, owner/staff).
export const releaseClamps = (id) => fetch(`/api/releases/${id}/clamps/`).then(j)
export const reconcileRelease = (id) =>
  fetch(`/api/releases/${id}/reconcile/`, { method: 'POST', headers: csrfHeaders() }).then(j)

// Science CI — re-bake, then diff against the published baseline. {from,to,value_diff,topology_diff,summary}.
export const verifyGraph = (id) =>
  fetch(`/api/graphs/${id}/verify/`, { method: 'POST', headers: csrfHeaders() }).then(j)

// Graph output → ICC-style nested column chart data (Eon/Era/Period bands).
export const iccChart = (id, node) =>
  fetch(`/api/graphs/${id}/icc-chart/${node ? `?node=${encodeURIComponent(node)}` : ''}`).then(j)

// Published release → ICC chart data across all ranks (Eon–Age).
export const releaseIccChart = (id) => fetch(`/api/releases/${id}/icc-chart/`).then(j)

// Release narrate — counterpart to bake. Per-rank narrative documents + saved narrative.
export const narrateRelease = (id) =>
  fetch(`/api/releases/${id}/narrate/`, { method: 'POST', headers: csrfHeaders() }).then(j)

// --- proposals (P05.4 = CI) ---
export const proposeGraph = (id, comment) =>
  fetch(`/api/graphs/${id}/propose/`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ comment: comment || '' }) }).then(j)
export const listProposals = (state) =>
  fetch(`/api/proposals/${state ? `?state=${state}` : ''}`).then(j)
export const getProposal = (id) => fetch(`/api/proposals/${id}/`).then(j)
export const ratifyProposal = (id, comment) =>
  fetch(`/api/proposals/${id}/ratify/`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ comment: comment || '' }) }).then(j)
export const rejectProposal = (id, comment) =>
  fetch(`/api/proposals/${id}/reject/`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ comment: comment || '' }) }).then(j)

// --- releases / diff ---
export const listReleases = () => fetch('/api/releases/').then(j)
export const getRelease = (id) => fetch(`/api/releases/${id}/`).then(j)
export const bakeRelease = (id) =>
  fetch(`/api/releases/${id}/bake/`, { method: 'POST', headers: csrfHeaders() }).then(j)
export const diffReleases = (a, b) =>
  fetch(`/api/releases/diff/?a=${a}&b=${b}`).then(j)

// --- sandbox overrides (P05.5) ---
export const createSandbox = (id) =>
  fetch(`/api/releases/${id}/sandbox/`, { method: 'POST', headers: csrfHeaders() }).then(j)
export const releaseCandidates = (id) => fetch(`/api/releases/${id}/candidates/`).then(j)
export const setReleaseOverride = (id, boundary, candidate) =>
  fetch(`/api/releases/${id}/override/`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ boundary, candidate: candidate || null }) }).then(j)

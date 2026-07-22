import { useEffect, useState } from 'react'
import { listReleases, listProposals, listGraphs, listReferences } from './api.js'

// Home = the landing dashboard. A quick pulse of the engine (counts + latest artifacts)
// with jump-offs into each surface. Clicking the brand in the topnav returns here.
const fmtDate = (s) => (s ? new Date(s).toLocaleDateString() : '')

const SURFACES = [
  ['editor', 'Editor', 'Build a dependency graph, evaluate it, bake or propose.'],
  ['vault', 'Vault', 'Baked releases — chart, table, narrative, diff, sandbox.'],
  ['proposals', 'Proposals', 'Science CI — review proposed changes against the baseline.'],
  ['library', 'Bibliography', 'The shared reference library behind the graphs.'],
]

export default function Home({ onGo, onOpenRelease }) {
  const [releases, setReleases] = useState(null)
  const [proposals, setProposals] = useState(null)
  const [graphs, setGraphs] = useState(null)
  const [references, setReferences] = useState(null)

  useEffect(() => {
    listReleases().then(setReleases).catch(() => setReleases([]))
    listProposals().then(setProposals).catch(() => setProposals([]))
    listGraphs().then(setGraphs).catch(() => setGraphs([]))
    listReferences().then(setReferences).catch(() => setReferences([]))
  }, [])

  const open = proposals?.filter((p) => p.state === 'open')
  const baseline = releases?.find((r) => r.is_baseline)
  const recentReleases = releases?.slice(0, 6)
  const recentProposals = proposals?.slice(0, 6)

  const stats = [
    ['Releases', releases?.length, 'vault'],
    ['Open proposals', open?.length, 'proposals'],
    ['Graphs', graphs?.length, 'editor'],
    ['References', references?.length, 'library'],
  ]

  return (
    <div className="home">
      <div className="home-inner">
        <header className="home-hero">
          <h1>cdGTS</h1>
          <p className="home-tagline">Continuously Deployed Geologic Time Scale — a graph-based geologic time scale engine.</p>
          <p className="home-blurb">
            Boundary ages are not looked up in a table — they are the output of a reproducible pipeline.
            Build the dependency graph in the <b>Editor</b>, bake immutable artifacts into the <b>Vault</b>,
            and run new evidence through <b>Proposals</b>, a CI for the time scale itself.
            {baseline && <> Current baseline: <button className="home-baseline" onClick={() => onOpenRelease(baseline)}>{baseline.version}</button>.</>}
          </p>
        </header>

        <div className="home-stats">
          {stats.map(([label, value, view]) => (
            <button key={label} className="home-stat" onClick={() => onGo(view)}>
              <span className="home-stat-value">{value ?? '·'}</span>
              <span className="home-stat-label">{label}</span>
            </button>
          ))}
        </div>

        <div className="home-cols">
          <section className="home-card">
            <h2>Latest releases</h2>
            {recentReleases == null ? <p className="home-empty">Loading…</p>
              : recentReleases.length === 0 ? <p className="home-empty">No releases yet.</p>
                : (
                  <ul className="home-list">
                    {recentReleases.map((r) => (
                      <li key={r.id}>
                        <button className="home-row" onClick={() => onOpenRelease(r)} title={r.note}>
                          <span className="home-row-main">{r.version}</span>
                          <span className={`vault-kind ${r.kind}`}>{r.is_baseline ? 'baseline' : r.kind}</span>
                          <span className="home-row-meta">{r.record_count} bd · {fmtDate(r.created_at)}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
            <button className="home-more" onClick={() => onGo('vault')}>Open Vault →</button>
          </section>

          <section className="home-card">
            <h2>Recent proposals</h2>
            {recentProposals == null ? <p className="home-empty">Loading…</p>
              : recentProposals.length === 0 ? <p className="home-empty">No proposals yet.</p>
                : (
                  <ul className="home-list">
                    {recentProposals.map((p) => (
                      <li key={p.id}>
                        <button className="home-row" onClick={() => onGo('proposals')} title={p.comment}>
                          <span className="home-row-main">#{p.id} {p.graph_name || p.graph}</span>
                          <span className={`home-state ${p.state}`}>{p.state}</span>
                          <span className="home-row-meta">{p.author || 'anon'} · {fmtDate(p.created_at)}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
            <button className="home-more" onClick={() => onGo('proposals')}>Open Proposals →</button>
          </section>
        </div>

        <div className="home-surfaces">
          {SURFACES.map(([view, label, blurb]) => (
            <button key={view} className="home-surface" onClick={() => onGo(view)}>
              <span className="home-surface-name">{label}</span>
              <span className="home-surface-blurb">{blurb}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

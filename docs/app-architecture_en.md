# App Architecture

*English · [한국어](app-architecture.md)*

> Status: **design v0.** First translation of the brainstorming concept corpus into a Django app
> structure — a blueprint before code. Vocabulary and structure depend on
> [concept-map](concept-map_en.md) · [node-graph-paradigm](node-graph-paradigm_en.md) ·
> [boundary-gateway-schema](boundary-gateway-schema_en.md). Not final.

## 0. Design principles

Two axes from the concept docs become the app boundaries:

1. **Gateway/network two-layer** (node-graph §gateway) — separate the *fixed, ratifiable/citable
   contract* from the *freely churning network*. → `graph` holds both, with `Gateway` as a
   first-class model.
2. **Registry (canonical naming) vs release (frozen artifact)** — names/lineage are stable, while
   value/definition snapshots are per-version. → `chrono` (canonical) ↔ `releases` (snapshot).
3. **Node *type definitions* vs *instances*** — which nodes can exist (vocabulary) is a different
   concern from an actually-wired network. → `nodes` (types) ↔ `graph` (instances).

## 1. App map

| App | Responsibility | Concept |
|---|---|---|
| **`chrono`** | Canonical naming·hierarchy·boundary identity·authority (DB registry) | Layer 0, `identity.lineage` |
| **`nodes`** | Node *type system* — data/process/clamp kinds, ports, distribution payload | node-graph node kinds, fidelity ladder |
| **`graph`** | The actual DAG — node instances·edges·node groups·gateways·canvas layout | network, gateway two-layer |
| **`engine`** | Evaluation (probabilistic propagation)·incremental re-eval·coherence gate·bake/narrate | Layer 5, coherence-gate |
| **`releases`** | Release manifest (selection+clamps)·ICC/GTS·value/topology diff | versioning, competing-models, topology-diff |
| **(frontend)** | React Flow drag&drop canvas ↔ `graph` REST API | Figma/Blender-nodes feel |

Dependency direction (lower does not know upper):

```
chrono ◁─ nodes ◁─ graph ◁─ engine ◁─ releases
(registry)  (types)  (DAG)   (eval)    (release·diff)
   ▲                                      │
   └────── releases.BoundaryRecord ────────┘
           → references chrono.Boundary
```

## 2. Per-app detail

### 2.1 `chrono` — canonical registry ("DB management")

*Names and lineage, not values.* Everything points here.

- `Unit` — dual naming (chronostratigraphic Eonothem/System/Stage ↔ geochronologic Eon/Period/Age)
  as two faces of one entity. Hierarchy via self-FK.
- `Boundary` — **stable slug** (`base-triassic`) + `separates(below/above → Unit)`. No value/definition.
- `BoundaryLineage` — `op: created|renamed|split|merged|retyped|deprecated` + `from:[Boundary]`.
  Precondition for topology diff.
- `Authority` — ICS, subcommission, `sandbox-branch:*`, `fork:*`.
- `Ratification` — year·body.
- `Locality` — GSSP outcrop. Scalar `lat/lon` for now → **promote to PointField when PostGIS lands**
  (the real trigger for the SQLite→PostGIS switch).

### 2.2 `nodes` — node type system ("defining node kinds")

*Which node kinds can exist* = vocabulary. Not instances.

- `NodeType` — `category: data | process | clamp`, port spec (in/out types), parameter schema (JSON).
  - data: `radiometric-uPb`, `astronomical`, `magnetostratigraphic`, `biostratigraphic` (immutable·cited·leaf)
  - process: `age-depth-model`, `cross-section-correlation`, `calibration-transfer`, `joint-inference`
  - clamp: `pin | range | order | freeze-version` (GSSA = special case of `pin`)
- `Distribution` (value object) — the schema's `uncertainty` fidelity ladder **L0–L5**:
  `fidelity: exact|sym|decomposed|shape|joint|full`, `budget{analytical,systematic,model}`,
  `shared_components`, `posterior_ref`. What edges carry = this distribution (not a scalar).

> Keeping `NodeType` as data lets scholars register new model kinds like plugins. The actual
> compute kernel of a `process` node lives as code in `engine`, bound via `NodeType.kind`.

### 2.3 `graph` — the actual DAG ("network design")

One network a scholar built on the canvas. Backend state of the drag&drop editor.

- `Graph` — container (branch/sandbox unit), owner, status.
- `NodeInstance` — `graph`, `type→NodeType`, params, **canvas coords (x,y)**, group.
- `Edge` — `from_port→to_port`, **edge type (`co-location | calibration-transfer`)** — the gate
  detects cycles via this.
- `NodeGroup` — locality/boundary subgraph. Collapses into a gateway-like box.
- `Gateway` — **unit of ratification·citation·version (contract)**. Exposes a node group's output
  as a fixed type. The target that the schema's `BoundaryGateway` references.

> Invariant: keep it a DAG (no cycles) — except cut by `joint-inference`/clamp nodes (cycles §).

### 2.4 `engine` — evaluation ("making it run")

**Starting scope: pass-through first.** Node output = input distribution propagated verbatim
(no computation) — the "reported value + provenance" tier of idea §7. Stand up the graph, citation,
diff, and gate skeleton first; introduce MC/Bayesian compute kernels per node type incrementally.
Coheres with the redefined mission ("humans clamp, the machine propagates·reconciles·diffs").

- `EvalRun` — an evaluation job over a `Graph` (subgraph). Status·trigger·input hash.
- `NodeResult` — per-node output distribution + **content hash** (reuse cache if inputs unchanged =
  incremental re-eval).
- `CoherenceCertificate` — Layer 5 gate checks (L0–L3: monotone order·interval overlap·joint coherence).
- **Separation principle**: Django only orchestrates. Probabilistic propagation·joint inference run in a
  separate scientific stack (numpy/scipy/PyMC) worker. Synchronous/management-command at first → Celery/RQ later.
- **bake/narrate**: bake = summarize·freeze distribution → `releases`; narrate = serialize
  reasoning·caveats (GTS).

### 2.5 `releases` — version·release·diff

- `ModelCandidate` — competing candidate co-existing in the network (independently addressable),
  `scope: boundary|global`, `output{boundary:{value,dist}}`.
- `Release` — manifest: `selection{boundary→ModelCandidate}`, `clamps[]`.
  **The release owns the selection** (not the boundary record).
- `BoundaryRecord` — the `BoundaryGateway` snapshot frozen in one Release
  (definition+age+model_ref+provenance_ref) = ICC bake. References `chrono.Boundary`.
- `Diff` — between two Releases: **value diff** + **topology diff (orthogonal axis)**. Aligned by
  lineage, expressed as edit-script / two-color union graph.

## 3. Drag & drop editor — frontend (React Flow + DRF)

A Figma/Blender-nodes canvas is impossible with server rendering (django-bootstrap5) → needs a
client-side graph library. **Choice: React Flow.** (De-facto standard node editor; pan/zoom/snap/
minimap/custom nodes.)

Architecture:

```
[React Flow SPA (Vite build)]
      │  GET/PUT /api/graphs/{id}   {nodes[], edges[], viewport}
      ▼
[graph app + DRF]  ── NodeInstance/Edge/coords ↔ React Flow JSON 1:1
      │  POST /api/graphs/{id}/evaluate
      ▼
[engine]  → streams NodeResult (distributions)
```

- Graph save: debounced PUT.
- React Flow node JSON ↔ `graph.NodeInstance` (incl. coords) 1:1 → hence coords live in the model.
- `nodes.NodeType` drives the React Flow custom-node palette as data.

**Stack expansion (explicit)**: adds `djangorestframework` + a **Node/React toolchain** (separate
build step, `package.json`, Vite). The first departure from the pure server-rendered fsis2026 pattern.

## 4. What gets added to the stack

- `djangorestframework` (graph/engine API)
- Frontend toolchain: React + React Flow + Vite (separate `frontend/` dir, independent build)
- (later) Celery/RQ + numpy/scipy/PyMC worker — when the engine moves past pass-through

## 5. Open modeling questions (next decisions)

- **Where definition lives** — GSSP marker/outcrop on `chrono.Boundary` (stable) vs
  `releases.BoundaryRecord` (per-version, allows retype). Tentative: current value on Boundary,
  snapshot on Record.
- **NodeType code binding** — how to connect the compute kernel via `NodeType.kind` string ↔ engine registry.
- **Gateway ↔ BoundaryRecord relation** — overlap/reference between Gateway (in-graph contract) and
  Record (release snapshot).
- **Graph branch/sandbox model** — express fork·override (baseline+delta) (versioning §).
- Remaining schema open questions: see [TODOs](../TODOs.md) §2.

## 6. Links

- [concept-map](concept-map_en.md) — upper concept map
- [node-graph-paradigm](node-graph-paradigm_en.md) — gateway/network two-layer
- [boundary-gateway-schema](boundary-gateway-schema_en.md) — schema v0 (source of the models)
- [TODOs](../TODOs.md) §0 — kickoff decisions

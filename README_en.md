# cdGTS — Continuously Deployed Geologic Time Scale

*English · [한국어](README.md)*

> Status: concept (brainstorming) → **implemented & deployed**. Schema v0 is now built as 5 Django apps + a React node editor, and **v0.1.2** is deployed to production at [cdgts.paleobytes.info](https://cdgts.paleobytes.info). The concept corpus stays in `docs/`.

## What is it

Instead of treating the geologic time scale as a **~decade-cadence major release (a book)**, the idea is to treat it as **data that is version-controlled and continuously deployed, like software**.

- **International Chronostratigraphic Chart (ICC)** — the official consensus time scale published by the ICS.
- **Geologic Time Scale 2020 (GTS2020)** — a detailed reference work that folds in radiometric and astrochronologic calibration. **GTS2030** is currently in preparation.

cdGTS aims to see both as **the output of one reproducible pipeline**:

> primary observations (data) → processing/models → boundary ages

The key differentiator is a **testing/sandbox environment**. A researcher can continuously integrate newly obtained data and immediately see its effect on boundary ages as a **diff** — a kind of **"CI for science"**.

## Conceptual metaphor: the node graph

Like Blender's geometry nodes, the core metaphor is a network (DAG) of **data nodes** and **process/model nodes**. Evaluating the graph determines the age at a particular point on Earth; gather them all and you get the ICC/GTS.

- **Narrate** the graph at length → GTS2030 (the book)
- **crystallize/bake** the graph → ICC (a frozen snapshot)

Provenance (the FAIR principles), incremental re-evaluation, and what-if comparison are naturally built into the graph structure.

## The layer spine (Layer 0–6)

Nomenclature (0) → boundary definition (1) → primary observations (2) → local age model (3) → correlation (4) → global synthesis · coherence gate (5) → publication (6). Higher layers derive from lower ones. Publication yields two outputs: **ICC = bake (a frozen snapshot)**, **GTS = narrate (a book)**.

## Documents

The top-level map over everything is **[docs/concept-map_en.md](docs/concept-map_en.md) — start here** (the layer spine · document map · five convergence points).

**Concept**
- [docs/idea_en.md](docs/idea_en.md) — background · problem · layers 0–6 · gateways · open questions
- [docs/node-graph-paradigm_en.md](docs/node-graph-paradigm_en.md) — DAG · gateway/network · cycles · edge = distribution

**Cases (three types)**
- [docs/case-permian-triassic_en.md](docs/case-permian-triassic_en.md) — GSSP · local interpolation (the number is computed)
- [docs/case-precambrian-gssa_en.md](docs/case-precambrian-gssa_en.md) — GSSA · decreed (the number is the definition — the mirror image of P–T)
- [docs/case-cambrian-base-correlation_en.md](docs/case-cambrian-base-correlation_en.md) — GSSP · cross-section correlation (the number comes from other continents)

**Schema & design**
- [docs/boundary-gateway-schema_en.md](docs/boundary-gateway-schema_en.md) — boundary gateway schema v0 (all five §4 open questions resolved)
- [docs/versioning-global-vs-per-boundary_en.md](docs/versioning-global-vs-per-boundary_en.md) — global vs per-boundary versioning (records + manifest)
- [docs/coherence-gate_en.md](docs/coherence-gate_en.md) — the coherence gate (Layer 5): pinned boundary set → valid chart
- [docs/competing-models_en.md](docs/competing-models_en.md) — how competing models coexist (plural candidates + release selection)
- [docs/cycles_en.md](docs/cycles_en.md) — cyclic dependencies and **clamps** (hand-crafted gates placed by subcommissions)
- [docs/topology-diff_en.md](docs/topology-diff_en.md) — topology diff (the structural-change axis orthogonal to the value diff)
- [docs/distribution-representation_en.md](docs/distribution-representation_en.md) — distribution representation (the L0–L5 fidelity ladder)

## Key convergence points

Different threads repeatedly converged to the same structure (details in [concept-map](docs/concept-map_en.md) §3):

- **Provenance depth = a single axis** — coherence level, distribution fidelity, and cycle resolution all depend on it.
- **The clamp is the unifier** — GSSA (pin = point mass) · cycle-cutting · distribution operators fold into one primitive.
- **The ICC/GTS = bake/narrate dichotomy** recurs in the gate · competing models · diff · distribution.

## Status

Concept (brainstorming) → **implemented & deployed**. Schema v0 (all five §4 open questions resolved) has been brought down into a runnable app.

- **Stack**: Django 5.2 + SQLite + DRF + React Flow (Vite). 5 apps (chrono·nodes·graph·engine·releases) + a front-end node editor and release-diff view. Backend `pytest` 59 passed.
- **Engine**: value + provenance propagation (pass-through) · coherence gate · value/topology diff skeleton. A compute kernel (numpy/scipy) runs the real age-depth model.
- **Deployment**: Docker image `honestjung/cdgts`. Production [cdgts.paleobytes.info](https://cdgts.paleobytes.info) @ **v0.1.2**, dev/test @ v0.1.1. Atomic DB snapshot + NAS offsite backup (04:00 cron).

The current-state headline is in [HANDOFF.md](HANDOFF.md), per-round changes in [`devlog/`](devlog/), and the remaining open questions in [TODOs.md](TODOs.md).

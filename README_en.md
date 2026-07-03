# cdGTS — Continuously Deployed Geologic Time Scale

*English · [한국어](README.md)*

> ⚠️ Status: Early brainstorming. Nothing is settled yet — this is a space to throw out ideas and roll them around.

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

## Documents

- [docs/idea_en.md](docs/idea_en.md) — background, problem statement, core idea, the layered data model (Layer 0–4), open questions
- [docs/node-graph-paradigm_en.md](docs/node-graph-paradigm_en.md) — the node-graph paradigm in detail
- [docs/case-permian-triassic_en.md](docs/case-permian-triassic_en.md) — the first case study validating the model against the Permian–Triassic boundary (real data + node graph)
- [docs/case-precambrian-gssa_en.md](docs/case-precambrian-gssa_en.md) — the Precambrian GSSA counter-case (the number *is* the definition — the mirror image of P–T)
- [docs/case-cambrian-base-correlation_en.md](docs/case-cambrian-base-correlation_en.md) — base of the Cambrian (Fortune Head): the third type, where cross-section correlation produces the number
- [docs/boundary-gateway-schema_en.md](docs/boundary-gateway-schema_en.md) — draft boundary gateway schema (v0) spanning all three cases
- [docs/versioning-global-vs-per-boundary_en.md](docs/versioning-global-vs-per-boundary_en.md) — global vs per-boundary versioning analysis (open questions)
- [docs/coherence-gate_en.md](docs/coherence-gate_en.md) — the coherence gate concretized (Layer 5): pinned boundary set → valid chart

## Status

This is the brainstorming stage. The schema, code, and architecture have not been decided yet.

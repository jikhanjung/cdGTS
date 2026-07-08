# cdGTS — Continuously Deployed Geologic Time Scale

*English · [한국어](idea.md)*

> Status: Early brainstorming. Nothing is settled yet. A space to throw out ideas and roll them around.

## 1. Background

- The **ICS (International Commission on Stratigraphy)** publishes the **International Chronostratigraphic Chart (ICC)**. It shows the current official consensus on geologic time boundaries (GSSPs) and their ages, with revisions released irregularly (e.g., v2023/09, v2024/12 …).
- A more detailed reference work has been **GTS2020 (*Geologic Time Scale 2020*, Gradstein et al.)**, which incorporates radioisotopic and astrochronological calibration.
- **GTS2030** is currently in preparation.

## 2. The problem

The geologic time scale is published only as a "book / major release" on a roughly 10-year cycle. New dating data that accumulates in between is hard to reflect officially until the next major release.

## 3. Core idea

**Treat the geologic time scale like software.**

- Treat it **not as a table but as a computed artifact**: primary data → model → boundary ages, connected by a **reproducible pipeline**.
- **Version control + continuous deployment**: release verified **fixed versions** on a regular basis, but
- also provide a **test / sandbox environment**. Let scholars **continuously integrate** newly obtained data and immediately see its effect on boundary ages — a kind of **"CI for science."**

## 4. Scope

- Includes **both** the data store / schema **and** the query and visualization tools — **everything**.

## 5. Data model — node types (implemented)

The data model is **tier (registry / graph / release) × category (data / process / clamp)**, and the graph tier is
filled with the **16 node types** below.

> The original linear **Layer 0–6** brainstorm that used to sit here now holds only as a narrative reading order and is
> archived in [archive/idea-layer-model-0-6.md](archive/idea-layer-model-0-6.md). Current spine:
> [tier-category-model_en.md](tier-category-model_en.md) · [concept-map_en.md](concept-map_en.md) §1.

### data — observation / reference leaves (immutable, citable)
Where a scholar's new "facts" attach.
- **`radiometric-uPb`** — U–Pb radiometric age observation.
- **`astronomical`** — astronomically tuned (astrochronology) age.
- **`biostratigraphic`** — biostratigraphic datum (FAD/LAD) signal.
- **`magnetostratigraphic`** — magnetic-reversal pattern signal (for correlation).
- **`published-age`** — reference leaf for published boundary ages (ICS/GTS chart).

### process — transforms / models / synthesis
Where the messy science (interpolation, correlation, joint estimation) and chart assembly happen.
- **`age-depth-model`** — age–depth interpolation within one section (local; linear/spline).
- **`cross-section-correlation`** — synthesis of cross-section correlations (**load-bearing**). Case: [case-cambrian-base-correlation_en.md](case-cambrian-base-correlation_en.md).
- **`calibration-transfer`** — transfers a reference age onto a target signal.
- **`joint-inference`** — locally co-constrained joint estimation (the node that folds cycles).
- **`boundary`** — boundary point (0-cell); receives its age from an upstream computation.
- **`unit`** — time unit (1-cell, span); an unsubdivided interval as a single node.
- **`merge`** — terminal geometry merge; unions boundary/unit pieces → ICC chart.

### clamp — governance gates
Where consensus / ratification touches the numbers.
- **`pin`** — fixes a value (GSSA = a special case of pin).
- **`range`** — interval clamp [min, max].
- **`order`** — checks temporal order of two boundaries (older ≥ younger).
- **`freeze-version`** — cuts the version spiral; freezes to a specific release value.

Dual naming (chronostratigraphy Stage ↔ geochronology Age) lives in the registry tier (`chrono` app); the published
releases (ICC = bake / GTS = narrate) in the release tier (`releases` app). Ordering is expressed not as a separate node
but as an **`order` edge** (a boundary vertical-port connection); evaluation runs the graph in topological order to
propagate distributions ([node-graph-paradigm_en.md](node-graph-paradigm_en.md)), then the coherence gate checks
ordering / duration / covariance ([coherence-gate_en.md](coherence-gate_en.md)).

## 6. Imagined workflow (CI for science)

1. A scholar proposes a new **data node** (observation), PR-style.
2. The pipeline re-evaluates the downstream **process · clamp** nodes.
3. It shows a **diff** — e.g., "adding this one U–Pb shifts the Permian–Triassic boundary from 251.902 → 251.88 Ma, with reduced 2σ."
4. Fixed releases are verified snapshots; the sandbox is an experimental branch. Whether to allow personal fork time scales is undecided.

## 7. Open questions

- ~~**The status of the age model**: does cdGTS actually *compute* the age model, or is it just "published values + provenance records"?~~ **→ [resolved]** the engine really computes — `age-depth-model` (linear/spline MC), covariance-aware durations, coherence certificate (P06). The `published-age` leaf also supports the "published value + source" path (both exist).
- **The line between authority and experiment**: how to clearly distinguish sandbox results from the official ICC? How far to allow an individual scholar's "my branch time scale"?
- Consistency with existing formats: should it align with Macrostrat, GeoSciML / CGI Geologic Timescale, the official ICS distribution format, etc.?
- Concretizing the versioning strategy: how to map git tags, semantic versioning, and automated verification (CI)?

## 8. Ideas being refined — an intermediate tier and gateways

> Status: **At the level of a hunch. Not settled.** Whether this is the right approach can only be known by grabbing a real case and working through it. What follows is a record of a sense of direction.
>
> **[mostly realized]** The hunches here in §8.1 (a correlation/synthesis intermediate tier) and §8.2 (gateway contracts)
> hardened into implementation — correlation/synthesis = the `cross-section-correlation`·`joint-inference` nodes,
> gateways = `Gateway`/`merge` + the coherence gate. Read the Layer references as narrative reading order. Current:
> [tier-category-model_en.md](tier-category-model_en.md).

### 8.1 The intermediate tier — correlation / synthesis (promoted to Layers 4·5 in §5)

The early model jumped straight from Layer 3 (local age model) to publication, and between them **space and correlation** were missing entirely. §5 now promotes these to **Layer 4 (correlation) · Layer 5 (global synthesis)**.

Why this is essential: **a GSSP *defines* a boundary but in many cases does not give the boundary's *number*.** The golden-spike outcrop may be a lithology that cannot be radiometrically dated, in which case the actual number comes from datable beds in another region and is **tied to the GSSP point via correlation**. That is, correlation is not a side feature but a **load-bearing** step on the very path by which the number is obtained.

Operations of different character overlap at different scales:

| Scale | Operation | Current location |
|---|---|---|
| Single point | Age of one sample | Layer 2 |
| Section / stratigraphic column | Age-depth model (within one outcrop) | Layer 3 (spatially local) |
| Formation / sequence | Bundling several horizons into one unit | Local–regional |
| **Section ↔ Section** | **Correlation (bio/chemo/magneto-strat tie)** | now **Layer 4** |
| Global | Pooling multiple lines of evidence for the same boundary → number + uncertainty | now **Layer 5** |

→ **Promoted to integer layers in §5: Layer 4 (correlation), Layer 5 (global synthesis / coherence gate).**

Caution: correlation is itself an inference with uncertainty (probabilistic matching), and the **circular dependency** from [node-graph-paradigm_en.md](node-graph-paradigm_en.md) (biostratigraphy ↔ radiometric mutual calibration) breaks out precisely within this tier. The node-graph document already brings this spatial dimension in as a "correlation node / node group," but **this layer model (idea.md) does not yet reflect that** — the two documents need to be reconciled.

### 8.2 Layers as "gateways (contracts)" rather than "stages"

A bigger reinterpretation: don't nail the layers down as fixed sequential stages. Instead, place only **intermediate gateway layers** (units of agreed-upon fixed type, version, and citation) at intervals, and fill **the space between them with a free node network**. Messy science (circularity, alternative models, Monte Carlo, correlation) is confined *between* the gateways, while the gateways themselves stay clean and get released.

For the full development, see the **"gateway layers"** section of [node-graph-paradigm_en.md](node-graph-paradigm_en.md).

> **Retrospective:** how this reinterpretation actually solidified in the build — L0–6 decomposing into **tier (registry/graph/release) × category (data/process/clamp)** — is covered in [tier-category-model_en.md](tier-category-model_en.md).

### 8.3 Open questions this raises

- Whether to extract correlation / synthesis as a separate tier, and into how many.
  → In [case-permian-triassic_en.md](case-permian-triassic_en.md), confirm that this tier is not one but splits into two different characters:
  **(a) local age-depth interpolation** and **(b) cross-section correlation**.
  → In [case-cambrian-base-correlation_en.md](case-cambrian-base-correlation_en.md), confirm that (b) is real and is
  **both the main path to the number and the largest source of uncertainty** (the GSSP section cannot be dated; the number comes from correlation to another continent).
- Is the gateway **global** (one big table) or **per-boundary** (an independent version for each boundary)?
- Is the gateway a **type (schema)** or a **frozen instance (release)**, or both?
- What to **promote** to a gateway — this choice becomes the boundary of governance/ratification.
- **[Requirement confirmed by the cases] The boundary gateway schema must be polymorphic.**
  The two cases showed two extremes: GSSP-type = **a computed distribution + provenance (with ±)**
  ([case-permian-triassic_en.md](case-permian-triassic_en.md)); GSSA-type = **a decreed constant (no error, no upstream network)**
  ([case-precambrian-gssa_en.md](case-precambrian-gssa_en.md)). The ICC actually makes these two coexist in one table.
  → Remaining question: how to hold both types in a single schema.
- **Topology rewiring must be tracked as a version.** The GSSA→GSSP transition changes not a node's *value* but its *wiring*
  (Ediacaran done, Cryogenian in progress). Separately from a value diff, how to express and version a **topology diff**.
- **[Constraint from the Cambrian case] "Age-model choice" must be a first-class node.** From the same data, competing age models
  produce different numbers (Cambrian base 538.8 vs ~536). Whether the schema supports placing competing models side by side as **alternative graph branches** and showing the diff.
- **[Constraint] The boundary "position" node and the "age anchor" node must be separated.** A GSSP fixes only *where* the boundary is;
  *when* is supplied by the correlation subgraph (Fortune Head position ↔ Oman/Namibia anchors). The two must not be lumped into one node.
- **[Constraint] The provenance graph is geographically distributed.** Tracing a boundary number back may lead not to the GSSP but to a
  section / δ13C curve on another continent. The schema must accommodate this distributed provenance.

# Boundary Gateway Schema — Draft

*English · [한국어](boundary-gateway-schema.md)*

> **[superseded / kept as history]** This monolithic gateway YAML schema is only the **ancestor** of the
> implementation, not current. The app represents a boundary not as one gateway record but as a graph **`boundary`
> node + `published-age` leaf + `order` edge**, with release/clamp/provenance in the `releases`·`graph` app models.
> Current: [app-architecture_en.md](app-architecture_en.md) · [boundary-span-duality_en.md](boundary-span-duality_en.md) ·
> `releases/models.py`. (Below is the historical brainstorming.)

> Status: **Draft v0.** A first attempt to harden the brainstorming into concrete structure. Not settled.
> It gathers the requirements pulled from the three cases
> ([P–T](case-permian-triassic_en.md), [Precambrian GSSA](case-precambrian-gssa_en.md),
> [base of Cambrian](case-cambrian-base-correlation_en.md)) into a single schema.
> The notation below is **illustrative (YAML)** only; the serialization format is undecided.

## 1. Design principles (requirements from the three cases)

1. **Polymorphic.** A boundary number has three possible origins — a computed distribution
   (GSSP · local interpolation), a decreed constant (GSSA), and a correlation synthesis
   (GSSP · cross-section). One schema must hold all three.
2. **Separate position from age.** A GSSP pins only the *where/what* (marker · stratotype); the *when*
   (the number) is supplied by a separate subgraph. The two fields must not be conflated.
   (GSSA is the exception — no stratotype, and the number *is* the definition.)
3. **Provenance is a graph reference.** Don't inline-duplicate the number; point at a subgraph of the
   node graph. That subgraph can be **geographically distributed** (Cambrian: Canada + Oman + Namibia + Siberia).
4. **The age model is a first-class field.** Record which model produced the number, plus its
   **competing alternatives**.
5. **Gateway = the unit of versioning, citation, and ratification (a contract).** A frozen snapshot per
   release. Even the definition type (GSSP/GSSA) can change between versions (topology rewiring).

## 2. Schema (annotated illustrative notation)

Two axes are each independently polymorphic:

- `definition.type`: **GSSP | GSSA** — the *where/what* (position)
- `age.method`: **decreed | local-interpolation | cross-section-correlation** — *how the number arose*

> Coupling: `GSSA ⇒ age.method = decreed`. `GSSP ⇒ age.method ∈ {local-interpolation, cross-section-correlation}`.

```yaml
BoundaryGateway:
  id: string                     # stable slug. e.g. base-triassic
  version: string                # the release this record belongs to. e.g. ICC-2024/12

  identity:                      # Layer 0 — link to nomenclature/hierarchy
    separates:
      below: unit_ref            # unit below (dual-naming reference)
      above: unit_ref            # unit above
    # unit_ref carries both chronostratigraphic (System/Series/Stage) and geochronologic (Period/Epoch/Age) names
    lineage:                     # cross-version identity lineage (prerequisite for the topology diff)
      op: created | renamed | split | merged | retyped | deprecated
      from: [boundary_id]        # source(s) of a split/merge, or the previous id of a rename

  definition:                    # position — "where/what" (Layer 1)
    type: GSSP | GSSA
    ratified: { year: int, by: authority }
    # --- when type == GSSP ---
    marker:                      # the event that defines the boundary
      kind: biostratigraphic | chemostratigraphic | magnetostratigraphic | ...
      event: FAD | LAD | excursion | reversal | ...
      taxon_or_signal: string    # e.g. "Hindeodus parvus"
    stratotype:
      locality: string           # e.g. "Meishan D, Changxing, Zhejiang, China"
      coordinates: [lat, lon]
      level: string              # e.g. "base of Bed 27c"
    # --- when type == GSSA ---
    decreed_age_ma: number       # this number IS the definition (no stratotype)
    rationale: string            # e.g. "round-number convention"

  age:                           # age — "when" (output of Layers 3–5)
    value_ma: number
    uncertainty:                 # structured distribution (fidelity ladder L0–L5). GSSA = { fidelity: exact }
      fidelity: exact | sym | decomposed | shape | joint | full
      sigma: 1 | 2               # confidence level of the budget values
      budget: { analytical, systematic, model }   # decomposed budget; shared systematic = covariance key
      shape: { median, hpd95: [lo, hi] }?          # asymmetry/skew (symmetric assumed if absent)
      shared_components: [node_ref]                # shared systematic nodes (joint reconstruction)
      posterior_ref: sample_ref | model_ref?       # L5: samples / re-runnable model
      note: string?
    method: decreed | local-interpolation | cross-section-correlation
    model_ref: model_candidate_ref  # the model candidate this release *selected*. The authoritative binding is
                                    # the release manifest's selection. value_ma is a baked copy of that candidate's output.
    provenance_ref: graph_ref    # the subgraph the selected candidate yields the value from. May be geographically distributed.

  status:
    level: ratified | proposed | sandbox | deprecated
    authority: ICS | sandbox-branch:<id> | fork:<user>
    supersedes: version?         # previous-version record

  narrative_ref: doc_ref?        # the counterpart of the bake (this record) — the GTS-style narration (narrate)
```

Competing models coexist in plurality in the *network between* gateways. Each candidate is an **independent
object**, and a release selects one (`model_ref`). Detail: [competing-models_en.md](competing-models_en.md).

```yaml
ModelCandidate:                  # a competing candidate coexisting in the network (independently addressable)
  id: string                     # e.g. base-cambrian/bowyer2022-modelA
  version: string
  scope: boundary | global       # if global, sets many boundaries at once → internally coherent by construction
  sets: [boundary_id]            # (scope=global) the boundaries this candidate sets
  kind: string                   # bayesian-age-depth, global-d13C-age-model, committee-decision …
  inputs: [node_ref]             # contributing observation/anchor nodes
  correlation_via: [string]      # (cross-section) BACE, Sr isotopes …
  output:                        # the value(s) the candidate yields
    { boundary_id: { value_ma, uncertainty } }
  provenance_ref: graph_ref

# The release owns the selection (not the boundary record):
Release:
  version: string                # e.g. ICC-2024/12
  selection: { boundary_id: model_candidate_ref }   # a coherent selection = drawing from a consistent (ideally same global) set
  clamps: [clamp_ref]            # the authored clamps this release applies

# Clamp — a governance gateway a subcommission plugs *inside* the network (cuts cycles / pins authority)
Clamp:
  id: string
  owner: string                  # e.g. ICS Cambrian Subcommission
  target: node_ref | boundary_id # what it fixes
  kind: pin | range | order | freeze-version
  value_or_bound: any            # pin=value, range=[min,max], order=neighbor ref, freeze-version=version
  rationale: string
  ratified: { year: int, by: authority }
  overridable_in_sandbox: bool   # removable in a sandbox what-if?
# note: GSSA = the Clamp{kind: pin} special case (one root with definition.type=GSSA).
# note: provenance edges carry a type (co-location | calibration-transfer) so the gate can detect cycles.
```

> **[reconsidered]** The graph-level `Clamp` node above was later **scoped down**: of the graph clamp NodeTypes,
> `pin` · `range` · `freeze-version` were removed, leaving only `order`, and **GSSA is now represented as an authored
> `published-age` leaf rather than a `pin` clamp** (cycle-breaking is also unified into a single `joint-inference`).
> `releases.Clamp` + verify/reconcile remain in the code but are **isolated as demo-only**. So read the
> `kind: pin | range | order | freeze-version` and `GSSA = Clamp{kind: pin}` above as **historical/design** record.
> Background: [cycles §12](cycles_en.md#12-reconsideration-note-2026-07--is-clamp-needed-as-a-distinct-concept).

## 3. Applied to the three cases

### A. P–T boundary — GSSP · local interpolation

```yaml
id: base-triassic
version: ICC-2024/12
identity:
  separates: { below: changhsingian-stage, above: induan-stage }
definition:
  type: GSSP
  ratified: { year: 2001, by: ICS }
  marker: { kind: biostratigraphic, event: FAD, taxon_or_signal: "Hindeodus parvus" }
  stratotype:
    locality: "Meishan D, Changxing, Zhejiang, China"
    level: "base of Bed 27c"
age:
  value_ma: 251.902
  uncertainty:
    fidelity: decomposed
    sigma: 2
    budget: { analytical: 0.024 }          # +tracer/+decay systematics: see source
    shared_components: [earthtime-tracer, u-decay-const]
  method: local-interpolation
  model_ref: "base-triassic/burgess2014"   # selected candidate (ModelCandidate below)
  provenance_ref: "graph://base-triassic/age@Burgess2014"
status: { level: ratified, authority: ICS }
```

### B. Archean–Proterozoic boundary — GSSA · decreed

```yaml
id: base-proterozoic
version: ICC-2024/12
definition:
  type: GSSA
  ratified: { year: 1991, by: ICS }
  decreed_age_ma: 2500
  rationale: "round-number convention; no physical stratotype"
age:
  value_ma: 2500
  uncertainty: { fidelity: exact }                 # point mass δ(2500)
  method: decreed
  model_ref: "base-proterozoic/decree"     # candidate = the committee decision
  provenance_ref: "decision://ICS/precambrian-subcommission"
status: { level: ratified, authority: ICS }
# note: by definition.type history, currently GSSA. Another Precambrian boundary (Ediacaran) has already been rewired to a GSSP.
```

### C. Base of the Cambrian — GSSP · cross-section correlation

```yaml
id: base-cambrian
version: ICC-2024/12
identity:
  separates: { below: ediacaran-system, above: fortunian-stage }
definition:
  type: GSSP
  ratified: { year: 1992, by: ICS }
  marker: { kind: biostratigraphic, event: FAD, taxon_or_signal: "Treptichnus pedum" }
  stratotype:
    locality: "Fortune Head, Burin Peninsula, Newfoundland, Canada"
    level: "23 m above base of Member 2A (Quaco Road Mbr), Chapel Island Fm"
age:
  value_ma: 538.8
  uncertainty:
    fidelity: decomposed
    sigma: 2
    budget: { analytical: 0.6 }
    note: "contested; model-to-model down to ~536 → multimodality in the competing-models layer"
  method: cross-section-correlation
  model_ref: "ediacaran-cambrian/bowyer2022-modelAB"   # selected candidate (scope=global)
  provenance_ref: "graph://base-cambrian/age"   # Canada (position) + Oman/Namibia/Siberia (anchors)
status: { level: ratified, authority: ICS }

# Competing candidates — coexisting in the network; the release selects one:
- id: "ediacaran-cambrian/bowyer2022-modelAB"
  scope: global
  sets: [base-cambrian, base-fortunian, …]     # sets many boundaries at once → internally coherent
  kind: global-d13C-age-model
  inputs: [oman-ara-uPb, namibia-uPb, siberia-uPb]
  correlation_via: [BACE-d13C, Sr-isotope-stratigraphy]
  output: { base-cambrian: { value_ma: 538.8, uncertainty: { plus_minus: 0.6, sigma: 2 } } }
- id: "ediacaran-cambrian/bowyer2022-modelD"
  scope: global
  kind: global-d13C-age-model
  output: { base-cambrian: { value_ma: ~536, uncertainty: { note: "~3 Myr younger" } } }
```

These three examples make the two polymorphic axes concrete: **position (GSSP/GSSA)** and
**number origin (decreed/interpolation/correlation)** appear in different combinations, and in all three
`age.provenance_ref` points at the **live subgraph behind the frozen value**.

## 4. Open design questions

- **Global vs per-boundary versioning.** This draft assumes per-boundary independent versions (each record
  carries its own `version`). How to tie that to a whole-ICC release (a release = a snapshot set of boundary records?).
  → Separate note: [versioning-global-vs-per-boundary_en.md](versioning-global-vs-per-boundary_en.md).
- **Distribution representation.** → **Resolved**: `uncertainty` structured as a fidelity ladder (L0–L5) —
  decomposed budget (= covariance key) + shape + shared-component tags + posterior ref. GSSA = `fidelity: exact`
  (point mass). ICC canonical rung ≈ L2/L3, the joint (L4) on the release layer. Detail:
  [distribution-representation_en.md](distribution-representation_en.md).
- **How competing models coexist.** → **Resolved**: candidates coexist in the network (`ModelCandidate`
  independent objects), and a release binds one via `selection`. Reflected in §2's `age.model_ref` ·
  `ModelCandidate` · `Release`. Detail: [competing-models_en.md](competing-models_en.md).
- **Topology diff.** → **Resolved**: an axis orthogonal to the value diff. Aligned via stable ids +
  `identity.lineage` (declared split/merge/retype), notated as edit-script / two-colored union graph / changelog.
  Detail: [topology-diff_en.md](topology-diff_en.md).
- **Cycles.** → **Resolved**: local mutual constraint folds into a joint-inference node; global calibration
  feedback is cut by the version spiral + subcommission `Clamp`s. Reflected in §2's `Clamp` · `Release.clamps`.
  Detail: [cycles_en.md](cycles_en.md).

## 5. Links

- [idea_en.md](idea_en.md) §5 (layers) · §8 (gateways) — conceptual background
- [node-graph-paradigm_en.md](node-graph-paradigm_en.md) — gateways / node network
- Cases: [P–T](case-permian-triassic_en.md) · [Precambrian GSSA](case-precambrian-gssa_en.md) · [base of Cambrian](case-cambrian-base-correlation_en.md)

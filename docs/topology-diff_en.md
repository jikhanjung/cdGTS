# Topology Diff

*English · [한국어](topology-diff.md)*

> Status: **Analysis → partly reflected in the schema.** An expansion of the "topology diff" item in
> [boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) §4. The concretization of
> [node-graph-paradigm_en.md](node-graph-paradigm_en.md)'s *"topology is also subject to versioning."*
>
> **[partly implemented]** Value and topology diff are implemented as a release diff, and the split/merge lineage
> (so it isn't mistaken for delete+add) is carried by `chrono.BoundaryLineage`. Below is the design rationale (still valid).

## 1. Core insight — value diff and topology diff are orthogonal axes

The diffs we imagined so far were mostly **value diffs** ("adding this U-Pb shifts P–T from 251.902 → 251.88").
But:

| Change | Value diff | Topology diff |
|---|---|---|
| A new U-Pb shifts the number | **large** | 0 |
| **GSSA→GSSP conversion** (e.g. 2500 kept) | **≈0** | **large** |
| The same number produced by a *different model/data* | 0 | **large** |
| Stage split | (no correspondence at all) | **large** |

**One axis can be 0 while the other is huge.** GSSA→GSSP barely changes the value but completely changes the
number's *meaning* (decreed constant → outcrop-derived value). A value diff alone would lie "no change." → The
two must be **reported separately**.

## 2. What "topology" spans

- **Boundary/unit set (Layer 0):** creating/splitting/merging/renaming/deprecating stages, re-parenting the hierarchy.
- **Definition type · marker · stratotype (Layer 1):** GSSA→GSSP conversion, marker change, GSSP stratotype
  relocation (the Cambrian GSSP reassessment is a real example).
- **Provenance wiring (Layers 2–5):** add/remove observations, age-model node swap, add/remove correlation
  edges, ModelCandidate selection, clamp placement.

From the coarse level (the chart's named boundary set) to the fine level (the wiring of the provenance DAG behind
one number).

## 3. This is a graph-diff / tree-diff problem

Not a scalar comparison but a **structural** one. A value diff presumes a **stable correspondence** ("same
identity, different number"), which a topology change breaks:

- On a stage split there is no 1:1 mapping old ↔ new boundary → a value diff can't see the "split" and mistakes
  it for "delete + add."
- So **persistent identifiers** are a prerequisite, and **split/merge cannot be inferred from structure alone**
  → a new boundary must **declare explicit lineage**: "I was split off from old boundary X." Like Git's rename
  detection, but in science this is a **curated decision**, so it must be **recorded**, not guessed.

**Edit operations:** create / deprecate / rename / **split·merge** / **rewire** / **retype** / move.

## 4. Notation — three layers

1. **Edit script** — an ordered list of typed operations transforming `graph_v1 → graph_v2`. Machine-readable,
   replayable (the changelog of record).
2. **Two-colored union graph** — overlay both versions, color nodes/edges added/removed/unchanged. For
   visualization (a visual diff of the DAG).
3. **Semantic changelog** — "Stage X split into X1/X2 (ratified 20xx)", "Cryogenian base converted GSSA→GSSP."
   For humans / citation.

The three derive from one another (edit script + lineage → changelog → visualization).

## 5. Connections to existing machinery

- **Clamps give the vocabulary for retype.** Since GSSA = `Clamp{pin}`, a **GSSA→GSSP conversion = remove the
  clamp + add a provenance subgraph + retype the definition.** The topology diff is described in clamp
  operations. ([cycles_en.md](cycles_en.md))
- **A trigger to re-run the coherence gate.** A split changes the ordering set; a retype changes the required
  provenance → a topology diff calls for gate re-validation. ([coherence-gate_en.md](coherence-gate_en.md))
- **A release-manifest diff = the coarse topology diff** (boundary set + selection + clamps). The fine level is a
  provenance-graph diff. ([versioning-global-vs-per-boundary_en.md](versioning-global-vs-per-boundary_en.md))
- **ICC/GTS splits again.** An ICC diff (bake) = values + coarse topology (set, types). A GTS diff (narrate) = the
  full wiring diff.

## 6. Worked example — the Cryogenian base conversion (actually in progress)

```
retype:       definition.type  GSSA(720 pin)  →  GSSP(marker + stratotype)
clamp removed: Clamp{pin, 720 Ma}  deleted
subgraph:     + marker, + stratotype, + correlation/age subgraph, + ModelCandidate
value diff (effect): 720 (exact)  →  a derived value ± (uncertainty goes 'none → present')
```

A subtle point: **a retype changes the *shape* of the value — scalar (0 error) → distribution (with error).** A
naive value diff comparing two scalars can't even represent this "±0 → ±nonzero" change. Directly tied to the
schema's polymorphic value (decreed-exact vs computed-distribution).

## 7. Punchline — a change = a topology delta + its propagated value delta

A topology change usually produces downstream value changes (a split/retype shifts ages). The full "impact
report" is:

> **topology diff** (what changed structurally) → propagate → **value diff** (which numbers moved as a result)

**The two compose causally** — the topology change is the *cause*, the value change the *effect*. Why this is
essential to cdGTS's thesis: the most important changes in "CI for science" (boundary redefinition, stage split,
model swap) are **topological**, not numeric. A value-diff-only system misses exactly the changes that matter
most and are hardest to track by hand.

## 8. Reflected in the schema

- New `identity.lineage`: cross-version identity lineage — `op: created|renamed|split|merged|retyped|deprecated`,
  `from: [boundary_id]`. Declaring split/merge·retype so the diff can align. → [boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) §2.
- Note that a diff is not a record field but an **operation** between two versions (the taxonomy in §3).

## 9. Remaining open questions

- **Identifier persistence & lineage:** who assigns stable ids and how permanently; the format for recording split/merge lineage.
- **Granularity of topology:** the same change is a value change at one zoom and a topology change at another → at which layer to define the diff.
- **Aligning large rewirings:** id-first alignment + heuristics for the rest + flag the unaligned.
- **Selection diff vs structural diff:** whether swapping ModelCandidate A→B is a topology diff or a lighter selection diff.

## 10. Links

- [boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) §2 (`identity.lineage`) · §4
- [cycles_en.md](cycles_en.md) — clamp = retype vocabulary · [coherence-gate_en.md](coherence-gate_en.md) — re-validation trigger
- [node-graph-paradigm_en.md](node-graph-paradigm_en.md) — "topology is also subject to versioning" (original source)
- [versioning-global-vs-per-boundary_en.md](versioning-global-vs-per-boundary_en.md) — release-manifest diff

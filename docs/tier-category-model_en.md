# From Layers to Tier × Category

*English · [한국어](tier-category-model.md)*

> Status: **Retrospective (post-implementation).** Looks back at how the brainstorm's linear layers L0–6
> ([idea](idea_en.md) §5) folded up in the actual build. Not a new design — a re-description of what was built.

## 0. One-line thesis

**The linear L0–6 stack decomposed into two axes in the implementation** — a **tier** (registry / graph / release,
the gateway architecture of §8.2), and, within the graph tier, a **category** (data / process / clamp). Only the
"layer number" was an artifact.

## 1. The two things a layer number conflated

L0–6 pressed two distinct concepts onto one linear axis:

- **Kind** — *what* a node is. Observation / model / pin. → **intrinsic**. A U-Pb node is always an observation,
  in any graph.
- **Position** — *where* it sits in a pipeline. Upstream or downstream. → **extrinsic, emergent**. Not a property
  of the node type but of **how it is wired in a particular graph**.

Once the implementation is a DAG, "position" can't be a label. An age-model's output may feed another model; a
correlation may serve as an anchor. So what survived as a first-class taxonomy is **kind (category), not position
(layer number)**.

## 2. What survived — `NodeType.category`

The only node taxonomy in the implementation is three categories (`nodes.NodeType.category`):

| Category | What | Old layer | Examples (implemented types) |
|---|---|---|---|
| **data** | Immutable, cited observation leaf. Surfaces `params.distribution` as-is | L2 | radiometric-uPb · astronomical · magnetostratigraphic · biostratigraphic · **published-age** |
| **process** | Input distributions → output distribution (computation) | L3 · L4 · L5 | age-depth-model · cross-section-correlation · calibration-transfer · joint-inference |
| **clamp** | Pin a value or constrain | (outside the layers) | **order** (pin · range · freeze-version were removed — [cycles](cycles_en.md#12-reconsideration-note-2026-07--is-clamp-needed-as-a-distinct-concept)) |

L2 folded into data; L3·L4·L5 into process. The layer number dissolved into "depth within a specific DAG" — an
**emergent property, not a taxonomy**.

## 3. clamp — the category with no layer home

`clamp` had no place in the layer model, yet in practice it **cuts across two layers**:

- **GSSA** (L1, boundary definition) = an authored `published-age` leaf (data category) — a point mass δ. (Originally modeled as a `pin` clamp, since reconsidered.)
- **coherence constraints** (L5, order) = an `order` edge (the range/pin clamps were removed).

Layer numbers can't express "L1 and L5 are the same kind." Categories can. That is both evidence the layers were
the wrong cut, and the implementation-side confirmation of [concept-map](concept-map_en.md) §3-2 "clamp is the
unifier" — though that "clamp as unifier" premise was itself later reconsidered, scoping down clamp as a distinct
concept ([cycles](cycles_en.md#12-reconsideration-note-2026-07--is-clamp-needed-as-a-distinct-concept)).

## 4. Yet the layers didn't fully vanish — tiers

The ends (L0·L1·L6) were never nodes; they are **contracts / tiers**. So the structure is really 2-D, **tier ×
category**:

```
tier    registry (chrono)  ──────  graph  ──────────────  release (releases)
                                    └ category: data / process / clamp
old map  L0 · L1                    L2 ~ L5                 L6
build    Unit · Boundary ·          Graph · NodeInstance ·  Release · Selection ·
        Ratification · Locality     Edge · Gateway (engine)  BoundaryRecord · bake
```

- **Tier** (registry / graph / release) = the §8.2 gateway architecture. Three clean contracts.
- **Category** (data / process / clamp) = the node kind *inside* the graph tier.
- **Layer number** = emergent from wiring depth within a specific graph.

So the ends (L0/L1/L6) were gateway contracts, only the middle (L2–L5) won as categories, and **only the pure
linear numbering was the artifact**. Layers now survive as a human reading order (observe → model → synthesize →
release).

## 5. Ties to implementation status (as of 2026-07)

- **Tiers are solid**: registry (chrono) · graph/engine · release (releases), 1:1 across three apps.
- **Categories are solid**: data/process/clamp dispatch at runtime via [engine.kernels](../engine/kernels.py)
  `compute` (`category=="data"→params.distribution`, process→kernel, clamp→order). (pin/range/freeze-version were
  removed and GSSA moved to a `published-age` data leaf — [cycles](cycles_en.md#12-reconsideration-note-2026-07--is-clamp-needed-as-a-distinct-concept).)
- **The shallow parts stay shallow**: within process, the depth of L4 (correlation) and L5 (joint/coherence) is
  unfinished — notably the global coherence gate (`engine._certify`) is an ordering-dependent monotonicity stub.
  That is a separate task, orthogonal to this tier/category re-description.

## 6. Open questions

- Heterogeneity inside the data category: a pure observation (radiometric) and a "published-value reference"
  (published-age) differ in provenance depth ([concept-map](concept-map_en.md) §3-1, the provenance axis). Do we
  need a sub-distinction, or is a note enough?
- Keep clamp as its own category, or as a special case of process — currently its own category.
- Is the layer narrative (reading order) worth keeping in the docs, or fully replaced by tier × category?

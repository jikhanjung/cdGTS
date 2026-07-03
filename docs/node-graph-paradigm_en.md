# The Node-Graph Paradigm

*English · [한국어](node-graph-paradigm.md)*

> cdGTS's core conceptual metaphor. It starts from Blender's Geometry Nodes.

## The metaphor

Like Blender's Geometry Nodes, cdGTS is built as a **network of nodes**:

- **Data nodes** — the various primary observations (radiometric ages, astronomical ages, magnetostratigraphy, biostratigraphy …). Immutable, cited, the leaves of the graph.
- **Process/model nodes** — the processing and models that transform inputs (calibration, age-depth models, correlation …).
- **Edges** — data flow.

When this network is **evaluated**, the result is an **age for a specific point on Earth**. Gather all of these together and you get something like the ICC / GTS2030.

This view overlaps with the earlier Layer 2 (data) → Layer 3 (model) → Layer 4 (output) structure from [idea.md](idea_en.md), but seeing it as a **DAG (directed acyclic graph)** rather than as "layers" is more powerful.

## What the node metaphor gives you for free

- **Provenance = tracing the graph backward.** Follow the edges backward from any boundary age and every source that contributed is revealed. The lineage/audit of the FAIR principles is not a separate feature but is **built into the structure itself**.
- **Incremental re-evaluation.** Recompute only what is downstream of a changed node → the engine of "continuously tested".
- **Node swapping = what-if.** Swap a model node from spline ↔ Bayesian, or swap out a data node, and diff how the output changes. Alternative models/data = alternative graph branches.
- **Node group = a subgraph per region/boundary.** The local graphs of a particular locality are tied to a global stage boundary through a correlation node, and combining them all yields the whole-Earth time scale. → As the phrase "a specific point on Earth" implies, there is a genuine **spatial (geometry) dimension**.

## Two products, one graph

Two things come out of the same graph:

- **GTS2030** = the graph **narrated** at length — a "book" that serializes the reasoning, the evidence, and even the caveats.
- **ICC** = a snapshot that **bakes / crystallizes** the graph — only the final boundary numbers + names frozen. (Corresponds to Blender's "apply modifier → bake mesh".)

## Where it differs from Blender — the hard parts

1. **Edges carry distributions, not scalars.** Every observation has uncertainty, so evaluation is not deterministic but must be **probabilistic propagation** (Monte Carlo / Bayesian). To "bake" is precisely the act of summarizing and fixing a distribution.
2. **Cyclic dependencies.** Biostratigraphy is calibrated by radiometric ages, and the position of the radiometric sample is in turn constrained by biostratigraphy — a pure DAG can break. A decision is needed: forbid cycles and fold them into an explicit **joint inference node**, or allow iterative convergence.

## Further open problems

- **Topology is also subject to versioning.** It is not only node values that change but the **wiring** itself.
- **Governance / curation.** Who decides, and how, "which graph is the *official* ICC graph".

## The gateway layer — contracts and networks

> Status: hunch. It needs validation against real cases. It pairs with [idea.md](idea_en.md) §8.

The layers (Layer 0–4 in [idea.md](idea_en.md)) are reinterpreted not as "pipeline stages" but as **contracts**. Two kinds of thing alternate:

- **Gateway layer** = a **fixed type/interface** everyone has agreed on. Citable, version-tagged, the unit of release. The **commit point** that says "at this point, at least, we freeze to this schema".
- **The node network between gateways** = the **free topology** that produced that type. Where cycles, alternative models, probabilistic propagation, and correlation live.

The core rule: **the network is free, but the gateway type is upheld.** Whether you use a spline or Bayesian, both must emit the same gateway type (e.g. "global boundary estimate = distribution + provenance"). → Competing models = what-if branches.

| | Gateway | Node |
|---|---|---|
| Topology | fixed, schema contract | free, replaceable |
| Identity | citable, addressable | can be anonymous |
| Versioning | tagged independently | flows with the whole network |
| Immutability | frozen once released | keeps churning |
| Governance | **subject to ratification** | free experimentation |

What this gives you:

- **Reduced governance.** Not "control every node" but **"which gateways to ratify"**. Scholars play freely in the networks between gateways, and the curators (ICS, etc.) stamp only the gateways.
- **Cycle isolation.** Cycles are confined to the region *between* two gateways and resolved by joint inference, while the gateway output that comes out is a clean distribution. The cycle does not spread across the whole graph.
- **The meaning of CD becomes sharper.** Gateways are frozen periodically (releases), while the networks in between keep turning. The CI diff = "if you touch this network, how do the next gateway's numbers change".

An analogy: the compiler's **IR checkpoint.** Gateway = a stable intermediate representation (IR) that can be serialized, inspected, and diffed; the in-between network = optimization passes that can be swapped out at any time.

A rough layout (reading idea.md's Layers as gateways):

```
[G:naming]─▷(net)─▷[G:primary obs]─▷(age-depth net)─▷[G:local calibrated section]
                                                        │
                                        (correlation + synthesis net)
                                                        ▼
                                              [G:global boundary estimate]
                                                        │
                                              (bake / narrate net)
                                                  ┌─────┴─────┐
                                                  ▼           ▼
                                              [G:ICC]     [G:GTS]
```

Open questions:

- Is a gateway **global** or **per-boundary**.
- Is it a **type (schema)** or a **frozen instance (release)**, or both.
- What gets **promoted** to a gateway = the boundary of governance.
- **Boundary gateways are polymorphic.** GSSP-type (a computed distribution, with ±) ↔ GSSA-type (a decreed constant, no error)
  — the two types must fit in one schema. Grounds: [case-permian-triassic.md](case-permian-triassic_en.md),
  [case-precambrian-gssa.md](case-precambrian-gssa_en.md).
- **Topology rewiring is also subject to diff.** When the wiring itself changes — as in a GSSA leaf → GSSP network transition —
  a **topology diff** is needed separately from the value diff (Ediacaran done, Cryogenian in progress — a real, ongoing case).

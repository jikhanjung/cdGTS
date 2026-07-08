# Boundary–Span Duality — in the Graph Layer

*English · [한국어](boundary-span-duality.md)*

> Status: **design.** Fixes how the graph layer (`graph` app) represents the **chronostratigraphic
> skeleton**. chrono already separates Unit (span) from Boundary (point); we lift that same duality
> into the node graph as a first-class concern. Two decisions: (1) boundaries are referenced, not
> contained; (2) drop order nodes and connect boundary vertical ports directly.

> **[implemented]** This whole design is built — `nature` · `NodeGroup.kind/unit/lower/upper` · `Edge.kind=order` (graph/models.py), reflected in seed.

## 0. Thesis in one line

The skeleton of the time scale is **not a partition but a cell complex**. Units (Period, Age…) are
1-cells; boundaries are the 0-cells that share their endpoints. Two adjacent units **always share a
point**, so a boundary cannot live "inside one box." A boundary node is an **independent citizen**,
a member of no group; the unit (group) *references* its boundaries.

## 1. The problem — why today's structure creates a paradox

`NodeInstance.group` today is a **single FK** (`SET_NULL`). A node belongs to exactly one group —
mathematically a *partition*, a containment tree. Every element sits in exactly one box.

But the geologic column is not a partition.

- Base of Cambrian = top of Ediacaran (**adjacent units share a point**).
- Base of Cambrian = base of Cambrian's first stage (Fortunian) = base of Terreneuvian
  (**a unit and its sub-units share their lower bound**). In ICS these three are the same GSSP
  (Fortune Head) — a **single Boundary object** in chrono (`base-cambrian`).

So the `base-cambrian` node must be "outside" the Cambrian group (the seam with Ediacaran) and
"inside" it (the floor of the first stage) at once. "One box, one node" cannot express this. That is
the paradox.

## 2. The fix — boundaries are referenced, not contained

The instinct ("boundary nodes should exist independently") is right. But the implementation goes the
**opposite way from multi-membership** (putting one node in several groups).

- **Span groups nest as a tree.** Cambrian ⊃ Terreneuvian ⊃ Fortunian. A span has one parent, so the
  tree never breaks. `NodeGroup.parent` (nesting) is already this axis.
- **A boundary is a member of no group.** Instead the span points at it: `group.lower → boundary
  node` (lower = older), `group.upper → boundary node` (upper = younger). One `base-cambrian` node is
  referenced **simultaneously** as Ediacaran's `upper`, Cambrian's `lower`, and Terreneuvian's
  `lower`. Sharing lives on the *group* side (many groups → one node), not the *node* side — a single
  FK expresses it cleanly.

Key invariant: **whether a boundary is "a boundary of this unit" is not a property of the boundary
but of the (boundary, unit) pair.** `base-cambrianstage2` is *interior* to Cambrian but *bounding*
for Cambrianstage2. So don't stamp "boundary of X" on the boundary node; put it on the unit's
`lower`/`upper`. Then the number of boundary nodes = the number of distinct chrono.Boundary points,
not the number of unit endpoints (coincident endpoints dedupe to one node).

### Collapse semantics

Collapsing a unit hides its **interior** (sub-units, the internal boundaries between them, the
data/process machinery) and exposes its **two bounding boundaries as ports** — exactly what gateways
already do on collapse. A collapsed Cambrian still shows its `lower` (base-cambrian), the seam with
Ediacaran. Drill in and the interior boundaries reappear.

## 3. Node nature — a first-class property

Make a node's **nature** explicit; today it is only implicit in the node_type slug.

- `NodeInstance.nature ∈ {generic, boundary}`.
  - **boundary** — a boundary point (0-cell). An independent citizen — referenced, not contained.
    In assembly graphs this is the `published-age` leaf carrying the boundary value.
  - **generic** (default) — data/process/clamp machinery.
- nature is **orthogonal to node_type**. In pipeline graphs (examples 1–3) a boundary is a process
  node's output exposed by a Gateway — that node is generic, and the boundary identity lives in the
  Gateway. In assembly graphs the leaf node itself is boundary-nature. **Either way the bake/eval
  anchor stays the Gateway.**

Spans are groups, not nodes, so nature lives on the group side as `kind`:

- `NodeGroup.kind ∈ {container, unit}`.
  - **unit** — a chronostratigraphic span. `unit` (FK to chrono.Unit) binds it to the canonical unit
    → inherits rank and dual naming. `lower`/`upper` reference the two boundary nodes.
  - **container** (default) — a purely presentational grouping.

## 4. Drop order nodes — order is a connection, not a node

Today an `order` node sits between two boundaries (137 of them in example 4) checking
`gap ≥ min_gap`. But boundary nodes already carry **vertical order ports** (top = younger /
bottom = older, the ICC-column convention). **The connection between those ports is itself the order
constraint.** A dedicated node is redundant.

- Connect boundary nodes' vertical ports directly into a **time-ordered ladder**. That connection is
  an **order edge** (`Edge.kind = order`) asserting "target (younger) sits below source (older)."
- **Coherence gate L1 (order)** reads the **order-edge chain** instead of order-node verdicts: for
  each order edge it reads both boundary values and checks `younger < older` (gap ≥ min), chaining
  for monotonicity. Still *authored and sparse* (only placed connections are checked) — the property
  of order nodes, kept without the node.
- An order edge is a constraint, not data flow, so it is excluded from the data-DAG cycle check (the
  vertical chain is itself a DAG).

Result: example 4 loses nearly half its nodes (137 order nodes gone). The skeleton simplifies to
**boundary points + the order ladder linking them + unit groups.**

## 5. Model changes at a glance

| Target | Add | Meaning |
|---|---|---|
| `NodeInstance` | `nature` (generic\|boundary) | Boundary point as first-class, independent citizen. |
| `NodeGroup` | `kind` (container\|unit) | Marks the group as a span. |
| `NodeGroup` | `unit` (FK chrono.Unit, SET_NULL) | Bind to canonical unit (rank, dual name). |
| `NodeGroup` | `lower` / `upper` (FK NodeInstance, SET_NULL) | Reference the two bounding boundaries (shareable). |
| `Edge` | `kind = order` | Boundary vertical-port connection = order constraint. Replaces order nodes. |

Invariants (documented, enforced gradually):
- A boundary-nature node is not a group member (`group = null`); it is referenced by groups'
  lower/upper.
- One boundary node may be shared as the lower/upper of several groups (single FK, many-to-one on the
  group side).
- The engine stays flat (nature/kind/unit are for representation and coherence, not eval topology).

## 6. Fit with existing assets

- **Gateway** stays the bake/eval anchor (links chrono.Boundary). nature complements, not replaces it.
- Symmetric with chrono's Unit/Boundary split (and Boundary.below/above) — the graph layer now carries
  the same duality.
- Builds on **collapsed-group → port** (devlog 039) and **vertical order ports** (devlog 049).
- Related retrospective: [tier-category-model](tier-category-model_en.md) ·
  [node-graph-paradigm](node-graph-paradigm_en.md).

## 7. Staging

1. Schema (§5) + migration — additive and nullable, harmless to existing graphs.
2. Serializer round-trip + `_certify` L1 over order edges.
3. Seed transform (example 4): remove order nodes → order edges, boundary nature, unit-group
   kind/unit/lower/upper.
4. Frontend: preserve the new fields across save (no data loss) → seam rendering and order-ladder UI
   (follow-up).

# Evaluation order — dependency vs chronology, and order = a post-hoc check

*English · [한국어](evaluation-order.md)*

> Status: **post-implementation reflection + design confirmation.** What order the built engine
> (`engine/evaluate.py`) actually runs in, and what status the order (younger/older) node has inside it.
> Prompted by the question "should we sweep the graph in chronological order (Hadean → younger)?"
>
> **[implementation update]** Ordering is now expressed mainly as **`Edge.kind=order`** (a boundary vertical-port
> connection), not a separate `order` **node**. Gate L1 priority = **order edge > order node > gateway monotonicity
> heuristic**. The order-node description below still holds as a fallback path, and the "checks don't disturb
> computation order" thesis is unchanged. L1b/L2 (duration) are judged only over an asserted **unit span** (the
> order-edge interleave), devlog 120. Detail: [coherence-gate_en.md](coherence-gate_en.md).

## 0. Thesis in one line

Graph evaluation must run in **dependency order (topological sort)**. **Chronology (geologic-time order) is
not the order of computation — it is a property of the results.** The order node is a **post-hoc coherence
check** that changes no value, so it never perturbs the compute order.

## 1. Distinguish two "orders"

The confusion comes from calling two different orders by one word.

| | Definition | In the engine |
|---|---|---|
| **Dependency order (dataflow)** | "what feeds what" — a node runs once its inputs are ready | `topo_order` (topological sort). The necessary, uniquely correct order for a DAG |
| **Chronological order** | by the geologic age of the boundary (Hadean → present) | **Not a compute order.** A property of the **outputs** produced after evaluating the graph |

Boundaries are **largely independent** in the dataflow — Hadean base and Archean base don't reference each
other; each comes from its own upstream evidence (radiometric anchors, age-depth, correlation). Where one
boundary genuinely depends on another, that dependency is an **edge**, and `topo_order` already sequences it
correctly. Chronology and dependency may coincide, but they are not the same thing.

## 2. Two layers in the implementation — evaluate → certify

The engine splits into two stages:

```
evaluate_graph(graph)                     # ① compute in dependency order
  topo_order(...)  →  a distribution per node (kernels.compute)
        │
        ▼
_certify(run, graph, results)             # ② post-hoc coherence checks (the gate)
  L1 ordering · L2 duration …             # read values, judge only
```

① **evaluate** computes each node's distribution in topological order. ② **certify** takes those results and
runs the coherence gate ([coherence-gate_en.md](coherence-gate_en.md)). The key point: **computation and
checking are separate**.

## 3. How the order node is actually wired — an output tap on value nodes, an input to the check

It looks like the order node "feeds back" into a process node, but the wiring is the opposite:

- **Value nodes** (published-age, age-depth-model, …): `older`/`younger` are **outputs (source)** — mere taps
  that re-emit the node's own distribution. `kernels` produces **one** distribution per node, and every output
  port carries that same distribution (a source port changes no value; pure wiring).
- **Order node**: `younger` (top) / `older` (bottom) are **inputs (target)**. It **receives** two ages and the
  `order_check` kernel returns only a `{ok, gap}` judgment — **value unchanged** (`engine/kernels.py`). That
  judgment is then consumed as L1 inside `_certify`.

Edge direction: `age-depth.older (output) → order.older (input)`. So the order node is a **terminal sink**.

This yields a nice property:

> **A check only observes; it does not perturb the compute order.** topo sort places the order node after both
> operands automatically, and adding any number of order checks never changes the evaluation order of the
> value-producing nodes.

## 4. Three things to keep apart

"Coupled with a neighboring boundary" comes in different flavors:

| Relation | Does value flow? | How it's handled |
|---|---|---|
| order **check** (current) | ✗ (ok/gap judgment only) | Terminal sink. topo sort puts it last; no ordering problem |
| relative-age **propagation** (e.g. B = A − Δ) | ✓ directional | A **real data edge.** topo sort orders A→B (coincidentally chronological) |
| order **feedback constraint** (hypothetical) | ✓ bidirectional | Neighbors couple → a **cycle** → clamp / joint |

The second matters: even relative-age propagation is handled by the engine **following the edge, not reading a
clock**. When "chronology" seems needed, what's actually needed is **dependency order** — already handled.

## 5. Why "sweep from Hadean" is the wrong frame

Turn order from a check into a **value-adjusting constraint** (clamp so monotonicity holds), and neighbors
start referencing each other → a `process → order → process` **cycle**. That's exactly where topo sort breaks,
and the territory of [cycles_en.md](cycles_en.md).

And "sweep old→young" is just **one greedy, sequential** way to resolve that cycle. The problems:

- **Results depend on direction.** When younger evidence should tighten an older boundary (common), information
  flows only one way and is lost. **If the answer depends on sweep direction, that's a smell** — the signal to
  "lift this into an order-independent joint constraint."
- The principled solve is **joint inference with all constraints applied at once**; a sequential sweep is its
  degraded special case.
- A cycle isn't resolved by sweeping — you **clamp** (cut it with a fixed value) or solve it jointly.

## 6. Takeaway / recommendation

- Evaluation order should be driven by **dependency (topo sort)**, as it is now. Chronology lives not in
  computation but in three places: (a) the superposition constraint **inside** the age-depth kernel (deeper =
  older), (b) the **checks/constraints** of the coherence gate, (c) **presentation** ordering (narrate/display).
- **order = a post-hoc check** is the honest current summary. Keep the two-layer split: "evaluate (compute in
  dependency order) → certify (post-hoc temporal-coherence check)."
- If ordering must **actually adjust values**, that belongs to the **coherence gate's reconcile (L3b) / clamp**,
  not to a traversal direction. → [coherence-gate_en.md](coherence-gate_en.md) §3, [cycles_en.md](cycles_en.md).
  > ⚠️ **Reconsidered (2026-07):** clamp was scoped down — cycle-cutting folds into an authored `published-age` **leaf** / a joint-inference node / an `order` edge, not a `Clamp` primitive. See [cycles_en.md §12](cycles_en.md#12-reconsideration-note-2026-07--is-clamp-needed-as-a-distinct-concept).

## 7. Remaining open questions

- Keep the order node **check-only**, or one day promote it to a **feedback constraint** — if promoted, the
  clamp-vs-joint fork.
- As **derived checks** multiply (like L2 duration), does ordering/dependency appear *among the checks* in the
  certify layer?
- Can we **auto-detect** the "direction-dependent → lift to joint" verdict (re-run with the sweep reversed and
  diff)?

## 8. Links

- [node-graph-paradigm_en.md](node-graph-paradigm_en.md) — DAG · gateway/network · cycles · edge = distribution
- [coherence-gate_en.md](coherence-gate_en.md) — Layer 5 check ladder (L1 ordering · L2 duration · L3 reconcile)
- [cycles_en.md](cycles_en.md) — cyclic dependency and clamp (the territory if order becomes a feedback constraint)
- [tier-category-model_en.md](tier-category-model_en.md) — the data/process/clamp categories (post-implementation)

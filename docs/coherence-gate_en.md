# Coherence Gate — Layer 5

*English · [한국어](coherence-gate.md)*

> Status: The mechanism that turns a pinned set of boundaries into a valid
> global chart. It is the part flagged as "the real crux" in
> [versioning-global-vs-per-boundary_en.md](versioning-global-vs-per-boundary_en.md), and the operational core of
> **Layer 5 (global synthesis)** in [idea_en.md](idea_en.md) §5. → **implemented** (engine `_certify` · releases clamp reconcile · devlog 117·118·120). Tutorial: [tutorial-science-engine.md](tutorial-science-engine_en.md).

> **[framing update]** The "Layer 0–6" numbering here is now only a **reading order (narrative)**. The implemented spine is **tier (registry/graph/release) × category (data/process/clamp) + 16 node types** — see [tier-category-model.md](tier-category-model_en.md) · [concept-map.md](concept-map_en.md).

## 0. Where it sits — this IS Layer 5

The coherence gate is not a new concept but the **definition of the Layer 5 (global synthesis) node**. It takes
the per-boundary evidence produced by Layer 4 (correlation) and makes a **globally coherent set of boundary
ages**, then hands it to Layer 6 (publication).

```
[Layer 4: per-boundary correlation & evidence]
        │  (pinned boundary set + each one's provenance graph + shared-node graph)
        ▼
   {coherence gate  L0→L3}
        │
   ┌────┴─────────────┐
   ▼                  ▼
 PASS + certificate  violations[]
 (a valid chart)     {level, kind, boundaries[], severity}
        │
        ▼
[Layer 6: ICC (bake) / GTS (narrate)]
```

## 1. Signature

```
coherence_gate(
  manifest,          # {boundary_id → boundary_version} pinned set
  shared_node_graph, # which boundaries share which upstream nodes (decay constants, tracers…)
  claimed_level      # the coherence level this release claims, L0–L3
) → PASS + certificate | violations[]
```

- **certificate** = `{level_achieved, checks_run, warnings, gate_version}` — so consumers know the strength of the guarantee.
- **violations** = a structured list of `{level, kind, boundaries[], severity: fail|warn}`.

## 2. The ladder of checks (cheap/local → expensive/entangled)

| Level | Check | Input needed | Nature |
|---|---|---|---|
| **L0 structural** | Referential integrity + topology + **acyclicity**: every boundary resolves to an existing version, the units partition the timeline with **no gaps or overlaps**, and (after clamps are applied) provenance is **acyclic** within the release. Dual-naming pairs present. | id · topology · edge type | **FAIL** |
| **L1a ordering (point)** | For adjacent boundary pairs, age(younger base) < age(older base). Total monotonicity. | values | **FAIL** (almost always passes for flagship boundaries) |
| **L1b ordering (interval)** | Do adjacent boundaries' 2σ ranges overlap = a flag that "ordering is not statistically resolved" (not a violation). | values + ± | **WARN** |
| **L2 durations** | Stage/epoch length = difference of two boundaries. Negative durations; distribution mass leaking below zero. | values + ± + **covariance** | FAIL/WARN |
| **L3 correlation-aware** | Treat boundaries not as independent but jointly through shared upstream nodes. | each boundary's **provenance graph** | two branches below |

**"Adjacent" means asserted structure, not sorted values (important).**
The "adjacent boundary pair" in L1a/L1b/L2 is **not** inferred by sorting values. It comes only from a relationship the
user explicitly asserted — a **time-unit (span) node** joining two boundaries, or an **order edge** between them. Two
boundaries left floating with no connecting structure are **not judged (skip): "no assertion, no verdict."** A unit grips
its two bounding boundaries through the order-edge interleave (`base(older).younger → unit.older`,
`unit.younger → top(younger).older`) and its `duration = base − top` is what gets checked. (The machine never invents a
relationship — the project's "humans place, the machine checks" principle.)

**Why L2 requires covariance (the crux).**
Duration = age_old − age_young, and its variance is `Var(old) + Var(young) − 2·Cov(old, young)`. When two
boundaries share an upstream node (decay constant / tracer), `Cov > 0`, so naively computing
`Var(old)+Var(young)` **overestimates the duration's uncertainty**. To get it right the gate must know the
**correlation structure**, not just two `±` values.

**The two branches of L3.**
- **L3a validate:** leave boundary values as they are, compute the inter-boundary covariance from shared nodes,
  and **only check** that ordering/durations hold even with correlated error. Changes no numbers.
- **L3b reconcile:** put monotonic ordering as a hard prior and **jointly estimate** the boundary ages under
  shared priors → values can **shift**. Produces a coherent set even when raw records slightly conflict.

## 3. The central fork — validate only vs reconcile

This sets the gate's character:

- **Validate-only (L0–L2 + L3a):** the release's ages = the pinned records' ages, **verbatim**. Provenance stays
  clean (release number = record number = ratified value). But it can **only reject, not fix**.
- **Reconcile (L3b):** produces a coherent chart even when raw records conflict. But now the **release number ≠
  the record number** — a "release-adjusted age" appears and the release itself becomes an inference node.
  → **Reconciliation is more honest done via a subcommission's authored `Clamp` than via automatic joint
  inference** (the divergence becomes a named, attributable governance decision). Detail: [cycles_en.md](cycles_en.md).

**A clean mapping falls out — the two modes map exactly onto ICC/GTS:**

- **ICC = bake = validate-only.** Authority rests on traceable ratified values, so the release must not silently change numbers.
- **GTS = narrate = reconcile allowed.** For a research narrative chart, a globally co-estimated timeline is the point.

That is, **the gate's two modes = the gateway's two outputs.** Not a coincidence but two faces of one structure.

## 4. Two insights surfaced while concretizing

1. **Coherence is threatened by "asynchronous independent updates," not by "synchronous shared updates."** If a
   single decay constant changes, every dependent boundary moves **in lockstep**, so coherence is preserved. It
   is the **asynchronous** case — re-dating one boundary while leaving its neighbors — that breaks ordering. →
   The gate's main job is to **police asynchronous updates**.
2. **The coherence level a boundary can reach is capped by how machine-readable its provenance is.** L0–L1 need
   only values/ordering; L2–L3 need the provenance graph. A legacy boundary at the "published value + source
   only" level (or a GSSA) can participate only up to **L1**. → Directly connected to
   [idea_en.md](idea_en.md) §7's "does Layer 3 actually compute, or is it published-value + source only."
   **Coherence ambition sets the provenance requirement.**

## 5. What a boundary record must expose per level (minimal contract)

- **L0–L1:** `age.value_ma`, `identity.separates` (ordering), and (for L1b) `uncertainty`.
- **L2:** + shared-node identifiers (which boundaries it shares upstream with).
- **L3:** + the actual subgraph under `age.provenance_ref` (in a jointly-processable form).

→ This confirms that the `provenance_ref` in
[boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) is not decoration but the **key to the coherence level**.

## 6. Remaining open questions

- On L3b reconciliation, **how to cite/notate the "release-adjusted value"** alongside the record value.
- Policy on whether a release **blocks or passes** an L1b overlap WARN (differentiate flagship vs finely-subdivided intervals?).
- How far to track covariance — a full covariance matrix vs shared-node tags only.
- The gate's own version (`gate_version`) — when the check rules change, what is the status of past certificates?

## 7. Links

- [versioning-global-vs-per-boundary_en.md](versioning-global-vs-per-boundary_en.md) — the context where the coherence gate appeared (global release = manifest + coherence gate)
- [boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) — the `provenance_ref` · `age_model` fields
- [evaluation-order_en.md](evaluation-order_en.md) — the evaluate (dependency-order compute) → certify (gate) split; order = a post-hoc check
- [idea_en.md](idea_en.md) §5 (Layer 5) · [node-graph-paradigm_en.md](node-graph-paradigm_en.md) (shared nodes · cycles)
- Shared-node case: [case-permian-triassic_en.md](case-permian-triassic_en.md)

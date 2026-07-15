# Cyclic Dependencies and Clamps

*English · [한국어](cycles.md)*

> Status: **Analysis → partly reflected in the schema/gate → reconsidered (scope-down conclusion).** Expands the cycle problem (biostratigraphy ↔
> radiometric dating) that [node-graph-paradigm_en.md](node-graph-paradigm_en.md) flagged from the start, and
> introduces the subcommissions' **hand-crafted clamp** as the solution. → clamp primitives **implemented** (releases.Clamp · pin/range/order/freeze-version · devlog 118).
>
> ⚠️ **Reconsidered (2026-07): see [§12](#12-reconsideration-note-2026-07--is-clamp-needed-as-a-distinct-concept).** On the evidence of what was built and used, clamp is **not needed as a distinct first-class concept.** Everything it did folds into mechanisms that already exist — **an authored node (GSSA leaf) + order edges + a joint-inference node + the version spiral.** A human pinning a value is **fully covered by an authored node (GSSA leaf).** §1–9 are kept as the thinking (conceptual history).

## 1. The "cycle" is not one thing

Several feedback loops exist at different levels:

| Loop | Content |
|---|---|
| **Biostratigraphy ↔ radiometric** | A biozone gets absolute ages by dating ash beds within it, but the ash sample's position/zone membership is fixed biostratigraphically. Reusing the calibrated zone at other sections → feedback. |
| **Astrochronology ↔ radiometric anchor** | Cyclostratigraphy builds a *duration* scale from orbital cycles and needs a radiometric **anchor** for absolute pinning; radiometric ages are in turn validated/recalibrated against astrochronology. |
| **Decay constant ↔ inter-method calibration** | U–Pb ↔ Ar–Ar cross-calibration; K decay constants and monitor-mineral ages recalibrated against U–Pb and astrochronology → the "constants" are derived from ages. |
| **Age model ↔ correlation** | You must assign ages to build an age-depth model, correlation needs the age model, and correlation feeds back into a joint model (the Layer 4 ↔ 5 tangle). |

## 2. The crucial distinction — local mutual constraint vs global calibration feedback

- **Local mutual constraint is not a true cycle.** At one section, fossils and radiometric ages are both
  **observations** of the same truth (that section's age-depth relationship). Saying "they *jointly* constrain
  the age-depth model" has no logical circularity. The cycle appears only if you compute this *sequentially*.
- **The genuinely dangerous one is global calibration feedback.** A calibrated artifact (biozone absolute ages,
  decay constants, astrochronologic tuning) derived from some sections and *reused as input* to date others,
  which then feed back into re-deriving the calibration, becomes a loop across the whole graph. This is where the
  "dating the fossil by the rock and the rock by the fossil" circularity critique bites.

## 3. The local fix — a joint-inference node (+ a free bonus)

Fold local mutual constraint into a **Bayesian joint model**: put priors on age-depth + zone boundaries +
orbital tuning + (if needed) decay constants and sample the **joint posterior** → the cycle A↔B becomes a single
multi-input, multi-output node.

**Bonus:** that joint posterior *is* the **correlation structure (covariance)** the
[coherence gate](coherence-gate_en.md) asked for. Folding the cycle correctly gives the gate's L2/L3 input for free.

## 4. The global fix — unroll the cycle along the version axis

A gateway is a frozen versioned artifact. Promote a calibration artifact to a **gateway** and *within a release
it is a constant input*, cutting the live cycle. The feedback does not loop inside the release; it becomes the
**next release's calibration input**:

```
calibration_v1 → release R1 ages → (new data) → calibration_v2 → release R2 ages → …
```

That is, **a logical cycle is unrolled into a spiral along the time axis.** Each release is internally a clean
DAG; the feedback is the delta between consecutive releases. Same as compiler bootstrapping (freeze v1 to build
v2). **CD turns a cycle into fixpoint iteration; convergence = successive releases stop moving.**

## 5. Clamp — hand-crafted gates placed by subcommissions ★

**We already have one clamp: the GSSA.** A Precambrian boundary is not data-derived but a number the
subcommission pinned by hand. The clamp **promotes that GSSA special case to a general primitive.**

Flavors of clamp (like the node graph's `clamp(x,min,max)`):

- **pin** — fix to an exact value. ← this is the GSSA.
- **range** — constrain to `[min,max]` ("between 538–542 Ma; if it wanders out, clamp to the bound + flag").
- **order** — force ≤ the older neighbor (a monotonicity clamp).
- **freeze-version** — pin a calibration artifact to a specific version for this release (← cuts the cycle).

**It solves two open problems at once:**

1. **"Where to draw the freeze line."** → Not an algorithm but **the position where a subcommission places a
   clamp is the freeze line.** Each subcommission owns its system's boundaries, so the cycle is cut at an
   accountable point.
2. **"The spiral may oscillate."** → **A clamp is a damper.** A hand-fixed node prevents runaway feedback and
   stabilizes the version spiral. Exactly what a clamp does in signal processing.

## 6. The coherence gate is redrawn

The Layer 5 gate becomes not **one monolithic automated gate** but **many authored clamp nodes scattered through
the graph + an automated gate that checks the rest**:

- clamp = a **governance gateway owned by a subcommission, plugged *inside* the network**.
- the automated gate: (a) apply the authored clamps, (b) check that the remaining graph is **acyclic and
  coherent** and that the clamps actually cut all cycles.

**More honest than automated reconciliation (L3b).** When a value diverges from the model output, that
divergence becomes a *named, attributable decision*: *"the X Subcommission redefined model output Y via a clamp
(rationale: …)"* — not a hidden statistical adjustment. → Better to replace the gate's reconcile mode from
"automatic joint inference" to **"authored clamp."**

## 7. Tensions

- **Over-clamping = fossilization.** Clamp too much and the continuously-deployed stream is ignored → the chart
  stops reflecting new science. The **authority-stability vs CI-responsiveness** tension is localized to the
  clamp node and negotiated per boundary by the owning body.
- **A clamp is itself versioned/ratified.** When a subcommission changes a clamp, that is a governance event with
  its own diff.
- **Sandboxes must be able to remove a clamp.** "What if we don't fix this?" is exactly a what-if. Clamps live in
  the release manifest / governance layer and are **overridable (removable) in a sandbox** → same grain as the
  selection in [competing-models_en.md](competing-models_en.md).

## 8. Schema / graph implications

- Add a **`Clamp`** node type: `owner` (subcommission), `kind: pin|range|order|freeze-version`, `value|bound`,
  `rationale`, `ratified`, `overridable_in_sandbox`. → reflected in
  [boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) §2.
- **GSSA = the `Clamp{kind: pin}` special case** → definition type and clamp unified under one root.
- Add an edge **type** to provenance (`co-location` | `calibration-transfer`) → lets the gate detect
  self-reference (cycles).
- Coherence gate: check "acyclic + coherent residual graph after clamps applied" → [coherence-gate_en.md](coherence-gate_en.md).

## 9. This changes cdGTS's mission

cdGTS's role becomes **not "automatically compute the time scale" but "give subcommissions a graph on which they
place accountable clamps, and automatically propagate / check / diff the rest."** This is a **third answer** to
[idea_en.md](idea_en.md) §7's long-standing open question ("does it compute, or is it published-value + source"):
**humans clamp the authoritative nodes; the machine propagates, checks coherence, and diffs.**

## 10. Remaining open questions

- The **minimal set** of clamps — how to find the fewest clamps that cut all cycles (auto-suggest + human approval?).
- Spiral **convergence criteria / damping**.
- **Scope partitioning** of joint-inference nodes (folding everything is intractable) → the approximation the partition introduces.
- **Conflicts between clamps** (two subcommissions' clamps contradict at a boundary) — how to arbitrate.

## 11. Links

- [node-graph-paradigm_en.md](node-graph-paradigm_en.md) — cyclic dependency · joint inference (original source)
- [coherence-gate_en.md](coherence-gate_en.md) — clamp application + acyclicity check
- [boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) §2 — `Clamp` node · GSSA = clamp
- [competing-models_en.md](competing-models_en.md) · [versioning-global-vs-per-boundary_en.md](versioning-global-vs-per-boundary_en.md) — release/governance layer

## 12. Reconsideration note (2026-07) — is clamp needed as a distinct concept?

> Revisits the "clamp = the unifier" conclusion of §5–9 against what was actually built and used. **Bottom line:
> everything clamp did folds into other, already-existing mechanisms, so clamp does not need to exist as a
> distinct first-class concept / type / governance record. A human pinning a value is fully covered by an
> authored node (GSSA leaf).** The cycle analysis in §1–4 still holds — in fact it is what supports the
> conclusion that a graph-level loop never needs to arise in the first place.

### Usage (evidence)

- Graph clamp nodes: only two `pin` nodes exist, and **both are the same GSSA decree** (2500 Ma, base-proterozoic). `range`: 0 · `joint-inference`: 0.
- `releases.Clamp` (authored governance record): **0 in the real seed.** Only `seed_demo._clamps()` plants a demo (a range on base-triassic that is honored / a pin on base-cambrian that is violated → reconcile demo).
- So apart from the single GSSA, clamp is **almost entirely demonstration scaffolding.**

### Each of the four pillars folds away

- **Cycle-cutting → unnecessary.** Biostratigraphy↔radiometric is a *scientific* mutual calibration, not a
  pipeline dependency cycle. Fold the two into **a single joint-inference process node**, resolve the circularity
  *inside* the node, and emit only value+σ — the graph stays a DAG (§3's joint node is already this answer). That
  is why real graphs draw no loops: with no cycle to cut, no breaker (clamp) is needed. (The difficulty does not
  vanish; it is encapsulated *inside* the node boundary = the right place for it, and the job of P06.4b.)
- **pin / GSSA → an authored data leaf suffices.** A GSSA is "a boundary whose value is authored, not derived" —
  exactly what a `published-age` leaf (+ `definition_type=GSSA`) already does. The clamp abstraction adds nothing.
- **order (monotonicity) → already handled by order edges (the L1 gate).** `Clamp{order}` is redundant.
  - **Epilogue (devlog 149)**: this conclusion only removed `releases.Clamp{order}` — the graph-side **`order`
    NodeType** (plus its kernel and the L1 fallback branch) survived, used by no graph at all. It is now gone too,
    and since `order` was the **last member of the clamp category**, the **`clamp` category itself disappeared**
    (dropped from `NodeType.Category`). Remaining: data · process · reference.
    → [tier-category-model](tier-category-model_en.md) §2·§3.
- **freeze-version → already done by §4's version spiral** (a gateway = a constant within a release). No per-boundary clamp needed.

### The release override (§6) is in the wrong place

`releases.Clamp` + `reconcile` (L3b) *directly edit* the baked release's values to satisfy the clamps. But the
**graph that produced those values still says the old value** → a **provenance hole**: the published number no
longer traces to a graph evaluation. Reproducible provenance is this system's core, so overriding out-of-band at
the release tier conflicts with that principle. If a subcommission override is genuinely needed, it belongs as an
**authored node inside the graph that gets re-baked — which is then the same shape as a GSSA leaf.** Even this
case converges on the authored leaf.

### Conclusion

Clamp's four jobs + the governance override all fold as follows:

| What clamp tried to do | Replacement |
|---|---|
| pin / GSSA | **authored data leaf** (`published-age`, `definition_type=GSSA`) |
| cycle-cutting | **joint-inference node** (circularity encapsulated *inside* the node) |
| order (monotonicity) | **order edges** (L1) |
| freeze-version | **version spiral** (gateway) |
| release override | if ever needed → **an authored leaf inside the graph** + re-bake |

→ **No distinct clamp concept / type / governance record is needed.** §9's mission still holds: instead of
"humans clamp," it is **"humans author the authoritative nodes (leaf/order); the machine propagates, checks
coherence, and diffs."**

### Scope-down sketch (implementation is follow-up; direction only here)

1. **Keep the conceptual history.** §1–9 stay as the thinking (do not delete). This §12 is the reconsidered conclusion.
2. **Shrink the graph clamp nodes.** Migrate the two `pin` (GSSA) nodes to an authored leaf (`published-age`/GSSA);
   the `range` and the `clamp` category NodeType are unused → deprecation candidates. `is_cycle_breaker` can keep
   only `joint-inference`.
3. **Isolate `releases.Clamp` + verify/reconcile.** With zero real use, mark them **demo-only** (seed_demo) or
   consider removal. Do **not** build the graph↔release clamp *integration* (it would wire two unused machines
   together). This also eases the `services.py` bloat R02 flagged.
4. **Update the mission wording.** "humans clamp" → "humans author nodes."

### Triggers that would reopen this (deferred until then)

- **A real graph cycle that cannot be folded** — genuine mutual wiring between separate nodes that a single joint node cannot encapsulate.
- **A real governance override that must live outside the graph** — a case a subcommission cannot express even as an authored leaf.

Both are hypothetical today. If one appears, reopen this note.

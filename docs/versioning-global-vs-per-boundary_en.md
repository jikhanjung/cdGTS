# Global vs Per-Boundary Versioning — Open Questions

*English · [한국어](versioning-global-vs-per-boundary.md)*

> Status: **Analysis note. No decision.** An expansion of the "global vs per-boundary versioning" item in
> [boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) §4. Here we only decompose the problem and
> **define it as open questions**.
>
> **[partly implemented]** A global release = a pinned record set (bake) + the coherence gate is implemented
> (`releases` app, bake/narrate). Some open questions below are thereby resolved; an independent per-boundary
> version manifest is still unbuilt (open question).

## 1. The problem (one line)

It is the classic software problem of **"component version vs release lockfile"** — each package has a version,
and a separate lockfile pins them all at one instant. But geology adds a twist that pure software lacks:
because of **coherence constraints** between boundaries, a global release cannot be "just the latest value of
each boundary gathered together."

## 2. Sub-problems

- **A. Cadence mismatch (cdGTS's reason to exist).** Science updates per boundary, **asynchronously and
  continuously** (P–T 2014, base-Cambrian contested, Ediacaran 2004), while publication (ICC/GTS) is
  **global and periodic**. The whole thesis is "a per-boundary update shouldn't have to wait for a decadal
  global release," so per-boundary versions are mandatory. But citation/authority demand stable global
  snapshots → both are needed.

- **B. What a global release *is*.** ① a **copy snapshot** of all boundary records vs ② a
  `{boundary_id → boundary_version}` **manifest (lockfile)** + shared-node versions + model choices. ② has the
  same shape as git's (immutable blobs + a tree/tag pointing at them).

- **C. Coherence (the genuinely hard part).** Boundaries are not independent → covered separately in §3.

- **D. Changes that don't attach to a single boundary.**
  - *Shared-node recalibration:* one decay constant / tracer feeds dozens of boundaries (the P–T case), so
    changing it moves them **simultaneously**. Intrinsically a global event, awkward under per-boundary
    versioning alone.
  - *Topology/nomenclature changes:* splitting a stage, or GSSA→GSSP conversion, changes the **set of
    boundaries** itself (add/remove/rename). Per-boundary versioning only handles "fixed identity + changed
    value" → a global version must version the **set and topology** too.

- **E. Sandbox = baseline + overrides.** "What if I add this U-Pb date?" is a **per-boundary delta** layered on
  a global baseline. "Use ICC-2024/12 but swap base-cambrian for my experimental version" = the lockfile +
  local-override pattern.

- **F. Asymmetry of citation/authority.** Ratification is **per boundary** (P–T 2001, Cambrian 1992, Ediacaran
  2004); publication is **global**. `status.level: ratified` lives on the boundary, while a global release is
  the governance act of curating and bundling ratified boundaries. Reproducibility requires a citation to point
  at **both the boundary version and the global-release context**.

## 3. A reality check on coherence (C)

There are at least three constraints between boundaries:

- **Monotonic ordering:** in a chart, age(base of younger unit) < age(base of older unit). Updating boundaries
  independently and gathering "each one's latest" can in principle produce an **inversion**.
- **Duration:** a stage's length = the difference of two boundary ages. Differencing two boundaries taken from
  different versions gives a wrong value.
- **Correlated uncertainty:** when a shared node (decay constant / tracer) feeds several boundaries, their
  errors are partly **correlated**. A duration's uncertainty can be smaller than a naive root-sum-of-squares, so
  a global release must know the **correlation structure itself**, not just two `±` values.

> **Reality clue (important).** The flagship boundaries — the ones used widely enough to sit on the ICC — are
> **far enough apart** that they are not close enough to actually invert in time. So a monotonic-ordering
> violation is mostly **theoretical** for the flagship boundaries. Even so, monotonic ordering is an
> **invariant the model should be aware of**, and where the problem actually bites is in **finely-subdivided
> intervals** (e.g. closely-spaced stages), cases where **2σ ranges overlap**, and the duration /
> correlated-error computations above. → So a global release must be a set that has passed at least a
> **monotonic-ordering check**, and ideally a **coherence gate** that also handles correlated error — not
> merely "the latest values gathered."

## 4. Shape of a resolution (a direction only, not a decision)

It looks like **two layers**, not an either/or:

- **Boundary records** = the immutable, independently-versioned **source of truth** (the continuously-deployed
  components).
- **Global release** = a **manifest/lockfile** pinning those records + shared-node versions + model choices +
  a **coherence guarantee**. Like git's (blobs + tag), but having passed geology's specific **coherence gate**.

The crux is not "per-boundary vs global" but **how to define the coherence check that turns a pinned set of
boundaries into a valid chart**.

## 5. Open questions (collected)

1. Is a global release a **copy snapshot** or a **manifest/lockfile**?
2. Should the coherence gate be at the level of **validation**, or go all the way to **joint inference**?
3. Should the **monotonic-ordering invariant** be a hard constraint or a lint/warning? (Rare for flagship
   boundaries, but needed for finely-subdivided intervals.)
4. How to express/record a global event like **shared-node recalibration** that bumps many boundary versions at once.
5. Where to put the versioning of **topology/set changes** (add/remove/rename a boundary) — outside the boundary
   record, in a global layer?
6. How to represent **sandbox overrides** (baseline + per-boundary delta) in the schema.
7. A minimal form that lets a **citation** point at both a boundary version and a global release.
8. How a release should preserve/convey **correlated uncertainty** (the shared-error structure).

## 6. Links

- [boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) §4 — the item this note expands
- [idea_en.md](idea_en.md) §6 (workflow) · §7 (versioning strategy) ·
  [node-graph-paradigm_en.md](node-graph-paradigm_en.md) (shared nodes · incremental re-evaluation)
- Shared-node case: [case-permian-triassic_en.md](case-permian-triassic_en.md) (tracer/decay constants feed many boundaries)

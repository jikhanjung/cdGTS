<!-- lang: en · pair: tutorial-science-engine.md -->
# Tutorial — Understanding the Science Engine hands-on (Arc A / P06)

[한국어](tutorial-science-engine.md)

This walks you through cdGTS's **science engine** (uncertainty · covariance · coherence gate · clamps) by **clicking
through it**, not just reading. The ideas are abstract, so the tour is built around manipulating the deployed demo data.

- **Where**: the deploy `cdgts.paleobytes.info` (or test `127.0.0.1:8011`).
- **Prereq**: the demo data must exist — if not, run `python manage.py seed_demo` once on the server (idempotent).
- **Time**: 10–15 min, clicking only (no code).

---

## 0. In one sentence — what this engine does

> **Age uncertainty is not a single `±`.** It decomposes into components (analytical / systematic / model), and **when
> several boundaries share a systematic error (a decay constant, a tracer) those errors are correlated.** When you look at
> the *gap* between two boundaries (a duration, an order), the shared error **cancels in the difference** — so the order is
> more (or less) resolvable than a single ± would suggest. The engine carries this structure, and the **coherence gate**
> judges order and duration with it.

Once that sentence clicks, you understand Arc A. The exercises below manufacture exactly that click.

---

## 1. Background — just three concepts

### (a) Distribution = a fidelity ladder (L0–L5)
A boundary's age flows as a **distribution**, not a scalar.

| Level | Representation | Example |
|---|---|---|
| L0 exact | point mass (GSSA agreed value) | 2500 Ma |
| L2 decomposed | error budget (±analytical / +systematic / +model) | 251.9, budget{model:0.05} |
| L3 shape | asymmetric HPD | median + [lo,hi] |
| **L4 joint** | marginal + **shared systematic tags** | …, shared:[{decay-238U, σ}] |
| L5 full | posterior samples | (coming in P06.4) |

What matters: **L2's decomposed budget** and **L4's shared tags**. *Whether two boundaries share a systematic component*
**is** their covariance.

### (b) Covariance and duration
Since `duration = older − younger`:

```
Var(duration) = Var(older) + Var(younger) − 2·Cov(older, younger)
```

If two boundaries use the same systematic source (e.g. the same U decay constant), **Cov > 0** → the duration error
**shrinks** (correlated errors cancel in the difference). With no shared source, Cov = 0 and the errors just add. **This is
the heart of Arc A.**

### (c) The coherence gate (post-evaluation verdict)
Evaluating a graph attaches a **consistency certificate**, shown as chips in the Results panel:

| Chip | Check | Verdict |
|---|---|---|
| **L0** | structure (acyclic) | fail |
| **L1** | order (point) | fail |
| **L1b** | order (covariance-aware, 2σ) | **warn** |
| **L2** | duration > 0 | fail |
| **L3** | reconcile (clamp) | (release layer, §3) |

`pass` (green) · `warn` (amber) · `fail` (red). A **warn is not a failure** — it means "statistically unresolved."

---

## 2. Exercise 1 — the covariance gate: *same values, one tag flips the verdict*

The two deployed demo graphs have **identical values and identical errors**, differing by exactly one thing — a shared
systematic tag.

### Steps
1. In the **Editor**, use the top **graph dropdown** → **"Demo: duration overlap (independent errors → L1b warn)"**.
2. **Actions ▾ → Evaluate**.
3. Read the **Results panel**:
   - consistency badge **amber (warn)**, **L1b** chip amber.
   - note: `L1b 순서 통계적 미해결: olenekian↔anisian (Δ2.0 < 2σ 4.243)`.
4. Dropdown → **"Demo: duration resolved (shared systematic → L1b pass)"** → **Evaluate**.
   - consistency **green (pass)**, **L1b** green.

### What happened (the numbers)
In both graphs the two Age boundaries sit on either side of an **Olenekian time-unit** node, joined by order edges — that
**asserts** the sequence, and the gate only judges the duration of an **asserted unit** (two floating boundaries are
skipped). The boundaries are **base-Olenekian 249.0 Ma**, **base-Anisian 247.0 Ma** (gap **2.0 Myr**), each **1σ = 1.5 Myr**.

- **independent (warn)**: no sharing → `2σ_gap = 2·√(1.5² + 1.5²) ≈ 4.24`. Gap 2.0 < 4.24 → **order unresolved (warn)**.
  ("The boundaries are 2 Myr apart, but the error is 4 Myr — you can't be statistically sure which is older.")
- **shared (pass)**: both share `decay-238U` (σ 1.4) → `Cov = 1.4·1.4 = 1.96` →
  `Var_gap = 1.5² + 1.5² − 2·1.96 = 0.58`, `2σ_gap ≈ 1.52`. Gap 2.0 > 1.52 → **order resolved (pass)**.

### Takeaway ✅
> **Even with identical values and errors, where the error comes from (shared systematic or not) flips the order verdict.**
> A single `±` can never do this — which is why we carry distributions decomposed into components.

---

## 3. Exercise 2 — Clamps: verify-only (L3a) vs apply (L3b)

> **⚠️ Reconsidered — this exercise is DEMO-ONLY.** Whether "clamp" deserves to be a distinct first-class concept was
> reconsidered and **scoped down**: the graph clamp NodeTypes (`pin` · `range` · `freeze-version`) were removed, leaving only
> `order`; GSSA is now an authored `published-age` leaf rather than a `pin` clamp; and cycle-breaking is unified into a single
> `joint-inference`. `releases.Clamp` + verify/reconcile **still exist but are isolated as demo-only** (only `seed_demo`
> creates them, and the Vault tab is now labeled **"Clamps (demo)"**). So the walkthrough below still works as a
> **demonstration of the governance idea** — not as a live product feature.
> Background: [cycles §12](cycles_en.md#12-reconsideration-note-2026-07--is-clamp-needed-as-a-distinct-concept).

A **Clamp** is an authored governance constraint (pin/range/order/freeze) placed by a subcommission. How a release treats it
splits into two contracts.

### Steps
1. In the **Vault**, select release **ICS-2024/12** → the **Clamps (demo)** tab.
2. The table shows two clamps:
   - `base-triassic` **range [250, 253]** → **honored** (value 251.9 is inside).
   - `base-cambrian` **pin 536.0** → **violation**: `538.8 ≠ pin 536.0`.
   - 👉 The value does **not** change here. This is **L3a = verify** = the ICC/bake contract: *"leave the published value
     alone, just report governance violations."*
3. Signed in as **staff (admin ★)** you'll see a **Reconcile (L3b) →** button. Click it:
   - base-cambrian moves to **536.0**, the violation clears.
   - 👉 **L3b = reconcile (apply)** = the GTS contract: *"actually move the value to honor the authoritative clamp."*

### Arbitration
If a boundary has several clamps, the strongest wins by **precedence `pin > range > order > freeze`**. Same precedence but
**different owners** → flagged as a **conflict** (not auto-applied — a human must resolve it).

### Takeaway ✅
> The **split between L3a (verify) and L3b (reconcile)** is this project's core contract: *ICC freezes published values,
> GTS reconciles them.* Clamps are **where governance touches the numbers** — the bridge to the next topic (Arc B).

---

## 4. Experiments (build intuition)

- **Force an L2 fail**: in the Editor, set one boundary equal to its neighbor (e.g. base-Anisian 247 → 249), save →
  Evaluate → **L2 fail** (zero-length unit, red). "Duration ≤ 0 = degenerate."
- **Turn shared back into warn**: in `demo-cov-shared`, narrow the gap (e.g. 249 → 247.6) and even with sharing it warns
  again — showing sharing isn't magic, it's the size of correlation *relative to the gap*.
- **See the numbers**: each node card in the Results panel shows its uncertainty (± / HPD). The Vault **Table** tab also
  lists per-boundary uncertainty.

---

## 5. How the demo data is made

`releases/management/commands/seed_demo.py` (idempotent):
- Two covariance-contrast graphs (§2) — identical values/±, differing only by the `decay-238U` shared tag.
- Two authored clamps on the published release (§3) — an honored range + a violated pin.

It leaves the main seed untouched. It disappears after a container restart or the nightly mirror sync, so **re-run**:
```
docker exec <container> python manage.py seed_demo
```

---

## 6. The bridge from Arc A to governance

Once you've played with this, the next questions arise on their own:
- **Who** authors a clamp and **who** ratifies it? (→ P05 Membership · can_ratify · propose/ratify)
- When a boundary has **competing models**, pick one or average/envelope them? (→ **envelope/BMA**, Arc B)
- How is a whole release **versioned and assembled**? (→ global vs per-boundary versioning, lineage diff)

In short: **you need Arc A (honest uncertainty) to see why Arc B (governance) is needed.** The L3a/L3b split of clamps is
exactly that hinge.

---

## References
- Concepts: [distribution-representation](distribution-representation_en.md) · [coherence-gate](coherence-gate_en.md) ·
  [cycles](cycles_en.md) · [competing-models](competing-models_en.md) · [idea](idea_en.md)
- Implementation log: devlog `P06` (plan) · `116` (covariance backbone) · `117` (gate) · `118` (clamps) ·
  `119` (capstone demo) · `P06.4` (Bayesian joint plan).

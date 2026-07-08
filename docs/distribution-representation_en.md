# Distribution Representation

*English · [한국어](distribution-representation.md)*

> Status: **Analysis → reflected in the schema.** An expansion of the last open question ("distribution
> representation") in [boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) §4. The concretization of
> [node-graph-paradigm_en.md](node-graph-paradigm_en.md)'s *"edges carry distributions."*

## 1. Reframing — it isn't "± vs HPD granularity"

Three distinct problems overlap: the uncertainty is (A) **structured**, (B) **non-Gaussian**, and (C)
fundamentally **joint**.

## 2. A — uncertainty is a decomposed budget

A boundary age's error has several components that must not be lumped:

- **analytical** — the lab measurement error (P–T's ±0.024).
- **systematic** — decay-constant / tracer calibration. **Shared across boundaries** → correlated.
- **model (epistemic)** — which age-depth / correlation model (the competing-models axis).
- **interpolation / correlation** — error added by transfer when the boundary is not at a dated horizon.

Not an invention but **actual practice**. CA-ID-TIMS papers (including our P–T case, Burgess 2014) report ages as
**`± X / Y / Z`** (analytical / +tracer / +decay constant) — because which component to include depends on *what
you compare* (U-Pb to U-Pb → analytical only; U-Pb to Ar-Ar → include systematic).

**The crucial link:** whether two boundaries' errors are correlated is determined by *whether they share
systematic components*. So this decomposed budget *is* the **covariance information** the
[coherence gate](coherence-gate_en.md) asked for at L2. → **Distribution representation and coherence covariance
are two ends of one problem.** A single `plus_minus` does neither.

## 3. B — distributions are not Gaussian / symmetric

`± 2σ` assumes a symmetric normal, but:

- Bayesian age-depth posteriors are often **asymmetric** (95% HPD ≠ mean ± 2σ).
- A correlation transfer with two competing hypotheses is **multimodal**.
- The competing-models envelope is a **mixture**.

Representation options (cheap → expensive): point + symmetric σ → point + asymmetric HPD (median · 95% lo/hi) →
parametric (skew-normal) → quantiles/CDF → posterior-sample reference → a re-runnable **generating model**.

## 4. C — the real object is joint, not marginal (the deepest layer)

- **Duration = the difference of two correlated boundaries** → needs the joint (covariance).
- **Monotonic ordering is a joint constraint** → the true posterior is not a product of independent marginals
  but an **order-truncated joint**.

The real object of interest is the **joint posterior over all boundary ages**; per-boundary marginals are its
**lossy projection**. This joint is the same as the **joint posterior a joint-inference node yields for free** in
[cycles_en.md](cycles_en.md).

## 5. The fidelity ladder of "bake" (L0–L5)

| Level | Representation | Use |
|---|---|---|
| **L0 point** | number only (251.902 Ma) | ICC headline |
| **L1 symmetric ±** | value ± 2σ (analytical) | (old) schema |
| **L2 decomposed budget** | ± analytical / +systematic / +model | comparison · **covariance** |
| **L3 shape** | median + asymmetric HPD / parametric | skew · multimodal |
| **L4 joint summary** | marginals + covariance (or shared-component tags) | **durations · ordering** |
| **L5 full posterior** | sample reference / re-runnable generating model | anything (heavy, needs provenance) |

This ladder is **parallel** to the gate's L0–L3 and the provenance-cap from cycles. The **distribution fidelity a
boundary can expose is capped by the machine-readable depth of its provenance** — a legacy "published value +
source" boundary reaches L0–L1, a fully-modeled one L5. → **Distribution representation, coherence level, and
cycle resolution are all governed by the same provenance depth.** ICC (bake) freezes a mid rung; GTS (narrate)
references L5.

### 5.1 decomposed vs joint — implementation and intuition (P06)

The two rungs most often confused. **decomposed (L2) is one boundary's marginal; joint (L4) also carries the
correlation between boundaries.**

**Storage** (`nodes/distribution.py` · `engine/kernels.py`):
- **`decomposed`** = `budget: {analytical, systematic, model}` + `sigma` (the σ-level the budget is quoted at).
  1σ = `√(Σ budget²) / sigma`. The components are **magnitudes only** — no label for *which shared source*.
- **`joint`** = adds `shared_components: [{ref, sigma}]`. Each tag = *"σ of my error comes from this shared source
  (e.g. `decay-238U`)."* The marginal (own 1σ) is **identical** to decomposed; only the sharing info is added.

**The difference bites in duration.** `Var(dur) = Var_a + Var_b − 2·Cov`, `Cov = Σ_(shared ref) σ_a·σ_b`.
- decomposed vs decomposed → no shared ref → `Cov=0` → errors add in quadrature (**independence assumed**).
- joint vs joint (same ref) → `Cov>0` → that much **cancels in the difference**.

**"Independent measurement ≠ independent error" (the crux).** Two dates measured separately still feed the **same
value** of the **decay constant / tracer calibration** into both age calculations. If λ is off, both dates shift the
**same direction together** → full effect on **absolute ages**, almost none on their **difference (duration)**. So the
shared systematic cancels in a duration, leaving only each date's own **analytical** error. (This is what EARTHTIME's
`±X/Y/Z` reporting institutionalizes: compare within a system = X analytical only; absolute / cross-system = through
Z, the decay constant.)

**Demo numbers** (`seed_demo`, two adjacent Age boundaries, each 1σ=1.5):
- joint → **1.4** of it is the shared `decay-238U`, `√(1.5²−1.4²)=`**0.54** is the boundary's own analytical error.
- decomposed (independent): `σ_gap=√(1.5²+1.5²)=`**2.12** → 2σ 4.24.
- joint (shared): `Cov=1.96` → `σ_gap=√(0.54²+0.54²)=`**0.76** → 2σ 1.52. **The same gap flips warn→pass.**

**When to tag joint (a modeling claim).** A `joint` tag is a **scientific claim** that *"these two dates use the same
systematic source"* — the cancellation is only justified when that's true. Different methods (U-Pb vs Ar-Ar, different
λ) share nothing → **leave them decomposed** (→ independent, no cancellation). The model also assumes the tagged
component is **perfectly correlated (r=1)** (`Cov=σ·σ`). So the call is left to the data provider.
→ [coherence-gate.md](coherence-gate_en.md) L1b/L2, [tutorial-science-engine.md](tutorial-science-engine_en.md).

## 6. Unification with GSSA/clamp — a decreed value is a degenerate distribution

GSSA = exact = **δ(2500)**, a zero-variance **point mass**. The polymorphic value naturally includes it
(`fidelity: exact`). And **a clamp is a distribution operator**:

- **pin** = collapse to δ, **range** = truncate to `[min,max]`, **order** = truncate to the ordered region.

→ The clamp of [cycles_en.md](cycles_en.md) and the distribution representation close into one root.

## 7. The canonical rung — the official level ICC freezes

**rung** = a step on the fidelity ladder. The **canonical rung** = the **official standard fidelity level** ICC
declares it "freezes every boundary at, for release." Two forces pull: **self-contained citation** (a low rung —
reproducible from the release alone) vs **fidelity** (a high rung — the joint needs the whole set / re-runs).

Tentative direction (not a decision): **the boundary record's canonical = L2 (decomposed budget) + optionally L3
(shape)** — self-contained and citable. **The joint structure (L4) lives not on the boundary but on the
[release layer](versioning-global-vs-per-boundary_en.md)** as shared-component tags / sparse covariance,
reconstructed when durations are computed. (Most boundary pairs are uncorrelated, so sparse, not N×N.)

## 8. Reflected in the schema

`age.uncertainty` goes from a single `plus_minus` → a **structured distribution**:

```yaml
uncertainty:
  fidelity: exact | sym | decomposed | shape | joint | full
  sigma: 1 | 2                 # confidence level of the budget values
  budget: { analytical, systematic, model }   # decomposed budget; shared systematic = covariance key
  shape: { median, hpd95: [lo, hi] }?          # asymmetry/skew (symmetric assumed if absent)
  shared_components: [node_ref]                # shared systematic nodes (joint reconstruction)
  posterior_ref: sample_ref | model_ref?       # L5: samples / re-runnable model
  note: string?
# a decreed value (GSSA/pin) = { fidelity: exact } (point mass). ICC canonical rung ≈ L2/L3;
# the joint structure (L4) is kept on the release layer as shared-component tags.
```

## 9. Remaining open questions

- **Whether to carry model-to-model multimodality in the distribution or in the selection layer** (within-model
  error = distribution / between-model = the competing-models envelope; keeping them separate is cleaner).
- **Storage/versioning of posterior samples** (heavy → reference, do not embed).
- **Graceful degradation of legacy `± 2σ`-only data** (to L1).
- **Accuracy of sparse covariance reconstruction** — are shared-component tags alone enough.

## 10. Links

- [boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) §2 (`age.uncertainty`) · §4
- [coherence-gate_en.md](coherence-gate_en.md) — L2 covariance (= decomposed budget) · [cycles_en.md](cycles_en.md) — joint-inference joint · clamp = distribution operator
- [competing-models_en.md](competing-models_en.md) — model-to-model envelope (multimodal) · [node-graph-paradigm_en.md](node-graph-paradigm_en.md) — edge = distribution

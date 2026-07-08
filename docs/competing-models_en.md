# How Competing Models Coexist

*English · [한국어](competing-models.md)*

> Status: **Analysis note → partly reflected in the schema.** An expansion of the "how competing models coexist"
> item in [boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) §4. The head-on case of the node-graph
> document's **"node swap = what-if."** → ModelCandidate·selection·override **implemented** (P05.5); envelope/BMA not yet started (P06.5).

## 1. First, decompose "competing model"

Don't lump it into one word. The grain of competition differs by level:

| What differs | Example | In the graph |
|---|---|---|
| **Method** | spline vs Bayesian age-depth | same wiring, swap the node |
| **Input set** | include/exclude a disputed ash bed; Oman vs Namibia anchor | add/remove edges |
| **Correlation hypothesis (wiring)** | BACE placement → Bowyer 2022 model A/B vs C/D | **topology difference** |
| **Shared upstream node** | decay-constant / tracer version | upstream node swap (affects many boundaries at once) |
| **The data itself** | a new U-Pb | a new leaf |

Some competition is a node swap (same graph), some a wiring difference (topology diff), some an input
difference. And crucially the **scope** differs (per-boundary vs global) — see §5.

## 2. The two options are a false binary

§4's (a) `chosen + alternatives` in one record vs (b) each model an independent candidate — this is the same
**gateway/network two-layer structure** we already have:

- **Competing models live in the *free network between* gateways.** Each model is a process node wired to the
  same inputs and the same boundary-position node — exactly the node-graph document's "alternative graph
  branches." → **They coexist in plurality, each with full provenance** (the substance of option b).
- **The gateway (= the frozen boundary record) *selects* one and pins it.** → a single number (the substance of
  option a).

So the answer is not "either/or" but **plural in the network, selected at the gateway/release**. `chosen` should
not be a field that holds data but a **pointer to a candidate node**. Flattening alternatives into footnotes in
the record loses their provenance and makes "changing the winner" awkward.

## 3. The selection attaches to the *release*, not the record

The point where this joins the versioning note. The global release manifest already pins "model choices":

- **Model candidates** = independently addressable objects (plural, each with citation, provenance, output value).
- **Each release** (ICC-2024/12, a sandbox branch) carries a `{boundary → which candidate}` **selection mapping**.
- **The "official value" is derived:** `release.selection[boundary] → candidate → its output value`.

**Sandbox = baseline + selection override** ("use ICC-2024/12 but base-cambrian → model D"). So resolving
competition is not a permanent property of the record but a **per-release binding** — "continuous deployment
applied to model choice." Candidates accrue continuously via CI; only the ratified selection updates periodically.

## 4. Uncertainty — again ICC/GTS splits here

Competing models differ not only in point value but represent **model (epistemic) uncertainty** — a layer
distinct from measurement uncertainty. Two treatments:

- **Select one:** one model's value ± its internal error. Clean, but hides disagreement and **understates** ±.
- **Model averaging / envelope:** combine competing models (BMA) / report a range. Honest, but yields a value no
  single model endorses + the **who sets the weights** problem.

Same axis as the coherence gate's validate/reconcile fork:

- **ICC = bake = select.** Authority needs a single number.
- **GTS = narrate = keep the plurality.** Narrate model A/B/C/D, the envelope, the disagreement.

## 5. The twist: some models set not one boundary but *many*

Bowyer 2022's global δ¹³C age model A–D sets not just base-Cambrian but several neighboring Ediacaran–Cambrian
boundaries **at once**. So candidates come in two kinds:

- **Per-boundary (local) candidate** — one boundary's age-depth model.
- **Global candidate** — a model that sets many boundaries jointly.

**A global candidate is internally coherent by construction** (one model produces its boundaries consistently).
Conversely, picking boundaries one at a time from different global models (base-Cambrian from model A + a
neighbor from model C) is exactly where coherence breaks. → **Model selection and the
[coherence gate](coherence-gate_en.md) are two faces of one coin: a coherent selection = drawing from a
consistent set of models.**

## 6. What was reflected in the schema

[boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) §2 was adjusted:

- `age.age_model = {chosen, alternatives[]}` embedded → **`age.model_ref`** (a pointer to the selected
  candidate). `value_ma` is a **baked copy** of that candidate's output.
- **`ModelCandidate`** added as an independent object: `id/version`, `scope: boundary|global`, `sets` (the
  boundaries it sets, if global), `kind`, `inputs`, `correlation_via`, `output`, `provenance_ref`.
- The authoritative binding lives in the **release manifest's `selection`** (owned by the release, not the
  boundary record).

## 7. Remaining open questions

- **Candidate curation:** anyone can add a model node in a sandbox. What/who is the gatekeeper for the candidate
  set the ICC considers.
- **Model identity/versioning:** a model = code + config + inputs. Is a re-run with changed inputs a new
  candidate or a new version of the same one.
- **Envelope weights:** if model averaging is used, who sets the weights and how.
- **Combinatorial explosion:** N boundaries × M candidates × coherence constraints. Is it manageable given that
  most boundaries have only one candidate.
- **Partial adoption of a global candidate:** how to keep coherence when accepting only some of a global model's
  boundaries.

## 8. Links

- [boundary-gateway-schema_en.md](boundary-gateway-schema_en.md) §2 (`ModelCandidate` · `age.model_ref`) · §4
- [versioning-global-vs-per-boundary_en.md](versioning-global-vs-per-boundary_en.md) — release selection/manifest
- [coherence-gate_en.md](coherence-gate_en.md) — how global candidates interlock with coherence
- [node-graph-paradigm_en.md](node-graph-paradigm_en.md) — node swap = what-if · alternative graph branches
- Case: [case-cambrian-base-correlation_en.md](case-cambrian-base-correlation_en.md) (models A–D)

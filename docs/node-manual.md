# 노드 매뉴얼 — cdGTS

<!-- 생성된 문서입니다. 손으로 고치지 마세요 — `manage.py node_manual` 이 덮어씁니다.
     산문을 고치려면 seed/02_nodes.json 의 description/params_schema.help 또는 engine/kernels.py 의
     커널 docstring 을 고치고 재생성하세요. -->

> **자동 생성** (`manage.py node_manual`) — 시드(NodeType·Port·params_schema) × 커널 코드 × 실제 사용처를 조립.
> 목적: 어떤 노드가 무슨 기능을 갖는지 한눈에 보고 **무엇이 정말 필요한지·무엇이 더 필요한지** 판단하기 위한 것.
> 개념 지도는 [concept-map](concept-map.md) · 카테고리 모델은 [tier-category-model](tier-category-model.md).

> 생성: 2026-07-15 · NodeType **17** 개 · 사용 중 **13** 개 · **미사용 4** 개

## 요약

| 노드 | 카테고리 | 커널 | 포트 (in → out) | 인스턴스 |
|---|---|---|---|---|
| `order` | clamp | `order_check` | younger, older → — | — **미사용** |
| `astronomical` | data | `(leaf)` | — → age | — **미사용** |
| `biostratigraphic` | data | `(leaf)` | section → datum | **2** |
| `calibration-constant` | data | `calibration_constant` | — → value | **1** |
| `horizon` | data | `(leaf)` | section → out | **6** |
| `magnetostratigraphic` | data | `(leaf)` | — → reversals | — **미사용** |
| `published-age` | data | `(leaf)` | — → out, older, younger | **117** |
| `radiometric-uPb` | data | `radiometric_age` | section, calibration → age | **20** |
| `section` | data | `(leaf)` | — → h1, h2, h3 | **8** |
| `age-depth-model` | process | `age_depth_model` | dated_horizons → horizon_age, older, younger | **8** |
| `boundary` | process | `(pass-through + fallback)` | age → out, older, younger | **7** |
| `calibration-transfer` | process | `(pass-through)` | reference, target → calibrated | **2** |
| `cross-section-correlation` | process | `cross-section-correlation` | signals, anchors → correlated_age | **2** |
| `joint-inference` | process | `joint-inference` | constraints → estimates | — **미사용** |
| `merge` | process | `(pass-through)` | parts → out | **18** |
| `unit` | process | `(pass-through)` | — → older, younger, out | **118** |
| `reference` | reference | `(pass-through)` | — → citation | **8** |

> ⚠️ **어떤 그래프도 쓰지 않는 타입**: `order`, `astronomical`, `magnetostratigraphic`, `joint-inference`. 의도된 여지인지, 정리 대상인지 검토 필요.

## data

> 관측·저작된 값이 들어오는 leaf. 커널 없이 `params.distribution` 을 방출하는 것이 기본 (`calibration-constant`·`radiometric-uPb` 만 예외 — 공유 계통원 태그를 실어 방출).

### `astronomical`

Astronomically tuned age (immutable · leaf).

- **커널**: `(leaf)`
  - 데이터 leaf — 커널 없음. 저작된 `params.distribution` 을 그대로 방출한다.
- **사용**: ⚠️ **없음** (어떤 그래프도 이 타입을 쓰지 않는다)
- **포트**:
  - `age` (out, distribution)
- **파라미터**:
  - `distribution` (distribution) — Tuned age from the astronomical solution (authored leaf — cdGTS trusts the published value; the tuning itself is not modelled).
  - `depth` (number) — Stratigraphic depth/height

### `biostratigraphic`

Biostratigraphic datum (FAD/LAD) signal.

- **커널**: `(leaf)`
  - 데이터 leaf — 커널 없음. 저작된 `params.distribution` 을 그대로 방출한다.
- **사용**: 2개 인스턴스 — example-cambrian-base ×1, example-icc-partial ×1
- **포트**:
  - `section` (in, any)
  - `datum` (out, signal)

### `calibration-constant`

Shared calibration parameter (decay constant · monitor age e.g. FCs 28.201 Ma · tracer). A single upstream leaf that many radiometric ages depend on; its uncertainty is a shared systematic source. Change it → every dependent age re-computes (diff surfaces the impact); two ages sharing it get correlated durations. Emits its value tagged with a self-referencing shared_component (ref = symbol) so covariance propagates. Cite-able. NB: its `value` is the parameter itself (not a boundary age) — it feeds a rescale/joint kernel, not a boundary directly (that wiring is L1/L2, see R04).

- **커널**: `calibration_constant`
  - 공유 보정 파라미터(붕괴상수·monitor(FCs)·tracer) leaf. 저작된 분포를 방출하되, 그 불확실성 **전액을**
- **사용**: 1개 인스턴스 — demo-cov-shared ×1
- **포트**:
  - `value` (out, distribution)
- **파라미터**:
  - `distribution` (distribution) — Authored value + uncertainty of the constant. The kernel re-tags ALL of this uncertainty as a shared_component pointing at `symbol` (or `kind`), promoting the output to L4 `joint` — that tag is what makes two ages sharing this node covary.
  - `kind` (enum ∈ {monitor-age, decay-constant, tracer}) — Which calibration parameter this is
  - `symbol` (string) — Stable label used as the shared-component ref (e.g. FCs, λ238U, ET2535). Ages sharing the same symbol get correlated systematics.

### `horizon`

A stratigraphic level in a section, at a given depth (distance from section base). Carries no age of its own — an undated horizon (e.g. the boundary/correlation level marked by a δ13C excursion or fossil FAD) is the interpolation target: it feeds an age-depth model whose bracketing inputs are dated beds. Cite-able for its source.

- **커널**: `(leaf)`
  - 데이터 leaf — 커널 없음. 저작된 `params.distribution` 을 그대로 방출한다.
- **사용**: 6개 인스턴스 — example-cambrian-base ×3, example-icc-partial ×3
- **포트**:
  - `section` (in, any)
  - `out` (out, distribution)
- **파라미터**:
  - `depth` (number) — Distance from section base (a stratigraphic coordinate; higher = up-section)
  - `datum` (string) — Correlation signal at this level (e.g. δ13C BACE, T. pedum FAD)
  - `note` (string) — Free-form annotation (not read by any kernel).

### `magnetostratigraphic`

Magnetic-reversal pattern signal (for correlation).

- **커널**: `(leaf)`
  - 데이터 leaf — 커널 없음. 저작된 `params.distribution` 을 그대로 방출한다.
- **사용**: ⚠️ **없음** (어떤 그래프도 이 타입을 쓰지 않는다)
- **포트**:
  - `reversals` (out, signal)

### `published-age`

Reference leaf for published boundary ages (ICS/GTS chart). Holds the value only, no editing.

- **커널**: `(leaf)`
  - 데이터 leaf — 커널 없음. 저작된 `params.distribution` 을 그대로 방출한다.
- **사용**: 117개 인스턴스 — example-gssa-precambrian ×1, example-icc-partial ×116
- **포트**:
  - `out` (out, distribution)
  - `older` (out, distribution)
  - `younger` (out, distribution)
- **파라미터**:
  - `distribution` (distribution) — The published age as authored (leaf). Also how a GSSA is expressed — an `exact` point mass IS the definition, not a measurement (clamp scope-down, cycles §12).

### `radiometric-uPb`

U–Pb radiometric age observation (immutable · cited · leaf). Optionally wire shared calibration-constant node(s) into its `calibration` port: each folds its systematic σ into this age's budget AND tags it as a shared_component, so two ages sharing the same constant get correlated durations (value unchanged — covariance wiring, not recompute; R04 L1).

- **커널**: `radiometric_age`
  - U-Pb 방사연대 leaf. 자기 authored 연대(분석오차만)를 방출하되, `calibration` 포트로 들어온 공유 보정
- **사용**: 20개 인스턴스 — demo-cov-independent ×2, demo-cov-shared ×2, example-cambrian-base ×6, example-icc-partial ×8, example-permian-triassic ×2
- **포트**:
  - `section` (in, any)
  - `calibration` (in, distribution · multiple)
  - `age` (out, distribution)
- **파라미터**:
  - `distribution` (distribution) — Interpreted age as published (leaf — cdGTS trusts it; grain-level provenance stays in the cited paper, R04). `budget.analytical` = internal error; wiring a `calibration` input adds its σ to `budget.systematic` (= external) without changing the value.
  - `depth` (number) — Stratigraphic depth/height (for age–depth)

### `section`

A measured stratigraphic section at a locality. Emits its horizons (up to 3: h1/h2/h3). Cite-able: a reference node describing the section wires to its cited handle, so section-level provenance has a home. The h* edges are structural (carry no value) but keep the section in the boundary's data-flow cone so its references propagate to the bibliography.

- **커널**: `(leaf)`
  - 데이터 leaf — 커널 없음. 저작된 `params.distribution` 을 그대로 방출한다.
- **사용**: 8개 인스턴스 — example-cambrian-base ×4, example-icc-partial ×4
- **포트**:
  - `h1` (out, any)
  - `h2` (out, any)
  - `h3` (out, any)
- **파라미터**:
  - `locality` (string) — Section name / locality (e.g. Ara Group, Oman)
  - `region` (string) — Country / region
  - `note` (string) — Free-form annotation (not read by any kernel).

## process

> 상류 분포를 받아 계산하는 노드. 커널이 없으면 pass-through(= 의미론적/구조적 노드).

### `age-depth-model`

Age–depth interpolation within one section (local). Age at target_depth from dated_horizons (each depth+age).

- **커널**: `age_depth_model`
  - dated horizon((depth, age) 들)에서 target_depth 의 연대를 보간. depth 는 상류 노드 params["depth"].
- **사용**: 8개 인스턴스 — example-cambrian-base ×3, example-icc-partial ×4, example-permian-triassic ×1
- **포트**:
  - `dated_horizons` (in, distribution · multiple)
  - `horizon_age` (out, distribution)
  - `older` (out, distribution)
  - `younger` (out, distribution)
- **파라미터**:
  - `method` (enum ∈ {linear, spline}) — `linear` (default) = analytic two-point interpolation. `spline` = cubic interpolating spline + 3000-draw MC, and needs ≥3 dated horizons or it silently falls back to linear. NOTE: it is an *interpolating* spline — no smoothing factor, no cross-validation, no monotonicity constraint (R05 §2); nothing currently seeded uses `spline`.
  - `target_depth` (number) — Horizon to interpolate (e.g. GSSP level)

### `boundary`

Boundary point (0-cell). Receives the age from an upstream computation (data/process) as input and displays it. Shared by multiple units.

- **커널**: `(pass-through + fallback)`
  - 경계 점 — 상류가 준 연대를 통과. 입력이 없으면 자기 `params.distribution`(공표값) 으로 폴백.
- **사용**: 7개 인스턴스 — demo-cov-independent ×2, demo-cov-shared ×2, example-icc-partial ×3
- **포트**:
  - `age` (in, distribution)
  - `out` (out, distribution)
  - `older` (out, distribution)
  - `younger` (out, distribution)
- **파라미터**:
  - `distribution` (distribution) — Fallback age used ONLY when nothing is wired to the `age` port. With an upstream input this is ignored — the boundary passes the computed age through.

### `calibration-transfer`

Transfers a reference age onto a target signal.

- **커널**: `(pass-through)`
  - 커널 **미등록** → 첫 non-null 입력을 그대로 통과시킨다. 계산 노드가 아니라 의미론적/구조적 노드.
- **사용**: 2개 인스턴스 — example-cambrian-base ×1, example-icc-partial ×1
- **포트**:
  - `reference` (in, distribution)
  - `target` (in, signal)
  - `calibrated` (out, distribution)

### `cross-section-correlation`

Synthesis of cross-section correlations (load-bearing).

- **커널**: `cross-section-correlation`
  - `joint-inference` 와 **동일 커널**(note 문자열만 다름). 섹션별 연대를 역분산 평균한다. ⚠️ 상관 자체는 계산하지 않고(δ13C 는 읽히지 않는 문자열) 저자의 배선 주장을 받는다. 분산 검정(MSWD/χ²) 없음 — 불일치해도 조용히 평균된다. R05 는 이 타입의 **소멸**을 권고.
- **사용**: 2개 인스턴스 — example-cambrian-base ×1, example-icc-partial ×1
- **포트**:
  - `signals` (in, signal · multiple)
  - `anchors` (in, distribution · multiple)
  - `correlated_age` (out, distribution)
- **파라미터**:
  - `correlation_via` (multi-enum ∈ {d13C, Sr-isotope, biostratigraphy}) — ⚠️ ANNOTATION ONLY — no kernel reads this, and values are not validated against `choices` (instances carry `d13C-BACE`, which is not in the list). The correlation is asserted by the author's wiring, not computed. R05 proposes replacing this with first-class `tie-point` nodes.

### `joint-inference`

Locally co-constrained joint estimation — the node that folds cycles (cycles §).

- **커널**: `joint-inference`
  - 역분산(정밀도) 가중 결합 — 같은 양의 **독립** 추정들을 합쳐 σ 를 줄인다. exact 입력이 있으면 그것이 지배(pin).
- **사용**: ⚠️ **없음** (어떤 그래프도 이 타입을 쓰지 않는다)
- **포트**:
  - `constraints` (in, any · multiple)
  - `estimates` (out, distribution · multiple)

### `merge`

terminal geometry merge — 모든 boundary/time-period 조각을 union 해 ICC 차트를 구성. 순서 무관(배열은 order 엣지·연대가 결정).

- **커널**: `(pass-through)`
  - 커널 **미등록** → 첫 non-null 입력을 그대로 통과시킨다. 계산 노드가 아니라 의미론적/구조적 노드.
- **사용**: 18개 인스턴스 — example-icc-partial ×18
- **포트**:
  - `parts` (in, distribution · multiple)
  - `out` (out, distribution)

### `unit`

Time unit (1-cell, span). Represents an unsubdivided interval as a single node — sits between its lower/upper boundaries. Holds no value (boundaries carry the ages).

- **커널**: `(pass-through)`
  - 커널 **미등록** → 첫 non-null 입력을 그대로 통과시킨다. 계산 노드가 아니라 의미론적/구조적 노드.
- **사용**: 118개 인스턴스 — demo-cov-independent ×1, demo-cov-shared ×1, example-icc-partial ×116
- **포트**:
  - `older` (out, distribution)
  - `younger` (out, distribution)
  - `out` (out, distribution)

## clamp

> 값을 만들지 않고 **검사**하는 노드. clamp 축소(cycles §12) 이후 `order` 만 남았다.

### `order`

Checks temporal order of two boundaries (bottom=older ≥ top=younger + Δ). Check only · value unchanged.

- **커널**: `order_check`
  - 두 경계의 시간적 선후 **검사**(값 불변). 포트 older(아래·큰 Ma) / younger(위·작은 Ma).
- **사용**: ⚠️ **없음** (어떤 그래프도 이 타입을 쓰지 않는다)
- **포트**:
  - `younger` (in, distribution)
  - `older` (in, distribution)
- **파라미터**:
  - `min_gap` (number) — Minimum duration Δ (Ma). 0 = plain ordering.
  - `mode` (enum ∈ {hard, warn}) — hard = FAIL on violation · warn = warning

## reference

> 인용 provenance. `cite` 엣지로 데이터/모델 노드를 가리킨다(값을 나르지 않는다).

### `reference`

A bibliographic source (DOI-centric) for a data/model node. Wire its citation port to the node it sources with a cite edge; a bake can walk cite edges to collect the bibliography.

- **커널**: `(pass-through)`
  - 커널 **미등록** → 첫 non-null 입력을 그대로 통과시킨다. 계산 노드가 아니라 의미론적/구조적 노드.
- **사용**: 8개 인스턴스 — example-cambrian-base ×4, example-icc-partial ×4
- **포트**:
  - `citation` (out, any · multiple)
- **파라미터**:
  - `reference` (reference) — Natural key of the `references.Reference` row (DOI registry). This node cites data/model nodes via non-data `cite` edges, making provenance a first-class citizen of the graph (devlog 127).

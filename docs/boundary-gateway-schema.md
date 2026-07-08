# 경계 게이트웨이 스키마 초안 (Boundary Gateway Schema — Draft)

*[English](boundary-gateway-schema_en.md) · 한국어*

> **[대체됨 / 역사 보관]** 이 단일 게이트웨이 YAML 스키마는 구현의 **조상**일 뿐 현행이 아니다. 실제 구현은 경계를
> 하나의 게이트웨이 레코드가 아니라 그래프의 **`boundary` 노드 + `published-age` leaf + `order` edge**로 표현하고,
> 릴리스/clamp/provenance 는 `releases`·`graph` 앱 모델에 있다. 현행: [app-architecture.md](app-architecture.md) ·
> [boundary-span-duality.md](boundary-span-duality.md) · `releases/models.py`. (아래는 역사적 브레인스토밍.)

> 상태: **초안 v0.** 브레인스토밍을 처음으로 구체 구조로 굳혀보는 시도. 확정 아님.
> 세 케이스([P–T](case-permian-triassic.md), [선캄브리아 GSSA](case-precambrian-gssa.md),
> [캄브리아 base](case-cambrian-base-correlation.md))에서 뽑은 요구사항을 하나의 스키마로 모은 것.
> 아래 표기는 **예시(YAML)** 일 뿐이며 직렬화 포맷은 미정.

## 1. 설계 원칙 (세 케이스에서 나온 요구사항)

1. **다형(polymorphic).** 경계 숫자의 출처가 셋 — 계산된 분포(GSSP·국소 보간), 결정된 상수(GSSA),
   상관 종합(GSSP·섹션 간). 하나의 스키마가 셋 다 담아야 한다.
2. **위치와 연대의 분리.** GSSP는 *어디/무엇*(마커·노두)만 고정하고 *언제*(숫자)는 별도 서브그래프가 댄다.
   두 필드를 뭉치지 않는다. (GSSA만 예외 — 노두가 없고 숫자가 곧 정의.)
3. **provenance는 그래프 참조.** 숫자를 인라인으로 복제하지 않고 노드 그래프의 서브그래프를 가리킨다.
   이 서브그래프는 **지리적으로 분산**될 수 있다(캄브리아: 캐나다+오만+나미비아+시베리아).
4. **age model이 1급 필드.** 어떤 모델이 이 숫자를 냈는지 + **경쟁 대안**을 함께 기록.
5. **게이트웨이 = 버전·인용·비준의 단위(계약).** 릴리스마다 얼린 스냅샷. 정의 타입(GSSP/GSSA)조차
   버전 간 바뀔 수 있다(토폴로지 재배선).

## 2. 스키마 (주석 달린 예시 표기)

두 축이 각각 독립적으로 다형이다:

- `definition.type`: **GSSP | GSSA** — *어디/무엇* (위치)
- `age.method`: **decreed | local-interpolation | cross-section-correlation** — *어떻게 나온 숫자*

> 커플링: `GSSA ⇒ age.method = decreed`. `GSSP ⇒ age.method ∈ {local-interpolation, cross-section-correlation}`.

```yaml
BoundaryGateway:
  id: string                     # 안정적 슬러그. 예: base-triassic
  version: string                # 이 레코드가 속한 릴리스. 예: ICC-2024/12

  identity:                      # Layer 0 — 명명/계층 연결
    separates:
      below: unit_ref            # 아래 단위 (이중 명명 참조)
      above: unit_ref            # 위 단위
    # unit_ref는 각자 연대층서(System/Series/Stage) ↔ 지질연대(Period/Epoch/Age) 이름을 보유
    lineage:                     # 버전 간 정체성 계보 (토폴로지 diff의 전제)
      op: created | renamed | split | merged | retyped | deprecated
      from: [boundary_id]        # split/merge의 원본(들), rename의 이전 id

  definition:                    # 위치 — "어디/무엇" (Layer 1)
    type: GSSP | GSSA
    ratified: { year: int, by: authority }
    # --- type == GSSP 일 때 ---
    marker:                      # 경계를 정의하는 사건
      kind: biostratigraphic | chemostratigraphic | magnetostratigraphic | ...
      event: FAD | LAD | excursion | reversal | ...
      taxon_or_signal: string    # 예: "Hindeodus parvus"
    stratotype:
      locality: string           # 예: "Meishan D, Changxing, Zhejiang, China"
      coordinates: [lat, lon]
      level: string              # 예: "base of Bed 27c"
    # --- type == GSSA 일 때 ---
    decreed_age_ma: number       # 이 숫자가 곧 정의 (노두 없음)
    rationale: string            # 예: "round-number convention"

  age:                           # 연대 — "언제" (Layer 3–5의 산출)
    value_ma: number
    uncertainty:                 # 구조화된 분포 (충실도 사다리 L0–L5). GSSA = { fidelity: exact }
      fidelity: exact | sym | decomposed | shape | joint | full
      sigma: 1 | 2               # budget 값의 신뢰수준
      budget: { analytical, systematic, model }   # 분해 예산; 계통 공유 = 공분산 열쇠
      shape: { median, hpd95: [lo, hi] }?          # 비대칭/왜곡 (없으면 대칭 가정)
      shared_components: [node_ref]                # 공유 계통 노드 (joint 재구성)
      posterior_ref: sample_ref | model_ref?       # L5: 샘플 / 재실행 모델
      note: string?
    method: decreed | local-interpolation | cross-section-correlation
    model_ref: model_candidate_ref  # 이 릴리스가 *선택*한 모델 후보. 권위 바인딩은
                                    # 릴리스 매니페스트의 selection. value_ma는 그 후보 출력의 bake 사본.
    provenance_ref: graph_ref    # 선택된 후보가 값을 내는 서브그래프. 지리적으로 분산 가능.

  status:
    level: ratified | proposed | sandbox | deprecated
    authority: ICS | sandbox-branch:<id> | fork:<user>
    supersedes: version?         # 이전 버전 레코드

  narrative_ref: doc_ref?        # bake(이 레코드)의 짝 — GTS식 서술(narrate)
```

경쟁 모델은 게이트웨이 *사이 네트워크*에 복수로 공존한다. 각 후보는 **독립 객체**이고, 릴리스가 그중 하나를
선택(`model_ref`)한다. 상세: [competing-models.md](competing-models.md).

```yaml
ModelCandidate:                  # 네트워크에 공존하는 경쟁 후보 (독립 주소지정)
  id: string                     # 예: base-cambrian/bowyer2022-modelA
  version: string
  scope: boundary | global       # global이면 다수 경계를 한꺼번에 정함 → 그 자체로 내부 정합
  sets: [boundary_id]            # (scope=global) 이 후보가 정하는 경계들
  kind: string                   # bayesian-age-depth, global-d13C-age-model, committee-decision …
  inputs: [node_ref]             # 기여 관측/앵커 노드
  correlation_via: [string]      # (섹션 간) BACE, Sr 동위원소 …
  output:                        # 후보가 내는 값(들)
    { boundary_id: { value_ma, uncertainty } }
  provenance_ref: graph_ref

# 릴리스가 selection을 소유한다 (경계 레코드가 아니라):
Release:
  version: string                # 예: ICC-2024/12
  selection: { boundary_id: model_candidate_ref }   # 정합한 선택 = 일관된(가급적 같은 global) 후보에서 뽑기
  clamps: [clamp_ref]            # 이 릴리스가 적용하는 authored clamp들

# Clamp — subcommission이 네트워크 *안*에 꽂는 거버넌스 게이트웨이 (사이클 절단·권위 고정)
Clamp:
  id: string
  owner: string                  # 예: ICS Cambrian Subcommission
  target: node_ref | boundary_id # 무엇을 고정하나
  kind: pin | range | order | freeze-version
  value_or_bound: any            # pin=값, range=[min,max], order=이웃 참조, freeze-version=버전
  rationale: string
  ratified: { year: int, by: authority }
  overridable_in_sandbox: bool   # 샌드박스 what-if에서 제거 가능?
# 주: GSSA = Clamp{kind: pin} 의 특수 사례 (definition.type=GSSA 와 한 뿌리).
# 주: provenance 엣지엔 type(co-location | calibration-transfer)이 붙어 게이트가 사이클을 탐지한다.
```

## 3. 세 케이스 적용

### A. P–T 경계 — GSSP · 국소 보간

```yaml
id: base-triassic
version: ICC-2024/12
identity:
  separates: { below: changhsingian-stage, above: induan-stage }
definition:
  type: GSSP
  ratified: { year: 2001, by: ICS }
  marker: { kind: biostratigraphic, event: FAD, taxon_or_signal: "Hindeodus parvus" }
  stratotype:
    locality: "Meishan D, Changxing, Zhejiang, China"
    level: "base of Bed 27c"
age:
  value_ma: 251.902
  uncertainty:
    fidelity: decomposed
    sigma: 2
    budget: { analytical: 0.024 }          # +tracer/+decay 계통은 출처 참조
    shared_components: [earthtime-tracer, u-decay-const]
  method: local-interpolation
  model_ref: "base-triassic/burgess2014"   # 선택된 후보 (아래 ModelCandidate)
  provenance_ref: "graph://base-triassic/age@Burgess2014"
status: { level: ratified, authority: ICS }
```

### B. Archean–Proterozoic 경계 — GSSA · 결정

```yaml
id: base-proterozoic
version: ICC-2024/12
definition:
  type: GSSA
  ratified: { year: 1991, by: ICS }
  decreed_age_ma: 2500
  rationale: "round-number convention; 물리적 stratotype 없음"
age:
  value_ma: 2500
  uncertainty: { fidelity: exact }                 # 점질량 δ(2500)
  method: decreed
  model_ref: "base-proterozoic/decree"     # 후보 = 위원회 결정
  provenance_ref: "decision://ICS/precambrian-subcommission"
status: { level: ratified, authority: ICS }
# 주: definition.type 이력상 현재 GSSA. 다른 선캄 경계(Ediacaran)는 이미 GSSP로 재배선됨.
```

### C. 캄브리아기 base — GSSP · 섹션 간 상관

```yaml
id: base-cambrian
version: ICC-2024/12
identity:
  separates: { below: ediacaran-system, above: fortunian-stage }
definition:
  type: GSSP
  ratified: { year: 1992, by: ICS }
  marker: { kind: biostratigraphic, event: FAD, taxon_or_signal: "Treptichnus pedum" }
  stratotype:
    locality: "Fortune Head, Burin Peninsula, Newfoundland, Canada"
    level: "23 m above base of Member 2A (Quaco Road Mbr), Chapel Island Fm"
age:
  value_ma: 538.8
  uncertainty:
    fidelity: decomposed
    sigma: 2
    budget: { analytical: 0.6 }
    note: "contested; 모델 간 ~536까지 → 다봉은 competing-models 층"
  method: cross-section-correlation
  model_ref: "ediacaran-cambrian/bowyer2022-modelAB"   # 선택된 후보 (scope=global)
  provenance_ref: "graph://base-cambrian/age"   # 캐나다(위치) + 오만·나미비아·시베리아(앵커)
status: { level: ratified, authority: ICS }

# 경쟁 후보들 — 네트워크에 공존하고, 릴리스가 그중 하나를 선택:
- id: "ediacaran-cambrian/bowyer2022-modelAB"
  scope: global
  sets: [base-cambrian, base-fortunian, …]     # 여러 경계를 한꺼번에 → 내부 정합
  kind: global-d13C-age-model
  inputs: [oman-ara-uPb, namibia-uPb, siberia-uPb]
  correlation_via: [BACE-d13C, Sr-isotope-stratigraphy]
  output: { base-cambrian: { value_ma: 538.8, uncertainty: { plus_minus: 0.6, sigma: 2 } } }
- id: "ediacaran-cambrian/bowyer2022-modelD"
  scope: global
  kind: global-d13C-age-model
  output: { base-cambrian: { value_ma: ~536, uncertainty: { note: "~3 Myr younger" } } }
```

세 예시가 두 다형 축을 구체화한다: **위치(GSSP/GSSA)** 와 **숫자 출처(decreed/보간/상관)** 가
서로 다른 조합으로 나타나고, `age.provenance_ref` 는 세 경우 모두 **얼린 값 뒤의 살아있는 서브그래프**를 가리킨다.

## 4. 열린 설계 질문

- **전역 vs 경계별 버전.** 이 초안은 경계별 독립 버전을 가정(각 레코드가 자기 `version`). ICC 전체 릴리스와
  어떻게 묶을지(릴리스 = 경계 레코드들의 스냅샷 집합?).
  → 별도 검토: [versioning-global-vs-per-boundary.md](versioning-global-vs-per-boundary.md).
- **분포 표현.** → **정리됨**: `uncertainty`를 충실도 사다리(L0–L5)로 구조화 — 분해 예산(=공분산 열쇠) +
  모양 + 공유성분 태그 + 사후 참조. GSSA = `fidelity: exact`(점질량). ICC 정본 rung ≈ L2/L3, joint(L4)는
  릴리스 층. 상세: [distribution-representation.md](distribution-representation.md).
- **경쟁 모델 공존 방식.** → **정리됨**: 후보는 네트워크에 복수 공존(`ModelCandidate` 독립 객체), 릴리스가
  `selection`으로 하나를 바인딩. 위 §2의 `age.model_ref`·`ModelCandidate`·`Release`에 반영. 상세:
  [competing-models.md](competing-models.md).
- **토폴로지 diff.** → **정리됨**: 값 diff와 직교하는 별도 축. 안정 id + `identity.lineage`(split/merge/retype
  선언)로 정렬하고, edit-script / 2색 합집합그래프 / changelog로 표기. 상세: [topology-diff.md](topology-diff.md).
- **순환.** → **정리됨**: 국소 상호제약은 joint-inference 노드로 접고, 전역 보정 되먹임은 버전 나선 +
  subcommission의 `Clamp`로 절단. 위 §2의 `Clamp`·`Release.clamps`에 반영. 상세: [cycles.md](cycles.md).

## 5. 링크

- [idea.md](idea.md) §5(레이어)·§8(게이트웨이) — 개념 배경
- [node-graph-paradigm.md](node-graph-paradigm.md) — 게이트웨이/노드 네트워크
- 케이스: [P–T](case-permian-triassic.md) · [선캄브리아 GSSA](case-precambrian-gssa.md) · [캄브리아 base](case-cambrian-base-correlation.md)

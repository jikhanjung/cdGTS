# cdGTS — Continuously Deployed Geologic Time Scale

*[English](idea_en.md) · 한국어*

> 상태: 초기 브레인스토밍. 아직 확정된 것은 없음. 아이디어를 던지고 굴려보는 공간.

## 1. 배경

- **ICS (International Commission on Stratigraphy)** 는 **International Chronostratigraphic Chart (ICC)** 를 발행한다. 지질시대 경계(GSSP)와 그 연대에 대한 현재까지의 공식 합의를 보여주며, 부정기적으로 개정판이 나온다 (예: v2023/09, v2024/12 …).
- 더 상세한 참조 저작으로 **GTS2020 (*Geologic Time Scale 2020*, Gradstein et al.)** 이 있었다. 방사성동위원소·천문연대(astrochronology) 보정까지 담는다.
- 현재 **GTS2030** 이 준비 중.

## 2. 문제의식

지질시대표가 ~10년 주기의 "책 / 대형 릴리스"로만 발행된다. 그 사이에 쌓이는 새로운 연대측정 데이터는 다음 대형 릴리스까지 공식적으로 반영되기 어렵다.

## 3. 핵심 아이디어

지질시대표를 **소프트웨어처럼 다루자.**

- **표(table)가 아니라 계산의 산출물(computed artifact)** 로 취급한다: 원시 데이터 → 모델 → 경계 연대가 **재현 가능한 파이프라인**으로 연결된다.
- **버전 관리 + 지속적 배포(continuous deployment)**: 정기적으로 검증된 **fixed version** 을 릴리스하되,
- **테스트/샌드박스 환경**을 함께 제공한다. 학자들이 새로 얻은 데이터를 **continuously integrate** 해보고, 그것이 경계 연대에 미치는 영향을 즉시 확인할 수 있게 한다 — 일종의 **"과학을 위한 CI"**.

## 4. 범위 (Scope)

- 데이터 저장소 / 스키마 **그리고** 조회·시각화 도구까지 **모두 포함**.

## 5. 데이터 모델 — 계층 구조 (초안)

데이터를 다음 계층으로 나눈다. 상위 계층은 하위 계층으로부터 파생된다.

> 참고: 이 계층 구조는 [node-graph-paradigm.md](node-graph-paradigm.md)에서 **노드 그래프(DAG)** 로 재해석된다. Layer 2 = 데이터 노드, Layer 3~5 = 프로세스/모델 노드, Layer 6 = 그래프 평가 결과.

### Layer 0 — 명명 / 계층 (Nomenclature)
- 이중 체계: 연대층서 (Eonothem/Erathem/System/Series/**Stage**) ↔ 지질연대 (Eon/Era/Period/Epoch/**Age**). 같은 경계를 다른 이름으로 부르는 관계이므로 명시적으로 연결.
- 명명 체계 자체도 개정 대상 (스테이지 신설/분할 등). → 버전 관리 대상.

### Layer 1 — 경계 정의 (Boundary definition)
- **GSSP** (Phanerozoic): 물리적 노두, 마커(생물/화학/자기), 위치, ICS **비준 연도**. 경계는 "지점"으로 정의되고 연대는 파생값.
- **GSSA** (Precambrian): 물리적 노두 없이 **약속된 숫자 연대**로 정의.
- → 이 둘은 데이터 모델에서 근본적으로 다른 타입.

### Layer 2 — 원시 관측 (Primary observations) ← *continuous integration의 대상*
- 방사성 연대측정 (U-Pb, Ar-Ar …): 시료, **방법, 사용한 붕괴상수, 실험실, 오차(2σ)**, 층서적 위치.
- 천문연대 (astrochronology / cyclostratigraphy), 자기층서, 생층서 존(zone) 등.
- 각 관측은 **불변(immutable) · 인용 가능(cited)** 한 "사실". 학자가 추가하는 것은 여기.

### Layer 3 — 연대 모델 (Age model / method)
- Layer 2의 앵커들을 스플라인 / 베이지안 age-depth 모델 등으로 종합해 경계 연대 + 불확실성을 **산출**.
- 붕괴상수 재보정 같은 방법 변경이 반영되는 곳.

### Layer 4 — 상관 (Correlation)
- 서로 다른 노두(section)의 층서를 bio/chemo/magneto-strat로 **상관(correlate)** 해 엮는다. GSSP 지점이 датable하지 않을 때 숫자는 다른 지역에서 이 상관을 타고 온다 → 곁다리가 아니라 **load-bearing**. 사례: [case-cambrian-base-correlation.md](case-cambrian-base-correlation.md).

### Layer 5 — 전역 종합 / 정합성 게이트 (Global synthesis / coherence gate)
- 상관된 근거를 종합해 (a) 각 경계의 숫자+불확실성을 내고, (b) 경계들이 **전 지구적으로 정합**(단조 순서·지속시간·상관오차)하도록 만든다. 이 정합성 검사의 핵심 메커니즘이 **정합성 게이트**. 상세: [coherence-gate.md](coherence-gate.md).

### Layer 6 — 배포된 시대표 (Published timescale)
- Layer 1 + 5의 산출물. Fixed version으로 릴리스 (ICC vXXXX / GTSXXXX에 대응). ICC = bake, GTS = narrate.

## 6. 워크플로우 상상 (CI for science)

1. 학자가 Layer 2에 새 관측을 PR처럼 제안.
2. 파이프라인이 Layer 3~6를 재계산.
3. **diff**를 보여준다 — 예: "이 U-Pb 하나 추가하면 Permian–Triassic 경계가 251.902 → 251.88 Ma, 2σ 축소".
4. Fixed release는 검증된 스냅샷, sandbox는 실험 브랜치. 개인 fork 시대표 허용 여부는 미정.

## 7. 열린 질문 (Open questions)

- **Layer 3(모델)의 위상**: cdGTS가 실제로 age model을 *계산*까지 하는가, 아니면 당분간 "발표된 값 + 출처 기록" 수준이고 재계산 엔진은 후속 목표인가? (프로젝트 난이도를 크게 가름.)
- **권위 vs 실험의 경계**: sandbox 결과와 공식 ICC를 어떻게 명확히 구분? 학자 개인의 "내 브랜치 시대표"를 어디까지 허용?
- 기존 포맷과의 정합: Macrostrat, GeoSciML / CGI Geologic Timescale, ICS 공식 배포 형식 등과 맞출 것인가?
- 버전 전략 구체화: git 태그 · 시맨틱 버저닝 · 자동 검증(CI)을 어떻게 매핑할 것인가?

## 8. 정련 중인 생각 — 중간 티어와 게이트웨이

> 상태: **hunch(직감) 수준. 확정 아님.** 실제 사례를 하나 붙잡고 작업해봐야 맞는 접근인지 알 수 있다. 아래는 방향 감각을 기록해두는 것.

### 8.1 중간 티어 — correlation / synthesis (§5의 Layer 4·5로 승격)

초기 모델은 Layer 3(국소 age model)에서 배포로 바로 점프했고, 그 사이에 **공간(space)과 상관(correlation)** 이 통째로 빠져 있었다. 이제 §5에서 이를 **Layer 4(correlation)·Layer 5(global synthesis)** 로 승격했다.

왜 필수인가: **GSSP는 경계를 *정의*하지만 경계의 *숫자*를 주지는 않는 경우가 많다.** golden spike 노두가 방사연대 측정이 안 되는 암상일 수 있고, 그러면 실제 숫자는 다른 지역의 datable한 층에서 나와 **correlation으로 GSSP 지점에 연결**된다. 즉 correlation은 곁다리 기능이 아니라 **숫자를 얻는 경로 자체에 실려 있는(load-bearing)** 단계.

스케일마다 성격이 다른 연산이 겹쳐 있다:

| 스케일 | 연산 | 현재 위치 |
|---|---|---|
| 단일 포인트 | 시료 하나의 연대 | Layer 2 |
| Section / 주상도 | age-depth 모델 (한 노두 안) | Layer 3 (공간적으로 국소) |
| Formation / sequence | 여러 horizon을 한 단위로 묶기 | 국소~지역 |
| **Section ↔ Section** | **상관 (bio/chemo/magneto-strat tie)** | 이제 **Layer 4** |
| 전 지구 | 같은 경계의 여러 근거를 풀링 → 숫자+불확실성 | 이제 **Layer 5** |

→ **§5에서 정수 레이어로 승격: Layer 4 (correlation), Layer 5 (global synthesis / 정합성 게이트).**

주의: correlation 자체가 불확실성을 가진 추론(확률적 매칭)이며, [node-graph-paradigm.md](node-graph-paradigm.md)의 **순환 의존성**(생층서 ↔ 방사연대 상호 보정)이 정확히 이 티어 안에서 터진다. node-graph 문서엔 이미 "correlation 노드 / node group"으로 이 공간 차원이 들어와 있는데, **이 레이어 모델(idea.md)은 아직 그걸 반영하지 못하고 있다** — 두 문서를 맞춰야 한다.

### 8.2 레이어를 "단계"가 아니라 "게이트웨이(계약)"로

더 큰 재해석: 레이어를 고정된 순차 단계로 못 박지 말고, **중간중간 게이트웨이 레이어**(합의된 고정 타입·버전·인용의 단위)만 두고 **그 사이는 자유로운 노드 네트워크**로 채운다. 지저분한 과학(순환·대안 모델·몬테카를로·correlation)은 게이트웨이 *사이*에 가두고, 게이트웨이 자체는 깨끗하게 유지하며 릴리스한다.

자세한 전개는 [node-graph-paradigm.md](node-graph-paradigm.md)의 **"게이트웨이 레이어"** 절 참조.

> **구현 후 회고:** 실제 구현에서 이 재해석이 어떻게 굳었는지 — L0~6이 **티어(registry/graph/release) × 카테고리(data/process/clamp)** 로 분해된 과정 — 는 [tier-category-model.md](tier-category-model.md) 참조.

### 8.3 이에 따라 늘어나는 열린 질문

- correlation / synthesis를 별도 티어로 뽑을지, 몇 개로 나눌지.
  → [case-permian-triassic.md](case-permian-triassic.md)에서 이 티어가 하나가 아니라
  **(a) 국소 age-depth 보간**과 **(b) 섹션 간 상관**의 서로 다른 두 성격으로 갈림을 확인.
  → [case-cambrian-base-correlation.md](case-cambrian-base-correlation.md)에서 (b)가 실재하며
  **숫자의 주경로이자 최대 불확실성 원천**임을 확인(GSSP 섹션은 연대측정 불가, 숫자는 타 대륙 상관에서 옴).
- 게이트웨이는 **전역**(하나의 큰 표)인가 **경계별**(경계마다 독립 버전)인가.
- 게이트웨이는 **타입(스키마)** 인가 **얼린 인스턴스(릴리스)** 인가, 아니면 둘 다인가.
- 무엇을 게이트웨이로 **승격**할지 — 이 선택이 곧 거버넌스/비준의 경계가 된다.
- **[케이스에서 확정된 요구사항] 경계 게이트웨이 스키마는 다형(polymorphic)이어야 한다.**
  두 케이스가 두 극단을 보여줬다: GSSP형 = **계산된 분포 + provenance(± 있음)**
  ([case-permian-triassic.md](case-permian-triassic.md)), GSSA형 = **결정된 상수(오차 없음, 상류 네트워크 없음)**
  ([case-precambrian-gssa.md](case-precambrian-gssa.md)). ICC는 실제로 이 둘을 한 표에 공존시킨다.
  → 남는 질문: 두 타입을 어떻게 하나의 스키마로 담을 것인가.
- **토폴로지 재배선을 버전으로 추적해야 한다.** GSSA→GSSP 전환은 노드 *값*이 아니라 *배선*이 바뀌는 일
  (Ediacaran 완료, Cryogenian 진행 중). 값 diff와 별개로 **위상(topology) diff**를 어떻게 표현·버전할지.
- **[캄브리아 사례에서 나온 제약] "age model 선택"이 1급 노드여야 한다.** 같은 데이터에서 경쟁 age model이
  다른 숫자를 낸다(캄브리아 base 538.8 vs ~536). 경쟁 모델을 **대안 그래프 브랜치**로 나란히 두고 diff를
  보여주는 것을 스키마가 지원할지.
- **[제약] 경계 "위치" 노드와 "연대 앵커" 노드를 분리해야 한다.** GSSP는 *어디가* 경계인지만 고정하고,
  *언제*는 상관 서브그래프가 댄다(Fortune Head 위치 ↔ Oman/Namibia 앵커). 둘을 한 노드로 뭉치면 안 됨.
- **[제약] provenance 그래프가 지리적으로 분산된다.** 경계 숫자를 역추적하면 GSSP가 아니라 다른 대륙의
  섹션·δ¹³C 곡선이 나올 수 있다. 스키마가 이 분산된 출처를 감당해야.

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

## 5. 데이터 모델 — 노드 종류 (구현)

데이터 모델은 **티어(registry / graph / release) × 카테고리(data / process / clamp)** 로 구성되고, 그래프 티어는
아래 **16개 노드 타입**으로 채워진다.

> 원래 이 자리에 있던 선형 **Layer 0–6** 브레인스토밍은 이제 서사적 읽기 순서로만 유효하며
> [archive/idea-layer-model-0-6.md](archive/idea-layer-model-0-6.md) 에 보관했다. 현재 척추:
> [tier-category-model.md](tier-category-model.md) · [concept-map.md](concept-map.md) §1.

### data — 관측·참조 leaf (불변·인용 가능)
학자가 새로 넣는 "사실"이 여기 붙는다.
- **`radiometric-uPb`** — U–Pb 방사연대 관측.
- **`astronomical`** — 천문 튜닝(astrochronology) 연대.
- **`biostratigraphic`** — 생층서 datum(FAD/LAD) 신호.
- **`magnetostratigraphic`** — 자기역전 패턴 신호(상관용).
- **`published-age`** — 발표 경계연대 참조 leaf(ICS/GTS chart).

### process — 변환·모델·합성
지저분한 과학(보간·상관·동시추정)과 차트 조립이 여기서 일어난다.
- **`age-depth-model`** — 한 노두 내 age–depth 보간(국소, 선형/스플라인).
- **`cross-section-correlation`** — 노두 간 상관 종합(**load-bearing**). 사례: [case-cambrian-base-correlation.md](case-cambrian-base-correlation.md).
- **`calibration-transfer`** — 참조 연대를 타겟 신호로 전이.
- **`joint-inference`** — 국소 동시추정(순환을 접는 노드).
- **`boundary`** — 경계점(0-cell). 상류 계산에서 연대를 받는다.
- **`unit`** — 시간 단위(1-cell, span). 미분할 구간을 한 노드로.
- **`merge`** — 말단 기하 병합. boundary/unit 조각을 union → ICC 차트.

### clamp — 거버넌스 게이트
합의·비준이 값에 개입하는 지점.
- **`pin`** — 값 고정(GSSA = pin의 특수 case).
- **`range`** — 구간 [min, max] 절단.
- **`order`** — 두 경계 순서 검사(older ≥ younger).
- **`freeze-version`** — 버전 나선 차단, 특정 릴리스 값으로 고정.

이중 명명(연대층서 Stage ↔ 지질연대 Age)은 registry 티어(`chrono` 앱)가, 발표 릴리스(ICC=bake / GTS=narrate)는
release 티어(`releases` 앱)가 맡는다. 순서는 별도 노드가 아니라 **`order` edge**(경계 세로 포트 연결)로 표현하고,
평가는 그래프를 위상순으로 돌려 분포를 전파([node-graph-paradigm.md](node-graph-paradigm.md))한 뒤 정합성 게이트가
순서·지속시간·공분산을 검사한다([coherence-gate.md](coherence-gate.md)).

## 6. 워크플로우 상상 (CI for science)

1. 학자가 **data 노드**(관측)를 PR처럼 제안.
2. 파이프라인이 하류 **process·clamp** 를 재평가.
3. **diff**를 보여준다 — 예: "이 U-Pb 하나 추가하면 Permian–Triassic 경계가 251.902 → 251.88 Ma, 2σ 축소".
4. Fixed release는 검증된 스냅샷, sandbox는 실험 브랜치. 개인 fork 시대표 허용 여부는 미정.

## 7. 열린 질문 (Open questions)

- ~~**연대 모델의 위상**: cdGTS가 실제로 age model을 *계산*까지 하는가, 아니면 "발표된 값 + 출처 기록" 수준인가?~~
  **→ [해소됨]** 엔진이 실제로 계산한다 — `age-depth-model`(선형/스플라인 MC), 공분산 인지 지속시간, 정합성 인증서
  (P06). `published-age` leaf 는 "발표값+출처" 경로도 함께 지원(둘 다 있음).
- **권위 vs 실험의 경계**: sandbox 결과와 공식 ICC를 어떻게 명확히 구분? 학자 개인의 "내 브랜치 시대표"를 어디까지 허용?
- 기존 포맷과의 정합: Macrostrat, GeoSciML / CGI Geologic Timescale, ICS 공식 배포 형식 등과 맞출 것인가?
- 버전 전략 구체화: git 태그 · 시맨틱 버저닝 · 자동 검증(CI)을 어떻게 매핑할 것인가?

## 8. 정련 중인 생각 — 중간 티어와 게이트웨이

> 상태: **hunch(직감) 수준. 확정 아님.** 실제 사례를 하나 붙잡고 작업해봐야 맞는 접근인지 알 수 있다. 아래는 방향 감각을 기록해두는 것.
>
> **[대부분 실현됨]** 여기 §8.1(correlation/synthesis 중간 티어)·§8.2(게이트웨이 계약)의 직감은 구현으로 굳어졌다 —
> correlation/synthesis = `cross-section-correlation`·`joint-inference` 노드, 게이트웨이 = `Gateway`/`merge` + 정합성
> 게이트. Layer 참조는 서사적 읽기 순서로 읽을 것. 현행: [tier-category-model.md](tier-category-model.md).

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

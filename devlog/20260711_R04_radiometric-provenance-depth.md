# 20260711_R04 — 방사연대 provenance 를 cdGTS 에 어느 깊이까지 구현할까

> 성격: **검토(scope/altitude).** `docs/radiogenic_isotope_geochronology_summary.md`(Schmitz 2012, GTS2012 Ch.6
> 요약)를 cdGTS 관점에서 읽고, "논문 디테일을 다 구현할 필요는 없다 — **어느 수준이 적당한가**"를 정리한다.
> 결론: 재설계가 아니라 **한 프리미티브(공유 보정 파라미터 노드)만 1급으로 올리는 L1**이 적정선.

## 1. 이 문서는 cdGTS 논지를 검증한다

핵심 메시지 = "방사연대는 암석의 고정 숫자가 아니라 시료·분석법·표준·붕괴상수·오차모델로 계산한 **버전 있는
결과**." 이건 cdGTS 창립 명제 그대로이고, 이제 도메인 권위가 뒷받침한다. 그리고 substrate 는 이미 있다:
`Distribution.budget{analytical, systematic}` + `shared_components`(공분산) + 증분 content-hash 평가 +
`cite` 엣지. → **재설계 아님, 한 지점만 깊게.**

## 2. 적정 깊이 판별 규칙 (altitude rule)

논문의 깊은 사슬(시료→광물→분석법→동위원소비→tracer→monitor→붕괴상수→소프트웨어→기각분석→연대)은 대부분
**실험실 LIMS 관심사**. cdGTS 는 시대표 **그래프 엔진**이지 지질연대 데이터 저장소가 아니다. 판별 기준 하나:

> **"이걸 바꾸면 하류 경계 연대(또는 그 상관구조)를 다시 계산해야 하나?"** — 그렇다 → 노드/의존으로 모델링.
> 아니다 → 인용 출처 안에 두고 cite 만.

- 붕괴상수(²³⁸U/²³⁵U, ⁴⁰K)·FCs monitor(28.201 Ma)·EARTHTIME tracer → 바꾸면 다수 연대 이동 → **모델링**.
- zircon 하나 동위원소비·CA-TIMS 화학·Re–Os detrital 보정·이상치 기각 → published interpreted age 안에 접혀
  있고 cdGTS 는 그 값을 신뢰 → **모델링 안 함, 논문 cite 만**.

## 3. 그래프 레벨 load-bearing = 딱 하나

현재 `radiometric-uPb` = **불투명 leaf**(params=분포+depth, 입력=section, 출력=age; 붕괴상수·tracer·monitor
입력 없음). "계산된 provenance"가 아니라 "저장된 숫자+오차". 논문이 요구하는 유일한 새 1급 프리미티브:

**공유 보정 파라미터 노드** — 붕괴상수·monitor(FCs)·tracer 를 **소수의 공유 상류 노드**로 두고, 여러 방사연대가
거기 의존(edge)하며, 그 연대의 `systematic` 성분을 그 노드를 가리키는 `shared_component` 로 태깅.

이거 하나로:
1. **공분산 백본이 진짜 공유원을 얻음** — 두 경계가 같은 tracer/붕괴상수 공유 → duration 오차 상관(이미 커널의
   `shared_components`·covariance-aware duration 이 실데이터로 돎). = TODO §2 "joint·공분산 워크드 예시" 그 자체.
2. **"상수 바뀌면 전체 재계산"이 공짜** — FCs 노드 값 변경 → 증분 엔진이 하류 전부 dirty → **diff 가 "이 N개 경계
   영향/이동" 표시**. cdGTS 미션("기계가 전파·diff")의 킬러 유스케이스.

## 4. 레벨별 권고

- **L0 (현재)** — 불투명 leaf. 재계산·상관 불가.
- **L1 (권장, 적정선)** — 공유 보정 노드 2~3개(붕괴상수·FCs·tracer) + 방사연대가 거기 의존 + systematic 을
  shared_component 로 태깅. **재계산의 정확한 숫자는 수동/단순 rescale 로 두고, "무엇이 영향받는지"를 diff 로
  surface.** 딱 그래프 엔진의 고도.
  - **✅ 프리미티브 구현됨(2026-07)** — `calibration-constant` NodeType(data leaf, params: distribution·kind·
    symbol, out 포트 `value`). 커널이 출력 불확실성 전액을 자기 자신(ref=symbol)의 shared_component 로 자동
    태깅 → 소비 연대들이 공짜로 공분산 획득. **아직 미완**: 방사연대(radiometric-uPb)가 이걸 소비하는 배선
    (rescale/joint 커널)과 실제 예시 그래프는 미착수(= 아래 vertical slice).
- **L2 (후속, 선택)** — monitor/붕괴상수 변화 실제 rescale 커널(선형 민감도) + **FCs 교차보정(astrochronology +
  U-Pb → FCs 연대)을 joint-inference 노드로**(P06.4b). 구동 유스케이스 생길 때.
- **범위 밖 (명시)** — 동위원소비·CA-TIMS 화학·Re–Os detrital·이상치 기각·reduction SW → 인용 논문(DOI/cite)에
  둠. cdGTS 는 interpreted age + 사용 보정 + cite 만.

## 5. 기존 백로그 연결 (새 스코프 아님)

- **L1** = TODO "data 카테고리 내부 이질성"(재계산 가능 radiometric vs 불투명 published-age) +
  "joint·공분산 워크드 예시" 를 **실 도메인 콘텐츠로** 채움.
- **L2** = "계산 커널 확장" + P06.4b joint.
- 이 문서는 새 요구가 아니라 **이미 계획된 항목에 진짜 과학 구조를 공급**.

## 6. 부수 정정 — published-age vs 재계산 가능 radiometric

논문은 레거시 불투명 연대와 재계산 가능한 방사연대를 **동급 취급 금지**를 함축(원자료 없는 legacy age 배제).
현재 둘 다 category=data leaf 로 동급 → **provenance depth(재계산 가능 여부) 표기 필요**. 위 "data 이질성"
TODO 와 맞물림. (cf. concept-map §3-1 "provenance 깊이 = 하나의 축".)

## 7. 결론 / 다음

- **논문 디테일 구현 금지. "바꾸면 하류가 재계산되는가" 기준으로 공유 보정 파라미터(붕괴상수·FCs·tracer)만 1급
  노드로 올리는 L1 이 적정선.** 그러면 공분산·재계산·diff 가 실데이터로 돌고, lab 내부는 cite 로 남는다.
- 착수 시: P07 이 base-Cambrian 으로 한 것처럼 **한 경계(예: base-Triassic Meishan U-Pb, 또는 Ar-Ar/FCs 사례)로
  L1 vertical slice** — 공유 보정 노드 → 상관 duration + "FCs 바꾸면 이만큼 영향" diff 까지. (스케치 대기)
- 원문: `docs/radiogenic_isotope_geochronology_summary.md` · 관련: [cycles §12](../docs/cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가)(joint 노드) · [R01](20260707_R01_vision-implementation-review.md) 아크 A.

# 20260704_041 — 예제4를 order 노드로 시간순 세로 정렬

> [040](20260704_040_order-constraint.md) 의 order 제약을 `example-icc-partial`(예제4)에 실제 적용.
> 36개 period+ 경계를 연대순으로 세로 배치하고 인접쌍을 order 노드로 묶어 **전체 단조성을 authored 제약으로 인증**.

## 한 일 (seed/03_graphs.json)

- 그래프를 평가해 36 게이트웨이의 경계 연대를 얻고 **오름차순 정렬**.
- 경계 소스 노드를 **세로 컬럼**(x=1700)으로 재배치: 젊은=위(작은 y) / 오래된=아래(큰 y) — ICC 관례.
  최하단 base-hadean(4567) … 최상단 base-quaternary(2.58).
- 인접쌍마다 **order 노드 35개**(오른쪽 컬럼) + 엣지 70개: 아래(older)→`older` 포트, 위(younger)→`younger` 포트.
  mode=hard, Δ=0(동일 연대 경계쌍은 `≥`로 통과 — 예: base-cenozoic/base-paleogene 66.0).

## 결과
- `example-icc-partial`: 노드 42→77(+35 order), 엣지 +70, 게이트웨이 36 유지.
- 평가 인증서 **L1 = pass**(위반 0) — 기존 게이트웨이 나열순 warn 스텁이 **명시적 선후 제약 체인**으로 대체됨.
- bake 36경계 유지. GraphSerializer 라운드트립 검증 통과(포트·비순환).

## 검증
- `pytest` **76 passed**. seed replace(inserted 385→455) 정상.
- 배포 재시드는 `seed --mode=replace`(그래프 원자 skip 때문에 add 불가).

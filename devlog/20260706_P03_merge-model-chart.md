# 20260706_P03 — Plan: geometry-merge 모델 (ICC 차트를 그래프 산출로)

> Blender geometry-node 방식: 각 노드가 chart 조각(geometry)을 내보내고, terminal `merge` 노드가 합쳐
> **ICC 차트**를 만든다. 현재 `게이트웨이 → BoundaryRecord → rank별 타일링` bake 경로를 그래프 안으로 수렴.

## 개념
- **boundary** → tick(특정 Ma, chrono 정체성·rank 소속·±·정의방식).
- **time period(unit 노드/그룹)** → band `[older, younger]`(rank·name·color).
- **node group(kind=unit)** → 내부 Join = 하위 컬럼(epoch/age 는 이 nesting 안에서).
- **terminal `merge` 노드** → 모든 top-level 출력 union → chart geometry.

## 확정된 결정 (대화 2026-07-06)
1. **명시 granularity = period 까지.** epoch/age 는 nested group 으로 처리, 지금은 merge 대상 아님.
2. **merge 는 chart 만 대체.** narrate/diff 는 당분간 `BoundaryRecord` 유지(나중에 geometry 파생으로 수렴 가능).
3. **era 그룹 안 만듦.** Era/Eon 밴드는 경계의 **다중 게이트웨이**(예: bnd-base-cambrian = base-cambrian·paleozoic·phanerozoic)에서 타일링.
4. **merge 는 순서 무관**(union). 차트 배열은 기존 **order 엣지 + 경계 연대**가 결정.
5. **node = group = "unit" 통일** — plain unit 노드에도 `unit`/`lower`/`upper` 부여 예정(밴드에 rank·양 경계 필요).
6. **geometry 타입** = `band{rank,name,color,lower,upper,dist(±),provenance}` + `tick{boundary,age,±,GSSP/GSSA}`.
7. **gateway = identity 앵커** 유지(L1 정합성 포함).

## 단계
- **Stage 1 (구조·시각, 본 라운드):** `merge` 노드 타입 + terminal 노드 생성, top-level 출력(경계 27 + Precambrian unit 15 = 42) 배선. 평가/차트 로직 변경 없음 — "모든 게 하나로 모인다" 시각 확인.
  - Phanerozoic period 그룹은 아직 group-source 엣지 미지원 → 그 period 밴드는 경계에서 타일링(Stage 2에서 group 출력 엣지 도입 시 직접 배선).
- **Stage 2 (타입·커널):** geometry datatype + merge 커널(타일링) → 실제 chart geometry. plain unit 노드 unit/lower/upper 바인딩. group-source 엣지 지원.
- **Stage 3 (bake 대체):** `icc-chart` 엔드포인트가 merge geometry 를 읽도록 교체, chart 용 `BoundaryRecord` bake 은퇴(narrate/diff 는 유지).

## 열린 항목
- geometry datatype 스키마 상세(Stage 2).
- group-source 엣지(그룹이 edge source) 데이터모델(Stage 2).
- narrate/diff 수렴은 별도 라운드.

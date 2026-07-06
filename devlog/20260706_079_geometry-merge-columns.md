# 20260706_079 — geometry-merge: 컬럼 merge 그래프 + merge 구동 차트

P03 설계의 Stage 1~2b 구현. ICC 차트를 "게이트웨이 → BoundaryRecord bake" 가 아니라
**그래프의 merge 노드가 산출**하는 방향으로 전환 시작. (narrate/diff 는 아직 bake 유지 — P03 결정 ②)

## 1) unit/group output 포트 (frontend)
- time-period `unit` 노드 타입에 `out` 포트, unit 그룹(kind=unit) 콜랩스 노드에 `comp-out` 합성 포트.
- `GroupNode.jsx`/`index.css`: kind=unit 그룹에 "out ▸" 핸들. `Editor.jsx` buildView 가 group data 에 `kind` 전달.

## 2) merge 노드 타입 + 컬럼 merge 그래프 (Stage 1 + 재구성)
- **`merge` 노드 타입** (`02_nodes.json`): 다중입력 `parts` → `out`. 순수 union, 순서 무관(배열은 order 엣지·연대가 결정).
- **컬럼별 merge 구조** (`03_graphs.json`, merge 노드 18개):
  - period 그룹 내부 **"group output" merge** 12개 — 그룹 내용(age 경계)을 집약 → 컬럼 merge. Blender Group Output 격. 스키마 변경 없이 모두 실제 노드/엣지(내부 merge 는 그룹 member → 컬럼 merge 로 나가는 crossing 엣지가 그룹 출력 핸들이 됨).
  - **컬럼 merge 5개** (Cenozoic·Mesozoic·Paleozoic·Proterozoic·Archean): 컬럼 경계 + Precambrian unit + 그룹 output → 컬럼 merge.
  - **최종 merge** (`icc-chart`): 5 컬럼 merge → 최종.
- 재귀 구조라 나중에 Precambrian unit 이 그룹으로 세분돼도 동일 패턴으로 확장됨(내부 merge 생성 → 컬럼 merge).
- **age unit 은 채우지 않음** — 출력은 그룹 내부 merge 가 받은 age 경계들에서 타일링으로 나온다(P03 결정 ①: period 명시, epoch/age 타일링/nesting).

## 3) Stage 2b — merge 구동 차트 geometry (`releases/views.py`)
- **`merge_geometry(graph, merge_key, results)`**: merge 로 흘러드는 boundary subtree(재귀)를 모아 rank 별 타일링. 기존 `build_icc_levels` 재사용, 단 전-게이트웨이가 아니라 **그 merge 의 입력**으로 한정.
- **`IccChartView` 가 종단 merge 구동**: 기본은 종단 `icc-chart`, `?node=<merge-key>` 로 컬럼 부분 차트.
- geometry 는 chrono/gateway 접근이 필요해 순수 커널 아님 → `releases`(engine 위) 그래프-인지 서비스로 배치(레이어링 유지).

## 검증
- 종단 merge geometry == 기존 전-게이트웨이 차트 (완전 동일 → 무회귀, 프론트 그대로 렌더).
- `merge-paleozoic` → Cambrian~Permian period 만 (Cretaceous 없음) → geometry 가 merge 구조의 실제 산출임을 고정.
- 노드 타입 15→16, `test_icc_chart_driven_by_merge_tree` 추가, 전체 **91 passed**. bake 177·certify pass 유지.

## 다음 (Stage 3)
- chart 전용 bake 은퇴 → 엔드포인트/프론트가 merge geometry 로 완결. 컬럼 merge 클릭 시 부분 차트 표시.
- (나중) age unit 채우기 + unit→group 재귀, narrate/diff 의 geometry 수렴.

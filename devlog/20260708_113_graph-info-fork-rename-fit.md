# 20260708_113 — 그래프 정보 편집 · fork rename · 로드 시 fit (0.1.31)

## 그래프 기본정보 조회/편집

- **`Graph.description`** 필드 추가(TextField, blank) — migration `graph/0009`.
- **`GraphSerializer`** 에 `description` 추가. `name`/`description` 은 `required=False` →
  **PATCH(부분 갱신)** 로 편집(토폴로지 PUT 은 nodes/edges 없으면 `update()` 가 위상 교체를 건너뜀 → 안전).
- **`ⓘ Info` 다이얼로그**(툴바 그래프 선택 옆): 이름·설명 편집(소유자면) + Status·Owner·Forked-from·Slug 조회.
  read-only 그래프면 필드 비활성 + Close. `updateGraphInfo(id, {name, description})` PATCH.

## Fork 시 이름 지정

- **`fork_graph(source, user, name=None)`** — name 주면 그 이름, 아니면 `"<source> (fork)"`. description 도 복제.
  fork 뷰가 `request.data["name"]` 전달. `forkGraph(id, name)` 바디에 name.
- Editor: Fork 를 즉시 실행 대신 **rename 다이얼로그**로(기본값 `"<name> (fork)"`).

## 로드 시 자동 fit (조건부)

- 그래프 로드 시 **저장된 viewport 가 있으면 그대로 복원, 없으면 `fitView`** 한 번.
  (example④처럼 saved viewport 없는 그래프가 처음에 화면 밖으로 나가던 문제.) `shouldFitRef` 로 hydrate→effect 전달.

pytest graph 23 passed · frontend build OK. 테스트 서버 0.1.31 배포.

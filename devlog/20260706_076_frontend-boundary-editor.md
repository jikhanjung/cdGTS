# 20260706_076 — 프론트 에디터: boundary/unit 렌더 · 그룹 I/O · bound frame · 그룹 인스펙터 · 단일클릭 선택

> [075](20260706_075_boundary-span-model.md) 셀 복합체 모델의 편집 UI. 배포는 사용자.

## 노드 렌더 (`CdgtsNode.jsx`, `index.css`)
- **boundary** 노드: 보라(`#8b5cf6`), `◈ boundary` 뱃지. 요청에 따라 **제목만(반 높이)** — 포트 라벨·result 숨김, 핸들은 유지, 모서리 둥글게.
- **unit** 노드: 라벤더 대시(`▭ time period`), Age subdivisions 그룹과 같은 계열. 값 없는 span.
- 세로 order 포트 규약: younger=위(source)/older=아래(target).

## Blender식 그룹 I/O + bound frame (`GroupIoNode.jsx`, `BoundNode.jsx`, `Editor.jsx`)
- drill-in 시 외부 데이터 연결을 좌(input)·우(output) **하나의 인터페이스 노드**로 집약(포트 다중).
- unit 그룹 drill-in 시 그 span 의 upper(younger, 위)·lower(older, 아래) bounding 경계를 고정 프레임으로 표시 — 어느 중첩 구간을 열어도 일관.
- drill-in Y 방향: 오래된 게 아래(ICC), 최상위 레이아웃은 유지.

## 그룹 인스펙터 (`Inspector.jsx`, `Editor.jsx`)
- 노드그룹 선택 시 오른쪽 패널에 그룹 정보: name(편집), kind(container/unit), key, members(하위트리 수·하위그룹), collapsed, unit 그룹이면 unit 슬러그·upper(younger)·lower(older) 경계.

## 단일클릭 그룹 선택 (`Editor.jsx`)
- 원인: 제어형 모드에서 `onNodesChange` 가 그룹 노드의 `select` 변경을 버려(위치만 반영) 첫 클릭에 선택 안 됨(두 번 클릭 필요).
- 고침: 그룹의 select 변경을 `selectedGroupKeys` 로 반영, `onSelectionChange` 의 이중 그룹 처리(빈 값으로 덮어쓰던) 제거. 이제 한 번 클릭에 선택+정보. (더블클릭=drill-in 유지.)

## 검증
- vite 빌드 클린(202 모듈). 백엔드 무관.

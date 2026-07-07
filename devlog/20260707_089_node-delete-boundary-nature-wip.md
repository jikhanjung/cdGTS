# 20260707_089 — 노드 우클릭 삭제 · 팔레트 boundary nature 기본값 (0.1.25-WIP)

frontend 전용. WIP 태그(0.1.25-WIP)로 테스트 서버 배포.

## 1. 노드 우클릭 → 삭제 (Editor.jsx)
노드 컨텍스트 메뉴에 빨간 "Delete node" 추가. `onDeleteNodes(ids)` 가 노드 + 그 노드에 연결된
엣지를 함께 제거하고 선택에서 제외. 선택이 여러 개면 "Delete N nodes" 로 선택 전체 삭제.

## 2. 팔레트 boundary → nature=boundary 기본 (Editor.jsx · addNodeAt)
팔레트에서 `boundary`/`published-age` 타입을 드롭하면 `nature='boundary'` 를 기본 부여 →
놓자마자 컴팩트 ◈ boundary 스타일(제목 + 연대 readout, 포트는 핸들만)로, 기존 "Base of …"
노드와 동일한 모양·동작. 그 외 타입은 기존대로 generic. rfToApi 가 nature 직렬화 → 왕복 유지.

## 비고
- 이전엔 드롭 시 nature 미설정 → generic → 파란 process 노드로 보였음. 엔진 동작은 동일(nature 는 표시용).
- seed 무변경 → 재시드 불필요.

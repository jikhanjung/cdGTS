# 20260707_097 — 선택 노드 우클릭 시 그룹 메뉴 (0.1.25-WIP)

frontend 전용. 재시드 불필요.

## 다중선택 오버레이 우클릭 통과 (index.css)
096 에서 `.react-flow__nodesselection-rect` 를 시각만 숨겼으나 여전히 `pointer-events:all` 로
선택 영역을 덮어 우클릭을 가로챔 → `onNodeContextMenu` 미발화 → 브라우저 기본 메뉴.
`pointer-events:none` 추가 → 우클릭이 아래 노드/pane 으로 통과:
- 선택 노드 우클릭 → node 메뉴(이미 "Group selected nodes" 포함)
- 빈 공간 우클릭 → pane 메뉴(그룹 생성)
두 경우 모두 그룹 생성 메뉴. 다중 드래그는 선택 노드 드래그로 그대로 동작.

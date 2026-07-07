# 20260707_095 — 노드 선택 표시 링 · shift-click 추가 · 그룹 사각형 제거 (0.1.25-WIP)

frontend 전용. 재시드 불필요.

## 1. 일반 노드 선택 시 테두리 링 (CdgtsNode.jsx · index.css)
React Flow `selected` prop → `.cdgts-node.selected` 에 `box-shadow: 0 0 0 1.5px #fff, 0 0 0 3.5px #a142f4`
(흰 간격 + 라벤더 링). 노드 색과 무관하게 "테두리가 하나 더" 보임. 노드그룹의 선택 아웃라인과 동일 컨셉.

## 2. Shift+클릭 = 선택 추가 (Editor.jsx)
`multiSelectionKeyCode="Shift"` 는 있었으나 `selectionKeyCode`(기본 Shift)와 충돌. 박스 선택은
`selectionOnDrag`(평상시 드래그)로 되므로 `selectionKeyCode={null}` 로 Shift 를 선택 추가 전용화.

## 3. 다중 선택 시 전체 사각형 제거 (index.css)
드래그 다중선택의 그룹 바운딩 박스(`.react-flow__nodesselection-rect`, 점선+옅은 fill)를
`background:transparent; border:none` 으로 시각만 숨김. 드래그 중 러버밴드(`.react-flow__selection`)와
개별 노드 선택 링은 유지.

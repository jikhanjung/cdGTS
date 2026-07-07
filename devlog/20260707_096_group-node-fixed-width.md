# 20260707_096 — 그룹 노드 고정 width (0.1.25-WIP)

frontend 전용. 재시드 불필요.

## collapsed 그룹 노드 폭 고정 (Editor.jsx)
일반 노드는 노드 객체에 명시 width(DEFAULT_NODE_WIDTH=172)를 받는데, buildView 의 collapsed
그룹 노드는 width 미지정 → `.react-flow__node-cdgtsGroup` 래퍼가 content shrink-to-fit,
`.group-node{width:100%}` 무의미 → 긴 I/O 라벨이 노드를 옆으로 늘림.
그룹 노드에도 동일 메커니즘으로 `width: GROUP_NODE_WIDTH(200)` 부여 → 200px 고정, 라벨은
ellipsis 로 잘림.

# 20260707_098 — Group I/O 노드 선택 링 · 폭 제한 (0.1.25-WIP)

frontend 전용. 재시드 불필요.

## 1. 합성 노드(gio/bound) 선택 링 (Editor.jsx)
onNodesChange 가 `gio:in`/`gio:out`/`bound:*` 의 position 변경만 저장하고 select 변경은 버려
view 재생성 시 selected 유실 → 링 미표시(`.group-io-node.selected` CSS 는 이미 있음).
`ioSel` Set 상태 추가로 select 보존, viewNodes 에서 `selected: ioSel.has(id)` 부여.
activeGroup 변경 시 초기화(합성 노드는 해당 drill 내에서만 존재).

## 2. GroupIoNode 폭 제한 (Editor.jsx · index.css)
`.group-io-node` 에 상한 없어 긴 port 라벨이 노드 확장. gio 노드에 `width: GROUP_IO_WIDTH(200)`
부여, `.group-io-node{width:100%;box-sizing:border-box}` 로 래퍼 채움, port li 에
`overflow:hidden;text-overflow:ellipsis` 로 라벨 잘림.

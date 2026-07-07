# 20260707_099 — 파생 노드 강제선택 버그 수정 (0.1.25-WIP)

frontend 전용. 재시드 불필요.

## 박스 밖 Group Output 이 선택되는 현상 (Editor.jsx)
buildView 가 매 렌더마다 파생 노드(group/gio/bound)를 새 객체로 재생성 → 드래그로 실제 노드
선택 시 nodes 변경 → viewNodes 재계산 → gio:out 등이 새 객체가 됨 → React Flow 가 미측정
노드로 취급(`getNodesInside`: handleBounds 없음 → forceInitialRender, 또는 measured.height 0 →
area 0 → overlappingArea>=0 항상 참) → 박스 밖인데 강제 선택.

수정: `synthRef` (id→{sig,node}) 캐시로 position·selected·width·data 시그니처가 같으면 이전
객체 참조 재사용 → React Flow 가 재측정하지 않아 실제 겹침만 계산. 직접 클릭 시엔 sig 변경으로
정상 선택/링 표시.

# 20260707_085 — edge 선택 삭제 · ICC 차트 라벨 zoom 대응

두 가지 frontend 개선.

## 1. edge 선택·삭제 (order edge 포함) — Editor.jsx · index.css
edge 를 지울 방법이 없었다(우클릭 메뉴는 node/group/pane 뿐). younger/older(order) edge 포함
모든 edge 를 지울 수 있게.
- `onEdgeContextMenu` 추가 — edge 우클릭 시 컨텍스트 메뉴(`kind:'edge'`, edge 종류 저장).
- `onDeleteEdge` — 뷰 edge id 의 `v-` 접두어를 실제 edge id 로 되돌려 상태에서 제거. order·경계/그룹
  포트로 재배선된 edge 도 모두 실제 edge 하나에 매핑되므로 정상 삭제.
- 메뉴 항목: order 면 "Delete order (younger/older) edge", 그 외 "Delete edge". `.danger` 스타일(빨강).
- 선택된 edge 를 `stroke-width:3` 로 굵게 → 클릭 선택 후 Delete 키(기존 onEdgesChange 경로)도 피드백.

## 2. ICC 차트 라벨 zoom 대응 — IccChart.jsx
확대해도 원래 얇은 칸(예: Cambrian series 안 stage)은 이름이 안 보였다. 라벨은 `h > 13`
(viewBox 좌표 높이)일 때만 그렸는데 h 는 zoom 무관 → 아무리 확대해도 안 뜸. 폰트도 viewBox 와
함께 통째로 스케일돼 밴드 대비 비율 고정.
- 노출 조건을 화면상 높이 기준으로: `screenH = h·zoom > 12`. 확대하면 얇은 밴드가 커지는 순간 라벨 노출.
- 폰트 크기 `min(13, max(8, screenH·0.5)) / zoom` — `/zoom` 상쇄로 화면상 8~13px 로 읽히는 크기 유지,
  열 너비 초과 방지 상한.
- 수직정렬 `dominantBaseline="central"`(가변 폰트 정확 중앙, 기존 `+3` 보정 제거).
- zoom=1 기본 화면은 기존과 거의 동일(얇은 칸은 여전히 숨김·툴팁 유지).

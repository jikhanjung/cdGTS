# 20260707_091 — merge 노드 배지 라벨 (0.1.25-WIP)

frontend 전용. 재시드 불필요.

## merge 배지: PROCESS → ▽ Merge (CdgtsNode.jsx)
merge 노드(`nodeType === 'merge'`)의 우상단 카테고리 배지를 `process` 대신 `▽ Merge` 로 표시.
`▽`(깔때기 — 여러 parts 가 하나로 모이는 merge 의미)로 `◈ boundary`·`▭ time period` 와 같은
기하 글리프 스타일 통일. 배지는 CSS 대문자 처리 → 화면상 `▽ MERGE`.

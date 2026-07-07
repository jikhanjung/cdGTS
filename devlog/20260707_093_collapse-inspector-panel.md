# 20260707_093 — 오른쪽 Inspector 패널 접기 (0.1.25-WIP)

frontend 전용. 재시드 불필요.

## 데스크톱에서 속성 패널 숨기기 (Editor.jsx · Inspector.jsx · index.css)
데스크톱 우측 Inspector(280px 고정 패널)를 접을 수 있게.
- 상태 `inspectorCollapsed`(데스크톱 전용). collapsed 면 Inspector 미렌더 → 캔버스 확장.
- 툴바 토글 `Properties ◂`(숨김)/`Properties ▸`(표시), 선택 여부 무관 항상 접근.
- 패널 내 데스크톱용 ✕(노드/그룹 헤더 + 빈 상태 우상단) → onHide 로 즉시 숨김.
- 모바일 드로어(inspectorOpen)와 분리. `.desktop-only`/`.mobile-only` 유틸로 표시 제어.

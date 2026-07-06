# 20260707_083 — ICC 차트 확대/축소 (zoom + pan)

세션 초반 미뤄뒀던 항목. ICC Chart 뷰에 zoom 추가 (기존 scroll pan 유지).

## 변경 (frontend only — IccChart.jsx)
- **viewBox 기반 zoom** — SVG 를 `viewBox="0 0 W Hh"` 로 고정하고 표시 크기만 `W·zoom × Hh·zoom` 로 변경. 내부 렌더 좌표·타일링 로직은 그대로(안전).
- **인터랙션**:
  - Ctrl/⌘ + 마우스 휠 → 커서 지점 기준 zoom. 재렌더 후 scroll 위치를 보정(`useLayoutEffect` + `pendingScroll`)해 가리킨 지점이 화면에 고정.
  - 툴바 `−` / `현재%`(클릭 100% 복귀) / `+` / `Fit`(세로 맞춤).
  - 일반 스크롤 = pan (기존 `.iccchart-scroll` overflow:auto bounded viewport).
- clamp 0.15~6x.

## 비고
- 축/컬럼 헤더/밴드 라벨은 콘텐츠와 함께 스케일(1차 버전). 필요하면 축·헤더 고정은 후속.
- 좁은 최근대(Quaternary/Neogene)·미세 age 밴드 탐색에 유용.

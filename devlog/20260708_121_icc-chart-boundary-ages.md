# 20260708_121 — ICC 차트에 경계 연대(Ma) 표시 (공식 ICS 차트 스타일)

사용자 요청: Vault ICC 차트를 공식 ICS 차트(JPG/PDF)처럼 **각 경계에 연대 숫자**를 찍어 보여줘.

## 변경 (frontend/src/IccChart.jsx)

- **"Ages (Ma)" 토글**(기본 ON) 추가 — `± Uncertainty` 옆.
- `boundaryAges` memo: base 연대별로 그 경계를 무는 **가장 세밀한 컬럼(max ci)**을 골라, 그 컬럼 오른쪽 끝
  경계선 바로 위에 숫자를 찍음. `±pm` 있으면 병기(예: `251.9±0.2`). GSSA(오차 0)는 값만.
- 밴드가 화면에서 너무 얇으면(owning band screenH < 13px) 라벨 숨김 → **줌인하면 드러남**(밴드 이름 규칙과 동일).
- 폰트 1/zoom 카운터스케일(화면상 일정 크기). `.icc-agelabel` 흰 stroke halo(paint-order)로 색 밴드 위에서도 가독.

## 노트

숫자는 밴드의 **base(오래된) 경계**에 붙는다(젊은 band 의 top = 인접 older band 의 bottom 이므로 모든 내부 경계를 덮음).
맨 위 0 Ma 는 좌측 축이 이미 표기. 컬럼 폭 안 우측 정렬이라 가운데 밴드 이름과 겹치지 않음.

frontend 빌드 통과. (백엔드 무관 — 순수 표시.)

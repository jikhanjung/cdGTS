# 20260711_137 — Editor.jsx 분해 (1차: 뷰 레이어 + 컨텍스트 메뉴)

[R02 검토 노트](20260711_R02_source-code-review.md) 최우선 항목. `Editor.jsx`(1252줄)가 최대 회귀 위험
지점이라, Tier 1/2 안전망([134](20260711_134_ci-flow-scenario-test.md)·[136](20260711_136_tier2-browser-smoke.md))
확보 후 **위험이 낮은 순수/프레젠테이션 seam 부터** 뜯어낸다.

## 추출

- **`graphView.js`(신규 228줄)** — 순수 뷰/변환 레이어. `apiToRF`·`rfToApi`(API 그래프 ⇆ React Flow) +
  `buildView`(중첩 그룹 드릴인 구조 계산, 이 파일 최대 복잡도) + 관련 상수/헬퍼(`rfType`·`nodeWidth`·
  `edgeStyleFor`·`isOrderConn`/`isCiteConn`). **훅·상태 의존 0 → 독립 테스트 가능**. 빌드 JS 크기 불변 =
  순수 이동임을 확인.
- **`EditorMenu.jsx`(신규 60줄)** — 우클릭/롱프레스 컨텍스트 메뉴(node/group/pane/edge). `menu` 디스크립터 +
  핸들러 15개를 props 로 받는 프레젠테이션 컴포넌트. 참조 식별자를 동일명 prop 으로 1:1 이관.

## 결과

- `Editor.jsx` **1252 → 990줄**(−21%). 가장 gnarly 한 로직(buildView)과 메뉴 렌더가 본체에서 빠짐.
- `npm run build` 정상(211→212 모듈). 브라우저 스모크(app boots·editor 그래프 마운트·login CSRF)로 회귀 확인.

## 남은 분해 (후속)

R02 가 지목한 나머지 seam — **selection/menu 훅**, **graph actions(save/evaluate/bake/propose) 훅**,
**read-only gating** — 은 상태·클로저 의존이 깊어 위험이 높다. 착수 전에 **컨텍스트 메뉴·드릴인을 실제로
클릭하는 e2e 커버리지**를 스모크에 얇게 추가해 안전망을 두껍게 한 뒤 진행 권장. (이번엔 순수/프레젠테이션
2개만 확정적으로.)

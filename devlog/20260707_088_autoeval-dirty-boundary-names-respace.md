# 20260707_088 — 자동 평가·미저장 표시 · 경계 이름 · 평가높이 기준 재배치

두 세션 분량. 0.1.25 로 배포.

## 1. 기본 자동 평가 (Editor.jsx)
`onEvaluate` → `runEvaluation({silent})` 코어로 분리. 로컬==DB 가 보장되는 시점에만 조용히 자동 평가:
- 그래프 로드/전환 직후(`useEffect([graphId])`) · Save 성공 직후.
- silent 은 Results 패널·에러를 띄우지 않고 노드/Inspector 값만 채움. 수동 Evaluate 버튼은 그대로.
- 결과 부착(`data.result`)은 rfToApi 직렬화 대상이 아니라 dirty 에 영향 없음. 효과가 graphId 에만 묶여 편집/결과부착으로 재실행 안 됨(루프 없음).

## 2. 미저장(dirty) 표시 (Editor.jsx · index.css)
구조 시그니처(노드·엣지·그룹, viewport·결과 제외)를 마지막 저장/로드 스냅샷과 비교 → `dirty`.
툴바에 `● Unsaved`(호박)/`✓ Saved`(초록) 칩 + Save 버튼 강조. 평가는 서버의 저장 상태를 계산하므로
미저장 여부가 눈에 보이는 게 중요.

## 3. Phanerozoic 경계 이름 = "Base of <Period>" (seed/03_graphs.json)
example-icc-partial 현생누대 period-base 경계 12개 통일. published-age 10개(Ordovician…Quaternary)
+ boundary 타입 2개(triassic·cambrian, 주석은 description 으로 보존). 선캄브리아·그룹내 stage 경계는 유지.

## 4. 평가높이 기준 재배치 (seed/03_graphs.json · CdgtsNode.jsx)
평가 시 boundary 만 연대(value_ma)로 커지고(≈44px) unit 은 안 커짐(스팬=점 연대 없음).
- unit 의 "—" 결과 푸터 숨김(노이즈 제거·높이 안정).
- unit/boundary 교대 컬럼(11개 age 그룹 + 선캄브리아 top-level 2컬럼) 세로 간격을 높이 기준으로
  재조정: unit 뒤 +74 / boundary 뒤 +60. merge 세로 중앙. 상단 merge(y=-60)·현생누대 경계 컬럼 유지.

## 배포
seed 변경 포함 → 배포 시 `seed --mode=replace` 재시드 필요.

# 20260707_087 — boundary 연대 표시 (노드 얼굴 + Inspector)

boundary 노드가 입력(`age`)으로 받은 연대 / 공표 폴백값이 UI 어디에도 안 보이던 문제. 엔진은 이미
입력값을 통과시켜 연대로 계산(`engine/kernels.py` boundary 커널)하지만 표시가 없었다.

## 1. 노드 얼굴 — boundary 노드만 (CdgtsNode.jsx · index.css)
half-height 유지한 채 제목 아래 `### Ma` 한 줄 추가.
- 값 = `data.result.distribution.value_ma`(평가 결과 = age 입력에서 유래) → 없으면
  `data.params.distribution.value_ma`(자기 공표값) 폴백. 입력 연결 시 평가 후 입력값, 없으면 공표값 표시.
- 캐시 재사용 `•`, 툴팁으로 출처(recomputed/cache/published) 안내.
- 값이 전혀 없으면 기존처럼 제목만. `:has(.cdgts-node__bage)` 로 값 있을 때만 헤더 하단 각지게.

## 2. Inspector — 전 노드 공통 (Inspector.jsx · index.css)
`value_ma` 가 있는 모든 노드 상단에 읽기전용 "result age ### Ma" readout(캐시 `•`).
order(clamp) 노드는 값 대신 기존 판정 배너(상호 배타). boundary 는 params 폼의 공표 distribution 과
별개로, 결과 readout 이 실제 유효 연대(입력 유래 포함)를 보여준다.

## 비고
- 둘 다 Evaluate 후 `data.result` 채워지면 반영. 노드 얼굴은 평가 전에도 공표 폴백값 있으면 미리 표시.

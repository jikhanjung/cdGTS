# 20260703_024 — age-depth-model 실제 커널

> [023](20260703_023_compute-kernels.md) 후속. 커널 프레임워크 위에 age-depth 보간 커널 구현.

## 한 일

### 데이터 모델 확장 (age-depth 에 필요)
- **dated horizon = (depth, age)** — 데이터 노드 params 에 `depth`(층서 깊이/높이) 추가.
  age-depth-model params 에 `target_depth`(보간할 층준, 예 GSSP 레벨) + `method`(linear|spline).
- 커널 인터페이스 확장: 입력을 `{dist, params, port}` 로 실어 **상류 노드 params(depth)** 를 커널이 읽음.
  `evaluate._compute` 가 node_meta 로 상류 params 를 붙여 전달.
- fixture 갱신: age-depth-model(method linear/spline + target_depth), 데이터 노드(depth).

### 커널 (`engine/kernels.py`)
- `age_depth_model` — dated_horizons 에서 (depth, age) 수집 → target_depth 연대 보간.
  - **linear**(기본, 해석적): 브래킷 구간 선형 보간. 불확실성 = 두 점의 선형결합 분산
    `(1-t)²σ₁² + t²σ₂²` — 외삽 시 t∉[0,1] 로 분산 증가.
  - **spline**: scipy `CubicSpline` 평균 + **MC 전파**(각 horizon 정규 샘플, 매 draw 스플라인 적합 후
    target 평가, 시드 고정 결정론적) → shape/decomposed 요약.
  - 폴백: depth 없음 → pass-through, target 없음 → 결합, horizon 1개 → 그 값.

## 검증
- **pytest 59 passed**(age-depth 단위 6 + evaluate 통합 1).
- **live**: horizons(0→250, 10→256, 20→262 Ma, 2σ0.5) → linear t=5 **253.0**(2σ0.354, 보간 축소) /
  t=15 **259.0** / spline t=15 **259.004**(2σ0.419) / linear t=30 **268.0**(외삽, 2σ1.118 증가).

## 스택 / 배포
- numpy/scipy(023 에서 추가) 사용. 배포 시 이미지 재빌드 필요(023 주의 동일).

## 다음
- 단조(superposition) 검사·경고 / 베이지안 age-depth(별도 워커) / correlation tier 다봉 / 결과 뱃지에 method 표시.

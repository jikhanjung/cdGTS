# 20260703_023 — 계산 커널 착수 (engine.kernels)

> P01 후속. engine pass-through → **NodeType별 실제 계산 커널** 프레임워크 + 첫 진짜 커널들.
> 설계 [app-architecture §2.4](../docs/app-architecture.md)("커널은 engine 에 코드, slug 로 바인딩").

## 한 일

### 프레임워크 (`engine/kernels.py`)
- **레지스트리**: `slug → 커널 함수`. 미등록 slug 는 **pass-through 폴백**(첫 입력 통과).
- `compute(category, slug, inputs, params)` 디스패치. `moments`(분포→(mean,1σ): budget/shape/exact 처리) ·
  `dist_from`(mean,1σ→분포 dict).

### 진짜 커널 (이번 증분, 결정론적·해석적)
- `joint-inference` · `cross-section-correlation` — **역분산 가중 결합**(독립 추정 결합). 정밀한 입력이 큰 가중,
  결과 불확실성 축소. exact 입력이 있으면 지배(pin). 신호(None)는 제외.
- `range`(clamp) — **절단정규**(scipy `truncnorm`)로 분포 재성형(평균 이동 + 분산 축소). exact 는 구간 clip.
- `pin`(clamp) — exact(value) (GSSA 점질량, 기존 유지).
- age-depth-model·calibration-transfer·order·freeze-version — pass-through(깊이-연대 데이터/실제 모델은 후속).

### evaluate 연결
- `_compute` 를 `kernels.compute` 디스패치로 교체(입력 분포를 포트순으로 모아 전달). 증분 캐시·provenance·순환 처리 유지.

## 검증
- **pytest 52 passed**(kernels 단위 12: moments·결합 축소·정밀 가중·exact pin·절단·디스패치).
- **live**: U-Pb 251.9±0.4 + 252.3±0.4 (2σ) → joint 결합 **252.1 ± 0.283**(=0.4/√2). 불확실성 실제 축소.
- 기존 pass-through 테스트 유지(age-depth-model 폴백).

## 스택 / 배포 주의
- requirements: **numpy 2.2.6, scipy 1.15.3** 추가. in-process 계산(무거운 MCMC/PyMC·별도 워커는 후속).
- **배포 주의**: 현재 pushed `honestjung/cdgts:0.1.0` 는 numpy/scipy 없음. 이 커널을 배포하려면 **이미지 재빌드**
  (예 0.2.0). 기존 0.1.0 컨테이너는 구 코드라 정상.

## 다음
- age-depth-model 실제 커널(깊이-연대 노드 데이터 모델 확장 필요) / MC 전파(비선형·비대칭) /
  joint 공분산 추적 / 별도 과학 스택(PyMC·Celery) 분리 / 결과 뱃지에 계산 표시.

# 20260705_066 — ICC 차트 불확실성(±) 표현

> distribution 의 오차예산/sigma 가 데이터엔 있는데 차트엔 안 보였다(GTS 의 핵심이 불확실성).
> 각 하부경계의 대칭 오차 ±pm 를 차트에 밴드·툴팁으로.

## 한 일

### 백엔드 (`releases/views.py` — 마이그레이션·시드 무관)
- `_pm_from_dist(dist)` — distribution → 대칭 ±pm(Myr). exact(GSSA 약속값)=0, 예산 sqrt-합, shape=HPD 반폭.
  (ResultsPanel.summarizeDist 와 같은 사다리.)
- `build_icc_levels(unit_base, unit_unc=None)` — 밴드에 `pm`(경계 base 오차) 첨부.
  그래프 뷰는 평가 결과 distribution 에서, 릴리스 뷰는 `BoundaryRecord.uncertainty` 에서 pm 산출.

### 프론트 (`IccChart.jsx`)
- **± 불확실성** 토글 — 켜면 각 하부경계의 오차 밴드([base−pm, base+pm], 최소 2px)를 컬럼 위 반투명 오버레이로.
  경계는 여러 rank 공유 → base 로 dedup. 밴드 툴팁에 `± pm Ma`(GSSA 는 "약속값") 상시 표기.

## 결과
- 공표 ICC: 102 경계 오차>0(예: Triassic ±0.024·Jurassic ±0.2·Mississippian ±0.19), 75 약속값(GSSA/exact)=0.
- 전 스케일에선 오차가 작아 가는 밴드지만, 툴팁·토글로 GSSP 파생연대의 불확실성을 드러냄.

## 검증
- `pytest` **85 passed**(pm: GSSP>0·GSSA=0). 프론트 빌드 클린. **마이그레이션·재시드 불필요**(기존 오차 데이터 사용).

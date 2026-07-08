# 20260708_116 — P06.1 공분산 백본 (Distribution L4 실사용)

[P06](20260708_P06_arc-a-science-engine.md) 1단계. 공유 계통 성분을 실어 나르고, 지속시간 공분산을 해석적으로
재구성 — MCMC 없이 duration 오차를 정직하게. **엔진 내부 변경(사용자 가시 변화 없음 — 게이트 배선은 P06.2).**

## 표현 (nodes/distribution.py)

- `shared_components: [str]` → **`[{ref, sigma}]`** — 공유 계통원별 1σ 기여(Ma). 문서의 "태그만으로 충분한가"
  열린 질문을 **성분별 σ** 로 해소.
- `component_sigmas(d) → {ref: σ}` · **`covariance(a, b) = Σ_{공유 ref} σ_a·σ_b`**(완전상관 가정, 희소).

## 전파 (engine/kernels.py)

- `dist_from(mean, σ, shared=)` — shared 있으면 **L4 `joint`** 로 승격.
- `inverse_variance_combine` — 공유 성분을 가중 전파(out σ[ref] = Σ_i w_i·σ_i[ref]). (marginal σ 는 독립 가정이라
  공유 시 약간 과소 — 완전상관 결합은 P06.4.)
- `_linear_age_depth` — 보간 가중((1−t)·, t·)으로 두 horizon 의 공유 성분 결합.
- `range_clamp` — 절단 σ 비율만큼 공유 성분 축소. pass-through/pin/boundary/leaf 는 dict 그대로라 자동 보존.
- (spline/MC 경로 공유성분 전파 = 06.1b — MC라 06.4와 함께.)

## 지속시간 헬퍼

- **`duration_stats(older, younger)`** → (dur, 1σ), `Var = Var(o)+Var(y)−2·Cov`. Var 음수는 0 으로 바닥(√ 안전).
  P06.2 게이트(L2)가 이걸 소비.

## 검증

engine/test_kernels.py +8 (covariance·duration 축소·전파·round-trip·pass-through 보존). 전체 **pytest 125 passed**.

## 다음 (P06.2)

`duration_stats`/`covariance` 를 `_certify` 에 배선: L0 실검사 · L1b(2σ 겹침 warn) · L2(공분산 duration, ≤0 fail /
2σ 누출 warn). ICC/Verify ± 밴드에 경고 노출.

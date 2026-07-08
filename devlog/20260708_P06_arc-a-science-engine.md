# 20260708_P06 — 아크 A: Science Engine 심화 (계획)

R01이 꼽은 미착수 두 아크 중 C(멀티유저 CI)를 P04+P05로 완주. 남은 **A(과학 엔진 심화)** 착수.

## 현재 상태 (탐색 실측)

- **진짜 수치 커널은 age-depth(선형 + spline/MC) · range(truncnorm)뿐.** 나머지 process 노드는 pass-through.
- **`joint-inference` = 역분산 가중합 스텁** — 입력을 서로 **독립**으로 취급, 공분산 무시(`kernels.py:53`).
- **Distribution L4(`shared_components`) · L5(`posterior_ref`)는 필드만 있고 아무도 안 씀** — 엔진 구조상 공분산 불가.
- **정합성 게이트**: L0 하드코딩 pass · L1a 실동작(+게이트웨이 연대순 fallback 스텁) · L2 점추정 duration>0(± 없음).
  **L1b · L2-warn · L3 전무** (`evaluate.py:119` `_certify`).
- **경쟁 모델**: 저장 + P05.5 override picker + bake=한 후보 복사. envelope/BMA · 전역 정합 · Clamp 배선 없음.

문서(distribution-representation · coherence-gate · cycles · competing-models)가 이미 답을 갖고 있음.

## 설계 관점 — 순서를 가르는 핵심: **공분산 먼저**

가장 화려한 목표는 PyMC 베이지안이지만, 가치의 대부분은 **공분산**에 있다.
`duration = old − young` 인데 두 경계가 **공유 계통오차**(같은 붕괴상수·tracer·age model)를 쓰면 그 오차는 차이에서
상쇄된다 — `Var(dur) = Var(old) + Var(young) − 2·Cov`. 현재 엔진은 Cov=0(독립)이라 duration 오차를 **과대평가**.

이 Cov는 **MCMC 없이 해석적으로** 얻는다: 계통 성분에 태그+σ를 실어 전파하고, 지속시간 계산 때 공유 태그로 희소
공분산 재구성(distribution-representation.md가 제시한 길; "태그만으로 충분한가"라는 열린 질문을 **성분별 σ**로 해소).
→ **무거운 인프라 0으로 게이트를 진짜로 만들고 duration을 정직하게.** PyMC는 cycles.md 스스로 "authored clamp가 더
정직한 reconcile"이라 하므로 **마지막에, 좁게**.

## 단계

### P06.1 — 공분산 백본 (Distribution L4 실사용) · 난이도 中 · 의존성 없음 · 기반
- `shared_components: [str]` → **`[{ref, sigma}]`**(공유 계통원별 1σ 기여, Ma). L4 `joint` fidelity 실사용.
- 전파: leaf(authored) → pass-through(보존, 이미 됨) → `inverse_variance_combine`(가중 전파) → `_linear_age_depth`(보간
  가중 전파). `dist_from` 이 shared 실어나름.
- `Distribution.covariance(a, b)` = Σ_{공유 ref} σ_a·σ_b (min 클램프로 Var(dur)≥0 보장). `duration_stats(old, young)`.
- 산출물: 분포가 공유-계통 구조를 나름 + 공분산/지속시간 헬퍼. 신규 인프라 0.
- (후속 06.1b: spline/MC 경로 공유성분 전파 — MC라 06.4와 함께.)

### P06.2 — 공분산 인지 정합성 게이트 (L0 실装 · L1b · L2-with-±) · 난이도 中 · P06.1 의존
- **L0**: 게이트에서 구조/비순환 실검사(현재 하드코딩 pass).
- **L1b**: 인접 경계 2σ 구간 겹침 → WARN("순서 통계적으로 미해결").
- **L2**: `Var(dur)=Var(old)+Var(young)−2Cov`(P06.1). 점 ≤0 FAIL, 2σ 내 P(dur≤0) WARN. ICC/Verify ± 밴드에 경고 배선.

### P06.3 — L3 reconcile = authored Clamp 배선 · 난이도 中上 · P06.2 의존 · Arc B 접점
- **L3a verify**(값 불변 = ICC/bake 계약) 공식화 · **L3b reconcile**(값 이동 = GTS/narrate 계약).
- 문서 권고대로 자동 joint 대신 **`releases.Clamp`(owner·target·pin/range/order/freeze)를 평가·게이트에 배선** — 적용·충돌중재.
  P05 거버넌스(ratify) 재사용.

### P06.4 — 진짜 베이지안 joint 커널 (PyMC + 비동기 워커) · 난이도 高 · 위험 최대 · 마지막/선택
- `joint-inference` 스텁을 **국소 상호제약 클러스터**(cycles.md)의 실제 결합 사후분포로 교체 → "공짜로" 공분산,
  L5 `posterior_ref` 실사용. 인프라: PyMC 의존 + **별도 워커**(동기 평가에 MCMC 못 넣음 — 큐/워커 도입이 실 스코프).

### P06.5 — 경쟁 모델 envelope/BMA + 전역 정합 · 난이도 中 · Arc B 성격 · 선택
- select-one 옆 **envelope/BMA**(competing-models §4). **전역 후보 정합**(경계를 서로 다른 global 모델서 섞지 않기)을 게이트에 연결.

## 권고 경로

**P06.1 → 06.2 → 06.3** = "정직한 불확실성" 핵심 아크(전부 해석적·배포 가능·신뢰도 급상승).
**06.4(PyMC 워커)** 는 06.1–06.3 본 뒤 별도 결정하는 무거운 마일스톤, **06.5** 는 Arc B 인접.

**캡스톤 데모**(R01 §E): Cryogenian **GSSA→GSSP retype** — scalar→분포, 공유성분 duration, clamp reconcile을 한 번에
검증하는 end-to-end. 06.1–06.3 완료 시 검수 시나리오.

## 결정 (확정)
1. **해석적 공분산 먼저** (PyMC는 06.4로 지연) — 가치 대부분 확보, 인프라 0.
2. **reconcile = clamp-authored** (자동 joint 아님) — 문서 권고 + 거버넌스 재사용.
3. **공유성분 = 성분별 σ 태그** — 문서의 "태그만으로 충분한가" 열린 질문을 성분별 σ로 해소.

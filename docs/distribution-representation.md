# 분포 표현

*[English](distribution-representation_en.md) · 한국어*

> 상태: **검토 → 스키마에 반영.** [boundary-gateway-schema.md](boundary-gateway-schema.md) §4의 마지막 열린
> 질문("분포 표현")을 펼친 것. [node-graph-paradigm.md](node-graph-paradigm.md)의 *"엣지가 분포를 흘린다"* 의 구체화.

## 1. 재프레이밍 — "± vs HPD 입도"가 아니다

세 개의 서로 다른 난제가 겹쳐 있다: 불확실성이 (A) **구조화**돼 있고, (B) **가우시안이 아니고**, (C) 근본적으로
**결합(joint)** 이다.

## 2. A — 불확실성은 분해된 예산(budget)이다

경계 연대의 오차는 성분이 여럿이고 뭉치면 안 된다:

- **분석(analytical)** — 실험실 측정오차 (P–T의 ±0.024).
- **계통(systematic)** — 붕괴상수·tracer 보정. **여러 경계에 공유** → 상관됨.
- **모델(epistemic)** — 어느 age-depth/상관 모델 (competing-models 축).
- **보간/상관** — 경계가 датable 층에 없어 전이로 붙는 오차.

발명이 아니라 **실제 관행**이다. CA-ID-TIMS 논문(우리 P–T 사례 Burgess 2014 포함)은 연대를 **`± X / Y / Z`**
(분석 / +tracer / +붕괴상수)로 보고한다 — *무엇과 비교하느냐*에 따라 넣을 성분이 달라지기 때문(같은 U-Pb끼리
→ 분석만; U-Pb vs Ar-Ar → 계통까지).

**결정적 연결:** 두 경계의 오차 상관 여부는 *계통 성분 공유 여부*로 정해진다. 즉 이 분해 예산이 곧
[정합성 게이트](coherence-gate.md) L2가 요구한 **공분산 정보**. → **분포 표현과 정합성 공분산은 같은 문제의
양 끝.** 단일 `plus_minus`로는 둘 다 못 한다.

## 3. B — 분포는 가우시안·대칭이 아니다

`± 2σ`는 대칭 정규를 가정하는데:

- 베이지안 age-depth 사후분포는 흔히 **비대칭**(95% HPD ≠ 평균±2σ).
- 상관 전이는 경쟁 가설이 둘이면 **다봉(multimodal)**.
- competing-models 포락은 **혼합(mixture)**.

표현 선택지(값싼→비싼): 점+대칭σ → 점+비대칭 HPD(중앙값·95% 하/상한) → 파라메트릭(skew-normal) →
분위수/CDF → 사후 샘플 참조 → 재실행 가능한 **생성 모델**.

## 4. C — 진짜 객체는 marginal이 아니라 joint다 (가장 깊은 층)

- **지속시간 = 상관된 두 경계의 차** → joint(공분산) 필요.
- **단조 순서는 결합 제약** → 참 사후분포는 독립 marginal의 곱이 아니라 **순서로 절단된 joint**.

관심의 진짜 대상은 **모든 경계 연대에 대한 결합 사후분포**이고, 경계별 marginal은 그 **손실 있는 투영**이다.
이 joint가 [cycles.md](cycles.md)의 **동시추정 노드가 공짜로 내주는 결합 사후분포**와 같다.

## 5. "bake"의 충실도 사다리 (L0–L5)

| 층 | 표현 | 쓰임 |
|---|---|---|
| **L0 점** | 숫자만 (251.902 Ma) | ICC 헤드라인 |
| **L1 대칭 ±** | value ± 2σ(분석) | (구) 스키마 |
| **L2 분해 예산** | ± 분석 / +계통 / +모델 | 비교·**공분산** |
| **L3 모양** | 중앙값 + 비대칭 HPD / 파라메트릭 | 왜곡·다봉 |
| **L4 joint 요약** | marginal + 공분산(또는 공유성분 태그) | **지속시간·순서** |
| **L5 완전 사후** | 샘플 참조 / 재실행 생성 모델 | 무엇이든 (무겁고 provenance 필요) |

이 사다리는 게이트 L0–L3, cycles의 provenance-상한과 **평행**하다. 한 경계가 노출 가능한 **분포 충실도는
provenance의 기계가독 깊이가 상한**을 정한다 — "발표값+출처"뿐인 레거시는 L0–L1, 완전 모델링은 L5.
→ **분포 표현·정합성 레벨·순환 해소가 모두 같은 provenance 깊이에 종속.** ICC(bake)는 중간 rung을 얼리고,
GTS(narrate)는 L5를 참조.

### 5.1 decomposed vs joint — 구현과 직관 (P06)

사다리에서 가장 자주 헷갈리는 두 rung. **decomposed(L2)는 한 경계의 marginal, joint(L4)는 경계들 사이 상관까지.**

**저장 형식** (`nodes/distribution.py` · `engine/kernels.py`):
- **`decomposed`** = `budget: {analytical, systematic, model}` + `sigma`(budget 값이 몇 σ로 적혔나). 1σ 환산은
  `√(Σ budget²) / sigma`. 성분은 **크기만** 있고 *어느 공유원*인지 이름표가 없다.
- **`joint`** = 여기에 `shared_components: [{ref, sigma}]` 를 더한 것. 각 태그 = *"내 오차 중 σ만큼이 이 공유원
  (예: `decay-238U`)에서 왔다."* marginal(자기 1σ)은 decomposed와 **동일**하고, 공유 정보만 추가된다.

**차이가 지속시간에서 갈린다.** `Var(dur) = Var_a + Var_b − 2·Cov`, `Cov = Σ_(공유 ref) σ_a·σ_b`.
- decomposed끼리 → 공유 ref 없음 → `Cov=0` → 오차를 그대로 제곱합(**독립 가정**).
- joint끼리(같은 ref) → `Cov>0` → 그만큼 **차이에서 상쇄**.

**"독립 측정 ≠ 독립 오차" (핵심 직관).** 두 연대를 따로 측정해도 **붕괴상수·tracer 보정**은 두 계산에 **같은
값**으로 들어간다. λ이 틀리면 두 연대가 **같은 방향으로 함께** 밀린다 → **절대연대**엔 그대로 영향, **차이
(지속시간)**엔 거의 영향 없음. 그래서 공유 계통분은 duration에서 상쇄되고 남는 건 각자 고유한 **분석오차**뿐.
(EARTHTIME `±X/Y/Z` 표기의 제도화: 같은 시스템 비교=X 분석만, 절대·타 시스템 비교=Z 붕괴상수까지.)

**데모 숫자** (`seed_demo`, 인접 두 Age 경계, 각 1σ=1.5):
- joint면 그중 **1.4**가 `decay-238U` 공유, `√(1.5²−1.4²)=`**0.54**가 고유 분석오차.
- decomposed(독립): `σ_gap=√(1.5²+1.5²)=`**2.12** → 2σ 4.24.
- joint(공유): `Cov=1.96` → `σ_gap=√(0.54²+0.54²)=`**0.76** → 2σ 1.52. **같은 간격이 warn→pass로 뒤집힌다.**

**언제 joint로 태그하나 (모델링 주장).** `joint` 태그는 *"이 두 연대는 같은 계통원을 쓴다"*는 **과학적 주장**이다 —
참일 때만 상쇄가 정당. 서로 다른 방법(U-Pb vs Ar-Ar, 다른 λ)이면 공유하지 않으니 **decomposed로 두는 게 맞다**
(→ 독립, 상쇄 없음). 또 이 모델은 태그된 성분을 **완전상관(r=1)**으로 가정한다(`Cov=σ·σ`). 그래서 그 판단을
데이터 제공자에게 맡긴다. → [coherence-gate.md](coherence-gate.md) L1b/L2, [tutorial-science-engine.md](tutorial-science-engine.md).

## 6. GSSA/clamp와의 통일 — 결정값은 퇴화 분포다

GSSA = 정확 = **δ(2500)**, 분산 0의 **점질량(point mass)**. 다형 value가 이를 자연히 포함(`fidelity: exact`).
그리고 **clamp는 분포 연산자**다:

- **pin** = δ로 붕괴, **range** = `[min,max]` 절단, **order** = 순서 영역 절단.

→ [cycles.md](cycles.md)의 clamp와 분포 표현이 한 뿌리로 봉합된다.

## 7. canonical rung — ICC가 얼리는 정본 층

**rung** = 충실도 사다리의 단(段). **canonical rung** = ICC가 "모든 경계를 이 층으로 얼려 배포한다"고 정하는
**공식 표준 충실도 단**. 두 힘이 당긴다: **자기완결적 인용**(낮은 rung — 릴리스만으로 재현) vs **충실도**
(높은 rung — joint는 전체 집합/재실행 필요).

잠정 방향(결정 아님): **경계 레코드의 정본 = L2(분해 예산) + 가능하면 L3(모양)** — 자기완결·인용 가능.
**joint 구조(L4)는 경계가 아니라 [릴리스 층](versioning-global-vs-per-boundary.md)에** 공유성분 태그/희소
공분산으로 보존, 지속시간 계산 시 재구성. (대부분 경계쌍은 무상관이므로 N×N 대신 희소.)

## 8. 스키마 반영

`age.uncertainty`를 단일 `plus_minus` → **구조화된 분포**:

```yaml
uncertainty:
  fidelity: exact | sym | decomposed | shape | joint | full
  sigma: 1 | 2                 # budget 값의 신뢰수준
  budget: { analytical, systematic, model }   # 분해 예산; 계통 공유 = 공분산 열쇠
  shape: { median, hpd95: [lo, hi] }?          # 비대칭/왜곡 (없으면 대칭 가정)
  shared_components: [node_ref]                # 공유 계통 노드 (joint 재구성)
  posterior_ref: sample_ref | model_ref?       # L5: 샘플/재실행 모델
  note: string?
# 결정값(GSSA/pin) = { fidelity: exact } (점질량). ICC 정본 rung ≈ L2/L3;
# joint 구조(L4)는 릴리스 층에 공유성분 태그로 보존.
```

## 9. 남는 열린 질문

- **모델 간 다봉을 분포에 담을지, selection 층으로 뺄지** (내부 오차 = 분포 / 모델 간 = competing-models
  포락, 분리 유지가 깔끔).
- **사후 샘플의 저장·버전** (무거움 → 참조, 임베드 금지).
- **레거시 `± 2σ`뿐 데이터**의 우아한 저하(L1로).
- **희소 공분산 재구성**의 정확도 — 공유성분 태그만으로 충분한가.

## 10. 링크

- [boundary-gateway-schema.md](boundary-gateway-schema.md) §2 (`age.uncertainty`) · §4
- [coherence-gate.md](coherence-gate.md) — L2 공분산(= 분해 예산) · [cycles.md](cycles.md) — 동시추정 joint · clamp=분포 연산자
- [competing-models.md](competing-models.md) — 모델 간 포락(다봉) · [node-graph-paradigm.md](node-graph-paradigm.md) — 엣지=분포

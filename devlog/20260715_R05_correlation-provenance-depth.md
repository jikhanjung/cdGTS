# 20260715_R05 — 여러 섹션의 연대를 합치는 과정을 cdGTS 에 어느 깊이까지 구현할까

> 성격: **검토(scope/altitude).** `docs/statistical_procedures_summary.md`(Agterberg·Hammer·Gradstein 2012,
> GTS2012 Ch.14 요약)를 cdGTS 관점에서 읽는다. **[R04](20260711_R04_radiometric-provenance-depth.md) 의 자매편** —
> R04 가 "**방사연대** provenance 를 어느 깊이까지"였다면 본 문서는 "**상관(correlation)** provenance 를 어느 깊이까지".
> 두 문서의 원전도 같은 책의 자매 장이다(Ch.6 ↔ Ch.14).
>
> 결론: R04 와 **같은 모양의 답**. 재설계가 아니라 **한 프리미티브(`tie-point` = 상관 가설 노드)만 1급으로** 올리는 것이
> 적정선. Ch.14 의 spline/SF/LOOCV/MC 는 **대부분 구현 대상이 아니다.** 킬러 유스케이스는 계산이 아니라
> **엣지 토글**(§5)이고, **그 요구가 composite 척도를 authored leaf 가 아니라 derived 노드로 밀어낸다**(§6·§10).
> CONOP 여부는 **난이도가 아니라 필요성**으로 결정한다 — 커널은 trivial 로 시작하고 노드 경계만 지금 맞춘다.

## 1. 먼저 — 이 챕터는 "섹션 합치기"를 설명하지 않는다

Ch.14 의 스플라인은 **x축이 이미 하나로 합쳐져 있다고 전제**한다. 입력은 (composite 상대 층서 위치, 방사성연대)
쌍이고, 여러 섹션을 공통 상대척도로 통합하는 작업(graphic correlation·CONOP)은 **Ch.3 의 일**이다 —
즉 "섹션 합치기"는 이 장이 **푸는** 문제가 아니라 **전제하는** 문제다.
챕터 스스로 흘린다 — §4.3("초기 상대척도는 시간에 대략 비례해야") · §19.1("초기 상대척도가 최종 spline 에 영향") ·
§26("Ch.3 의 composite biochronology 와 결합하면").

두 아키텍처가 **정반대**다:

| | 무엇을 합치나 | 구조 |
|---|---|---|
| **cdGTS (P07)** | **답** | 섹션마다 독립 age-depth → 스칼라 → 역분산 가중평균 |
| **Ch.14 (GTS2012)** | **증거** | 전 섹션의 전 연대를 한 composite x축에 → 스플라인 1개 → 경계 위치에서 read-off |

차이는 실질적이다. 증거를 합치면 경계에서 먼 정밀 연대도 age model 을 통해 경계를 제약하지만, 답을 합치면
그 정보 공유가 없다. 그리고 Ch.14 는 한 번의 적합으로 **모든 경계를 서로 상관된 채** 동시에 낸다 — §16.5 의
duration 논의가 성립하는 이유다.

> **따름정리**: composite 상대척도 없이는 Ch.14 의 방법 자체를 들일 수 없다. 그게 이 검토의 1차 결론이다.

## 2. 현재 구현 실측 (2026-07-15 · 0.1.64 · 코드 확인)

- **`cross-section-correlation` = `inverse_variance_combine` 한 줄**(`engine/kernels.py:289` → `:58-76`).
  `joint-inference` 와 **동일 커널**이고 note 문자열만 다르다. 역분산 가중평균 — 선택도 bracket 도 아니다.
- **분산 검정 0건.** `mswd|chi2|dispersion|scaled_residual` grep = 코드 0 히트. 결합의 goodness-of-fit 게이트가 없다.
  - 실증(커널 직접 실행): `538.8±0.2` + `542.0±0.2` → **`540.4`, 1σ=0.14**. 3.2 Ma 어긋난 두 섹션이 경고 없이
    평균되고, **어느 섹션도 지지하지 않는 값**이 **입력보다 좁은 오차막대**로 나온다.
  - 공정하게: **현 예제 데이터는 건강하다**(세 섹션 MSWD ≈ 0.55 — Ch.14 §6.2 의 "Paleozoic 은 SF<1 이 흔함"과 부합).
    문제는 지금 숫자가 틀렸다는 게 아니라 **게이트가 없다는 것**.
- **composite 상대척도 0건.** `horizon.depth` 는 명시적 섹션 로컬 좌표(seed help = *"Distance from section base"*).
  Oman 108 · Namibia 195 · Siberia 48 — **서로 비교 불가능한 단위**이고 공통 프레임 사상 노드·필드가 없다.
  graphic correlation/CONOP/composite 구현 0건(히트는 전부 docs 의 ambition).
- **상관은 계산되지 않고 저자가 배선으로 주장한다.** δ13C 근거는 `horizon.datum` **문자열** + `correlation_via`
  **주석 param** 뿐 — **어떤 커널도 읽지 않는다**. `synthesis` 의 `signals` 포트는 시드 전체에서 **한 번도 배선된 적 없다**.
- **Ch.14 의 통계 장치는 전부 부재.** `_spline_age_depth`(`:192-206`)는 `scipy.interpolate.CubicSpline` =
  **보간 스플라인**(smoothing 아님). SF 없음 · LOOCV 없음 · 단조 제약 없음.
- **MC 는 한 곳뿐** — `_spline_age_depth`, n=3000 하드코딩, `default_rng(0)` 고정, **연대만 샘플하고 depth 는 상수**.
  즉 Ch.14 §5.2 가 "Paleozoic 에선 σ_x 가 σ_y 보다 클 수도 있다"고 한 **더 큰 항이 통째로 빠져 있다**.
- 🐛 **버그**: `_spline_age_depth` 가 horizon 튜플의 `comps`(4번째 원소)를 **아예 읽지 않고** `_summarize_samples`(`:151-163`)도
  `shared=` 를 안 넘긴다. linear 경로는 `_blend_components` 로 보존하는데 → **`method="spline"` 을 고르면 공분산
  백본이 조용히 끊기고 하류 duration 공분산이 0 이 된다.** 보간 방법 선택이 공분산 의미론을 바꿔선 안 된다.
  → ✅ **수정됨** (2026-07-15 — 본 문서 말미 Addendum).

## 3. 적정 깊이 판별 규칙 (R04 규칙 재적용)

> **"이걸 바꾸면 하류 경계 연대(또는 그 상관구조)를 다시 계산해야 하나?"** — 그렇다 → 노드/의존. 아니다 → cite 만.

- **모델링한다**: BACE 상관 가설(이 excursion = 저 excursion?) · tie-point 의 depth 범위 · composite 척도 버전 ·
  경계의 composite 위치(GSSP 마커의 상관).
- **모델링 안 한다**: CONOP 내부 seriation · 스플라인 계수 · SF 탐색 과정 · MC replicate 개별 draw ·
  δ13C 곡선의 원시 측정점. → 논문 cite 또는 노드 내부 구현 디테일.

## 4. 그래프 레벨 load-bearing = 딱 하나 — `tie-point`

R04 에서 붕괴상수에 했던 것과 **정확히 같은 수**다. 물리적으로 하나인 것이 그래프에 하나의 노드로 있으면 공유
구조가 공짜로 따라온다.

**`tie-point`** = 상관 가설을 1급 시민으로. 두 가지를 자연스럽게 싣는다:

1. **양쪽 섹션의 depth 좌표 + 불확실성** — 본질적으로 **rectangular**("이 구간 어딘가", 가우시안 아님).
   Ch.14 §5.3 의 uniform(σ_x = q/√12 ≈ 1.15q/4)이 **자동으로 등장**한다. 억지로 넣는 게 아니라 이 프리미티브의
   자연스러운 타입이다.
2. **`cite` 엣지** — 상관 주장의 근거 논문. 기존 `reference` 노드가 그대로 붙는다(devlog 127).

효과:

- 세 섹션이 **같은 BACE tie-point 를 공유** → 그 상관이 틀리면 세 섹션이 **같은 방향으로** 움직인다는 사실이
  위상에 기록된다. 지금은 독립 평균이라 σ 과소 — 커널 docstring(`:62`)이 자인하고 P06.4 로 미뤄둔 그 부채가,
  **별도 수정이 아니라 위상으로** 해소된다.
- **상관이 논쟁 가능해진다** → §5.

## 5. ★ 킬러 유스케이스 — 상관 가설을 클릭으로 켜고 끈다

본 검토의 핵심이자, R04 의 "상수 바뀌면 전체 재계산이 공짜"와 **같은 구조의 논지**. 다만 이번엔 **값이 아니라 위상**이다.

**시나리오**: 어떤 섹션의 동위원소 excursion 이 BACE 에 해당하는지 **논란이 있다**(실제로 흔한 상황).
cdGTS 에서는 — **모든 섹션의 데이터 노드를 다 만들어 놓고, tie 도 다 걸어 놓고, 특정 섹션만 연결했다 뺐다를
클릭 몇 번으로** 한다. "Siberia 의 excursion 이 BACE 가 아니라면?" → 엣지 하나 끊고 → 재평가 → diff.

이건 기존 자산 위에 **정확히 얹힌다**:

- **[topology-diff](../docs/topology-diff.md)** — "값 diff 와 직교하는 구조 diff". 엣지 토글 = 구조 변경이고,
  값 이동은 그 결과다. 이 문서가 왜 필요한지의 **실전 답**이 여기 있다.
- **[competing-models](../docs/competing-models.md)** — "네트워크 복수 후보 + 릴리스 선택". 상관 가설 A/B 가 곧 후보.
- **P05 fork/propose/ratify** — "Siberia 를 뺀 모델"이 그대로 **Proposal** 이 된다. 과학을 위한 CI 그 자체.
- **증분 content-hash 평가** — 엣지 하나 끊으면 하류만 dirty → 원클릭 diff("이 N개 경계 이동").

**Ch.14 는 이걸 못 한다.** 일회성 배치 적합이라, 자료를 넣고 빼려면 스크립트를 다시 돌리고 결과를 손으로 비교해야
한다. 챕터가 §18.7 에서 자랑하는 "재현 가능성"(입력+알고리즘 공개 시 재계산 가능)은 cdGTS 기준으로는 **최소한**이다.
cdGTS 가 파는 건 재현이 아니라 **탐색**이다.

> **이게 `tie-point` 를 노드로 만들어야 하는 결정적 이유다.** 상관이 `datum` 문자열로 남아 있으면 **토글할 대상이
> 없다.** 지금 구조에서 "Siberia 를 빼 보기"는 노드를 지우고 되돌리는 파괴적 편집이지, 가설 비교가 아니다.

## 6. 레벨별 권고

**L1 (이번 아크)** — 상관을 1급으로:
- `tie-point` NodeType(rectangular σ_x + cite) · `composite-scale` **derived 노드** · `age-model` 노드(N→M).
- **composite 는 authored leaf 가 아니라 derived 여야 한다** — §5 가 그렇게 요구한다. 근거는 §6.1.
  단 커널은 **trivial 로 시작**한다(§6.2): 노드 경계만 지금 맞추고 seriation 은 필요해질 때.
- **`cross-section-correlation` 은 소멸**한다 — composite + age-model 이 있으면 "섹션별 답을 평균" 단계 자체가
  존재 이유를 잃는다. clamp 축소와 같은 종류의 정리. (단 `joint-inference` 는 **산다** — 같은 ash bed 를 두 실험실이
  측정한 것처럼 *같은 양의 독립 추정*을 합치는 건 정당하다. 죽는 건 커널이 아니라 **섹션 상관에의 오용**이다.)

### 6.1 authored composite 는 §5 를 깨뜨린다 (초안 자기수정)

본 문서 초안은 "composite = authored leaf(GSSA 선례)"를 권고했다. **틀렸다.** §5 와 정면 충돌한다:

> composite 가 authored leaf 면 **tie 엣지를 토글해도 composite 가 갱신되지 않는다.** 전파가 죽고,
> §5 의 킬러 유스케이스가 성립하지 않는다. 게다가 "Siberia 를 뺀 composite"는 이미 authored 된 composite 와
> **모순된 상태**가 된다.

우회로는 있다 — 가설마다 composite 를 하나씩 authored(A=Siberia 포함 / B=제외) 하고 릴리스가 고르는 것
([competing-models](../docs/competing-models.md) 의 복수 후보). 하지만 **N 개 tie 에 2^N 개 composite 를 손으로
저작**해야 한다. tie 를 토글해 composite 를 **유도**하면 그게 공짜다. → **derived.**

**GSSA 선례가 여기 적용되지 않는 이유**: 붕괴상수·GSSA 는 cdGTS **바깥**에서 정해져 들어오는 값이라 leaf 가 맞다.
composite 는 **cdGTS 가 이미 노드로 갖고 있는 tie-point 들의 하류**다. 그걸 authored 로 두면 그래프에 계산이
있어야 할 자리에 구멍이 남는다. R04 의 결론을 기계적으로 복사한 게 실수였다.

**단, authored composite 도 산다** — 공표된 CONOP run(논문)을 인용해 후보로 두는 용도. 이건 정확히 **ICC 릴리스의
published vs bake 이중성** 그대로다: 공표 composite 와 유도 composite 가 후보로 공존하고 릴리스가 고른다.

### 6.2 CONOP — 필요성으로 결정한다, 난이도로 결정하지 않는다

초안은 "CONOP 은 큰 일이고 cdGTS 의 강점이 아니다"라고 썼다. **난이도 논거는 철회한다.** 알고리즘 자체(사건 순서에
대한 제약 최적화 / simulated annealing 계열 seriation)는 원칙만 알면 구현이 큰 문제가 아니고, 병렬화 계열 후속 작업까지
갈 필요도 없다. 필요하면 **저자와 직접 협업하는 경로도 열려 있다**(사용자 면식). 난이도는 이 결정의 축이 아니다.

진짜 축은 **필요성**이고, R04 의 altitude rule 도 애초에 그 기준이었다. 그리고 답은 **규모에 따라 갈린다**:

- **단일 tie 문제**(P07 base-of-Cambrian: 세 섹션이 BACE 한 지점에서 묶임) → **composite 가 trivial 하다.**
  tie 가 곧 상관이고 seriation 할 것이 없다. **CONOP 불필요.**
- **다중 사건 문제**(Ordovician graptolite composite — Ch.14 §3.3 의 Cooper) → 사건들의 **순서 자체가 불확실**해서
  seriation 이 진짜 계산이 된다. **그때 CONOP 이 필요해진다.**

→ **결론: `composite-scale` 노드를 지금 만들되 커널은 trivial(ties → 직접 투영)로 둔다.** 노드 경계가 맞으면
나중에 커널만 CONOP 으로 갈아끼우면 되고 아키텍처는 안 바뀐다. "필요한가"는 다중 사건 seriation 을 스코프에 넣을
때 다시 묻는다 — **"cdGTS 를 너무 복잡하게 만들지 않는다"가 그 판단의 기준.**

**L2** — 정직성 게이트:
- **SF/MSWD 분산 게이트**(Ch.14 §6). 가장 값싸고 효과 크다. SF ≈ scaled residual 의 RMS ≈ √MSWD.
- **§10 오차 확대식 outlier** — 삭제가 아니라 가중치 낮추기. (원 σ, 조정 σ, 사유, 유지 여부)가 전부 노드 파라미터로
  떨어져 provenance 철학과 정확히 맞는다. **챕터에서 가장 구현하기 좋은 아이디어.**
- **hiatus** — age-model 에 `breaks` 입력(부정합 위치)만 열면 piecewise. §9.2/§16.2 가 꼽는 한계를 값싸게 정직화.

**L3** — 미룬다:
- **CONOP 계열 seriation 커널**(다중 사건에서 순서 자체가 불확실해질 때). §6.2 — 난이도가 아니라 스코프로 판단.
- joint 동시추정(P06.4b) · L5 `posterior_ref` 방출.

## 7. 부수 발견 — 기존 구조의 부채 (챕터와 무관, 지금 갚을 수 있음)

**ⓐ 공분산 메커니즘은 보기보다 일반적이다.** Σ = L·Lᵀ 로 항상 인수분해되므로, 각 출력에 loading 벡터를 실으면
`covariance()` 의 현재 공식이 **임의의 공분산 행렬을 이미 표현한다**:

```
Cov(a,b) = Σ_k L[a][k]·L[b][k]      ← nodes/distribution.py:119-122 그대로
Var(a)   = Σ_k L[a][k]²
```

붕괴상수 공유(ref=`decay-238U`)와 스플라인 적합 공유(ref=`agemodel:<node>:pc1`)가 **같은 메커니즘의 특수 케이스**가
된다. L4 `joint` 가 생각보다 힘이 세다.

두 걸림돌(둘 다 작다):
- **음의 loading 을 못 싣는다.** `dist_from` 의 `if s > 0`(`engine/kernels.py:51`)이 걸러내고,
  `covariance()` 는 `ca.keys() & cb.keys()` 교집합에 양수만 곱하므로 **공분산이 음수가 될 수 없다**. 스플라인 적합에서
  인접 경계는 음의 상관을 가질 수 있다. → 부호를 살려야 한다.
  **미해결** — addendum 에서 이 부채가 **실제로 도달 가능함이 확인됐다**(카디널 가중치가 음수를 가진다).
- **marginal σ 와 공유성분이 서로 다른 경로로 계산돼 어긋날 수 있다**(`budget.model` 은 독립 가정, components 는 별도).
  이게 "공유원 있으면 σ 과소" 부채의 뿌리다. → **components 를 marginal 의 단일 진리원으로**(σ_a = ‖L[a]‖) 삼으면
  그 부채가 **정의상 소멸**한다. **미해결** — addendum 의 수정은 공유성분을 해석적으로 전파할 뿐, MC 는 여전히
  horizon 을 독립으로 뽑는다.

한계(정직하게): 이건 **선형-가우시안만** 표현한다. Ch.14 의 MC 는 왜도를 낸다 → L5 `posterior_ref` 가 여전히 필요하고,
아직 아무 커널도 방출하지 않는 그 자리가 **정확히 §25 의 replicate 가 살 곳**이다. 사다리 의도는 이미 맞게 설계돼 있었다.

**ⓑ `fidelity` 단일 enum 이 조합을 막는다.** "왜도가 있으면서 동시에 공유성분도 있다"를 표현할 수 없다
(`dist_from` = `joint if comps else decomposed` · `_summarize_samples` = `shape` + `shared` 유실). §2 의 spline
공분산 유실 버그가 사실 **이 enum 강제의 증상**이다. 그런데 Ch.14 의 산출물이 정확히 그 조합이다(MC → 비대칭,
external error → 공유). 필드(`shape`·`shared_components`·`posterior_ref`)는 이미 직교인데 라벨만 하나를 고르라고
강요한다. → **직교 축**(marginal 형태 × 공분산 구조)으로 보거나, 최소한 존재 필드로부터 **유도되는 라벨**로 강등.
**부분 완화**(addendum) — 라벨을 사다리 위쪽(`joint`)으로 두고 `shape` 필드를 유지하는 우회로 손실은 막았다.
읽는 쪽(`moments()`·`component_sigmas()`)이 라벨이 아니라 필드를 보기 때문에 동작한다. **enum 자체는 그대로.**

**ⓒ `hpd95` 키에 equal-tailed percentile 이 들어간다**(`_summarize_samples:157` = `np.percentile(…, [2.5, 97.5])`).
HPD 가 아니다. 게다가 `moments():33-35` 가 `(hi−lo)/(2·1.96)` 으로 역산해 **대칭 σ 로 되돌리므로**, 왜도가 있어
`shape` 로 승격된 분포도 하류에서 붕괴한다. Ch.14 의 산출물이 바로 percentile 구간이라 직접 관련된다.

## 8. 챕터를 따라가지 말아야 할 곳

- **§5.4–5.5 의 σ_x→Ma 환산은 순환적**이다 — 층서 오차를 시간으로 바꾸려면 age model 이 필요한데 그 환산된 오차로
  age model 을 적합한다. 챕터는 "spline 이 대체로 직선이니까"(§5.5)로 넘어간다. **그래프에선 이 순환이 그냥 없다**:
  tie-point 의 σ_x 는 depth 단위로 남아 있고 age-model 을 통과할 때 비로소 시간으로 변환된다. 사전 환산도 근사도
  불필요. 이건 일회성 적합 절차의 산물이지 문제의 본질이 아니다 — **베끼지 말 것.**
- **§16.1** — MC 가 관측값을 참값 중심처럼 사용. 저자들도 "충분히 조사되지 않았다"고 자인.
- **보간 스플라인의 함정**(현재 코드): SF→0 = §4.2 의 "자료점을 자세히 따라감 → 요동" 극단 = §15.1 의 time reversal
  영역인데, §15.2 의 처방("SF 를 높여 단조성 회복")을 **SF 가 없어서 쓸 수 없다**. 병은 있고 약은 없는 상태.
  (커널의 `np.diff(depths_s) <= 0` 체크는 age 단조성이 아니라 **depth 중복** 검사다.)

## 9. 챕터 대비 cdGTS 가 앞선 곳 — R04 L1 의 검증

§16.3–16.5 는 챕터가 **스스로 인정하는 최대 한계**다: 모든 방사연대 오차를 독립으로 취급 → 경계연대 오차 과소평가 →
duration 은 별도 **규칙**("internal error 만 쓰라")으로 땜질.

**R04 L1(0.1.54~55)이 이걸 구조적으로 더 낫게 풀었다.** 붕괴상수를 실제 노드로 만들어 `shared_components` 로
태깅하니 임의 위상에서 공분산이 자동으로 따라 나오고, `duration_stats`(`:247-259`)가 이미 `Var(o)+Var(y)−2·Cov` 를
계산한다. **Ch.14 는 규칙이지만 cdGTS 는 provenance 다.** 캡스톤 데모(shared→Cov 1.96→pass vs independent→Cov 0→warn)가
정확히 §16.4 의 실패 모드를 재현한 것.

⚠️ 단 요약 §26 의 첫 항목("correlated external error 를 covariance matrix 로")이 "이미 L1 에서 됨"이라는 뜻인데,
**§21–26 은 원저가 아니라 요약자의 cdGTS 해석**이다([문서 헤더](../docs/statistical_procedures_summary.md) 경고 참조).
Agterberg et al. 의 로드맵으로 인용하지 말 것.

## 10. 전략적 반론 (약해졌지만 남아 있음)

반론: cdGTS 의 사명이 **최고의 age-model 엔진**이 아니라 **provenance·CI·diff** 라면 — composite 는 외부 아티팩트로
**cite 만 하고** "갱신되면 무엇이 바뀌는지"만 보여주는 게 본령일 수 있다(devlog 127 reference 노드 방향).

**§6.1 이 이 반론을 상당히 약화시킨다.** cite-only composite 로는 §5 의 tie 토글이 전파되지 않는다. 즉 이 반론을
받아들이면 **킬러 유스케이스를 포기**하는 것이고, 그러면 tie-point 를 1급으로 올릴 이유의 절반이 사라진다.

살아남는 형태는 더 좁다: **공표 composite 를 인용 후보로 두되(§6.1 말미), 유도 composite 와 나란히 놓고 diff 한다.**
"우리 ties 로 유도한 composite vs 논문의 CONOP run" — 이건 오히려 cdGTS 다운 산출물이다. **이 형태로 반론을 흡수한다.**

남는 진짜 결정: **다중 사건 seriation(=CONOP)을 언제 스코프에 넣는가**(§6.2). 지금은 아니다.

## 11. 버티컬 슬라이스 제안 (R04 L1 과 같은 모양)

기존 base-of-Cambrian 예제를 그대로 두고: 세 δ13C BACE 상관을 **`tie-point` 노드 하나**로 묶고(물리적으로 하나의
사건 → 하나의 노드), rectangular σ_x 를 실은 뒤, ash bed 6개를 composite x축에 올려 `age-model` 하나로 적합,
Fortune Head 의 T. pedum tie-point 에서 경계를 read-off.

**예상: σ 가 지금(±0.138)보다 커진다.** σ_x 가 들어오고 붕괴상수·tie-point 공유가 상관을 만드니까. **그게 요점이다** —
값이 아니라 정직함이 산출물이고, `demo-cov` 와 똑같은 구조의 이야기다: **같은 데이터, 순진한 σ vs 정직한 σ.**

그리고 §5 를 데모로: **tie 엣지 하나 토글 → 원클릭 diff.**

## 12. 결론 / 다음

1. **Ch.14 는 "섹션 합치기"의 답이 아니다** — x축이 이미 합쳐져 있다고 전제한다. 진짜 합치기는 Ch.3.
2. **1급으로 올릴 프리미티브는 `tie-point` 하나** (R04 의 붕괴상수와 같은 수).
3. **킬러 유스케이스는 계산이 아니라 엣지 토글**(§5) — 상관 가설을 클릭으로 켜고 끄기. topology-diff·competing-models·
   P05 가 이미 그 자리에 있다. 이걸 하려면 tie 가 **노드**여야 한다.
4. **§5 가 composite 를 derived 로 밀어낸다**(§6.1) — authored leaf 면 토글이 전파되지 않는다. R04 의 GSSA=leaf 결론을
   기계적으로 복사한 게 초안의 실수. **CONOP 은 난이도가 아니라 필요성으로 판단**(§6.2)하고, 지금은 **trivial 커널로
   노드 경계만 맞춘다**.
5. **`cross-section-correlation` 은 소멸**, `joint-inference` 는 생존.
6. **챕터와 독립으로 지금 갚을 부채**(§7): loading 부호 · marginal 단일 진리원 · fidelity enum · `hpd95` 오칭.
   **spline 공분산 유실(§2)은 그냥 버그** → ✅ **수정됨**(addendum, pytest 182). 나머지 부채는 미해결.

**다음**: §11 슬라이스 착수 여부, 또는 §7 잔여 부채(MC 상관 draw · loading 부호). 미착수.

## Addendum (2026-07-15) — spline 공유성분 유실 수정

§2 의 🐛 버그만 **선상환**했다(챕터·아크와 독립인 순수 버그). 나머지 §7 부채와 §11 슬라이스는 그대로 미착수.

**핵심 통찰**: `CubicSpline` **평가는 입력 연대에 대해 선형**이다 — `f(target) = Σ_i c_i·y_i`. 따라서 linear 경로와
**같은 결합 규칙**이 그대로 적용되고, 공유성분을 MC 로 뽑을 필요 없이 **해석적으로** 전파할 수 있다. 카디널 가중치
`c_i` 는 각 horizon 에 단위 임펄스를 넣어 적합·평가하면 나온다(`_spline_weights`; knot 수가 적어 비용 무시, Σc_i = 1).

- `_blend_components` 를 **n-ary 로 일반화** — 기존 2점 전용 시그니처는 `s1`·`s2` 를 받기만 하고 **쓰지 않는 죽은
  파라미터**였다. 이제 linear·spline 이 같은 함수를 쓴다.
- `_summarize_samples(…, shared=)` 추가. 왜도+공유성분 공존 시 라벨은 `joint`, `shape` 필드 유지(§7ⓑ 부분 완화).
- `_shared_comps` 추출(직렬화 경계) + `float()` 캐스팅 — spline 만 `np.float64` 를 내던 불일치 제거.
  (`np.float64` 는 `float` 서브클래스라 JSON 직렬화는 원래 통과했다. 버그는 아니었고 일관성 문제였다.)
- 회귀 테스트 4종. 핵심은 **spline 과 linear 의 공분산 구조가 같아야 한다**는 것 — 보간 방법 선택이 백본을 다시는
  조용히 끊지 못한다. **pytest 178 → 182 passed.**

**수정 전/후 실측**(네 horizon 이 `decay-238U` σ=0.4 공유, 두 경계를 spline 보간):

| | fidelity | shared | Cov | duration σ |
|---|---|---|---|---|
| 전 | `decomposed` | 없음 | **0.0** | 0.5808 |
| 후 | `joint` | `decay-238U: 0.4` | **0.16** | **0.1318** |

linear 경로는 전후 동일(Cov 0.16) — 리팩터 회귀 없음. duration σ 가 4.4배 좁아진 것이 Ch.14 §16.5 그대로다.

**정직하게 남는 것**:
- **MC 는 여전히 horizon 을 독립으로 뽑는다.** 공유성분은 이제 해석적으로 맞게 전파되지만 `draws` 는 각 horizon 에
  독립 정규를 쓴다(σ=0.5 중 0.4 가 공통인데도). 그래서 marginal 이 과소평가되고, 위 예의 duration σ 0.13 은 완전
  모델링 값(~0.3)보다 작다 — **0.58(과대) → 0.13(과소)로 옮겨간 셈**. 보고된 버그(Cov 가 조용히 0)는 해소됐으나
  §7ⓐ 의 marginal/components 이원화는 그대로. 고치려면 draw 당 공유 성분을 한 번만 뽑아야 하고(≈6줄), 기존 테스트·
  데모 수치가 바뀌므로 별도 라운드.
- **음의 loading 부채가 이 경로에서 실제로 도달 가능함이 확인됐다**(§7ⓐ). target 30 · knot [10,20,40,50] 의 카디널
  가중치 = `[-0.167, 0.667, 0.667, -0.167]`. 전 horizon 이 같은 ref 를 공유하면 Σc_i = 1 이라 상쇄돼 정확하지만,
  **음의 가중치 knot 에만 붙은 ref 는 순 기여가 음수가 되어 `_shared_comps` 의 `if s > 0` 에 탈락**한다.
  해당 줄에 R05 §7 참조 주석을 달아 뒀다.

**미배포** — 코드 변경, 다음 릴리스에 포함. 마이그레이션 없음(커널만).

## 관련

- [R04](20260711_R04_radiometric-provenance-depth.md) — 자매편(방사연대 provenance 깊이) · [devlog 139](20260712_139_calibration-constant-covariance-slice.md) — R04 L1 착지
- [devlog 131](20260710_131_p07-base-cambrian-realistic-model.md) — P07 base-of-Cambrian 모델(본 검토의 대상 그래프)
- `docs/statistical_procedures_summary.md`(Ch.14) · `docs/radiogenic_isotope_geochronology_summary.md`(Ch.6)
- `docs/topology-diff.md` · `docs/competing-models.md` · `docs/cycles.md` §12 · `docs/distribution-representation.md`

<!-- lang: ko · pair: tutorial-science-engine_en.md -->
# 튜토리얼 — Science Engine 손으로 이해하기 (Arc A / P06)

[English](tutorial-science-engine_en.md)

이 문서는 cdGTS의 **과학 엔진**(불확실성·공분산·정합성 게이트·clamp)을 **실제로 눌러보며** 이해하는 안내입니다.
추상적인 개념이라 글만으로는 잘 안 잡히므로, 배포된 데모 데이터를 직접 조작하는 순서로 구성했습니다.

- **대상**: 배포판 `cdgts.paleobytes.info`(또는 테스트 `127.0.0.1:8011`).
- **선행**: 데모 데이터가 있어야 합니다 — 없으면 서버에서 `python manage.py seed_demo` 한 번 실행(멱등).
- **소요**: 10–15분. 클릭만으로 됩니다(코드 불필요).

---

## 0. 한 문장으로 — 이 엔진이 뭘 하나

> **연대 불확실성은 단일 `±`가 아니다.** 성분(분석/계통/모델)으로 쪼개지고, **여러 경계가 같은 계통오차(붕괴상수 등)를
> 공유하면 그 오차는 상관된다.** 두 경계의 *간격*(지속시간·순서)을 볼 때 공유오차는 **차이에서 상쇄**되므로, 순서가
> 생각보다 잘(또는 못) 결정된다. 엔진은 이 구조를 나르고, **정합성 게이트**가 그걸로 순서·지속시간을 판정한다.

이 한 문장이 손에 잡히면 Arc A는 이해한 겁니다. 아래 실습이 정확히 그 순간을 만듭니다.

---

## 1. 배경 — 딱 필요한 개념 3가지

### (a) 분포 = 충실도 사다리 (L0–L5)
경계의 연대는 스칼라가 아니라 **분포**로 흐릅니다.

| 층 | 표현 | 예 |
|---|---|---|
| L0 exact | 점질량 (GSSA 약속값) | 2500 Ma |
| L2 decomposed | 분해 예산 (±분석 / +계통 / +모델) | 251.9, budget{model:0.05} |
| L3 shape | 비대칭 HPD | median + [lo,hi] |
| **L4 joint** | marginal + **공유 계통 태그** | …, shared:[{decay-238U, σ}] |
| L5 full | 사후 표본 | (P06.4 예정) |

핵심은 **L2의 분해 예산**과 **L4의 공유 태그**입니다. *계통 성분을 공유하느냐*가 곧 공분산입니다.

### (b) 공분산과 지속시간
`지속시간 = 아래경계 − 위경계` 이므로:

```
Var(지속시간) = Var(아래) + Var(위) − 2·Cov(아래, 위)
```

두 경계가 같은 계통원(예: 같은 U 붕괴상수)을 쓰면 **Cov > 0** → 지속시간 오차가 **줄어듭니다**(상관된 오차가 차이에서
상쇄). 반대로 공유가 없으면 Cov=0, 오차가 그대로 더해집니다. **이게 Arc A의 심장입니다.**

### (c) 정합성 게이트 (평가 후 자동 판정)
그래프를 Evaluate 하면 결과에 **consistency 인증서**가 붙고, Results 패널에 칩으로 뜹니다:

| 칩 | 검사 | 결과 |
|---|---|---|
| **L0** | 구조(비순환) | fail |
| **L1** | 순서(점추정) | fail |
| **L1b** | 순서(공분산 인지 2σ) | **warn** |
| **L2** | 지속시간 > 0 | fail |
| **L3** | reconcile(clamp) | (릴리스 층, §3) |

`pass`(초록)·`warn`(노랑)·`fail`(빨강). **warn은 실패가 아니라 "통계적으로 미해결"** 경고입니다.

---

## 2. 실습 1 — 공분산 게이트: *같은 값, 태그 하나로 판정이 바뀐다*

배포된 데모 그래프 두 개는 **값도 오차도 완전히 동일**하고, 딱 하나 — 공유 계통 태그 — 만 다릅니다.

### 단계
1. **Editor** 화면. 상단 **그래프 선택 드롭다운** → **"Demo: duration overlap (independent errors → L1b warn)"**.
2. **Actions ▾ → Evaluate**.
3. 하단 **Results 패널** 확인:
   - consistency 배지 **노랑(warn)**, **L1b** 칩 노랑.
   - 경고줄: `L1b 순서 통계적 미해결: olenekian↔anisian (Δ2.0 < 2σ 4.243)`.
4. 드롭다운 → **"Demo: duration resolved (shared systematic → L1b pass)"** → **Evaluate**.
   - consistency **초록(pass)**, **L1b** 초록.

### 무슨 일이 벌어진 건가 (숫자)
두 그래프 모두 인접한 두 Age 경계: **base-Olenekian 249.0 Ma**, **base-Anisian 247.0 Ma** (간격 **2.0 Myr**),
각 경계 **1σ = 1.5 Myr**.

- **independent(warn)**: 공유 없음 → `2σ_gap = 2·√(1.5² + 1.5²) ≈ 4.24`. 간격 2.0 < 4.24 → **순서 미해결(warn)**.
  ("두 경계가 2 Myr 떨어졌다지만, 오차가 4 Myr나 돼서 어느 게 먼저인지 통계적으로 확신 못 함.")
- **shared(pass)**: 둘 다 `decay-238U` (σ 1.4)를 공유 → `Cov = 1.4·1.4 = 1.96` →
  `Var_gap = 1.5² + 1.5² − 2·1.96 = 0.58`, `2σ_gap ≈ 1.52`. 간격 2.0 > 1.52 → **순서 해소(pass)**.

### 가져갈 것 ✅
> **값과 오차가 똑같아도, 오차가 어디서 왔는지(공유 계통이냐)에 따라 순서 판정이 뒤집힌다.**
> 단일 `±`로는 절대 못 하는 일입니다 — 그래서 분포를 성분으로 쪼개 나릅니다.

---

## 3. 실습 2 — Clamp: 검증만(L3a) vs 적용(L3b)

**Clamp** = 소위원회가 authored한 거버넌스 제약(pin/range/order/freeze). 릴리스가 이걸 어떻게 대하느냐가 두 계약으로 갈립니다.

### 단계
1. **Vault** 화면 → 릴리스 목록에서 **ICS-2024/12** 선택 → **Clamps** 탭.
2. 표에 clamp 2개:
   - `base-triassic` **range [250, 253]** → **honored**(값 251.9가 범위 안).
   - `base-cambrian` **pin 536.0** → **violation**: `538.8 ≠ pin 536.0`.
   - 👉 지금은 **값이 안 바뀝니다**. 이게 **L3a = verify(검증만)** = ICC/bake 계약: *"발표값은 그대로, 거버넌스 위반만 알려준다."*
3. **staff(admin ★)로 로그인**하면 **Reconcile (L3b) →** 버튼이 보입니다. 누르면:
   - base-cambrian 값이 **536.0으로 이동**, 위반이 사라짐.
   - 👉 **L3b = reconcile(적용)** = GTS 계약: *"권위 있는 clamp로 값을 실제로 맞춘다."*

### 중재 규칙
한 경계에 clamp가 여럿이면 **precedence `pin > range > order > freeze`** 로 가장 강한 걸 적용. 같은 등급인데 **서로
다른 소유자**면 **conflict**로 표시(자동으로 안 밀어붙임 — 사람이 풀 문제).

### 가져갈 것 ✅
> **L3a(검증)와 L3b(적용)의 분리**가 곧 "ICC는 발표값을 얼리고, GTS는 재조정한다"는 이 프로젝트의 핵심 계약입니다.
> clamp가 **거버넌스가 값에 개입하는 지점**이고, 이게 다음 주제(Arc B 거버넌스)로 가는 다리입니다.

---

## 4. 직접 실험 (감 잡기)

- **L2 fail 만들기**: Editor에서 데모 그래프의 한 경계 값을 이웃과 같게(예: base-Anisian 247 → 249) 바꾸고 저장 →
  Evaluate → **L2 fail**(영-길이 유닛, 빨강). "지속시간 ≤ 0 = 퇴화."
- **shared를 다시 warn으로**: `demo-cov-shared`에서 간격을 더 좁히면(예: 249 → 247.6) 공유가 있어도 다시 warn.
  공유가 *만능이 아니라* 간격 대비 상관 크기의 문제임을 보여줍니다.
- **숫자 보기**: Results 패널의 각 노드 카드에 uncertainty(± / HPD)가 표시됩니다. Vault의 **Table** 탭에서도 경계별
  불확실성을 볼 수 있습니다.

---

## 5. 데모 데이터는 어떻게 만들어지나

`releases/management/commands/seed_demo.py` (멱등):
- 공분산 대비 그래프 2개(위 §2) — 값·± 동일, `decay-238U` 공유 태그만 차이.
- 공표 릴리스에 authored clamp 2개(§3) — honored range + violated pin.

메인 시드는 **안 건드립니다**. 컨테이너 재시작·야간 미러 sync 후엔 사라지므로 **재실행**:
```
docker exec <컨테이너> python manage.py seed_demo
```

---

## 6. Arc A → 거버넌스로 가는 다리

여기까지 만지면 자연스럽게 다음 질문이 생깁니다:
- clamp를 **누가** authored하고 **누가** ratify하나? (→ P05 Membership·can_ratify·propose/ratify)
- 한 경계에 **경쟁 모델**이 여럿일 때 하나만 고를까, 포락/평균할까? (→ **envelope/BMA**, Arc B)
- 릴리스 전체를 **어떻게 버전·조립**하나? (→ 전역 vs 경계별 버전, lineage diff)

즉 **Arc A(정직한 불확실성)를 이해해야 Arc B(거버넌스)가 왜 필요한지**가 잡힙니다. clamp의 L3a/L3b가 바로 그 경첩입니다.

---

## 참고 문서
- 개념: [distribution-representation](distribution-representation.md) · [coherence-gate](coherence-gate.md) ·
  [cycles](cycles.md) · [competing-models](competing-models.md) · [idea](idea.md)
- 구현 기록: devlog `P06`(계획) · `116`(공분산 백본) · `117`(게이트) · `118`(clamp) · `119`(캡스톤 데모) ·
  `P06.4`(베이지안 joint 계획).

# 정합성 게이트 (Coherence Gate) — Layer 5

*[English](coherence-gate_en.md) · 한국어*

> 상태: **구체화 초안. 결정 아님.** 핀된 경계 집합을 유효한 전 지구 차트로 바꾸는 메커니즘.
> [versioning-global-vs-per-boundary.md](versioning-global-vs-per-boundary.md)에서 "진짜 알맹이"로 지목한 부분이자,
> [idea.md](idea.md) §5의 **Layer 5(전역 종합)** 의 작동 핵심.

## 0. 위치 — 이것은 곧 Layer 5

정합성 게이트는 새 개념이 아니라 **Layer 5(global synthesis) 노드의 정의**다. Layer 4(correlation)가 낸
경계별 근거를 받아, **전 지구적으로 정합한 경계 연대 집합**을 만들어 Layer 6(배포)로 넘긴다.

```
[Layer 4: 경계별 상관·근거]
        │  (핀된 경계 집합 + 각자의 provenance 그래프 + 공유 노드 그래프)
        ▼
   {정합성 게이트  L0→L3}
        │
   ┌────┴─────────────┐
   ▼                  ▼
 PASS + 인증서       violations[]
 (유효한 차트)       {level, kind, boundaries[], severity}
        │
        ▼
[Layer 6: ICC(bake) / GTS(narrate)]
```

## 1. 시그니처

```
coherence_gate(
  manifest,          # {boundary_id → boundary_version} 핀 집합
  shared_node_graph, # 어떤 경계들이 어떤 상류 노드(붕괴상수·tracer…)를 공유하는지
  claimed_level      # 이 릴리스가 주장하는 정합성 수준 L0~L3
) → PASS + certificate | violations[]
```

- **certificate** = `{level_achieved, checks_run, warnings, gate_version}` — 소비자가 보증의 강도를 알 수 있게.
- **violations** = `{level, kind, boundaries[], severity: fail|warn}` 구조화 목록.

## 2. 검사의 사다리 (싸고 국소 → 비싸고 얽힘)

| 레벨 | 검사 | 필요 입력 | 성격 |
|---|---|---|---|
| **L0 구조** | 참조 무결성 + 위상 + **비순환**: 모든 경계가 실존 버전으로 해석되고, 단위들이 경계로 **빈틈·겹침 없이 분할**되며, (clamp 적용 후) provenance가 릴리스 안에서 **비순환**인가. 이중 명명 쌍 존재. | id·위상·엣지 type | **FAIL** |
| **L1a 순서(점추정)** | 인접 경계쌍에서 age(젊은 base) < age(오래된 base). 총 단조. | 값 | **FAIL** (대표 경계엔 거의 항상 통과) |
| **L1b 순서(구간)** | 인접 경계의 2σ 구간이 겹치는가 = "순서가 통계적으로 미해결" 표시(위반 아님). | 값 + ± | **WARN** |
| **L2 지속시간** | stage/epoch 길이 = 두 경계 차. 음(-)의 지속시간, 분포가 0 아래로 새는지. | 값 + ± + **공분산** | FAIL/WARN |
| **L3 상관인지** | 경계들을 독립으로 보지 않고 공유 상류 노드로 결합 처리. | 각 경계의 **provenance 그래프** | 아래 두 갈래 |

**L2가 왜 공분산을 요구하나 (핵심).**
지속시간 = age_old − age_young, 그 분산은 `Var(old) + Var(young) − 2·Cov(old, young)`. 두 경계가 상류 노드
(붕괴상수·tracer)를 공유하면 `Cov > 0`이라, 순진하게 `Var(old)+Var(young)`로 계산하면 **지속시간 불확실성을
과대평가**한다. 제대로 하려면 게이트가 두 개의 `±` 값이 아니라 **상관 구조**를 알아야 한다.

**L3의 두 갈래.**
- **L3a 검증(validate):** 경계 값은 그대로 두고, 공유 노드에서 오는 경계 간 공분산을 계산해 순서·지속시간이
  상관오차까지 감안해도 성립하는지 **확인만** 한다. 숫자를 바꾸지 않음.
- **L3b 재조정(reconcile):** 단조 순서를 hard prior로 두고 공유 사전분포 아래에서 경계 연대를 **공동추정** →
  값이 **이동**할 수 있다. 원시 레코드가 살짝 충돌해도 정합 집합을 만들어냄.

## 3. 중심 갈림길 — 검증만 vs 재조정까지

이것이 게이트의 성격을 정한다:

- **검증 전용 (L0~L2 + L3a):** 릴리스의 연대 = 핀된 레코드의 연대 **그대로**. provenance가 깨끗함
  (릴리스 숫자 = 레코드 숫자 = 비준값). 대신 **거부만 가능, 수정 불가**.
- **재조정 (L3b):** 원시 레코드가 충돌해도 정합 차트를 만듦. 대신 **릴리스 숫자 ≠ 레코드 숫자** —
  "릴리스 보정값"이 생기고 릴리스 자체가 하나의 추론 노드가 됨.
  → **재조정은 자동 joint inference보다 subcommission의 authored `Clamp`로 하는 편이 정직하다**(갈라짐이
  이름 붙은·귀속 가능한 거버넌스 결정이 됨). 상세: [cycles.md](cycles.md).

**깔끔한 매핑 하나가 떨어진다 — 두 모드가 ICC/GTS와 정확히 붙는다:**

- **ICC = bake = 검증 전용.** 권위가 추적 가능한 비준값에 있으므로 릴리스가 숫자를 몰래 바꾸면 안 됨.
- **GTS = narrate = 재조정 허용.** 연구용 서술 차트에선 전 지구 공동추정 타임라인이 목적에 맞음.

즉 **게이트의 두 모드 = 게이트웨이의 두 출력.** 우연이 아니라 같은 구조의 다른 면.

## 4. 구체화하며 드러난 두 통찰

1. **정합성을 위협하는 건 "비동기 독립 갱신"이지 "동기 공유 갱신"이 아니다.** 붕괴상수 하나가 바뀌면
   의존하는 모든 경계가 **한 몸으로** 움직여 오히려 정합성이 유지된다. 반대로 한 경계만 재측정하고 이웃은
   그대로 두는 **비동기** 상황이 순서를 깨뜨린다. → 게이트의 주 임무는 **비동기 갱신 감시**.
2. **경계가 도달할 수 있는 정합성 레벨은 provenance가 얼마나 기계가독인가로 상한이 정해진다.** L0~L1은
   값·순서만, L2~L3은 provenance 그래프가 필요. "발표된 값 + 출처만" 수준의 레거시 경계(또는 GSSA)는
   **L1까지만** 참여 가능. → [idea.md](idea.md) §7의 "Layer 3을 실제 계산까지 하나, 발표값+출처만인가"와 직결.
   **정합성 야심이 곧 provenance 요구 수준을 정한다.**

## 5. 경계 레코드가 레벨별로 내놔야 하는 것 (최소 계약)

- **L0~L1:** `age.value_ma`, `identity.separates`(순서), (L1b는) `uncertainty`.
- **L2:** + 공유 노드 식별자 (어떤 경계와 상류를 공유하는지).
- **L3:** + `age.provenance_ref` 아래 실제 서브그래프 (공동 처리 가능한 형태).

→ [boundary-gateway-schema.md](boundary-gateway-schema.md)의 `provenance_ref`가 장식이 아니라
**정합성 레벨의 열쇠**임이 여기서 확정된다.

## 6. 남는 열린 질문

- L3b 재조정 시 "릴리스 보정값"을 레코드값과 나란히 **어떻게 인용·표기**할지.
- L1b 겹침 WARN을 릴리스가 **차단할지 통과시킬지** 정책(대표 경계 vs 세밀 구간 차등?).
- 공분산을 어디까지 추적할지 — 전체 공분산 행렬 vs 공유 노드 태그만.
- 게이트 자체의 버전(`gate_version`) — 검사 규칙이 바뀌면 과거 인증서의 지위는?

## 7. 링크

- [versioning-global-vs-per-boundary.md](versioning-global-vs-per-boundary.md) — 정합성 게이트가 등장한 맥락(전역 릴리스 = 매니페스트 + coherence 게이트)
- [boundary-gateway-schema.md](boundary-gateway-schema.md) — `provenance_ref`·`age_model` 필드
- [idea.md](idea.md) §5 (Layer 5) · [node-graph-paradigm.md](node-graph-paradigm.md) (공유 노드·순환)
- 공유 노드 사례: [case-permian-triassic.md](case-permian-triassic.md)

# 순환 의존성과 clamp

*[English](cycles_en.md) · 한국어*

> 상태: **검토 → 스키마/게이트에 일부 반영.** [node-graph-paradigm.md](node-graph-paradigm.md)이 처음부터
>짚은 순환 문제(생층서 ↔ 방사연대)를 펼치고, subcommission의 **hand-crafted clamp**를 해법으로 도입. → clamp 프리미티브 **구현됨** (releases.Clamp · pin/range/order/freeze-version · devlog 118).

## 1. "순환"은 하나가 아니다

여러 피드백 루프가 층위별로 있다:

| 루프 | 내용 |
|---|---|
| **생층서 ↔ 방사연대** | 생대(biozone)는 그 안의 재층을 연대측정해 절대연대를 얻지만, 재층 시료의 위치·소속 생대는 생층서로 잡는다. 보정된 생대를 다른 섹션에 재사용 → 되먹임. |
| **천문연대 ↔ 방사 앵커** | cyclostratigraphy는 궤도 주기로 *지속시간* 척도를 만들고 절대 고정엔 방사 **앵커**가 필요. 방사연대는 다시 천문연대로 검증·재보정됨. |
| **붕괴상수 ↔ 방법 간 교차보정** | U–Pb ↔ Ar–Ar 교차보정, K 붕괴상수·모니터 광물 연대가 U–Pb·천문연대에 맞춰 재보정 → "상수"가 연대에서 파생. |
| **age model ↔ correlation** | 층에 연대를 줘야 age-depth 모델을 짓고, 상관엔 age model이 필요하고, 상관은 다시 공동 모델로 되먹임 (Layer 4 ↔ 5 얽힘). |

## 2. 결정적 구분 — 국소 상호제약 vs 전역 보정 되먹임

- **국소 상호제약은 진짜 순환이 아니다.** 한 섹션의 화석·재층 연대는 둘 다 *같은 진실*(그 섹션의 age-depth
  관계)에 대한 **관측**이다. "둘이 age-depth를 *공동으로* 제약한다"고 하면 논리적 순환이 없다. 순환은 이걸
  *순차* 계산하려 할 때만 생긴다.
- **진짜 위험한 건 전역 보정 되먹임이다.** 보정된 산물(생대 절대연대·붕괴상수·천문 튜닝)이 일부 섹션에서
  파생돼 *다른 섹션의 입력으로 재사용*되고, 그 다른 섹션이 다시 보정 재도출에 기여하면 그래프 전체를 도는
  루프가 된다. "화석을 암석으로, 암석을 화석으로 연대측정"이라는 순환논증 비판이 무는 곳.

## 3. 국소 순환의 해법 — 동시추정 노드 (+ 공짜 보너스)

국소 상호제약은 **베이지안 공동모델**로 접는다: age-depth + 생대 경계 + 궤도 튜닝 + (필요시) 붕괴상수에
사전분포를 걸고 **결합 사후분포**를 샘플링 → 사이클 A↔B가 다중입력·다중출력 노드 하나가 된다.

**보너스:** 이 결합 사후분포가 곧 [정합성 게이트](coherence-gate.md)가 요구했던 **상관 구조(공분산)**. 순환을
제대로 접으면 게이트의 L2/L3 입력이 공짜로 딸려온다.

## 4. 전역 순환의 해법 — 버전 축으로 사이클을 편다

게이트웨이는 얼린 버전 산물이다. 보정 산물을 **게이트웨이로 승격**하면 *한 릴리스 안에서는 상수 입력*이 되어
살아있는 사이클이 끊긴다. 되먹임은 릴리스 안에서 돌지 않고 **다음 릴리스의 보정 입력**이 된다:

```
보정_v1 → 릴리스 R1 연대 → (새 데이터) → 보정_v2 → 릴리스 R2 연대 → …
```

즉 **논리적 순환이 시간축의 나선(spiral)으로 펴진다.** 각 릴리스 내부는 깨끗한 DAG, 되먹임은 연속 릴리스의
delta. 컴파일러 부트스트래핑과 같다(v1을 얼려 v2 빌드). **CD가 순환을 고정점 반복으로 바꾸고, 수렴 =
연속 릴리스가 더는 안 움직임.**

## 5. Clamp — subcommission이 놓는 hand-crafted 게이트 ★

**우리는 이미 clamp를 하나 갖고 있다: GSSA.** 선캄브리아 경계는 데이터 파생이 아니라 subcommission이 숫자를
손으로 못 박은 값이다. clamp는 그 GSSA 특수 사례를 **일반 원시타입으로 승격**한 것.

clamp의 결(노드 그래프의 `clamp(x,min,max)` 처럼):

- **pin** — 정확한 값으로 고정. ← GSSA가 이것.
- **range** — `[min,max]`로 구속 ("538–542 Ma 사이. 벗어나면 경계로 clamp + 플래그").
- **order** — 이웃보다 작거나 같도록 강제 (단조성 clamp).
- **freeze-version** — 보정 산물을 이 릴리스 동안 특정 버전으로 핀 (← 사이클 절단).

**두 열린 문제를 동시에 해결한다:**

1. **"얼리는 경계를 어디에 긋나."** → 알고리즘이 아니라 **subcommission이 clamp를 놓는 위치가 곧 freeze
   line.** 각 subcommission이 자기 system 경계를 소유하므로 책임 소재가 분명한 지점에서 사이클이 끊긴다.
2. **"나선이 진동할 수 있다."** → **clamp가 곧 damper.** 손으로 고정한 노드가 되먹임 폭주를 막아 버전 나선을
   안정화. 신호에서 clamp가 하는 일 그대로.

## 6. 정합성 게이트가 다시 그려진다

Layer 5의 게이트가 **하나의 거대한 자동 게이트**가 아니라, 그래프 중간중간에 흩어진 **여러 authored clamp 노드
+ 나머지를 검사하는 자동 게이트**가 된다:

- clamp = subcommission이 소유한 **거버넌스 게이트웨이를 네트워크 *안*에 꽂은 것.**
- 자동 게이트: (a) authored clamp를 적용, (b) 남은 그래프가 **비순환·정합적**이고 clamp가 사이클을 실제로
  다 끊었는지 검사.

**자동 재조정(L3b)보다 정직하다.** 값이 모델 출력과 갈라질 때, 그 갈라짐이 *"X Subcommission이 모델 출력 Y를
clamp로 재정의 (근거: …)"* 라는 **이름 붙은·귀속 가능한 결정**이 된다. 숨은 통계적 보정이 아니라.
→ 게이트의 reconcile 모드를 "자동 joint inference"에서 **"authored clamp"** 로 대체하는 편이 낫다.

## 7. 긴장

- **과잉 clamp = 화석화.** 너무 고정하면 continuously deployed 스트림을 무시 → 차트가 새 과학을 안 반영.
  **권위 안정성 vs CI 반응성**의 긴장이 clamp 노드에 국소화되고, 소유한 body가 경계별로 협상한다.
- **clamp 자체가 버전·비준 대상.** subcommission이 clamp를 바꾸면 자체 diff를 갖는 거버넌스 이벤트.
- **샌드박스에선 clamp를 뗄 수 있어야.** "이 고정을 안 하면?"이 곧 what-if. clamp는 릴리스 매니페스트/거버넌스
  층에 속하고 샌드박스에서 **오버라이드(제거) 가능** → [competing-models.md](competing-models.md)의 selection과 같은 결.

## 8. 스키마/그래프 함의

- **`Clamp`** 노드 타입 신설: `owner`(subcommission), `kind: pin|range|order|freeze-version`, `value|bound`,
  `rationale`, `ratified`, `overridable_in_sandbox`. → [boundary-gateway-schema.md](boundary-gateway-schema.md) §2에 반영.
- **GSSA = `Clamp{kind: pin}`의 특수 사례** → 정의 타입과 clamp가 한 뿌리로 통일.
- provenance 엣지에 **type**(`co-location` | `calibration-transfer`) 추가 → 게이트가 자기참조(사이클)를 탐지.
- 정합성 게이트: "clamp 적용 후 잔여 그래프 비순환·정합" 검사 → [coherence-gate.md](coherence-gate.md).

## 9. 이게 cdGTS 미션을 바꾼다

cdGTS의 역할이 **"시대표 자동 계산"이 아니라 "subcommission이 책임 있는 clamp를 놓는 그래프를 주고, 나머지
전파·검사·diff는 기계가 자동으로"** 가 된다. 이건 [idea.md](idea.md) §7의 오랜 열린 질문("계산까지 하나,
발표값+출처 수준인가")에 대한 **제3의 답**: **사람은 authoritative 노드를 clamp하고, 기계는 전파·정합·diff를 한다.**

## 10. 남는 열린 질문

- clamp 배치의 **최소 집합** — 모든 사이클을 끊는 최소한의 clamp를 어떻게 찾나(자동 제안 + 사람 승인?).
- 나선 **수렴 판정·감쇠** 기준.
- 동시추정 노드의 **스코프 분할**(전부 결합은 불가) → 분할이 들여오는 근사.
- clamp 간 **충돌**(두 subcommission의 clamp가 경계에서 모순)을 어떻게 중재.

## 11. 링크

- [node-graph-paradigm.md](node-graph-paradigm.md) — 순환 의존성·joint inference (원 출처)
- [coherence-gate.md](coherence-gate.md) — clamp 적용 + 비순환 검사
- [boundary-gateway-schema.md](boundary-gateway-schema.md) §2 — `Clamp` 노드 · GSSA=clamp
- [competing-models.md](competing-models.md) · [versioning-global-vs-per-boundary.md](versioning-global-vs-per-boundary.md) — 릴리스/거버넌스 층

# 순환 의존성과 clamp

*[English](cycles_en.md) · 한국어*

> 상태: **검토 → 스키마/게이트에 일부 반영 → 재검토(축소 결론).** [node-graph-paradigm.md](node-graph-paradigm.md)이 처음부터
>짚은 순환 문제(생층서 ↔ 방사연대)를 펼치고, subcommission의 **hand-crafted clamp**를 해법으로 도입. → clamp 프리미티브 **구현됨** (releases.Clamp · pin/range/order/freeze-version · devlog 118).
>
> ⚠️ **재검토(2026-07): [§12](#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가) 참조.** 구현·사용 현황상 clamp는 **별도 1급 개념으로 필요치 않다는 결론.** 하던 일이 전부 이미 있는 메커니즘으로 접힌다 — **authored 노드(GSSA leaf) + order 엣지 + joint-inference 노드 + 버전 나선.** 사람이 값을 못 박는 일은 **authored 노드(GSSA leaf) 하나로 충분히 대신된다.** §1–9는 사고 과정(개념사)으로 보존.

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

## 12. 재검토 노트 (2026-07) — clamp는 별도 개념으로 필요한가

> 구현·사용 현황을 근거로 §5–9의 "clamp = 통일자" 결론을 되짚는다. **요지: clamp가 하던 일은 전부 다른,
> 이미 있는 메커니즘으로 접히므로 clamp를 별도 1급 개념/타입/거버넌스 레코드로 둘 필요가 없다. 사람이 값을
> 못 박는 일은 authored 노드(GSSA leaf) 하나로 충분히 대신된다.** §1–4의 순환 분석 자체는 유효하다 —
> 오히려 그 분석이 "그래프 레벨 루프가 애초에 생기지 않는다"는 결론을 뒷받침한다.

### 사용 현황 (증거)

- 그래프 clamp 노드: `pin` 2개가 전부인데 **둘 다 같은 GSSA decree**(2500 Ma, base-proterozoic). `range` 0개 · `joint-inference` 0개.
- `releases.Clamp`(authored 거버넌스 레코드): **실 seed 0건.** `seed_demo._clamps()`가 심는 데모(base-triassic range=지킴 / base-cambrian pin=위반→reconcile 시연)뿐.
- 즉 clamp는 GSSA 하나를 빼면 **거의 전부 시연용 스캐폴딩.**

### 네 기둥이 각각 접힌다

- **순환 절단 → 불필요.** 생층서↔방사연대는 *과학적* 상호보정이지 파이프라인 의존성 순환이 아니다. 둘을
  **하나의 joint-inference process 노드**로 접어 순환논리를 노드 *안*에서 풀고 출력은 value+σ만 내보내면 그래프는
  DAG로 남는다(§3의 동시추정 노드가 이미 이 답). 실 그래프가 루프를 안 그리는 이유가 이것 — 끊을 순환이
  없으니 breaker(clamp)도 없어도 된다. (어려움은 사라지는 게 아니라 노드 경계 *안*으로 캡슐화된다 = P06.4b의
  자리이자 올바른 위치.)
- **pin / GSSA → authored 데이터 leaf로 충분.** GSSA는 "값이 파생이 아니라 authored인 경계"인데, 그건
  `published-age`(+ `definition_type=GSSA`) leaf가 이미 하는 일. clamp 추상이 더해주는 게 없다.
- **order(단조성) → 이미 order 엣지(L1 게이트)가 담당.** `Clamp{order}`는 중복.
- **freeze-version → §4의 버전축 나선이 이미 하는 일**(게이트웨이 = 릴리스 내 상수). 경계별 clamp가 따로 필요 없다.

### release override(§6)는 자리가 틀렸다

`releases.Clamp` + `reconcile`(L3b)은 bake된 릴리스 값을 clamp에 맞게 *직접 수정*한다. 그런데 그 값을 만든
**그래프는 여전히 옛 값**을 말한다 → 공표 숫자가 그래프 평가로 추적되지 않는 **provenance 구멍**. 재현가능한
출처가 이 시스템의 핵심인데 릴리스 tier에서 out-of-band로 덮는 설계는 그 원칙과 충돌한다. 만약 subcommission
override가 진짜 필요하다면 **그래프 안 authored 노드로 들어가 재-bake되는 게 맞다 — 그러면 결국 GSSA leaf와
같은 꼴.** 이 경우조차 authored leaf로 수렴한다.

### 결론

clamp가 하려던 네 가지 + 거버넌스 override는 전부 이렇게 접힌다:

| clamp가 하려던 것 | 대체 |
|---|---|
| pin / GSSA | **authored 데이터 leaf** (`published-age`, `definition_type=GSSA`) |
| 순환 절단 | **joint-inference 노드** (순환을 노드 *안*에 캡슐화) |
| order (단조성) | **order 엣지** (L1) |
| freeze-version | **버전축 나선** (게이트웨이) |
| release override | 필요하면 → **그래프 안 authored leaf** + 재-bake |

→ **별도의 clamp 개념/타입/거버넌스 레코드는 필요 없다.** §9의 미션도 그대로 성립한다: "사람이 clamp" 대신
**"사람이 authoritative 노드를 authored(leaf/order), 기계가 전파·정합·diff."**

### 정리안 스케치 (구현은 후속, 여기선 방향만)

1. **개념사 보존.** §1–9는 사고 과정으로 유지(삭제 X). 본 §12가 재검토 결론.
2. **그래프 clamp 노드 축소.** `pin` 2개(GSSA)를 authored leaf(`published-age`/GSSA)로 이관, `range`·`clamp`
   category NodeType은 미사용 → deprecate 후보. `is_cycle_breaker`는 `joint-inference`만 남기면 된다.
3. **`releases.Clamp` + verify/reconcile 격리.** 실사용 0이므로 "**demo 전용**"으로 명시(seed_demo 한정) 또는 제거
   검토. graph↔release clamp *통합*은 **하지 않는다**(미사용 기계 둘을 잇는 셈). R02가 지적한 `services.py`
   비대화도 이로써 자연 완화.
4. **미션 문구 갱신.** "사람이 clamp" → "사람이 authored 노드".

### 이 결론을 뒤집을 트리거 (그 전엔 보류)

- **접을 수 없는 실제 그래프 순환** — joint 노드 하나로 캡슐화가 불가능한, 별개 노드 간 진짜 상호 배선이 실제 모델에 등장.
- **그래프 밖에 살아야 하는 진짜 거버넌스 override** — 계산값을 authored leaf로도 표현 못 하는 방식으로 덮어야 하는 실사례.

둘 다 지금은 가설. 나타나면 이 노트를 다시 연다.

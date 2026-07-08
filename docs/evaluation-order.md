# 평가 순서 — 의존순 계산 vs 연대순, 그리고 order = 사후 검사

*[English](evaluation-order_en.md) · 한국어*

> 상태: **구현 후 회고 + 설계 확인.** 구현된 엔진(`engine/evaluate.py`)이 실제로 어떤 순서로 도는지,
> 그리고 order(younger/older) 노드가 그 안에서 어떤 지위인지 정리. "그래프를 연대순(Hadean→젊은 쪽)으로
> 훑어야 하나?"라는 질문에서 출발.
>
> **[구현 갱신]** 지금은 순서를 별도 `order` **노드**가 아니라 주로 **`Edge.kind=order`**(경계 세로 포트 연결)로
> 표현한다. 게이트 L1 우선순위 = **order edge > order 노드 > 게이트웨이 단조 휴리스틱**. 아래 order-노드 서술은
> 폴백 경로로 유효하고 "검사는 계산 순서를 교란하지 않는다"는 논지는 그대로다. L1b/L2(지속시간)는 assert된
> **유닛 스팬**(order edge 인터리브)에서만 판정한다(devlog 120). 상세: [coherence-gate.md](coherence-gate.md).

## 0. 한 줄 논지

그래프 평가는 **의존 순서(위상정렬)**로 돌아야 한다. **연대순(지질시간 순)은 계산의 순서가 아니라 결과의 속성**이다.
order 노드는 값을 바꾸지 않는 **사후(post hoc) 정합성 검사**라, 계산 순서를 교란하지 않는다.

## 1. 두 개의 "순서"를 구분하라

혼동의 뿌리는 서로 다른 두 순서를 한 단어로 부르는 데 있다.

| | 정의 | 엔진에서 |
|---|---|---|
| **의존 순서 (dataflow)** | "무엇이 무엇을 먹이는가" — 입력이 준비된 노드부터 | `topo_order`(위상정렬). DAG 평가의 필연적·유일하게 옳은 순서 |
| **연대 순서 (chronology)** | 경계의 지질학적 나이 순 (Hadean → 현재) | **계산 순서가 아님.** 그래프를 평가한 뒤 나오는 **산출물의 속성** |

경계들은 dataflow 상 **대체로 독립**이다 — Hadean base와 Archean base는 서로를 참조하지 않고, 각자의 상류
증거(방사연대 앵커·age-depth·상관)에서 나온다. 한 경계가 **진짜로** 다른 경계에 의존하면 그건 **엣지**로
표현되고, `topo_order`가 이미 올바르게 정렬한다. 연대순과 우연히 겹칠 수 있어도 같은 것이 아니다.

## 2. 구현의 두 층 — evaluate → certify

엔진은 두 단계로 갈라져 있다:

```
evaluate_graph(graph)                     # ① 의존순 계산
  topo_order(...)  →  노드별 분포 산출(kernels.compute)
        │
        ▼
_certify(run, graph, results)             # ② 사후 정합성 검사 (게이트)
  L1 순서 · L2 지속시간 …                  # 값을 읽고 판정만
```

① **evaluate** 는 위상정렬 순서로 각 노드의 분포를 계산한다. ② **certify** 는 그 결과를 받아 정합성
게이트([coherence-gate.md](coherence-gate.md))를 돌린다. **계산과 검사가 분리**돼 있다는 게 핵심.

## 3. order 노드의 실제 배선 — 값 노드의 출력 tap, 검사의 입력

order 노드가 process 노드에 "되먹이는" 것처럼 보이지만, 배선은 반대다:

- **값 노드**(published-age, age-depth-model 등): `older`/`younger` 는 **출력(source)**. 자기 분포를 그대로
  내보내는 tap일 뿐 — `kernels` 는 노드당 분포를 **하나** 내고, 모든 출력 포트가 그 동일 분포를 실어보낸다
  (source 포트는 값을 바꾸지 않음, 순수 배선).
- **order 노드**: `younger`(위)·`older`(아래) 는 **입력(target)**. 두 나이를 **받아서** `order_check` 커널이
  `{ok, gap}` 판정만 낸다 — **값 불변**(`engine/kernels.py`). 그리고 이 판정은 `_certify` 안에서 L1로 소비된다.

엣지 방향: `age-depth.older(출력) → order.older(입력)`. 즉 order 노드는 **말단 싱크(sink)** 다.

여기서 좋은 성질이 나온다:

> **검사는 관찰만 하고 계산 순서를 교란하지 않는다.** order 노드는 두 피연산자 뒤에 topo sort가 자동으로
> 놓고, order를 아무리 추가해도 값 만드는 노드들의 평가 순서는 바뀌지 않는다.

## 4. 세 가지를 갈라두라

"이웃 경계와 얽힌다"는 상황도 성격이 다 다르다:

| 관계 | 값이 흐르나 | 어떻게 처리되나 |
|---|---|---|
| order **검사** (현재) | ✗ (ok/gap 판정만) | 말단 싱크. topo sort가 뒤에 배치, 순서 문제 없음 |
| 상대연대 **전파** (예: B = A − Δ) | ✓ 방향성 | **진짜 데이터 엣지.** topo sort가 A→B 정렬(우연히 연대순과 겹침) |
| order **되먹임 제약** (가상) | ✓ 양방향 | 이웃끼리 커플 → **사이클** → clamp / joint |

두 번째가 중요하다: 상대연대 전파조차 엔진은 **시계를 보는 게 아니라 엣지를 따라갈** 뿐이다. "연대순"이
필요해 보여도 실제로 필요한 건 **의존순**이고, 그건 이미 처리된다.

## 5. "Hadean부터 훑는다"가 왜 잘못된 프레임인가

order를 검사가 아니라 **값을 조정하는 제약**으로 바꾸면(단조성을 만족하도록 clamp) — 이웃이 서로를 참조하게
되어 `process → order → process` **사이클**이 생긴다. 이게 topo sort가 깨지는 자리이자
[cycles.md](cycles.md)의 영역이다.

그리고 "old→young으로 쓸어간다"는 그 사이클을 푸는 **하나의 greedy·순차 방식**일 뿐이다. 문제:

- **방향에 결과가 의존한다.** 젊은 쪽 증거가 늙은 경계를 조여야 하는 경우(흔하다)에 정보가 한 방향으로만
  흘러 손실된다. **sweep 방향에 따라 답이 달라진다면 그건 냄새** — "이건 순서-무관한 joint 제약으로 빼라"는 신호.
- 원칙적 풀이는 **모든 제약을 한 번에 거는 동시추정(joint inference)** 이고, 순차 sweep은 그 열화판이다.
- 사이클은 sweep으로 해결되지 않는다 — **clamp(고정값으로 절단)** 하거나 joint로 푼다.

## 6. 정리 / 권장

- 평가 순서는 지금처럼 **의존성(topo sort)** 이 몰아야 한다. 연대순은 계산이 아니라 (a) age-depth 커널
  **내부**의 누중 제약(깊을수록 old), (b) 정합성 게이트의 **검사/제약**, (c) 서술·표시 **정렬** — 이 세 군데에 산다.
- **order = post hoc 검사**가 현재의 정직한 요약이다. "evaluate(의존순 계산) → certify(사후 시간정합 검사)"의
  두 층 분리를 유지할 것을 권한다.
- 순서가 값을 **실제로 조정**해야 한다면, 그건 그래프 순회 방향이 아니라 **coherence gate의 재조정(L3b) /
  clamp** 로 모델링할 자리다. → [coherence-gate.md](coherence-gate.md) §3, [cycles.md](cycles.md).

## 7. 남는 열린 질문

- order 노드를 **검사로만** 둘지, 언젠가 **되먹임 제약**으로 승격할지 — 승격 시 clamp vs joint의 갈림길.
- L2 지속시간처럼 **파생 검사**가 늘 때, certify 층의 순서·의존(검사끼리의 의존)이 생기는가.
- "sweep 방향 의존 = joint로 빼라"는 판정을 **자동으로 감지**할 수 있나(방향 뒤집어 재실행 후 diff).

## 8. 링크

- [node-graph-paradigm.md](node-graph-paradigm.md) — DAG·게이트웨이/네트워크·순환·엣지=분포
- [coherence-gate.md](coherence-gate.md) — Layer 5 검사 사다리(L1 순서·L2 지속시간·L3 재조정)
- [cycles.md](cycles.md) — 순환 의존과 clamp (order를 되먹임 제약으로 만들 때의 영역)
- [tier-category-model.md](tier-category-model.md) — data/process/clamp 카테고리(구현 후 회고)

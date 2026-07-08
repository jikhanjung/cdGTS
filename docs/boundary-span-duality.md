# 경계·구간 이중성 — 그래프 계층에서 (Boundary–Span Duality)

*[English](boundary-span-duality_en.md) · 한국어*

> 상태: **설계.** 그래프 계층(`graph` 앱)에서 **연대층서 골격**을 어떻게 표현할지 확정한다.
> chrono 가 이미 Unit(구간)/Boundary(점)을 분리해 둔 이중성을, 노드 그래프에도 1급으로 끌어올린다.
> 두 결정을 담는다: (1) 경계는 담기지 않고 참조된다, (2) order 노드를 없애고 경계 세로 포트를 직접 잇는다.

> **[구현 완료]** 이 설계는 전부 구현됨 — `nature` · `NodeGroup.kind/unit/lower/upper` · `Edge.kind=order` (graph/models.py), seed 반영.

## 0. 한 줄 논지

시대표의 골격은 **분할(partition)이 아니라 셀 복합체(cell complex)** 다. 구간(Period·Age…)은 1-셀,
경계는 그 끝을 공유하는 0-셀이다. 인접한 두 구간은 **항상 한 점을 공유**하므로, 경계는 "한 상자 안"에
담길 수 없다. 경계 노드는 어느 그룹의 멤버도 아닌 **독립 시민**이고, 구간(그룹)이 자기 경계를 *참조*한다.

## 1. 문제 — 왜 지금 구조가 역설을 만드나

현재 `NodeInstance.group` 은 **단일 FK**(`SET_NULL`) 다. 한 노드는 정확히 하나의 그룹에만 속한다 —
수학적으로 *분할*, 트리 포함이다. 모든 원소가 정확히 한 상자 안에 있어야 한다.

그런데 지질주상도는 분할이 아니다.

- 캄브리아기 하부 경계 = 에디아카라기 상부 경계 (**인접 구간이 점을 공유**).
- 캄브리아기 하부 경계 = 캄브리아기 첫 stage(Fortunian) 하부 경계 = Terreneuvian 하부 경계
  (**상·하위 구간이 lower 를 공유**). ICS 에서 이 셋은 같은 GSSP(Fortune Head) — chrono 에도
  **Boundary 객체 하나**(`base-cambrian`)다.

그래서 `base-cambrian` 노드는 캄브리아기 그룹의 "밖"(에디아카라기와의 seam)이면서 동시에 "안"(첫
stage 의 바닥)이어야 한다. "한 상자 안 하나"로는 표현할 수 없다. 이게 역설의 정체다.

## 2. 해법 — 경계는 담기지 않고 *참조된다*

직관("경계 노드는 독립적으로 존재해야 한다")은 맞다. 단, 구현은 **multi-membership(한 노드를 여러
그룹에 넣기)이 아니라 그 반대**로 간다.

- **구간(span) 그룹은 트리로 중첩.** Cambrian ⊃ Terreneuvian ⊃ Fortunian. 구간은 부모가 하나이므로
  트리가 깨지지 않는다. `NodeGroup.parent`(중첩)가 이미 이 축이다.
- **경계는 어느 그룹의 멤버도 아니다.** 대신 구간이 자기 경계를 가리킨다:
  `group.lower → 경계노드`(아래=더 오래된), `group.upper → 경계노드`(위=더 젊은).
  하나의 `base-cambrian` 노드를 에디아카라기가 `upper` 로, 캄브리아기가 `lower` 로, Terreneuvian 이
  `lower` 로 **동시에 참조**한다. 공유는 *노드 쪽*(한 노드가 여러 그룹에 속함)이 아니라 *그룹 쪽*(여러
  그룹이 한 노드를 가리킴)에 산다 — 단일 FK 로 깨끗하게 표현된다.

핵심 불변식: **경계가 "이 구간의 경계냐"는 경계의 속성이 아니라 (경계, 구간) 쌍의 속성**이다.
`base-cambrianstage2` 는 Cambrian 입장에선 *내부*, Cambrianstage2 입장에선 *bounding* 이다. 그러니
"~의 경계임"을 경계 노드에 새기지 않고, 구간의 `lower`/`upper` 로 둔다. 그러면 등장하는 경계 노드 수 =
서로 다른 chrono.Boundary 점의 수이지, 구간 끝점의 수가 아니다 (coincident 끝점은 한 노드로 dedup).

### 접기(collapse) 의미론

구간을 접으면 **내부**(하위 구간, 그 사이 내부 경계, 데이터/프로세스 기계장치)는 숨기고, **양 끝
bounding 경계는 port 로 노출**한다 — 지금 게이트웨이가 접힐 때 하는 동작 그대로다. 접힌 캄브리아기의
`lower`(base-cambrian)는 에디아카라기와의 seam 이므로 계속 보인다. 드릴인하면 내부 경계가 다시 나타난다.

## 3. 노드 성격 (nature) — 1급 속성

노드에 **성격(nature)** 을 명시한다. 지금은 node_type slug 에 암묵적으로만 있다.

- `NodeInstance.nature ∈ {generic, boundary}`.
  - **boundary** — 경계 점(0-셀). 독립 시민 — 그룹에 담기지 않고 참조된다. 조립 그래프에서 경계 값을
    담는 `published-age` leaf 가 이에 해당.
  - **generic**(기본) — 데이터/프로세스/clamp 기계장치.
- nature 는 **node_type 과 직교**한다. 파이프라인 그래프(예제 1–3)에서 경계는 process 노드 출력을
  Gateway 가 노출하는 형태다 — 그 노드는 generic 이고, 경계 정체성은 Gateway 가 진다. 조립
  그래프에서는 leaf 노드 자체가 boundary nature 다. **어느 쪽이든 bake/eval 의 앵커는 Gateway** 로 불변.

구간(span)은 노드가 아니라 **NodeGroup** 이므로 nature 를 그룹 쪽 `kind` 로 표현한다:

- `NodeGroup.kind ∈ {container, unit}`.
  - **unit** — 연대층서 구간(span). `unit`(chrono.Unit FK)로 정본 단위에 바인딩 → rank·이중명명 상속.
    `lower`/`upper` 로 두 경계 노드 참조.
  - **container**(기본) — 순수 표현용 묶음.

## 4. order 노드 제거 — 순서는 노드가 아니라 *연결*이다

지금은 두 경계 사이에 `order` 노드(예제 4 에 137개)를 두고 `gap ≥ min_gap` 을 검사한다. 하지만 경계
노드는 이미 **세로 order 포트**(위=younger / 아래=older, ICC 컬럼 관례)를 가진다. **포트를 잇는 연결선
자체가 순서 제약**이다. 별도 노드는 잉여다.

- 경계 노드끼리 세로 포트를 **시간순 사다리**로 직접 연결한다. 이 연결선 = **order edge**
  (`Edge.kind = order`). "source(더 오래된) 아래에 target(더 젊은)" 을 주장한다.
- **정합성 게이트 L1(order)** 은 order 노드의 판정 대신 **order edge 체인**을 읽는다: 각 order edge 의
  두 경계 값을 읽어 `younger < older`(gap ≥ min)를 검사, 사슬로 이어 단조성을 인증. 여전히 *authored ·
  sparse*(사람이 놓은 연결만 검사) — order 노드의 성질을 노드 없이 유지한다.
- order edge 는 데이터 흐름이 아니라 제약이므로 DAG 데이터 사이클 판정에서 분리한다(세로 사슬은 그
  자체로 DAG).

결과: 예제 4 에서 노드 수가 절반 가까이 준다(order 137개 소거). 골격이 **경계 점 + 이를 잇는 order
사다리 + 구간 그룹**으로 단순해진다.

## 5. 모델 변경 요약

| 대상 | 추가 | 의미 |
|---|---|---|
| `NodeInstance` | `nature` (generic\|boundary) | 경계 점을 1급으로. 독립 시민. |
| `NodeGroup` | `kind` (container\|unit) | 구간(span)임을 표시. |
| `NodeGroup` | `unit` (FK chrono.Unit, SET_NULL) | 정본 단위 바인딩(rank·이중명명). |
| `NodeGroup` | `lower` / `upper` (FK NodeInstance, SET_NULL) | 두 bounding 경계 참조(공유 가능). |
| `Edge` | `kind = order` | 경계 세로 포트 연결 = 순서 제약. order 노드 대체. |

불변식(문서화, 점진 강제):
- boundary nature 노드는 group 멤버가 아니다(`group = null`). 대신 그룹의 lower/upper 로 참조된다.
- 한 경계 노드는 여러 그룹의 lower/upper 로 공유될 수 있다(단일 FK, 그룹 쪽 다대일).
- 엔진은 여전히 평탄(nature/kind/unit 은 표현·정합용, 평가 위상 아님).

## 6. 기존 자산과의 정합

- **Gateway** 는 그대로 bake/eval 앵커(chrono.Boundary 연결). nature 는 Gateway 를 대체하지 않고 보완.
- **chrono** 의 Unit/Boundary 분리(및 Boundary.below/above)와 대칭 — 그래프 계층이 이제 같은 이중성을 가짐.
- **접힌 그룹 → port** 동작(devlog 039)과 **세로 order 포트**(devlog 049) 위에 얹는다.
- 관련 회고: [tier-category-model](tier-category-model.md) · [node-graph-paradigm](node-graph-paradigm.md).

## 7. 이행 (staging)

1. 스키마(§5) + 마이그레이션 — additive·nullable, 기존 그래프 무해.
2. 시리얼라이저 왕복 + `_certify` L1 을 order edge 로.
3. 시드 변환(예제 4): order 노드 제거 → order edge, 경계 nature, 구간 그룹 kind/unit/lower/upper.
4. 프론트: 새 필드 저장 왕복 보존(유실 방지) → seam 렌더·order 사다리 UI(후속).

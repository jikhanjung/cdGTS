# 레이어에서 티어 × 카테고리로

*[English](tier-category-model_en.md) · 한국어*

> 상태: **구현 후 회고(retrospective).** 브레인스토밍의 선형 레이어 L0~6([idea](idea.md) §5)이 실제 구현에서
> 어떻게 접혔는지 되짚는다. 새 설계가 아니라 이미 지어진 것의 재서술.

## 0. 한 줄 논지

**L0~6 선형 스택은 구현에서 두 축으로 분해됐다** — **티어**(registry / graph / release, §8.2의 게이트웨이
아키텍처)와, graph 티어 안의 **카테고리**(data / process / clamp). "레이어 번호"만이 인공물이었다.

## 1. 레이어 번호가 섞고 있던 두 가지

L0~6은 하나의 선형 축에 서로 다른 두 개념을 눌러 담고 있었다:

- **종류(kind)** — 노드가 *무엇인가*. 관측이냐 / 모델이냐 / 못박기냐. → **본질적**. U-Pb 노드는 어느 그래프에
  놓이든 항상 관측이다.
- **위치(position)** — 파이프라인에서 *어디쯤인가*. 앞이냐 뒤냐. → **비본질적·창발적**. 노드 타입의 속성이
  아니라 그 노드가 **특정 그래프에서 어떻게 배선됐는지**에서 나온다.

구현이 DAG가 되는 순간 "위치"는 라벨이 될 수 없다. age-model 출력이 또 다른 model로 들어갈 수도, correlation이
앵커처럼 쓰일 수도 있다. 그래서 1급 분류로 살아남은 건 **위치(레이어 번호)가 아니라 종류(카테고리)** 다.

## 2. 살아남은 것 — `NodeType.category`

구현의 유일한 노드 분류는 세 카테고리다 (`nodes.NodeType.category`):

| 카테고리 | 무엇 | 옛 레이어 | 예 (구현된 타입) |
|---|---|---|---|
| **data** | 불변·인용 관측 leaf. `params.distribution` 를 그대로 출력 | L2 | radiometric-uPb · astronomical · magnetostratigraphic · biostratigraphic · **published-age** |
| **process** | 입력 분포 → 산출 분포 (계산) | L3 · L4 · L5 | age-depth-model · cross-section-correlation · calibration-transfer · joint-inference |
| **clamp** | 값을 못박거나 제약 | (레이어 밖) | **order** (pin · range · freeze-version 는 제거됨 — [cycles](cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가)) |

L2가 data로, L3·L4·L5가 process로 접혔다. 레이어 번호는 "특정 DAG에서의 깊이"로 녹아 **분류가 아니라 창발
속성**이 됐다.

## 3. clamp — 어떤 레이어에도 집이 없던 카테고리

`clamp`은 레이어 모델에 자리가 없었지만 실제론 **두 레이어를 가로지른다**:

- **GSSA**(L1 경계 정의) = 저작된 `published-age` leaf (data 카테고리) — 점질량 δ. (당초 `pin` clamp 로 모델링했으나 재검토됨.)
- **정합성 제약**(L5 순서) = `order` 엣지 (range/pin clamp 은 제거됨).

레이어 번호로는 "L1과 L5가 같은 종류"를 표현할 수 없다. 카테고리로는 자연스럽다. 레이어가 옳은 절단면이
아니었다는 방증이자, [concept-map](concept-map.md) §3-2 "clamp가 통일자"의 구현 측 증거다 — 단, 이 "clamp 통일자"
전제 자체는 이후 재검토되어 별도 개념으로서의 clamp 는 축소됐다([cycles](cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가)).

## 4. 그래도 레이어가 완전히 사라진 건 아니다 — 티어

끝단(L0·L1·L6)은 애초에 노드가 아니라 **계약/티어**였다. 그래서 지금 구조는 사실상 **티어 × 카테고리**의 2차원이다:

```
티어    registry (chrono)  ──────  graph  ──────────────  release (releases)
                                    └ 카테고리: data / process / clamp
옛 매핑  L0 · L1                     L2 ~ L5                 L6
구현     Unit · Boundary ·           Graph · NodeInstance ·  Release · Selection ·
        Ratification · Locality     Edge · Gateway (engine)  BoundaryRecord · bake
```

- **티어**(registry / graph / release) = §8.2의 게이트웨이 아키텍처. 깨끗한 계약 세 칸.
- **카테고리**(data / process / clamp) = graph 티어 *안*의 노드 종류.
- **레이어 번호** = 특정 그래프 안의 배선 깊이로 창발.

즉 양 끝(L0/L1/L6)은 게이트웨이 계약이었고, 중간(L2~L5)만 카테고리로 이겼으며, **순수 선형 번호매기기만
인공물**이었다. 레이어는 이제 사람이 읽는 서사 순서(관측→모델→종합→배포)로만 유효하다.

## 5. 구현 상태와의 연결 (2026-07 기준)

- **티어는 견고**: registry(chrono) · graph/engine · release(releases) 3앱으로 1:1.
- **카테고리도 견고**: data/process/clamp 가 `category=="data"→params.distribution`, process→커널, clamp→order
  로 런타임 디스패치([engine.kernels](../engine/kernels.py) `compute`). (pin/range/freeze-version 은 제거, GSSA 는
  `published-age` data leaf 로 이관 — [cycles](cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가).)
- **얕은 곳은 여전히 얕다**: process 안에서 L4(correlation)·L5(joint/coherence)의 깊이는 미완 — 특히 전역
  정합성 게이트(`engine._certify`)는 나열순 monotonicity 스텁. 이건 티어/카테고리 재서술과 무관한 별개 과제.

## 6. 열린 질문

- data 카테고리 안의 이질성: 순수 관측(radiometric)과 "발표값 참조"(published-age)는 provenance 깊이가 다르다
  ([concept-map](concept-map.md) §3-1 provenance 축). 하위 구분이 필요한가, note 로 충분한가?
- clamp을 카테고리로 둘지, process의 특수형으로 둘지 — 현재는 별도 카테고리.
- 레이어 서사(읽기 순서)를 문서에 남길 가치가 있나, 아니면 티어×카테고리로 완전 대체하나?

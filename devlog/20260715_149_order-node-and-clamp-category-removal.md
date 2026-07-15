# 20260715_149 — `order` 노드 제거 → `clamp` 카테고리 소멸

> 성격: **정리(scope-down).** [devlog 135](20260711_135_clamp-scopedown.md)(clamp 축소)의 **미완 잔재 회수**.
> 계기: [노드 매뉴얼 자동 생성](20260715_R05_correlation-provenance-depth.md)(0.1.66)이 *"어떤 그래프도 쓰지 않는 타입 4개"*
> 를 표면화 — 사용자 판단: **`order` 는 정리, 나머지 3개는 존치.**

## 1. 왜 지금

devlog 135 는 "**order 제약 = order 엣지**"로 결정하고 `graph/models.py` 에 그렇게 적어두기까지 했다:

```python
ORDER = "order", "order"  # boundary vertical-port connection = order constraint (replaces the order node).
```

*"replaces the order node"* — 그런데 **그 order 노드를 실제로 지우지 않았다.** NodeType·Port·커널·L1 폴백 가지가
그대로 남아, 시드된 어느 그래프도 쓰지 않는 채 1개월 가까이 방치됐다. 매뉴얼이 없었으면 계속 못 봤을 것이다.

> **매뉴얼의 첫 수확**: 만든 목적("무엇이 정말 필요한가")이 만든 당일에 회수됐다.

## 2. 무엇을 지웠나

| 층 | 제거 |
|---|---|
| 시드 | `order` NodeType + Port 2개(`younger`·`older`) — `02_nodes.json` 57 → 54 객체 |
| 커널 | `order_check()` + `KERNELS["order"]` 레지스트리 항목 |
| 게이트 | `_certify` 의 **L1 중간 폴백 가지**(`elif order_nodes:` — mode=hard/warn 판정) |
| 모델 | `NodeType.Category.CLAMP` enum (→ 마이그레이션 `nodes/0004_alter_nodetype_category.py`) |
| 프론트 | 팔레트 그룹 `clamp` · `CdgtsNode` 의 clamp 색(`#a24bd8`) |
| 테스트 | order 커널 5종(`test_kernels.py`) + order 제약 L1 4종(`tests.py`) + 죽은 `_agein` 헬퍼 |

**`order` 가 clamp 카테고리의 마지막 멤버**였으므로 카테고리가 비었고, enum 에서도 뺐다(사용자 결정).
→ 남은 카테고리 = **data · process · reference** 3종.

## 3. L1 게이트가 어떻게 바뀌었나

**전**: order 엣지 > **order 노드** > 게이트웨이 단조 휴리스틱 (3단)
**후**: order 엣지 > 게이트웨이 단조 휴리스틱 (2단)

중간 단은 order 노드 인스턴스가 0개라 **한 번도 안 타던 죽은 가지**다. 판정 결과 변화 없음(실측: 재시드 후
행 수·경계 연대 동일).

## 4. 헷갈리기 쉬운 것 — `clamp` 이 가리키던 세 가지

이 정리에서 **하나만** 없앴다. 나머지 둘은 그대로다:

| 이름 | 무엇 | 이번에? |
|---|---|---|
| `nodes.NodeType.Category.CLAMP` | 그래프 노드 카테고리 | **제거** ← 이번 대상 |
| `releases.Clamp` | 릴리스 층 governance clamp (pin/range/order/freeze) | **존치** — DEMO-ONLY, `seed_demo` 시연용(cycles §12) |
| `engine.kernels.range_clamp` | 절단정규 커널 | **존치** — `releases/services.py` 의 L3b reconcile 이 사용 |

프론트의 `clampZoom`·CSS `line-clamp` 도 무관(수학 clamp).

## 5. 순환 breaker 는 무관함을 확인

`clamp` 카테고리가 cycle-breaker 였다면 제거가 순환 의미를 바꿨을 것이다. 실측: breaker 판정은
**`slug == "joint-inference"` 하나뿐**(`graph/serializers.py:175` · `engine/evaluate.py:201` ·
`graph/models.py:is_cycle_breaker`). docstring 이 "clamp/joint" 라 쓴 건 devlog 135 이전의 낡은 주석 → 함께 정정.

> 그래서 **`joint-inference` 는 인스턴스 0개여도 존치가 맞다** — 유일한 순환 breaker이고, 없으면 DAG 불변식상
> 순환을 끊을 수단 자체가 사라진다. "미사용 = 불필요"가 아닌 사례.

## 6. 남긴 것 (사용자 결정)

- **`joint-inference`** — 위 §5. 유일한 breaker. (⚠️ [R05](20260715_R05_correlation-provenance-depth.md) 는
  "`cross-section-correlation` 소멸 / `joint-inference` 생존"이라 봤는데, 정작 **미사용인 쪽이 `joint-inference`** 이고
  둘은 같은 커널이다 — R05 아크에서 재검토.)
- **`astronomical` · `magnetostratigraphic`** — 아직 안 쓴 여지. data leaf 라 유지 비용이 사실상 0.

## 7. 검증

- pytest **183 → 174** (order 테스트 9종 제거 = 183−9). 회귀 없음.
- 재시드 후 매뉴얼 재생성: **NodeType 16 · 미사용 3** · 카테고리 3종. 경계 연대·행 수 불변.
- ⚠️ **시드 + 마이그레이션 변경** → 배포 시 `--reseed` 필요. `nodes/0004` 는 enum choices 변경만(데이터 무손실).

## 관련

- [devlog 135](20260711_135_clamp-scopedown.md) — clamp 축소(본 정리의 원류) · [cycles §12](../docs/cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가) 후일담 추가
- [tier-category-model](../docs/tier-category-model.md) §2·§3 — 카테고리 표 갱신(KR/EN)
- [docs/node-manual.md](../docs/node-manual.md) — 이 정리를 촉발한 자동 생성 매뉴얼

# 20260711_135 — clamp 축소 (별도 개념 제거 · authored leaf 로 수렴)

[cycles.md §12](docs/cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가) 재검토 결론의 구현.
"clamp = 통일자"였으나 실사용은 GSSA 하나뿐(그래프 clamp 노드 `pin` 2개=둘 다 GSSA, `range`/`freeze-version`
0개, `releases.Clamp` 실 seed 0건=demo뿐)이라, **clamp를 별도 1급 개념/타입에서 제거하고 authored leaf 로 수렴**시킨다.

## 무엇이 무엇으로 접혔나

| clamp가 하려던 것 | 대체 |
|---|---|
| pin / GSSA | **authored `published-age` leaf**(exact) |
| 순환 절단 | **joint-inference 노드**(상호보정을 노드 *안*에 캡슐화) |
| order(단조성) | **order 엣지**(L1) — 이미 존재 |
| freeze-version | **버전축 나선**(게이트웨이) |
| release override | 필요 시 그래프 안 authored leaf + 재-bake |

## 변경

**① GSSA pin → published-age 이관 (핵심 증명).** `seed/03_graphs.json` 의 `gssa-decree` 노드 2개
(example-gssa-precambrian · example-icc-partial)를 `pin{value:2500}` → `published-age{distribution:
exact 2500}` 로. **재시드+평가 확인: 두 그래프 모두 base-proterozoic = 2500 Ma 로 동일** — authored leaf 가
pin 을 값 손실 없이 대체함을 실증.

**② 그래프 clamp NodeType 제거.** `seed/02_nodes.json` 에서 `pin`·`range`·`freeze-version` NodeType + 포트
행 제거(NodeType 19→16). `order` 는 L1 선후 검사 fallback 으로 남겨 clamp 카테고리 유지. `engine/kernels.py`
`compute()` 의 pin/range 디스패치 분기 제거(`range_clamp` *함수*는 reconcile 데모가 쓰므로 존치).

**③ cycle-breaker = joint-inference 전용.** `graph/models.py is_cycle_breaker` · `graph/serializers.py`
검증 · `engine/evaluate.py` 의 breaker 계산에서 `category==clamp` 조건 삭제 → joint-inference 만 순환을 접음.

**④ releases.Clamp / verify_clamps / reconcile 을 DEMO-ONLY 로 격리.** 모델·서비스 독스트링에 경고 명시,
Vault 탭 라벨 `Clamps` → `Clamps (demo)`. 기능·테스트·seed_demo 는 유지(통합은 하지 않음). provenance 구멍
(릴리스 tier out-of-band 값 수정) 근거도 독스트링에 기록.

**⑤ 미션 문구 개정.** "사람이 clamp" → **"사람이 authored 노드(값=leaf·선후=order)"** (HANDOFF · app-architecture 한/영).

## 검증

- 백엔드 `pytest` **165 passed**. 조정: `test_pin_emits_exact`→`test_published_age_emits_exact`, 엔진 테스트의
  pin 편의노드→`_exact_leaf`(published-age), `test_pin_clamp_has_value_param`→`test_graph_clamp_nodes_removed`
  (pin/range/freeze-version 부재 + clamp=order 만 단언), seed count 19→16.
- 재시드 후 GSSA 그래프 2종 평가 = 2500 Ma(동일). 프론트 `npm run build` 정상.
- ⚠️ **seed 변경** — 배포 시 `seed --mode=replace` 필요.

## 남긴 것 / 후속

- `order` NodeType(0 인스턴스지만 evaluate 의 order-node fallback 이 참조) · `range_clamp()` 함수 · releases.Clamp
  기계는 **의도적으로 존치**(각각 L1 fallback · reconcile 데모). 완전 제거는 별도 판단.
- cycles §12 의 "트리거"(접을 수 없는 실 순환 · 그래프 밖 거버넌스 override)가 나타나면 재검토.

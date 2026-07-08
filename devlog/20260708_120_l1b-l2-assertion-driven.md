# 20260708_120 — L1b/L2 를 "값 정렬" → "assert된 유닛" 기반으로 (P06.2b)

사용자 지적: **떨어져 있는 두 경계만 있는데 L1b warn 을 던지는 건 이상하다.** 선후를 order edge 로 잇거나 유닛으로
묶은 것도 아닌데 왜 순서를 판정하나. → 맞다. 기존 게이트는 **값을 정렬해 인접을 추론**했다("기계가 관계를 발명").
프로젝트 철학("사람이 놓고 기계가 검사")과 어긋남.

## 변경 — "주장 없으면 판정 없음"

`duration_gate(unit_dist, rank_of)` (rank 별 base 정렬 타일링) → **`duration_gate(pairs)`** (assert된 쌍만).
- 쌍은 **time unit(span) 노드**에서 나온다: order edge 인터리브로 유닛의 양 끝 경계를 물어(`base.younger→unit.older`,
  `unit.younger→top.older`) `duration = base − top` 검사. (유닛 없이 두 경계를 직접 order edge 로 이은 경우도 한 쌍.)
- **assert된 쌍이 없으면 L1b·L2 = skip.** 떨어져 있는 경계엔 경고 안 함.
- L2 = 어떤 쌍이든 duration ≤ 0(영-길이/역전) → fail. L1b = 공분산 인지 2σ 안에서 ≤0 가능 → warn.

`_certify`: 유닛 노드를 순회하며 order edge 로 양 끝 경계를 찾아 pairs 구성. 라벨은 게이트웨이 경계 slug(base- 제거).

### 왜 유닛인가 (구현 중 발견)
ICC 그래프의 order edge 는 `base→unit→base` 로 **인터리브**돼 있고 유닛 노드는 value_ma=None. 그래서 "order edge 한 개
= 한 쌍"으로 보면 유닛이 끼어 판정이 안 됨. 올바른 단위는 **유닛 스팬**(양 끝 경계). 이게 coherence-gate.md 의
"유닛 duration>0" 과도 정확히 일치.

## 데모 (사용자 요청: "그 둘 사이 time unit 도 넣어줘")

`seed_demo` 의 두 대비 그래프에 **Olenekian time unit** 노드 추가 + order edge 인터리브(직접 edge 제거).
이제 데모가 예제(example-icc-partial)와 같은 base→unit→base 패턴. 게이트는 이 assert된 유닛의 지속시간을 판정 →
independent=warn / shared=pass 그대로.

## 검증

- `duration_gate` 단위테스트 5개 새 시그니처로 갱신(+ **no-assertion→skip** 테스트 신규).
- `test_l2_duration_gate`(예제 그래프): 유닛 스팬 기반으로도 영-길이 → L2 fail 복구.
- 캡스톤: 데모 유닛 추가 후에도 warn/pass 유지.
- 전체 **pytest 137 passed**.

## 문서

coherence-gate.md(+en): "'인접'은 값이 아니라 assert된 구조" 원칙 명시. tutorial(+en) §2: 두 경계가
Olenekian 유닛+order edge 로 assert돼 있음을 설명.

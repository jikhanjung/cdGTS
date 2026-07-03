# 20260703_010 — 토폴로지 diff

> 브레인스토밍 단계 devlog. 요약 수준.

## 한 일

### 1. 문서화
`docs/topology-diff.md` (+ `_en`). 스키마 §4 "토폴로지 diff"를 펼침.
- **핵심:** 값 diff와 토폴로지 diff는 **직교하는 두 축.** 한 축이 0인데 다른 축이 거대할 수 있음
  (GSSA→GSSP = 값 ≈0, 토폴로지 큼 / 새 U-Pb = 값 큼, 토폴로지 0).
- **그래프/트리 diff 문제:** 안정 id 전제 + split/merge는 구조 추론 불가 → **명시적 lineage 선언** 필요
  (Git rename 탐지와 유사하되 큐레이션 기록).
- **연산 분류:** create/deprecate/rename/split·merge/rewire/retype/move.
- **표기 3층위:** edit-script(기계) / 2색 합집합그래프(시각) / 의미 changelog(사람).
- **연결:** clamp = retype 어휘(GSSA→GSSP = clamp 제거 + 서브그래프 추가), 게이트 재검증 트리거,
  매니페스트 diff = 거친 토폴로지, ICC/GTS diff 깊이 차이.
- **워크드 예시:** Cryogenian 전환 — retype이 값의 *모양*을 바꿈(스칼라 → 분포, ±0 → ±nonzero), 순진한
  값 diff는 표현조차 못 함.
- **펀치라인:** 변화 = **토폴로지 델타 → 전파 → 값 델타** (원인→결과 인과 합성). CI-for-science의 가장
  중요한 변화가 토폴로지이므로 필수.

### 2. 스키마 반영 (KR/EN)
- `identity.lineage` 신설(`op: created|renamed|split|merged|retyped|deprecated`, `from`) — diff 정렬의 전제.
- §4 "토폴로지 diff" 항목 **정리됨** 표시.

## 커밋

- (이 커밋) topology-diff KR/EN + 스키마 반영 KR/EN + README + devlog 010.

## 다음 후보

- 스키마 §4 **마지막 남은 열린 질문: 분포 표현**(value± vs 분포 요약/샘플).
- 또는 지금까지 9개 문서를 잇는 **통합 개념 지도** 정리.

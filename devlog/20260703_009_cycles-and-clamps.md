# 20260703_009 — 순환 의존성 + clamp 도입

> 브레인스토밍 단계 devlog. 요약 수준.

## 한 일

### 1. 문서화
`docs/cycles.md` (+ `_en`). node-graph 문서가 처음부터 짚은 순환 문제를 펼치고 해법 정리.
- **순환은 하나가 아님:** 생층서↔방사연대 / 천문↔앵커 / 붕괴상수↔교차보정 / age model↔correlation.
- **핵심 구분:** 국소 상호제약(진짜 순환 아님) vs 전역 보정 되먹임(진짜 순환).
- **국소 해법:** 베이지안 동시추정 노드 → 보너스로 게이트가 원하던 공분산이 딸려옴.
- **전역 해법:** 보정을 게이트웨이로 얼려 **버전 축으로 사이클을 편다**(나선/고정점 반복 = CD).

### 2. clamp 도입 (사용자 아이디어)
subcommission이 그래프 중간중간에 **hand-crafted clamp**를 놓아 사이클을 절단·권위 고정.
- **GSSA = `Clamp{kind: pin}`의 특수 사례** → 이미 갖고 있던 clamp를 일반 원시타입으로 승격.
- clamp 결: pin / range / order / freeze-version.
- 두 열린 문제 동시 해결: freeze line을 거버넌스가 긋고(위치=clamp), 나선을 damping.
- **정합성 게이트 재구성:** 단일 자동 게이트 → 흩어진 authored clamp + 잔여 검사. 자동 재조정(L3b)보다
  정직(갈라짐이 이름 붙은 귀속 가능 결정).
- **미션 재정의:** "자동 계산"이 아니라 "사람이 authoritative 노드를 clamp, 기계가 전파·정합·diff" →
  idea §7의 제3의 답.

### 3. 스키마·게이트 반영 (KR/EN)
- 스키마 §2에 **`Clamp`** 노드(owner·kind·value_or_bound·rationale·ratified·overridable_in_sandbox),
  `Release.clamps`, provenance 엣지 type(co-location|calibration-transfer) 주석, GSSA=clamp 통일.
- §4 "순환" 항목 **정리됨** 표시.
- coherence-gate L0에 **비순환 검사** 추가, 재조정을 authored clamp로 대체 권고.

## 커밋

- (이 커밋) cycles KR/EN + 스키마/게이트 반영 KR/EN + README + devlog 009.

## 다음 후보

- 스키마 §4 마지막 남은 열린 질문: **분포 표현**, **토폴로지 diff**.
- cycles §10: clamp 최소 집합 자동 제안, 나선 수렴 판정, clamp 충돌 중재.

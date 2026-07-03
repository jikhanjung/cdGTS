# 20260703_007 — 정합성 게이트 구체화 + 레이어 정수 재번호

> 브레인스토밍 단계 devlog. 요약 수준.

## 한 일

### 1. 정합성 게이트 문서화 (Layer 5)
`docs/coherence-gate.md` (+ `_en`). 핀된 경계 집합을 유효한 전 지구 차트로 바꾸는 메커니즘 =
**Layer 5(global synthesis) 노드의 정의**.
- **시그니처:** `coherence_gate(manifest, shared_node_graph, claimed_level) → PASS+certificate | violations[]`.
- **검사 사다리 L0~L3:** 구조 → 순서(점/구간) → 지속시간(공분산 필요) → 상관인지(검증 L3a / 재조정 L3b).
- **L2 공분산 핵심:** 지속시간 분산 = Var(old)+Var(young)−2·Cov. 공유 노드로 Cov>0 → 순진 계산은 과대평가.
- **중심 갈림길:** 검증 전용 vs 재조정. → **ICC(bake)=검증 전용, GTS(narrate)=재조정** 으로 깔끔히 매핑.
- **두 통찰:** (a) 정합성을 위협하는 건 비동기 독립 갱신이지 동기 공유 갱신이 아님, (b) 도달 가능한 정합성
  레벨은 provenance 기계가독성으로 상한 → idea §7과 직결.

### 2. 레이어 소수점 → 정수 재번호 (사용자 요청)
소수점 레이어(3.5/3.7)가 이상하다는 지적 반영. 매핑:
- **3.5 → Layer 4** (correlation)
- **3.7 → Layer 5** (global synthesis / 정합성 게이트)
- **기존 Layer 4(배포) → Layer 6**

idea.md §5를 정수 사다리 **0~6**으로 재구성(Layer 4·5를 정식 레이어로 승격), 그리고 모든 문서
(idea, node-graph, 세 케이스, 스키마) 한/영에서 참조를 일괄 갱신. 검증: 문서 전체에 소수점 레이어 0건.

## 커밋

- (이 커밋) coherence-gate KR/EN + 레이어 재번호(문서 다수 KR/EN) + README 인덱스 + devlog 007.

## 다음 후보

- 정합성 게이트 §6 열린 질문(재조정값 인용, L1b 정책, 공분산 추적 범위) 중 하나.
- 또는 스키마 §4의 "경쟁 모델 공존 방식".

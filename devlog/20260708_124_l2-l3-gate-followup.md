# 20260708_124 — L2/L3 게이트 확장 후속 (평가 + L2 fail 상세)

HANDOFF "후속"의 **L2/L3 확장** 항목 처리. 착수해 보니 대부분 이미 P06 에서 배포돼 있었고,
남은 실질 조각은 하나 — 그것도 도메인 판단이라 사용자 결정에 따라 **추가하지 않기로**.

## 현황 점검 (이미 배포된 것)

- **프론트 cert 뷰 L2 상세** — `ResultsPanel` 이 인증서 칩(L0/L1/L1b/L2/L3) + `checks.notes` 를
  이미 렌더(P06). "047 이월" 분은 사실상 완료.
- **L3 joint reconcile** — release 레벨 clamp reconcile(L3a verify / L3b reconcile)로 devlog 118 구현.
  `_certify` 내 L3 는 의도적으로 skip(reconcile 은 그래프 평가가 아니라 릴리스 거버넌스 액션).
- **L1b 2σ 겹침 warn**, **L2 duration ≤0 fail** — devlog 117·120 구현.

## 이번 변경 (도메인-무관, 안전)

- **L2 fail 상세 note** — `duration_gate` 가 퇴화(≤0) 쌍 라벨(`a↔b (Δ… ≤ 0)`)을 함께 반환하도록
  확장(반환 4-튜플). `_certify` 가 L2 fail 시 `checks.notes` 에 추가 → 프론트가 **어느 경계쌍이**
  퇴화인지 바로 표시. (종전엔 L1b 미해결만 note 가 있고 L2 fail 은 어느 쌍인지 안 보였음.)
  기존 `duration_gate` 테스트 언패킹 갱신 + degenerate-note 단언 추가.

## 결정 — L2 "과대/과소 duration" warn 은 추가하지 않음

- "과소" 지속시간은 이미 **L1b(2σ 겹침 warn) + L2(≤0 fail)** 로 통계적으로 커버.
- "과대(비현실적으로 긴)" 지속시간 warn 은 본질적으로 **rank 별 도메인 기대치**(임의 상한)가 필요.
  게이트를 도메인 상수 없이 통계적으로만 유지하는 편이 깔끔 → **추가하지 않음**(사용자 확정).
  필요해지면 rank 별 기대 범위(ICC 데이터 유도)로 후속 가능.

## 테스트

- engine pytest 통과(duration_gate 4-튜플 반영 + degenerate-note 단언). 풀 스위트 회귀 없음.

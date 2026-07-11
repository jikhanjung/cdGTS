# 20260711_134 — Tier-1 CI 플로우 시나리오 테스트 (+ gateway-wipe 버그 수정)

R02 리뷰([R01](20260707_R01_vision-implementation-review.md) 후속 논의)에서 나온 방향: 백엔드 pytest 는 강하지만
핵심 가치인 **로그인 → fork → 편집 → bake → diff → propose → ratify** 플로우는 문서상 "브라우저 검증 필요"로만
남아 있었다. 브라우저 E2E(Playwright)는 이 저장소(무CI·무JS테스트)엔 비용 과다 → **Tier 1 = pytest API 시나리오
테스트**를 먼저 붙인다. 핵심은 **실제 세션+CSRF 경로**로 태우는 것(기존 테스트는 전부 `force_authenticate` 라
CSRF 를 건너뜀).

## 시나리오 테스트 (`test_ci_flow.py`, 신규)

- **`Client(enforce_csrf_checks=True)`** + SPA 와 동일한 CSRF 왕복: `whoami`(@ensure_csrf_cookie)로 쿠키를 심고
  `X-CSRFToken` 헤더로 되돌려줌. 로그인 시 토큰이 rotate 되므로 매 write 마다 쿠키에서 재취득.
- **골든패스 한 판**: login → fork(시스템 그래프 딥클론) → 편집(published-age 538.8→537.0, PUT) → verify(공표
  baseline 대비 −3.0 Ma) → bake(불변 레코드 1건) → propose(sandbox→proposed, affected=base-cambrian) →
  ratify(개인 fork 저자는 403 → ICS chair 는 200, 새 baseline 537.0 · graph ratified · 구 baseline demote).
- **CSRF 실효성 가드**: 헤더 없는 세션 write 는 403 — 위 플로우가 요행으로 통과한 게 아님을 증명("pytest 초록,
  브라우저 403" 사각지대 차단).

## 발견·수정한 버그 — PUT 저장이 gateway 를 지움

시나리오를 조립하다 실측으로 확인: **`Gateway.node` 가 `on_delete=CASCADE`** 인데 그래프 PUT 의
`_replace_topology` 가 `graph.nodes.all().delete()` 로 전 노드를 지웠다 재생성한다 → **저장할 때마다 그래프의
boundary gateway 가 통째로 삭제**됨(재생성 없음). 즉 예제 그래프를 fork 해서 값 하나 바꾸고 저장하면, 이후
bake/verify/propose 가 경계를 하나도 못 찾는 상태가 됐다. 기존 테스트는 gateway 생성 후 PUT 없이 propose 만
해서 이 seam 을 못 건드렸다.

- **수정(`graph/serializers.py _replace_topology`)**: 삭제 전에 gateway 를 (slug·name·node key·output_port·
  boundary) 로 스냅샷 → 노드 재생성 후 **node key 로 재링크해 bulk_create**. 편집은 gateway 를 보존하고,
  boundary 노드가 삭제된 gateway 는 자연히 드롭(key 부재). create 경로는 기존 gateway 가 없어 no-op.
- 시나리오 테스트에 회귀 가드: 편집 저장 후 `gateways == 1` 단언.

## 검증

- 백엔드 `pytest` **166 passed**(기존 164 + 시나리오 2). `_replace_topology` 변경이 group/boundary 왕복·seed
  회귀 테스트에 영향 없음 확인.
- 배포: 테스트서버 **0.1.50**. gateway 보존은 편집→저장→bake 흐름의 실동작 변경이므로 테스트 서버에서 육안 확인 권장.

## 메모 / 다음

- **Tier 2(Playwright 해피패스 스모크 1개)**는 프론트 변경이 잦아질 때 옵트인 — 넣더라도 비블로킹(별도 `npm run
  e2e`, 릴리스 전 수동)로. 프론트 JS 배선(CSRF 헤더 실부착·버튼→엔드포인트)은 Tier 1 로는 안 잡히고 브라우저만 잡음.
- gateway-wipe 는 운영에도 있던 잠복 버그 — 0.1.50 을 운영 반영할 때 함께 닫힘(현재 운영 0.1.47).

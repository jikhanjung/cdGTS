# 20260708_111 — P05 가시성 취약점 차단 (리뷰 후속)

P05 diff 리뷰 지적: ViewSet의 소유권/가시성은 제대로 강제되나, **APIView 보조 엔드포인트들이 `get_object_or_404(pk)`
로 직접 조회**해 가시성 쿼리셋을 건너뜀 → 남의 private 샌드박스 그래프/릴리스 값이 순차 pk 열거로 유출(bake/narrate는
남의 객체에 write까지). P05.2가 세운 "남의 샌드박스=404" 약속과 정면 모순.

## 수정 — 단일 진실원(visibility helper) 재사용

- **`graph/permissions.visible_graphs(user)`** · **`releases/permissions.visible_releases(user)`**(+`can_write_release`).
  두 ViewSet의 `get_queryset`도 이 헬퍼로 통일(DRY).
- **가시성 필터 적용**(직접 pk 조회 → `get_object_or_404(visible_*(user), pk)`):
  - `GET graphs/{id}/icc-chart/` · `POST graphs/{id}/verify/` · `GET/POST graphs/{id}/bake/` → `visible_graphs`.
  - `GET releases/{id}/icc-chart/` · `POST releases/{id}/narrate/` · `releases/diff/`(a·b) → `visible_releases`.
- **write 게이팅**(남의/공유 객체 변조 차단):
  - `releases/{id}/bake/`(action, 레코드 재생성) → owner/staff(`can_write_release`)만, 아니면 403.
  - `narrate_release(release, persist=)` → owner/staff만 narrative 저장, 뷰어는 **렌더-온리**(sections엔 inline 포함).
  - release icc-chart의 lazy bake도 `can_write_release`일 때만.
- **settings** REST_FRAMEWORK 주석을 현재 상태(공개 read + 쿼리셋 가시성 필터 + write 게이팅)로 갱신.

## 검증

pytest **114 passed**(+2 신규: graph·release 보조 엔드포인트가 남의 private 샌드박스에 404). 기존 2개 조정:
익명 re-bake·narrate persist 테스트 → staff 인증(새 게이트 반영).

## 남은 미세항목(의도된 것)

- `ReleaseViewSet`/`ProposalViewSet`은 여전히 AllowAny지만 **공개 read(Vault·CI 리뷰)** 의도 + 쿼리셋이 가시성 필터.
- `verify`의 transient scratch 릴리스 write는 **visible 그래프 한정**(공개 데모면 익명도, 단 per-graph 스크래치·
  Vault 제외라 무해). 완전한 익명-무write가 필요하면 후속.

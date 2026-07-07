# 20260707_109 — P05.4: Propose / Review / Ratify (= CI)

[P05](20260707_P05_arc-c-multiuser-ci-platform.md) 4단계 = MVP의 마지막 조각. "science를 위한 CI"의 실체:
제안 → verify diff 리뷰 → 권한자 승인(새 공표 baseline) / 거절.

## 백엔드 (커밋 ad33bbf)

- **`Proposal` 모델** — graph↔baseline, state(open/merged/rejected), author, `affected`(영향 경계 집합),
  reviewer, review_comment, result_release. migration releases.0007.
- **services** — `verify_graph`/`diff_graph_vs_release` 리팩터, `affected_boundaries`,
  `propose_graph`(sandbox→proposed), `ratify_proposal`(→ 새 **published** baseline 1개로 교체, graph→ratified,
  proposal→merged), `reject_proposal`(→sandbox), `publish_graph`, `next_published_version`.
- **`accounts.permissions.can_ratify(user, proposal)`** — 중앙 판정 한 곳(Authority ICS/subcommission 멤버십).
  인터벌 스코프는 여기 `proposal.affected`로 후행 필터(P05 §확장). whoami가 `can_ratify` 노출.
- **엔드포인트** — `POST graphs/{id}/propose/`(owner), `ProposalViewSet`: 목록(?state)·상세(+리뷰 diff·can_ratify)·
  `ratify`·`reject`(권한자). GraphVerifyView도 `verify_graph`로 정리.

## 프론트

- **Proposals 뷰**(신규 nav) — 좌측 제안 목록(state 필터), 우측 리뷰: verify diff(summary·value_diff 표·topology)
  + 권한자면 코멘트 + **Ratify → publish** / **Reject**.
- **Editor Propose 버튼** — owner·sandbox일 때. 저장 후 propose → Proposals로 이동.
- api: propose/list/get/ratify/reject.

## 검증

pytest **110 passed**(+5: propose·owner-only·ratify가 baseline 교체·reject 복귀·상세 diff). build OK.

## 결과 = 아크 C MVP 완성

로그인 → fork → 편집 → (bake→Vault) / **propose → review → ratify**. P05.5(샌드박스 오버라이드)는 MVP 밖(아크 B seam).

## 알려진 한계(후속)

- 그래프당 open proposal 중복 방지 없음. · Editor의 status는 목록 재조회 전까지 stale(제안 후 nav 이동으로 완화).
- ratify는 전역(단일 ICS) — 인터벌 스코프는 훅만 준비됨.

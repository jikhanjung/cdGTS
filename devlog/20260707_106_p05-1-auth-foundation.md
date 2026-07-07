# 20260707_106 — P05.1: 인증 토대

[P05](20260707_P05_arc-c-multiuser-ci-platform.md) 1단계. 세션 인증 + User↔Authority 멤버십 + 프론트 로그인.
결정 1(세션 인증)·3(Authority 멤버십)의 토대.

## 백엔드

- **`accounts` 앱 신설** — `Membership`(user↔`chrono.Authority`, role owner/member/chair, unique(user,authority)).
  향후 ratify 권한(P05.4)·인터벌 스코프의 부착점.
- **시그널** — User `post_save`(created) → 개인 **fork Authority**(`user-<pk>`, kind=fork) + owner Membership 자동 생성.
- **엔드포인트**(`/api/auth/`) — `whoami`(`@ensure_csrf_cookie`로 CSRF 쿠키 프라임, 멤버십 포함),
  `login`(세션), `logout`.
- **DRF 기본 설정** — 인증=`SessionAuthentication`, 기본 권한=`IsAuthenticatedOrReadOnly`(**읽기 공개/쓰기 인증**).
  ⚠ 기존 뷰의 명시적 `AllowAny`는 그대로 → 익명 쓰기는 **P05.2에서 소유권과 함께** 잠금(지금 앱 안 깨짐).
- migration accounts.0001. 관리자에 Membership 등록(초대제 = admin이 계정/멤버십 생성).

## 프론트

- **CSRF** — `csrfHeaders()`가 `csrftoken` 쿠키를 `X-CSRFToken`으로 첨부. 모든 쓰기(create/save/evaluate/bake/
  verify/narrate/bake-release) 7곳 적용 → 로그인 사용자의 세션 쓰기가 CSRF 통과.
- **로그인 UI** — `LoginBar`(topnav 우측): 로그인 시 username(★=staff)+Logout, 아니면 Login 모달(초대제라 가입 없음).
  App이 마운트 시 `whoami`로 상태·CSRF 쿠키 확보. `.modal-backdrop`을 `position:fixed`로(앱 레벨 모달).

## 검증

pytest **100 passed**(+4: 시그널·whoami·login/logout·공개 읽기). build OK(204 modules).

## 다음

P05.2 — `Graph.owner` 강제 + 객체 수준 권한(owner/authority 멤버만 편집·bake), 가시성(sandbox=owner 전용),
Release 소유 → bake 이름 `<userid>` 세그먼트 활성. 여기서 기존 `AllowAny`를 실제 권한으로 교체.

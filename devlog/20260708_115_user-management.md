# 20260708_115 — 사용자 관리 + 내 프로필 편집 (0.1.32)

staff 관리자용 사용자 관리 화면과, 모든 사용자의 자기 프로필 편집.

## 백엔드 (accounts)

- **`user_payload`** 에 `first_name`·`last_name`·`email` 추가(whoami/login 응답).
- **`PATCH /api/auth/me/`**(`update_me`, DRF `@api_view`, IsAuthenticated) — 자기 이름·이메일 편집.
- **`UserViewSet`**(`IsAdminUser` = staff 전용, `/api/users/`):
  - list/retrieve/create(비번 포함)/partial_update(이름·이메일·is_staff·is_active).
  - `set_password`(≥6자) · `add_membership`/`remove_membership`(멤버십 추가·제거) · `authorities`(ICS/subcommission 목록).
  - 멤버십 액션은 `get_queryset().get(pk)` 로 **재조회 후 직렬화**(prefetch 캐시가 stale 이라 새 멤버십 반영 안 되던 것 방지).
- `UserSerializer`(memberships·can_ratify 포함)/`UserCreateSerializer`(set_password). urls: SimpleRouter + `auth/me/`.

## 프론트

- **아이디 클릭 → 내 프로필 다이얼로그**(LoginBar): 이름·이메일 편집 → `updateProfile` PATCH → whoami 갱신.
- **`System ▾` 드롭다운**(staff 전용, App nav) → **User management**. (항목 확장 가능한 컨테이너)
- **Users 페이지**: 목록(사용자·이름·이메일·역할칩·활성) + New user + Edit 모달(이름·이메일·staff/active,
  비번 재설정, 멤버십 add/remove 로 **ratify 권한 직접 부여**).

## 버그픽스 (함께)

- **nav 드롭다운이 아래 화면에 가려짐** — `.topnav { overflow-x:auto }` 가 overflow-y 까지 auto 로 만들어 클리핑.
  가로 스크롤은 모바일에서만 필요 → `overflow-x:auto` 를 ≤820px 미디어쿼리로 이동(데스크톱은 clip 없음).

pytest **117 passed**(+3: staff-only 게이트·CRUD·멤버십·프로필). 정식 0.1.32 배포.

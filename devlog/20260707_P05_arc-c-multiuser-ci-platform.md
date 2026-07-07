# 20260707_P05 — 아크 C: 멀티유저 "CI for science" 플랫폼 (계획)

R01 리뷰가 꼽은 두 미착수 아크 중 사용자 선택 = **C(멀티유저 플랫폼)**. P04(Editor→Bake→Vault) 위에 얹는다.

## 전제 / 위치

- **선행 = [P04](20260707_P04_editor-bake-vault-restructure.md)**: 아티팩트 = 불변 **Release**(Vault 보관),
  bake 이름에 `<userid>` 세그먼트 자리 예약(`GeologicTimeScale.Release.<userid>.YYYYMMDD.NN`).
- **큰 레버리지**: "CI"의 핵심 diff 엔진(`graphs/{id}/verify` = 제안 vs baseline 값/토폴로지 diff)이 **이미 있음**.
  이 아크는 새 과학이 아니라 그 위에 **사용자·권한·워크플로우 껍데기**를 씌우는 일.

## 이미 깔린 훅 (그대로 활용)

- `Graph.owner`(nullable, 미강제) · `Graph.status`(sandbox/proposed/ratified/deprecated).
- `Authority.kind`(ICS/subcommission/sandbox/fork) — 권한 주체. (User↔Authority `Membership`은 추가 필요.)
- `Clamp.overridable_in_sandbox` · `Release.is_baseline`.
- `graphs/{id}/verify` = PR 리뷰 diff의 알맹이.
- `config/settings.py`에 `REST_FRAMEWORK` 없음, 전 뷰 `AllowAny` ← 출발점.

## 목표 사용자 여정 (MVP)

로그인 → 공개 Vault(공표 ICC + 남의 ratified Release) 열람 → 관심 그래프 **fork** → 내 샌드박스에서 편집 →
**Bake**(내 Release) → baseline 대비 **diff** 확인 → **Propose**(제안) → 권한자 **리뷰**(verify diff) →
**Ratify**(승격 = 새 공표 Release) 또는 거절.

## 단계

- **P05.1 인증 토대** — `REST_FRAMEWORK` 기본(인증=**세션**+선택 토큰, 기본권한=`IsAuthenticatedOrReadOnly`).
  `User`(django auth) + `Membership`(User↔Authority·role). 가입 시 개인 Authority(kind=fork) 자동 생성.
  login/logout/whoami + 프론트 로그인 UI. **읽기 공개 / 쓰기 인증**.
- **P05.2 소유권 & 가시성** — `Graph.owner` 강제(생성=현재 사용자); 편집/평가-쓰기/bake는 owner(또는 authority
  멤버), 객체 수준 권한. 가시성: ratified/proposed 그래프 + 모든 Release 공개 읽기, sandbox = owner 전용
  (+공유 링크). **Release에도 소유 부여** → bake 이름 `<userid>` 세그먼트 활성. `status` 전이 규칙.
- **P05.3 Fork** — Graph 깊은 복제(nodes/edges/groups/gateways) → 새 owner, status=sandbox,
  `Graph.forked_from` FK. 프론트: Fork 버튼 · "내 그래프/내 Vault" · 원본 lineage.
- **P05.4 Propose / Review (= CI)** — Propose: sandbox→proposed, baseline Release 연결. 얇은 `Proposal`
  모델(author·baseline·target·state open/merged/rejected·reviewer·comment). **리뷰 화면 = 기존 verify diff
  재사용**(제안 vs baseline 값+토폴로지). Ratify: 권한 Authority(ICS/subcommission 멤버) 승인 → ratified
  (+새 공표 Release bake); 거절 → sandbox 복귀.
- **P05.5 샌드박스 오버라이드 (아크 B seam, MVP 밖)** — 샌드박스 = baseline Release + 경계별 override
  (`Selection` / `Clamp.overridable_in_sandbox`). competing-models "ICC-2024/12 쓰되 base-cambrian→model D".
  아크 B(경쟁모델·버전)와 만나는 지점이라 후속.

## MVP 컷라인

**P05.1 + .2 + .3 + .4(얇게)** = 로그인 → 공개 열람 → fork → 편집 → bake → diff 리뷰 → 승인/거절.
이게 "continuously deployed / CI for science"의 최소 실체.

## 확정 필요한 결정 (기본값 제안)

1. **인증 방식** — 세션(동일 오리진, 권장) vs 토큰/JWT.
2. **가입 정책** — 관리자 초대(MVP, 스팸/악용 회피) vs 공개 셀프 가입(후속).
3. **ratify 권한** — ICS/subcommission Membership 보유자.
4. **샌드박스 가시성** — owner 전용 + 공유 링크(권장) vs 공개 읽기.
5. **Proposal 모델 깊이** — 얇게(상태 + diff) vs 스레드 코멘트/리뷰(후속).

## 리스크 / 주의

- `AllowAny → 인증` 전환 시 기존 프론트 호출 전부 CSRF/인증 헤더 필요(회귀 위험). **공개 읽기 경로는 유지**.
- 소유·가시성 도입 시 seed/데모 그래프·Release의 `owner=null`을 **공용/시스템 소유**로 처리 필요.
- Release(P04)에 소유가 붙는 시점을 P05.2와 정렬.

## 문서 짝

- 개념 근거: idea §7(권위 vs 실험, 개인 fork), versioning-global-vs-per-boundary(샌드박스=baseline+override),
  competing-models(오버라이드). 필요 시 `docs/` 개념 문서(예: multiuser-sandbox-workflow) KR/EN 신설은 후속.

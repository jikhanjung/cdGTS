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
  모델(author·baseline·target·state open/merged/rejected·reviewer·comment · **affected=영향 경계/단위 집합**,
  verify diff에서 산출). **리뷰 화면 = 기존 verify diff 재사용**(제안 vs baseline 값+토폴로지). Ratify: 권한
  Authority(ICS/subcommission 멤버) 승인 → ratified(+새 공표 Release bake); 거절 → sandbox 복귀. **ratify
  판정은 중앙 함수 `can_ratify(user, proposal)` 한 곳**(§인터벌 스코프 대비).
- **P05.5 샌드박스 오버라이드 (아크 B seam, MVP 밖)** — 샌드박스 = baseline Release + 경계별 override
  (`Selection` / `Clamp.overridable_in_sandbox`). competing-models "ICC-2024/12 쓰되 base-cambrian→model D".
  아크 B(경쟁모델·버전)와 만나는 지점이라 후속.

## MVP 컷라인

**P05.1 + .2 + .3 + .4(얇게)** = 로그인 → 공개 열람 → fork → 편집 → bake → diff 리뷰 → 승인/거절.
이게 "continuously deployed / CI for science"의 최소 실체.

## 결정 (확정)

"보수적 MVP" 조합 — 1·2·4·5는 서로 맞물리고, 3이 거버넌스 축.

1. **인증 방식 = 세션(쿠키+CSRF)** — 동일 오리진 SPA엔 최소·표준·안전(HttpOnly, XSS 토큰탈취 없음).
   프로그램적 접근 필요해지면 DRF TokenAuth 병행. JWT는 현 규모에 과함(불채택).
2. **가입 정책 = 관리자 초대(승인제)** — 초기 소수 학자, 스팸/악용·데이터 품질 관리. fork/sandbox 격리 +
   ratify 분리가 안정되면 이후 공개 셀프로 개방(후속).
3. **ratify 권한 = Authority 멤버십 기반** — ICS/subcommission `Membership` 보유자만 승격 가능(실제 ICS
   거버넌스 반영). MVP는 단일 "ICS Authority"로 시작 → 점차 subcommission별 세분.
4. **샌드박스 가시성 = owner 전용 + 공유 링크** — 공식(ratified)·릴리스는 항상 공개, 샌드박스는 기본 비공개
   (제안 시 자동 공개). 미검증 값이 "공식처럼" 오해되는 것 차단. "공개 샌드박스" 옵트인은 후속.
5. **Proposal 모델 깊이 = 얇게** — `{author, baseline, target, state(open/merged/rejected), reviewer,
   한 줄 comment, affected(영향 경계/단위 집합)}` + 기존 verify diff 화면. 노드/경계별 스레드 코멘트는 후속.
   (`affected` 기록은 인터벌 스코프 권한의 전제 — 아래 §확장 지점.)

## 확장 지점 — 인터벌 스코프 권한 (후속, 지금 감안)

실제 ICS는 subcommission이 **시기(층서 구간)별**로 나뉜다(Cambrian·Permian Subcommission 등). 따라서
"그래프 전체"가 아니라 **특정 구간(= `chrono.Unit` 서브트리 / 경계 집합)**에 대한 ratify/거버넌스 권한이 도메인적으로
맞다. **MVP엔 넣지 않되(전역 ICS Authority 하나로 시작), 나중에 아프지 않게 두 훅만 "스코프-준비"로:**

- **Authority에 스코프 자리** — `Authority.scope_unit`(FK `chrono.Unit`, nullable=전역/ICS). 관할 = 이 Unit과 하위.
  `chrono.Unit`은 이미 parent 계층·rank, `Authority`는 이미 parent self-FK(ICS→subcommission) 보유 → 추가는
  **순수 additive**(지금 안 만들어도 나중 마이그레이션 1개). 지금은 이 필드를 열어만 두고 항상 null(=전역).
- **판정 중앙화 + Proposal의 `affected` 기록** — `can_ratify(user, proposal)`를 한 곳에 두고, Proposal이
  자기가 바꾸는 경계/단위 집합(`affected`, verify diff 산출)을 기록. 그러면 인터벌 스코프는 "ratifier의
  `scope_unit`이 `proposal.affected`를 전부 덮는가"라는 **후행 필터**로, 데이터 재설계 없이 추가된다. 여러 구간
  걸친 제안 → 여러 subcommission 승인(실제 ICS와 동형).

**즉 retrofit 난이도는 낮다.** 유일한 함정은 whole-graph·unscoped 가정을 여러 뷰/권한 체크에 흩뿌리는 것 —
그래서 P05.2/P05.4의 권한 판정을 처음부터 **중앙 함수**로 모으고 Proposal에 `affected`를 남기는 것이 유일한 선결.

## 리스크 / 주의

- `AllowAny → 인증` 전환 시 기존 프론트 호출 전부 CSRF/인증 헤더 필요(회귀 위험). **공개 읽기 경로는 유지**.
- 소유·가시성 도입 시 seed/데모 그래프·Release의 `owner=null`을 **공용/시스템 소유**로 처리 필요.
- Release(P04)에 소유가 붙는 시점을 P05.2와 정렬.

## 문서 짝

- 개념 근거: idea §7(권위 vs 실험, 개인 fork), versioning-global-vs-per-boundary(샌드박스=baseline+override),
  competing-models(오버라이드). 필요 시 `docs/` 개념 문서(예: multiuser-sandbox-workflow) KR/EN 신설은 후속.

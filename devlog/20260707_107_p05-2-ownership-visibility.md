# 20260707_107 — P05.2: 소유권 & 가시성

[P05](20260707_P05_arc-c-multiuser-ci-platform.md) 2단계. 기존 `AllowAny`를 실제 권한으로 교체. 결정 4(샌드박스
가시성)의 토대. **여기서부터 익명은 읽기 전용.**

## 백엔드

- **GraphViewSet** — `AllowAny` → `GraphAccessPermission`(신규 `graph/permissions.py`).
  - **가시성(get_queryset)**: 공개(proposed/ratified) + 시스템(owner=null 데모) + 내 그래프. 남의 샌드박스는
    목록에서 제외 → 직접 조회도 **404**(존재 은닉).
  - **쓰기**: 인증 + owner(또는 staff). owner=null 시스템 그래프는 staff만 편집.
  - **생성(perform_create)**: owner = 현재 사용자.
- **Release.owner** FK 추가(auth.User, null=시스템). `snapshot_graph(graph, label, user)`가 owner 기록 +
  이름에 `<user>` 세그먼트: `GeologicTimeScale.Release.<user>.YYYYMMDD.NN`(NN = user·day 순번).
  `GraphBakeView` → `IsAuthenticatedOrReadOnly`(bake = 인증 필요, 읽을 수 있는 그래프면 누구나 자기 Release로).
- 직렬화에 owner 노출(Graph·Release). migration releases.0006.
- **분석 뷰는 그대로 공개** — evaluate/verify/icc-chart/narrate/release-bake 는 `AllowAny` 유지(읽기 성격).

## 프론트

- App이 `user`를 Editor에 전달. `canEdit = 인증 && (owner==나 || staff)`, `canBake = 인증`.
- **Save**: 비-owner면 비활성 + 안내("fork to edit"/"sign in"). **Bake**: 미인증이면 비활성.
- **🔒 Read-only 배지**(save-state 자리) — 남의/시스템 그래프. 로그인 상태 바뀌면 그래프 목록 재조회.

## 검증

pytest **103 passed**(+3: 익명 쓰기 거부·비-owner 403·가시성 404/목록). build OK. 기존 그래프 PUT 테스트는
authenticated owner fixture로, seed bake 테스트는 force_authenticate로 갱신.

## 다음

P05.3 — **Fork**: 그래프 깊은 복제(nodes/edges/groups/gateways) → 새 owner·sandbox·`forked_from`. 데모를
편집하려면 fork(현재 소유 그래프 생성 경로). 프론트 Fork 버튼 + lineage.

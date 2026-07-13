# 20260713_140 — seed --mode=replace 레인 경계 (운영 데이터 보존)

[P08](20260713_P08_deploy-data-contract-retrofit.md) 의 최우선 항목 **P08.1(불변식 성립)** 구현.
cross-project 배포·데이터 계약(`../devdocs/wiki/deploy-data-contract.md`)의 핵심 불변식 —
*"`seed --mode=replace` 는 오직 시스템 정의 데이터만 건드린다"* — 을 cdGTS seed 명령에 실제로 세웠다.

## 문제 (잠복 footgun)

`releases/management/commands/seed.py` 의 `_delete_all()` 이 `graph.Graph`·`releases.Release` 등을
**`model.objects.all().delete()` 로 통째 삭제**하고 있었다. owner 필터가 없어, P05 로 들어온 **운영 데이터**
(학자 fork 그래프·owner-set bake·Proposal)가 `--mode=replace` 시:

- owner-set 그래프/릴리스가 **silent 삭제**,
- 시스템 baseline Release·ModelCandidate 를 지우면 운영 `Proposal.baseline`·`Selection.candidate`(둘 다
  **PROTECT**)가 막혀 **replace 자체가 ProtectedError 로 실패**하거나, 운영 Selection/BoundaryRecord 가
  시스템 `chrono.Boundary` **CASCADE** 로 딸려 삭제.

단일 사용자라 아직 안 터졌을 뿐, 멀티유저 운영을 여는 순간의 잠복 폭탄. (판별자는 이미 있었다 —
`Graph.owner`·`Release.owner` 가 `null = 시스템/공표`, set = 운영자.)

부수로 발견한 잠복 버그: `references.Reference` 가 `SEED_MODELS` 에 **누락** → replace 가 삭제는 안 하면서
재적재는 해서, 데이터 있는 DB 재replace 시 slug unique 중복 INSERT 위험.

## 전략 — delete-all+reload → upsert 하이브리드

참조 무결성을 지키려면 시스템 행의 **pk 정체성 보존**이 관건이라, 모델을 성격별로 갈랐다:

- **레지스트리**(chrono·nodes·**references**·candidate·Release·Selection) = **자연키 upsert**(제자리 갱신).
  기존 행을 자연키로 찾아 pk 를 실어 UPDATE → 운영 데이터의 PROTECT/CASCADE 참조가 안 깨진다.
- **graph 계열**(NodeInstance·Edge·Gateway 는 자연키 없음 → upsert 불가) = 시스템 그래프(owner NULL)만
  통째 삭제(CASCADE) 후 재생성. 운영 참조(fork `forked_from`·릴리스 `source_graph`)는 전부 SET_NULL 이라
  안전(딸려 삭제 없음).
- **파생물**(BoundaryRecord·engine 산출) = 시스템 스코프만 비우고 **시스템 릴리스만 재-bake**(운영 bake·eval
  캐시 보존).
- 픽스처에서 사라진 시스템 행은 **스코프 한정 prune**(자기참조 FK null 후 자식→부모 순).

`SYSTEM_SCOPE` 딕셔너리로 삭제/프룬을 owner-null(또는 부모 owner-null)로 한정. add 모드는 무변경.

## 한 일

1. `seed.py` `_delete_all()`+`_load_all()` → **`_replace()`**(삭제→스트림 upsert/insert→prune) + `_prune()` +
   모듈 헬퍼 `_scoped_qs`·`_natural_key`·`_existing_pk`. `_bake(only, system_only=)` 로 replace 는 시스템
   릴리스만 재-bake. `references.Reference` 를 `SEED_MODELS` 에 추가. 도크스트링에 레인 경계 규약 명시.
2. **회귀 테스트**(`test_replace_preserves_operational_data`) — owner-set 그래프(+노드)·릴리스, 시스템
   baseline 을 가리키는 Proposal, 시스템 candidate 를 가리키는 Selection 을 심고 replace → **전부 생존(같은 pk)**
   + 시스템 baseline/candidate **pk 불변**(=upsert 증명) + 시스템 예제 그래프 4 재구성 확인. 예전 코드였다면
   PROTECT 로 실패하거나 owner-set 행이 사라졌을 케이스를 고정.

## 검증

- 백엔드 **175 passed**(기존 174 + 신규 1). 기존 seed 멱등 테스트(`test_replace_on_populated_db_no_protectederror`,
  replace 2회)가 references upsert 멱등성까지 함께 커버.
- **운영 미러 dry-run**(`DATABASE_PATH=/srv/cdGTS/db.sqlite3 seed --mode=replace --dry-run`) — 실데이터 규모
  (279 노드 조립 그래프 포함)에서 `inserted 1056 · updated 794 · removed 1893`, **무예외**·롤백.

## 남은 것 (P08 후속)

- 알려진 한계: 운영 그래프가 **시스템 예제 그래프**를 `forked_from` 으로 가리키면, 그 예제는 삭제·재생성
  대상이라 replace 후 링크가 SET_NULL(계보 표기만 상실, 운영 그래프 자체는 무손상). 흔한 경로(타 사용자 그래프
  fork)는 무관.
- P08.2 매니페스트(`deploy.toml`) · P08.3 `DEPLOY.md` · P08.4 preflight/smoke/rollback · P08.5 `/healthz` ·
  P08.6 운영 git pull 제거.

*근거: `../devdocs/wiki/deploy-data-contract.md`(불변식·판별 기준) · [P08](20260713_P08_deploy-data-contract-retrofit.md) ·
관련 devlog 106~110(owner·Proposal)·P02/031~033(seed 통합·드리프트).*

# 20260713_P08 — 배포·데이터 계약 retrofit (계획)

cross-project **배포·데이터 계약**(`../devdocs/wiki/deploy-data-contract.md`, 2026-07-13 설계 세션 산물)을
cdGTS 에 적용하는 계획. cdGTS 는 계약이 지목한 **파일럿**(worker·seed·reseed·마이그레이션·백업을 다 exercise) 이라
여기서 되면 나머지 프로젝트는 부분집합이다.

## 계약 요약 (근거 문서)

세 수명주기를 분리한다:
1. **코드 레인(`deploy`)** — 이미지 + 마이그레이션. 멱등·교체 가능.
2. **시스템 시드 레인(`seed`)** — 시스템을 *정의*하는 참조 데이터(ICC 경계·NodeType·데모 그래프·공표 릴리스).
   리포에 버전관리, 배포와 함께 나가며 `--mode=replace` 안전.
3. **운영 데이터 — 파이프라인 밖** — 사용으로 *쌓이는* 데이터(학자 fork 그래프·bake·Proposal). 리포에 없고,
   운영에 살며, 백업이 잡고, **seed 가 절대 안 건드린다.**

> **불변식**: `seed --mode=replace` 는 오직 시스템 정의 데이터만 건드린다. 운영 데이터는 seed 가 닿지 않는 곳에
> 살고, 백업이 항상 잡는다. 배포 파이프라인은 운영 데이터를 나르지 않는다.

판별은 **모양이 아니라 출처(provenance)**: 개발자가 기본 상태로 저작 = 시스템 시드 / 운영자가 입력 = 운영 데이터.

## 현재 상태 (탐색 실측)

**좋은 소식 — 판별자가 이미 코드에 있다.** `graph.Graph.owner`·`releases.Release.owner` 둘 다
`null = 시스템/공표`, set = 운영자(학자). 시드 그래프 4개 전부 `owner: null`(seed/03_graphs.json). 즉 계약이
요구하는 provenance 경계선이 스키마에 존재하고 시드도 일관되게 따른다.

**나쁜 소식 — 시드 명령이 그 경계를 강제하지 않는다(불변식 위반).** `releases/management/commands/seed.py`
`_delete_all()` (L100-103) 이 `graph.Graph`·`releases.Release` 등을 **`model.objects.all().delete()` 로 통째
삭제**한다. owner 필터가 없다. 그래서 `--mode=replace` 는:

- owner-set 그래프(학자 fork/편집),
- 그 그래프로 bake 한 owner-set 릴리스,
- 이들을 참조하는 `Proposal`(애초에 `SEED_MODELS` 에도 없어 재적재 불가) · fork lineage

를 전부 지우고 cascade 로 딸려 보낸다. = 계약이 경고하는 **바로 그 reseed footgun**. 단일 사용자라 아직
안 터졌을 뿐. cdgts-app.md 의 "필요한 건 규율뿐" 진단보다 실제 작업이 조금 더 크다 — seed 코드가 물리적으로
경계를 강제하지 않는다.

**부분 구현된 것**(참조 구현에 근접): build/sync/deploy 책임 분리(`deploy/build.sh`·`sync_to_srv.sh`·
`host/deploy.sh`), prod 배포 전 원자적 DB 스냅샷(WAL 포함)+retention 20, nginx 점검 모드, 그리고 0.1.52 함정에서
나온 **DB-바인딩 검증 게이트**(`host/deploy.sh` [5/5]) = 계약의 `smoke` 도메인 불변식 정신 그 자체.

## 레인 분류 (1단계 결과)

| 레인 | 모델 | 판별 |
|---|---|---|
| **시스템 시드** | chrono.*(Authority·Unit·Boundary·Lineage·Ratification·Locality) · nodes.NodeType/Port · references.Reference · owner-null 그래프(example-*) · 공표/데모 릴리스(ICS-2024/12·Demo.*) | 개발자 저작 |
| **운영 데이터** | owner-set graph.Graph(+자식) · owner-set releases.Release(+Selection) · **releases.Proposal** · fork lineage | 운영자 입력 |
| **파생/캐시** | engine.EvalRun·NodeResult·CoherenceCertificate · releases.BoundaryRecord | 재생성 가능(=replace 시 정리해도 bake 로 복원) |

`releases.ModelCandidate`·`Clamp`·`CandidateOutput` = 현재 시스템 시드(데모). owner 없음 → 전량 시스템 취급 유지.

## 작업 항목 (계약 7단계 매핑, 우선순위순)

### P08.1 — 불변식 성립 (seed replace 스코핑) ★ 최우선·load-bearing — ✅ 완료([devlog 140](20260713_140_seed-replace-lane-boundary.md))

> **구현됨(2026-07-13).** delete-all+reload → **레지스트리 자연키 upsert(pk 보존) + 시스템 그래프만 삭제·재생성 +
> 파생물 시스템 스코프 재-bake + 스코프 prune**. 운영(owner-set) 그래프·릴리스·Proposal·Selection 이 replace 를
> 넘어 생존. `references.Reference` 누락(재replace 시 중복 INSERT 잠복 버그)도 함께 수정. pytest **175**(운영
> 데이터 생존 회귀 신규) · 운영 미러 dry-run(inserted 1056·updated 794·removed 1893, 무예외). 아래는 원안.


- `_delete_all()` 을 **시스템 소유 행으로 한정**: `graph.Graph`·`releases.Release` 는 `owner__isnull=True`
  필터, 자식(NodeInstance·Edge·Gateway·NodeGroup·Selection)은 **시스템 부모에 속한 것만** 삭제. owner-set 행과
  그 자식·Proposal 은 절대 안 건드린다.
- `_load_all()` 도 시스템 범위만 재적재(시드 파일은 owner-null 뿐이라 자연스러움).
- **경계 참조 FK 확인**: 운영 그래프의 `forked_from`·릴리스의 `source_graph`/`base` 가 시스템 행을 가리킬 때,
  시스템 행 삭제-재생성 사이 링크 보존. 전부 `SET_NULL` 이라 삭제 시 null 로 끊김 → **자연키 재링크** 또는
  **삭제 대신 upsert** 전략 검토(후자가 안전). 파생물(BoundaryRecord 등)은 재-bake 로 복원되므로 기존대로 정리.
- **회귀 테스트**: owner-set 그래프·릴리스·Proposal 을 심고 `seed --mode=replace` 후 **살아남는지** 검증
  (현재는 죽는다 → red→green). dry-run 미리보기도 동일 보장.
- 산출: seed.py 변경 + 테스트 1~2개. 프론트·마이그레이션 무관.

> **이걸 P05 멀티유저를 운영에 여는 전제조건으로 둔다.** 지금은 잠복 폭탄.

### P08.2 — 매니페스트 (`deploy/deploy.toml`) — ✅ 완료([devlog 141](20260713_141_deploy-manifest-and-notes.md))

> **작성됨(2026-07-13).** `deploy/deploy.toml` — image·db_path·has_seed·services·health·[verbs]·[targets.prod/test].
> prod=GCP dolfinid-2(`cdgts.paleobytes.info`, SSH 키)·test=m710q. 아래는 원안.

선언적 매니페스트로 프로젝트별 지식을 파일에 고정:

```toml
image      = "honestjung/cdgts"
target     = "dolfinid"                 # prod. test = m710q
health_url = "https://cdgts.paleobytes.info/healthz"
db_path    = "/srv/cdGTS"
has_seed   = true
services   = ["cdgts", "cdgts-worker"]  # worker = run_worker (P06.4a)
```

### P08.3 — DEPLOY.md (릴리스별 append-only 운영 델타 노트) — ✅ 완료([devlog 141](20260713_141_deploy-manifest-and-notes.md))

> **작성됨(2026-07-13).** 루트 `DEPLOY.md` — 상시 불변식(재시드·DATABASE_PATH 바인딩·migrate·Crossref) +
> 릴리스별 노트(최신→과거, 🔴 필수/🟡 주의/🟢 무조치). 0.1.3~P08.1 소급. 아래는 원안.

HANDOFF 산문에 흩어진 배포 caveat 를 얇은 정형 층으로 추출. 초기 항목(기존 릴리스 소급):
- `0.1.52`: compose 볼륨 파일→디렉터리 바인드. `.env` `DATABASE_PATH=/app/hostdb/db.sqlite3` 먼저 — 안 바꾸면
  이미지 내부 빈 DB 폴백([5/5] 게이트가 잡음).
- `0.1.51`·`0.1.55`: seed 변경 → `seed --mode=replace` + `seed_demo` 재시드 필요.
- 이후: 릴리스마다 한두 줄 append. `preflight` 가 이걸 권위 소스로 출력, devlog 는 2차.

### P08.4 — 동사 정형화 (`preflight`·`smoke`·`rollback` 신규, `deploy`·`seed` 재편) — ✅ 완료([devlog 142](20260713_142_deploy-verbs-and-healthz.md))

> **구현됨(2026-07-13).** `deploy/preflight.sh`(빌드 호스트: 위험 표면 git diff + seed 냄새 lint + DEPLOY.md 출력) ·
> `deploy/host/smoke.sh`(healthz 200 + 버전 일치 + 행 수) · `deploy/host/rollback.sh`(이전 이미지 + pre_deploy 스냅샷).
> `deploy.sh` 에 [6/6] smoke 자동 호출, `sync_to_srv.sh` 가 smoke·rollback 동기화. 아래는 원안.



`deploy/` 스크립트 관례 유지하되 계약 동사 이름·책임으로 노출:
- **`preflight`** (신규): 마지막 배포 태그 이후 `git diff` 에서 위험 표면(`migrations/`·`.env*`·`seed/`·
  `docker-compose*.yml`) 변경 자동 플래그 + 운영-데이터-seed 냄새 lint + `DEPLOY.md` 델타 출력. **기억 의존 0.**
- **`deploy`** ≈ 기존 `host/deploy.sh`(백업→스왑→migrate(entrypoint)→up)에 **(플래그 시) reseed** 단계 명문화.
- **`seed`** ≈ `manage.py seed`(P08.1 후 시스템 한정 보장).
- **`smoke`** (정형화): 기존 `/admin/login/` probe + DB 바인딩 게이트에 **버전 일치 + 핵심 행 수>0** 추가.
- **`rollback`** (신규): 이전 이미지 태그 + `backup/pre_deploy` 스냅샷 복원. 지금 스냅샷은 뜨지만 복원 경로가 없다.

### P08.5 — `/healthz` 엔드포인트 — ✅ 완료([devlog 142](20260713_142_deploy-verbs-and-healthz.md))

> **구현됨(2026-07-13).** `config/health.py` — 버전(`config.version.VERSION`) + DB 연결 + 핵심 행 수 → 200/503
> JSON. 시스템 시드 부재(빈 이미지 DB 폴백) = 503. 인증 없음. `config/urls.py` 에 `path('healthz', ...)`.
> pytest 3(ok/빈DB 503/무인증). 아래는 원안.

버전(`config.version`) + DB 연결 + 핵심 행 수(예: NodeType·Boundary>0) 를 반환하는 가벼운 뷰. `smoke` 가 찌른다.
현재 `deploy.sh` 가 `/admin/login/` 로 대용 중 → 정식화.

### P08.6 — 운영 git pull 제거 (후순위)

현재 `build.sh` 가 운영 호스트에 `git pull`+`sync_to_srv.sh`(host/* 복사)를 요구 → 운영 서버에 소스 체크아웃 필요.
`host/*`(compose·deploy.sh·maintenance)를 이미지에 포함하거나 별도 아티팩트로 배송 → repo 의존 제거. 인프라 변경이라
가장 무겁고 스테이크 낮음 → 마지막. (dolfinid passphrase 는 cdGTS 가 아니라 그 호스트 이슈라 여기선 범위 밖.)

## 착수 순서

1. **P08.1 (불변식)** — 실제 안전 문제, 좁은 변경. 먼저.
2. **P08.2·P08.3 (매니페스트·DEPLOY.md)** — 저비용, 기억 의존 감소 효과 큼.
3. **P08.4·P08.5 (동사·healthz)** — preflight/smoke 정형화.
4. **P08.6 (git pull 제거)** — 마지막, 선택.

**P08.1~P08.5 완료**(devlog 140·141·142). 남은 것은 **P08.6**(운영 git pull 제거) — 인프라 변경·후순위·선택.

## 범위 밖 (명시)

- 고가용성·무중단·정교한 모니터링 — 계약 명시적 비목표(스테이크 낮음).
- 다른 프로젝트(fcmanager·fsis2026) retrofit — 사용자 주도로 각 리포에서 별도.
- dolfinid passphrase 인증 재배치 — 호스트 인프라 이슈.

*근거: `../devdocs/wiki/deploy-data-contract.md` · 관련 devlog cdGTS P02/031~033(seed 통합·드리프트)·
106~110(accounts·owner·Release.kind·Proposal)·135(clamp 축소→replace 주의)·138(Editor 분해)·139(공유 보정 노드).*

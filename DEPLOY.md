# DEPLOY — 릴리스별 운영 델타 노트

> **성격**: 배포·데이터 계약(devlog [P08](devlog/20260713_P08_deploy-data-contract-retrofit.md))의 얇은 정형 층.
> devlog 는 "무슨 일이 있었나"의 서사라 배포 주의점이 산문에 묻히고·안 적히고·여러 릴리스 한 번에 배포할 때
> 읽는 범위 밖으로 샌다(lossy). 이 파일은 그 반대 — **배포자가 딱 필요한 것만**, 릴리스별 한두 줄, **append-only**.
> 배포 전 이 파일을 권위 소스로 읽고, 더 깊은 맥락이 필요할 때만 해당 devlog 를 2차로 참조.
>
> **규칙**: 새 릴리스는 맨 위(최신)에 추가. 항목 = `버전 — 조치(재시드·env·마이그레이션·주의)`. 조치 없으면
> "코드/프론트 전용, 조치 없음" 한 줄. 관례: 🔴 필수 조치 · 🟡 주의 · 🟢 무조치.
>
> 상시 절차(0.1.58~): (빌드호스트)`build.sh X.Y.Z` → (운영/테스트)`deploy-{prod,dev}.sh X.Y.Z [--reseed]`.
> `sync_to_srv.sh` 는 **최초 부트스트랩 전용**(self-heal 이후 상시 경로에서 빠짐). 상세 [deploy/README.md](deploy/README.md),
> 선언층 [deploy/deploy.toml](deploy/deploy.toml).

## 상시 불변식 (릴리스 무관)

- 🔴 **시드/레이아웃 변경 릴리스 → 재시드**. 0.1.57~ 는 **배포 시 `--reseed` 플래그**로 자동
  (`deploy-{prod,dev}.sh X.Y.Z --reseed` → migrate 후 smoke 전에 `seed --mode=replace` + `seed_demo`). 수동이면
  `docker exec cdgts python manage.py seed --mode=replace` + `seed_demo`. `add` 는 그래프를 slug 단위로 원자 skip →
  변경 반영 안 됨. **replace 는 P08.1(devlog 140) 이후 운영 데이터(owner-set 그래프·릴리스·Proposal)를 보존**
  (자연키 upsert + 시스템 그래프 재생성, 멱등). 데모 그래프는 시스템이라 replace 가 지움 → `seed_demo` 로 복원.
  빈 DB 최초 배포도 `--reseed` 로 채워야 smoke(healthz 행 수>0)가 통과.
- 🔴 **prod 최초/DB 이전 시 `.env` `DATABASE_PATH=/app/hostdb/db.sqlite3`** 확인. compose 가 **`/srv/cdGTS/db`**(0.1.64~,
  종전 whole-/srv)를 `/app/hostdb` 디렉터리로 바인드(WAL 공유). 이 경로를 벗어나면 컨테이너가 이미지 내부 빈 DB 로 폴백 →
  사이트가 빈 데이터로 뜬다(실데이터는 `/srv/cdGTS/db/db.sqlite3` 에 안전). `deploy.sh` [5/6] DB 바인딩 게이트가 배포 직후 잡아 실패시킴.
  **fresh 호스트 부트스트랩은 `mkdir -p /srv/cdGTS/db` 를 배포 계정 소유로 먼저**(entrypoint 가 이 디렉터리 소유 uid 로 gosu 드롭).
- 🟡 마이그레이션은 web entrypoint 가 자동 적용(`migrate --noinput`). 워커는 web 이 스키마를 올린 뒤 폴링만.
- 🟢 **배포는 웹+워커 둘 다 올린다**(0.1.60~): `deploy.sh` 재기동이 `docker compose up -d`(전 서비스)라 웹(cdgts)과
  워커(cdgts-worker) 모두 현재 이미지로 뜬다. (0.1.60 이전엔 `up -d cdgts` 라 prod 스냅샷 경로에서 워커가 빠졌음.)
- 🟡 Crossref 자동 메타데이터(0.1.49)는 컨테이너 외부망(api.crossref.org) 필요.
- 🟢 **git-free 배포**(0.1.56~): 상시 배포는 `deploy-{prod,dev}.sh X.Y.Z` — 모든 host 파일을 이미지에서 추출.
  **운영 서버에 repo 불필요.** 0.1.58~ 는 부트스트랩 파일(deploy-prod/dev.sh·_extract_and_deploy.sh)도
  이미지에서 **자기 치유**(self-heal)하므로 repo 는 영영 필요 없다(prod 에서 삭제 가능).
- 🟢 **git-free 부트스트랩**(최초 1회 또는 self-heal 도입 시): repo 없이 이미지에서 부트스트랩 파일만 심는다 —
  ```
  cd /srv/cdGTS && CID=$(docker create honestjung/cdgts:X.Y.Z)
  for f in _extract_and_deploy.sh deploy-prod.sh deploy-dev.sh; do docker cp "$CID:/app/deploy/host/$f" ./; done
  docker rm "$CID" && chmod +x _extract_and_deploy.sh deploy-prod.sh deploy-dev.sh
  ```
  이후 `deploy-{prod,dev}.sh X.Y.Z` 만으로 부트스트랩 포함 전부 self-heal. (`.env`·`db/`·`backup/` 는 유지.)
- 🟢 **롤백은 코드/DB 분리**(계약, 0.1.61~): `rollback.sh <이전> [--db=keep|restore]`. **`--db=keep`(기본)** = 이미지
  태그만 전환, 현재 DB 유지(배포 후 운영자 입력 보존). `--db=restore` = 정지 후 pre_deploy 스냅샷 복원(그 배포 창의
  운영 쓰기는 유실). **keep 가드**: 직전 배포가 migration 을 적용했으면(스냅샷 `.mig` 사이드카 vs 현재 비교) 이전 코드가
  새 스키마와 비호환일 수 있어 keep 을 막고 `--db=restore`/`--force` 로 승격. 기본값은 `deploy.toml rollback_db="keep"` 선언.
- 🟡 **prod SSL 리다이렉트 + smoke**: prod `.env` `SECURE_SSL_REDIRECT=True` 라 평문 HTTP 는 301(HTTPS)로 튄다.
  `smoke.sh`·deploy 대기 루프는 `X-Forwarded-Proto: https` 헤더를 실어(settings 의 SECURE_PROXY_SSL_HEADER)
  로컬 컨테이너를 직접 검증한다(0.1.57~ 반영). 수동 확인도 동일: `curl -sH 'X-Forwarded-Proto: https' http://127.0.0.1:8011/healthz`.

## 릴리스 노트 (최신 → 과거)

- **0.1.64** — 🟡 **DB 마운트 db/ 서브디렉터리 컷오버**(devlog 148) + 🟢 gosu HOME 명시. 🟡 **whole-/srv → `/srv/cdGTS/db`
  마운트로 축소** — 컨테이너가 `.env`(시크릿)·`backup/`·배포 스크립트를 못 보게 blast radius 축소(fsis/fcmanager 동형, cdGTS 예외 해소).
  `deploy.sh` [3/6] 이 옛 루트 DB 를 db/ 로 **1회 자동 `mv` 컷오버**(멱등, 컨테이너 정지 후) + `/srv/cdGTS/db.sqlite3 → db/db.sqlite3`
  **안전망 symlink**(컷오버 이전 이미지 재배포 대비). `.env` `DATABASE_PATH` 무변경(컨테이너 경로 동일). ⚠️ **one-way** — 컷오버
  이후 컷오버 이전 이미지를 full 재배포하면 옛 compose(whole-/srv)라 빈 DB 로 뜰 수 있으나 [6/6] smoke(boundaries=0)가 잡음
  (실데이터 안전); `rollback.sh --db=keep` 은 호스트 compose 유지라 안전. 🟢 **gosu 드롭 시 `HOME=/tmp`(+`MPLCONFIGDIR`)**
  (entrypoint, fsis 0.5.82 동형) — 미등록 numeric uid 의 비쓰기 HOME 함정 선제 차단, 동작 무변화. 마이그레이션 없음.
- **0.1.63** — 🟡 **3-repo 일관성 정렬 + hourly DB 백업**(devlog 147). 🟡 **hourly DB 백업 신설**(`scripts/backup_db.py`, fcmanager/fsis 동형 —
  sqlite online backup, 12개 유지; nginx conf 는 같은 호스트 fcmanager 스크립트가 커버). 배포 시 이미지에서 self-heal 추출.
  🔴 **최초 1회 cron 등록**(prod dolfinid, **완료 2026-07-14**): `0 * * * * /usr/bin/python3 /srv/cdGTS/scripts/backup_db.py >> /srv/cdGTS/backup/backup.log 2>&1`.
  ⚠️ backup_db.py 는 self-heal 한 세대 지연 → 이번 릴리스는 이미지에서 **1회 수동 부트스트랩** 필요(`docker cp /app/scripts/backup_db.py`); 다음 배포부터 자동.
  ⚠️ backup 디렉터리는 cron 실행 uid 소유여야 함(prod `/srv/cdGTS/backup`=1001 OK).
  🟢 **3-repo 일관성 정렬**(fsis/fcmanager 동형, 조치 없음): `deploy.sh` 직접 호출 기본 `DEPLOY_SNAPSHOT=1`(안전측),
  헬스 대기 `/healthz`(종전 `/admin/login/`), DB 게이트 `manage.py shell -c` 경유(종전 순수 `python -c`),
  smoke python3 JSON 검증 + 버전 인자 필수(종전 grep·선택), 매니페스트 `db_path` = DB 파일 전체 경로 표준.
- **0.1.62** — 🟡 **컨테이너 비-root 실행 전환**(devlog 146, 코드/이미지만·마이그레이션 없음). entrypoint 가 root 로 시작해
  마운트 디렉터리(`/app/hostdb`) **소유 uid 를 감지 → gosu 로 드롭**(prod 1001·test 1000). 웹·워커 둘 다 비-root. Dockerfile 에
  `gosu` 설치. `deploy.sh [5/6]` 에 **쓰기 프로브**(앱 uid CREATE/DROP) 추가 — 디렉터리 마운트 소유권 함정을 배포 직후 잡음.
  ⚠️ **전제**: 각 호스트에서 `/srv/cdGTS` 와 `db.sqlite3*` 가 **같은 비-root uid 소유**여야 한다(현재 충족). 어긋나면 [5/6]
  쓰기 프로브가 FATAL — `chown <uid>:<gid> /srv/cdGTS /srv/cdGTS/db.sqlite3*` 로 정렬. 양 서버 배포·검증(PID1 uid=1001/1000).
- **0.1.61** — 🟢 **배포·데이터 계약 외부 검토분 반영**(devlog 145, 코드/스크립트만·마이그레이션 없음). ⓐ **롤백 코드/DB 분리**
  (`rollback.sh --db=keep|restore` + keep 가드, §상시 불변식). ⓑ 매니페스트 `contract_version=1`·`rollback_db="keep"` 필드.
  ⓒ **self-heal 추출 안전망**(`_extract_and_deploy.sh` 가 교체 전 `bash -n` 검증 + `.previous` 보존). ⓓ `deploy.sh` 스냅샷이
  `.mig` 사이드카(배포 전 migration 수) 기록 — keep 가드 판정용. ⚠️ 호스트에 반영되려면 이 이미지로 **1회 배포**(self-heal 추출).
- **0.1.60** — 🟢 **워커 배포 버그 수정**(devlog 미기록·핫픽스). `deploy.sh` 재기동 `up -d cdgts`(웹만) → `up -d`(전
  서비스). 이전엔 prod 스냅샷 경로(`down` 후 웹만 up)에서 **워커(cdgts-worker, 비동기 평가)가 계속 부재**했음.
  0.1.60 배포 시 prod 에 워커 즉시 기동 확인. 이후 배포는 자동으로 웹+워커 둘 다. 조치 없음.
- **0.1.59** — 🟢 버전만 올림(코드 변경 없음). git-free 릴리스 플로우 end-to-end 검증용.
- **0.1.58** — 🟢 **부트스트랩 self-heal**(§git-free 배포). 도입 시 **최초 1회 git-free 부트스트랩**(§상시 불변식의
  docker cp 블록)으로 self-heal `_extract_and_deploy.sh` 를 심으면, 이후 배포가 부트스트랩까지 갱신 → repo 영영 불필요.
- **0.1.57** — 🟢 배포 스크립트 수정. ⓐ smoke prod SSL 대응(`X-Forwarded-Proto`, §상시 불변식). ⓑ `--reseed` 배포
  플래그(§상시 불변식). ⚠️ `--reseed` 를 래퍼로 흘리려면 새 `_extract_and_deploy.sh` 필요 → 0.1.58 self-heal 이전엔
  재부트스트랩(`sync_to_srv.sh` 또는 git-free docker cp) 1회.
- **0.1.56** — 🔴 **git-free 배포 전환(P08.6) — 이번 1회 부트스트랩 필요**. 호스트 배포 진입점이
  `deploy.sh` → **`deploy-{prod,dev}.sh`**(이미지에서 host 파일 추출)로 바뀜. 기존 호스트의 래퍼는 옛 2줄 버전이라,
  이번에 repo 머신에서 **`./deploy/sync_to_srv.sh` 1회** 실행해 새 래퍼(`deploy-prod/dev.sh`·`_extract_and_deploy.sh`)를
  설치한 뒤 `deploy-dev.sh 0.1.56` / `deploy-prod.sh 0.1.56`. 이후 릴리스는 git 불필요. 이 릴리스에 P08.1~P08.5
  포함(seed 레인 경계·/healthz·smoke·매니페스트). 🔴 seed 변경(P08.1) 포함 → 배포 후 `seed --mode=replace`.
- **P08.1** (0.1.56 에 포함) — 🟢 마이그레이션 없음(관리 명령만). `seed --mode=replace` 의미가
  delete-all → **운영 데이터 보존 upsert** 로 바뀜(devlog 140). 배포 후 재시드해도 학자 데이터 안전.
  `references.Reference` 재replace 중복 INSERT 잠복 버그 동봉 수정.
- **0.1.54~0.1.55** — 🔴 **재시드 필요**(`seed --mode=replace` + `seed_demo`). `calibration-constant` NodeType
  신규 + `seed_demo` demo-cov 그래프를 공유 노드 구조로 재구성(devlog 139). 마이그레이션 없음(시드/동적 UI).
- **0.1.53** — 🟢 프론트 전용(Editor 분해 2차 + e2e 스모크). 조치 없음.
- **0.1.52** — 🔴 **compose 볼륨 파일→디렉터리 바인드로 변경** — 배포 전 `.env` `DATABASE_PATH=/app/hostdb/db.sqlite3`
  먼저 확인(위 불변식). `deploy.sh` 에 DB 바인딩 검증 게이트 추가(현재 [5/6]). 🟢 프론트 분해 1차는 무조치.
- **0.1.51** — 🔴 **재시드 필요**. clamp 축소(devlog 135): GSSA pin→`published-age` leaf, `pin`/`range`/
  `freeze-version` NodeType 제거(시드 변경).
- **0.1.50** — 🔴 **재시드 필요**. gateway-wipe 버그 수정 + 예제 노드 재배치(시드 변경).
- **0.1.49** — 🟡 Crossref 자동 메타데이터 = 외부망(api.crossref.org) 필요. 로그인 필요 엔드포인트.
- **0.1.4** — 🔴 ICC 재시드(`seed --mode=replace`) — `example-icc-partial` 은 add 로 반영 안 됨(원자 skip).
  마이그레이션 graph.0002 자동 적용.
- **0.1.3** — 🔴 최초 운영 재시드(`seed --mode=replace`) — 드리프트 3건 해소. self-FK ProtectedError 수정 포함.

> 과거 전체 맥락은 `devlog/` · `HANDOFF.md`. 이 파일은 배포 조치만.

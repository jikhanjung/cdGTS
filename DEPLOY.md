# DEPLOY — 릴리스별 운영 델타 노트

> **성격**: 배포·데이터 계약(devlog [P08](devlog/20260713_P08_deploy-data-contract-retrofit.md))의 얇은 정형 층.
> devlog 는 "무슨 일이 있었나"의 서사라 배포 주의점이 산문에 묻히고·안 적히고·여러 릴리스 한 번에 배포할 때
> 읽는 범위 밖으로 샌다(lossy). 이 파일은 그 반대 — **배포자가 딱 필요한 것만**, 릴리스별 한두 줄, **append-only**.
> 배포 전 이 파일을 권위 소스로 읽고, 더 깊은 맥락이 필요할 때만 해당 devlog 를 2차로 참조.
>
> **규칙**: 새 릴리스는 맨 위(최신)에 추가. 항목 = `버전 — 조치(재시드·env·마이그레이션·주의)`. 조치 없으면
> "코드/프론트 전용, 조치 없음" 한 줄. 관례: 🔴 필수 조치 · 🟡 주의 · 🟢 무조치.
>
> 상시 절차(`build.sh`→`sync_to_srv.sh`→`deploy-{prod,dev}.sh`)는 [deploy/README.md](deploy/README.md),
> 선언층은 [deploy/deploy.toml](deploy/deploy.toml).

## 상시 불변식 (릴리스 무관)

- 🔴 **시드/레이아웃 변경 릴리스 → 재시드**. 0.1.57~ 는 **배포 시 `--reseed` 플래그**로 자동
  (`deploy-{prod,dev}.sh X.Y.Z --reseed` → migrate 후 smoke 전에 `seed --mode=replace` + `seed_demo`). 수동이면
  `docker exec cdgts python manage.py seed --mode=replace` + `seed_demo`. `add` 는 그래프를 slug 단위로 원자 skip →
  변경 반영 안 됨. **replace 는 P08.1(devlog 140) 이후 운영 데이터(owner-set 그래프·릴리스·Proposal)를 보존**
  (자연키 upsert + 시스템 그래프 재생성, 멱등). 데모 그래프는 시스템이라 replace 가 지움 → `seed_demo` 로 복원.
  빈 DB 최초 배포도 `--reseed` 로 채워야 smoke(healthz 행 수>0)가 통과.
- 🔴 **prod 최초/DB 이전 시 `.env` `DATABASE_PATH=/app/hostdb/db.sqlite3`** 확인. compose 가 `/srv/cdGTS` 를
  `/app/hostdb` 디렉터리로 바인드(WAL 공유). 이 경로를 벗어나면 컨테이너가 이미지 내부 빈 DB 로 폴백 →
  사이트가 빈 데이터로 뜬다(실데이터는 호스트에 안전). `deploy.sh` [5/5] DB 바인딩 게이트가 배포 직후 잡아 실패시킴.
- 🟡 마이그레이션은 web entrypoint 가 자동 적용(`migrate --noinput`). 워커는 web 이 스키마를 올린 뒤 폴링만.
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
  이후 `deploy-{prod,dev}.sh X.Y.Z` 만으로 부트스트랩 포함 전부 self-heal. (`.env`·`db.sqlite3`·`backup/` 는 유지.)
- 🟡 **prod SSL 리다이렉트 + smoke**: prod `.env` `SECURE_SSL_REDIRECT=True` 라 평문 HTTP 는 301(HTTPS)로 튄다.
  `smoke.sh`·deploy 대기 루프는 `X-Forwarded-Proto: https` 헤더를 실어(settings 의 SECURE_PROXY_SSL_HEADER)
  로컬 컨테이너를 직접 검증한다(0.1.57~ 반영). 수동 확인도 동일: `curl -sH 'X-Forwarded-Proto: https' http://127.0.0.1:8011/healthz`.

## 릴리스 노트 (최신 → 과거)

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
  먼저 확인(위 불변식). `deploy.sh` 에 [5/5] DB 바인딩 검증 게이트 추가. 🟢 프론트 분해 1차는 무조치.
- **0.1.51** — 🔴 **재시드 필요**. clamp 축소(devlog 135): GSSA pin→`published-age` leaf, `pin`/`range`/
  `freeze-version` NodeType 제거(시드 변경).
- **0.1.50** — 🔴 **재시드 필요**. gateway-wipe 버그 수정 + 예제 노드 재배치(시드 변경).
- **0.1.49** — 🟡 Crossref 자동 메타데이터 = 외부망(api.crossref.org) 필요. 로그인 필요 엔드포인트.
- **0.1.4** — 🔴 ICC 재시드(`seed --mode=replace`) — `example-icc-partial` 은 add 로 반영 안 됨(원자 skip).
  마이그레이션 graph.0002 자동 적용.
- **0.1.3** — 🔴 최초 운영 재시드(`seed --mode=replace`) — 드리프트 3건 해소. self-FK ProtectedError 수정 포함.

> 과거 전체 맥락은 `devlog/` · `HANDOFF.md`. 이 파일은 배포 조치만.

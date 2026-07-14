# 20260714_146 — 컨테이너 비-root 실행 + 배포 게이트 쓰기 프로브

계약(`../devdocs/wiki/deploy-data-contract.md` §동사 deploy)에 **디렉터리 마운트 소유권 함정**(fcmanager 0.6.16~0.6.17)이
추가된 걸 계기로, cdGTS 운영서버 DB 디렉터리 소유권을 점검하고 **컨테이너를 비-root 로 전환**했다.

## 점검 결과 — 지금은 문제 없음(root 라서)

prod(dolfinid) 확인: 컨테이너 `id` = **uid=0(root)**. 마운트 디렉터리 `/srv/cdGTS`(소유 1001)와 무관하게 root 라
쓰기 가능(`DIR_WRITABLE` + Django `DB_WRITE_OK` 확인). fcmanager 가 걸린 건 비-root uid 1000 이 디렉터리 소유자와
어긋난 경우였고, cdGTS 는 root 라 그 조건 자체가 성립 안 했다.

**그러나 안전한 이유가 "root 로 돌기 때문"**이라는 게 문제. 언젠가 보안 하드닝으로 비-root 로 바꾸면 **바로 그 순간
prod 에서 함정에 빠지고**(디렉터리 소유 1001 ≠ 컨테이너 uid), 테스트 서버(m710q, uid 1000=배포계정)에선 재현이 안 돼
소리 없이 샌다 — 계약이 경고한 시나리오. 그래서 지금 제대로 비-root 로 전환.

## 조건 — cdGTS 는 안전하게 전환 가능

| 호스트 | 마운트 dir 소유 | db 파일 소유 |
|---|---|---|
| prod (dolfinid) | uid **1001** (gid 0) | 1001:1002 |
| test (m710q) | uid **1000** (gid 0) | 1000:1000 |

각 호스트에서 **"디렉터리 소유자 = db 파일 소유자"가 이미 일치**. 호스트마다 uid 가 달라(1001 vs 1000) Dockerfile
`USER` 고정은 못 쓴다 → **런타임에 마운트 소유자를 감지해 그 uid 로 드롭**.

## 한 일

- **`deploy/entrypoint.sh`** — root 로 시작 → `$HOSTDB`(/app/hostdb = 마운트) 소유 uid 감지 → collectstatic(web,
  이미지 static 쓰기라 root 로 먼저) + 잔존 root 소유 DB 형제 파일 소유 정리 → **`gosu <uid:gid>` 로 드롭** → migrate·
  gunicorn·worker 는 비-root 로. 마운트가 root 소유면 기존대로 root(폴백). **호스트 무관·chown 불요**(소유자를 따라감).
  worker(인자 `run_worker`)도 같은 드롭 경로 → 웹·워커 둘 다 동일 uid 로 DB 쓰기(WAL 형제 파일 일관).
- **`deploy/Dockerfile`** — `gosu` 설치(USER 고정 안 함 — 시작은 root, entrypoint 가 드롭).
- **`deploy/host/deploy.sh` [5/6] 게이트에 쓰기 프로브 추가**(계약 fcmanager 0.6.17) — 읽기 경로 게이트로는 소유권
  함정을 못 잡으니, 앱과 **같은 uid**(`docker compose exec -u <마운트 소유자>`)로 임시 테이블 CREATE/DROP 하여 실제
  쓰기 가능성을 배포 직후 검증. readonly(소유권 오배치)면 배포를 FATAL 로 중단.

## root↔비-root 상호운용(admin exec)

`docker exec cdgts python manage.py seed/...` 는 이미지 기본 USER(root)로 실행돼 root 로 DB 를 쓴다. 장수 앱(gunicorn,
uid 1001)이 이미 -wal 을 열어 소유하고 있으면 root exec 는 그 기존 -wal 을 쓸 뿐 새 root 소유 파일을 만들지 않아 안전.
entrypoint 의 `umask 002` + DB 형제 파일 소유 정리로 잔존 불일치도 흡수. (신규 파일이 root 소유로 생기는 fresh-DB
경계만 유의 — 그 경우 migrate 가 앱 uid 로 먼저 만든다.)

## 상태 — 양 서버 배포·검증 완료(0.1.62)

- 로컬 `bash -n` 통과. `build.sh 0.1.62`(pytest 178·gosu 포함 이미지 재빌드·push).
- **실배포 완료** — `deploy-dev.sh 0.1.62`(m710q) → `remote-prod.sh 0.1.62`(prod). 둘 다 [5/6] 쓰기 프로브 통과·smoke green.
- **비-root 실검증**(host PID1 uid — `docker exec` 은 root 라 무의미, 실제 프로세스 uid 로 확인):
  - test: gunicorn·run_worker 둘 다 **uid 1000**, 로그 `entrypoint: drop → uid 1000:0`.
  - prod: gunicorn·run_worker 둘 다 **uid 1001**, 로그 `entrypoint: drop → uid 1001:0`. 공개 HTTPS healthz = 0.1.62.
  - **쓰기 프로브 uid = 앱 uid**(test 1000·prod 1001) 로 CREATE/DROP 성공 → 비-root 쓰기 실동작 확인(prod 가 테스트 못 하는 부분).
- 롤백 필요 시 entrypoint/Dockerfile revert + 재빌드·배포(코드만·마이그레이션 없음). 또는 `rollback.sh <이전> --db=keep`.

*근거: `../devdocs/wiki/deploy-data-contract.md`(§동사 deploy 디렉터리 마운트 소유권 함정·쓰기 프로브) · [145](20260713_145_deploy-contract-external-review.md).*

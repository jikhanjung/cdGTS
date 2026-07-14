# 20260714_148 — DB 마운트 db/ 서브디렉터리 컷오버 (blast radius 축소)

cdGTS 는 `/srv/cdGTS` **전체**를 컨테이너 `/app/hostdb` 로 마운트해왔다. 그래서 앱이 뚫리면(RCE) 비-root 라도
마운트 소유 uid 로 도는 프로세스가 `.env`(시크릿)·`backup/`(스냅샷+hourly 백업)·배포 스크립트를 읽거나 덮어쓸 수
있는 blast radius 문제가 있었다. fsis·fcmanager 는 이미 **db/ 전용 서브디렉터리만 마운트**하도록 전환 → cdGTS 만
유일 예외로 남아 있었다. 이번에 그 예외를 해소(3-repo 정렬 완성).

## 계약 예외의 명분이 약했다

계약이 cdGTS 를 예외로 둔 근거는 "web·worker 다중 컨테이너가 DB 를 공유해야 한다"였는데, 검토 결과 약하다 —
두 컨테이너가 똑같이 `/srv/cdGTS/db` 를 마운트하면 그만이다(WAL 형제 파일은 여전히 같은 디렉터리에서 공유).
fcmanager 는 컷오버를 `deploy.sh` 의 1회 자동 `mv` 로 처리한 선례까지 만들어 뒀다.

## 변경 표면 — 예상보다 작음(핵심 두 개 무변경)

- **무변경**: `.env` `DATABASE_PATH`(컨테이너 경로 `/app/hostdb/db.sqlite3` 동일 — 마운트 **소스**만 바뀜) · DB 바인딩
  게이트 `EXPECT_PREFIX=/app/hostdb/`.
- **변경**: compose 마운트 2곳(`/srv/cdGTS` → `/srv/cdGTS/db`) · `deploy.sh`(정본 `$DB=$ROOT/db/db.sqlite3` + 컷오버 +
  스냅샷 소스 + 쓰기 프로브 stat 대상) · `rollback.sh` 복원 경로(db/ 폴백) · `deploy.toml` `db_path` · `sync-cdgts-db.sh`
  원격/로컬 경로(전환기 폴백) · 문서. `backup_db.py` 는 이미 `_DB_NEW if exists else legacy` fallback 준비돼 무변경.

## 멱등 컷오버 + 안전망

`deploy.sh` [3/6] 이 옛 루트 DB 를 감지하면 **1회 자동 이행**(컨테이너 정지 후 `mv db.sqlite3 → db/`, +wal/shm).
가드 `[ -f root/db.sqlite3 ] && [ ! -L ... ] && [ ! -e db/db.sqlite3 ]` 로 멱등. 이행 후 `ln -sf db/db.sqlite3
root/db.sqlite3` **안전망 symlink** — 컷오버 이전 이미지(옛 compose = whole-/srv 마운트)로 실수 재배포해도 상대경로
symlink 로 DB 를 찾는다. symlink 은 db/ 마운트 밖이라 정상 steady-state 의 blast radius 엔 영향 없음.

## one-way 경계 (부드러움)

- **`rollback.sh --db=keep`(기본) 안전** — 호스트 compose 는 컷오버판(db/ 마운트)이 유지(롤백은 compose 미변경), 이전
  이미지도 `/app/hostdb` 사용 → DB 찾음. 복원 경로도 db/ 폴백 처리.
- **위험은 컷오버 이전 이미지의 full 재배포뿐** — 옛 compose(whole-/srv) 추출 → `/srv/cdGTS/db.sqlite3`(symlink) 경유로
  대부분 찾지만, 못 찾아도 [6/6] smoke(`boundaries=0`)가 **큰 소리로 배포 실패**시킴(조용한 데이터 손실 아님, 실데이터는 db/).

## 검증 (0.1.64, 양 서버)

- build 0.1.64(pytest) → deploy-dev(m710q, **실제 컷오버**) → remote-prod(dolfinid, 실제 컷오버).
- 확인 항목: DB 가 `db/db.sqlite3` 로 이동 · 컨테이너가 `/app/hostdb`=db/ 마운트 · **컨테이너에서 `/app/hostdb` 에 `.env`·
  `backup/` 안 보임**(blast radius 축소 실증) · 비-root(uid 1001/1000) · 쓰기 프로브(마운트 소유자) · smoke green · 안전망 symlink 설치.

*근거: `../devdocs/wiki/deploy-data-contract.md`(§동사 deploy — DB 마운트/컷오버 · fcmanager mv 선례) · [146](20260714_146_nonroot-container.md)·[147](20260714_147_three-repo-consistency-align.md).*

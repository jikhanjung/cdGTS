# 20260703_026 — DB/배포 분리 + 운영→테스트 DB sync (fsis 패턴)

> [025](20260703_025_deploy-0.1.1-devtest.md) 후속. 개발/테스트 서버에서 배포는 DB 를 건드리지 않고,
> DB 는 운영서버에서 cron 으로 받아와 테스트용으로 쓴다. fsis2026 `scripts/backup-fsis.sh` §7 참조.

## 한 일

### deploy.sh: DB 미터치
- pre-deploy DB 스냅샷 블록 **제거**. 배포 = 이미지 스왑만(pull → .env → `compose up -d` → 헬스체크, 4단계).
  DB 볼륨(`/srv/cdGTS/db.sqlite3`) 유지. `backup/` 불필요.

### DB sync 스크립트 (`scripts/sync-cdgts-db.sh`, 신규)
- fsis `backup-fsis.sh` 의 DB pull + dev 동기화 패턴을 cdGTS 용으로 축약(uploads 없음 → DB 만).
- 동작: 운영서버 `scp /srv/cdGTS/db.sqlite3`(+wal/shm) → `~/backups/cdGTS/db_history/db_YYYYMMDD.sqlite3`
  (계층 보관: N일 초과 월초만·12/01 영구) + `current/` → **테스트 DB(`/srv/cdGTS/db.sqlite3`) 교체**.
- 안전 교체: 컨테이너가 DB 를 열고 있으므로 `stop → cp → up -d`(라이브 파일 스왑 회피). wal/shm 정리.
- cron: `0 4 * * * .../scripts/sync-cdgts-db.sh`. `REMOTE_HOST`(운영 주소) 확인 필요.

### README
- DB 관리 섹션 추가(배포와 분리). deploy.sh 표기 갱신(“DB 안 건드림”).

## 검증
- `bash -n` 두 스크립트 OK. deploy.sh `/srv/cdGTS` 재동기화.
- **DB 스왑 경로 로컬 검증**(scp 제외): 현재 DB 를 mock 스냅샷으로 stop→copy→up → 재기동 후
  `/api/node-types/` 200, 노드타입 12 정상. 컨테이너 Up.
- scp pull 은 운영서버 필요 → REMOTE_HOST 설정 후 실행(현재 미검증).

## 후속 (사용자)
- `scripts/sync-cdgts-db.sh` `REMOTE_HOST` 를 실제 운영서버로 설정 + crontab 등록.
- 운영서버 배포는 별도(사용자). 운영 DB 가 이 sync 의 source of truth.

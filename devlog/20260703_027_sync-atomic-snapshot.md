# 20260703_027 — DB sync 원자적 스냅샷 (WAL torn-copy 회피)

> [026](20260703_026_db-sync-deploy-separation.md) 후속. 운영서버 Claude 의 리뷰 지적 반영.

## 배경 (지적 사항)

026 의 `sync-cdgts-db.sh` 는 운영 live `db.sqlite3` + `-wal` + `-shm` 를 **각각 따로 scp** 했다.
WAL 모드에서 이 셋은 서로 다른 시점일 수 있어(운영 컨테이너가 그 사이 write), torn/불일치 사본이
나올 위험이 있다(hot-copy 문제). 트래픽 낮으면 대개 무해하지만 완전 일관은 보장 못 한다.

## 한 일

- pull 방식 교체: 운영서버에서 **sqlite online backup API(`src.backup(dst)`)로 원자적 스냅샷**을 만든 뒤
  그 **단일 일관 파일만 scp**. writer 가 있어도 일관 스냅샷을 보장(fsis `backup_db.py` 와 동일 방식).
  - 운영 host `python3`(sqlite3 모듈) 확인 → `ssh dolfinid python3 - <src> <dst>` heredoc 으로 실행.
  - 임시 스냅샷 `/srv/cdGTS/.db_sync_snapshot.sqlite3` 생성 → scp → 원격 삭제(정리).
- 스냅샷이 이미 단일 파일이라 dev 교체에서 `-wal/-shm` 복사 제거(남은 것은 정리만).
- README DB 관리 섹션에 방식 명시.

## 검증 (SSH whitelist 후 실서버)

- `honestjung@cdgts.paleobytes.info`(dolfinid-2) 로 sync 실행 exit 0.
- pull(원자적 스냅샷) 480K → `~/backups/cdGTS/db_history/db_20260703.sqlite3`.
- 스냅샷 `PRAGMA integrity_check = ok`, `-wal/-shm` 없음(단일 파일).
- 운영 임시 스냅샷 잔여 없음(정리 확인).
- 컨테이너 정지→교체→재기동 후 로컬(8011) = 운영 복사본(graphs `['sandbox']`, node-types 12).

## 비고

- 이 개선은 dev/test 스크립트 한정. 운영서버엔 변경 없음.
- SSH 접근: 사용자 탐색 중 실패 인증으로 이 서버 IP(1.234.232.37)가 운영 fail2ban 에 걸렸다가
  whitelist(`ignoreip`) 후 해제. `~/.ssh/config` 에 `dolfinid` 별칭 추가됨.

# 20260709_130 — WAL + 평가 write 원자화 (멀티컨테이너 SQLite 동시 접근)

web(gunicorn)과 worker([123](20260708_123_p06-4a-async-eval-worker.md)) 두 컨테이너가 **하나의 SQLite
파일**을 공유한다. "두 컨테이너 동시 접근에 문제 없나?"라는 질문에서 출발해 동시성 방어를 강화했다.

## 진단 (기존 상태)

- `OPTIONS`: `timeout=20`(busy_timeout 20s) + `transaction_mode='IMMEDIATE'` → writer 경합의
  deadlock snake 방지 + 20초 재시도. 여기까진 OK.
- 그러나 `journal_mode=delete`(rollback) — 커밋 시 EXCLUSIVE 락이 **reader 까지** 잠깐 막는다.
- `evaluate_graph` 가 `transaction.atomic` 없이 `EvalRun.create`(루프 전) → 계산 루프 → `bulk_create`
  순 → 중간 실패 시 **NodeResult 없는 반쪽 EvalRun** 잔존 가능(정합성 문제).

## 함정 (WAL + 파일-단일 마운트)

compose 가 DB **파일 하나**만 마운트(`/srv/cdGTS/db.sqlite3:/app/db.sqlite3`)했다. 이 상태로 WAL 을
켜면 `-wal`/`-shm` 형제 파일이 각 컨테이너의 `/app/` 사설 레이어에 생겨 **web·worker 가 서로의 커밋을
못 본다**(컨테이너별 사설 WAL 로 분기) — delete 모드보다 나쁨. WAL 은 접근자들이 `-wal`/`-shm` 을
공유해야 하고, 그러려면 DB 가 든 **디렉터리**를 같은 inode 로 공유 마운트해야 한다(동일 호스트 → 커널
page cache·mmap 공유로 정상 동작).

## 변경

- **`settings.py`** — `OPTIONS['init_command'] = 'PRAGMA journal_mode=WAL;'`. reader 가 writer 에
  안 막힘. single-writer 유지(writer 경합은 timeout 흡수).
- **`deploy/host/docker-compose.yml`** — 두 서비스 볼륨을 파일 → **디렉터리** 마운트로 변경
  (`/srv/cdGTS:/app/hostdb`). host DB 파일 위치는 그대로(이동 없음), `-wal`/`-shm` 이 host
  `/srv/cdGTS/` 에 생겨 두 컨테이너 공유 + `deploy.sh` 스냅샷(47–48행, 이미 `-wal`/`-shm` cp)이 잡음.
- **`.env(.example)`** — `DATABASE_PATH=/app/hostdb/db.sqlite3`.
- **`engine/evaluate.py`** — 무거운 계산 루프는 트랜잭션 **밖** 유지(락 점유 짧게), 쓰기 꼬리
  (`EvalRun` 생성 + `NodeResult` bulk_create + `_certify`)만 `transaction.atomic()` 으로 묶음 →
  반쪽 EvalRun 제거. row 는 run 생성 전이라 튜플로 모아 두고 커밋 단계에서 `NodeResult` 로 변환.

## 검증

- pytest 게이트 통과(build.sh). engine 55 passed.
- 배포 후 테스트서버(0.1.44):
  - `journal_mode=wal`, `busy_timeout=20000`, `db=/app/hostdb/db.sqlite3`.
  - host 에 `db.sqlite3-wal` + `db.sqlite3-shm` 생성 확인(공유 디렉터리 마운트 동작).
  - worker 가 같은 DB 조회(ref count 일치) — 데이터 온전, 분기 없음.

## ⚠️ 운영 배포 주의

프로덕션 `/srv/cdGTS/.env` 를 배포 **전에** `DATABASE_PATH=/app/hostdb/db.sqlite3` 로 변경해야 함
(DB 파일 이동 불필요). 안 바꾸면 컨테이너가 옛 경로를 못 찾아 **빈 DB 를 새로 생성**. compose 는
`sync_to_srv.sh` 가 자동 반영되지만 `.env` 는 host 관리라 수동. (`deploy-prod.sh` 는 배포 전 스냅샷 있음.)

## 메모 / 다음

- 진짜 확장(다중 worker / 고빈도 쓰기)이 오면 Postgres + `SELECT FOR UPDATE SKIP LOCKED` 로 전환.
  잡 로직은 `engine/jobs.py`(`claim_next_job`/`process_job`)에 격리돼 있어 인터페이스 유지 가능.

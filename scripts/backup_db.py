#!/usr/bin/env python3
"""cdGTS 운영(dolfinid) hourly DB 백업 — sqlite3 online backup API.

fcmanager/fsis2026 의 backup_db.py 와 동형(계약 — 운영 데이터의 안전망은 파이프라인이 아니라 백업).
종전 cdGTS 운영 백업은 pre_deploy 스냅샷(배포 시) + m710q daily pull(scripts/sync-cdgts-db.sh,
NAS 오프사이트 포함)뿐이라 최악 손실창 24h — hourly 트랙을 추가해 형제 프로젝트와 정렬(2026-07-14).

  - DB: sqlite3 online backup API (컨테이너가 쓰는 중에도 일관 스냅샷)
  - 스냅샷마다 PRAGMA integrity_check → **실패하면 채택도 prune 도 하지 않는다**(아래 참조)
  - 최근 RETAIN_COUNT 개만 유지(오래된 것부터 삭제)
  - pre_deploy 스냅샷 retention 은 deploy.sh 가 단독 관리(20개) — 여기서 건드리지 않는다
    (fsis 에서 두 곳이 다른 수치로 같은 디렉터리를 prune 하던 충돌 교훈, 2026-07-14).
  - nginx conf 백업은 같은 호스트(dolfinid)의 fcmanager backup_db.py 가 이미 hourly 수행 — 중복 생략.
  - 배포 시 이미지에서 self-heal 추출(deploy/host/_extract_and_deploy.sh).
  - cron 등록(최초 1회, dolfinid honestjung crontab):
      0 * * * * /usr/bin/python3 /srv/cdGTS/scripts/backup_db.py >> /srv/cdGTS/backup/backup.log 2>&1

무결성 검사를 왜 여기 두나 (0.1.68, devlog 150)
------------------------------------------------
목적은 **탐지가 아니라 로테이션 오염 방지**다. `backup()` 은 소스 페이지를 충실히 복사하므로 소스가
깨져 있으면 스냅샷도 조용히 깨진 채 만들어지고, 매시 로테이션이라 **RETAIN_COUNT 시간이면 성한 스냅샷이
전부 prune 된다.** 손상을 늦게 알아차리는 것보다 이쪽이 훨씬 위험하다 — 복구 대상 자체가 사라지므로.
그래서 규칙은 두 줄이다:

  1. 스냅샷이 검사에 걸리면 **채택하지 않는다**(로테이션에 안 들어감) + **prune 을 건너뛴다**(과거 성한 것 보존).
  2. DB 디렉터리에 센티넬 파일을 남긴다 → /healthz 가 stat 만 해서 degraded 반환 → **배포마다 도는 smoke 가 잡는다.**

센티넬이 backup/ 아닌 db/ 에 있는 이유: 0.1.64 가 컨테이너 시야에서 backup/ 을 뺐다(blast radius).
컨테이너가 보는 건 /srv/cdGTS/db → /app/hostdb 뿐. MAILTO 미설정이라 cron 실패는 backup.log 에만 남고
아무도 안 읽으므로, 사람이 이미 보는 경로(smoke)에 물리지 않으면 검사는 연극이 된다.

⚠️ **3-repo 정렬 예외**: fcmanager/fsis2026 의 backup_db.py 에는 아직 이 기능이 없다(devlog 147 이
   동형화해둔 상태에서 cdGTS 만 선행 — P08 때와 같은 파일럿). 검증 후 포팅할 것.
"""
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path('/srv/cdGTS/backup')
# 현 레이아웃 = whole-/srv 디렉터리 마운트(DB 가 /srv/cdGTS 루트, cdGTS 예외 — web·worker 공유).
# DB 전용 하위 디렉터리(db/)로 컷오버하면(계약 일반 권고) 새 경로가 우선.
_DB_NEW = Path('/srv/cdGTS/db/db.sqlite3')
_DB_LEGACY = Path('/srv/cdGTS/db.sqlite3')
SOURCES = [
    ('cdgts', _DB_NEW if _DB_NEW.exists() else _DB_LEGACY),
]
# 매시 1개 → 최근 24시간 유지. **일일 오프사이트 pull(04:00, m710q→NAS 90일)과 창을 맞춘 값** —
# 12 였을 땐 하루 중 절반만 시간 단위 granularity 가 있어 두 트랙 사이에 틈이 생겼다. 24 면
# hourly 창이 daily 주기를 온전히 덮는다. 비용은 무시할 만하다(DB 1.1MB → 약 26MB).
# ⚠️ fsis/fcmanager 는 아직 12 — 이 값만 갈라진다(무결성 게이트 이식 때 함께 판단할 것).
RETAIN_COUNT = 24
MIN_FREE_GB = 2        # 백업 디렉토리 여유가 이 미만이면 abort (디스크 풀 방지)

# DB 디렉터리(= 컨테이너의 /app/hostdb)에 놓는 손상 플래그. config/health.py 가 stat 한다.
SENTINEL_NAME = 'INTEGRITY_FAIL'


def log(msg: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)


def integrity_check(path: Path) -> list[str]:
    """PRAGMA integrity_check — 통과면 [], 실패면 문제 문자열 목록(빈 목록이 아니면 손상).

    읽기 전용 URI 로 연다: 검사 대상은 방금 만든 스냅샷이지 라이브 DB 가 아니다.
    라이브 소스 대신 스냅샷을 검사하는 이유 — (a) 소스가 깨졌으면 backup() 이 그대로 복사하므로
    스냅샷 손상 ⇒ 소스 손상이 성립하고, (b) 라이브 DB 에 긴 read 트랜잭션을 걸지 않는다.
    """
    conn = None
    try:
        conn = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
        rows = conn.execute('PRAGMA integrity_check').fetchall()
    except sqlite3.DatabaseError as e:
        return [f'열기/PRAGMA 실패: {e}']      # 헤더부터 깨진 경우 — 손상으로 취급
    finally:
        if conn is not None:
            conn.close()
    return [r[0] for r in rows if r and r[0] != 'ok']


def raise_sentinel(db_dir: Path, problems: list[str]):
    """DB 디렉터리에 손상 플래그를 남긴다 → /healthz degraded → smoke 실패(사람이 본다)."""
    body = [
        f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} backup_db.py: PRAGMA integrity_check 실패.',
        '이 파일이 있는 한 /healthz 는 degraded 이고 smoke 는 실패한다.',
        '백업 로테이션 prune 은 중단됐다 — backup/ 의 과거 스냅샷이 복구 후보다.',
        '조치 후(예: rollback.sh --db=restore) 다음 정시 검사가 통과하면 자동으로 지워진다.',
        '',
        *problems[:20],
    ]
    try:
        (db_dir / SENTINEL_NAME).write_text('\n'.join(body) + '\n')
    except OSError as e:
        log(f'경고: 센티넬 기록 실패 ({db_dir / SENTINEL_NAME}: {e}) — smoke 가 못 잡는다')


def clear_sentinel(db_dir: Path):
    """검사 통과 시 자기 해제. 손상이 고쳐졌는데 degraded 로 남아 있으면 안 된다."""
    sentinel = db_dir / SENTINEL_NAME
    if sentinel.exists():
        try:
            sentinel.unlink()
            log(f'integrity OK — 센티넬 해제({sentinel})')
        except OSError as e:
            log(f'경고: 센티넬 해제 실패 ({sentinel}: {e})')


def backup_one(name: str, src: Path) -> Path | None:
    if not src.exists():
        log(f'{name}: source not found ({src}) — skip')
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H')
    dest = BACKUP_DIR / f'{name}_{stamp}.sqlite3'
    tmp = dest.with_suffix('.sqlite3.tmp')
    try:
        # `with sqlite3.connect(...)` 를 쓰지 않는다 — 그건 **트랜잭션** 컨텍스트지 close 가 아니다
        # (파이썬 sqlite3 의 고전적 함정). 종전 코드는 이 관용구를 썼지만 cron 단명 프로세스라
        # 종료 시 GC 가 닫아주며 체크포인트했다 → 실해는 없었다(prod backup/ 실측: 고아 0개).
        # 그래도 명시적으로 닫는다: GC 타이밍에 기대는 정합성은 계약이 아니고, 아래 integrity_check 가
        # 정적인 파일을 봐야 하기 때문.
        source_conn = dest_conn = None
        try:
            source_conn = sqlite3.connect(str(src))
            dest_conn = sqlite3.connect(str(tmp))
            source_conn.backup(dest_conn)       # online backup API — writer 상주해도 일관 스냅샷
            # backup 은 소스의 저널 모드까지 복사 → 스냅샷이 WAL 로 뜬다. **아카이브는 WAL 일 이유가 없다**
            # (동시 writer 가 없다). DELETE 로 내려 -wal/-shm 이 아예 존재하지 않게 만든다 — 이게
            # sync-cdgts-db.sh 가 이미 전제하는 계약("스냅샷 = 일관된 단일 파일")이기도 하다.
            # 특히 아래 integrity_check 는 mode=ro 로 여는데, **읽기 전용 커넥션은 WAL DB 의 -shm 을
            # 만들어놓고 치울 권한이 없다** → DELETE 가 아니면 검사 자체가 매시 고아 파일 2개를 남긴다
            # (0.1.68 테스트서버 실측으로 발견. prune 의 glob `*.sqlite3` 에도 안 걸려 영구 누적).
            dest_conn.execute('PRAGMA journal_mode=DELETE')
        finally:
            for conn in (dest_conn, source_conn):
                if conn is not None:
                    conn.close()

        # 채택 전 게이트 — 깨진 스냅샷은 로테이션에 들어가지 않는다(docstring "로테이션 오염 방지").
        problems = integrity_check(tmp)
        if problems:
            log(f'{name}: !! INTEGRITY FAIL — 스냅샷 미채택. 라이브 DB({src}) 손상으로 간주.')
            for p in problems[:5]:
                log(f'{name}:    {p}')
            # 증거는 하나만 남긴다: 최초 손상이 가장 정보가 많고, 매시 쌓이면 디스크가 샌다.
            # 확장자가 .sqlite3 가 아니므로 prune_old() 의 glob 에도 안 걸린다.
            evidence = BACKUP_DIR / f'{name}_INTEGRITY_FAIL.corrupt'
            if evidence.exists():
                tmp.unlink()
                log(f'{name}: 증거 사본 이미 있음({evidence.name}) — 이번 것은 버림')
            else:
                tmp.replace(evidence)
                log(f'{name}: 증거 사본 보존 → {evidence.name}')
            raise_sentinel(src.parent, problems)
            return None

        tmp.replace(dest)
        clear_sentinel(src.parent)
        size_mb = dest.stat().st_size / (1024 * 1024)
        log(f'{name}: backup OK ({dest.name}, {size_mb:.1f} MB, integrity ok)')
        return dest
    except Exception as e:
        log(f'{name}: ERROR {e}')
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        return None


def prune_old(name: str, suffix: str = '.sqlite3'):
    """RETAIN_COUNT 개 최신만 남기고 나머지 삭제."""
    snapshots = []
    for f in BACKUP_DIR.glob(f'{name}_*{suffix}'):
        stem = f.name[:-len(suffix)] if f.name.endswith(suffix) else f.stem
        parts = stem.split('_')
        if len(parts) < 3:
            continue
        try:
            dt = datetime.strptime(f'{parts[-2]}_{parts[-1]}', '%Y%m%d_%H')
        except ValueError:
            continue
        snapshots.append((dt, f))
    snapshots.sort(key=lambda x: x[0], reverse=True)
    deleted = 0
    for _, f in snapshots[RETAIN_COUNT:]:
        try:
            f.unlink()
            deleted += 1
        except OSError:
            pass
    if deleted:
        log(f'{name}: pruned {deleted} old snapshot(s)')


def check_disk_space() -> bool:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    free_gb = shutil.disk_usage(BACKUP_DIR).free / (1024 ** 3)
    if free_gb < MIN_FREE_GB:
        msg = f'ABORT: free disk {free_gb:.2f} GB < {MIN_FREE_GB} GB threshold — skipping backup'
        log(msg)
        print(f'ERROR: {msg}', file=sys.stderr)
        return False
    return True


def main():
    if not check_disk_space():
        sys.exit(1)
    failed = False
    for name, src in SOURCES:
        dest = backup_one(name, src)
        if dest is None:
            # 스냅샷을 못 만들었거나(디스크/IO) 무결성에 걸렸다. 어느 쪽이든 **prune 하지 않는다** —
            # 새 스냅샷이 없는데 과거 것을 지우면 보관 창이 소리 없이 줄어든다.
            failed = True
            log(f'{name}: prune 건너뜀(스냅샷 미채택) — 과거 스냅샷 보존')
            continue
        prune_old(name)
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()

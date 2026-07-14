#!/usr/bin/env python3
"""cdGTS 운영(dolfinid) hourly DB 백업 — sqlite3 online backup API.

fcmanager/fsis2026 의 backup_db.py 와 동형(계약 — 운영 데이터의 안전망은 파이프라인이 아니라 백업).
종전 cdGTS 운영 백업은 pre_deploy 스냅샷(배포 시) + m710q daily pull(scripts/sync-cdgts-db.sh,
NAS 오프사이트 포함)뿐이라 최악 손실창 24h — hourly 트랙을 추가해 형제 프로젝트와 정렬(2026-07-14).

  - DB: sqlite3 online backup API (컨테이너가 쓰는 중에도 일관 스냅샷)
  - 최근 RETAIN_COUNT 개만 유지(오래된 것부터 삭제)
  - pre_deploy 스냅샷 retention 은 deploy.sh 가 단독 관리(20개) — 여기서 건드리지 않는다
    (fsis 에서 두 곳이 다른 수치로 같은 디렉터리를 prune 하던 충돌 교훈, 2026-07-14).
  - nginx conf 백업은 같은 호스트(dolfinid)의 fcmanager backup_db.py 가 이미 hourly 수행 — 중복 생략.
  - 배포 시 이미지에서 self-heal 추출(deploy/host/_extract_and_deploy.sh).
  - cron 등록(최초 1회, dolfinid honestjung crontab):
      0 * * * * /usr/bin/python3 /srv/cdGTS/scripts/backup_db.py >> /srv/cdGTS/backup/backup.log 2>&1
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
RETAIN_COUNT = 12      # 매시 1개 → 최근 12시간 유지(fsis/fcmanager 와 동일)
MIN_FREE_GB = 2        # 백업 디렉토리 여유가 이 미만이면 abort (디스크 풀 방지)


def log(msg: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)


def backup_one(name: str, src: Path) -> Path | None:
    if not src.exists():
        log(f'{name}: source not found ({src}) — skip')
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H')
    dest = BACKUP_DIR / f'{name}_{stamp}.sqlite3'
    tmp = dest.with_suffix('.sqlite3.tmp')
    try:
        with sqlite3.connect(str(src)) as source_conn, sqlite3.connect(str(tmp)) as dest_conn:
            source_conn.backup(dest_conn)
        tmp.replace(dest)
        size_mb = dest.stat().st_size / (1024 * 1024)
        log(f'{name}: backup OK ({dest.name}, {size_mb:.1f} MB)')
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
    for name, src in SOURCES:
        backup_one(name, src)
        prune_old(name)


if __name__ == '__main__':
    main()

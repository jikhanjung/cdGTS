"""scripts/backup_db.py — 무결성 게이트 (0.1.68, devlog 150).

핵심 계약은 탐지가 아니라 **로테이션 오염 방지**다: 소스가 깨지면 backup() 은 그걸 충실히 복사하고,
매시 로테이션이라 RETAIN_COUNT 시간이면 성한 스냅샷이 전부 prune 된다. 그래서 여기서 지키는 불변식은 둘:

  1. 깨진 스냅샷은 로테이션에 **채택되지 않는다**
  2. 채택 실패 시 prune 을 **건너뛴다**(과거 성한 스냅샷 보존)

Django 무관 — 순수 스크립트라 db 픽스처를 쓰지 않는다.
"""
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import backup_db  # noqa: E402


def _make_db(path: Path, rows: int = 200) -> Path:
    """실제로 열리는 sqlite DB. 손상을 만들려면 페이지가 여러 개여야 해서 행을 넉넉히 넣는다."""
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, blob TEXT)")
    conn.executemany("INSERT INTO t (blob) VALUES (?)", [("x" * 200,) for _ in range(rows)])
    conn.commit()
    conn.close()
    return path


def _corrupt(path: Path):
    """btree 페이지 하나를 쓰레기로 덮는다 — 헤더는 살려서 '열리지만 깨진' 상태를 만든다.

    (헤더까지 부수면 sqlite 가 즉시 NotADatabase 를 던져서, 우리가 실제로 겪은 상황
    — 열리고 질의도 되는데 integrity_check 만 걸리는 — 을 재현하지 못한다.)
    """
    with open(path, "r+b") as f:
        f.seek(4096 * 2 + 100)      # 1페이지=4096, 3번째 페이지 중간
        f.write(b"\xde\xad\xbe\xef" * 64)


@pytest.fixture
def env(tmp_path, monkeypatch):
    """BACKUP_DIR 을 tmp 로 돌린다 — 모듈 상수가 /srv 를 가리키므로 반드시 격리."""
    backup = tmp_path / "backup"
    backup.mkdir()
    monkeypatch.setattr(backup_db, "BACKUP_DIR", backup)
    dbdir = tmp_path / "db"
    dbdir.mkdir()
    return dbdir, backup


# --- integrity_check 자체 ---


def test_integrity_check_passes_on_healthy_db(tmp_path):
    assert backup_db.integrity_check(_make_db(tmp_path / "ok.sqlite3")) == []


def test_integrity_check_catches_corruption(tmp_path):
    db = _make_db(tmp_path / "bad.sqlite3")
    _corrupt(db)
    assert backup_db.integrity_check(db) != []


def test_integrity_check_treats_garbage_as_corrupt(tmp_path):
    """헤더부터 깨진 파일 = 예외가 아니라 '손상' 으로 보고돼야 한다(cron 이 죽으면 안 된다)."""
    junk = tmp_path / "junk.sqlite3"
    junk.write_bytes(b"not a database at all")
    problems = backup_db.integrity_check(junk)
    assert problems and "실패" in problems[0]


def test_integrity_check_does_not_write_to_target(tmp_path):
    """mode=ro 계약 — 검사가 대상 파일을 건드리면 안 된다(-wal/-shm 도 안 생겨야)."""
    db = _make_db(tmp_path / "ro.sqlite3")
    before = db.stat().st_mtime_ns
    backup_db.integrity_check(db)
    assert db.stat().st_mtime_ns == before
    assert not (tmp_path / "ro.sqlite3-wal").exists()


# --- 센티넬 ---


def test_sentinel_roundtrip(env):
    dbdir, _ = env
    backup_db.raise_sentinel(dbdir, ["page 3 is never used"])
    sentinel = dbdir / backup_db.SENTINEL_NAME
    assert sentinel.exists()
    assert "page 3 is never used" in sentinel.read_text()

    backup_db.clear_sentinel(dbdir)
    assert not sentinel.exists()


def test_clear_sentinel_is_idempotent(env):
    dbdir, _ = env
    backup_db.clear_sentinel(dbdir)          # 없을 때 호출해도 조용해야 한다(정상 경로)


def test_sentinel_name_matches_healthz():
    """config/health.py 와 파일명이 갈라지면 손상이 조용히 안 잡힌다 — 규약을 못 박는다."""
    from config.health import SENTINEL_NAME

    assert backup_db.SENTINEL_NAME == SENTINEL_NAME


# --- backup_one 의 채택 게이트 ---


def test_healthy_backup_is_promoted_and_clears_sentinel(env):
    dbdir, backup = env
    src = _make_db(dbdir / "db.sqlite3")
    (dbdir / backup_db.SENTINEL_NAME).write_text("직전 실행의 잔재\n")

    dest = backup_db.backup_one("cdgts", src)

    assert dest is not None and dest.exists()
    assert backup_db.integrity_check(dest) == []
    assert not (dbdir / backup_db.SENTINEL_NAME).exists()   # 자기해제
    assert not list(backup.glob("*.tmp"))


def test_backup_leaves_no_wal_siblings(env):
    """백업 디렉터리에 스냅샷 외 부산물이 없어야 한다 — 테스트서버 실측으로 잡힌 버그(0.1.68).

    backup() 은 소스의 저널 모드를 복사하므로 스냅샷이 WAL 로 뜨는데, integrity_check 가 mode=ro 로
    열면 **읽기 전용 커넥션이 -shm 을 만들어놓고 치울 권한이 없어** 매시 고아 2개가 남는다
    (`prune_old()` 의 glob `*.sqlite3` 이 못 잡아 영구 누적). 해법은 스냅샷을 DELETE 모드로 내리는 것 —
    아카이브에 동시 writer 는 없고, `sync-cdgts-db.sh` 도 이미 "단일 파일"을 전제한다.

    ⚠️ 소스가 **WAL 이어야** 재현된다(운영과 동일 조건). 이 픽스처 한 줄이 테스트의 핵심.
    """
    dbdir, backup = env
    src = _make_db(dbdir / "db.sqlite3")
    sqlite3.connect(str(src)).execute("PRAGMA journal_mode=WAL").close()   # 운영과 같은 모드

    dest = backup_db.backup_one("cdgts", src)

    strays = [p.name for p in backup.iterdir() if p != dest]
    assert strays == [], f"백업 디렉터리에 부산물: {strays}"


def test_corrupt_source_is_not_promoted(env):
    """가장 중요한 테스트 — 깨진 스냅샷이 로테이션에 들어가면 안 된다."""
    dbdir, backup = env
    src = _make_db(dbdir / "db.sqlite3")
    _corrupt(src)

    dest = backup_db.backup_one("cdgts", src)

    assert dest is None
    assert not list(backup.glob("cdgts_*.sqlite3"))          # 로테이션 오염 없음
    assert (dbdir / backup_db.SENTINEL_NAME).exists()        # smoke 가 볼 플래그
    assert (backup / "cdgts_INTEGRITY_FAIL.corrupt").exists()  # 증거는 남는다
    assert not list(backup.glob("*.tmp"))                    # tmp 누수 없음


def test_corrupt_evidence_is_kept_once(env):
    """매시 반복돼도 증거 사본은 1개 — 최초가 가장 정보가 많고, 쌓이면 디스크가 샌다."""
    dbdir, backup = env
    src = _make_db(dbdir / "db.sqlite3")
    _corrupt(src)

    backup_db.backup_one("cdgts", src)
    first = (backup / "cdgts_INTEGRITY_FAIL.corrupt").read_bytes()
    backup_db.backup_one("cdgts", src)      # 다음 정시

    assert len(list(backup.glob("*.corrupt"))) == 1
    assert (backup / "cdgts_INTEGRITY_FAIL.corrupt").read_bytes() == first  # 최초 보존


def test_corrupt_evidence_escapes_prune(env):
    """.corrupt 는 prune_old() 의 glob(.sqlite3)에 안 걸려야 한다 — 증거가 조용히 사라지면 안 된다."""
    dbdir, backup = env
    src = _make_db(dbdir / "db.sqlite3")
    _corrupt(src)
    backup_db.backup_one("cdgts", src)

    backup_db.prune_old("cdgts")

    assert (backup / "cdgts_INTEGRITY_FAIL.corrupt").exists()


# --- main() 의 prune 규칙 (로테이션 오염 방지의 본체) ---


def test_main_skips_prune_when_integrity_fails(env, monkeypatch):
    """손상 시 과거 스냅샷을 지우지 않는다. 이게 없으면 12시간 뒤 복구 대상이 0개가 된다."""
    dbdir, backup = env
    src = _make_db(dbdir / "db.sqlite3")
    monkeypatch.setattr(backup_db, "SOURCES", [("cdgts", src)])
    monkeypatch.setattr(backup_db, "RETAIN_COUNT", 2)

    # 성한 시절에 쌓아둔 과거 스냅샷 4개 — 정상이라면 2개로 prune 될 것들
    olds = []
    for hour in range(4):
        f = backup / f"cdgts_20260714_{hour:02d}.sqlite3"
        _make_db(f)
        olds.append(f)

    _corrupt(src)
    with pytest.raises(SystemExit) as exc:
        backup_db.main()

    assert exc.value.code == 1                       # cron 에 실패로 보고
    assert all(f.exists() for f in olds)             # ← 전부 살아 있어야 한다


def test_main_prunes_normally_when_healthy(env, monkeypatch):
    """대조군 — 건전하면 평소대로 RETAIN_COUNT 로 줄인다(게이트가 prune 을 죽이지 않았다)."""
    dbdir, backup = env
    src = _make_db(dbdir / "db.sqlite3")
    monkeypatch.setattr(backup_db, "SOURCES", [("cdgts", src)])
    monkeypatch.setattr(backup_db, "RETAIN_COUNT", 2)
    for hour in range(4):
        _make_db(backup / f"cdgts_20260714_{hour:02d}.sqlite3")

    with pytest.raises(SystemExit) as exc:
        backup_db.main()

    assert exc.value.code == 0
    assert len(list(backup.glob("cdgts_*.sqlite3"))) == 2

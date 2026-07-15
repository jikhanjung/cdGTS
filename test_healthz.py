"""/healthz 헬스체크 (P08.5) — smoke 동사가 소비하는 계약."""
from unittest import mock

import pytest
from django.core.management import call_command
from django.test import Client

from config.health import SENTINEL_NAME
from config.version import VERSION


@pytest.fixture
def db_dir(tmp_path, settings):
    """DB 가 있는 *척* 하는 디렉터리 — 센티넬 탐지는 경로 규약(DB 옆)만 쓴다.

    settings.DATABASES 를 직접 갈아끼우지 않고 patch.dict 로 덮는다: override_settings 는
    DATABASES 변경 시 커넥션을 닫아 db 픽스처를 깨뜨린다. 라이브 커넥션은 settings_dict 사본을
    쥐고 있으므로 이 패치에 영향받지 않는다(질의는 계속 동작).
    """
    with mock.patch.dict(
        settings.DATABASES["default"], {"NAME": str(tmp_path / "db.sqlite3")}
    ):
        yield tmp_path


def _seed():
    call_command("loaddata", "01_chrono", verbosity=0)
    call_command("loaddata", "02_nodes", verbosity=0)


def test_healthz_ok_when_seeded(db):
    call_command("loaddata", "01_chrono", verbosity=0)
    call_command("loaddata", "02_nodes", verbosity=0)
    resp = Client().get("/healthz")
    assert resp.status_code == 200
    d = resp.json()
    assert d["status"] == "ok"
    assert d["version"] == VERSION                    # 이미지에 구운 버전 = smoke 의 버전 일치 검사
    assert d["counts"]["node_types"] > 0 and d["counts"]["boundaries"] > 0


def test_healthz_unhealthy_when_empty(db):
    """빈 DB(시스템 시드 없음 = 빈 이미지 DB 폴백) → 503. 도메인 불변식 게이트."""
    resp = Client().get("/healthz")
    assert resp.status_code == 503
    assert resp.json()["status"] == "unhealthy"


def test_healthz_needs_no_auth(db):
    """인증 없이 도달 가능(헬스체크 불변식)."""
    call_command("loaddata", "01_chrono", verbosity=0)
    call_command("loaddata", "02_nodes", verbosity=0)
    assert Client().get("/healthz").status_code == 200


# --- 무결성 센티넬 (0.1.68) — scripts/backup_db.py 와의 파일명·경로 규약 ---


def test_healthz_degraded_when_sentinel_present(db, db_dir):
    """hourly backup_db.py 가 DB 옆에 센티넬을 남기면 degraded — 단, **200**.

    503 이 아닌 이유는 config/health.py 참조: btree 손상 ≠ 서빙 불능. smoke 는 status!="ok" 로
    거르므로 200 이어도 배포 게이트는 걸린다(test_smoke_contract_rejects_degraded 가 그 짝).
    """
    _seed()
    (db_dir / SENTINEL_NAME).write_text("2026-07-15 06:00:00 backup_db.py: ...실패.\n상세\n")

    resp = Client().get("/healthz")
    assert resp.status_code == 200                       # 트래픽에서 빼지 않는다
    d = resp.json()
    assert d["status"] == "degraded"
    assert d["integrity"].startswith("2026-07-15 06:00:00")   # 첫 줄 = 타임스탬프+사유
    assert d["counts"]["node_types"] > 0                 # 앱은 여전히 답한다


def test_healthz_ok_when_sentinel_absent(db, db_dir):
    """센티넬 없음 = 정상. (자기해제가 동작하면 이 상태로 돌아온다.)"""
    _seed()
    assert Client().get("/healthz").json()["status"] == "ok"


def test_healthz_unhealthy_beats_degraded(db, db_dir):
    """빈 DB + 센티넬 → unhealthy(503) 우선. 연결/시드가 없으면 손상 여부는 부차적."""
    (db_dir / SENTINEL_NAME).write_text("깨졌음\n")
    resp = Client().get("/healthz")
    assert resp.status_code == 503
    assert resp.json()["status"] == "unhealthy"


def test_healthz_survives_unstattable_db_name(db, settings):
    """DB NAME 이 경로가 아닐 때(테스트의 in-memory URI 등) 센티넬 탐지가 죽지 않아야 한다."""
    _seed()
    with mock.patch.dict(
        settings.DATABASES["default"], {"NAME": "file:memorydb_default?mode=memory&cache=shared"}
    ):
        assert Client().get("/healthz").json()["status"] == "ok"

"""/healthz 헬스체크 (P08.5) — smoke 동사가 소비하는 계약."""
import pytest
from django.core.management import call_command
from django.test import Client

from config.version import VERSION


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

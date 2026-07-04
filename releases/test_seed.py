"""
seed 관리 명령 회귀 테스트.

핵심: **데이터 있는 DB 에서 --mode=replace** — chrono.Unit.parent 같은 자기참조 PROTECT FK 의
일괄 삭제가 막히면 안 된다(devlog 033 의 ProtectedError 회귀). 로컬 검증이 빈 DB 에서만 돌아
운영에서야 터졌던 케이스를 고정한다.
"""
import pytest
from django.core.management import call_command

from chrono.models import Boundary, Unit
from graph.models import Graph
from nodes.models import NodeType
from releases.models import BoundaryRecord, Release


@pytest.fixture
def seeded(db):
    call_command("seed", mode="replace", verbosity=0)


def _counts():
    return (
        Unit.objects.count(), Boundary.objects.count(), NodeType.objects.count(),
        Graph.objects.count(), Release.objects.count(), BoundaryRecord.objects.count(),
    )


def test_replace_populates(seeded):
    units, boundaries, types, graphs, releases, records = _counts()
    assert (units, boundaries, types, graphs) == (12, 3, 12, 4)
    assert (releases, records) == (2, 5)                     # records = bake 산출
    # 자기참조 계보가 실제로 존재 → 아래 재-replace 가 self-FK 삭제 경로를 밟는다.
    assert Unit.objects.filter(parent__isnull=False).exists()


def test_replace_on_populated_db_no_protectederror(seeded):
    """회귀: 데이터 있는 DB 의 replace 재실행. 예전엔 Unit.parent(PROTECT) 때문에 ProtectedError."""
    before = _counts()
    assert Unit.objects.filter(parent__isnull=False).exists()   # 삭제될 self-FK 데이터 존재 확인
    call_command("seed", mode="replace", verbosity=0)           # raise 하면 테스트 실패
    assert _counts() == before                                  # 멱등: 카운트 동일


def test_add_is_idempotent(seeded):
    before = _counts()
    call_command("seed", mode="add", verbosity=0)               # 없는 것만 → 추가 0
    assert _counts() == before


def test_seed_content_canonical(seeded):
    """정본값 가드 — seed 파일 드리프트 회귀 방지(운영에서 겪은 age-depth/radiometric 어긋남)."""
    adm = NodeType.objects.get(slug="age-depth-model")
    assert adm.params_schema["method"]["choices"] == ["linear", "spline"]
    assert NodeType.objects.get(slug="radiometric-uPb").params_schema      # 비어있지 않음

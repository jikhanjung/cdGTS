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
    # ICS chart.ttl 확장: period+ units(42) + 전체 boundary(175) + published-age 타입(13)
    assert (units, boundaries, types, graphs) == (42, 175, 13, 4)
    assert (releases, records) == (2, 5)                     # records = 릴리스 bake 산출
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


def test_bake_graph_produces_icc_table(seeded):
    """조립 그래프 bake → 게이트웨이 출력이 ICC 테이블(BoundaryRecord)로 얼려진다.
    period 이상(Eon/Era/Period) 36경계 = 예제 파이프라인 3 + ICS 공표값 데이터 노드 33."""
    from graph.models import Graph
    from releases.services import bake_graph
    g = Graph.objects.get(slug="example-icc-partial")
    rel, n = bake_graph(g)
    assert n == 36
    assert rel.version == "graph:example-icc-partial"
    recs = {r.boundary.slug: r for r in rel.records.select_related("boundary")}
    # 예제 파이프라인 값 유지
    assert {"base-proterozoic", "base-cambrian", "base-triassic"} <= set(recs)
    assert recs["base-proterozoic"].value_ma == 2500 and recs["base-proterozoic"].definition_type == "GSSA"
    assert recs["base-triassic"].definition_type == "GSSP"
    # chart.ttl 공표값 데이터 노드 (period)
    assert recs["base-jurassic"].value_ma == 201.4
    assert recs["base-hadean"].value_ma == 4567.0 and recs["base-hadean"].definition_type == "GSSA"
    # 재-bake 는 같은 릴리스에 멱등
    rel2, n2 = bake_graph(g)
    assert n2 == 36 and rel2.pk == rel.pk

    # HTTP 엔드포인트도 확인
    from rest_framework.test import APIClient
    resp = APIClient().post(f"/api/graphs/{g.pk}/bake/")
    assert resp.status_code == 200 and resp.data["baked"] == 36
    assert resp.data["release"]["version"] == "graph:example-icc-partial"
    assert len(resp.data["release"]["records"]) == 36


def test_finer_boundaries_registry_only(seeded):
    """Epoch/Age 경계는 registry(Boundary)에만 — 네트웍(게이트웨이)엔 없다. period+ 는 네트웍에."""
    from graph.models import Gateway
    assert Boundary.objects.filter(slug="base-fortunian").exists()        # Age → registry
    assert not Gateway.objects.filter(boundary__slug="base-fortunian").exists()
    assert Gateway.objects.filter(boundary__slug="base-jurassic").exists()  # Period → 네트웍


def test_seed_content_canonical(seeded):
    """정본값 가드 — seed 파일 드리프트 회귀 방지(운영에서 겪은 age-depth/radiometric 어긋남)."""
    adm = NodeType.objects.get(slug="age-depth-model")
    assert adm.params_schema["method"]["choices"] == ["linear", "spline"]
    assert NodeType.objects.get(slug="radiometric-uPb").params_schema      # 비어있지 않음

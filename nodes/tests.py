import json

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from nodes.distribution import FIDELITY_LADDER, Distribution, DistributionError
from nodes.models import NodeType, Port


@pytest.fixture
def seeded(db):
    call_command("loaddata", "02_nodes", verbosity=0)


# --- Distribution 값 객체 (충실도 L0–L5) ---

def test_fidelity_levels_ordered():
    assert [Distribution(fidelity=f, value_ma=1 if f == "exact" else None).level
            for f in FIDELITY_LADDER] == [0, 1, 2, 3, 4, 5]


def test_exact_is_point_mass():
    d = Distribution.exact(2500)
    assert d.level == 0 and d.value_ma == 2500 and d.budget == {}


def test_exact_rejects_budget():
    with pytest.raises(DistributionError):
        Distribution(fidelity="exact", value_ma=2500, budget={"analytical": 0.1})


def test_unknown_fidelity_rejected():
    with pytest.raises(DistributionError):
        Distribution(fidelity="bogus")


@pytest.mark.parametrize("dist", [
    Distribution.exact(2500),
    Distribution.symmetric(251.902, 0.024, sigma=2),
    Distribution(fidelity="decomposed", value_ma=251.902, sigma=2,
                 budget={"analytical": 0.024}, shared_components=["earthtime-tracer", "u-decay-const"]),
    Distribution(fidelity="shape", value_ma=538.8, shape={"median": 538.8, "hpd95": [538.2, 539.4]}),
    Distribution(fidelity="full", value_ma=252.0, posterior_ref="samples://run/42", note="posterior"),
])
def test_roundtrip_through_json(dist):
    """직렬화 왕복: Distribution → dict → JSON → dict → Distribution 동일."""
    restored = Distribution.from_dict(json.loads(json.dumps(dist.to_dict())))
    assert restored == dist


def test_to_dict_omits_empties():
    assert Distribution.exact(2500).to_dict() == {"fidelity": "exact", "value_ma": 2500}


# --- NodeType 카탈로그 (데이터로 존재, 하드코딩 아님) ---

def test_catalog_loads(seeded):
    assert NodeType.objects.count() == 16          # + boundary + unit + merge (terminal chart)
    assert set(NodeType.objects.values_list("category", flat=True)) == {"data", "process", "clamp"}
    assert NodeType.objects.get(slug="published-age").category == "data"


def test_ports_wired(seeded):
    adm = NodeType.objects.get(slug="age-depth-model")
    assert [p.name for p in adm.input_ports] == ["dated_horizons"]
    # horizon_age(값) + order 참여용 세로 포트 older/younger (published-age 미러, 순수 배선)
    assert [p.name for p in adm.output_ports] == ["horizon_age", "older", "younger"]
    assert adm.input_ports.first().multiple is True


def test_pin_clamp_has_value_param(seeded):
    pin = NodeType.objects.get(slug="pin")
    assert pin.category == NodeType.Category.CLAMP
    assert "value" in pin.params_schema


def test_edges_carry_distributions(seeded):
    # 데이터/모델 출력은 분포, 상관 신호는 signal.
    assert Port.objects.get(node_type__slug="radiometric-uPb", direction="out").datatype == "distribution"
    assert Port.objects.get(node_type__slug="biostratigraphic", direction="out").datatype == "signal"


def test_node_types_api(seeded):
    resp = APIClient().get("/api/node-types/")
    assert resp.status_code == 200
    adm = next(t for t in resp.data if t["slug"] == "age-depth-model")
    assert adm["category"] == "process"
    assert {p["name"] for p in adm["ports"]} == {"dated_horizons", "horizon_age", "older", "younger"}

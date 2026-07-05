import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from graph.dag import find_unbroken_cycles
from graph.models import Graph


@pytest.fixture
def node_types(db):
    call_command("loaddata", "02_nodes", verbosity=0)


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def graph(node_types):
    return Graph.objects.create(slug="sandbox-1", name="Sandbox 1")


# --- DAG 불변식 (순수 함수) ---

def test_acyclic_ok():
    assert find_unbroken_cycles(["a", "b", "c"], set(), [("a", "b"), ("b", "c")]) == set()


def test_unbroken_cycle_detected():
    stuck = find_unbroken_cycles(["a", "b"], set(), [("a", "b"), ("b", "a")])
    assert stuck == {"a", "b"}


def test_cycle_broken_by_breaker():
    # a → j → a, j 가 cycle-breaker(joint-inference/clamp) → 허용
    assert find_unbroken_cycles(["a", "j"], {"j"}, [("a", "j"), ("j", "a")]) == set()


# --- API 왕복 {nodes, edges, viewport} ---

def _payload():
    return {
        "nodes": [
            {"key": "obs1", "node_type": "radiometric-uPb", "x": 0, "y": 0, "params": {}},
            {"key": "adm", "node_type": "age-depth-model", "x": 200, "y": 0, "params": {"method": "bayesian"}},
        ],
        "edges": [
            {"source": "obs1", "source_port": "age",
             "target": "adm", "target_port": "dated_horizons", "kind": "data"},
        ],
        "viewport": {"x": 10, "y": 20, "zoom": 1.5},
    }


def test_group_roundtrip(api, graph):
    """노드그룹(멤버십 + 접기 + 위치)이 PUT/GET 왕복. 엔진 무관·표현용."""
    payload = _payload()
    payload["groups"] = [{"key": "g1", "name": "Meishan", "collapsed": True, "x": 100, "y": 50}]
    payload["nodes"][0]["group"] = "g1"          # obs1 → 그룹, adm 은 그룹 밖
    put = api.put(f"/api/graphs/{graph.pk}/", payload, format="json")
    assert put.status_code == 200, put.data
    got = api.get(f"/api/graphs/{graph.pk}/").data
    assert got["groups"] == [{"key": "g1", "name": "Meishan", "collapsed": True, "x": 100, "y": 50, "parent": None}]
    by_key = {n["key"]: n for n in got["nodes"]}
    assert by_key["obs1"]["group"] == "g1"
    assert by_key["adm"]["group"] is None


def test_nested_group_roundtrip(api, graph):
    """중첩 노드그룹 — 하위그룹 parent 가 PUT/GET 왕복. 엔진 무관·드릴인 계층."""
    payload = _payload()
    payload["groups"] = [
        {"key": "outer", "name": "Carboniferous", "collapsed": True, "x": 0, "y": 0, "parent": None},
        {"key": "inner", "name": "Mississippian", "collapsed": True, "x": 10, "y": 10, "parent": "outer"},
    ]
    payload["nodes"][0]["group"] = "inner"       # 노드는 하위그룹 소속
    put = api.put(f"/api/graphs/{graph.pk}/", payload, format="json")
    assert put.status_code == 200, put.data
    got = {g["key"]: g for g in api.get(f"/api/graphs/{graph.pk}/").data["groups"]}
    assert got["inner"]["parent"] == "outer" and got["outer"]["parent"] is None


def test_group_cycle_rejected(api, graph):
    payload = _payload()
    payload["groups"] = [
        {"key": "a", "name": "A", "collapsed": True, "x": 0, "y": 0, "parent": "b"},
        {"key": "b", "name": "B", "collapsed": True, "x": 0, "y": 0, "parent": "a"},
    ]
    assert api.put(f"/api/graphs/{graph.pk}/", payload, format="json").status_code == 400


def test_group_bad_ref_rejected(api, graph):
    payload = _payload()
    payload["nodes"][0]["group"] = "ghost"       # groups 에 없는 그룹
    put = api.put(f"/api/graphs/{graph.pk}/", payload, format="json")
    assert put.status_code == 400


def test_put_then_get_roundtrip(api, graph):
    put = api.put(f"/api/graphs/{graph.pk}/", _payload(), format="json")
    assert put.status_code == 200, put.data
    got = api.get(f"/api/graphs/{graph.pk}/").data
    assert {n["key"] for n in got["nodes"]} == {"obs1", "adm"}
    edge = got["edges"][0]
    # 엣지 끝점은 노드 key 여야 React Flow 노드 id 와 매칭됨.
    assert edge["source"] == "obs1" and edge["target"] == "adm"
    assert edge["target_port"] == "dated_horizons"
    assert got["viewport"] == {"x": 10, "y": 20, "zoom": 1.5}


def test_put_replaces_wholesale(api, graph):
    api.put(f"/api/graphs/{graph.pk}/", _payload(), format="json")
    smaller = {"nodes": [{"key": "solo", "node_type": "astronomical", "x": 0, "y": 0}],
               "edges": [], "viewport": {}}
    api.put(f"/api/graphs/{graph.pk}/", smaller, format="json")
    got = api.get(f"/api/graphs/{graph.pk}/").data
    assert [n["key"] for n in got["nodes"]] == ["solo"]
    assert got["edges"] == []


def test_cycle_rejected(api, graph):
    payload = {
        "nodes": [
            {"key": "a", "node_type": "calibration-transfer", "x": 0, "y": 0},
            {"key": "b", "node_type": "calibration-transfer", "x": 100, "y": 0},
        ],
        "edges": [
            {"source": "a", "source_port": "calibrated", "target": "b", "target_port": "reference"},
            {"source": "b", "source_port": "calibrated", "target": "a", "target_port": "reference"},
        ],
        "viewport": {},
    }
    resp = api.put(f"/api/graphs/{graph.pk}/", payload, format="json")
    assert resp.status_code == 400
    assert "순환" in str(resp.data)


def test_cycle_through_joint_inference_allowed(api, graph):
    payload = {
        "nodes": [
            {"key": "a", "node_type": "calibration-transfer", "x": 0, "y": 0},
            {"key": "j", "node_type": "joint-inference", "x": 100, "y": 0},
        ],
        "edges": [
            {"source": "a", "source_port": "calibrated", "target": "j", "target_port": "constraints"},
            {"source": "j", "source_port": "estimates", "target": "a", "target_port": "reference"},
        ],
        "viewport": {},
    }
    assert api.put(f"/api/graphs/{graph.pk}/", payload, format="json").status_code == 200


def test_bad_port_rejected(api, graph):
    payload = {
        "nodes": [
            {"key": "obs1", "node_type": "radiometric-uPb", "x": 0, "y": 0},
            {"key": "adm", "node_type": "age-depth-model", "x": 100, "y": 0},
        ],
        "edges": [
            {"source": "obs1", "source_port": "age", "target": "adm", "target_port": "NOPE"},
        ],
        "viewport": {},
    }
    resp = api.put(f"/api/graphs/{graph.pk}/", payload, format="json")
    assert resp.status_code == 400
    assert "입력 포트" in str(resp.data)

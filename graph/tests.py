import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from graph.dag import find_unbroken_cycles
from graph.models import Graph


@pytest.fixture
def node_types(db):
    call_command("loaddata", "initial_node_types", verbosity=0)


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


def test_evaluate_stub(api, graph):
    api.put(f"/api/graphs/{graph.pk}/", _payload(), format="json")
    resp = api.post(f"/api/graphs/{graph.pk}/evaluate/")
    assert resp.status_code == 200
    assert resp.data["status"] == "not-implemented"
    assert resp.data["node_count"] == 2

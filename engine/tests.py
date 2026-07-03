import pytest
from django.core.management import call_command

from engine.evaluate import content_hash, evaluate_graph, topo_order
from graph.models import Edge, Graph, NodeInstance
from nodes.models import NodeType


@pytest.fixture
def node_types(db):
    call_command("loaddata", "initial_node_types", verbosity=0)


def _build_chain(distribution):
    """uPb(data, dist) → age-depth-model(process) 체인 그래프."""
    g = Graph.objects.create(slug="g", name="G")
    uPb = NodeInstance.objects.create(
        graph=g, key="uPb", node_type=NodeType.objects.get(slug="radiometric-uPb"),
        params={"distribution": distribution},
    )
    adm = NodeInstance.objects.create(
        graph=g, key="adm", node_type=NodeType.objects.get(slug="age-depth-model"), params={},
    )
    Edge.objects.create(graph=g, source=uPb, source_port="age", target=adm, target_port="dated_horizons")
    return g


# --- 순수 함수 ---

def test_topo_order():
    order = topo_order(["a", "b", "c"], [("a", "b"), ("b", "c")])
    assert order.index("a") < order.index("b") < order.index("c")


def test_hash_changes_with_params():
    assert content_hash("t", {"v": 1}, []) != content_hash("t", {"v": 2}, [])
    assert content_hash("t", {"v": 1}, []) == content_hash("t", {"v": 1}, [])


# --- pass-through 전파 ---

def test_distribution_propagates_downstream(node_types):
    dist = {"fidelity": "decomposed", "value_ma": 251.902, "budget": {"analytical": 0.024}}
    g = _build_chain(dist)
    run = evaluate_graph(g)
    by_key = {r.node_key: r for r in run.results.all()}
    # leaf 값이 하류 process 까지 그대로 전파.
    assert by_key["uPb"].distribution["value_ma"] == 251.902
    assert by_key["adm"].distribution["value_ma"] == 251.902
    # provenance 역추적: adm 은 uPb 에서 왔다.
    assert by_key["adm"].provenance == ["uPb"]


def test_pin_emits_exact(node_types):
    g = Graph.objects.create(slug="p", name="P")
    NodeInstance.objects.create(
        graph=g, key="pin1", node_type=NodeType.objects.get(slug="pin"), params={"value": 2500},
    )
    run = evaluate_graph(g)
    r = run.results.get(node_key="pin1")
    assert r.distribution == {"fidelity": "exact", "value_ma": 2500}   # GSSA 점질량


# --- 증분 캐시 ---

def test_incremental_cache_hit_when_unchanged(node_types):
    g = _build_chain({"fidelity": "sym", "value_ma": 250.0, "sigma": 2, "budget": {"analytical": 0.1}})
    evaluate_graph(g)                      # run 1
    run2 = evaluate_graph(g)               # run 2, 입력 불변
    assert all(r.cached for r in run2.results.all())
    assert run2.stats["cached"] == 2 and run2.stats["computed"] == 0


def test_leaf_change_dirties_downstream(node_types):
    g = _build_chain({"fidelity": "sym", "value_ma": 250.0, "sigma": 2, "budget": {"analytical": 0.1}})
    evaluate_graph(g)                      # run 1
    leaf = g.nodes.get(key="uPb")
    leaf.params = {"distribution": {"fidelity": "sym", "value_ma": 249.0, "sigma": 2, "budget": {"analytical": 0.1}}}
    leaf.save()
    run2 = evaluate_graph(g)               # leaf 바뀜 → leaf + 하류 재계산
    assert run2.stats["computed"] == 2 and run2.stats["cached"] == 0
    assert g.eval_runs.first().results.get(node_key="adm").distribution["value_ma"] == 249.0


# --- API + 인증서 ---

def test_evaluate_endpoint(node_types):
    from rest_framework.test import APIClient
    g = _build_chain({"fidelity": "exact", "value_ma": 538.8})
    resp = APIClient().post(f"/api/graphs/{g.pk}/evaluate/")
    assert resp.status_code == 200
    assert resp.data["stats"]["computed"] == 2
    assert resp.data["certificate"]["passed"] is True
    keys = {r["node_key"] for r in resp.data["results"]}
    assert keys == {"uPb", "adm"}

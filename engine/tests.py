import pytest
from django.core.management import call_command

from engine.evaluate import content_hash, evaluate_graph, topo_order
from graph.models import Edge, Graph, NodeInstance
from nodes.models import NodeType


@pytest.fixture
def node_types(db):
    call_command("loaddata", "02_nodes", verbosity=0)


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


def test_age_depth_interpolates_through_graph(node_types):
    """두 dated horizon(depth+age) → age-depth-model(target_depth) → 보간 연대."""
    g = Graph.objects.create(slug="ad", name="AD")
    uPb = NodeType.objects.get(slug="radiometric-uPb")
    h1 = NodeInstance.objects.create(graph=g, key="h1", node_type=uPb, params={
        "depth": 0, "distribution": {"fidelity": "decomposed", "value_ma": 250.0, "sigma": 1, "budget": {"model": 1.0}}})
    h2 = NodeInstance.objects.create(graph=g, key="h2", node_type=uPb, params={
        "depth": 10, "distribution": {"fidelity": "decomposed", "value_ma": 260.0, "sigma": 1, "budget": {"model": 1.0}}})
    adm = NodeInstance.objects.create(
        graph=g, key="adm", node_type=NodeType.objects.get(slug="age-depth-model"),
        params={"method": "linear", "target_depth": 5})
    Edge.objects.create(graph=g, source=h1, source_port="age", target=adm, target_port="dated_horizons")
    Edge.objects.create(graph=g, source=h2, source_port="age", target=adm, target_port="dated_horizons")
    run = evaluate_graph(g)
    r = run.results.get(node_key="adm")
    assert r.distribution["value_ma"] == 255.0          # 중점 보간
    assert set(r.provenance) == {"h1", "h2"}            # 두 horizon 이 기여


def test_pin_emits_exact(node_types):
    g = Graph.objects.create(slug="p", name="P")
    NodeInstance.objects.create(
        graph=g, key="pin1", node_type=NodeType.objects.get(slug="pin"), params={"value": 2500},
    )
    run = evaluate_graph(g)
    r = run.results.get(node_key="pin1")
    assert r.distribution == {"fidelity": "exact", "value_ma": 2500}   # GSSA 점질량


def _order_graph(older_val, younger_val, min_gap=0, mode="hard"):
    g = Graph.objects.create(slug=f"ord-{older_val}-{younger_val}-{min_gap}-{mode}", name="Order")
    pin = NodeType.objects.get(slug="pin")
    older = NodeInstance.objects.create(graph=g, key="older", node_type=pin, params={"value": older_val})
    younger = NodeInstance.objects.create(graph=g, key="younger", node_type=pin, params={"value": younger_val})
    oc = NodeInstance.objects.create(graph=g, key="oc", node_type=NodeType.objects.get(slug="order"),
                                     params={"min_gap": min_gap, "mode": mode})
    Edge.objects.create(graph=g, source=older, source_port="out", target=oc, target_port="older")
    Edge.objects.create(graph=g, source=younger, source_port="out", target=oc, target_port="younger")
    return g


def test_order_constraint_certifies_pass(node_types):
    run = evaluate_graph(_order_graph(500, 400))
    assert run.results.get(node_key="oc").distribution["ok"] is True
    assert run.certificate.checks["L1"] == "pass" and run.certificate.passed is True


def test_order_constraint_hard_violation_fails(node_types):
    run = evaluate_graph(_order_graph(300, 400, mode="hard"))   # older < younger
    assert run.results.get(node_key="oc").distribution["ok"] is False
    assert run.certificate.checks["L1"] == "fail" and run.certificate.passed is False


def test_order_constraint_warn_mode_warns(node_types):
    run = evaluate_graph(_order_graph(300, 400, mode="warn"))
    assert run.certificate.checks["L1"] == "warn" and run.certificate.passed is True


def test_order_constraint_min_gap(node_types):
    run = evaluate_graph(_order_graph(460, 400, min_gap=100))   # gap 60 < Δ 100
    assert run.results.get(node_key="oc").distribution["ok"] is False


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


# --- 비동기 평가 잡 + 워커 (P06.4a) ---

def _joint_graph():
    """두 pin → joint-inference(constraints). joint 노드가 있으므로 needs_async=True."""
    g = Graph.objects.create(slug="joint", name="Joint")
    pin = NodeType.objects.get(slug="pin")
    a = NodeInstance.objects.create(graph=g, key="a", node_type=pin, params={"value": 500})
    b = NodeInstance.objects.create(graph=g, key="b", node_type=pin, params={"value": 400})
    ji = NodeInstance.objects.create(graph=g, key="ji",
                                     node_type=NodeType.objects.get(slug="joint-inference"), params={})
    Edge.objects.create(graph=g, source=a, source_port="out", target=ji, target_port="constraints")
    Edge.objects.create(graph=g, source=b, source_port="out", target=ji, target_port="constraints")
    return g


def test_needs_async_false_for_analytic(node_types):
    from engine.evaluate import needs_async
    assert needs_async(_build_chain({"fidelity": "exact", "value_ma": 538.8})) is False


def test_needs_async_true_for_joint(node_types):
    from engine.evaluate import needs_async
    assert needs_async(_joint_graph()) is True


def test_evaluate_endpoint_queues_job_for_joint(node_types):
    from rest_framework.test import APIClient
    from engine.models import EvalJob
    g = _joint_graph()
    resp = APIClient().post(f"/api/graphs/{g.pk}/evaluate/")
    assert resp.status_code == 202                       # 동기(200) 아님 — 큐잉됨
    assert resp.data["status"] == "queued"
    assert resp.data["run"] is None
    assert EvalJob.objects.filter(graph=g, status="queued").count() == 1


def test_worker_processes_queued_job(node_types):
    from django.core.management import call_command
    from engine.models import EvalJob
    g = _joint_graph()
    job = EvalJob.objects.create(graph=g)
    call_command("run_worker", once=True)                # 큐를 한 번 비우고 종료
    job.refresh_from_db()
    assert job.status == "done"
    assert job.run is not None
    # 워커가 만든 run 이 그래프의 최신 EvalRun 이고 joint 결과를 담는다.
    assert job.run.results.get(node_key="ji").distribution is not None
    assert job.started_at is not None and job.finished_at is not None


def test_claim_next_job_is_atomic(node_types):
    from engine.jobs import claim_next_job
    from engine.models import EvalJob
    g = _joint_graph()
    EvalJob.objects.create(graph=g)
    first = claim_next_job()
    assert first is not None and first.status == "running"
    assert claim_next_job() is None                      # 이미 클레임됨 — 두 번째는 없음


def test_eval_job_endpoint_embeds_run_when_done(node_types):
    from rest_framework.test import APIClient
    from engine.jobs import claim_next_job, process_job
    from engine.models import EvalJob
    g = _joint_graph()
    EvalJob.objects.create(graph=g)
    process_job(claim_next_job())
    job = EvalJob.objects.filter(graph=g).first()
    resp = APIClient().get(f"/api/eval-jobs/{job.pk}/")
    assert resp.status_code == 200
    assert resp.data["status"] == "done"
    assert resp.data["run"]["certificate"] is not None
    assert {r["node_key"] for r in resp.data["run"]["results"]} == {"a", "b", "ji"}


def test_process_job_records_failure(node_types, monkeypatch):
    from engine import jobs
    from engine.jobs import claim_next_job, process_job
    from engine.models import EvalJob
    g = _joint_graph()
    EvalJob.objects.create(graph=g)
    monkeypatch.setattr(jobs, "evaluate_graph", lambda graph: (_ for _ in ()).throw(RuntimeError("boom")))
    job = process_job(claim_next_job())
    assert job.status == "failed"
    assert "boom" in job.error and job.run is None

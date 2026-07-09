import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from graph.dag import find_unbroken_cycles
from graph.models import Graph


@pytest.fixture
def node_types(db):
    call_command("loaddata", "02_nodes", verbosity=0)


@pytest.fixture
def user(db):
    from django.contrib.auth import get_user_model
    return get_user_model().objects.create_user("editor", password="pw12345")


@pytest.fixture
def api(user):
    c = APIClient()
    c.force_authenticate(user=user)          # P05.2: graph writes require the authenticated owner
    return c


@pytest.fixture
def graph(node_types, user):
    return Graph.objects.create(slug="sandbox-1", name="Sandbox 1", owner=user)


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
    assert got["groups"] == [{
        "key": "g1", "name": "Meishan", "collapsed": True, "x": 100, "y": 50,
        "parent": None, "kind": "container", "unit": None, "lower": None, "upper": None,
    }]
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
    assert "cycle" in str(resp.data)


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
    assert "input port" in str(resp.data)


# --- 경계·구간 이중성 (boundary-span-duality) ---

@pytest.fixture
def chrono(db):
    call_command("loaddata", "01_chrono", verbosity=0)


def _boundary_node(key, value_ma):
    """경계 점 = boundary nature 의 published-age leaf (값을 담음)."""
    return {"key": key, "node_type": "published-age", "nature": "boundary",
            "x": 0, "y": 0, "params": {"distribution": {"value_ma": value_ma}}}


def test_span_group_and_boundary_roundtrip(api, graph, chrono):
    """span 그룹(kind=unit·unit·lower/upper) + boundary nature 노드가 PUT/GET 왕복."""
    payload = {
        "nodes": [_boundary_node("base-cambrian", 538.8), _boundary_node("base-ordovician", 486.85)],
        "edges": [],
        "groups": [{
            "key": "cambrian", "name": "Cambrian", "collapsed": True, "x": 0, "y": 0,
            "kind": "unit", "unit": "cambrian", "lower": "base-cambrian", "upper": "base-ordovician",
        }],
        "viewport": {},
    }
    put = api.put(f"/api/graphs/{graph.pk}/", payload, format="json")
    assert put.status_code == 200, put.data
    got = api.get(f"/api/graphs/{graph.pk}/").data
    g = got["groups"][0]
    assert g["kind"] == "unit" and g["unit"] == "cambrian"
    assert g["lower"] == "base-cambrian" and g["upper"] == "base-ordovician"
    by_key = {n["key"]: n for n in got["nodes"]}
    assert by_key["base-cambrian"]["nature"] == "boundary"
    # 경계는 담기지 않고 참조된다 — 그룹 멤버가 아님.
    assert by_key["base-cambrian"]["group"] is None


def test_shared_boundary_referenced_by_two_groups(api, graph, chrono):
    """한 경계 노드가 인접 두 구간의 lower/upper 로 공유(에디아카라기 upper ≡ 캄브리아기 lower)."""
    payload = {
        "nodes": [
            _boundary_node("base-ediacaran", 635.0),
            _boundary_node("base-cambrian", 538.8),
            _boundary_node("base-ordovician", 486.85),
        ],
        "edges": [],
        "groups": [
            {"key": "ediacaran", "name": "Ediacaran", "collapsed": True, "x": 0, "y": 0,
             "kind": "unit", "unit": "ediacaran", "lower": "base-ediacaran", "upper": "base-cambrian"},
            {"key": "cambrian", "name": "Cambrian", "collapsed": True, "x": 0, "y": 100,
             "kind": "unit", "unit": "cambrian", "lower": "base-cambrian", "upper": "base-ordovician"},
        ],
        "viewport": {},
    }
    put = api.put(f"/api/graphs/{graph.pk}/", payload, format="json")
    assert put.status_code == 200, put.data
    got = {g["key"]: g for g in api.get(f"/api/graphs/{graph.pk}/").data["groups"]}
    # 같은 경계 노드가 한쪽엔 upper, 다른쪽엔 lower.
    assert got["ediacaran"]["upper"] == "base-cambrian"
    assert got["cambrian"]["lower"] == "base-cambrian"


def test_group_bad_boundary_ref_rejected(api, graph, chrono):
    payload = {
        "nodes": [_boundary_node("base-cambrian", 538.8)],
        "edges": [],
        "groups": [{"key": "cambrian", "name": "Cambrian", "collapsed": True, "x": 0, "y": 0,
                    "kind": "unit", "lower": "base-cambrian", "upper": "ghost-boundary"}],
        "viewport": {},
    }
    assert api.put(f"/api/graphs/{graph.pk}/", payload, format="json").status_code == 400


def _order_graph(v_older, v_younger):
    """오래된 경계 → order edge → 젊은 경계. source=older(큰 Ma), target=younger(작은 Ma)."""
    return {
        "nodes": [_boundary_node("older", v_older), _boundary_node("younger", v_younger)],
        "edges": [{"source": "older", "source_port": "younger", "target": "younger",
                   "target_port": "older", "kind": "order"}],
        "viewport": {},
    }


def test_order_edge_roundtrip_and_cycle_exempt(api, graph):
    """order edge 는 세로 포트 연결(제약) — 포트 방향 검증·데이터 사이클 판정에서 제외, 왕복."""
    put = api.put(f"/api/graphs/{graph.pk}/", _order_graph(500.0, 480.0), format="json")
    assert put.status_code == 200, put.data
    edges = api.get(f"/api/graphs/{graph.pk}/").data["edges"]
    assert edges[0]["kind"] == "order"


def test_certify_l1_reads_order_edges(api, graph):
    """정합성 게이트 L1 이 order edge 체인에서 판정: 순서 정상=pass, 역전=fail."""
    from engine.evaluate import evaluate_graph
    from engine.models import CoherenceCertificate

    api.put(f"/api/graphs/{graph.pk}/", _order_graph(500.0, 480.0), format="json")
    g = Graph.objects.get(pk=graph.pk)
    evaluate_graph(g)
    cert = CoherenceCertificate.objects.filter(eval_run__graph=g).latest("id")
    assert cert.checks["L1"] == "pass"

    # 역전: 오래된 쪽 값이 젊은 쪽보다 작음 → L1 fail.
    api.put(f"/api/graphs/{graph.pk}/", _order_graph(480.0, 500.0), format="json")
    g = Graph.objects.get(pk=graph.pk)
    evaluate_graph(g)
    cert = CoherenceCertificate.objects.filter(eval_run__graph=g).latest("id")
    assert cert.checks["L1"] == "fail" and cert.passed is False


# --- reference nodes + cite edges (provenance) ---

def _cite_graph():
    """reference 노드 → cite edge → data 노드. cite 는 데이터 흐름이 아닌 provenance 주석."""
    return {
        "nodes": [
            {"key": "obs1", "node_type": "radiometric-uPb", "x": 0, "y": 0, "params": {}},
            {"key": "ref1", "node_type": "reference", "x": -200, "y": 0,
             "params": {"reference": "cohen-2013"}},
        ],
        "edges": [
            {"source": "ref1", "source_port": "citation", "target": "obs1",
             "target_port": "cited", "kind": "cite"},
        ],
        "viewport": {},
    }


def test_cite_edge_roundtrip_and_data_exempt(api, graph):
    """cite edge 는 포트 검증·데이터 사이클 판정에서 제외되고 왕복한다(대상에 선언 포트 불필요)."""
    put = api.put(f"/api/graphs/{graph.pk}/", _cite_graph(), format="json")
    assert put.status_code == 200, put.data
    edges = api.get(f"/api/graphs/{graph.pk}/").data["edges"]
    assert edges[0]["kind"] == "cite" and edges[0]["target_port"] == "cited"


def test_cite_edge_ignored_by_evaluation(api, graph):
    """cite edge 는 평가 위상에서 제외 — reference 노드가 data 노드 결과를 바꾸지 않는다."""
    from engine.evaluate import evaluate_graph
    api.put(f"/api/graphs/{graph.pk}/", _cite_graph(), format="json")
    g = Graph.objects.get(pk=graph.pk)
    run = evaluate_graph(g)
    by_key = {r.node_key: r for r in run.results.all()}
    assert by_key["obs1"].provenance == []          # cite 는 data provenance 가 아님
    assert by_key["ref1"].distribution is None       # reference 노드는 값 없음


def test_graph_references_endpoint(api, graph, db):
    """그래프 참고문헌 API — reference 노드가 가리키는 Reference + cite 대상(bake→bibliography 토대)."""
    from references.models import Reference
    Reference.objects.create(slug="cohen-2013", doi="10.1130/2012.chart", title="ICS chart", authors="Cohen", year=2013)
    api.put(f"/api/graphs/{graph.pk}/", _cite_graph(), format="json")
    data = api.get(f"/api/graphs/{graph.pk}/references/").data
    assert [r["slug"] for r in data["bibliography"]] == ["cohen-2013"]
    assert data["bibliography"][0]["link"] == "https://doi.org/10.1130/2012.chart"
    assert data["citations"] == [{"node": "ref1", "reference": "cohen-2013", "cites": ["obs1"]}]
    assert data["by_boundary"] == {}                 # no gateway in this graph → no per-boundary attribution


# --- P05.2 ownership & visibility ---

def test_anonymous_cannot_write(graph):
    """익명 = 읽기 전용. 그래프 편집/생성은 인증 필요."""
    anon = APIClient()
    assert anon.put(f"/api/graphs/{graph.pk}/", _payload(), format="json").status_code in (401, 403)
    assert anon.post("/api/graphs/", {"slug": "x", "name": "X", "nodes": [], "edges": []}, format="json").status_code in (401, 403)


def test_non_owner_cannot_write_public_but_owner_can(api, graph, node_types):
    """공개(보이는) 그래프도 owner만 쓰기(403); owner는 가능(200). (숨은 샌드박스는 404 — 가시성 테스트 참고.)"""
    from django.contrib.auth import get_user_model
    pub = Graph.objects.create(slug="pub-edit", name="Pub", owner=graph.owner, status=Graph.Status.RATIFIED)
    other = APIClient()
    other.force_authenticate(user=get_user_model().objects.create_user("mallory", password="pw12345"))
    assert other.put(f"/api/graphs/{pub.pk}/", _payload(), format="json").status_code == 403
    assert api.put(f"/api/graphs/{graph.pk}/", _payload(), format="json").status_code == 200


def test_fork_deep_clones_and_reowns(api, graph, node_types):
    """Fork = 위상 깊은 복제(nodes/edges/groups) + 새 owner·sandbox·forked_from. 원본 불변."""
    payload = _payload()
    payload["groups"] = [{"key": "g1", "name": "Grp", "collapsed": False, "x": 5, "y": 5}]
    payload["nodes"][0]["group"] = "g1"
    api.put(f"/api/graphs/{graph.pk}/", payload, format="json")
    Graph.objects.filter(pk=graph.pk).update(status=Graph.Status.RATIFIED)   # public → forkable by others

    from django.contrib.auth import get_user_model
    forker = APIClient()
    fuser = get_user_model().objects.create_user("forker", password="pw12345")
    forker.force_authenticate(user=fuser)
    resp = forker.post(f"/api/graphs/{graph.pk}/fork/")
    assert resp.status_code == 201, resp.data
    fork = resp.data
    assert fork["owner"] == "forker" and fork["status"] == "sandbox"
    assert fork["forked_from"] == graph.slug and fork["id"] != graph.id
    assert {n["key"] for n in fork["nodes"]} == {"obs1", "adm"}
    assert len(fork["edges"]) == 1 and fork["groups"][0]["key"] == "g1"
    assert next(n for n in fork["nodes"] if n["key"] == "obs1")["group"] == "g1"
    # 원본은 그대로, 새 그래프는 forker 것
    assert Graph.objects.get(pk=graph.pk).owner_id == graph.owner_id
    assert Graph.objects.get(pk=fork["id"]).owner_id == fuser.id


def test_fork_requires_auth(graph):
    assert APIClient().post(f"/api/graphs/{graph.pk}/fork/").status_code in (401, 403)


def test_aux_graph_endpoints_dont_leak_private_sandbox(api, graph, node_types):
    """bake / verify / icc-chart must not expose another user's private sandbox graph by pk."""
    from django.contrib.auth import get_user_model
    api.put(f"/api/graphs/{graph.pk}/", _payload(), format="json")   # ann's private sandbox has content
    other = APIClient()
    other.force_authenticate(user=get_user_model().objects.create_user("mallory", password="pw12345"))
    assert other.get(f"/api/graphs/{graph.pk}/icc-chart/").status_code == 404
    assert other.post(f"/api/graphs/{graph.pk}/verify/").status_code == 404
    assert other.post(f"/api/graphs/{graph.pk}/bake/").status_code == 404
    # anonymous likewise cannot read a private sandbox's chart
    assert APIClient().get(f"/api/graphs/{graph.pk}/icc-chart/").status_code == 404


def test_sandbox_visibility(api, graph, node_types):
    """샌드박스는 owner 전용; 공개(proposed/ratified)·시스템(owner=null)은 모두 열람."""
    from django.contrib.auth import get_user_model
    Graph.objects.create(slug="sys-demo", name="Demo", owner=None)           # 시스템 = 공개
    Graph.objects.create(slug="pub", name="Pub", owner=graph.owner, status=Graph.Status.RATIFIED)
    stranger = APIClient()
    stranger.force_authenticate(user=get_user_model().objects.create_user("na", password="pw12345"))
    slugs = {g["slug"] for g in stranger.get("/api/graphs/").data}
    assert "sys-demo" in slugs and "pub" in slugs        # 공개·시스템 보임
    assert "sandbox-1" not in slugs                        # 남의 샌드박스 숨김
    assert stranger.get(f"/api/graphs/{graph.pk}/").status_code == 404
    assert "sandbox-1" in {g["slug"] for g in api.get("/api/graphs/").data}   # owner 에겐 보임

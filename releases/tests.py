import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from chrono.models import Boundary
from graph.models import Gateway, Graph, NodeInstance
from nodes.models import NodeType
from releases.models import (
    CandidateOutput, ModelCandidate, Release, Selection,
)
from releases.services import bake_graph, bake_release, diff_releases, next_release_version, snapshot_graph


@pytest.fixture
def chrono(db):
    call_command("loaddata", "01_chrono", verbosity=0)


@pytest.fixture
def nodes(db):
    call_command("loaddata", "02_nodes", verbosity=0)


def _graph_with_gateway(slug="g1"):
    camb = Boundary.objects.get(slug="base-cambrian")
    g = Graph.objects.create(slug=slug, name="G1")
    pub = NodeInstance.objects.create(
        graph=g, key="pub", node_type=NodeType.objects.get(slug="published-age"),
        params={"distribution": {"fidelity": "exact", "value_ma": 538.8}},
    )
    Gateway.objects.create(graph=g, slug="gw", name="Base Cambrian", node=pub, boundary=camb)
    return g


# --- P04.1: bake = immutable named Vault artifact ---

def test_snapshot_graph_is_immutable_and_named(chrono, nodes):
    g = _graph_with_gateway()
    r1, n1 = snapshot_graph(g)
    r2, n2 = snapshot_graph(g)
    assert r1.pk != r2.pk                              # each bake = a distinct artifact (never overwrites)
    assert n1 == 1 and n2 == 1
    assert r1.kind == Release.Kind.BAKE and r1.source_graph == g
    day = timezone.now().strftime("%Y%m%d")
    assert r1.version == f"GeologicTimeScale.Release.{day}.01"
    assert r2.version == f"GeologicTimeScale.Release.{day}.02"   # daily sequence increments
    assert r1.records.get().value_ma == 538.8


def test_snapshot_graph_custom_label(chrono, nodes):
    g = _graph_with_gateway()
    r, _ = snapshot_graph(g, label="MyChart.v1")
    assert r.version == "MyChart.v1" and r.kind == Release.Kind.BAKE


def test_scratch_bake_is_transient_and_reused(chrono, nodes):
    g = _graph_with_gateway()
    r1, _ = bake_graph(g)
    r2, _ = bake_graph(g)
    assert r1.pk == r2.pk                              # graph:<slug> reused (overwritten), for verify
    assert r1.kind == Release.Kind.TRANSIENT


def test_vault_list_excludes_transient(chrono, nodes):
    g = _graph_with_gateway()
    snapshot_graph(g)                                  # kept bake
    bake_graph(g)                                      # transient scratch
    kinds = [r["kind"] for r in APIClient().get("/api/releases/").data]
    assert "transient" not in kinds and "bake" in kinds


# --- P05.4: propose / review / ratify (= CI) ---

@pytest.fixture
def ci(chrono, nodes):
    from django.contrib.auth import get_user_model
    from chrono.models import Authority, Boundary
    from accounts.models import Membership
    from releases.models import BoundaryRecord
    User = get_user_model()

    author = User.objects.create_user("author", password="pw12345")
    g = _graph_with_gateway()                                   # base-cambrian gateway → 538.8
    Graph.objects.filter(pk=g.pk).update(owner=author)
    g.refresh_from_db()

    camb = Boundary.objects.get(slug="base-cambrian")
    baseline = Release.objects.create(version="ICS-baseline", kind=Release.Kind.PUBLISHED, is_baseline=True)
    BoundaryRecord.objects.create(release=baseline, boundary=camb, value_ma=540.0,
                                  definition_type=camb.definition_type or "")

    ratifier = User.objects.create_user("chair", password="pw12345")
    ics = Authority.objects.create(slug="ics-gov", name="ICS Gov", kind=Authority.Kind.ICS)
    Membership.objects.create(user=ratifier, authority=ics, role=Membership.Role.CHAIR)
    return {"g": g, "author": author, "ratifier": ratifier, "baseline": baseline}


def _propose(ci):
    api = APIClient(); api.force_authenticate(user=ci["author"])
    return api.post(f"/api/graphs/{ci['g'].pk}/propose/", {"comment": "shift"}, format="json")


def test_propose_sets_proposed_and_affected(ci):
    resp = _propose(ci)
    assert resp.status_code == 201, resp.data
    p = resp.data["proposal"]
    assert p["state"] == "open" and p["affected"] == ["base-cambrian"] and p["author"] == "author"
    assert resp.data["diff"]["value_diff"][0]["delta"] == -1.2      # 538.8 − 540
    assert Graph.objects.get(pk=ci["g"].pk).status == "proposed"


def test_only_owner_proposes(ci):
    other = APIClient(); other.force_authenticate(user=ci["ratifier"])
    assert other.post(f"/api/graphs/{ci['g'].pk}/propose/").status_code == 403


def test_ratify_publishes_new_baseline(ci):
    pid = _propose(ci).data["proposal"]["id"]
    # author (personal fork only) cannot ratify
    aapi = APIClient(); aapi.force_authenticate(user=ci["author"])
    assert aapi.post(f"/api/proposals/{pid}/ratify/").status_code == 403
    # ICS member can
    rapi = APIClient(); rapi.force_authenticate(user=ci["ratifier"])
    ok = rapi.post(f"/api/proposals/{pid}/ratify/", {"comment": "ok"}, format="json")
    assert ok.status_code == 200 and ok.data["proposal"]["state"] == "merged"
    assert Graph.objects.get(pk=ci["g"].pk).status == "ratified"
    baselines = Release.objects.filter(is_baseline=True)
    assert baselines.count() == 1                                   # old demoted, new sole baseline
    assert baselines.get().version.startswith("GeologicTimeScale.Published.")
    assert baselines.get().records.get(boundary__slug="base-cambrian").value_ma == 538.8


def test_reject_returns_to_sandbox(ci):
    pid = _propose(ci).data["proposal"]["id"]
    rapi = APIClient(); rapi.force_authenticate(user=ci["ratifier"])
    resp = rapi.post(f"/api/proposals/{pid}/reject/", {"comment": "no"}, format="json")
    assert resp.status_code == 200 and resp.data["proposal"]["state"] == "rejected"
    assert Graph.objects.get(pk=ci["g"].pk).status == "sandbox"
    assert Release.objects.get(is_baseline=True).version == "ICS-baseline"   # unchanged


def test_proposal_detail_carries_diff(ci):
    pid = _propose(ci).data["proposal"]["id"]
    d = APIClient().get(f"/api/proposals/{pid}/").data                # anonymous public review
    assert d["diff"]["value_diff"][0]["boundary"] == "base-cambrian"
    assert d["can_ratify"] is False


def test_next_release_version_sequence(chrono):
    day = timezone.now().strftime("%Y%m%d")
    assert next_release_version() == f"GeologicTimeScale.Release.{day}.01"
    Release.objects.create(version=f"GeologicTimeScale.Release.{day}.01", kind=Release.Kind.BAKE)
    assert next_release_version() == f"GeologicTimeScale.Release.{day}.02"


def _candidate(slug, boundary, value, method="cross-section-correlation"):
    c = ModelCandidate.objects.create(slug=slug, kind="global-d13C-age-model", method=method)
    CandidateOutput.objects.create(
        candidate=c, boundary=boundary,
        distribution={"fidelity": "decomposed", "value_ma": value, "budget": {"analytical": 0.6}},
    )
    return c


def _release(version, boundary, candidate):
    r = Release.objects.create(version=version)
    Selection.objects.create(release=r, boundary=boundary, candidate=candidate)
    return r


# --- bake ---

def test_bake_snapshots_selection(chrono):
    camb = Boundary.objects.get(slug="base-cambrian")
    cand = _candidate("cand-a", camb, 538.8)
    rel = _release("ICC-2024/12", camb, cand)
    n = bake_release(rel)
    assert n == 1
    rec = rel.records.get(boundary=camb)
    assert rec.value_ma == 538.8
    assert rec.definition_type == "GSSP"          # chrono.Boundary 스냅샷
    assert rec.method == "cross-section-correlation"
    assert rec.candidate == cand


# --- diff: 값 vs 토폴로지 직교 ---

def test_value_diff(chrono):
    camb = Boundary.objects.get(slug="base-cambrian")
    r1 = _release("v1", camb, _candidate("c1", camb, 538.8))
    r2 = _release("v2", camb, _candidate("c2", camb, 536.0))
    bake_release(r1)
    bake_release(r2)
    d = diff_releases(r1, r2)
    assert d["topology_diff"] == []
    assert d["value_diff"][0]["boundary"] == "base-cambrian"
    assert d["value_diff"][0]["delta"] == -2.8


def test_topology_retype_is_orthogonal(chrono):
    """base-proterozoic 를 GSSA→GSSP 로 retype = 토폴로지 diff (값 diff 아님)."""
    prot = Boundary.objects.get(slug="base-proterozoic")
    r1 = _release("v1", prot, _candidate("cd1", prot, 2500.0, method="decreed"))
    bake_release(r1)
    # 재배선: 같은 값이지만 정의 타입 변경.
    prot.definition_type = "GSSP"
    prot.save()
    r2 = _release("v2", prot, _candidate("cd2", prot, 2500.0, method="local-interpolation"))
    bake_release(r2)
    d = diff_releases(r1, r2)
    assert d["value_diff"] == []                  # 값 그대로
    assert d["topology_diff"][0] == {"boundary": "base-proterozoic", "op": "retype",
                                     "from": "GSSA", "to": "GSSP"}


def test_added_removed_topology(chrono):
    camb = Boundary.objects.get(slug="base-cambrian")
    trias = Boundary.objects.get(slug="base-triassic")
    r1 = _release("v1", camb, _candidate("x1", camb, 538.8))
    r2 = Release.objects.create(version="v2")
    Selection.objects.create(release=r2, boundary=camb, candidate=ModelCandidate.objects.get(slug="x1"))
    Selection.objects.create(release=r2, boundary=trias,
                             candidate=_candidate("x2", trias, 251.9, method="local-interpolation"))
    bake_release(r1)
    bake_release(r2)
    d = diff_releases(r1, r2)
    assert {"boundary": "base-triassic", "op": "added"} in d["topology_diff"]


# --- API ---

def test_bake_and_diff_endpoints(chrono):
    camb = Boundary.objects.get(slug="base-cambrian")
    r1 = _release("v1", camb, _candidate("c1", camb, 538.8))
    r2 = _release("v2", camb, _candidate("c2", camb, 536.0))
    api = APIClient()
    assert api.post(f"/api/releases/{r1.pk}/bake/").data["baked"] == 1
    api.post(f"/api/releases/{r2.pk}/bake/")
    d = api.get(f"/api/releases/diff/?a={r1.pk}&b={r2.pk}").data
    assert d["value_diff"][0]["delta"] == -2.8
    rel = api.get(f"/api/releases/{r1.pk}/").data
    assert rel["records"][0]["value_ma"] == 538.8

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


# --- bake → bibliography (cite provenance) ---

def test_bake_collects_bibliography(chrono, nodes):
    from graph.models import Edge
    from references.models import Reference
    g = _graph_with_gateway()
    pub = g.nodes.get(key="pub")
    Reference.objects.create(slug="cohen-2013", doi="10.1130/x", title="ICS chart", authors="Cohen", year=2013)
    ref = NodeInstance.objects.create(graph=g, key="ref1",
                                      node_type=NodeType.objects.get(slug="reference"),
                                      params={"reference": "cohen-2013"})
    Edge.objects.create(graph=g, source=ref, source_port="citation", target=pub, target_port="cited", kind="cite")
    rel, _ = snapshot_graph(g)
    assert rel.records.get().references == ["cohen-2013"]        # cite provenance snapshot on the record
    data = APIClient().get(f"/api/releases/{rel.pk}/references/").data
    assert [r["slug"] for r in data["bibliography"]] == ["cohen-2013"]
    assert data["by_boundary"]["base-cambrian"] == ["cohen-2013"]


def test_bibliography_only_includes_upstream_cited(chrono, nodes):
    from graph.models import Edge
    from graph.services import graph_bibliography
    from references.models import Reference
    g = _graph_with_gateway()
    pub = g.nodes.get(key="pub")
    Reference.objects.create(slug="rel-ref", title="R")
    Reference.objects.create(slug="unrel-ref", title="U")
    r1 = NodeInstance.objects.create(graph=g, key="r1", node_type=NodeType.objects.get(slug="reference"),
                                     params={"reference": "rel-ref"})
    Edge.objects.create(graph=g, source=r1, source_port="citation", target=pub, target_port="cited", kind="cite")
    iso = NodeInstance.objects.create(graph=g, key="iso", node_type=NodeType.objects.get(slug="published-age"), params={})
    r2 = NodeInstance.objects.create(graph=g, key="r2", node_type=NodeType.objects.get(slug="reference"),
                                     params={"reference": "unrel-ref"})
    Edge.objects.create(graph=g, source=r2, source_port="citation", target=iso, target_port="cited", kind="cite")
    biblio = graph_bibliography(g)
    assert biblio["by_boundary"]["base-cambrian"] == ["rel-ref"]   # only the upstream-cited reference contributes
    assert set(biblio["all"]) == {"rel-ref", "unrel-ref"}          # both reference nodes present in the graph


# --- P05.5: sandbox overrides (baseline + per-boundary candidate swap) ---

@pytest.fixture
def sandbox_setup(chrono):
    """A baseline with two competing candidates on base-cambrian (A=538.8 selected, B=540.0)."""
    from django.contrib.auth import get_user_model
    camb = Boundary.objects.get(slug="base-cambrian")
    a = _candidate("cand-a", camb, 538.8)
    b = _candidate("cand-b", camb, 540.0)
    baseline = _release("ICS-2024/12", camb, a)          # baseline picks A
    baseline.is_baseline = True; baseline.kind = Release.Kind.PUBLISHED; baseline.save()
    bake_release(baseline)
    user = get_user_model().objects.create_user("ann", password="pw12345")
    return {"baseline": baseline, "camb": camb, "a": a, "b": b, "user": user}


def test_sandbox_copies_baseline_then_overrides(sandbox_setup):
    from releases.services import create_sandbox_release, set_override
    s = sandbox_setup
    sb = create_sandbox_release(s["baseline"], s["user"])
    assert sb.kind == Release.Kind.SANDBOX and sb.base_id == s["baseline"].id and sb.owner == s["user"]
    assert sb.records.get(boundary=s["camb"]).value_ma == 538.8       # starts identical to baseline
    set_override(sb, "base-cambrian", "cand-b")
    assert sb.records.get(boundary=s["camb"]).value_ma == 540.0       # overridden
    from releases.services import diff_releases
    assert diff_releases(s["baseline"], sb)["value_diff"][0]["delta"] == round(540.0 - 538.8, 6)
    set_override(sb, "base-cambrian", None)                            # reset to baseline
    assert sb.records.get(boundary=s["camb"]).value_ma == 538.8


def test_sandbox_endpoints_and_visibility(sandbox_setup):
    s = sandbox_setup
    owner = APIClient(); owner.force_authenticate(user=s["user"])
    sb = owner.post(f"/api/releases/{s['baseline'].pk}/sandbox/")
    assert sb.status_code == 201 and sb.data["kind"] == "sandbox"
    sid = sb.data["id"]
    # overridable candidates listed
    cands = owner.get(f"/api/releases/{sid}/candidates/").data["boundaries"]
    row = next(r for r in cands if r["boundary"] == "base-cambrian")
    assert set(row["options"]) == {"cand-a", "cand-b"} and row["selected"] == "cand-a"
    # override via endpoint
    ov = owner.post(f"/api/releases/{sid}/override/", {"boundary": "base-cambrian", "candidate": "cand-b"}, format="json")
    assert ov.status_code == 200
    assert next(r for r in ov.data["records"] if r["boundary"] == "base-cambrian")["value_ma"] == 540.0
    # other users can't see or override this private sandbox
    from django.contrib.auth import get_user_model
    other = APIClient(); other.force_authenticate(user=get_user_model().objects.create_user("bob", password="pw12345"))
    assert sid not in {r["id"] for r in other.get("/api/releases/").data}
    assert other.post(f"/api/releases/{sid}/override/", {"boundary": "base-cambrian", "candidate": "cand-a"}, format="json").status_code in (403, 404)
    # anonymous cannot create a sandbox
    assert APIClient().post(f"/api/releases/{s['baseline'].pk}/sandbox/").status_code in (401, 403)


def test_aux_release_endpoints_dont_leak_private_sandbox(sandbox_setup):
    """release icc-chart / narrate / diff / bake must not expose another user's private sandbox by pk."""
    from django.contrib.auth import get_user_model
    from releases.services import create_sandbox_release
    s = sandbox_setup
    sb = create_sandbox_release(s["baseline"], s["user"])          # ann's private sandbox
    other = APIClient()
    other.force_authenticate(user=get_user_model().objects.create_user("bob", password="pw12345"))
    assert other.get(f"/api/releases/{sb.pk}/icc-chart/").status_code == 404
    assert other.post(f"/api/releases/{sb.pk}/narrate/").status_code == 404
    assert other.post(f"/api/releases/{sb.pk}/bake/").status_code == 404
    assert other.get(f"/api/releases/diff/?a={s['baseline'].pk}&b={sb.pk}").status_code == 404
    # owner still reaches it
    owner = APIClient(); owner.force_authenticate(user=s["user"])
    assert owner.get(f"/api/releases/{sb.pk}/icc-chart/").status_code == 200


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


def test_shape_diff_detects_uncertainty_appearing(chrono):
    """retype 이 값의 *모양*을 바꾼다: 스칼라 exact → 분포(±). 값은 거의 안 움직여도 shape_diff 로 잡힘."""
    from releases.models import BoundaryRecord
    cryo = Boundary.objects.get(slug="base-cryogenian")
    r1 = Release.objects.create(version="cryo-gssa")
    r2 = Release.objects.create(version="cryo-gssp")
    BoundaryRecord.objects.create(release=r1, boundary=cryo, definition_type="GSSA",
                                  value_ma=720.0, uncertainty={"fidelity": "exact", "value_ma": 720.0})
    BoundaryRecord.objects.create(
        release=r2, boundary=cryo, definition_type="GSSP", value_ma=719.5,
        uncertainty={"fidelity": "decomposed", "value_ma": 719.5, "sigma": 2, "budget": {"model": 0.9}})
    d = diff_releases(r1, r2)
    # 세 축이 함께 잡힌다: retype(정의) + 작은 값 이동 + shape(오차 등장).
    assert d["topology_diff"][0]["op"] == "retype"
    assert d["value_diff"][0]["delta"] == -0.5
    sd = d["shape_diff"][0]
    assert sd["boundary"] == "base-cryogenian"
    assert sd["from_kind"] == "exact" and sd["to_kind"] == "dist"
    assert sd["from"] == "exact" and sd["to"].startswith("±")


def test_shape_diff_empty_when_shape_unchanged(chrono):
    """두 exact 값(값만 다름) → shape 변화 없음(shape_diff 비어 있음)."""
    from releases.models import BoundaryRecord
    camb = Boundary.objects.get(slug="base-cambrian")
    r1 = Release.objects.create(version="s1")
    r2 = Release.objects.create(version="s2")
    BoundaryRecord.objects.create(release=r1, boundary=camb, value_ma=538.8,
                                  uncertainty={"fidelity": "exact", "value_ma": 538.8})
    BoundaryRecord.objects.create(release=r2, boundary=camb, value_ma=536.0,
                                  uncertainty={"fidelity": "exact", "value_ma": 536.0})
    d = diff_releases(r1, r2)
    assert d["shape_diff"] == [] and d["value_diff"][0]["delta"] == -2.8


# --- P06.3: authored clamps (L3a verify / L3b reconcile) ---

def _sub(slug):
    from chrono.models import Authority
    return Authority.objects.create(slug=slug, name=slug.upper(), kind=Authority.Kind.SUBCOMMISSION)


def _clamp(rel, slug, boundary, kind, value, owner):
    from releases.models import Clamp
    c = Clamp.objects.create(slug=slug, owner=owner, target_boundary=boundary, kind=kind, value=value)
    rel.clamps.add(c)
    return c


def _baked(version="v1", value=538.8):
    camb = Boundary.objects.get(slug="base-cambrian")
    rel = _release(version, camb, _candidate(f"cand-{version}", camb, value))
    bake_release(rel)
    return rel, camb


def test_verify_clamps_flags_range_violation(chrono):
    from releases.services import verify_clamps
    rel, camb = _baked(value=538.8)
    _clamp(rel, "cl-range", camb, "range", {"range": [530.0, 535.0]}, _sub("camb-sub"))
    v = verify_clamps(rel)
    assert any(x["kind"] == "range" and x["boundary"] == "base-cambrian" for x in v)
    assert rel.records.get(boundary=camb).value_ma == 538.8    # L3a = 값 불변


def test_verify_clamps_passes_when_honored(chrono):
    from releases.services import verify_clamps
    rel, camb = _baked(value=538.8)
    _clamp(rel, "cl-r", camb, "range", {"range": [536.0, 540.0]}, _sub("s"))
    assert verify_clamps(rel) == []


def test_reconcile_applies_pin(chrono):
    from releases.services import reconcile_release
    rel, camb = _baked(value=538.8)
    _clamp(rel, "cl-pin", camb, "pin", {"value": 539.0}, _sub("s"))
    changed, conflicts = reconcile_release(rel)
    assert changed == 1 and conflicts == []
    rec = rel.records.get(boundary=camb)
    assert rec.value_ma == 539.0 and rec.uncertainty["fidelity"] == "exact"   # pin → 점질량


def test_reconcile_pin_beats_range(chrono):
    from releases.services import reconcile_release
    rel, camb = _baked(value=538.8)
    owner = _sub("s")
    _clamp(rel, "cl-pin", camb, "pin", {"value": 537.0}, owner)
    _clamp(rel, "cl-range", camb, "range", {"range": [520.0, 525.0]}, owner)   # 무시됨(precedence 낮음)
    reconcile_release(rel)
    assert rel.records.get(boundary=camb).value_ma == 537.0


def test_reconcile_flags_conflicting_owners(chrono):
    from releases.services import reconcile_release
    rel, camb = _baked(value=538.8)
    _clamp(rel, "p1", camb, "pin", {"value": 539.0}, _sub("o1"))
    _clamp(rel, "p2", camb, "pin", {"value": 536.0}, _sub("o2"))    # 동급·다owner = 충돌
    _, conflicts = reconcile_release(rel)
    assert "base-cambrian" in conflicts


def test_clamps_endpoint_and_reconcile_permission(chrono):
    from django.contrib.auth import get_user_model
    rel, camb = _baked(value=538.8)
    _clamp(rel, "cl-range", camb, "range", {"range": [530.0, 535.0]}, _sub("s"))
    # L3a verify via API (public read)
    resp = APIClient().get(f"/api/releases/{rel.pk}/clamps/")
    assert resp.status_code == 200 and len(resp.data["violations"]) == 1
    # reconcile is owner/staff only
    assert APIClient().post(f"/api/releases/{rel.pk}/reconcile/").status_code in (401, 403)
    staff = APIClient(); staff.force_authenticate(user=get_user_model().objects.create_user("ed", password="pw12345", is_staff=True))
    r = staff.post(f"/api/releases/{rel.pk}/reconcile/")
    assert r.status_code == 200 and r.data["changed"] == 1    # range 적용 → 값 이동
    assert APIClient().get(f"/api/releases/{rel.pk}/clamps/").data["violations"] == []   # 이제 지켜짐


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
    from django.contrib.auth import get_user_model
    camb = Boundary.objects.get(slug="base-cambrian")
    r1 = _release("v1", camb, _candidate("c1", camb, 538.8))
    r2 = _release("v2", camb, _candidate("c2", camb, 536.0))
    api = APIClient()
    api.force_authenticate(user=get_user_model().objects.create_user("ed", password="pw12345", is_staff=True))
    assert api.post(f"/api/releases/{r1.pk}/bake/").data["baked"] == 1
    api.post(f"/api/releases/{r2.pk}/bake/")
    d = api.get(f"/api/releases/diff/?a={r1.pk}&b={r2.pk}").data
    assert d["value_diff"][0]["delta"] == -2.8
    rel = api.get(f"/api/releases/{r1.pk}/").data
    assert rel["records"][0]["value_ma"] == 538.8

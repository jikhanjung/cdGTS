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
    # ICS chart.ttl 전 rank: units 177(Eon4/Era10/Period22/Subperiod2/Epoch37/Age102) · boundary 177 · type 13
    # (Carboniferous 아계 Mississippian/Pennsylvanian 추가로 175→177)
    assert (units, boundaries, types, graphs) == (177, 177, 13, 4)
    # releases 3(예시 2 + 공표 ICS-2024/12) · records = 예시 5 + 공표 177 bake
    assert (releases, records) == (3, 182)
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
    계층 완성: 그래프가 **전 177 ICC 경계**(Eon…Age, Subperiod 포함)를 재구성 → 공표 릴리스와 대칭."""
    from graph.models import Graph
    from releases.services import bake_graph
    g = Graph.objects.get(slug="example-icc-partial")
    rel, n = bake_graph(g)
    assert n == 177                                          # 전 ICC 경계 (period+36·age91·epoch25·subperiod2·첫30)
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
    assert n2 == 177 and rel2.pk == rel.pk

    # HTTP 엔드포인트도 확인
    from rest_framework.test import APIClient
    resp = APIClient().post(f"/api/graphs/{g.pk}/bake/")
    assert resp.status_code == 200 and resp.data["baked"] == 177
    assert resp.data["release"]["version"] == "graph:example-icc-partial"
    assert len(resp.data["release"]["records"]) == 177


def test_icc_chart_tiles_by_rank(seeded):
    """ICC 차트 엔드포인트 — 조립 그래프가 Eon…Age 5 rank 를 rank 별 base 연대로 타일링(top=younger, bottom=older)."""
    from graph.models import Graph
    from rest_framework.test import APIClient
    g = Graph.objects.get(slug="example-icc-partial")
    resp = APIClient().get(f"/api/graphs/{g.pk}/icc-chart/")
    assert resp.status_code == 200
    d = resp.data
    assert d["max_ma"] == 4567.0
    lv = {x["rank"]: x["bands"] for x in d["levels"]}
    # 계층 완성: 그래프-bake 도 공표 릴리스와 대칭인 6 rank 컬럼 (Subperiod = Carboniferous 만)
    assert [x["rank"] for x in d["levels"]] == ["Eon", "Era", "Period", "Subperiod", "Epoch", "Age"]
    assert (len(lv["Eon"]), len(lv["Era"]), len(lv["Period"])) == (4, 10, 22)
    assert len(lv["Subperiod"]) == 2 and len(lv["Epoch"]) == 37 and len(lv["Age"]) == 102  # 공표 릴리스와 동일
    # Subperiod 는 sparse rank — 밴드가 제 구간에서 닫힌다(Pennsylvanian 은 Carboniferous 젊은 끝=Permian base 298.9)
    sp = {b["slug"]: b for b in lv["Subperiod"]}
    assert sp["mississippian"]["color"] == "#678F66" and sp["pennsylvanian"]["color"] == "#7EBCC6"
    assert (sp["mississippian"]["top"], sp["mississippian"]["bottom"]) == (323.4, 358.86)
    assert (sp["pennsylvanian"]["top"], sp["pennsylvanian"]["bottom"]) == (298.9, 323.4)
    eon = {b["slug"]: b for b in lv["Eon"]}
    assert eon["phanerozoic"]["top"] == 0.0 and eon["phanerozoic"]["bottom"] == 538.8
    assert eon["hadean"]["bottom"] == 4567.0
    assert lv["Period"][0]["slug"] == "quaternary" and lv["Period"][0]["top"] == 0.0
    # 공식 ICS 색 주입 확인 (Triassic = #812B92)
    per = {b["slug"]: b for b in lv["Period"]}
    assert per["triassic"]["color"] == "#812B92"
    # Epoch 은 별도 노드 없이 일치 age pub 에 게이트웨이로 산출 → base(Middle Triassic)=base(Anisian)
    ep = {b["slug"]: b for b in lv["Epoch"]}
    age = {b["slug"]: b for b in lv["Age"]}
    assert ep["middletriassic"]["bottom"] == age["anisian"]["bottom"] == 247.0
    # 타일링 폐합 회귀: 첫 age/epoch(=period base, coincident GSSP)가 등록돼 밴드가 period 경계에서 닫힘.
    # (없으면 이전 period 마지막 밴드가 P-T 경계를 넘어 Induan/Lower Triassic 을 삼켰다)
    assert age["induan"]["bottom"] == ep["lowertriassic"]["bottom"] == 251.9022
    assert age["changhsingian"]["top"] == 251.9022            # 경계 넘지 않음
    assert ep["lopingian"]["top"] == 251.9022


def test_release_icc_chart_five_ranks(seeded):
    """공표 릴리스(ICS-2024/12) ICC 차트 — Age 까지 6 rank 컬럼(Subperiod 포함), 값·색 포함."""
    from rest_framework.test import APIClient
    r = Release.objects.get(version="ICS-2024/12")
    resp = APIClient().get(f"/api/releases/{r.pk}/icc-chart/")
    assert resp.status_code == 200
    d = resp.data
    assert d["max_ma"] == 4567.0
    ranks = [lv["rank"] for lv in d["levels"]]
    assert ranks == ["Eon", "Era", "Period", "Subperiod", "Epoch", "Age"]     # 6 컬럼
    lv = {x["rank"]: x["bands"] for x in d["levels"]}
    assert len(lv["Age"]) >= 90 and len(lv["Epoch"]) >= 30       # stage/epoch 다수
    per = {b["slug"]: b for b in lv["Period"]}
    assert per["triassic"]["color"] == "#812B92"                 # 공식 색 통과
    # Age 컬럼 타일링: 최상단은 최근 age, top=0
    assert lv["Age"][0]["top"] == 0.0


def test_narrate_release_renders_and_persists(seeded):
    """narrate(bake 의 짝) — rank 별 서술 문서 + BoundaryRecord.narrative 저장. 사실 창작 없이 필드 렌더."""
    from rest_framework.test import APIClient
    r = Release.objects.get(version="ICS-2024/12")
    resp = APIClient().post(f"/api/releases/{r.pk}/narrate/")
    assert resp.status_code == 200
    secs = {s["rank"]: s["entries"] for s in resp.data["sections"]}
    assert list(secs) == ["Eon", "Era", "Period", "Subperiod", "Epoch", "Age"]
    # Subperiod 서술: Mississippian/Pennsylvanian (이중 명명 Subsystem)
    assert {e["boundary"] for e in secs["Subperiod"]} == {"base-mississippian", "base-pennsylvanian"}
    # GSSP 는 이중 명명 + 파생 연대 + 오차, GSSA 는 약속값(오차 없음)
    tri = next(e for e in secs["Period"] if e["boundary"] == "base-triassic")
    assert "Triassic System" in tri["narrative"] and "251.902 ± 0.024 Ma" in tri["narrative"] and "GSSP" in tri["narrative"]
    prot = next(e for e in secs["Eon"] if e["boundary"] == "base-proterozoic")
    assert "약속값" in prot["narrative"] and "±" not in prot["narrative"]
    # 저장 확인
    assert BoundaryRecord.objects.get(release=r, boundary__slug="base-triassic").narrative == tri["narrative"]
    # 오래된→젊은 순
    per = secs["Period"]
    assert per[0]["value_ma"] >= per[-1]["value_ma"]


def test_l2_duration_gate(seeded):
    """L2 지속시간 — 유닛 duration(base−top) 자동 검사. 영-길이면 L1(gap≥0)은 통과해도 L2 fail."""
    from graph.models import Graph, NodeInstance
    from engine.evaluate import evaluate_graph
    g = Graph.objects.get(slug="example-icc-partial")
    cert = evaluate_graph(g).certificate
    assert cert.checks["L2"] == "pass" and cert.passed

    # pub-olenekian(250.8, Age) 을 anisian(247.0) 과 동일화 → 같은 rank 영-길이 유닛
    n = NodeInstance.objects.get(graph=g, key="pub-olenekian")
    n.params["distribution"]["value_ma"] = 247.0
    n.save()
    cert2 = evaluate_graph(g).certificate
    assert cert2.checks["L1"] == "pass"        # order 는 gap≥0 이라 coincidence 허용
    assert cert2.checks["L2"] == "fail" and not cert2.passed


def test_graph_reconstructs_full_icc(seeded):
    """계층 완성 — 조립 그래프가 전 ICC 경계(Eon…Age)를 게이트웨이로 산출. registry-only 경계 없음."""
    from graph.models import Graph, Gateway
    g = Graph.objects.get(slug="example-icc-partial")
    covered = set(Gateway.objects.filter(graph=g).values_list("boundary__slug", flat=True))
    assert covered == set(Boundary.objects.values_list("slug", flat=True))    # 모든 경계가 네트웍에
    assert Gateway.objects.filter(graph=g, boundary__slug="base-fortunian").exists()  # 첫 age 도 coincident 게이트웨이
    assert Gateway.objects.filter(graph=g, boundary__slug="base-jurassic").exists()   # Period


def test_age_groups_all_periods(seeded):
    """전 period age 노드그룹 — Triassic 프로토타입 일반화. 그룹당 내부 age 분할점 + order 체인, tie 는 밖."""
    from graph.models import Graph, NodeGroup, Gateway, NodeInstance
    from engine.evaluate import evaluate_graph
    g = Graph.objects.get(slug="example-icc-partial")
    assert g.groups.filter(key__startswith="ages-").count() == 12     # age 세분 있는 period(Carboniferous 포함)
    grp = NodeGroup.objects.get(graph=g, key="ages-triassic")
    keys = set(grp.members.values_list("key", flat=True))
    # 멤버 = 내부 age pub 6 + 내부 order 5 (period 경계에 tie 하는 order 2 는 그룹 밖)
    assert {"pub-olenekian", "pub-anisian", "pub-ladinian", "pub-carnian", "pub-norian", "pub-rhaetian"} <= keys
    assert "oa-olenekian" not in keys and "oa-jurassic" not in keys    # tie order 는 외부
    assert len(keys) == 11
    # 내부 age 는 pub 노드 + 게이트웨이. 첫 age induan(=period base)은 pub 없이
    # period 산출노드에 coincident 게이트웨이로만 등록(하나의 GSSP 가 base-triassic 과 공유).
    assert Gateway.objects.filter(graph=g, boundary__slug="base-olenekian").exists()
    assert not NodeInstance.objects.filter(graph=g, key="pub-induan").exists()      # 첫 age = pub 없음
    assert Gateway.objects.filter(graph=g, boundary__slug="base-induan").exists()    # coincident 게이트웨이는 존재
    # 전 age 체인 통과 → L1·L2 pass
    run = evaluate_graph(g)
    assert run.certificate.passed and run.certificate.checks["L2"] == "pass"


def test_seed_content_canonical(seeded):
    """정본값 가드 — seed 파일 드리프트 회귀 방지(운영에서 겪은 age-depth/radiometric 어긋남)."""
    adm = NodeType.objects.get(slug="age-depth-model")
    assert adm.params_schema["method"]["choices"] == ["linear", "spline"]
    assert NodeType.objects.get(slug="radiometric-uPb").params_schema      # 비어있지 않음

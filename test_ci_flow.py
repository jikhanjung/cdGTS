"""
Tier-1 scenario test — the core "CI for science" flow end to end, over the *real* session + CSRF path.

Unlike the per-app unit tests (which use DRF `force_authenticate` and so skip CSRF), this drives the whole
golden path a browser walks — login → fork → edit(save) → diff → bake → propose → ratify — with Django's
test Client under `enforce_csrf_checks=True`, sending the csrftoken cookie back as an `X-CSRFToken` header
exactly like the SPA's `csrfHeaders()`. That closes the classic "green in pytest, 403 in the browser" gap and
locks the seam between the pieces (P05.1–.4), not just each piece in isolation.
"""
import json

import pytest
from django.core.management import call_command
from django.test import Client


@pytest.fixture
def scenario(db):
    call_command("loaddata", "01_chrono", verbosity=0)
    call_command("loaddata", "02_nodes", verbosity=0)

    from django.contrib.auth import get_user_model
    from accounts.models import Membership
    from chrono.models import Authority, Boundary
    from graph.models import Gateway, Graph, NodeInstance
    from nodes.models import NodeType
    from releases.models import BoundaryRecord, Release
    User = get_user_model()

    camb = Boundary.objects.get(slug="base-cambrian")

    # A system (owner=null → public) source graph: published-age 538.8 → base-cambrian gateway.
    src = Graph.objects.create(slug="sys-cambrian", name="System · Base Cambrian")
    pub = NodeInstance.objects.create(
        graph=src, key="pub", node_type=NodeType.objects.get(slug="published-age"),
        params={"distribution": {"fidelity": "exact", "value_ma": 538.8}},
    )
    Gateway.objects.create(graph=src, slug="gw", name="Base Cambrian", node=pub, boundary=camb)

    # The published baseline to diff/propose against: base-cambrian = 540.0.
    baseline = Release.objects.create(version="ICS-baseline", kind=Release.Kind.PUBLISHED, is_baseline=True)
    BoundaryRecord.objects.create(
        release=baseline, boundary=camb, value_ma=540.0, definition_type=camb.definition_type or "",
    )

    author = User.objects.create_user("author", password="pw12345")
    ratifier = User.objects.create_user("chair", password="pw12345")
    ics = Authority.objects.create(slug="ics-gov", name="ICS Gov", kind=Authority.Kind.ICS)
    Membership.objects.create(user=ratifier, authority=ics, role=Membership.Role.CHAIR)
    return {"src": src, "author": author, "ratifier": ratifier}


def _login(username, password="pw12345"):
    """Real session login through CSRF, mirroring the SPA: whoami primes the cookie, login sends it back."""
    c = Client(enforce_csrf_checks=True)
    c.get("/api/auth/whoami/")                       # @ensure_csrf_cookie → sets csrftoken
    r = c.post(
        "/api/auth/login/", data=json.dumps({"username": username, "password": password}),
        content_type="application/json", HTTP_X_CSRFTOKEN=c.cookies["csrftoken"].value,
    )
    assert r.status_code == 200, r.content
    return c


def _post(c, url, body=None):
    """POST with the current csrftoken as X-CSRFToken (token rotates on login, so re-read each call)."""
    return c.post(url, data=json.dumps(body or {}), content_type="application/json",
                  HTTP_X_CSRFTOKEN=c.cookies["csrftoken"].value)


def test_csrf_is_actually_enforced_on_session_writes(scenario):
    """A session write without the header is refused — proves the flow below isn't passing by luck."""
    c = _login("author")
    naked = c.post(f"/api/graphs/{scenario['src'].pk}/fork/", content_type="application/json")
    assert naked.status_code == 403


def test_ci_golden_path_login_fork_edit_bake_diff_propose_ratify(scenario):
    s = scenario
    c = _login("author")

    # 1. Fork the system graph into my own sandbox (the deep clone carries the gateway).
    r = _post(c, f"/api/graphs/{s['src'].pk}/fork/")
    assert r.status_code == 201, r.content
    fork = r.json()
    fid = fork["id"]
    assert fork["owner"] == "author" and fork["status"] == "sandbox"
    assert len(fork["gateways"]) == 1

    # 2. Edit: shift the published age 538.8 → 537.0 and save the whole graph (PUT, like the editor).
    for n in fork["nodes"]:
        if n["key"] == "pub":
            n["params"]["distribution"]["value_ma"] = 537.0
    put = c.put(
        f"/api/graphs/{fid}/",
        data=json.dumps({"nodes": fork["nodes"], "edges": fork["edges"], "groups": fork["groups"]}),
        content_type="application/json", HTTP_X_CSRFTOKEN=c.cookies["csrftoken"].value,
    )
    assert put.status_code == 200, put.content
    saved = c.get(f"/api/graphs/{fid}/").json()
    assert len(saved["gateways"]) == 1                    # the edit must not wipe the boundary contract

    # 3. Science-CI diff against the published baseline: my edit moved base-cambrian by −3.0 Ma.
    d = _post(c, f"/api/graphs/{fid}/verify/").json()
    vdiff = {x["boundary"]: x for x in d["value_diff"]}
    assert vdiff["base-cambrian"]["delta"] == round(537.0 - 540.0, 6)

    # 4. Bake → one immutable BoundaryRecord for base-cambrian.
    b = _post(c, f"/api/graphs/{fid}/bake/")
    assert b.status_code in (200, 201), b.content
    assert b.json()["baked"] == 1

    # 5. Propose (sandbox → proposed).
    p = _post(c, f"/api/graphs/{fid}/propose/", {"comment": "shift base-cambrian to 537"})
    assert p.status_code == 201, p.content
    proposal = p.json()["proposal"]
    assert proposal["affected"] == ["base-cambrian"] and proposal["state"] == "open"
    pid = proposal["id"]

    from graph.models import Graph
    assert Graph.objects.get(pk=fid).status == "proposed"

    # 6a. The author (personal fork only) cannot ratify their own proposal.
    assert _post(c, f"/api/proposals/{pid}/ratify/").status_code == 403

    # 6b. An ICS chair ratifies → new published baseline, graph → ratified.
    rc = _login("chair")
    ok = _post(rc, f"/api/proposals/{pid}/ratify/", {"comment": "accepted"})
    assert ok.status_code == 200, ok.content
    assert Graph.objects.get(pk=fid).status == "ratified"

    # The ratified edit is now THE baseline value.
    from releases.models import Release
    baselines = Release.objects.filter(is_baseline=True)
    assert baselines.count() == 1                          # old baseline demoted, not duplicated
    rec = baselines.first().records.get(boundary__slug="base-cambrian")
    assert float(rec.value_ma) == 537.0

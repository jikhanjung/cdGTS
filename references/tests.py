import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError
from rest_framework.test import APIClient

from references.models import Reference


def test_link_prefers_doi_then_url(db):
    r = Reference.objects.create(slug="cohen-2013", doi="10.1130/x", title="ICS chart")
    assert r.link == "https://doi.org/10.1130/x"
    r2 = Reference.objects.create(slug="web-only", url="https://stratigraphy.org", title="ICS")
    assert r2.link == "https://stratigraphy.org"
    r3 = Reference.objects.create(slug="bare", title="no link")
    assert r3.link == ""


def test_duplicate_doi_rejected(db):
    Reference.objects.create(slug="a", doi="10.1/z", title="A")
    with pytest.raises(IntegrityError):
        Reference.objects.create(slug="b", doi="10.1/z", title="B")


def test_blank_doi_not_deduplicated(db):
    # 빈 DOI 는 유일성 제약 대상 아님(부분 인덱스) — 여러 개 허용.
    Reference.objects.create(slug="a", title="A")
    Reference.objects.create(slug="b", title="B")            # 예외 없어야


def test_list_public_but_write_needs_auth(db):
    Reference.objects.create(slug="seed", title="Seed", doi="10.1/seed")
    c = APIClient()
    assert c.get("/api/references/").status_code == 200      # 읽기 공개
    denied = c.post("/api/references/", {"slug": "x", "title": "T"}, format="json")
    assert denied.status_code in (401, 403)                  # 쓰기 로그인 필요

    c.force_authenticate(User.objects.create_user("u", password="p"))
    created = c.post("/api/references/",
                     {"slug": "new", "title": "New", "doi": "10.1/new", "authors": "Smith", "year": 2020},
                     format="json")
    assert created.status_code == 201
    assert created.data["link"] == "https://doi.org/10.1/new"
    assert created.data["created_by"] == "u"          # creator recorded


def test_edit_delete_limited_to_creator_or_staff(db):
    creator = User.objects.create_user("creator", password="p")
    other = User.objects.create_user("other", password="p")
    staff = User.objects.create_user("boss", password="p", is_staff=True)
    ref = Reference.objects.create(slug="r", title="R", created_by=creator)

    # other (not creator, not staff) — no edit, no delete
    c = APIClient(); c.force_authenticate(other)
    assert c.patch(f"/api/references/{ref.id}/", {"title": "X"}, format="json").status_code == 403
    assert c.delete(f"/api/references/{ref.id}/").status_code == 403

    # creator — can edit
    c.force_authenticate(creator)
    assert c.patch(f"/api/references/{ref.id}/", {"title": "Edited"}, format="json").status_code == 200

    # staff — can edit anyone's
    c.force_authenticate(staff)
    assert c.patch(f"/api/references/{ref.id}/", {"note": "reviewed"}, format="json").status_code == 200


def test_orphan_reference_editable_only_by_staff(db):
    ref = Reference.objects.create(slug="sys", title="Seed", created_by=None)   # no creator
    c = APIClient(); c.force_authenticate(User.objects.create_user("u", password="p"))
    assert c.patch(f"/api/references/{ref.id}/", {"title": "X"}, format="json").status_code == 403
    c.force_authenticate(User.objects.create_user("boss", password="p", is_staff=True))
    assert c.patch(f"/api/references/{ref.id}/", {"title": "X"}, format="json").status_code == 200


def test_cannot_delete_cited_reference(db):
    from django.core.management import call_command
    from graph.models import Edge, Graph, NodeInstance
    from nodes.models import NodeType
    call_command("loaddata", "02_nodes", verbosity=0)

    creator = User.objects.create_user("creator", password="p")
    ref = Reference.objects.create(slug="cohen-2013", title="ICS chart", created_by=creator)
    g = Graph.objects.create(slug="g", name="G")
    obs = NodeInstance.objects.create(graph=g, key="obs", node_type=NodeType.objects.get(slug="radiometric-uPb"), params={})
    rnode = NodeInstance.objects.create(graph=g, key="ref1", node_type=NodeType.objects.get(slug="reference"),
                                        params={"reference": "cohen-2013"})
    Edge.objects.create(graph=g, source=rnode, source_port="citation", target=obs, target_port="cited", kind="cite")

    c = APIClient(); c.force_authenticate(creator)
    blocked = c.delete(f"/api/references/{ref.id}/")
    assert blocked.status_code == 409                         # cited → deletion refused
    assert "G" in blocked.data["cited_by"]
    assert Reference.objects.filter(id=ref.id).exists()

    # remove the citation → deletable
    rnode.delete()
    assert c.delete(f"/api/references/{ref.id}/").status_code == 204
    assert not Reference.objects.filter(id=ref.id).exists()


# --- Crossref autofill (5b) ---

import io
import json
import urllib.error

from references.crossref import CrossrefError, fetch_crossref, normalize_doi

_CROSSREF_SAMPLE = {
    "message": {
        "DOI": "10.1130/2012.gts",
        "title": ["The ICS International Chronostratigraphic Chart"],
        "container-title": ["Episodes"],
        "author": [
            {"given": "Kim M.", "family": "Cohen"},
            {"given": "Stan C.", "family": "Finney"},
            {"given": "Philip L.", "family": "Gibbard"},
        ],
        "issued": {"date-parts": [[2013, 9]]},
        "type": "journal-article",
    }
}


def _fake_urlopen(payload, code=200):
    def _open(req, timeout=None):
        if code != 200:
            raise urllib.error.HTTPError(req.full_url, code, "err", {}, None)
        return io.BytesIO(json.dumps(payload).encode())   # supports context manager + .read()
    return _open


def test_normalize_doi_strips_url_prefix():
    assert normalize_doi("https://doi.org/10.1/x") == "10.1/x"
    assert normalize_doi("  https://dx.doi.org/10.1/Y ") == "10.1/Y"
    assert normalize_doi("10.1/z") == "10.1/z"


def test_fetch_crossref_maps_fields(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen(_CROSSREF_SAMPLE))
    data = fetch_crossref("https://doi.org/10.1130/2012.gts")
    assert data["title"].startswith("The ICS International")
    assert data["authors"] == "Cohen, K., Finney, S. & Gibbard, P."
    assert data["year"] == 2013
    assert data["container"] == "Episodes"
    assert data["kind"] == "article"
    assert data["doi"] == "10.1130/2012.gts"
    assert data["suggested_slug"] == "cohen-2013"


def test_fetch_crossref_404(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen(None, code=404))
    with pytest.raises(CrossrefError) as ei:
        fetch_crossref("10.1/missing")
    assert ei.value.status == 404


def test_fetch_crossref_blank_doi():
    with pytest.raises(CrossrefError) as ei:
        fetch_crossref("   ")
    assert ei.value.status == 400


def test_crossref_action_requires_login_then_returns_data(db, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen(_CROSSREF_SAMPLE))
    c = APIClient()
    assert c.get("/api/references/crossref/?doi=10.1130/2012.gts").status_code == 403   # open proxy guard
    c.force_authenticate(User.objects.create_user("u", password="p"))
    ok = c.get("/api/references/crossref/?doi=10.1130/2012.gts")
    assert ok.status_code == 200
    assert ok.data["year"] == 2013 and ok.data["suggested_slug"] == "cohen-2013"

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

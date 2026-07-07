import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from chrono.models import Authority
from accounts.models import Membership

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user("ann", password="pw12345")


# --- signal: personal fork authority on user creation ---

def test_new_user_gets_personal_fork_authority(user):
    a = Authority.objects.get(slug=f"user-{user.pk}")
    assert a.kind == Authority.Kind.FORK
    m = Membership.objects.get(user=user, authority=a)
    assert m.role == Membership.Role.OWNER


# --- auth endpoints ---

def test_whoami_anonymous(db):
    r = APIClient().get("/api/auth/whoami/")
    assert r.status_code == 200 and r.json() == {"authenticated": False}


def test_login_logout_flow(user):
    api = APIClient()
    bad = api.post("/api/auth/login/", {"username": "ann", "password": "nope"}, format="json")
    assert bad.status_code == 401
    ok = api.post("/api/auth/login/", {"username": "ann", "password": "pw12345"}, format="json")
    assert ok.status_code == 200
    body = ok.json()
    assert body["authenticated"] and body["username"] == "ann"
    assert any(m["role"] == "owner" and m["kind"] == "fork" for m in body["memberships"])

    who = api.get("/api/auth/whoami/")
    assert who.json()["authenticated"] is True

    api.post("/api/auth/logout/")
    assert api.get("/api/auth/whoami/").json() == {"authenticated": False}


# --- default permission: read public / write authenticated (for views without explicit AllowAny) ---

def test_read_is_public(db):
    assert APIClient().get("/api/node-types/").status_code == 200

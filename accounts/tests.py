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


# --- staff user management ---

@pytest.fixture
def staff(db):
    return User.objects.create_user("root", password="pw12345", is_staff=True)


def test_user_admin_requires_staff(user, staff):
    assert APIClient().get("/api/users/").status_code in (401, 403)          # anonymous
    non = APIClient(); non.force_authenticate(user=user)
    assert non.get("/api/users/").status_code == 403                          # non-staff
    adm = APIClient(); adm.force_authenticate(user=staff)
    assert adm.get("/api/users/").status_code == 200                          # staff


def test_user_admin_create_edit_password_membership(staff):
    api = APIClient(); api.force_authenticate(user=staff)
    # create
    r = api.post("/api/users/", {"username": "bob", "password": "pw12345",
                                 "email": "bob@x.io", "is_staff": False}, format="json")
    assert r.status_code == 201
    uid = r.json()["id"]
    # edit profile fields
    r = api.patch(f"/api/users/{uid}/", {"first_name": "Bob", "is_staff": True}, format="json")
    assert r.status_code == 200 and r.json()["first_name"] == "Bob" and r.json()["is_staff"] is True
    # reset password → new one works
    assert api.post(f"/api/users/{uid}/set_password/", {"password": "newpw123"}, format="json").status_code == 200
    fresh = APIClient()
    assert fresh.post("/api/auth/login/", {"username": "bob", "password": "newpw123"}, format="json").status_code == 200
    # membership → grants ratify
    ics = Authority.objects.create(slug="ics-gov", name="ICS", kind=Authority.Kind.ICS)
    r = api.post(f"/api/users/{uid}/add_membership/", {"authority": "ics-gov", "role": "chair"}, format="json")
    assert r.status_code == 200 and r.json()["can_ratify"] is True
    mid = next(m["id"] for m in r.json()["memberships"] if m["authority"] == "ics-gov")
    r = api.post(f"/api/users/{uid}/remove_membership/", {"membership_id": mid}, format="json")
    assert r.json()["can_ratify"] is False


def test_update_own_profile(user):
    api = APIClient(); api.force_authenticate(user=user)
    r = api.patch("/api/auth/me/", {"first_name": "Ann", "email": "ann@x.io"}, format="json")
    assert r.status_code == 200
    user.refresh_from_db()
    assert user.first_name == "Ann" and user.email == "ann@x.io"

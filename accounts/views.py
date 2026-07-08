"""Session auth endpoints for the SPA (P05.1) + staff user management. whoami primes the CSRF cookie."""
import json

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from rest_framework import permissions, response, viewsets
from rest_framework.decorators import action, api_view, permission_classes

from chrono.models import Authority

from .models import Membership
from .serializers import UserCreateSerializer, UserSerializer


def user_payload(user):
    from .permissions import can_ratify
    return {
        "authenticated": True,
        "id": user.id,
        "username": user.get_username(),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_staff": user.is_staff,
        "can_ratify": can_ratify(user),
        "memberships": [
            {
                "authority": m.authority.slug,
                "authority_name": m.authority.name,
                "kind": m.authority.kind,
                "role": m.role,
            }
            for m in user.memberships.select_related("authority").all()
        ],
    }


@ensure_csrf_cookie
def whoami(request):
    if request.user.is_authenticated:
        return JsonResponse(user_payload(request.user))
    return JsonResponse({"authenticated": False})


@require_POST
def login_view(request):
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)
    user = authenticate(request, username=data.get("username"), password=data.get("password"))
    if user is None:
        return JsonResponse({"detail": "Invalid username or password."}, status=401)
    login(request, user)
    return JsonResponse(user_payload(user))


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"authenticated": False})


@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def update_me(request):
    """Edit your own profile — first/last name + email."""
    u = request.user
    for f in ("first_name", "last_name", "email"):
        if f in request.data:
            setattr(u, f, (request.data[f] or "").strip())
    u.save(update_fields=["first_name", "last_name", "email"])
    return response.Response(user_payload(u))


class UserViewSet(viewsets.ModelViewSet):
    """Staff-only user administration (list/create/edit + password + memberships)."""
    permission_classes = [permissions.IsAdminUser]
    queryset = get_user_model().objects.prefetch_related("memberships__authority").order_by("username")

    def get_serializer_class(self):
        return UserCreateSerializer if self.action == "create" else UserSerializer

    @action(detail=False, methods=["get"])
    def authorities(self, request):
        """Governance authorities (ICS / subcommission) — the ones a membership grants ratify through."""
        qs = Authority.objects.filter(kind__in=[Authority.Kind.ICS, Authority.Kind.SUBCOMMISSION]).order_by("name")
        return response.Response([{"slug": a.slug, "name": a.name, "kind": a.kind} for a in qs])

    @action(detail=True, methods=["post"])
    def set_password(self, request, pk=None):
        user = self.get_object()
        pw = request.data.get("password") or ""
        if len(pw) < 6:
            return response.Response({"detail": "Password must be at least 6 characters."}, status=400)
        user.set_password(pw)
        user.save(update_fields=["password"])
        return response.Response({"status": "ok"})

    @action(detail=True, methods=["post"])
    def add_membership(self, request, pk=None):
        user = self.get_object()
        authority = get_object_or_404(Authority, slug=request.data.get("authority"))
        role = request.data.get("role") or Membership.Role.MEMBER
        Membership.objects.update_or_create(user=user, authority=authority, defaults={"role": role})
        return response.Response(UserSerializer(self.get_queryset().get(pk=user.pk)).data)

    @action(detail=True, methods=["post"])
    def remove_membership(self, request, pk=None):
        user = self.get_object()
        Membership.objects.filter(user=user, id=request.data.get("membership_id")).delete()
        return response.Response(UserSerializer(self.get_queryset().get(pk=user.pk)).data)

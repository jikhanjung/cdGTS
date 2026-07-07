"""Session auth endpoints for the SPA (P05.1). whoami primes the CSRF cookie the SPA sends back on writes."""
import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST


def user_payload(user):
    return {
        "authenticated": True,
        "id": user.id,
        "username": user.get_username(),
        "is_staff": user.is_staff,
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

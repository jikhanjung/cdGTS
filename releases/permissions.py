"""Release visibility (P05.2/.5). Single source of truth so aux endpoints can't leak private sandboxes by pk."""
from django.db.models import Q

from .models import Release


def visible_releases(user):
    """Vault-visible releases: kept artifacts, minus other users' private sandboxes."""
    qs = Release.objects.exclude(kind=Release.Kind.TRANSIENT)
    if getattr(user, "is_authenticated", False):
        return qs.exclude(Q(kind=Release.Kind.SANDBOX) & ~Q(owner=user))
    return qs.exclude(kind=Release.Kind.SANDBOX)


def can_write_release(user, release):
    """Who may mutate a release (narrate persist, lazy re-bake): its owner or staff."""
    return bool(getattr(user, "is_authenticated", False) and (user.is_staff or release.owner_id == user.id))

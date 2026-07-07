from django.db.models import Q
from rest_framework import permissions

from .models import Graph

PUBLIC_STATUSES = {Graph.Status.PROPOSED, Graph.Status.RATIFIED}


def graph_is_public(graph):
    """Readable by anyone: proposed/ratified graphs, and system/demo graphs (owner is null)."""
    return graph.owner_id is None or graph.status in PUBLIC_STATUSES


def visible_graphs(user):
    """
    The graphs a user may read: public (proposed/ratified) + system (owner=null) + their own.
    Single source of truth — the ViewSet AND every auxiliary endpoint (bake/verify/icc-chart) fetch through this
    so private sandboxes never leak by direct pk.
    """
    public = Q(status__in=list(PUBLIC_STATUSES)) | Q(owner__isnull=True)
    if getattr(user, "is_authenticated", False):
        return Graph.objects.filter(public | Q(owner=user))
    return Graph.objects.filter(public)


class GraphAccessPermission(permissions.BasePermission):
    """
    Read = public graphs + your own (queryset also filters, so hidden graphs 404 on list).
    Write = authenticated owner only (staff may edit system/demo graphs with owner=null).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return graph_is_public(obj) or obj.owner_id == request.user.id
        # fork clones a *readable* graph into your own sandbox — it doesn't mutate the source.
        if getattr(view, "action", None) == "fork":
            return bool(request.user and request.user.is_authenticated)
        if request.user.is_staff:
            return True
        return obj.owner_id is not None and obj.owner_id == request.user.id

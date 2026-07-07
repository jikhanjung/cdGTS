from rest_framework import permissions

from .models import Graph

PUBLIC_STATUSES = {Graph.Status.PROPOSED, Graph.Status.RATIFIED}


def graph_is_public(graph):
    """Readable by anyone: proposed/ratified graphs, and system/demo graphs (owner is null)."""
    return graph.owner_id is None or graph.status in PUBLIC_STATUSES


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

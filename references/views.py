from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from .crossref import CrossrefError, fetch_crossref
from .models import Reference
from .permissions import ReferenceAccessPermission
from .serializers import ReferenceSerializer


class Conflict(APIException):
    status_code = 409
    default_detail = "Conflict."
    default_code = "conflict"


class ReferenceViewSet(viewsets.ModelViewSet):
    """
    Bibliographic registry CRUD (global shared library).
      GET/POST /api/references/          — list · create (create needs login)
      GET/PATCH/DELETE /api/references/{id}/   — edit/delete: staff or creator only

    Deletion is refused (409) while any graph's `reference` node still cites the entry.
    """
    queryset = Reference.objects.all()
    serializer_class = ReferenceSerializer
    permission_classes = [ReferenceAccessPermission]

    @action(detail=False, methods=["get"])
    def crossref(self, request):
        """
        GET /api/references/crossref/?doi=10.xxxx/… — fetch bibliographic metadata from Crossref to
        autofill a new reference. Read-only proxy (no DB write). Login required (same bar as create),
        so it isn't an open outbound proxy.
        """
        if not request.user.is_authenticated:
            return Response({"detail": "Login required."}, status=403)
        try:
            data = fetch_crossref(request.query_params.get("doi"))
        except CrossrefError as e:
            return Response({"detail": str(e)}, status=e.status)
        return Response(data)

    def perform_create(self, serializer):
        u = self.request.user
        serializer.save(created_by=u if u.is_authenticated else None)

    def perform_destroy(self, instance):
        from graph.models import NodeInstance

        citing = NodeInstance.objects.filter(
            node_type__slug="reference", params__reference=instance.slug,
        ).select_related("graph")
        graphs = sorted({n.graph.name for n in citing})
        if graphs:
            raise Conflict(detail={
                "detail": "Reference is cited by a graph — remove those citations first.",
                "cited_by": graphs,
            })
        instance.delete()

from rest_framework import viewsets
from rest_framework.exceptions import APIException

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

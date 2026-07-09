from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .permissions import GraphAccessPermission, visible_graphs
from .serializers import GraphSerializer
from .services import fork_graph


class GraphViewSet(viewsets.ModelViewSet):
    """
    그래프 CRUD (P05.2 소유권/가시성).
      GET/PUT /api/graphs/{id}/ — React Flow {nodes, edges, viewport} 왕복

    평가는 engine 앱이 소유: POST /api/graphs/{id}/evaluate/ (engine.views.EvaluateView).
    가시성: 공개(proposed/ratified) + 시스템(owner=null) + 내 그래프. 쓰기: 인증된 owner(또는 staff).
    """
    serializer_class = GraphSerializer
    permission_classes = [GraphAccessPermission]

    def get_queryset(self):
        return visible_graphs(self.request.user).prefetch_related("nodes__node_type", "edges", "gateways")

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(owner=user if user.is_authenticated else None)

    @action(detail=True, methods=["post"])
    def fork(self, request, pk=None):
        """Deep-clone a readable graph into a new sandbox the caller owns (P05.3)."""
        if not request.user.is_authenticated:
            return Response({"detail": "Sign in to fork."}, status=401)
        source = self.get_object()          # get_queryset enforces "can only fork what you can see"
        fork = fork_graph(source, request.user, name=request.data.get("name"))
        return Response(self.get_serializer(fork).data, status=201)

    @action(detail=True, methods=["get"])
    def references(self, request, pk=None):
        """
        This graph's bibliography — Reference entries cited by its `reference` nodes.
        `citations` maps each reference node to the data/model nodes it sources (cite edges).
        Seam for bake→bibliography: collect a result's sources by walking cite edges.
        """
        from references.models import Reference
        from references.serializers import ReferenceSerializer

        from .services import graph_bibliography

        graph = self.get_object()
        ref_nodes = [n for n in graph.nodes.select_related("node_type") if n.node_type.slug == "reference"]
        cites = {}
        for e in graph.edges.filter(kind="cite").select_related("source", "target"):
            cites.setdefault(e.source.key, []).append(e.target.key)
        biblio = graph_bibliography(graph)
        refs = Reference.objects.filter(slug__in=biblio["all"])
        return Response({
            "bibliography": ReferenceSerializer(refs, many=True).data,
            "by_boundary": biblio["by_boundary"],       # contributing refs per gateway boundary (bake→bibliography)
            "citations": [
                {"node": n.key, "reference": (n.params or {}).get("reference"), "cites": cites.get(n.key, [])}
                for n in ref_nodes
            ],
        })

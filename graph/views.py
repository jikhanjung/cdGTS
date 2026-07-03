from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Graph
from .serializers import GraphSerializer


class GraphViewSet(viewsets.ModelViewSet):
    """
    그래프 CRUD + 평가 트리거.
      GET/PUT /api/graphs/{id}/       — React Flow {nodes, edges, viewport} 왕복
      POST    /api/graphs/{id}/evaluate/ — 평가(Phase 5 engine 스텁)

    권한: dev 단계 AllowAny (착수 검증용). 인증·소유권은 후속.
    """
    queryset = Graph.objects.prefetch_related("nodes__node_type", "edges", "gateways")
    serializer_class = GraphSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=["post"])
    def evaluate(self, request, pk=None):
        graph = self.get_object()
        return Response({
            "status": "not-implemented",
            "detail": "평가 엔진은 Phase 5(engine) 에서 구현됩니다.",
            "graph": graph.slug,
            "node_count": graph.nodes.count(),
            "edge_count": graph.edges.count(),
        })

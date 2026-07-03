from rest_framework import permissions, viewsets

from .models import Graph
from .serializers import GraphSerializer


class GraphViewSet(viewsets.ModelViewSet):
    """
    그래프 CRUD.
      GET/PUT /api/graphs/{id}/ — React Flow {nodes, edges, viewport} 왕복

    평가는 engine 앱이 소유: POST /api/graphs/{id}/evaluate/ (engine.views.EvaluateView).
    권한: dev 단계 AllowAny (착수 검증용). 인증·소유권은 후속.
    """
    queryset = Graph.objects.prefetch_related("nodes__node_type", "edges", "gateways")
    serializer_class = GraphSerializer
    permission_classes = [permissions.AllowAny]

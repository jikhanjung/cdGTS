from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Graph
from .permissions import GraphAccessPermission
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
        qs = Graph.objects.prefetch_related("nodes__node_type", "edges", "gateways")
        user = self.request.user
        public = Q(status__in=["proposed", "ratified"]) | Q(owner__isnull=True)
        if user.is_authenticated:
            return qs.filter(public | Q(owner=user))
        return qs.filter(public)

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(owner=user if user.is_authenticated else None)

    @action(detail=True, methods=["post"])
    def fork(self, request, pk=None):
        """Deep-clone a readable graph into a new sandbox the caller owns (P05.3)."""
        if not request.user.is_authenticated:
            return Response({"detail": "Sign in to fork."}, status=401)
        source = self.get_object()          # get_queryset enforces "can only fork what you can see"
        fork = fork_graph(source, request.user)
        return Response(self.get_serializer(fork).data, status=201)

from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from graph.models import Graph

from .evaluate import evaluate_graph
from .serializers import EvalRunSerializer


class EvaluateView(APIView):
    """
    POST /api/graphs/{id}/evaluate/ — 그래프를 평가하고 최신 run(+결과·인증서) 반환.
    GET  /api/graphs/{id}/evaluate/ — 마지막 run(있으면) 반환.
    engine 이 소유(graph 는 engine 을 모른다).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        graph = get_object_or_404(Graph, pk=pk)
        run = evaluate_graph(graph)
        return Response(EvalRunSerializer(run).data)

    def get(self, request, pk):
        graph = get_object_or_404(Graph, pk=pk)
        run = graph.eval_runs.first()
        if run is None:
            return Response({"detail": "아직 평가된 적 없음."}, status=404)
        return Response(EvalRunSerializer(run).data)

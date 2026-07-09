from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from graph.models import Graph

from .evaluate import evaluate_graph, needs_async
from .models import EvalJob
from .serializers import EvalJobSerializer, EvalRunSerializer


class EvaluateView(APIView):
    """
    POST /api/graphs/{id}/evaluate/ — 그래프를 평가.
      해석적 그래프 → 동기 평가, 최신 run(+결과·인증서) 반환(200, 종전과 동일).
      joint/순환 클러스터 그래프(needs_async) → EvalJob 을 큐잉하고 202 + 잡 상태 반환(워커가 처리).
    GET  /api/graphs/{id}/evaluate/ — 마지막 run(있으면) 반환.
    engine 이 소유(graph 는 engine 을 모른다).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        graph = get_object_or_404(Graph, pk=pk)
        if needs_async(graph):
            user = request.user if request.user.is_authenticated else None
            job = EvalJob.objects.create(graph=graph, requested_by=user)
            return Response(EvalJobSerializer(job).data, status=202)
        run = evaluate_graph(graph)
        return Response(EvalRunSerializer(run).data)

    def get(self, request, pk):
        graph = get_object_or_404(Graph, pk=pk)
        run = graph.eval_runs.first()
        if run is None:
            return Response({"detail": "아직 평가된 적 없음."}, status=404)
        return Response(EvalRunSerializer(run).data)


class EvalJobView(APIView):
    """GET /api/eval-jobs/{id}/ — 비동기 잡 상태 폴링. done 이면 run 임베드."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        job = get_object_or_404(EvalJob, pk=pk)
        return Response(EvalJobSerializer(job).data)

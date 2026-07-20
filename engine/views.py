from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from graph.permissions import visible_graphs

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
        # visible_graphs = 단일 진리원(graph ViewSet·bake/verify/icc 와 동일) — 비공개 sandbox 는 pk 로도 404.
        graph = get_object_or_404(visible_graphs(request.user), pk=pk)
        if needs_async(graph):
            user = request.user if request.user.is_authenticated else None
            job = EvalJob.objects.create(graph=graph, requested_by=user)
            return Response(EvalJobSerializer(job).data, status=202)
        run = evaluate_graph(graph)
        return Response(EvalRunSerializer(run).data)

    def get(self, request, pk):
        graph = get_object_or_404(visible_graphs(request.user), pk=pk)
        run = graph.eval_runs.first()
        if run is None:
            return Response({"detail": "아직 평가된 적 없음."}, status=404)
        return Response(EvalRunSerializer(run).data)


class EvalJobView(APIView):
    """GET /api/eval-jobs/{id}/ — 비동기 잡 상태 폴링. done 이면 run 임베드."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        # 잡의 그래프가 가시 범위 안일 때만 — 비공개 그래프의 잡은 pk 로도 404.
        job = get_object_or_404(EvalJob.objects.filter(graph__in=visible_graphs(request.user)), pk=pk)
        return Response(EvalJobSerializer(job).data)

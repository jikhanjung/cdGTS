from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from graph.models import Graph

from .models import Release
from .serializers import ReleaseSerializer
from .services import bake_graph, bake_release, diff_releases


class ReleaseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    릴리스 조회 + bake + diff.
      GET  /api/releases/                — 목록
      GET  /api/releases/{id}/           — 레코드 포함 상세
      POST /api/releases/{id}/bake/      — selection → BoundaryRecord 스냅샷
      GET  /api/releases/diff/?a=&b=     — 두 릴리스 값/토폴로지 diff
    """
    queryset = Release.objects.prefetch_related("records__boundary", "records__candidate", "clamps")
    serializer_class = ReleaseSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=["post"])
    def bake(self, request, pk=None):
        release = self.get_object()
        n = bake_release(release)
        release = self.get_queryset().get(pk=release.pk)
        return Response({"baked": n, "release": ReleaseSerializer(release).data})

    @action(detail=False, methods=["get"])
    def diff(self, request):
        a = get_object_or_404(Release, pk=request.query_params.get("a"))
        b = get_object_or_404(Release, pk=request.query_params.get("b"))
        return Response(diff_releases(a, b))


class GraphBakeView(APIView):
    """
    POST /api/graphs/{id}/bake/ — 그래프를 평가해 게이트웨이 출력을 ICC 테이블(BoundaryRecord)로 얼린다.
    그래프당 릴리스 `graph:<slug>` 하나에 스냅샷. 반환: {baked, release(records 포함)}.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        graph = get_object_or_404(Graph, pk=pk)
        release, n = bake_graph(graph)
        release = (Release.objects
                   .prefetch_related("records__boundary", "records__candidate")
                   .get(pk=release.pk))
        return Response({"baked": n, "release": ReleaseSerializer(release).data})


class IccChartView(APIView):
    """
    GET /api/graphs/{id}/icc-chart/ — 그래프 산출물을 chrono 계층(Eon/Era/Period)과 join 해
    ICC식 중첩 컬럼 차트 데이터로. 각 rank 안에서 base 연대로 타일링해 [top(younger), bottom(older)] 밴드 생성.
    """
    permission_classes = [permissions.AllowAny]

    GEO = {1: "Eon", 2: "Era", 3: "Period"}

    def get(self, request, pk):
        from engine.evaluate import evaluate_graph
        from chrono.models import Unit
        graph = get_object_or_404(Graph, pk=pk)

        run = graph.eval_runs.first() or evaluate_graph(graph)
        results = {r.node_key: (r.distribution or {}) for r in run.results.all()}

        # 게이트웨이 경계 → 값. 경계 slug 'base-<unit>' → 유닛 slug.
        unit_base = {}
        for gw in graph.gateways.select_related("node", "boundary"):
            if gw.boundary is None:
                continue
            v = results.get(gw.node.key, {}).get("value_ma")
            if v is not None and gw.boundary.slug.startswith("base-"):
                unit_base[gw.boundary.slug[len("base-"):]] = float(v)

        units = {u.slug: u for u in Unit.objects.filter(slug__in=unit_base.keys())}
        max_ma = max(unit_base.values(), default=0.0)
        levels = []
        for rank_n in (1, 2, 3):
            us = sorted(
                ((s, units[s].name, base) for s, base in unit_base.items()
                 if s in units and units[s].rank == rank_n),
                key=lambda z: z[2],
            )  # base 오름차순 = 젊은 것부터
            bands, prev = [], 0.0
            for s, name, base in us:
                bands.append({"slug": s, "name": name, "top": round(prev, 4), "bottom": round(base, 4),
                              "color": units[s].color or None})
                prev = base
            levels.append({"rank": self.GEO[rank_n], "rank_n": rank_n, "bands": bands})

        return Response({"graph": graph.slug, "max_ma": round(max_ma, 4), "levels": levels})

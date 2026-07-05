from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from graph.models import Graph

from .models import Release
from .serializers import ReleaseSerializer
from .services import bake_graph, bake_release, diff_releases, narrate_release


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


class GraphVerifyView(APIView):
    """
    POST /api/graphs/{id}/verify/ — **Science CI 루프**. 그래프를 재-bake 하고 공표 기준(is_baseline)
    릴리스와 diff. 반환: {from(공표), to(그래프), value_diff, topology_diff, summary}.
    value_diff.delta = 그래프값 − 공표값 (내 편집이 경계를 얼마나 이동시켰나).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        graph = get_object_or_404(Graph, pk=pk)
        baseline = Release.objects.filter(is_baseline=True).order_by("version").first()
        if baseline is None:
            return Response({"detail": "공표 기준(is_baseline) 릴리스가 없습니다."}, status=400)
        release, n = bake_graph(graph)
        d = diff_releases(baseline, release)          # from=공표 → to=그래프
        deltas = [x["delta"] for x in d["value_diff"] if x["delta"] is not None]
        td = d["topology_diff"]
        d["summary"] = {
            "baked": n,
            "moved": len(d["value_diff"]),
            "max_abs_delta": round(max((abs(x) for x in deltas), default=0.0), 4),
            "added": sum(1 for t in td if t["op"] == "added"),
            "removed": sum(1 for t in td if t["op"] == "removed"),
            "retyped": sum(1 for t in td if t["op"] == "retype"),
        }
        return Response(d)


_GEO = {1: "Eon", 2: "Era", 3: "Period", 4: "Subperiod", 5: "Epoch", 6: "Age"}


def build_icc_levels(unit_base):
    """{unit_slug: base_ma} → ICC 중첩 컬럼. rank(Eon~Age) 별 밴드 = [bottom(older)=자기 base,
    top(younger)= **rank 이하(같거나 굵은) 중 자기보다 젊은 base 의 최대**, 없으면 0].
    coarser 경계(예: Permian base)가 sparse rank(Subperiod) 밴드를 제 구간에서 닫아준다
    — Pennsylvanian 은 Carboniferous 의 젊은 끝(=Permian base)에서 멈춘다. 부모 FK 에 의존하지 않는다
    (시드의 period→era 링크가 불완전해도 안전). gapless rank 는 종전 타일링과 동일 결과."""
    from chrono.models import Unit
    units = {u.slug: u for u in Unit.objects.filter(slug__in=unit_base.keys())}
    items = [(s, units[s].name, base, units[s].rank, units[s].color)
             for s, base in unit_base.items() if s in units]
    max_ma = max((it[2] for it in items), default=0.0)
    # coincident 경계(같은 GSSP 를 여러 rank/노드가 산출) 허용오차. 같은 지점이 modeled vs published
    # 로 미세하게(예: 251.902 vs 251.902182) 달라도 younger cap 으로 오인해 sliver 밴드가 생기지 않도록.
    # 0.001 Ma(1000년)는 ICC 실제 최소 경계 간격(홀로세 세분 ~0.0035 Ma)보다 작아 안전.
    EPS = 1e-3
    levels = []
    for rank_n in (1, 2, 3, 4, 5, 6):
        # 자기보다 굵거나 같은 rank 의 base 들(정렬) — top(younger cap) 후보
        caps = sorted(b for _, _, b, rk, _ in items if rk <= rank_n)
        us = sorted((it for it in items if it[3] == rank_n), key=lambda z: z[2])
        bands = []
        for s, name, b, rk, color in us:
            younger = [c for c in caps if c < b - EPS]
            bands.append({"slug": s, "name": name, "top": round(max(younger) if younger else 0.0, 4),
                          "bottom": round(b, 4), "color": color or None})
        if bands:
            levels.append({"rank": _GEO[rank_n], "rank_n": rank_n, "bands": bands})
    return {"max_ma": round(max_ma, 4), "levels": levels}


class IccChartView(APIView):
    """
    GET /api/graphs/{id}/icc-chart/ — 그래프 산출물(게이트웨이=period+)을 chrono 계층과 join 한 ICC 차트.
    네트웍이 period+ 만이라 Eon/Era/Period 3 컬럼.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        from engine.evaluate import evaluate_graph
        graph = get_object_or_404(Graph, pk=pk)
        run = graph.eval_runs.first() or evaluate_graph(graph)
        results = {r.node_key: (r.distribution or {}) for r in run.results.all()}

        unit_base = {}
        for gw in graph.gateways.select_related("node", "boundary"):
            if gw.boundary is None:
                continue
            v = results.get(gw.node.key, {}).get("value_ma")
            if v is not None and gw.boundary.slug.startswith("base-"):
                unit_base[gw.boundary.slug[len("base-"):]] = float(v)

        return Response({"graph": graph.slug, **build_icc_levels(unit_base)})


class ReleaseIccChartView(APIView):
    """
    GET /api/releases/{id}/icc-chart/ — 공표 릴리스(BoundaryRecord)를 전 rank(Eon~Age)로.
    공표 ICC(ICS-2024/12)는 stage 까지 있어 5 컬럼. 미-bake 릴리스는 지연 bake.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        release = get_object_or_404(Release, pk=pk)
        if not release.records.exists():
            bake_release(release)
        unit_base = {}
        for rec in release.records.select_related("boundary"):
            if rec.value_ma is None:
                continue
            bslug = rec.boundary.slug
            if bslug.startswith("base-"):
                unit_base[bslug[len("base-"):]] = float(rec.value_ma)
        return Response({"release": release.version, **build_icc_levels(unit_base)})


class ReleaseNarrateView(APIView):
    """
    POST /api/releases/{id}/narrate/ — bake 의 짝. 릴리스를 rank 별 서술 문서로 렌더하고
    각 레코드 narrative 를 저장. 반환: {release, sections}.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        release = get_object_or_404(Release, pk=pk)
        sections = narrate_release(release)
        return Response({"release": release.version, "sections": sections})

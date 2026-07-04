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

from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Release
from .serializers import ReleaseSerializer
from .services import bake_release, diff_releases


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

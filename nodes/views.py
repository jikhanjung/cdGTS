from rest_framework import permissions, viewsets

from .models import NodeType
from .serializers import NodeTypeSerializer


class NodeTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """노드 타입 카탈로그 (읽기 전용) — 프론트 팔레트 소스."""
    queryset = NodeType.objects.prefetch_related("ports")
    serializer_class = NodeTypeSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

"""
graph — 실제 DAG (네트워크). 학자가 캔버스에서 만든 한 개의 네트워크.

drag&drop 에디터(React Flow)의 백엔드 상태. 노드 *타입*은 nodes 앱, 평가는 engine 앱.
게이트웨이/네트워크 2계층: Gateway = 비준·인용 대상 계약, NodeInstance/Edge = 자유 churn.

설계: docs/app-architecture.md §2.3 / DAG 불변식: graph/dag.py
"""
from django.conf import settings
from django.db import models

from nodes.models import NodeType


class GraphManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class NodeInstanceManager(models.Manager):
    def get_by_natural_key(self, graph_slug, key):
        return self.get(graph__slug=graph_slug, key=key)


class GatewayManager(models.Manager):
    def get_by_natural_key(self, graph_slug, slug):
        return self.get(graph__slug=graph_slug, slug=slug)


class EdgeManager(models.Manager):
    def get_by_natural_key(self, graph_slug, source_key, source_port, target_key, target_port):
        return self.get(
            graph__slug=graph_slug,
            source__key=source_key, source_port=source_port,
            target__key=target_key, target_port=target_port,
        )


class Graph(models.Model):
    """네트워크 컨테이너 (브랜치/샌드박스 단위). viewport = React Flow 팬/줌 상태."""
    class Status(models.TextChoices):
        SANDBOX = "sandbox", "Sandbox"
        PROPOSED = "proposed", "Proposed"
        RATIFIED = "ratified", "Ratified"
        DEPRECATED = "deprecated", "Deprecated"

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="graphs",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SANDBOX)
    viewport = models.JSONField(default=dict, blank=True, help_text="React Flow {x, y, zoom}")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GraphManager()

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.slug

    def natural_key(self):
        return (self.slug,)


class NodeGroup(models.Model):
    """지역/경계별 서브그래프 (node-graph: node group = locality). 접으면 게이트웨이처럼."""
    graph = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name="groups")
    key = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    collapsed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["graph", "key"], name="uniq_group_key_per_graph")
        ]

    def __str__(self):
        return f"{self.graph.slug}/{self.key}"


class NodeInstance(models.Model):
    """캔버스에 놓인 노드. key = React Flow 노드 id(클라이언트 제공, 그래프 내 유일)."""
    graph = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name="nodes")
    key = models.CharField(max_length=100, help_text="React Flow 노드 id (그래프 내 유일)")
    node_type = models.ForeignKey(NodeType, on_delete=models.PROTECT, related_name="instances")
    label = models.CharField(max_length=200, blank=True)
    params = models.JSONField(default=dict, blank=True)
    x = models.FloatField(default=0)
    y = models.FloatField(default=0)
    group = models.ForeignKey(
        NodeGroup, null=True, blank=True, on_delete=models.SET_NULL, related_name="members",
    )

    objects = NodeInstanceManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["graph", "key"], name="uniq_node_key_per_graph")
        ]

    def __str__(self):
        return f"{self.graph.slug}/{self.key}:{self.node_type.slug}"

    def natural_key(self):
        return (self.graph.slug, self.key)

    natural_key.dependencies = ["graph.graph", "nodes.nodetype"]

    @property
    def is_cycle_breaker(self):
        """사이클을 접는/끊는 노드 — joint-inference 또는 clamp (cycles §)."""
        return self.node_type.category == NodeType.Category.CLAMP or self.node_type.slug == "joint-inference"


class Edge(models.Model):
    """데이터 흐름. kind: 일반 data / provenance(co-location·calibration-transfer)로 게이트가 사이클 탐지."""
    class Kind(models.TextChoices):
        DATA = "data", "data"
        CO_LOCATION = "co-location", "co-location"
        CALIBRATION_TRANSFER = "calibration-transfer", "calibration-transfer"

    graph = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name="edges")
    source = models.ForeignKey(NodeInstance, on_delete=models.CASCADE, related_name="out_edges")
    source_port = models.CharField(max_length=100)
    target = models.ForeignKey(NodeInstance, on_delete=models.CASCADE, related_name="in_edges")
    target_port = models.CharField(max_length=100)
    kind = models.CharField(max_length=24, choices=Kind.choices, default=Kind.DATA)

    objects = EdgeManager()

    def __str__(self):
        return f"{self.source.key}.{self.source_port} → {self.target.key}.{self.target_port}"

    def natural_key(self):
        return (self.graph.slug, self.source.key, self.source_port, self.target.key, self.target_port)

    natural_key.dependencies = ["graph.graph", "graph.nodeinstance"]


class Gateway(models.Model):
    """
    비준·인용·버전의 단위(계약). 노드그룹/노드의 출력을 고정 타입으로 노출.
    스키마 BoundaryGateway 가 참조하는 대상. 경계 추정 게이트웨이는 chrono.Boundary 를 가리킨다.
    """
    graph = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name="gateways")
    slug = models.SlugField()
    name = models.CharField(max_length=200)
    node = models.ForeignKey(
        NodeInstance, on_delete=models.CASCADE, related_name="gateways",
        help_text="출력을 노출하는 노드",
    )
    output_port = models.CharField(max_length=100, default="out")
    boundary = models.ForeignKey(
        "chrono.Boundary", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="gateways", help_text="이 게이트웨이가 추정하는 경계(있으면)",
    )

    objects = GatewayManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["graph", "slug"], name="uniq_gateway_slug_per_graph")
        ]

    def __str__(self):
        return f"{self.graph.slug}::{self.slug}"

    def natural_key(self):
        return (self.graph.slug, self.slug)

    natural_key.dependencies = ["graph.graph", "graph.nodeinstance", "chrono.boundary"]

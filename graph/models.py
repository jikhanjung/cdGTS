"""
graph — the actual DAG (network). A single network a scholar builds on the canvas.

Backend state of the drag&drop editor (React Flow). Node *types* live in the nodes app, evaluation in the engine app.
Two layers, gateway/network: Gateway = the contract that gets ratified/cited, NodeInstance/Edge = free churn.

Design: docs/app-architecture.md §2.3 / DAG invariants: graph/dag.py
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


class NodeGroupManager(models.Manager):
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
    """Network container (branch/sandbox unit). viewport = React Flow pan/zoom state."""
    class Status(models.TextChoices):
        SANDBOX = "sandbox", "Sandbox"
        PROPOSED = "proposed", "Proposed"
        RATIFIED = "ratified", "Ratified"
        DEPRECATED = "deprecated", "Deprecated"

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="", help_text="Free-text notes about this graph/branch.")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="graphs",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SANDBOX)
    forked_from = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="forks",
        help_text="The graph this was forked from (lineage).",
    )
    viewport = models.JSONField(default=dict, blank=True, help_text="React Flow {x, y, zoom}")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GraphManager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.slug

    def natural_key(self):
        return (self.slug,)


class NodeGroup(models.Model):
    """
    Per-locality/boundary subgraph (node-graph: node group = locality). Collapses like a gateway.
    No effect on the engine (flat evaluation) — an editing/presentation container. x/y = canvas position of the collapsed group node.
    """
    graph = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name="groups")
    key = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    collapsed = models.BooleanField(default=False)
    x = models.FloatField(default=0)
    y = models.FloatField(default=0)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children",
        help_text="Parent group (nesting). null=top-level. Engine-agnostic — presentation/drill-in hierarchy only.",
    )

    class Kind(models.TextChoices):
        CONTAINER = "container", "Container (presentation grouping)"
        UNIT = "unit", "Unit (chronostratigraphic span)"

    kind = models.CharField(
        max_length=12, choices=Kind.choices, default=Kind.CONTAINER,
        help_text="Group nature. unit=chronostratigraphic span — references the canonical unit/boundaries via unit/lower/upper.",
    )
    unit = models.ForeignKey(
        "chrono.Unit", null=True, blank=True, on_delete=models.SET_NULL, related_name="span_groups",
        help_text="Canonical unit this span group represents (if any). Inherits rank and dual naming.",
    )
    # Boundaries are referenced, not contained (cell complex). One boundary node can be shared as lower/upper of several groups.
    lower = models.ForeignKey(
        "NodeInstance", null=True, blank=True, on_delete=models.SET_NULL, related_name="lower_of_groups",
        help_text="Lower (older) bounding boundary node. Can be shared with adjacent/child groups.",
    )
    upper = models.ForeignKey(
        "NodeInstance", null=True, blank=True, on_delete=models.SET_NULL, related_name="upper_of_groups",
        help_text="Upper (younger) bounding boundary node. Can be shared with adjacent/parent groups.",
    )

    objects = NodeGroupManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["graph", "key"], name="uniq_group_key_per_graph")
        ]

    def __str__(self):
        return f"{self.graph.slug}/{self.key}"

    def natural_key(self):
        return (self.graph.slug, self.key)

    natural_key.dependencies = ["graph.graph"]


class NodeInstance(models.Model):
    """A node placed on the canvas. key = React Flow node id (client-provided, unique within the graph)."""

    class Nature(models.TextChoices):
        GENERIC = "generic", "Generic (data/process/clamp machinery)"
        BOUNDARY = "boundary", "Boundary (boundary point / 0-cell · independent citizen)"

    graph = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name="nodes")
    key = models.CharField(max_length=100, help_text="React Flow node id (unique within the graph)")
    node_type = models.ForeignKey(NodeType, on_delete=models.PROTECT, related_name="instances")
    nature = models.CharField(
        max_length=12, choices=Nature.choices, default=Nature.GENERIC,
        help_text="Node nature. boundary=boundary point (0-cell) — independent citizen, not contained in a group but referenced via lower/upper. Orthogonal to node_type.",
    )
    label = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True, help_text="User description (keep the title short, put detail here · node tooltip). Separate from the note in params.")
    params = models.JSONField(default=dict, blank=True)
    x = models.FloatField(default=0)
    y = models.FloatField(default=0)
    width = models.FloatField(null=True, blank=True, help_text="User-adjusted node width (px). null=default width.")
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

    natural_key.dependencies = ["graph.graph", "nodes.nodetype", "graph.nodegroup"]

    @property
    def is_cycle_breaker(self):
        """Node that folds/breaks a cycle — joint-inference or clamp (cycles §)."""
        return self.node_type.category == NodeType.Category.CLAMP or self.node_type.slug == "joint-inference"


class Edge(models.Model):
    """Data flow. kind: plain data / provenance (co-location, calibration-transfer) so the gate detects cycles."""
    class Kind(models.TextChoices):
        DATA = "data", "data"
        CO_LOCATION = "co-location", "co-location"
        CALIBRATION_TRANSFER = "calibration-transfer", "calibration-transfer"
        ORDER = "order", "order"  # boundary vertical-port connection = order constraint (replaces the order node). Not data flow.

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
    Unit of ratification/citation/versioning (contract). Exposes a node-group's/node's output as a fixed type.
    The target the schema BoundaryGateway references. A boundary-estimating gateway points at chrono.Boundary.
    """
    graph = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name="gateways")
    slug = models.SlugField()
    name = models.CharField(max_length=200)
    node = models.ForeignKey(
        NodeInstance, on_delete=models.CASCADE, related_name="gateways",
        help_text="The node whose output is exposed",
    )
    output_port = models.CharField(max_length=100, default="out")
    boundary = models.ForeignKey(
        "chrono.Boundary", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="gateways", help_text="The boundary this gateway estimates (if any)",
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

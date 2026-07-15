"""
nodes — node *type system* (vocabulary).

*What kinds of nodes may exist*. Actual wired instances live in the graph app, the compute kernel in the engine app.
Corresponds to Blender's node catalog. Keeping NodeType as data lets scholars register new model kinds like plugins.

Design: docs/app-architecture.md §2.2 / Schema: docs/boundary-gateway-schema.md
For the distribution value object (what edges carry) see nodes/distribution.py.
"""
from django.db import models


class NodeTypeManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class NodeType(models.Model):
    """
    Node type definition. category is the main split (data/process); slug is the engine compute
    kernel binding key (process nodes). data=immutable leaf.
    (`clamp` 카테고리는 devlog 149 에서 제거 — 마지막 멤버 `order` 가 order **edge** 로 대체됨. cycles §12.)
    """
    class Category(models.TextChoices):
        DATA = "data", "Data (immutable observation / leaf)"
        PROCESS = "process", "Process (transform / model)"
        REFERENCE = "reference", "Reference (provenance / citation)"

    slug = models.SlugField(unique=True, help_text="Identifier = engine kernel binding key. e.g. age-depth-model")
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=10, choices=Category.choices)
    description = models.TextField(blank=True)
    params_schema = models.JSONField(
        default=dict, blank=True,
        help_text="Parameter schema (JSON). Basis for the editor to render parameter controls.",
    )

    objects = NodeTypeManager()

    class Meta:
        ordering = ["category", "slug"]

    def __str__(self):
        return self.slug

    def natural_key(self):
        return (self.slug,)

    @property
    def input_ports(self):
        return self.ports.filter(direction=Port.Direction.IN)

    @property
    def output_ports(self):
        return self.ports.filter(direction=Port.Direction.OUT)


class PortManager(models.Manager):
    def get_by_natural_key(self, nodetype_slug, direction, name):
        return self.get(node_type__slug=nodetype_slug, direction=direction, name=name)


class Port(models.Model):
    """
    Input/output port spec of a type. Mostly datatype=distribution (edges carry distributions — node-graph §Blender-difference).
    """
    class Direction(models.TextChoices):
        IN = "in", "in"
        OUT = "out", "out"

    class DataType(models.TextChoices):
        DISTRIBUTION = "distribution", "distribution"   # uncertainty distribution (L0–L5)
        SCALAR = "scalar", "scalar"
        SERIES = "series", "series"                     # e.g. age-depth curves
        SIGNAL = "signal", "signal"                     # correlatable signal (δ13C, magnetic reversal, biostratigraphy)
        ANY = "any", "any"

    node_type = models.ForeignKey(NodeType, on_delete=models.CASCADE, related_name="ports")
    name = models.CharField(max_length=100)
    direction = models.CharField(max_length=3, choices=Direction.choices)
    datatype = models.CharField(max_length=12, choices=DataType.choices, default=DataType.DISTRIBUTION)
    multiple = models.BooleanField(default=False, help_text="Allow multiple connections (bundle input)")
    order = models.IntegerField(default=0)

    objects = PortManager()

    class Meta:
        ordering = ["node_type", "direction", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["node_type", "direction", "name"], name="uniq_port_per_direction"
            )
        ]

    def __str__(self):
        return f"{self.node_type.slug}.{self.name} ({self.direction}:{self.datatype})"

    def natural_key(self):
        return (self.node_type.slug, self.direction, self.name)

    natural_key.dependencies = ["nodes.nodetype"]

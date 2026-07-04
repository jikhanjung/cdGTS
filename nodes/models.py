"""
nodes — 노드 *타입 시스템* (어휘).

*무슨 종류의 노드가 존재할 수 있는가*. 실제 배선된 인스턴스는 graph 앱, 계산 커널은 engine 앱.
블렌더 노드 카탈로그에 대응. NodeType 을 데이터로 두어 학자가 새 모델 종류를 플러그인처럼 등록.

설계: docs/app-architecture.md §2.2 / 스키마: docs/boundary-gateway-schema.md
분포 값 객체(엣지가 흘리는 것)는 nodes/distribution.py 참조.
"""
from django.db import models


class NodeTypeManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class NodeType(models.Model):
    """
    노드 타입 정의. category 로 크게 갈리고(data/process/clamp), slug 가 engine 계산 커널
    바인딩 키(process 노드). data=불변 leaf, clamp=거버넌스 게이트웨이.
    """
    class Category(models.TextChoices):
        DATA = "data", "Data (불변 관측·leaf)"
        PROCESS = "process", "Process (변환·모델)"
        CLAMP = "clamp", "Clamp (거버넌스 게이트)"

    slug = models.SlugField(unique=True, help_text="식별자 = engine 커널 바인딩 키. 예: age-depth-model")
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=10, choices=Category.choices)
    description = models.TextField(blank=True)
    params_schema = models.JSONField(
        default=dict, blank=True,
        help_text="파라미터 스키마(JSON). 에디터가 파라미터 컨트롤을 렌더할 근거.",
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
    타입의 입출력 포트 스펙. 대부분 datatype=distribution (엣지가 분포를 흘린다 — node-graph §블렌더차이).
    """
    class Direction(models.TextChoices):
        IN = "in", "in"
        OUT = "out", "out"

    class DataType(models.TextChoices):
        DISTRIBUTION = "distribution", "distribution"   # 불확실성 분포 (L0–L5)
        SCALAR = "scalar", "scalar"
        SERIES = "series", "series"                     # age-depth 곡선 등
        SIGNAL = "signal", "signal"                     # 상관 가능한 신호(d13C·자기반전·생층서)
        ANY = "any", "any"

    node_type = models.ForeignKey(NodeType, on_delete=models.CASCADE, related_name="ports")
    name = models.CharField(max_length=100)
    direction = models.CharField(max_length=3, choices=Direction.choices)
    datatype = models.CharField(max_length=12, choices=DataType.choices, default=DataType.DISTRIBUTION)
    multiple = models.BooleanField(default=False, help_text="다중 연결 허용(번들 입력)")
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

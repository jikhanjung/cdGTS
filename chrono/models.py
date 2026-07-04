"""
chrono — 정본 registry (Layer 0).

값이 아니라 *이름과 계보*를 관리한다. 경계 연대 숫자·정의 스냅샷은 releases 앱(BoundaryRecord)에,
평가 그래프는 graph 앱에 산다. 여기는 모두가 가리키는 안정적 정본.

설계: docs/app-architecture.md §2.1 / 스키마: docs/boundary-gateway-schema.md
"""
from django.db import models


class Rank(models.IntegerChoices):
    """이중 명명 사다리 — 한 등급의 두 이름(연대층서 ↔ 지질연대)."""
    EON = 1, "Eon / Eonothem"
    ERA = 2, "Era / Erathem"
    PERIOD = 3, "Period / System"
    EPOCH = 4, "Epoch / Series"
    AGE = 5, "Age / Stage"


# 이중 명명: 같은 고유명(예: Changhsingian)에 등급어만 다르게 붙는다.
_CHRONO_TERM = {1: "Eonothem", 2: "Erathem", 3: "System", 4: "Series", 5: "Stage"}
_GEO_TERM = {1: "Eon", 2: "Era", 3: "Period", 4: "Epoch", 5: "Age"}


class UnitManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class AuthorityManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class BoundaryManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class BoundaryLineageManager(models.Manager):
    def get_by_natural_key(self, boundary_slug, op):
        return self.get(boundary__slug=boundary_slug, op=op)


class RatificationManager(models.Manager):
    def get_by_natural_key(self, boundary_slug, authority_slug, year):
        return self.get(boundary__slug=boundary_slug, authority__slug=authority_slug, year=year)


class LocalityManager(models.Manager):
    def get_by_natural_key(self, boundary_slug):
        return self.get(boundary__slug=boundary_slug)


class Unit(models.Model):
    """
    이중 명명 단위 (Layer 0). 같은 엔티티가 연대층서(System…)와 지질연대(Period…) 두 얼굴을 갖는다.
    고유명은 공유되고 등급어만 다르다: "Changhsingian Stage" = "Changhsingian Age".
    위계는 self-FK(부모 = 상위 등급 단위).
    """
    slug = models.SlugField(unique=True, help_text="안정 식별자. 예: changhsingian")
    name = models.CharField(max_length=100, help_text="고유명(등급어 제외). 예: Changhsingian")
    rank = models.IntegerField(choices=Rank.choices)
    color = models.CharField(max_length=7, blank=True, default="",
                             help_text="ICS 공식 색 (#RRGGBB). ICC 차트 표시용.")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children",
        help_text="상위 등급 단위. 예: Changhsingian(Age) → Lopingian(Epoch)",
    )

    objects = UnitManager()

    class Meta:
        ordering = ["rank", "name"]

    def __str__(self):
        return f"{self.name} ({self.geochronologic_term})"

    def natural_key(self):
        return (self.slug,)

    @property
    def chronostratigraphic_term(self):
        """연대층서 등급어. 예: Stage."""
        return _CHRONO_TERM[self.rank]

    @property
    def geochronologic_term(self):
        """지질연대 등급어. 예: Age."""
        return _GEO_TERM[self.rank]

    @property
    def chronostratigraphic_name(self):
        return f"{self.name} {self.chronostratigraphic_term}"

    @property
    def geochronologic_name(self):
        return f"{self.name} {self.geochronologic_term}"


class Authority(models.Model):
    """비준·clamp의 주체. ICS·subcommission·샌드박스·fork."""
    class Kind(models.TextChoices):
        ICS = "ICS", "ICS"
        SUBCOMMISSION = "subcommission", "Subcommission"
        SANDBOX = "sandbox-branch", "Sandbox branch"
        FORK = "fork", "Fork"

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.ICS)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children",
        help_text="상위 권위. 예: Cambrian Subcommission → ICS",
    )

    objects = AuthorityManager()

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "authorities"

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.slug,)


class Boundary(models.Model):
    """
    경계 정체성 (안정 슬러그). 값·정의 스냅샷은 여기 두지 않는다 — releases.BoundaryRecord.
    definition_type 은 *현재* 분류(재배선 시 releases 스냅샷이 버전별 진실).
    """
    class DefinitionType(models.TextChoices):
        GSSP = "GSSP", "GSSP (지점)"
        GSSA = "GSSA", "GSSA (결정 숫자)"

    slug = models.SlugField(unique=True, help_text="안정 슬러그. 예: base-triassic")
    name = models.CharField(max_length=200, help_text="사람용 이름. 예: Base of the Triassic")
    below = models.ForeignKey(
        Unit, null=True, blank=True, on_delete=models.PROTECT, related_name="boundaries_above",
        help_text="경계 아래(더 오래된) 단위",
    )
    above = models.ForeignKey(
        Unit, null=True, blank=True, on_delete=models.PROTECT, related_name="boundaries_below",
        help_text="경계 위(더 젊은) 단위",
    )
    definition_type = models.CharField(
        max_length=8, choices=DefinitionType.choices, null=True, blank=True,
        help_text="현재 정의 방식. 버전별 진실은 releases 스냅샷.",
    )
    note = models.TextField(blank=True)

    objects = BoundaryManager()

    class Meta:
        ordering = ["slug"]
        verbose_name_plural = "boundaries"

    def __str__(self):
        return self.slug

    def natural_key(self):
        return (self.slug,)


class BoundaryLineage(models.Model):
    """
    버전 간 경계 정체성 계보 (토폴로지 diff의 전제). 스키마 identity.lineage.
    op=renamed 는 sources 에 이전 경계, split/merge 는 원본(들).
    """
    class Op(models.TextChoices):
        CREATED = "created", "created"
        RENAMED = "renamed", "renamed"
        SPLIT = "split", "split"
        MERGED = "merged", "merged"
        RETYPED = "retyped", "retyped (GSSA↔GSSP)"
        DEPRECATED = "deprecated", "deprecated"

    boundary = models.ForeignKey(Boundary, on_delete=models.CASCADE, related_name="lineage")
    op = models.CharField(max_length=12, choices=Op.choices)
    sources = models.ManyToManyField(
        Boundary, blank=True, related_name="lineage_targets",
        help_text="split/merge 원본(들), rename 의 이전 경계",
    )
    note = models.TextField(blank=True)

    objects = BoundaryLineageManager()

    def __str__(self):
        return f"{self.boundary.slug}: {self.op}"

    def natural_key(self):
        return (self.boundary.slug, self.op)

    natural_key.dependencies = ["chrono.boundary"]


class Ratification(models.Model):
    """경계 비준 사건. 스키마 definition.ratified {year, by}."""
    boundary = models.ForeignKey(Boundary, on_delete=models.CASCADE, related_name="ratifications")
    authority = models.ForeignKey(Authority, on_delete=models.PROTECT, related_name="ratifications")
    year = models.IntegerField()
    note = models.TextField(blank=True)

    objects = RatificationManager()

    class Meta:
        ordering = ["year"]

    def __str__(self):
        return f"{self.boundary.slug} @ {self.year} ({self.authority.slug})"

    def natural_key(self):
        return (self.boundary.slug, self.authority.slug, self.year)

    natural_key.dependencies = ["chrono.boundary", "chrono.authority"]


class Locality(models.Model):
    """
    GSSP 노두(stratotype 지점). GSSA 는 노두 없음. 스키마 definition.stratotype.
    지금은 lat/lon 스칼라 — PostGIS 착수 시 PointField 로 승격(공간 차원 트리거).
    """
    boundary = models.OneToOneField(
        Boundary, on_delete=models.CASCADE, related_name="stratotype",
        help_text="이 노두가 정의하는 경계(GSSP)",
    )
    name = models.CharField(max_length=300, help_text='예: "Meishan D, Changxing, Zhejiang, China"')
    level = models.CharField(max_length=300, blank=True, help_text='예: "base of Bed 27c"')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    objects = LocalityManager()

    class Meta:
        verbose_name_plural = "localities"

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.boundary.slug,)

    natural_key.dependencies = ["chrono.boundary"]

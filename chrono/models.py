"""
chrono — canonical registry (Layer 0).

Manages *names and lineage*, not values. Boundary age numbers and definition snapshots live in the releases app (BoundaryRecord),
evaluation graphs in the graph app. This is the stable canon everyone points at.

Design: docs/app-architecture.md §2.1 / Schema: docs/boundary-gateway-schema.md
"""
from django.db import models


class Rank(models.IntegerChoices):
    """Dual-naming ladder — the two names of a rank (chronostratigraphic ↔ geochronologic).
    Subperiod (Subsystem) is an official ICS rank between Period and Epoch, currently used only by the Carboniferous."""
    EON = 1, "Eon / Eonothem"
    ERA = 2, "Era / Erathem"
    PERIOD = 3, "Period / System"
    SUB_PERIOD = 4, "Subperiod / Subsystem"
    EPOCH = 5, "Epoch / Series"
    AGE = 6, "Age / Stage"


# Dual naming: the same proper name (e.g. Changhsingian) takes only a different rank term.
_CHRONO_TERM = {1: "Eonothem", 2: "Erathem", 3: "System", 4: "Subsystem", 5: "Series", 6: "Stage"}
_GEO_TERM = {1: "Eon", 2: "Era", 3: "Period", 4: "Subperiod", 5: "Epoch", 6: "Age"}


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
    Dual-naming unit (Layer 0). The same entity has two faces: chronostratigraphic (System…) and geochronologic (Period…).
    The proper name is shared and only the rank term differs: "Changhsingian Stage" = "Changhsingian Age".
    Hierarchy is a self-FK (parent = higher-rank unit).
    """
    slug = models.SlugField(unique=True, help_text="Stable identifier. e.g. changhsingian")
    name = models.CharField(max_length=100, help_text="Proper name (without the rank term). e.g. Changhsingian")
    rank = models.IntegerField(choices=Rank.choices)
    color = models.CharField(max_length=7, blank=True, default="",
                             help_text="Official ICS color (#RRGGBB). For ICC chart display.")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children",
        help_text="Higher-rank unit. e.g. Changhsingian(Age) → Lopingian(Epoch)",
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
        """Chronostratigraphic rank term. e.g. Stage."""
        return _CHRONO_TERM[self.rank]

    @property
    def geochronologic_term(self):
        """Geochronologic rank term. e.g. Age."""
        return _GEO_TERM[self.rank]

    @property
    def chronostratigraphic_name(self):
        return f"{self.name} {self.chronostratigraphic_term}"

    @property
    def geochronologic_name(self):
        return f"{self.name} {self.geochronologic_term}"


class Authority(models.Model):
    """The agent behind ratifications/clamps. ICS, subcommission, sandbox, fork."""
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
        help_text="Parent authority. e.g. Cambrian Subcommission → ICS",
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
    Boundary identity (stable slug). Value/definition snapshots do not live here — releases.BoundaryRecord.
    definition_type is the *current* classification (on rewiring, the releases snapshot is the per-version truth).
    """
    class DefinitionType(models.TextChoices):
        GSSP = "GSSP", "GSSP (point)"
        GSSA = "GSSA", "GSSA (decreed number)"

    slug = models.SlugField(unique=True, help_text="Stable slug. e.g. base-triassic")
    name = models.CharField(max_length=200, help_text="Human-readable name. e.g. Base of the Triassic")
    below = models.ForeignKey(
        Unit, null=True, blank=True, on_delete=models.PROTECT, related_name="boundaries_above",
        help_text="Unit below (older than) the boundary",
    )
    above = models.ForeignKey(
        Unit, null=True, blank=True, on_delete=models.PROTECT, related_name="boundaries_below",
        help_text="Unit above (younger than) the boundary",
    )
    definition_type = models.CharField(
        max_length=8, choices=DefinitionType.choices, null=True, blank=True,
        help_text="Current definition method. Per-version truth is the releases snapshot.",
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
    Cross-version boundary identity lineage (premise of the topology diff). Schema identity.lineage.
    op=renamed puts the previous boundary in sources; split/merge the origin(s).
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
        help_text="split/merge origin(s), the previous boundary of a rename",
    )
    note = models.TextField(blank=True)

    objects = BoundaryLineageManager()

    def __str__(self):
        return f"{self.boundary.slug}: {self.op}"

    def natural_key(self):
        return (self.boundary.slug, self.op)

    natural_key.dependencies = ["chrono.boundary"]


class Ratification(models.Model):
    """Boundary ratification event. Schema definition.ratified {year, by}."""
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
    GSSP outcrop (stratotype point). GSSA has no outcrop. Schema definition.stratotype.
    Currently lat/lon scalars — promote to PointField when PostGIS is adopted (spatial-dimension trigger).
    """
    boundary = models.OneToOneField(
        Boundary, on_delete=models.CASCADE, related_name="stratotype",
        help_text="The boundary this outcrop defines (GSSP)",
    )
    name = models.CharField(max_length=300, help_text='e.g. "Meishan D, Changxing, Zhejiang, China"')
    level = models.CharField(max_length=300, blank=True, help_text='e.g. "base of Bed 27c"')
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

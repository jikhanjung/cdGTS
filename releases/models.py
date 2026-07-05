"""
releases — 버전·배포·diff (최상위 조립자).

경쟁 후보(ModelCandidate)는 네트워크에 복수 공존하고, Release 가 selection 으로 하나를 바인딩한다
(경계 레코드가 아니라 릴리스가 selection 소유). BoundaryRecord = 한 릴리스에서 얼린 스냅샷 = ICC bake.
Diff = 두 릴리스 간 값 diff + 토폴로지 diff(직교 축).

설계: docs/app-architecture.md §2.5 / 스키마: docs/boundary-gateway-schema.md §2
"""
from django.db import models


class AgeMethod(models.TextChoices):
    DECREED = "decreed", "decreed (GSSA)"
    LOCAL_INTERP = "local-interpolation", "local interpolation"
    CROSS_SECTION = "cross-section-correlation", "cross-section correlation"


class ModelCandidateManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class CandidateOutputManager(models.Manager):
    def get_by_natural_key(self, candidate_slug, boundary_slug):
        return self.get(candidate__slug=candidate_slug, boundary__slug=boundary_slug)


class ClampManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class ReleaseManager(models.Manager):
    def get_by_natural_key(self, version):
        return self.get(version=version)


class SelectionManager(models.Manager):
    def get_by_natural_key(self, release_version, boundary_slug):
        return self.get(release__version=release_version, boundary__slug=boundary_slug)


class ModelCandidate(models.Model):
    """네트워크에 공존하는 경쟁 후보 (독립 주소지정). 릴리스가 그중 하나를 선택."""
    class Scope(models.TextChoices):
        BOUNDARY = "boundary", "boundary"
        GLOBAL = "global", "global (다경계 동시)"

    slug = models.SlugField(unique=True, help_text="예: ediacaran-cambrian/bowyer2022-modelAB")
    scope = models.CharField(max_length=10, choices=Scope.choices, default=Scope.BOUNDARY)
    kind = models.CharField(max_length=100, help_text="예: global-d13C-age-model, committee-decision")
    method = models.CharField(max_length=28, choices=AgeMethod.choices)
    provenance_ref = models.CharField(max_length=300, blank=True, help_text="값을 내는 서브그래프 참조")
    note = models.TextField(blank=True)

    objects = ModelCandidateManager()

    def __str__(self):
        return self.slug

    def natural_key(self):
        return (self.slug,)


class CandidateOutput(models.Model):
    """후보가 특정 경계에 대해 내는 값(분포)."""
    candidate = models.ForeignKey(ModelCandidate, on_delete=models.CASCADE, related_name="outputs")
    boundary = models.ForeignKey("chrono.Boundary", on_delete=models.CASCADE, related_name="candidate_outputs")
    distribution = models.JSONField(help_text="Distribution.to_dict (nodes.distribution)")

    objects = CandidateOutputManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["candidate", "boundary"], name="uniq_output_per_candidate_boundary")
        ]

    def __str__(self):
        return f"{self.candidate.slug} → {self.boundary.slug}"

    def natural_key(self):
        return (self.candidate.slug, self.boundary.slug)

    natural_key.dependencies = ["releases.modelcandidate", "chrono.boundary"]


class Clamp(models.Model):
    """
    subcommission 이 놓는 거버넌스 clamp (스키마 Clamp). GSSA = Clamp{pin} 의 특수사례.
    graph 의 clamp *노드*는 그래프 내 표현, 이건 릴리스가 적용하는 *authored* 거버넌스 레코드.
    """
    class Kind(models.TextChoices):
        PIN = "pin", "pin"
        RANGE = "range", "range"
        ORDER = "order", "order"
        FREEZE_VERSION = "freeze-version", "freeze-version"

    slug = models.SlugField(unique=True)
    owner = models.ForeignKey("chrono.Authority", on_delete=models.PROTECT, related_name="clamps")
    target_boundary = models.ForeignKey(
        "chrono.Boundary", null=True, blank=True, on_delete=models.CASCADE, related_name="clamps",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    value = models.JSONField(default=dict, blank=True, help_text="pin=값 / range=[min,max] / order=이웃 / freeze=버전")
    rationale = models.TextField(blank=True)
    ratified_year = models.IntegerField(null=True, blank=True)
    overridable_in_sandbox = models.BooleanField(default=True)

    objects = ClampManager()

    def __str__(self):
        return f"{self.slug} ({self.kind})"

    def natural_key(self):
        return (self.slug,)


class Release(models.Model):
    """전역 릴리스 매니페스트. selection 과 clamps 를 소유."""
    version = models.CharField(max_length=50, unique=True, help_text="예: ICC-2024/12")
    authority = models.ForeignKey(
        "chrono.Authority", null=True, blank=True, on_delete=models.SET_NULL, related_name="releases",
    )
    note = models.TextField(blank=True)
    is_baseline = models.BooleanField(
        default=False, help_text="공표 기준 릴리스(Science CI 의 diff 대상). 그래프-bake 를 이것과 비교.",
    )
    clamps = models.ManyToManyField(Clamp, blank=True, related_name="releases")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ReleaseManager()

    class Meta:
        ordering = ["version"]

    def __str__(self):
        return self.version

    def natural_key(self):
        return (self.version,)


class Selection(models.Model):
    """릴리스의 경계별 후보 선택 (정합한 선택)."""
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="selections")
    boundary = models.ForeignKey("chrono.Boundary", on_delete=models.CASCADE, related_name="selections")
    candidate = models.ForeignKey(ModelCandidate, on_delete=models.PROTECT, related_name="selections")

    objects = SelectionManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["release", "boundary"], name="uniq_selection_per_release_boundary")
        ]

    def __str__(self):
        return f"{self.release.version}: {self.boundary.slug} → {self.candidate.slug}"

    def natural_key(self):
        return (self.release.version, self.boundary.slug)

    natural_key.dependencies = ["releases.release", "chrono.boundary"]


class BoundaryRecord(models.Model):
    """
    한 릴리스에서 얼린 BoundaryGateway 스냅샷 = ICC bake.
    definition_type 은 그 시점 분류(버전별 진실), value/uncertainty 는 선택된 후보 출력의 bake 사본.
    """
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="records")
    boundary = models.ForeignKey("chrono.Boundary", on_delete=models.CASCADE, related_name="records")
    definition_type = models.CharField(max_length=8, blank=True)   # GSSP|GSSA 스냅샷
    value_ma = models.FloatField(null=True, blank=True)
    uncertainty = models.JSONField(null=True, blank=True, help_text="Distribution.to_dict")
    method = models.CharField(max_length=28, choices=AgeMethod.choices, blank=True)
    candidate = models.ForeignKey(
        ModelCandidate, null=True, blank=True, on_delete=models.SET_NULL, related_name="records",
    )
    provenance_ref = models.CharField(max_length=300, blank=True)
    narrative = models.TextField(blank=True, help_text="GTS narrate 서술(스텁)")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["release", "boundary"], name="uniq_record_per_release_boundary")
        ]
        ordering = ["boundary__slug"]

    def __str__(self):
        return f"{self.release.version}/{self.boundary.slug} = {self.value_ma}"

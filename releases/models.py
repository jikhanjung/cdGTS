"""
releases — versions, deployment, diff (top-level assembler).

Competing candidates (ModelCandidate) coexist in the network, and a Release binds one via selection
(the release owns the selection, not the boundary record). BoundaryRecord = a snapshot frozen in one release = ICC bake.
Diff = value diff between two releases + topology diff (orthogonal axes).

Design: docs/app-architecture.md §2.5 / Schema: docs/boundary-gateway-schema.md §2
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
    """Competing candidate coexisting in the network (independently addressable). A release selects one of them."""
    class Scope(models.TextChoices):
        BOUNDARY = "boundary", "boundary"
        GLOBAL = "global", "global (multiple boundaries at once)"

    slug = models.SlugField(unique=True, help_text="e.g. ediacaran-cambrian/bowyer2022-modelAB")
    scope = models.CharField(max_length=10, choices=Scope.choices, default=Scope.BOUNDARY)
    kind = models.CharField(max_length=100, help_text="e.g. global-d13C-age-model, committee-decision")
    method = models.CharField(max_length=28, choices=AgeMethod.choices)
    provenance_ref = models.CharField(max_length=300, blank=True, help_text="Reference to the subgraph that produces the value")
    note = models.TextField(blank=True)

    objects = ModelCandidateManager()

    def __str__(self):
        return self.slug

    def natural_key(self):
        return (self.slug,)


class CandidateOutput(models.Model):
    """The value (distribution) a candidate produces for a specific boundary."""
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
    Governance clamp placed by a subcommission (schema Clamp). GSSA = a special case of Clamp{pin}.

    ⚠️ DEMO-ONLY (2026-07, cycles §12): kept to demonstrate the L3a verify / L3b reconcile idea (seed_demo),
    but **not a live product feature** — no real release authors clamps. The reconsideration concluded a clamp
    is not needed as a distinct concept: an authored value is a `published-age` leaf (GSSA), cycles fold into a
    joint-inference node, order is an order edge. See docs/cycles.md §12. Applying a clamp at the release layer
    also edits baked values out-of-band (a provenance hole); a real override belongs as an authored graph node
    that re-bakes. Do not build graph-clamp ↔ this integration.
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
    value = models.JSONField(default=dict, blank=True, help_text="pin=value / range=[min,max] / order=neighbors / freeze=version")
    rationale = models.TextField(blank=True)
    ratified_year = models.IntegerField(null=True, blank=True)
    overridable_in_sandbox = models.BooleanField(default=True)

    objects = ClampManager()

    def __str__(self):
        return f"{self.slug} ({self.kind})"

    def natural_key(self):
        return (self.slug,)


class Release(models.Model):
    """Global release manifest. Owns the selection and clamps.

    kind distinguishes the artifact:
      - published : official release (ICS-2024/12 …); is_baseline marks the CI diff target.
      - bake      : an immutable snapshot a user baked from a graph (the Vault artifact).
      - transient : the scratch re-bake used by Science-CI verify (graph:<slug>, overwritten, hidden from Vault).
    """
    class Kind(models.TextChoices):
        PUBLISHED = "published", "published"
        BAKE = "bake", "bake"
        SANDBOX = "sandbox", "sandbox"        # a baseline + per-boundary candidate overrides (P05.5)
        TRANSIENT = "transient", "transient"

    version = models.CharField(max_length=100, unique=True, help_text="e.g. ICC-2024/12 · GeologicTimeScale.Release.<user>.YYYYMMDD.NN")
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.PUBLISHED)
    owner = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="releases",
        help_text="The user who baked this artifact (null = system/published).",
    )
    source_graph = models.ForeignKey(
        "graph.Graph", null=True, blank=True, on_delete=models.SET_NULL, related_name="bakes",
        help_text="Provenance: the graph this artifact was baked from (bake/transient kinds).",
    )
    base = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="sandboxes",
        help_text="The baseline this sandbox derives from (sandbox kind = base + per-boundary overrides).",
    )
    authority = models.ForeignKey(
        "chrono.Authority", null=True, blank=True, on_delete=models.SET_NULL, related_name="releases",
    )
    note = models.TextField(blank=True)
    is_baseline = models.BooleanField(
        default=False, help_text="Published baseline release (the diff target of Science CI). Graph bakes are compared against this.",
    )
    clamps = models.ManyToManyField(Clamp, blank=True, related_name="releases")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ReleaseManager()

    class Meta:
        ordering = ["-created_at", "version"]

    def __str__(self):
        return self.version

    def natural_key(self):
        return (self.version,)


class Proposal(models.Model):
    """
    A proposed change (P05.4 = CI). Binds a sandbox graph to the baseline it targets; review = verify diff.
    `affected` (boundary slugs the change touches, from the diff) is the seam for interval-scoped ratify (P05 §확장).
    """
    class State(models.TextChoices):
        OPEN = "open", "open"
        MERGED = "merged", "merged"
        REJECTED = "rejected", "rejected"

    graph = models.ForeignKey("graph.Graph", on_delete=models.CASCADE, related_name="proposals")
    baseline = models.ForeignKey(Release, on_delete=models.PROTECT, related_name="proposals_against")
    author = models.ForeignKey("auth.User", null=True, on_delete=models.SET_NULL, related_name="proposals")
    state = models.CharField(max_length=8, choices=State.choices, default=State.OPEN)
    comment = models.TextField(blank=True)
    affected = models.JSONField(default=list, blank=True, help_text="Boundary slugs the change moves/retypes (from the diff).")
    reviewer = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="reviews")
    review_comment = models.TextField(blank=True)
    result_release = models.ForeignKey(
        Release, null=True, blank=True, on_delete=models.SET_NULL, related_name="from_proposal",
        help_text="The published Release baked when this proposal was ratified.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Proposal #{self.pk}: {self.graph.slug} vs {self.baseline.version} ({self.state})"


class Selection(models.Model):
    """A release's per-boundary candidate selection (coherent selection)."""
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
    A BoundaryGateway snapshot frozen in one release = ICC bake.
    definition_type is the classification at that point (per-version truth); value/uncertainty are the baked copy of the selected candidate's output.
    """
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="records")
    boundary = models.ForeignKey("chrono.Boundary", on_delete=models.CASCADE, related_name="records")
    definition_type = models.CharField(max_length=8, blank=True)   # GSSP|GSSA snapshot
    value_ma = models.FloatField(null=True, blank=True)
    uncertainty = models.JSONField(null=True, blank=True, help_text="Distribution.to_dict")
    method = models.CharField(max_length=28, choices=AgeMethod.choices, blank=True)
    candidate = models.ForeignKey(
        ModelCandidate, null=True, blank=True, on_delete=models.SET_NULL, related_name="records",
    )
    provenance_ref = models.CharField(max_length=300, blank=True)
    references = models.JSONField(default=list, blank=True,
                                  help_text="Contributing reference slugs — cite-edge provenance snapshot at bake.")
    narrative = models.TextField(blank=True, help_text="GTS narrate prose (stub)")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["release", "boundary"], name="uniq_record_per_release_boundary")
        ]
        ordering = ["boundary__slug"]

    def __str__(self):
        return f"{self.release.version}/{self.boundary.slug} = {self.value_ma}"

"""
references — bibliographic registry (DOI-centric).

A Reference is the *source* of a data or model node. It is cited from the graph by `reference`
NodeType instances wired with `cite` edges (non-data — excluded from evaluation & cycle detection),
so provenance is a first-class, wire-able citizen. A bake can later walk cite edges upstream to
collect the full bibliography of a result.

Design: docs/node-graph-paradigm.md (everything is a node) · cite edge in graph.models.Edge.

Ownership: the registry is a **global shared library** (a DOI is a global fact, not per-user), but
`created_by` records who added an entry, and edits/deletes are limited to that creator or staff
(references.permissions.ReferenceAccessPermission). A reference cited by any graph can't be deleted.
"""
from django.conf import settings
from django.db import models


class ReferenceManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class Reference(models.Model):
    """One bibliographic entry. `doi` is the primary handle; `slug` is the stable natural key."""

    class Kind(models.TextChoices):
        ARTICLE = "article", "journal article"
        BOOK = "book", "book"
        CHAPTER = "chapter", "book chapter"
        DATASET = "dataset", "dataset"
        REPORT = "report", "report"
        WEB = "web", "web"

    slug = models.SlugField(max_length=120, unique=True, help_text="Stable id / natural key. e.g. cohen-2013-ics")
    doi = models.CharField(max_length=200, blank=True, help_text="DOI without the https://doi.org/ prefix.")
    title = models.CharField(max_length=500)
    authors = models.CharField(max_length=500, blank=True, help_text="e.g. Cohen, Finney, Gibbard & Fan")
    year = models.IntegerField(null=True, blank=True)
    container = models.CharField(max_length=300, blank=True, help_text="Journal / publisher / venue.")
    url = models.URLField(blank=True, help_text="Fallback link when there is no DOI.")
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.ARTICLE)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="Who added this entry (null = system/seed). Only they or staff may edit/delete it.",
    )

    objects = ReferenceManager()

    class Meta:
        ordering = ["year", "slug"]
        constraints = [
            models.UniqueConstraint(fields=["doi"], condition=~models.Q(doi=""), name="uniq_doi_when_present"),
        ]

    def __str__(self):
        who = self.authors or self.slug
        return f"{who} ({self.year})" if self.year else who

    def natural_key(self):
        return (self.slug,)

    @property
    def link(self):
        """Resolvable URL — DOI first, else the fallback url."""
        return f"https://doi.org/{self.doi}" if self.doi else self.url

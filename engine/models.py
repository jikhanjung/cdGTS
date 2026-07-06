"""
engine — evaluation (Layer 5 orchestration).

Initial scope: **pass-through** — node output = input distribution propagated as-is (no computation). idea §7 "published value + source" layer.
Incremental re-evaluation via node content hash (reuse the previous run's result when inputs are unchanged). Heavy computation (MC/Bayesian) comes later.

Design: docs/app-architecture.md §2.4 / Evaluation logic: engine/evaluate.py
"""
from django.db import models

from graph.models import Graph


class EvalRun(models.Model):
    """An evaluation job for one graph."""
    graph = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name="eval_runs")
    created_at = models.DateTimeField(auto_now_add=True)
    stats = models.JSONField(default=dict, blank=True, help_text="e.g. {computed, cached}")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"run#{self.pk} of {self.graph.slug}"


class NodeResult(models.Model):
    """
    Per-node output. distribution = propagated distribution (Distribution.to_dict) or null (signal/no data).
    content_hash = (type, params, input hash) → reused when inputs are unchanged (incremental). provenance = contributing upstream node keys (traceback).
    Nodes are replaced on re-save, so referenced by the key string rather than an FK.
    """
    eval_run = models.ForeignKey(EvalRun, on_delete=models.CASCADE, related_name="results")
    node_key = models.CharField(max_length=100)
    content_hash = models.CharField(max_length=40)
    distribution = models.JSONField(null=True, blank=True)
    provenance = models.JSONField(default=list, blank=True)
    cached = models.BooleanField(default=False, help_text="Reused from a previous run (incremental hit)")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["eval_run", "node_key"], name="uniq_result_per_run_node")
        ]

    def __str__(self):
        return f"{self.node_key}@run#{self.eval_run_id}"


class CoherenceCertificate(models.Model):
    """
    Layer 5 coherence gate certificate (stub). Results of the check ladder L0–L3.
    Skeleton only for now — real monotonic-order, interval-overlap, and joint-coherence checks come later.
    """
    eval_run = models.OneToOneField(EvalRun, on_delete=models.CASCADE, related_name="certificate")
    passed = models.BooleanField(default=True)
    checks = models.JSONField(default=dict, blank=True, help_text="{L0, L1, L2, L3: pass|warn|skip}")

    def __str__(self):
        return f"cert(run#{self.eval_run_id}, {'pass' if self.passed else 'fail'})"

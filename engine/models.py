"""
engine — evaluation (Layer 5 orchestration).

Initial scope: **pass-through** — node output = input distribution propagated as-is (no computation). idea §7 "published value + source" layer.
Incremental re-evaluation via node content hash (reuse the previous run's result when inputs are unchanged). Heavy computation (MC/Bayesian) comes later.

Design: docs/app-architecture.md §2.4 / Evaluation logic: engine/evaluate.py
"""
from django.conf import settings
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


class EvalJob(models.Model):
    """
    비동기 평가 잡 (P06.4a). joint 커널·순환 상호제약 클러스터가 있는 그래프는 in-request 로
    돌리기엔 (장차 MCMC 로) 무거우므로 워커로 미룬다. 해석적(빠른) 그래프는 종전대로 동기
    평가하고 이 잡을 만들지 않는다(engine.evaluate.needs_async 가 라우팅).

    워커(`manage.py run_worker`)가 queued 를 집어 evaluate_graph 를 돌리고 결과 EvalRun 을 run 에 건다.
    P06.4a 는 인프라만 — 커널은 아직 해석적이라 동기·비동기 결과가 동일하다(진짜 MCMC 는 P06.4b).
    """
    STATUS_CHOICES = [
        ("queued", "queued"), ("running", "running"), ("done", "done"), ("failed", "failed"),
    ]
    graph = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name="eval_jobs")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="queued")
    params = models.JSONField(default=dict, blank=True)
    run = models.ForeignKey(EvalRun, null=True, blank=True, on_delete=models.SET_NULL,
                            related_name="jobs", help_text="완료 시 산출된 EvalRun")
    error = models.TextField(blank=True, default="")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"job#{self.pk} {self.status} of {self.graph.slug}"

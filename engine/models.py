"""
engine — 평가 (Layer 5 오케스트레이션).

착수 스코프: **pass-through** — 노드 출력 = 입력 분포 그대로 전파(계산 없음). idea §7 "발표값+출처" 층.
증분 재평가는 노드 콘텐츠 해시로(입력 불변 시 이전 run 결과 재사용). 무거운 계산(MC/베이지안)은 후속.

설계: docs/app-architecture.md §2.4 / 평가 로직: engine/evaluate.py
"""
from django.db import models

from graph.models import Graph


class EvalRun(models.Model):
    """한 그래프의 평가 작업."""
    graph = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name="eval_runs")
    created_at = models.DateTimeField(auto_now_add=True)
    stats = models.JSONField(default=dict, blank=True, help_text="{computed, cached} 등")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"run#{self.pk} of {self.graph.slug}"


class NodeResult(models.Model):
    """
    노드별 산출. distribution = 전파된 분포(Distribution.to_dict) 또는 null(신호/무데이터).
    content_hash = (타입·params·입력 해시) → 입력 불변 시 재사용(증분). provenance = 기여 상류 노드 key(역추적).
    node 는 재저장 시 교체되므로 FK 아닌 key 문자열로 참조.
    """
    eval_run = models.ForeignKey(EvalRun, on_delete=models.CASCADE, related_name="results")
    node_key = models.CharField(max_length=100)
    content_hash = models.CharField(max_length=40)
    distribution = models.JSONField(null=True, blank=True)
    provenance = models.JSONField(default=list, blank=True)
    cached = models.BooleanField(default=False, help_text="이전 run 에서 재사용(증분 히트)")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["eval_run", "node_key"], name="uniq_result_per_run_node")
        ]

    def __str__(self):
        return f"{self.node_key}@run#{self.eval_run_id}"


class CoherenceCertificate(models.Model):
    """
    Layer 5 정합성 게이트 인증서 (스텁). 검사 사다리 L0–L3 결과.
    현 단계는 뼈대만 — 실제 단조순서·구간겹침·joint 정합 검사는 후속.
    """
    eval_run = models.OneToOneField(EvalRun, on_delete=models.CASCADE, related_name="certificate")
    passed = models.BooleanField(default=True)
    checks = models.JSONField(default=dict, blank=True, help_text="{L0, L1, L2, L3: pass|warn|skip}")

    def __str__(self):
        return f"cert(run#{self.eval_run_id}, {'pass' if self.passed else 'fail'})"

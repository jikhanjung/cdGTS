from rest_framework import serializers

from .models import CoherenceCertificate, EvalJob, EvalRun, NodeResult


class NodeResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeResult
        fields = ["node_key", "distribution", "provenance", "cached"]


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoherenceCertificate
        fields = ["passed", "checks"]


class EvalRunSerializer(serializers.ModelSerializer):
    results = NodeResultSerializer(many=True, read_only=True)
    certificate = CertificateSerializer(read_only=True)

    class Meta:
        model = EvalRun
        fields = ["id", "created_at", "stats", "results", "certificate"]


class EvalJobSerializer(serializers.ModelSerializer):
    """비동기 평가 잡. done 이면 `run` 에 전체 EvalRun(결과·인증서)을 임베드해 프론트가 그대로 소비."""
    run = EvalRunSerializer(read_only=True)

    class Meta:
        model = EvalJob
        fields = ["id", "status", "error", "created_at", "started_at", "finished_at", "run"]

from rest_framework import serializers

from .models import CoherenceCertificate, EvalRun, NodeResult


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

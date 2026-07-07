from rest_framework import serializers

from .models import BoundaryRecord, ModelCandidate, Proposal, Release


class BoundaryRecordSerializer(serializers.ModelSerializer):
    boundary = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    candidate = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = BoundaryRecord
        fields = ["boundary", "definition_type", "value_ma", "uncertainty",
                  "method", "candidate", "provenance_ref", "narrative"]


class ReleaseListSerializer(serializers.ModelSerializer):
    """Light entry for the Vault list — no heavy `records` payload."""
    authority = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    owner = serializers.SlugRelatedField(slug_field="username", read_only=True)
    source_graph = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    record_count = serializers.IntegerField(source="records.count", read_only=True)

    class Meta:
        model = Release
        fields = ["id", "version", "kind", "is_baseline", "owner", "source_graph",
                  "authority", "note", "created_at", "record_count"]


class ReleaseSerializer(serializers.ModelSerializer):
    authority = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    owner = serializers.SlugRelatedField(slug_field="username", read_only=True)
    source_graph = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    records = BoundaryRecordSerializer(many=True, read_only=True)
    clamps = serializers.SlugRelatedField(slug_field="slug", many=True, read_only=True)

    class Meta:
        model = Release
        fields = ["id", "version", "kind", "is_baseline", "owner", "source_graph",
                  "authority", "note", "created_at", "clamps", "records"]


class ModelCandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelCandidate
        fields = ["slug", "scope", "kind", "method", "provenance_ref", "note"]


class ProposalSerializer(serializers.ModelSerializer):
    graph = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    graph_id = serializers.IntegerField(source="graph.id", read_only=True)
    graph_name = serializers.CharField(source="graph.name", read_only=True)
    baseline = serializers.SlugRelatedField(slug_field="version", read_only=True)
    author = serializers.SlugRelatedField(slug_field="username", read_only=True)
    reviewer = serializers.SlugRelatedField(slug_field="username", read_only=True)
    result_release = serializers.SlugRelatedField(slug_field="version", read_only=True)

    class Meta:
        model = Proposal
        fields = ["id", "graph", "graph_id", "graph_name", "baseline", "author", "state",
                  "comment", "affected", "reviewer", "review_comment", "result_release",
                  "created_at", "updated_at"]

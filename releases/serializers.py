from rest_framework import serializers

from .models import BoundaryRecord, ModelCandidate, Release


class BoundaryRecordSerializer(serializers.ModelSerializer):
    boundary = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    candidate = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = BoundaryRecord
        fields = ["boundary", "definition_type", "value_ma", "uncertainty",
                  "method", "candidate", "provenance_ref", "narrative"]


class ReleaseSerializer(serializers.ModelSerializer):
    authority = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    records = BoundaryRecordSerializer(many=True, read_only=True)
    clamps = serializers.SlugRelatedField(slug_field="slug", many=True, read_only=True)

    class Meta:
        model = Release
        fields = ["id", "version", "authority", "note", "clamps", "records"]


class ModelCandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelCandidate
        fields = ["slug", "scope", "kind", "method", "provenance_ref", "note"]

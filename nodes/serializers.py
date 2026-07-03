"""nodes 읽기 API — 프론트 팔레트를 데이터로 구동."""
from rest_framework import serializers

from .models import NodeType, Port


class PortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Port
        fields = ["name", "direction", "datatype", "multiple", "order"]


class NodeTypeSerializer(serializers.ModelSerializer):
    ports = PortSerializer(many=True, read_only=True)

    class Meta:
        model = NodeType
        fields = ["slug", "name", "category", "description", "params_schema", "ports"]

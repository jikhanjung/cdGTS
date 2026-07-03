"""
graph 직렬화 — React Flow 왕복 계약 {nodes[], edges[], viewport}.

PUT 은 노드/엣지를 통째 교체(wholesale replace)하고 저장 전에 검증:
  포트 방향 정합 + 끊기지 않은 순환 금지(joint-inference/clamp 로만 절단 허용).
"""
from django.db import transaction
from rest_framework import serializers

from nodes.models import NodeType, Port

from .dag import find_unbroken_cycles
from .models import Edge, Gateway, Graph, NodeInstance


class NodeInstanceSerializer(serializers.ModelSerializer):
    node_type = serializers.SlugRelatedField(slug_field="slug", queryset=NodeType.objects.all())

    class Meta:
        model = NodeInstance
        fields = ["key", "node_type", "label", "params", "x", "y"]


class EdgeSerializer(serializers.Serializer):
    """엣지 끝점은 NodeInstance.key (React Flow 노드 id). FK 가 아니라 key 로 왕복."""
    source = serializers.CharField()          # NodeInstance.key
    source_port = serializers.CharField()
    target = serializers.CharField()
    target_port = serializers.CharField()
    kind = serializers.ChoiceField(choices=Edge.Kind.choices, default=Edge.Kind.DATA)

    def to_representation(self, instance):
        return {
            "source": instance.source.key,
            "source_port": instance.source_port,
            "target": instance.target.key,
            "target_port": instance.target_port,
            "kind": instance.kind,
        }


class GatewaySerializer(serializers.ModelSerializer):
    node = serializers.SlugRelatedField(slug_field="key", read_only=True)
    boundary = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = Gateway
        fields = ["slug", "name", "node", "output_port", "boundary"]


class GraphSerializer(serializers.ModelSerializer):
    nodes = NodeInstanceSerializer(many=True)
    edges = EdgeSerializer(many=True)
    gateways = GatewaySerializer(many=True, read_only=True)

    class Meta:
        model = Graph
        fields = ["id", "slug", "name", "status", "viewport", "nodes", "edges", "gateways"]
        # 토폴로지 PUT 은 nodes/edges/viewport 만 바꾼다 — slug/name 은 생성 시 고정.
        extra_kwargs = {"slug": {"required": False}, "name": {"required": False}}

    # --- 검증: 위상 정합을 저장 전에 (nodes/edges 를 함께 봐야 하므로 여기서) ---
    def validate(self, attrs):
        nodes = attrs.get("nodes", [])
        edges = attrs.get("edges", [])

        keys = [n["key"] for n in nodes]
        if len(keys) != len(set(keys)):
            raise serializers.ValidationError("노드 key 가 중복됨.")
        key_to_type = {n["key"]: n["node_type"] for n in nodes}

        # 타입별 포트 방향 인덱스 (한 번만 조회)
        type_ids = {t.id for t in key_to_type.values()}
        ports = Port.objects.filter(node_type_id__in=type_ids)
        out_ports, in_ports = {}, {}
        for p in ports:
            (out_ports if p.direction == Port.Direction.OUT else in_ports).setdefault(
                p.node_type_id, set()
            ).add(p.name)

        for e in edges:
            for endpoint in ("source", "target"):
                if e[endpoint] not in key_to_type:
                    raise serializers.ValidationError(
                        f"엣지가 없는 노드 key 를 참조: {e[endpoint]!r}"
                    )
            st = key_to_type[e["source"]]
            tt = key_to_type[e["target"]]
            if e["source_port"] not in out_ports.get(st.id, set()):
                raise serializers.ValidationError(
                    f"{st.slug} 에 출력 포트 {e['source_port']!r} 없음."
                )
            if e["target_port"] not in in_ports.get(tt.id, set()):
                raise serializers.ValidationError(
                    f"{tt.slug} 에 입력 포트 {e['target_port']!r} 없음."
                )

        # DAG 불변식: cycle-breaker(clamp/joint-inference) 로만 순환 절단 허용.
        breaker_slugs = {"joint-inference"}
        breaker_keys = {
            k for k, t in key_to_type.items()
            if t.category == NodeType.Category.CLAMP or t.slug in breaker_slugs
        }
        stuck = find_unbroken_cycles(keys, breaker_keys, [(e["source"], e["target"]) for e in edges])
        if stuck:
            raise serializers.ValidationError(
                f"끊기지 않은 순환(joint-inference/clamp 없이): {sorted(stuck)}"
            )
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        nodes = validated_data.pop("nodes", None)
        edges = validated_data.pop("edges", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if nodes is not None:
            self._replace_topology(instance, nodes, edges or [])
        return instance

    @transaction.atomic
    def create(self, validated_data):
        nodes = validated_data.pop("nodes", [])
        edges = validated_data.pop("edges", [])
        instance = Graph.objects.create(**validated_data)
        self._replace_topology(instance, nodes, edges)
        return instance

    def _replace_topology(self, graph, nodes, edges):
        graph.nodes.all().delete()          # cascade 로 edges 도 제거
        key_to_obj = {
            n["key"]: NodeInstance.objects.create(graph=graph, **n) for n in nodes
        }
        Edge.objects.bulk_create([
            Edge(
                graph=graph,
                source=key_to_obj[e["source"]], source_port=e["source_port"],
                target=key_to_obj[e["target"]], target_port=e["target_port"],
                kind=e.get("kind", Edge.Kind.DATA),
            )
            for e in edges
        ])

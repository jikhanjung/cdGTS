"""
graph 직렬화 — React Flow 왕복 계약 {nodes[], edges[], viewport}.

PUT 은 노드/엣지를 통째 교체(wholesale replace)하고 저장 전에 검증:
  포트 방향 정합 + 끊기지 않은 순환 금지(joint-inference/clamp 로만 절단 허용).
"""
from django.db import transaction
from rest_framework import serializers

from chrono.models import Unit
from nodes.models import NodeType, Port

from .dag import find_unbroken_cycles
from .models import Edge, Gateway, Graph, NodeGroup, NodeInstance


class NodeGroupSerializer(serializers.ModelSerializer):
    """노드그룹 = 편집/표현용 컨테이너(멤버십 + 접기 + 접힌 노드 위치 + 중첩 parent). 엔진 무관.
    kind=unit 이면 연대층서 구간(span) — unit(정본 단위)·lower/upper(경계 노드 key) 참조."""
    # 상위 그룹 key (없으면 null). write 는 문자열, read 는 to_representation 에서 parent.key.
    parent = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)
    # 정본 단위 slug (없으면 null).
    unit = serializers.SlugRelatedField(
        slug_field="slug", queryset=Unit.objects.all(), required=False, allow_null=True,
    )
    # bounding 경계 노드 key (없으면 null). write 문자열, read 는 to_representation.
    lower = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)
    upper = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)

    class Meta:
        model = NodeGroup
        fields = ["key", "name", "collapsed", "x", "y", "parent", "kind", "unit", "lower", "upper"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["parent"] = instance.parent.key if instance.parent_id else None
        data["lower"] = instance.lower.key if instance.lower_id else None
        data["upper"] = instance.upper.key if instance.upper_id else None
        return data


class NodeInstanceSerializer(serializers.ModelSerializer):
    node_type = serializers.SlugRelatedField(slug_field="slug", queryset=NodeType.objects.all())
    # 소속 그룹 key (없으면 null). write 는 문자열, read 는 to_representation 에서 group.key.
    group = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)

    class Meta:
        model = NodeInstance
        fields = ["key", "node_type", "nature", "label", "description", "params", "x", "y", "width", "group"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["group"] = instance.group.key if instance.group_id else None
        return data


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
    groups = NodeGroupSerializer(many=True, required=False)
    gateways = GatewaySerializer(many=True, read_only=True)
    owner = serializers.SlugRelatedField(slug_field="username", read_only=True)
    forked_from = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = Graph
        fields = ["id", "slug", "name", "description", "status", "owner", "forked_from", "viewport",
                  "nodes", "edges", "groups", "gateways"]
        # 토폴로지 PUT 은 nodes/edges/groups/viewport 만 바꾼다 — slug 는 생성 시 고정.
        # name/description 은 PATCH(부분 갱신)로 편집 — required=False 라 토폴로지 PUT 에도 안전.
        extra_kwargs = {"slug": {"required": False}, "name": {"required": False},
                        "description": {"required": False}}

    # --- 검증: 위상 정합을 저장 전에 (nodes/edges 를 함께 봐야 하므로 여기서) ---
    def validate(self, attrs):
        nodes = attrs.get("nodes", [])
        edges = attrs.get("edges", [])
        groups = attrs.get("groups", [])

        keys = [n["key"] for n in nodes]
        if len(keys) != len(set(keys)):
            raise serializers.ValidationError("Duplicate node key.")
        key_to_type = {n["key"]: n["node_type"] for n in nodes}

        # 그룹 정합: 노드가 참조하는 group key 는 groups 에 있어야 함.
        group_keys = {g["key"] for g in groups}
        if len(group_keys) != len(groups):
            raise serializers.ValidationError("Duplicate group key.")
        for n in nodes:
            if n.get("group") and n["group"] not in group_keys:
                raise serializers.ValidationError(f"Node {n['key']!r} references missing group {n['group']!r}.")
        # span 그룹의 lower/upper 는 존재하는 노드 key 여야 함.
        node_keys = set(keys)
        for g in groups:
            for side in ("lower", "upper"):
                ref = g.get(side)
                if ref and ref not in node_keys:
                    raise serializers.ValidationError(
                        f"Group {g['key']!r} {side} references missing node {ref!r}."
                    )
        # 중첩: parent 는 존재하는 그룹이어야 하고 자기 자신/순환이면 안 됨.
        for g in groups:
            pk = g.get("parent")
            if pk and pk not in group_keys:
                raise serializers.ValidationError(f"Group {g['key']!r} references missing parent group {pk!r}.")
            if pk == g["key"]:
                raise serializers.ValidationError(f"Group {g['key']!r} references itself as parent.")
        parent_of = {g["key"]: g.get("parent") for g in groups}
        for start in parent_of:                     # 순환 방지
            seen, cur = set(), start
            while cur is not None:
                if cur in seen:
                    raise serializers.ValidationError(f"Cyclic group parent reference ({start!r}).")
                seen.add(cur)
                cur = parent_of.get(cur)

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
                        f"Edge references missing node key: {e[endpoint]!r}"
                    )
            # order/cite edge 는 데이터 포트가 아니라 제약·주석 연결 — 데이터 포트 방향 검증에서 제외.
            if e.get("kind") in Edge.NON_DATA_KINDS:
                continue
            st = key_to_type[e["source"]]
            tt = key_to_type[e["target"]]
            if e["source_port"] not in out_ports.get(st.id, set()):
                raise serializers.ValidationError(
                    f"{st.slug} has no output port {e['source_port']!r}."
                )
            if e["target_port"] not in in_ports.get(tt.id, set()):
                raise serializers.ValidationError(
                    f"{tt.slug} has no input port {e['target_port']!r}."
                )

        # DAG 불변식: cycle-breaker(clamp/joint-inference) 로만 순환 절단 허용.
        # order edge 는 데이터 흐름이 아니라 제약 — 데이터 DAG 사이클 판정에서 제외.
        breaker_slugs = {"joint-inference"}
        breaker_keys = {
            k for k, t in key_to_type.items()
            if t.category == NodeType.Category.CLAMP or t.slug in breaker_slugs
        }
        data_edges = [(e["source"], e["target"]) for e in edges if e.get("kind") not in Edge.NON_DATA_KINDS]
        stuck = find_unbroken_cycles(keys, breaker_keys, data_edges)
        if stuck:
            raise serializers.ValidationError(
                f"Unbroken cycle (no joint-inference/clamp): {sorted(stuck)}"
            )
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        nodes = validated_data.pop("nodes", None)
        edges = validated_data.pop("edges", None)
        groups = validated_data.pop("groups", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if nodes is not None:
            self._replace_topology(instance, nodes, edges or [], groups or [])
        return instance

    @transaction.atomic
    def create(self, validated_data):
        nodes = validated_data.pop("nodes", [])
        edges = validated_data.pop("edges", [])
        groups = validated_data.pop("groups", [])
        instance = Graph.objects.create(**validated_data)
        self._replace_topology(instance, nodes, edges, groups)
        return instance

    def _replace_topology(self, graph, nodes, edges, groups):
        graph.nodes.all().delete()          # cascade 로 edges 도 제거
        graph.groups.all().delete()
        key_to_group = {}
        parent_of = {}
        bound_of = {}                       # group key → (lower node key, upper node key)
        for g in groups:                    # 1패스: parent·lower·upper 빼고 생성
            fields = dict(g)
            parent_of[fields["key"]] = fields.pop("parent", None)
            bound_of[fields["key"]] = (fields.pop("lower", None), fields.pop("upper", None))
            key_to_group[fields["key"]] = NodeGroup.objects.create(graph=graph, **fields)
        for k, pk in parent_of.items():     # 2패스: 중첩 링크
            if pk and pk in key_to_group:
                key_to_group[k].parent = key_to_group[pk]
                key_to_group[k].save(update_fields=["parent"])
        key_to_obj = {}
        for n in nodes:
            fields = dict(n)
            gkey = fields.pop("group", None)
            obj = NodeInstance.objects.create(graph=graph, **fields)
            if gkey and gkey in key_to_group:
                obj.group = key_to_group[gkey]
                obj.save(update_fields=["group"])
            key_to_obj[n["key"]] = obj
        for gkey, (lo, up) in bound_of.items():   # 3패스: span 그룹 → 경계 노드 참조(노드 생성 후)
            grp, dirty = key_to_group[gkey], []
            if lo and lo in key_to_obj:
                grp.lower = key_to_obj[lo]; dirty.append("lower")
            if up and up in key_to_obj:
                grp.upper = key_to_obj[up]; dirty.append("upper")
            if dirty:
                grp.save(update_fields=dirty)
        Edge.objects.bulk_create([
            Edge(
                graph=graph,
                source=key_to_obj[e["source"]], source_port=e["source_port"],
                target=key_to_obj[e["target"]], target_port=e["target_port"],
                kind=e.get("kind", Edge.Kind.DATA),
            )
            for e in edges
        ])

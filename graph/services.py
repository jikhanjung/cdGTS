"""Graph fork (P05.3) — deep-clone a graph into a new sandbox the user owns."""
from collections import defaultdict, deque

from django.db import transaction
from django.utils.text import slugify

from .models import Edge, Gateway, Graph, NodeGroup, NodeInstance


def graph_bibliography(graph):
    """
    Which registry references feed each boundary — the bake→bibliography seam.

    A `reference` node cites a data/model node via a `cite` edge. It **contributes** to a gateway's
    boundary when its cited node lies in the upstream data-flow cone of that gateway's node (walk data
    edges backward). `order`/`cite` edges are not data flow, so they don't propagate the cone.

    Returns {"by_boundary": {boundary_slug: [ref_slug, ...]}, "all": [ref_slug, ...] present in the graph}.
    """
    insts = list(graph.nodes.select_related("node_type"))
    ref_slug_of = {n.key: (n.params or {}).get("reference")
                   for n in insts if n.node_type.slug == "reference"}

    back = defaultdict(list)          # target key -> [source keys]  (data-flow edges only)
    cited_by = defaultdict(list)      # cited node key -> [reference node keys]
    for e in graph.edges.select_related("source", "target"):
        if e.kind == Edge.Kind.CITE:
            cited_by[e.target.key].append(e.source.key)
        elif e.kind not in Edge.NON_DATA_KINDS:
            back[e.target.key].append(e.source.key)

    def upstream(start):              # data-flow cone (incl. start)
        seen, q = {start}, deque([start])
        while q:
            for s in back.get(q.popleft(), []):
                if s not in seen:
                    seen.add(s)
                    q.append(s)
        return seen

    by_boundary = {}
    for gw in graph.gateways.select_related("boundary", "node"):
        if gw.boundary is None:
            continue
        refs = []
        for node_key in upstream(gw.node.key):
            for rk in cited_by.get(node_key, []):
                slug = ref_slug_of.get(rk)
                if slug and slug not in refs:
                    refs.append(slug)
        by_boundary[gw.boundary.slug] = refs

    every = sorted({s for s in ref_slug_of.values() if s})
    return {"by_boundary": by_boundary, "all": every}


def _unique_slug(base):
    slug = base
    n = 1
    while Graph.objects.filter(slug=slug).exists():
        n += 1
        slug = f"{base}-{n}"
    return slug


@transaction.atomic
def fork_graph(source, user, name=None):
    """
    Clone source's topology (groups · nodes · edges · gateways) into a new sandbox graph owned by `user`.
    Node/group keys are preserved (unique per graph), so edges/gateways re-link by key. Returns the new Graph.
    `name` overrides the default "<source> (fork)".
    """
    fork = Graph.objects.create(
        slug=_unique_slug(f"{source.slug}-fork"),
        name=(name or "").strip() or f"{source.name} (fork)",
        description=source.description,
        owner=user,
        status=Graph.Status.SANDBOX,
        forked_from=source,
        viewport=source.viewport,
    )

    # groups first (parent/lower/upper wired after nodes exist)
    group_map = {}
    for g in source.groups.all():
        group_map[g.key] = NodeGroup.objects.create(
            graph=fork, key=g.key, name=g.name, collapsed=g.collapsed,
            x=g.x, y=g.y, kind=g.kind, unit=g.unit,
        )
    for g in source.groups.all():
        if g.parent_id:
            group_map[g.key].parent = group_map[g.parent.key]
            group_map[g.key].save(update_fields=["parent"])

    # nodes (map old key → new NodeInstance)
    node_map = {}
    for n in source.nodes.select_related("group"):
        node_map[n.key] = NodeInstance.objects.create(
            graph=fork, key=n.key, node_type=n.node_type, nature=n.nature,
            label=n.label, description=n.description, params=n.params,
            x=n.x, y=n.y, width=n.width,
            group=group_map[n.group.key] if n.group_id else None,
        )

    # span groups: lower/upper boundary node refs (now that nodes exist)
    for g in source.groups.select_related("lower", "upper"):
        dirty = []
        if g.lower_id:
            group_map[g.key].lower = node_map[g.lower.key]; dirty.append("lower")
        if g.upper_id:
            group_map[g.key].upper = node_map[g.upper.key]; dirty.append("upper")
        if dirty:
            group_map[g.key].save(update_fields=dirty)

    Edge.objects.bulk_create([
        Edge(graph=fork,
             source=node_map[e.source.key], source_port=e.source_port,
             target=node_map[e.target.key], target_port=e.target_port, kind=e.kind)
        for e in source.edges.select_related("source", "target")
    ])

    for gw in source.gateways.select_related("node", "boundary"):
        Gateway.objects.create(
            graph=fork, slug=gw.slug, name=gw.name,
            node=node_map[gw.node.key], output_port=gw.output_port, boundary=gw.boundary,
        )

    return fork

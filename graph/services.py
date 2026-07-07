"""Graph fork (P05.3) — deep-clone a graph into a new sandbox the user owns."""
from django.db import transaction
from django.utils.text import slugify

from .models import Edge, Gateway, Graph, NodeGroup, NodeInstance


def _unique_slug(base):
    slug = base
    n = 1
    while Graph.objects.filter(slug=slug).exists():
        n += 1
        slug = f"{base}-{n}"
    return slug


@transaction.atomic
def fork_graph(source, user):
    """
    Clone source's topology (groups · nodes · edges · gateways) into a new sandbox graph owned by `user`.
    Node/group keys are preserved (unique per graph), so edges/gateways re-link by key. Returns the new Graph.
    """
    fork = Graph.objects.create(
        slug=_unique_slug(f"{source.slug}-fork"),
        name=f"{source.name} (fork)",
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

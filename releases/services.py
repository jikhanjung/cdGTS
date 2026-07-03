"""
bake — 릴리스의 selection 을 BoundaryRecord 스냅샷으로 얼린다 (ICC bake).
diff — 두 릴리스 간 **값 diff** 와 **토폴로지 diff**(직교 축)를 낸다.

토폴로지 diff 는 값 diff 와 별개 축: 경계 추가/삭제 + retype(GSSA↔GSSP) 같은 *배선* 변화.
값 diff 는 같은 경계의 value_ma 변화. (topology-diff.md)
"""
from .models import BoundaryRecord


def bake_release(release):
    """selection 을 돌며 BoundaryRecord 를 (재)생성. 반환: 레코드 수."""
    release.records.all().delete()
    rows = []
    for sel in release.selections.select_related("boundary", "candidate"):
        output = sel.candidate.outputs.filter(boundary=sel.boundary).first()
        dist = output.distribution if output else None
        rows.append(BoundaryRecord(
            release=release,
            boundary=sel.boundary,
            definition_type=sel.boundary.definition_type or "",
            value_ma=(dist or {}).get("value_ma") if dist else None,
            uncertainty=dist,
            method=sel.candidate.method,
            candidate=sel.candidate,
            provenance_ref=sel.candidate.provenance_ref,
        ))
    BoundaryRecord.objects.bulk_create(rows)
    return len(rows)


def diff_releases(rel_a, rel_b):
    """rel_a → rel_b 로의 변화. value_diff 와 topology_diff 를 분리해 반환."""
    a = {r.boundary.slug: r for r in rel_a.records.select_related("boundary")}
    b = {r.boundary.slug: r for r in rel_b.records.select_related("boundary")}
    shared = a.keys() & b.keys()

    value_diff = []
    topology_diff = []

    for slug in sorted(shared):
        ra, rb = a[slug], b[slug]
        if (ra.definition_type or "") != (rb.definition_type or ""):
            topology_diff.append({
                "boundary": slug, "op": "retype",
                "from": ra.definition_type, "to": rb.definition_type,
            })
        if ra.value_ma != rb.value_ma:
            value_diff.append({
                "boundary": slug, "from": ra.value_ma, "to": rb.value_ma,
                "delta": None if (ra.value_ma is None or rb.value_ma is None)
                         else round(rb.value_ma - ra.value_ma, 6),
            })

    for slug in sorted(b.keys() - a.keys()):
        topology_diff.append({"boundary": slug, "op": "added"})
    for slug in sorted(a.keys() - b.keys()):
        topology_diff.append({"boundary": slug, "op": "removed"})

    return {
        "from": rel_a.version,
        "to": rel_b.version,
        "value_diff": value_diff,
        "topology_diff": topology_diff,
    }

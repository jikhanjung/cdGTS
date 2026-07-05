"""
bake — 릴리스의 selection 을 BoundaryRecord 스냅샷으로 얼린다 (ICC bake).
diff — 두 릴리스 간 **값 diff** 와 **토폴로지 diff**(직교 축)를 낸다.

토폴로지 diff 는 값 diff 와 별개 축: 경계 추가/삭제 + retype(GSSA↔GSSP) 같은 *배선* 변화.
값 diff 는 같은 경계의 value_ma 변화. (topology-diff.md)
"""
from .models import BoundaryRecord


def bake_graph(graph):
    """
    그래프를 평가해 **게이트웨이 출력을 ICC 테이블로 얼린다** (graph → ICC bake).
    각 게이트웨이(경계 지정)의 노드 결과 분포 → BoundaryRecord. 릴리스는 그래프당 하나
    (version=`graph:<slug>`)로 재사용 → 재-bake 는 레코드 갱신. 릴리스 diff 도 그대로 적용됨.
    반환: (release, 레코드 수).
    """
    from engine.evaluate import evaluate_graph
    from .models import Release

    run = evaluate_graph(graph)
    results = {r.node_key: r for r in run.results.all()}

    release, _ = Release.objects.get_or_create(
        version=f"graph:{graph.slug}",
        defaults={"note": f"'{graph.name}' 그래프 bake (자동 생성 ICC 스냅샷)"},
    )
    release.records.all().delete()
    rows = []
    for gw in graph.gateways.select_related("boundary", "node"):
        if gw.boundary is None:
            continue
        r = results.get(gw.node.key)
        dist = r.distribution if r else None
        rows.append(BoundaryRecord(
            release=release,
            boundary=gw.boundary,
            definition_type=gw.boundary.definition_type or "",
            value_ma=(dist or {}).get("value_ma") if dist else None,
            uncertainty=dist,
            provenance_ref=f"{graph.slug}::{gw.node.key}",
        ))
    BoundaryRecord.objects.bulk_create(rows)
    return release, len(rows)


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


def _narrate_record(rec, unit):
    """레코드 하나 → 결정적 서술(사실 창작 없이 구조화 필드만 렌더). 이중 명명(Period/System) 사용."""
    if unit is not None:
        name, geo, chrono = unit.name, unit.geochronologic_term, unit.chronostratigraphic_term
    else:
        name, geo, chrono = rec.boundary.slug, "", ""
    dt = (rec.definition_type or "").upper()
    val = rec.value_ma
    moe = ((rec.uncertainty or {}).get("budget") or {}).get("analytical") if rec.uncertainty else None
    if val is None:
        val_txt = "연대 미상"
    elif moe:
        val_txt = f"{val:g} ± {moe:g} Ma"
    else:
        val_txt = f"{val:g} Ma"
    if dt == "GSSP":
        defn, lead = "GSSP(하부 경계 층서형 단면·지점)으로 정의되며", "파생 연대는"
        mtxt = f"({rec.get_method_display()})" if rec.method else ""
    elif dt == "GSSA":
        defn, lead, mtxt = "GSSA(약속된 표준 연대)로 정의되며", "약속값은", ""
    else:
        defn, lead, mtxt = "정의 방식이 기재되지 않았으며", "연대는", ""
    head = f"{name} {geo}".strip()
    base = f"{name} {chrono}의 바닥" if chrono else "하부 경계"
    prov = f" 근거: {rec.provenance_ref}." if rec.provenance_ref else ""
    return f"{head}의 하부 경계({base})는 {defn}, {lead} {val_txt}{mtxt}이다.{prov}"


def narrate_release(release):
    """bake 의 짝 — 릴리스를 '서술한 책'으로. 각 레코드의 narrative 를 결정적으로 채우고(저장),
    rank(Eon~Age) 별 · 오래된→젊은 순으로 조립한 문서(sections)를 반환."""
    from chrono.models import Unit
    if not release.records.exists():
        bake_release(release)
    records = list(release.records.select_related("boundary", "candidate"))
    slugs = [r.boundary.slug[5:] for r in records if r.boundary.slug.startswith("base-")]
    units = {u.slug: u for u in Unit.objects.filter(slug__in=slugs)}

    by_rank = {}
    for r in records:
        bs = r.boundary.slug
        u = units.get(bs[5:] if bs.startswith("base-") else bs)
        r.narrative = _narrate_record(r, u)
        by_rank.setdefault(u.rank if u else 0, []).append((r, u))
    BoundaryRecord.objects.bulk_update(records, ["narrative"])

    GEO = {1: "Eon", 2: "Era", 3: "Period", 4: "Epoch", 5: "Age"}
    sections = []
    for rn in (1, 2, 3, 4, 5):
        rows = by_rank.get(rn, [])
        rows.sort(key=lambda z: (z[0].value_ma if z[0].value_ma is not None else 0), reverse=True)
        if not rows:
            continue
        sections.append({"rank": GEO[rn], "rank_n": rn, "entries": [
            {"boundary": r.boundary.slug, "name": (u.name if u else r.boundary.slug),
             "value_ma": r.value_ma, "definition_type": r.definition_type, "narrative": r.narrative}
            for r, u in rows]})
    return sections


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

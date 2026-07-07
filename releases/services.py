"""
bake — 릴리스의 selection 을 BoundaryRecord 스냅샷으로 얼린다 (ICC bake).
diff — 두 릴리스 간 **값 diff** 와 **토폴로지 diff**(직교 축)를 낸다.

토폴로지 diff 는 값 diff 와 별개 축: 경계 추가/삭제 + retype(GSSA↔GSSP) 같은 *배선* 변화.
값 diff 는 같은 경계의 value_ma 변화. (topology-diff.md)
"""
from .models import BoundaryRecord


def _write_graph_records(graph, release):
    """Evaluate `graph` and (re)write its gateway outputs as this release's BoundaryRecords. Returns count."""
    from engine.evaluate import evaluate_graph

    run = evaluate_graph(graph)
    results = {r.node_key: r for r in run.results.all()}
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
    return len(rows)


def next_release_version(when=None, user=None):
    """
    Suggested immutable bake name: GeologicTimeScale.Release[.<user>].YYYYMMDD.NN
    (NN = that user·day's zero-padded sequence). The <user> segment appears once a user is known (multiuser).
    """
    from django.utils import timezone
    from django.utils.text import slugify
    from .models import Release

    day = (when or timezone.now()).strftime("%Y%m%d")
    seg = f"{slugify(user.get_username())}." if user is not None else ""
    prefix = f"GeologicTimeScale.Release.{seg}{day}."
    used = Release.objects.filter(version__startswith=prefix).values_list("version", flat=True)
    n = 0
    for v in used:
        try:
            n = max(n, int(v[len(prefix):]))
        except (ValueError, IndexError):
            pass
    return f"{prefix}{n + 1:02d}"


def snapshot_graph(graph, label=None, user=None):
    """
    Bake action: freeze the graph's current gateway outputs into a **new immutable Release** (kind=bake) kept in the Vault.
    Unlike the scratch bake_graph, this never overwrites — each call is a distinct, named, provenance-tagged artifact.
    `user` (when set) owns the release and adds a `<user>` segment to the auto name. Returns (release, record count).
    """
    from .models import Release

    version = (label or "").strip() or next_release_version(user=user)
    release = Release.objects.create(
        version=version,
        kind=Release.Kind.BAKE,
        source_graph=graph,
        owner=user if (user is not None and user.is_authenticated) else None,
        note=f"Bake of graph '{graph.name}'",
    )
    n = _write_graph_records(graph, release)
    return release, n


def bake_graph(graph):
    """
    Scratch re-bake for Science-CI verify: a single reusable `graph:<slug>` release (kind=transient, hidden from Vault),
    overwritten each call. For a kept artifact use snapshot_graph. Returns (release, record count).
    """
    from .models import Release

    release, _ = Release.objects.get_or_create(
        version=f"graph:{graph.slug}",
        defaults={"kind": Release.Kind.TRANSIENT, "source_graph": graph,
                  "note": f"Scratch bake of graph '{graph.name}' (Science-CI verify)"},
    )
    if release.kind != Release.Kind.TRANSIENT or release.source_graph_id != graph.id:
        release.kind = Release.Kind.TRANSIENT
        release.source_graph = graph
        release.save(update_fields=["kind", "source_graph"])
    n = _write_graph_records(graph, release)
    return release, n


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
    """One record → deterministic prose (renders structured fields only, no invented facts). Uses dual naming (Period/System)."""
    if unit is not None:
        name, geo, chrono = unit.name, unit.geochronologic_term, unit.chronostratigraphic_term
    else:
        name, geo, chrono = rec.boundary.slug, "", ""
    dt = (rec.definition_type or "").upper()
    val = rec.value_ma
    moe = ((rec.uncertainty or {}).get("budget") or {}).get("analytical") if rec.uncertainty else None
    if val is None:
        val_txt = "an unknown age"
    elif moe:
        val_txt = f"{val:g} ± {moe:g} Ma"
    else:
        val_txt = f"{val:g} Ma"
    if dt == "GSSP":
        defn, lead = "is defined by a GSSP (Global Boundary Stratotype Section and Point)", "its derived age is"
        mtxt = f" ({rec.get_method_display()})" if rec.method else ""
    elif dt == "GSSA":
        defn, lead, mtxt = "is defined by a GSSA (Global Standard Stratigraphic Age)", "its agreed value is", ""
    else:
        defn, lead, mtxt = "has no stated definition method", "its age is", ""
    head = f"{name} {geo}".strip()
    base = f"base of the {name} {chrono}" if chrono else "lower boundary"
    prov = f" Source: {rec.provenance_ref}." if rec.provenance_ref else ""
    return f"The lower boundary of {head} ({base}) {defn}, and {lead} {val_txt}{mtxt}.{prov}"


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

    GEO = {1: "Eon", 2: "Era", 3: "Period", 4: "Subperiod", 5: "Epoch", 6: "Age"}
    sections = []
    for rn in (1, 2, 3, 4, 5, 6):
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

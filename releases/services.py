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


def _next_seq(prefix):
    """`<prefix>NN` where NN is the next zero-padded sequence among existing versions with that prefix."""
    from .models import Release
    used = Release.objects.filter(version__startswith=prefix).values_list("version", flat=True)
    n = 0
    for v in used:
        try:
            n = max(n, int(v[len(prefix):]))
        except (ValueError, IndexError):
            pass
    return f"{prefix}{n + 1:02d}"


def _day(when=None):
    from django.utils import timezone
    return (when or timezone.now()).strftime("%Y%m%d")


def next_release_version(when=None, user=None):
    """Suggested immutable bake name: GeologicTimeScale.Release[.<user>].YYYYMMDD.NN (per user·day sequence)."""
    from django.utils.text import slugify
    seg = f"{slugify(user.get_username())}." if user is not None else ""
    return _next_seq(f"GeologicTimeScale.Release.{seg}{_day(when)}.")


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


def _diff_summary(d, baked):
    deltas = [x["delta"] for x in d["value_diff"] if x["delta"] is not None]
    td = d["topology_diff"]
    return {
        "baked": baked,
        "moved": len(d["value_diff"]),
        "max_abs_delta": round(max((abs(x) for x in deltas), default=0.0), 4),
        "added": sum(1 for t in td if t["op"] == "added"),
        "removed": sum(1 for t in td if t["op"] == "removed"),
        "retyped": sum(1 for t in td if t["op"] == "retype"),
    }


def diff_graph_vs_release(graph, baseline):
    """Scratch-bake `graph` and diff it against `baseline` (from=baseline → to=graph). Returns the diff dict + summary."""
    release, n = bake_graph(graph)
    d = diff_releases(baseline, release)
    d["summary"] = _diff_summary(d, n)
    d["baseline"] = baseline.version
    return d


def verify_graph(graph):
    """Science-CI: diff the graph against the current published baseline. Returns (baseline, diff) or (None, None)."""
    from .models import Release
    baseline = Release.objects.filter(is_baseline=True).order_by("version").first()
    if baseline is None:
        return None, None
    return baseline, diff_graph_vs_release(graph, baseline)


def affected_boundaries(diff):
    """Boundary slugs a diff touches (moved value or topology change) — the seam for interval-scoped ratify."""
    return sorted(
        {x["boundary"] for x in diff["value_diff"]} | {t["boundary"] for t in diff["topology_diff"]}
    )


def next_published_version(when=None):
    """Auto name for a ratified public release: GeologicTimeScale.Published.YYYYMMDD.NN."""
    return _next_seq(f"GeologicTimeScale.Published.{_day(when)}.")


def publish_graph(graph):
    """Ratify: freeze the graph into a new **published** Release that becomes the sole baseline. Returns (release, n)."""
    from django.db import transaction
    from .models import Release
    with transaction.atomic():
        Release.objects.filter(is_baseline=True).update(is_baseline=False)
        release = Release.objects.create(
            version=next_published_version(), kind=Release.Kind.PUBLISHED, is_baseline=True,
            source_graph=graph, note=f"Ratified from '{graph.name}'",
        )
        n = _write_graph_records(graph, release)
    return release, n


def propose_graph(graph, user, comment=""):
    """Owner proposes a sandbox graph against the baseline (sandbox→proposed). Returns (proposal, diff)."""
    from graph.models import Graph
    from .models import Proposal
    baseline, diff = verify_graph(graph)
    if baseline is None:
        raise ValueError("No published baseline (is_baseline) to propose against.")
    proposal = Proposal.objects.create(
        graph=graph, baseline=baseline, author=user if user.is_authenticated else None,
        comment=comment, affected=affected_boundaries(diff),
    )
    graph.status = Graph.Status.PROPOSED
    graph.save(update_fields=["status"])
    return proposal, diff


def ratify_proposal(proposal, reviewer, comment=""):
    """Accept a proposal → publish a new baseline Release, graph→ratified, proposal→merged. Returns the release."""
    from graph.models import Graph
    from .models import Proposal
    release, _ = publish_graph(proposal.graph)
    proposal.graph.status = Graph.Status.RATIFIED
    proposal.graph.save(update_fields=["status"])
    proposal.state = Proposal.State.MERGED
    proposal.reviewer = reviewer
    proposal.review_comment = comment
    proposal.result_release = release
    proposal.save(update_fields=["state", "reviewer", "review_comment", "result_release", "updated_at"])
    return release


def reject_proposal(proposal, reviewer, comment=""):
    """Reject a proposal → graph back to sandbox, proposal→rejected."""
    from graph.models import Graph
    from .models import Proposal
    proposal.graph.status = Graph.Status.SANDBOX
    proposal.graph.save(update_fields=["status"])
    proposal.state = Proposal.State.REJECTED
    proposal.reviewer = reviewer
    proposal.review_comment = comment
    proposal.save(update_fields=["state", "reviewer", "review_comment", "updated_at"])


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


# --- P05.5: sandbox = a baseline + per-boundary candidate overrides (Arc B seam) ---

def next_sandbox_version(user, when=None):
    from django.utils.text import slugify
    seg = f"{slugify(user.get_username())}." if user is not None else ""
    return _next_seq(f"GeologicTimeScale.Sandbox.{seg}{_day(when)}.")


def create_sandbox_release(baseline, user):
    """Fork a published baseline into a private sandbox Release: copy its selections, then bake (identical to start)."""
    from .models import Release, Selection
    sandbox = Release.objects.create(
        version=next_sandbox_version(user), kind=Release.Kind.SANDBOX,
        owner=user if (user is not None and user.is_authenticated) else None,
        base=baseline, note=f"Sandbox of {baseline.version}",
    )
    Selection.objects.bulk_create([
        Selection(release=sandbox, boundary=s.boundary, candidate=s.candidate)
        for s in baseline.selections.select_related("boundary", "candidate")
    ])
    bake_release(sandbox)
    return sandbox


def set_override(sandbox, boundary_slug, candidate_slug):
    """Override (or reset, candidate_slug=None → baseline's pick) one boundary's selected candidate, then re-bake."""
    from chrono.models import Boundary
    from .models import ModelCandidate, Selection
    boundary = Boundary.objects.get(slug=boundary_slug)
    sel = sandbox.selections.filter(boundary=boundary).first()

    if candidate_slug is None:                                   # reset to baseline
        base_sel = sandbox.base.selections.filter(boundary=boundary).first() if sandbox.base_id else None
        if base_sel is None:
            if sel:
                sel.delete()
        elif sel:
            sel.candidate = base_sel.candidate
            sel.save(update_fields=["candidate"])
        else:
            Selection.objects.create(release=sandbox, boundary=boundary, candidate=base_sel.candidate)
    else:
        candidate = ModelCandidate.objects.get(slug=candidate_slug)
        if not candidate.outputs.filter(boundary=boundary).exists():
            raise ValueError(f"{candidate_slug} has no output for {boundary_slug}.")
        if sel:
            sel.candidate = candidate
            sel.save(update_fields=["candidate"])
        else:
            Selection.objects.create(release=sandbox, boundary=boundary, candidate=candidate)

    bake_release(sandbox)
    return sandbox


def overridable_candidates(release):
    """Boundaries with >1 competing candidate → override options + the release's current pick + baseline's pick."""
    from django.db.models import Count
    from .models import CandidateOutput
    slugs = [m["boundary__slug"] for m in
             CandidateOutput.objects.values("boundary__slug").annotate(n=Count("candidate")).filter(n__gt=1)]
    cur = {s.boundary.slug: s.candidate.slug
           for s in release.selections.select_related("boundary", "candidate")}
    base = {}
    if release.base_id:
        base = {s.boundary.slug: s.candidate.slug
                for s in release.base.selections.select_related("boundary", "candidate")}
    rows = []
    for slug in sorted(slugs):
        options = sorted(set(CandidateOutput.objects.filter(boundary__slug=slug)
                             .values_list("candidate__slug", flat=True)))
        rows.append({"boundary": slug, "options": options,
                     "selected": cur.get(slug), "baseline": base.get(slug)})
    return rows


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

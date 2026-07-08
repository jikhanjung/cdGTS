import math

from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from graph.models import Graph

from accounts.permissions import can_ratify
from graph.permissions import visible_graphs

from .models import Proposal, Release
from .permissions import can_write_release, visible_releases
from .serializers import ProposalSerializer, ReleaseListSerializer, ReleaseSerializer
from .services import (
    bake_release, create_sandbox_release, diff_graph_vs_release, diff_releases, narrate_release,
    overridable_candidates, propose_graph, ratify_proposal, reconcile_release, reject_proposal,
    set_override, snapshot_graph, verify_clamps, verify_graph,
)


class ReleaseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    릴리스 조회 + bake + diff.
      GET  /api/releases/                — 목록
      GET  /api/releases/{id}/           — 레코드 포함 상세
      POST /api/releases/{id}/bake/      — selection → BoundaryRecord 스냅샷
      GET  /api/releases/diff/?a=&b=     — 두 릴리스 값/토폴로지 diff
    """
    queryset = Release.objects.prefetch_related("records__boundary", "records__candidate", "clamps")
    serializer_class = ReleaseSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Vault = kept artifacts; hides the scratch verify release (transient) and others' private sandboxes.
        qs = visible_releases(self.request.user).prefetch_related(
            "records__boundary", "records__candidate", "clamps")
        kind = self.request.query_params.get("kind")
        return qs.filter(kind=kind) if kind else qs

    def get_serializer_class(self):
        return ReleaseListSerializer if self.action == "list" else ReleaseSerializer

    @action(detail=True, methods=["post"])
    def bake(self, request, pk=None):
        release = self.get_object()                       # visible-only
        if not can_write_release(request.user, release):
            return Response({"detail": "Only the owner (or staff) can re-bake this release."}, status=403)
        n = bake_release(release)
        release = self.get_queryset().get(pk=release.pk)
        return Response({"baked": n, "release": ReleaseSerializer(release).data})

    @action(detail=False, methods=["get"])
    def diff(self, request):
        vis = visible_releases(request.user)              # can only diff releases you can see
        a = get_object_or_404(vis, pk=request.query_params.get("a"))
        b = get_object_or_404(vis, pk=request.query_params.get("b"))
        return Response(diff_releases(a, b))

    # --- P05.5 sandbox overrides ---
    @action(detail=True, methods=["post"])
    def sandbox(self, request, pk=None):
        """Fork this published release into a private sandbox the caller owns (baseline + overrides)."""
        if not request.user.is_authenticated:
            return Response({"detail": "Sign in to sandbox a release."}, status=401)
        baseline = self.get_object()
        if baseline.kind == Release.Kind.SANDBOX:
            return Response({"detail": "Sandbox a published/baseline release, not another sandbox."}, status=400)
        sandbox = create_sandbox_release(baseline, request.user)
        return Response(ReleaseSerializer(self.get_queryset().get(pk=sandbox.pk)).data, status=201)

    @action(detail=True, methods=["get"])
    def candidates(self, request, pk=None):
        """Overridable boundaries (>1 competing candidate) + options + current/baseline pick."""
        return Response({"boundaries": overridable_candidates(self.get_object())})

    @action(detail=True, methods=["post"])
    def override(self, request, pk=None):
        """Set/reset one boundary's candidate on your sandbox, then re-bake. body {boundary, candidate|null}."""
        release = self.get_object()
        if release.kind != Release.Kind.SANDBOX:
            return Response({"detail": "Overrides apply to sandbox releases only."}, status=400)
        if not (request.user.is_authenticated and (request.user.is_staff or release.owner_id == request.user.id)):
            return Response({"detail": "Only the sandbox owner can override it."}, status=403)
        boundary = request.data.get("boundary")
        if not boundary:
            return Response({"detail": "boundary is required."}, status=400)
        try:
            set_override(release, boundary, request.data.get("candidate"))
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(ReleaseSerializer(self.get_queryset().get(pk=release.pk)).data)

    # --- P06.3 authored clamps (L3a verify / L3b reconcile) ---
    @action(detail=True, methods=["get"])
    def clamps(self, request, pk=None):
        """이 릴리스의 authored clamp 목록 + L3a 검사(값이 clamp 를 지키는지, 값 불변)."""
        release = self.get_object()
        return Response({
            "clamps": [{"slug": c.slug, "kind": c.kind, "boundary": c.target_boundary.slug if c.target_boundary_id else None,
                        "owner": c.owner.slug, "value": c.value, "rationale": c.rationale}
                       for c in release.clamps.select_related("target_boundary", "owner")],
            "violations": verify_clamps(release),
        })

    @action(detail=True, methods=["post"])
    def reconcile(self, request, pk=None):
        """L3b — authored clamp 을 records 에 적용(값 이동 = GTS 계약). 소유자/staff 만."""
        release = self.get_object()
        if not can_write_release(request.user, release):
            return Response({"detail": "Only the owner (or staff) can reconcile this release."}, status=403)
        changed, conflicts = reconcile_release(release)
        return Response({"changed": changed, "conflicts": conflicts,
                         "release": ReleaseSerializer(self.get_queryset().get(pk=release.pk)).data})


class GraphBakeView(APIView):
    """
    POST /api/graphs/{id}/bake/ — Bake 액션: 그래프를 평가해 게이트웨이 출력을 **새 불변 Release(kind=bake)**
    로 얼려 Vault 에 보관(덮어쓰지 않음). body `label` 있으면 그 이름, 없으면
    `GeologicTimeScale.Release.YYYYMMDD.NN` 자동 제안. 반환: {baked, release(records 포함)}.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        # Editable default name for the Bake dialog (includes the <user> segment once signed in).
        from .services import next_release_version
        get_object_or_404(visible_graphs(request.user), pk=pk)
        user = request.user if request.user.is_authenticated else None
        return Response({"suggested": next_release_version(user=user)})

    def post(self, request, pk):
        graph = get_object_or_404(visible_graphs(request.user), pk=pk)
        release, n = snapshot_graph(graph, label=request.data.get("label"), user=request.user)
        release = (Release.objects
                   .prefetch_related("records__boundary", "records__candidate")
                   .get(pk=release.pk))
        return Response({"baked": n, "release": ReleaseSerializer(release).data})


class GraphVerifyView(APIView):
    """
    POST /api/graphs/{id}/verify/ — **Science CI 루프**. 그래프를 재-bake 하고 공표 기준(is_baseline)
    릴리스와 diff. 반환: {from(공표), to(그래프), value_diff, topology_diff, summary}.
    value_diff.delta = 그래프값 − 공표값 (내 편집이 경계를 얼마나 이동시켰나).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        graph = get_object_or_404(visible_graphs(request.user), pk=pk)
        baseline, d = verify_graph(graph)
        if baseline is None:
            return Response({"detail": "공표 기준(is_baseline) 릴리스가 없습니다."}, status=400)
        return Response(d)


class GraphProposeView(APIView):
    """
    POST /api/graphs/{id}/propose/ — 소유자가 샌드박스 그래프를 공표 기준 대비 제안(sandbox→proposed).
    body {comment}. 반환: {proposal, diff}. (P05.4)
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        graph = get_object_or_404(Graph, pk=pk)
        if not (request.user.is_staff or graph.owner_id == request.user.id):
            return Response({"detail": "Only the graph owner can propose it."}, status=403)
        try:
            proposal, diff = propose_graph(graph, request.user, comment=request.data.get("comment", ""))
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        return Response({"proposal": ProposalSerializer(proposal).data, "diff": diff}, status=201)


class ProposalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    제안 목록/상세 + ratify/reject (P05.4 = CI).
      GET  /api/proposals/            — 목록(?state=open)
      GET  /api/proposals/{id}/       — 상세 + 리뷰 diff(제안 vs baseline)
      POST /api/proposals/{id}/ratify — 권한자 승인 → 새 공표 Release + graph ratified
      POST /api/proposals/{id}/reject — 권한자 거절 → graph sandbox 복귀
    """
    queryset = Proposal.objects.select_related("graph", "baseline", "author", "reviewer", "result_release")
    serializer_class = ProposalSerializer
    permission_classes = [permissions.AllowAny]           # 리뷰는 공개 열람

    def get_queryset(self):
        qs = super().get_queryset()
        state = self.request.query_params.get("state")
        return qs.filter(state=state) if state else qs

    def retrieve(self, request, *args, **kwargs):
        proposal = self.get_object()
        data = ProposalSerializer(proposal).data
        data["diff"] = diff_graph_vs_release(proposal.graph, proposal.baseline)
        data["can_ratify"] = can_ratify(request.user, proposal)
        return Response(data)

    @action(detail=True, methods=["post"])
    def ratify(self, request, pk=None):
        proposal = self.get_object()
        if not can_ratify(request.user, proposal):
            return Response({"detail": "You are not a ratifying authority member."}, status=403)
        if proposal.state != Proposal.State.OPEN:
            return Response({"detail": f"Proposal already {proposal.state}."}, status=400)
        release = ratify_proposal(proposal, request.user, comment=request.data.get("comment", ""))
        return Response({"proposal": ProposalSerializer(proposal).data, "release": ReleaseSerializer(release).data})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        proposal = self.get_object()
        if not can_ratify(request.user, proposal):
            return Response({"detail": "You are not a ratifying authority member."}, status=403)
        if proposal.state != Proposal.State.OPEN:
            return Response({"detail": f"Proposal already {proposal.state}."}, status=400)
        reject_proposal(proposal, request.user, comment=request.data.get("comment", ""))
        return Response({"proposal": ProposalSerializer(proposal).data})


_GEO = {1: "Eon", 2: "Era", 3: "Period", 4: "Subperiod", 5: "Epoch", 6: "Age"}


def _pm_from_dist(dist):
    """distribution dict → 대칭 오차 ±pm(Myr). exact(GSSA 약속값)=0, 예산 sqrt-합, shape=HPD 반폭.
    ResultsPanel.summarizeDist 와 같은 사다리. 정보 없으면 None."""
    if not dist:
        return None
    if dist.get("fidelity") == "exact":
        return 0.0                                   # 약속값(GSSA) — 오차 없음
    budget = dist.get("budget") or {}
    combined = math.sqrt(sum((float(v) or 0.0) ** 2 for v in budget.values()))
    if combined > 0:
        return round(combined, 4)
    shape = dist.get("shape") or {}
    hpd = shape.get("hpd95")
    if isinstance(hpd, (list, tuple)) and len(hpd) == 2 and None not in hpd:
        return round(abs(hpd[1] - hpd[0]) / 2, 4)
    return None


def build_icc_levels(unit_base, unit_unc=None):
    """{unit_slug: base_ma} → ICC 중첩 컬럼. rank(Eon~Age) 별 밴드 = [bottom(older)=자기 base,
    top(younger)= **rank 이하(같거나 굵은) 중 자기보다 젊은 base 의 최대**, 없으면 0].
    coarser 경계(예: Permian base)가 sparse rank(Subperiod) 밴드를 제 구간에서 닫아준다
    — Pennsylvanian 은 Carboniferous 의 젊은 끝(=Permian base)에서 멈춘다. 부모 FK 에 의존하지 않는다
    (시드의 period→era 링크가 불완전해도 안전). gapless rank 는 종전 타일링과 동일 결과.
    unit_unc={slug: ±pm(Myr)} 있으면 밴드에 `pm`(경계 base 의 대칭 오차) 첨부."""
    from chrono.models import Unit
    unc = unit_unc or {}
    units = {u.slug: u for u in Unit.objects.filter(slug__in=unit_base.keys())}
    items = [(s, units[s].name, base, units[s].rank, units[s].color)
             for s, base in unit_base.items() if s in units]
    max_ma = max((it[2] for it in items), default=0.0)
    # coincident 경계(같은 GSSP 를 여러 rank/노드가 산출) 허용오차. 같은 지점이 modeled vs published
    # 로 미세하게(예: 251.902 vs 251.902182) 달라도 younger cap 으로 오인해 sliver 밴드가 생기지 않도록.
    # 0.001 Ma(1000년)는 ICC 실제 최소 경계 간격(홀로세 세분 ~0.0035 Ma)보다 작아 안전.
    EPS = 1e-3
    levels = []
    for rank_n in (1, 2, 3, 4, 5, 6):
        # 자기보다 굵거나 같은 rank 의 base 들(정렬) — top(younger cap) 후보
        caps = sorted(b for _, _, b, rk, _ in items if rk <= rank_n)
        us = sorted((it for it in items if it[3] == rank_n), key=lambda z: z[2])
        bands = []
        for s, name, b, rk, color in us:
            younger = [c for c in caps if c < b - EPS]
            bands.append({"slug": s, "name": name, "top": round(max(younger) if younger else 0.0, 4),
                          "bottom": round(b, 4), "color": color or None, "pm": unc.get(s)})
        if bands:
            levels.append({"rank": _GEO[rank_n], "rank_n": rank_n, "bands": bands})
    return {"max_ma": round(max_ma, 4), "levels": levels}


def _merge_source_boundaries(graph, merge_key):
    """merge 노드로 data 엣지를 통해 (재귀적으로) 흘러드는 boundary 노드 key 집합.
    merge 트리(그룹 내부 merge → 컬럼 merge → 최종)를 거슬러 올라가 tick(경계)들을 모은다.
    종단 merge 면 그래프의 전 boundary, 컬럼 merge 면 그 컬럼 소속 boundary 만 → 부분 차트."""
    from collections import defaultdict
    nature = dict(graph.nodes.values_list("key", "nature"))
    incoming = defaultdict(list)
    for s, t in graph.edges.filter(kind="data").values_list("source__key", "target__key"):
        incoming[t].append(s)
    seen, bnds, stack = set(), set(), [merge_key]
    while stack:
        for s in incoming.get(stack.pop(), []):
            if s in seen:
                continue
            seen.add(s)
            if nature.get(s) == "boundary":
                bnds.add(s)
            stack.append(s)          # merge/unit 는 계속 거슬러 올라간다
    return bnds


def merge_geometry(graph, merge_key, results):
    """merge 노드의 산출 = 그로 흘러드는 boundary(게이트웨이=chrono 정체성)들을 rank 별로 타일링.
    build_icc_levels 를 그대로 재사용하되, 전-게이트웨이가 아니라 이 merge 의 입력 subtree 로 한정."""
    bnds = _merge_source_boundaries(graph, merge_key)
    unit_base, unit_unc = {}, {}
    for gw in graph.gateways.select_related("node", "boundary"):
        if gw.boundary is None or gw.node.key not in bnds:
            continue
        if not gw.boundary.slug.startswith("base-"):
            continue
        dist = results.get(gw.node.key, {})
        v = dist.get("value_ma")
        if v is None:
            continue
        slug = gw.boundary.slug[len("base-"):]
        unit_base[slug] = float(v)
        unit_unc[slug] = _pm_from_dist(dist)
    return build_icc_levels(unit_base, unit_unc)


def _terminal_merge_key(graph):
    """종단 merge = 다른 노드로 나가는 data 엣지가 없는 merge 노드. 없으면 None."""
    merges = set(graph.nodes.filter(node_type__slug="merge").values_list("key", flat=True))
    if not merges:
        return None
    with_out = set(graph.edges.filter(kind="data", source__key__in=merges)
                   .values_list("source__key", flat=True))
    terminals = sorted(merges - with_out)
    return terminals[0] if terminals else None


class IccChartView(APIView):
    """
    GET /api/graphs/{id}/icc-chart/ — 그래프 산출물을 ICC 차트로.
    산출 주체는 **종단 merge 노드**(그로 흘러든 경계들을 타일링). `?node=<merge-key>` 로 특정
    컬럼 merge 의 부분 차트도 조회 가능. merge 없는 그래프는 종전대로 전 게이트웨이 타일링.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        from engine.evaluate import evaluate_graph
        graph = get_object_or_404(visible_graphs(request.user), pk=pk)
        run = graph.eval_runs.first() or evaluate_graph(graph)
        results = {r.node_key: (r.distribution or {}) for r in run.results.all()}

        merge_key = request.query_params.get("node") or _terminal_merge_key(graph)
        if merge_key:
            return Response({"graph": graph.slug, "node": merge_key,
                             **merge_geometry(graph, merge_key, results)})

        # merge 없는 그래프 — 종전 전-게이트웨이 경로
        unit_base, unit_unc = {}, {}
        for gw in graph.gateways.select_related("node", "boundary"):
            if gw.boundary is None:
                continue
            dist = results.get(gw.node.key, {})
            v = dist.get("value_ma")
            if v is not None and gw.boundary.slug.startswith("base-"):
                slug = gw.boundary.slug[len("base-"):]
                unit_base[slug] = float(v)
                unit_unc[slug] = _pm_from_dist(dist)
        return Response({"graph": graph.slug, **build_icc_levels(unit_base, unit_unc)})


class ReleaseIccChartView(APIView):
    """
    GET /api/releases/{id}/icc-chart/ — 공표 릴리스(BoundaryRecord)를 전 rank(Eon~Age)로.
    공표 ICC(ICS-2024/12)는 stage 까지 있어 5 컬럼. 미-bake 릴리스는 지연 bake.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        release = get_object_or_404(visible_releases(request.user), pk=pk)
        if not release.records.exists() and can_write_release(request.user, release):
            bake_release(release)
        unit_base, unit_unc = {}, {}
        for rec in release.records.select_related("boundary"):
            if rec.value_ma is None:
                continue
            bslug = rec.boundary.slug
            if bslug.startswith("base-"):
                slug = bslug[len("base-"):]
                unit_base[slug] = float(rec.value_ma)
                unit_unc[slug] = _pm_from_dist(rec.uncertainty)
        return Response({"release": release.version, **build_icc_levels(unit_base, unit_unc)})


class ReleaseNarrateView(APIView):
    """
    POST /api/releases/{id}/narrate/ — bake 의 짝. 릴리스를 rank 별 서술 문서로 렌더하고
    각 레코드 narrative 를 저장. 반환: {release, sections}.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        release = get_object_or_404(visible_releases(request.user), pk=pk)
        # Render for anyone who can see it; only owner/staff persist the narrative onto the shared records.
        sections = narrate_release(release, persist=can_write_release(request.user, release))
        return Response({"release": release.version, "sections": sections})

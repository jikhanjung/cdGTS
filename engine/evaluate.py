"""
평가 — 노드를 위상순으로 돌며 분포를 하류로 전파. 노드별 연산은 engine.kernels 가 담당
(joint-inference·correlation=역분산 결합, range=절단, pin=exact, 나머지=pass-through 폴백).

증분: 노드 content_hash = sha1(타입, params, 정렬된 입력 해시). 이전 run 의 같은 node_key 가
같은 해시면 결과 재사용(cached). leaf param 이 바뀌면 해시가 바뀌어 하류가 자동 dirty.

순환: 저장 시 'breaker(clamp/joint-inference) 없는 순환'은 이미 거부됨. breaker 를 지나는 순환은
위상정렬에서 남으므로, 남은 노드는 뒤에 붙여 available 한 상류만으로 1회 평가(진짜 joint 는 후속).
"""
import hashlib
import json
from collections import defaultdict

from . import kernels


def content_hash(type_slug, params, input_hashes):
    payload = json.dumps([type_slug, params, sorted(input_hashes)], sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def topo_order(node_keys, edges):
    """Kahn 위상순. 순환에 남는 노드는 임의 순서로 뒤에 붙인다."""
    keys = list(node_keys)
    adj = defaultdict(list)
    indeg = {k: 0 for k in keys}
    for s, t in edges:
        if s in indeg and t in indeg:
            adj[s].append(t)
            indeg[t] += 1
    queue = [k for k in keys if indeg[k] == 0]
    order = []
    while queue:
        n = queue.pop(0)
        order.append(n)
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
    leftover = [k for k in keys if k not in set(order)]   # 순환 잔여
    return order + leftover


def _compute(node, incoming, results, node_meta):
    """(distribution_dict|None, provenance_keys) 반환. 커널 디스패치. incoming = 포트순 입력 엣지.
    각 입력에 상류 노드 params 를 함께 실어 보낸다(age-depth 의 depth 등)."""
    prov = [e["source"] for e in incoming if e["source"] in results]
    inputs = []
    for e in incoming:
        r = results.get(e["source"])
        inputs.append({
            "dist": r["distribution"] if r else None,
            "params": node_meta.get(e["source"], {}).get("params", {}),
            "port": e["target_port"],
        })
    dist = kernels.compute(node["category"], node["slug"], inputs, node["params"])
    return dist, prov


def evaluate_graph(graph):
    """그래프를 평가해 EvalRun 을 만들고 반환. 증분 캐시는 직전 run 과 비교."""
    from .models import EvalRun, NodeResult

    insts = list(graph.nodes.select_related("node_type"))
    # order edge 는 데이터 흐름이 아니라 제약(경계 세로 포트 연결) — 평가 위상에서 제외, _certify 만 읽음.
    edges = [e for e in graph.edges.select_related("source", "target") if e.kind != "order"]

    node_meta = {
        n.key: {
            "slug": n.node_type.slug,
            "category": n.node_type.category,
            "params": n.params or {},
        }
        for n in insts
    }
    incoming = defaultdict(list)   # target key -> [{source, source_port, target_port}]
    for e in edges:
        incoming[e.target.key].append({"source": e.source.key, "source_port": e.source_port,
                                       "target_port": e.target_port})

    order = topo_order(node_meta.keys(), [(e.source.key, e.target.key) for e in edges])

    prev = graph.eval_runs.first()   # ordering=-id → 직전 run
    prev_results = {r.node_key: r for r in prev.results.all()} if prev else {}

    run = EvalRun.objects.create(graph=graph)
    results = {}
    rows = []
    stats = {"computed": 0, "cached": 0}

    for key in order:
        meta = node_meta[key]
        inc = incoming.get(key, [])
        input_hashes = [results[e["source"]]["hash"] for e in inc if e["source"] in results]
        h = content_hash(meta["slug"], meta["params"], input_hashes)

        prior = prev_results.get(key)
        if prior is not None and prior.content_hash == h:
            dist, prov, cached = prior.distribution, prior.provenance, True
            stats["cached"] += 1
        else:
            dist, prov = _compute(meta, inc, results, node_meta)
            cached = False
            stats["computed"] += 1

        results[key] = {"hash": h, "distribution": dist, "provenance": prov}
        rows.append(NodeResult(eval_run=run, node_key=key, content_hash=h,
                               distribution=dist, provenance=prov, cached=cached))

    NodeResult.objects.bulk_create(rows)
    run.stats = stats
    run.save(update_fields=["stats"])

    _certify(run, graph, results)
    return run


def duration_gate(pairs):
    """
    L2/L1b 지속시간 판정(순수) — **사용자가 assert 한 선후 쌍**(order edge)만 대상. 값 정렬 타일링 아님.
    떨어져 있는(관계 안 맺은) 두 경계는 판정하지 않는다 — "주장 없으면 판정 없음."
    pairs = [(older_dist, younger_dist, older_label, younger_label), ...]  (older = 큰 Ma).
      L2  = assert 된 쌍의 점추정 duration = older − younger ≤ 0(퇴화/영-길이/역전) 있으면 fail.
      L1b = 공분산 인지 지속시간이 2σ 안에서 ≤0 가능(gap < 2σ_gap)이면 warn.
    assert 된(양쪽 값이 풀린) 쌍이 하나도 없으면 둘 다 skip.
    반환 (l2, l1b, unresolved_notes[]).
    """
    from .kernels import duration_stats

    degenerate, unresolved, checked = 0, [], 0
    for older, younger, ol, yl in pairs:
        bo, by = (older or {}).get("value_ma"), (younger or {}).get("value_ma")
        if bo is None or by is None:
            continue
        checked += 1
        if bo - by <= 0:                                 # older 가 younger 보다 안 늙음 = 영-길이/역전
            degenerate += 1
        else:                                            # 공분산 인지 2σ 검사
            ds = duration_stats(older, younger)          # older = 큰 base
            if ds is not None:
                gap, sig = ds
                if sig > 0 and gap < 2 * sig:
                    unresolved.append(f"{ol}↔{yl} (Δ{round(gap, 3)} < 2σ {round(2 * sig, 3)})")
    if checked == 0:
        return "skip", "skip", []
    l2 = "pass" if degenerate == 0 else "fail"
    l1b = "warn" if unresolved else "pass"
    return l2, l1b, unresolved


def _certify(run, graph, results):
    """
    정합성 게이트 (coherence-gate.md).
      L0 구조 — cycle-breaker(clamp/joint-inference) 를 지나지 않는 순환이 남으면 fail.
      L1 순서 — authored `order` 제약(노드/엣지)이 있으면 그걸로, 없으면 게이트웨이 단조 휴리스틱 폴백(L1a).
      L1b 통계적 순서 — 인접 경계 지속시간이 2σ 안에서 ≤0 이 될 수 있으면(공분산 인지) "미해결" warn.
      L2 지속시간 — rank 별 타일링. 점추정 duration ≤ 0(퇴화/영-길이) → fail.
      L3 은 skip(후속: joint reconcile / clamp).
    """
    from .models import CoherenceCertificate
    from graph.dag import find_unbroken_cycles

    checks = {"L0": "pass", "L1": "skip", "L1b": "skip", "L2": "skip", "L3": "skip", "notes": []}
    passed = True

    # L0 구조 — breaker 를 잘라낸 데이터 그래프가 acyclic 이어야. (저장 검증의 런타임 재확인.)
    insts = list(graph.nodes.select_related("node_type"))
    breaker_keys = {n.key for n in insts
                    if n.node_type.category == "clamp" or n.node_type.slug == "joint-inference"}
    data_edges = [(e.source.key, e.target.key)
                  for e in graph.edges.select_related("source", "target") if e.kind != "order"]
    stuck = find_unbroken_cycles([n.key for n in insts], breaker_keys, data_edges)
    if stuck:
        checks["L0"] = "fail"
        checks["notes"].append(f"L0: 끊기지 않은 순환 {sorted(stuck)}")
        passed = False

    # L1 우선순위: order edge(경계 세로 포트 연결) > order 노드 > 게이트웨이 단조 휴리스틱.
    order_edges = list(graph.edges.filter(kind="order").select_related("source", "target"))
    order_nodes = [n for n in graph.nodes.select_related("node_type") if n.node_type.slug == "order"]
    if order_edges:
        # 각 order edge: source=더 오래된(큰 Ma), target=더 젊은(작은 Ma). source.value ≥ target.value 여야.
        violations, checked = 0, 0
        for e in order_edges:
            rs, rt = results.get(e.source.key), results.get(e.target.key)
            vs = (rs["distribution"] or {}).get("value_ma") if rs and rs["distribution"] else None
            vt = (rt["distribution"] or {}).get("value_ma") if rt and rt["distribution"] else None
            if vs is None or vt is None:
                continue
            checked += 1
            if float(vs) < float(vt):        # 오래된 경계가 젊은 경계보다 작음 = 역전
                violations += 1
        if checked:
            checks["L1"] = "pass" if violations == 0 else "fail"
            if violations:
                passed = False
    elif order_nodes:
        # 사람이 명시한 선후 제약 — 국소·authored·provenance. 위반 시 mode 로 FAIL/WARN.
        violations, hard_fail = 0, False
        for n in order_nodes:
            r = results.get(n.key)
            d = r["distribution"] if r else None
            if not d or d.get("ok") is None:
                continue
            if not d["ok"]:
                violations += 1
                if (n.params or {}).get("mode", "hard") == "hard":
                    hard_fail = True
        if violations == 0:
            checks["L1"] = "pass"
        elif hard_fail:
            checks["L1"] = "fail"; passed = False
        else:
            checks["L1"] = "warn"
    else:
        gateways = list(graph.gateways.select_related("boundary"))
        vals = []
        for gw in gateways:
            r = results.get(gw.node.key)
            if r and r["distribution"] and r["distribution"].get("value_ma") is not None:
                vals.append(r["distribution"]["value_ma"])
        if len(vals) >= 2:
            checks["L1"] = "pass" if vals == sorted(vals) or vals == sorted(vals, reverse=True) else "warn"
            passed = checks["L1"] != "warn"

    # L2/L1b 지속시간 — **assert 된 time unit** 의 duration(base−top)만 검사(공분산 인지).
    # 관계를 안 맺은 경계끼리는 판정하지 않는다(skip). order edge 인터리브로 유닛의 양 끝 경계를 찾는다:
    #   base(older).younger → unit.older ,  unit.younger → top(younger).older.
    # 유닛 없이 두 경계를 직접 order edge 로 이은 경우도 한 쌍으로 본다.
    unit_keys = {n.key for n in insts if n.node_type.slug == "unit"}
    bnd_keys = {n.key for n in insts if n.nature == "boundary"}
    gw_label = {gw.node.key: gw.boundary.slug[len("base-"):]
                for gw in graph.gateways.select_related("boundary", "node")
                if gw.boundary and gw.boundary.slug.startswith("base-")}
    lbl = lambda k: gw_label.get(k, k)                                    # noqa: E731
    dist_of = lambda k: (results.get(k) or {}).get("distribution")       # noqa: E731
    older_of, younger_of = {}, {}
    for e in order_edges:
        if e.target.key in unit_keys and e.target_port == "older":
            older_of[e.target.key] = e.source.key
        elif e.source.key in unit_keys and e.source_port == "younger":
            younger_of[e.source.key] = e.target.key
    pairs = []
    for u in unit_keys:                                                  # 유닛 span = base(older) − top(younger)
        ob, yb = older_of.get(u), younger_of.get(u)
        if ob is not None and yb is not None:
            pairs.append((dist_of(ob), dist_of(yb), lbl(ob), lbl(yb)))
    for e in order_edges:                                                # 유닛 없이 직접 이은 경계쌍
        if e.source.key in bnd_keys and e.target.key in bnd_keys:
            pairs.append((dist_of(e.source.key), dist_of(e.target.key), lbl(e.source.key), lbl(e.target.key)))
    if pairs:
        l2, l1b, unresolved = duration_gate(pairs)
        checks["L2"], checks["L1b"] = l2, l1b
        if l2 == "fail":
            passed = False
        if unresolved:
            checks["notes"].append("L1b 순서 통계적 미해결: " + ", ".join(unresolved))

    CoherenceCertificate.objects.create(eval_run=run, passed=passed, checks=checks)

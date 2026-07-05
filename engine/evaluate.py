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
    edges = list(graph.edges.select_related("source", "target"))

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


def _certify(run, graph, results):
    """
    정합성 게이트.
      L1 순서 — authored `order` 제약(노드)이 있으면 그걸로, 없으면 게이트웨이 단조 휴리스틱 폴백.
      L2 지속시간 — 게이트웨이가 덮는 **모든 유닛의 [base, top] 길이**를 rank 별 타일링으로 자동(파생) 검사.
        authored·sparse 한 order(L1) 를 보완하는 안전망. duration ≤ 0(퇴화/영-길이) → fail.
      L3 은 skip(후속: joint reconcile).
    """
    from .models import CoherenceCertificate

    checks = {"L0": "pass", "L1": "skip", "L2": "skip", "L3": "skip"}
    passed = True

    order_nodes = [n for n in graph.nodes.select_related("node_type") if n.node_type.slug == "order"]
    if order_nodes:
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

    # L2 지속시간 — 게이트웨이 산출값 → 유닛 base. rank 별로 base 오름차순 타일링해
    # 각 유닛 duration = base − top(이전 젊은 base, 가장 젊은 것은 0). ≤0 이면 퇴화 유닛 → fail.
    from chrono.models import Unit
    unit_base = {}
    for gw in graph.gateways.select_related("boundary", "node"):
        if gw.boundary is None or not gw.boundary.slug.startswith("base-"):
            continue
        r = results.get(gw.node.key)
        v = (r["distribution"] or {}).get("value_ma") if r and r["distribution"] else None
        if v is not None:
            unit_base[gw.boundary.slug[len("base-"):]] = float(v)
    if unit_base:
        rank_of = {u.slug: u.rank for u in Unit.objects.filter(slug__in=unit_base.keys())}
        degenerate = 0
        for rank_n in set(rank_of.values()):
            bases = sorted(b for s, b in unit_base.items() if rank_of.get(s) == rank_n)
            prev = 0.0
            for b in bases:
                if b - prev <= 0:            # 같은 rank 인접 base 동일/역전 = 영-길이 유닛
                    degenerate += 1
                prev = b
        checks["L2"] = "pass" if degenerate == 0 else "fail"
        if degenerate:
            passed = False

    CoherenceCertificate.objects.create(eval_run=run, passed=passed, checks=checks)

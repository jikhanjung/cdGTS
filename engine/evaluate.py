"""
pass-through 평가.

노드를 위상순으로 돌며 분포를 하류로 전파한다(계산 없음):
  - data(leaf)   : params["distribution"] (Distribution dict) 를 그대로 방출.
  - clamp pin     : exact(params["value"]) 방출 (GSSA = Clamp{pin}).
  - clamp 기타     : 입력 분포 통과.
  - process       : 첫 입력 분포 통과 + provenance 기록(실제 결합은 후속 커널).

증분: 노드 content_hash = sha1(타입, params, 정렬된 입력 해시). 이전 run 의 같은 node_key 가
같은 해시면 결과 재사용(cached). leaf param 이 바뀌면 해시가 바뀌어 하류가 자동 dirty.

순환: 저장 시 'breaker(clamp/joint-inference) 없는 순환'은 이미 거부됨. breaker 를 지나는 순환은
위상정렬에서 남으므로, 남은 노드는 뒤에 붙여 available 한 상류만으로 1회 평가(진짜 joint 는 후속).
"""
import hashlib
import json
from collections import defaultdict

from nodes.distribution import Distribution


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


def _compute(node, incoming, results):
    """(distribution_dict|None, provenance_keys) 반환. incoming = target 이 이 노드인 엣지들(포트순)."""
    prov = [e["source"] for e in incoming if e["source"] in results]
    cat = node["category"]
    slug = node["slug"]

    if cat == "data":
        return node["params"].get("distribution"), prov

    if slug == "pin":
        val = node["params"].get("value")
        return (Distribution.exact(val).to_dict() if val is not None else None), prov

    # clamp 기타 + process: 첫 입력 분포 통과.
    for e in incoming:
        r = results.get(e["source"])
        if r and r["distribution"] is not None:
            return r["distribution"], prov
    return None, prov


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
            dist, prov = _compute(meta, inc, results)
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
    """정합성 게이트 스텁 — 게이트웨이 경계 연대의 단조성만 대략 확인(L1), 나머지 skip."""
    from .models import CoherenceCertificate

    checks = {"L0": "pass", "L1": "skip", "L2": "skip", "L3": "skip"}
    passed = True

    gateways = list(graph.gateways.select_related("boundary"))
    vals = []
    for gw in gateways:
        r = results.get(gw.node.key)
        if r and r["distribution"] and r["distribution"].get("value_ma") is not None:
            vals.append(r["distribution"]["value_ma"])
    if len(vals) >= 2:
        # 단조(정렬돼 있으면 pass). 실제 층서순 대조는 후속.
        checks["L1"] = "pass" if vals == sorted(vals) or vals == sorted(vals, reverse=True) else "warn"
        passed = checks["L1"] != "warn"

    CoherenceCertificate.objects.create(eval_run=run, passed=passed, checks=checks)

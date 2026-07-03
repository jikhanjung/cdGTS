"""
DAG 불변식.

네트워크는 자유롭되 순환은 금지 — **단, joint-inference/clamp 노드를 지나는 순환은 허용**
(그 노드가 순환을 접거나 끊는다; cycles §). 구현: cycle-breaker 노드를 제거했을 때 남은
그래프가 acyclic 이어야 한다. 남으면 "끊기지 않은 순환" = 위반.

노드는 key 문자열로 다룬다(모델 비의존 — 저장 전 검증 가능).
"""


def find_unbroken_cycles(node_keys, breaker_keys, edges):
    """
    끊기지 않은 순환에 속한 노드 key 집합을 돌려준다(없으면 빈 set).

    node_keys: 전체 노드 key iterable
    breaker_keys: cycle-breaker 노드 key iterable (joint-inference / clamp)
    edges: (source_key, target_key) 튜플 iterable
    """
    breakers = set(breaker_keys)
    # breaker 를 잘라낸 부분그래프에서만 순환을 찾는다.
    live = {k for k in node_keys if k not in breakers}
    adj = {k: [] for k in live}
    indeg = {k: 0 for k in live}
    for s, t in edges:
        if s in live and t in live:
            adj[s].append(t)
            indeg[t] += 1

    # Kahn 위상정렬: 끝까지 못 비우면 남은 게 순환.
    queue = [k for k in live if indeg[k] == 0]
    removed = 0
    while queue:
        n = queue.pop()
        removed += 1
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)

    if removed == len(live):
        return set()
    return {k for k in live if indeg[k] > 0}

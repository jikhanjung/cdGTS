"""
계산 커널 — pass-through 를 넘어서는 실제 노드 연산.

NodeType.slug → 커널 함수 레지스트리. 미등록 slug 는 pass-through(첫 입력 통과)로 폴백.
이번 증분(결정론적, 해석적):
  - joint-inference / cross-section-correlation : **역분산 가중 결합**(독립 추정 결합 → 불확실성 축소).
후속(별도 과학 스택): age-depth 베이지안·joint MCMC·공분산 전파. 현재는 in-process numpy/scipy.

> GSSA(옛 pin clamp)는 이제 authored `published-age` leaf(exact)로 표현한다 — cycles.md §12 참조.
> `range_clamp`(절단정규)은 남겨두되(릴리스 reconcile 데모가 사용), 그래프 clamp 노드로는 쓰지 않는다.

분포는 nodes.distribution.Distribution 의 dict 표현을 주고받는다.
"""
import math

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.stats import truncnorm

from nodes.distribution import Distribution, component_sigmas, covariance

_Z95 = 1.959963984540054   # 95% 양측 z


def moments(d):
    """분포 dict → (mean, sigma1). 사용 불가면 None. sigma1 = 1σ."""
    if not d or d.get("value_ma") is None:
        return None
    mean = float(d["value_ma"])
    if d.get("fidelity") == "exact":
        return (mean, 0.0)
    shape = d.get("shape")
    if shape and shape.get("hpd95"):
        lo, hi = shape["hpd95"]
        return (mean, (float(hi) - float(lo)) / (2 * _Z95))
    budget = d.get("budget") or {}
    if budget:
        total = math.sqrt(sum(float(v) ** 2 for v in budget.values()))
        sigma_level = d.get("sigma") or 1
        return (mean, total / sigma_level)
    return (mean, 0.0)   # 값만 있고 분산 정보 없음 → 점질량 취급


def dist_from(mean, sigma1, note="", shared=None):
    """
    (mean, 1σ) → 분포 dict. σ=0 이면 exact, 아니면 decomposed(2σ, model 성분).
    shared = {ref: 1σ 기여} 있으면 공유 계통 성분을 실어 L4 `joint` 로 승격(공분산 재구성용).
    """
    if sigma1 <= 0:
        return Distribution.exact(round(mean, 6), note=note).to_dict()
    comps = [{"ref": r, "sigma": round(s, 6)} for r, s in (shared or {}).items() if s > 0]
    return Distribution(
        fidelity="joint" if comps else "decomposed", value_ma=round(mean, 6), sigma=2,
        budget={"model": round(2 * sigma1, 6)}, shared_components=comps, note=note,
    ).to_dict()


def inverse_variance_combine(inputs, note):
    """
    독립 추정들의 역분산 가중 결합. exact 입력이 있으면 그것이 지배(pin).
    공유 계통 성분은 가중치로 전파(out σ[ref] = Σ_i w_i·σ_i[ref]) — 하류 duration 공분산 보존.
    (marginal σ 자체는 독립 가정이라 공유원이 있으면 약간 과소 — 완전 상관 결합은 P06.4.)
    """
    valid = [(m[0], m[1], component_sigmas(d)) for d, m in ((d, moments(d)) for d in inputs) if m is not None]
    if not valid:
        return None
    exacts = [mu for (mu, s, _) in valid if s == 0]
    if exacts:
        return Distribution.exact(round(sum(exacts) / len(exacts), 6), note=note + " (pinned)").to_dict()
    weights = [1.0 / (s * s) for (_, s, _) in valid]
    wsum = sum(weights)
    mean = sum(w * mu for w, (mu, _, _) in zip(weights, valid)) / wsum
    sigma1 = math.sqrt(1.0 / wsum)
    refs = set().union(*[c.keys() for (_, _, c) in valid]) if valid else set()
    shared = {r: sum((w / wsum) * c.get(r, 0.0) for w, (_, _, c) in zip(weights, valid)) for r in refs}
    return dist_from(mean, sigma1, note=f"{note} (n={len(valid)})", shared=shared)


def calibration_constant(params):
    """
    공유 보정 파라미터(붕괴상수·monitor(FCs)·tracer) leaf. 저작된 분포를 방출하되, 그 불확실성 **전액을**
    자기 자신을 가리키는 `shared_component`(ref=symbol)로 태깅해 L4 `joint` 로 승격한다.
    → 이 노드를 소비하는 두 방사연대는 같은 ref 를 공유 → covariance() 가 계통오차 상관을 복원하고,
      duration 오차가 정직하게 상쇄된다(R04 #3 "공유 계통원" 의 실동작). 상수를 바꾸면 하류가 전부 재계산.
    이미 shared_components 가 저작돼 있으면 존중(재태깅 안 함). 값만 있고 불확실성 없으면 그대로 통과.
    """
    params = params or {}
    d = params.get("distribution")
    if not d or d.get("shared_components"):
        return d
    m = moments(d)
    if m is None or m[1] <= 0:          # 불확실성 없음 → 공분산 기여 없음, 원본 그대로
        return d
    ref = params.get("symbol") or params.get("kind") or "calibration"
    out = dict(d)
    out["shared_components"] = [{"ref": ref, "sigma": round(m[1], 6)}]
    if out.get("fidelity") in ("sym", "decomposed"):
        out["fidelity"] = "joint"       # 공유성분 태그 → 공분산 재구성 가능 층
    return out


def range_clamp(dist, lo, hi):
    """분포를 [lo, hi] 로 절단(절단정규). exact 는 구간으로 clip."""
    m = moments(dist)
    if m is None:
        return dist
    mean, sigma1 = m
    if sigma1 == 0:
        return Distribution.exact(round(min(max(mean, lo), hi), 6), note=f"clamp[{lo},{hi}]").to_dict()
    a, b = (lo - mean) / sigma1, (hi - mean) / sigma1
    tn = truncnorm(a, b, loc=mean, scale=sigma1)
    new_sigma1 = float(tn.std())
    scale = new_sigma1 / sigma1 if sigma1 > 0 else 1.0     # 절단으로 준 σ 비율만큼 공유성분도 축소
    shared = {r: s * scale for r, s in component_sigmas(dist).items()}
    return dist_from(float(tn.mean()), new_sigma1, note=f"range[{lo},{hi}]", shared=shared)


def _summarize_samples(samples, note):
    """MC 샘플 → 분포 dict. 왜도 있으면 shape(median+hpd95), 아니면 decomposed(2σ)."""
    med = float(np.median(samples))
    mean = float(np.mean(samples))
    std = float(np.std(samples))
    if std > 0 and abs(mean - med) > 0.1 * std:
        lo, hi = np.percentile(samples, [2.5, 97.5])
        return Distribution(
            fidelity="shape", value_ma=round(med, 6),
            shape={"median": round(med, 6), "hpd95": [round(float(lo), 6), round(float(hi), 6)]},
            note=note,
        ).to_dict()
    return dist_from(med, std, note=note)


def _blend_components(c1, s1, c2, s2, w1, w2):
    """두 horizon 의 공유 계통 성분을 보간 가중치로 선형 결합: out[ref] = w1·σ1[ref] + w2·σ2[ref]."""
    return {r: w1 * c1.get(r, 0.0) + w2 * c2.get(r, 0.0) for r in set(c1) | set(c2)}


def _linear_age_depth(horizons, target):
    """정렬된 (depth, mean, sigma1, comps) 에서 target 깊이의 연대를 선형 보간(구간 밖은 최근접 구간으로 외삽)."""
    depths = [h[0] for h in horizons]
    if target <= depths[0]:
        (d1, m1, s1, c1), (d2, m2, s2, c2) = horizons[0], horizons[1]
    elif target >= depths[-1]:
        (d1, m1, s1, c1), (d2, m2, s2, c2) = horizons[-2], horizons[-1]
    else:
        k = next(i for i in range(len(horizons) - 1) if depths[i] <= target <= depths[i + 1])
        (d1, m1, s1, c1), (d2, m2, s2, c2) = horizons[k], horizons[k + 1]
    if d2 == d1:   # 같은 깊이 두 점 → 결합
        return dist_from((m1 + m2) / 2, math.sqrt((s1 * s1 + s2 * s2)) / 2,
                         note="age-depth (coincident)", shared=_blend_components(c1, s1, c2, s2, 0.5, 0.5))
    t = (target - d1) / (d2 - d1)
    mean = m1 + (m2 - m1) * t
    var = (1 - t) ** 2 * s1 * s1 + t * t * s2 * s2   # 독립 두 점의 선형결합 분산(외삽 시 증가)
    where = "interp" if depths[0] <= target <= depths[-1] else "extrap"
    return dist_from(mean, math.sqrt(var), note=f"age-depth linear @ {target} ({where})",
                     shared=_blend_components(c1, s1, c2, s2, 1 - t, t))


def _spline_age_depth(horizons, target):
    """3차 스플라인 + MC 불확실성 전파(각 horizon 을 정규 샘플, 매 draw 스플라인 적합 후 target 평가)."""
    depths = np.array([h[0] for h in horizons])
    means = np.array([h[1] for h in horizons])
    sigmas = np.array([h[2] for h in horizons])
    order = np.argsort(depths)
    depths_s = depths[order]
    if np.any(np.diff(depths_s) <= 0):   # 중복/비단조 깊이 → 선형 폴백
        return _linear_age_depth(horizons, target)
    means_s, sigmas_s = means[order], sigmas[order]
    rng = np.random.default_rng(0)       # 결정론적(입력 고정 시 재현)
    n = 3000
    draws = means_s + sigmas_s * rng.standard_normal((n, len(means_s)))
    vals = np.array([CubicSpline(depths_s, draws[k])(target) for k in range(n)])
    return _summarize_samples(vals, note=f"age-depth spline @ {target}")


def age_depth_model(inputs, params):
    """
    dated horizon((depth, age) 들)에서 target_depth 의 연대를 보간. depth 는 상류 노드 params["depth"].
    method: linear(기본, 해석적) | spline(MC 전파). target_depth 없으면 결합으로 폴백.
    """
    params = params or {}
    method = params.get("method", "linear")

    horizons = []
    target_from_input = None
    for i in inputs:
        depth = (i.get("params") or {}).get("depth")
        if depth is None:
            continue
        m = moments(i.get("dist"))
        if m is not None:
            horizons.append((float(depth), m[0], m[1], component_sigmas(i.get("dist"))))
        elif target_from_input is None:
            target_from_input = float(depth)   # depth 만 있고 age 없는 입력 = 보간 target(경계 horizon)

    # target: undated horizon 입력 우선, 없으면 target_depth param 폴백
    target = target_from_input if target_from_input is not None else params.get("target_depth")

    dists = [i.get("dist") for i in inputs]
    if not horizons:
        return _first_non_null(dists)                       # 깊이 정보 없음 → pass-through
    if target is None:
        return inverse_variance_combine(dists, "age-depth (no target)")
    horizons.sort(key=lambda h: h[0])
    target = float(target)
    if len(horizons) == 1:
        _, m0, s0, c0 = horizons[0]
        return dist_from(m0, s0, note=f"age-depth @ {target} (single horizon)", shared=c0)
    if method == "spline" and len(horizons) >= 3:
        return _spline_age_depth(horizons, target)
    return _linear_age_depth(horizons, target)


def duration_stats(older, younger):
    """
    지속시간(= older − younger) 의 (값, 1σ). 공유 계통 성분이 있으면 Var = Var(o)+Var(y)−2·Cov 로
    정직하게 축소(상관 오차가 차이에서 상쇄). coherence-gate L2 가 요구하는 공분산 인지 duration.
    입력 부족이면 None.
    """
    mo, my = moments(older), moments(younger)
    if mo is None or my is None:
        return None
    dur = mo[0] - my[0]
    cov = covariance(older, younger)
    var = mo[1] ** 2 + my[1] ** 2 - 2 * cov
    return (dur, math.sqrt(max(var, 0.0)))


def order_check(inputs, params):
    """
    두 경계의 시간적 선후 **검사**(값 불변). 포트 older(아래·큰 Ma) / younger(위·작은 Ma).
    ok = age(older) ≥ age(younger) + Δ(min_gap). 결과는 분포가 아니라 판정 dict(kind=order).
    """
    params = params or {}
    gap_min = float(params.get("min_gap") or 0)
    older = younger = None
    for i in inputs:
        m = moments(i.get("dist"))
        if m is None:
            continue
        if i.get("port") == "older":
            older = m[0]
        elif i.get("port") == "younger":
            younger = m[0]
    if older is None or younger is None:
        return {"kind": "order", "ok": None, "note": "order: older/younger 입력 부족"}
    gap = round(older - younger, 6)
    ok = gap >= gap_min
    return {"kind": "order", "ok": ok, "gap": gap, "min_gap": gap_min,
            "note": f"order {'✓' if ok else '✗'}: gap {gap} {'≥' if ok else '<'} Δ {gap_min}"}


# --- 레지스트리 (slug → fn(inputs, params) → dist dict|None). inputs = [{dist, params, port}] ---
KERNELS = {
    "joint-inference": lambda inputs, params: inverse_variance_combine([i["dist"] for i in inputs], "joint"),
    "cross-section-correlation": lambda inputs, params: inverse_variance_combine([i["dist"] for i in inputs], "correlation"),
    "age-depth-model": age_depth_model,
    "order": order_check,
}


def _first_non_null(dists):
    for d in dists:
        if d is not None:
            return d
    return None


def compute(category, slug, inputs, params):
    """
    노드 하나의 출력 분포 계산.
    inputs = 포트순 입력 목록, 각 원소 {"dist": 분포|None, "params": 상류노드 params, "port": target_port}.
    """
    if slug == "calibration-constant":
        return calibration_constant(params)     # data leaf 지만 출력에 공유 계통원 태그를 실어 방출
    if category == "data":
        return (params or {}).get("distribution")
    if slug == "boundary":
        # 경계 점 — 상류 계산(data/process)이 준 연대를 통과. 입력 없으면 자기 공표값(fallback).
        d = _first_non_null([i["dist"] for i in inputs])
        return d if d is not None else (params or {}).get("distribution")
    fn = KERNELS.get(slug)
    if fn is not None:
        return fn(inputs, params)
    return _first_non_null([i["dist"] for i in inputs])   # pass-through 폴백

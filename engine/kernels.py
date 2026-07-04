"""
계산 커널 — pass-through 를 넘어서는 실제 노드 연산.

NodeType.slug → 커널 함수 레지스트리. 미등록 slug 는 pass-through(첫 입력 통과)로 폴백.
이번 증분(결정론적, 해석적):
  - joint-inference / cross-section-correlation : **역분산 가중 결합**(독립 추정 결합 → 불확실성 축소).
  - range(clamp) : **절단정규**(scipy truncnorm) 로 분포 재성형.
  - pin(clamp)   : exact(value) (GSSA 점질량).
후속(별도 과학 스택): age-depth 베이지안·joint MCMC·공분산 전파. 현재는 in-process numpy/scipy.

분포는 nodes.distribution.Distribution 의 dict 표현을 주고받는다.
"""
import math

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.stats import truncnorm

from nodes.distribution import Distribution

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


def dist_from(mean, sigma1, note=""):
    """(mean, 1σ) → 분포 dict. σ=0 이면 exact, 아니면 decomposed(2σ, model 성분)."""
    if sigma1 <= 0:
        return Distribution.exact(round(mean, 6), note=note).to_dict()
    return Distribution(
        fidelity="decomposed", value_ma=round(mean, 6), sigma=2,
        budget={"model": round(2 * sigma1, 6)}, note=note,
    ).to_dict()


def inverse_variance_combine(inputs, note):
    """독립 추정들의 역분산 가중 결합. exact 입력이 있으면 그것이 지배(pin)."""
    ms = [m for m in (moments(d) for d in inputs) if m is not None]
    if not ms:
        return None
    exacts = [mu for (mu, s) in ms if s == 0]
    if exacts:
        return Distribution.exact(round(sum(exacts) / len(exacts), 6), note=note + " (pinned)").to_dict()
    weights = [1.0 / (s * s) for (_, s) in ms]
    wsum = sum(weights)
    mean = sum(w * mu for w, (mu, _) in zip(weights, ms)) / wsum
    sigma1 = math.sqrt(1.0 / wsum)
    return dist_from(mean, sigma1, note=f"{note} (n={len(ms)})")


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
    return dist_from(float(tn.mean()), float(tn.std()), note=f"range[{lo},{hi}]")


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


def _linear_age_depth(horizons, target):
    """정렬된 (depth, mean, sigma1) 에서 target 깊이의 연대를 선형 보간(구간 밖은 최근접 구간으로 외삽)."""
    depths = [h[0] for h in horizons]
    if target <= depths[0]:
        (d1, m1, s1), (d2, m2, s2) = horizons[0], horizons[1]
    elif target >= depths[-1]:
        (d1, m1, s1), (d2, m2, s2) = horizons[-2], horizons[-1]
    else:
        k = next(i for i in range(len(horizons) - 1) if depths[i] <= target <= depths[i + 1])
        (d1, m1, s1), (d2, m2, s2) = horizons[k], horizons[k + 1]
    if d2 == d1:   # 같은 깊이 두 점 → 결합
        return dist_from((m1 + m2) / 2, math.sqrt((s1 * s1 + s2 * s2)) / 2, note="age-depth (coincident)")
    t = (target - d1) / (d2 - d1)
    mean = m1 + (m2 - m1) * t
    var = (1 - t) ** 2 * s1 * s1 + t * t * s2 * s2   # 독립 두 점의 선형결합 분산(외삽 시 증가)
    where = "interp" if depths[0] <= target <= depths[-1] else "extrap"
    return dist_from(mean, math.sqrt(var), note=f"age-depth linear @ {target} ({where})")


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
    target = params.get("target_depth")

    horizons = []
    for i in inputs:
        depth = (i.get("params") or {}).get("depth")
        m = moments(i.get("dist"))
        if depth is not None and m is not None:
            horizons.append((float(depth), m[0], m[1]))

    dists = [i.get("dist") for i in inputs]
    if not horizons:
        return _first_non_null(dists)                       # 깊이 정보 없음 → pass-through
    if target is None:
        return inverse_variance_combine(dists, "age-depth (no target)")
    horizons.sort()
    target = float(target)
    if len(horizons) == 1:
        _, m0, s0 = horizons[0]
        return dist_from(m0, s0, note=f"age-depth @ {target} (single horizon)")
    if method == "spline" and len(horizons) >= 3:
        return _spline_age_depth(horizons, target)
    return _linear_age_depth(horizons, target)


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
    if category == "data":
        return (params or {}).get("distribution")
    if slug == "pin":
        v = (params or {}).get("value")
        return Distribution.exact(v).to_dict() if v is not None else None
    if slug == "range":
        d = _first_non_null([i["dist"] for i in inputs])
        lo, hi = (params or {}).get("min"), (params or {}).get("max")
        if d is not None and lo is not None and hi is not None:
            return range_clamp(d, float(lo), float(hi))
        return d
    fn = KERNELS.get(slug)
    if fn is not None:
        return fn(inputs, params)
    return _first_non_null([i["dist"] for i in inputs])   # pass-through 폴백

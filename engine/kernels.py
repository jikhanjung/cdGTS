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


# --- 레지스트리 (slug → fn(inputs, params) → dist dict|None) ---
KERNELS = {
    "joint-inference": lambda inputs, params: inverse_variance_combine(inputs, "joint"),
    "cross-section-correlation": lambda inputs, params: inverse_variance_combine(inputs, "correlation"),
}


def _first_non_null(inputs):
    for d in inputs:
        if d is not None:
            return d
    return None


def compute(category, slug, inputs, params):
    """노드 하나의 출력 분포 계산. inputs = 입력 분포 dict 목록(포트순, 없으면 None)."""
    if category == "data":
        return params.get("distribution")
    if slug == "pin":
        v = params.get("value")
        return Distribution.exact(v).to_dict() if v is not None else None
    if slug == "range":
        d = _first_non_null(inputs)
        lo, hi = params.get("min"), params.get("max")
        if d is not None and lo is not None and hi is not None:
            return range_clamp(d, float(lo), float(hi))
        return d
    fn = KERNELS.get(slug)
    if fn is not None:
        return fn(inputs, params)
    return _first_non_null(inputs)   # pass-through 폴백

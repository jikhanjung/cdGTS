"""
계산 커널 — pass-through 를 넘어서는 실제 노드 연산.

NodeType.slug → 커널 함수 레지스트리. 미등록 slug 는 pass-through(첫 입력 통과)로 폴백.
이번 증분(결정론적, 해석적):
  - joint-inference / cross-section-correlation : **역분산 가중 결합**(독립 추정 결합 → 불확실성 축소).
> `order` 노드 커널은 devlog 149 에서 제거 — order 제약은 order **edge** 로 표현하고 _certify(L1)가 읽는다.
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


def _shared_comps(shared):
    """{ref: 1σ 기여} → shared_components 직렬화 형태. (음/영 기여 생략은 R05 §7 부채 — 부호 있는 loading 미지원.)"""
    return [{"ref": r, "sigma": round(float(s), 6)} for r, s in (shared or {}).items() if s > 0]


def dist_from(mean, sigma1, note="", shared=None):
    """
    (mean, 1σ) → 분포 dict. σ=0 이면 exact, 아니면 decomposed(2σ, model 성분).
    shared = {ref: 1σ 기여} 있으면 공유 계통 성분을 실어 L4 `joint` 로 승격(공분산 재구성용).
    """
    if sigma1 <= 0:
        return Distribution.exact(round(mean, 6), note=note).to_dict()
    comps = _shared_comps(shared)
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


def radiometric_age(inputs, params):
    """
    U-Pb 방사연대 leaf. 자기 authored 연대(분석오차만)를 방출하되, `calibration` 포트로 들어온 공유 보정
    노드(calibration-constant)의 계통 기여를 **접어넣는다**: 각 공유원 σ 를
      (a) budget.systematic 에 제곱합 → marginal σ 증가(그 연대 자신의 오차에 계통분이 더해짐),
      (b) shared_components 에 태그 → 같은 보정 노드를 쓰는 다른 연대와 covariance() 로 상관.
    값(value_ma)은 불변 — 이건 **재계산이 아니라 공분산 배선(L1)**. calibration 입력이 없으면 기존 불투명
    leaf 그대로(하위호환). → 두 연대를 같은 calibration 노드에 걸면 duration 오차가 상쇄(R04 vertical slice).
    """
    params = params or {}
    d = params.get("distribution")
    if not d:
        return d
    contrib = {}
    for i in inputs:
        if i.get("port") == "calibration":
            for ref, sig in component_sigmas(i.get("dist")).items():
                contrib[ref] = contrib.get(ref, 0.0) + sig       # 같은 ref 여러 입력 → 합
    if not contrib:
        return d                                                 # 보정 입력 없음 → 원본(불투명 leaf)
    out = dict(d)
    budget = dict(out.get("budget") or {})
    sys_add = math.sqrt(sum(s * s for s in contrib.values()))    # 여러 보정원 → 제곱합(독립 가정)
    budget["systematic"] = round(math.sqrt(budget.get("systematic", 0.0) ** 2 + sys_add ** 2), 6)
    out["budget"] = budget
    merged = {c["ref"]: c["sigma"] for c in out.get("shared_components", []) or []}
    for ref, sig in contrib.items():
        merged[ref] = merged.get(ref, 0.0) + sig
    out["shared_components"] = [{"ref": r, "sigma": round(s, 6)} for r, s in merged.items()]
    out["fidelity"] = "joint"                                    # 공유성분 태그 → 공분산 재구성 층
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


def _summarize_samples(samples, note, shared=None):
    """
    MC 샘플 → 분포 dict. 왜도 있으면 shape(median+hpd95), 아니면 decomposed(2σ).
    shared = {ref: 1σ 기여} 있으면 공유 계통 성분을 실어 `joint` 로 승격 — 왜도가 있어도 공분산 백본을 잃지 않는다
    (`shape` 와 `shared_components` 는 직교 필드이고, moments()/component_sigmas() 는 fidelity 라벨이 아니라
    필드를 읽는다. 라벨이 둘 중 하나를 강요하는 문제는 R05 §7 부채).
    """
    med = float(np.median(samples))
    mean = float(np.mean(samples))
    std = float(np.std(samples))
    if std > 0 and abs(mean - med) > 0.1 * std:
        lo, hi = np.percentile(samples, [2.5, 97.5])
        comps = _shared_comps(shared)
        return Distribution(
            fidelity="joint" if comps else "shape", value_ma=round(med, 6),
            shape={"median": round(med, 6), "hpd95": [round(float(lo), 6), round(float(hi), 6)]},
            shared_components=comps, note=note,
        ).to_dict()
    return dist_from(med, std, note=note, shared=shared)


def _blend_components(comps, weights):
    """
    공유 계통 성분의 선형 결합: out[ref] = Σ_i w_i·σ_i[ref] (공유원은 완전상관 → 가중치가 그대로 실린다).
    선형보간·스플라인 평가 **둘 다 입력 연대에 대해 선형**이라 같은 규칙이 적용된다.
    """
    out: dict[str, float] = {}
    for w, c in zip(weights, comps):
        for r, s in (c or {}).items():
            out[r] = out.get(r, 0.0) + w * s
    return out


def _spline_weights(depths_s, target):
    """
    CubicSpline 평가의 카디널 가중치 c_i (f(target) = Σ_i c_i·y_i). 평가가 y 에 대해 선형이므로
    각 horizon 에 단위 임펄스를 넣어 적합·평가하면 그 계수가 나온다(knot 수가 적어 비용 무시 가능, Σc_i = 1).
    """
    eye = np.eye(len(depths_s))
    return np.array([float(CubicSpline(depths_s, eye[i])(target)) for i in range(len(depths_s))])


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
                         note="age-depth (coincident)", shared=_blend_components([c1, c2], [0.5, 0.5]))
    t = (target - d1) / (d2 - d1)
    mean = m1 + (m2 - m1) * t
    var = (1 - t) ** 2 * s1 * s1 + t * t * s2 * s2   # 독립 두 점의 선형결합 분산(외삽 시 증가)
    where = "interp" if depths[0] <= target <= depths[-1] else "extrap"
    return dist_from(mean, math.sqrt(var), note=f"age-depth linear @ {target} ({where})",
                     shared=_blend_components([c1, c2], [1 - t, t]))


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
    comps_s = [horizons[i][3] for i in order]
    rng = np.random.default_rng(0)       # 결정론적(입력 고정 시 재현)
    n = 3000
    draws = means_s + sigmas_s * rng.standard_normal((n, len(means_s)))
    vals = np.array([CubicSpline(depths_s, draws[k])(target) for k in range(n)])
    # 공유 계통 성분은 MC 로 뽑지 않고 해석적으로 전파 — 평가가 y 에 대해 선형이라 카디널 가중치가 곧 결합 계수.
    shared = _blend_components(comps_s, _spline_weights(depths_s, target))
    return _summarize_samples(vals, note=f"age-depth spline @ {target}", shared=shared)


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


# --- 레지스트리 (slug → fn(inputs, params) → dist dict|None). inputs = [{dist, params, port}] ---
KERNELS = {
    "joint-inference": lambda inputs, params: inverse_variance_combine([i["dist"] for i in inputs], "joint"),
    "cross-section-correlation": lambda inputs, params: inverse_variance_combine([i["dist"] for i in inputs], "correlation"),
    "age-depth-model": age_depth_model,
}

# 레지스트리 람다는 docstring 을 못 실으므로 여기 둔다(노드 매뉴얼 생성기가 읽는다).
_KERNEL_NOTES = {
    "joint-inference": "역분산(정밀도) 가중 결합 — 같은 양의 **독립** 추정들을 합쳐 σ 를 줄인다. exact 입력이 있으면 그것이 지배(pin).",
    "cross-section-correlation": "`joint-inference` 와 **동일 커널**(note 문자열만 다름). 섹션별 연대를 역분산 평균한다. "
                                 "⚠️ 상관 자체는 계산하지 않고(δ13C 는 읽히지 않는 문자열) 저자의 배선 주장을 받는다. "
                                 "분산 검정(MSWD/χ²) 없음 — 불일치해도 조용히 평균된다. R05 는 이 타입의 **소멸**을 권고.",
}


def kernel_for(category, slug):
    """
    (category, slug) → (커널 라벨, 설명) — `compute()` 가 실제로 어디로 보내는지.

    ⚠️ **`compute()` 의 분기 우선순위와 반드시 일치해야 한다.** 두 곳에 흩어지면 매뉴얼이 거짓말을 한다
    (`test_kernels.py` 의 정합성 테스트가 시드된 전 slug 에 대해 이걸 검사한다).
    노드 매뉴얼 생성기(`manage.py node_manual`)가 유일한 소비자.
    """
    if slug in ("calibration-constant", "radiometric-uPb"):
        fn = {"calibration-constant": calibration_constant, "radiometric-uPb": radiometric_age}[slug]
        return (fn.__name__, (fn.__doc__ or "").strip())
    if category == "data":
        return ("(leaf)", "데이터 leaf — 커널 없음. 저작된 `params.distribution` 을 그대로 방출한다.")
    if slug == "boundary":
        return ("(pass-through + fallback)",
                "경계 점 — 상류가 준 연대를 통과. 입력이 없으면 자기 `params.distribution`(공표값) 으로 폴백.")
    fn = KERNELS.get(slug)
    if fn is not None:
        note = _KERNEL_NOTES.get(slug) or (fn.__doc__ or "").strip()
        return (getattr(fn, "__name__", slug).replace("<lambda>", slug), note)
    return ("(pass-through)",
            "커널 **미등록** → 첫 non-null 입력을 그대로 통과시킨다. 계산 노드가 아니라 의미론적/구조적 노드.")


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
    if slug == "radiometric-uPb":
        return radiometric_age(inputs, params)  # data leaf 지만 calibration 입력의 계통원을 접어넣어 방출
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

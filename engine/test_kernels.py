"""engine.kernels 단위 테스트 — 실제 계산(역분산 결합·절단). DB 불요."""
import math

from engine.kernels import (
    age_depth_model, compute, dist_from, inverse_variance_combine, moments, order_check, range_clamp,
)


def _sym(value, sigma1):
    return {"fidelity": "decomposed", "value_ma": value, "sigma": 1, "budget": {"model": sigma1}}


def _agein(port, value):
    return {"dist": {"fidelity": "exact", "value_ma": value}, "params": {}, "port": port}


# --- order (선후 검사) ---

def test_order_pass_when_older_is_older():
    r = order_check([_agein("older", 500), _agein("younger", 400)], {"min_gap": 0})
    assert r["kind"] == "order" and r["ok"] is True and r["gap"] == 100

def test_order_fail_when_inverted():
    r = order_check([_agein("older", 300), _agein("younger", 400)], {"min_gap": 0})
    assert r["ok"] is False and r["gap"] == -100

def test_order_min_gap_duration():
    # gap 60 < Δ 100 → 위반(최소 지속시간 미달)
    r = order_check([_agein("older", 460), _agein("younger", 400)], {"min_gap": 100})
    assert r["ok"] is False

def test_order_missing_input():
    assert order_check([_agein("older", 500)], {})["ok"] is None

def test_order_via_compute_dispatch():
    r = compute("clamp", "order", [_agein("older", 500), _agein("younger", 400)], {"min_gap": 0})
    assert r["ok"] is True


def _horizon(depth, value, sigma1):
    return {"dist": _sym(value, sigma1), "params": {"depth": depth}, "port": "dated_horizons"}


# --- moments ---

def test_moments_from_budget_2sigma():
    d = {"fidelity": "decomposed", "value_ma": 251.9, "sigma": 2, "budget": {"analytical": 0.024}}
    mean, s1 = moments(d)
    assert mean == 251.9 and abs(s1 - 0.012) < 1e-9   # 2σ=0.024 → 1σ=0.012


def test_moments_exact_is_zero_sigma():
    assert moments({"fidelity": "exact", "value_ma": 2500}) == (2500.0, 0.0)


def test_moments_from_shape_hpd():
    d = {"fidelity": "shape", "value_ma": 538.8, "shape": {"median": 538.8, "hpd95": [537.8, 539.8]}}
    _, s1 = moments(d)
    assert abs(s1 - (2.0 / (2 * 1.959963984540054))) < 1e-6


# --- 역분산 결합: 불확실성이 줄어든다 ---

def test_combine_shrinks_uncertainty():
    # 두 독립 추정 (같은 1σ) 결합 → 1σ 가 √2 배 작아진다.
    a, b = _sym(100.0, 1.0), _sym(102.0, 1.0)
    out = inverse_variance_combine([a, b], "joint")
    mean, s1 = moments(out)
    assert abs(mean - 101.0) < 1e-6                 # 동일 가중 → 중점
    assert abs(s1 - 1.0 / math.sqrt(2)) < 1e-6      # 1/√(1/1+1/1)


def test_combine_weights_by_precision():
    # 정밀한 추정(작은 σ)이 더 큰 가중.
    tight, loose = _sym(100.0, 0.5), _sym(110.0, 2.0)
    mean, _ = moments(inverse_variance_combine([tight, loose], "joint"))
    assert mean < 102.0                             # tight 쪽(100)으로 크게 당겨짐


def test_combine_ignores_signals_none():
    # 신호(분포 없음=None)는 결합에서 제외.
    out = inverse_variance_combine([None, _sym(538.8, 0.3), None], "correlation")
    assert moments(out)[0] == 538.8


def test_exact_input_pins_result():
    out = inverse_variance_combine([{"fidelity": "exact", "value_ma": 2500}, _sym(2490, 5)], "joint")
    assert out == {"fidelity": "exact", "value_ma": 2500.0, "note": "joint (pinned)"}


# --- range clamp: 절단 ---

def test_range_clamp_shifts_mean():
    # 하한이 평균 위면 절단정규 평균이 위로 이동.
    out = range_clamp(_sym(100.0, 1.0), 100.5, 200.0)
    mean, s1 = moments(out)
    assert mean > 100.5 and s1 < 1.0                # 절단 → 평균 상향 + 분산 축소


def test_range_clamp_exact_clips():
    out = range_clamp({"fidelity": "exact", "value_ma": 100.0}, 101.0, 200.0)
    assert out["value_ma"] == 101.0


# --- compute 디스패치 ---

def test_compute_passthrough_fallback():
    # calibration-transfer 는 미등록 커널 → 첫 입력 통과.
    d = _sym(251.9, 0.1)
    assert compute("process", "calibration-transfer", [{"dist": d, "params": {}}], {}) == d


def test_compute_pin():
    assert compute("clamp", "pin", [], {"value": 2500}) == {"fidelity": "exact", "value_ma": 2500}


def test_compute_data_emits_params():
    d = _sym(1.0, 0.1)
    assert compute("data", "radiometric-uPb", [], {"distribution": d}) == d


# --- age-depth-model ---

def test_age_depth_linear_midpoint():
    # depth 0→250, depth 10→260; target 5 → 255. var = 0.25·1+0.25·1 = 0.5.
    out = age_depth_model([_horizon(0, 250, 1.0), _horizon(10, 260, 1.0)],
                          {"method": "linear", "target_depth": 5})
    mean, s1 = moments(out)
    assert abs(mean - 255.0) < 1e-6
    assert abs(s1 - math.sqrt(0.5)) < 1e-6


def test_age_depth_extrapolation_grows_uncertainty():
    hs = [_horizon(0, 250, 1.0), _horizon(10, 260, 1.0)]
    s_in = moments(age_depth_model(hs, {"target_depth": 5}))[1]
    s_ex = moments(age_depth_model(hs, {"target_depth": 30}))[1]
    assert s_ex > s_in


def test_age_depth_single_horizon():
    assert moments(age_depth_model([_horizon(5, 255, 0.5)], {"target_depth": 5}))[0] == 255.0


def test_age_depth_no_depth_passes_through():
    inp = {"dist": _sym(251.9, 0.1), "params": {}, "port": "dated_horizons"}
    assert age_depth_model([inp], {"target_depth": 5}) == _sym(251.9, 0.1)


def test_age_depth_no_target_combines():
    out = age_depth_model([_horizon(0, 250, 1.0), _horizon(10, 252, 1.0)], {})
    assert moments(out)[1] < 1.0        # target 없음 → 결합(불확실성 축소)


def test_age_depth_spline_runs():
    hs = [_horizon(0, 250, 0.5), _horizon(10, 256, 0.5), _horizon(20, 260, 0.5)]
    out = age_depth_model(hs, {"method": "spline", "target_depth": 10})
    assert out is not None and moments(out)[0] is not None


# --- P06.1: 공유 계통 성분 · 공분산 · 지속시간 ---

from engine.kernels import duration_stats                       # noqa: E402
from nodes.distribution import Distribution, component_sigmas, covariance   # noqa: E402


def test_dist_from_shared_is_joint():
    d = dist_from(100.0, 1.0, shared={"decay-U": 0.5})
    assert d["fidelity"] == "joint" and d["shared_components"] == [{"ref": "decay-U", "sigma": 0.5}]
    d0 = dist_from(100.0, 1.0)
    assert d0["fidelity"] == "decomposed" and "shared_components" not in d0


def test_covariance_only_over_shared_refs():
    a = dist_from(700.0, 2.0, shared={"decay-U": 1.0, "tracer": 0.5})
    b = dist_from(600.0, 2.0, shared={"decay-U": 0.8})
    assert abs(covariance(a, b) - 1.0 * 0.8) < 1e-9          # only decay-U shared
    assert covariance(a, dist_from(600.0, 2.0, shared={"other": 1.0})) == 0.0
    assert covariance(a, dist_from(600.0, 2.0)) == 0.0       # no components


def test_duration_shrinks_with_shared_systematic():
    # 두 경계가 같은 붕괴상수(1.5 Ma 1σ)를 공유 → duration 오차가 독립 가정보다 작다.
    a = dist_from(700.0, 2.0, shared={"decay-U": 1.5})
    b = dist_from(600.0, 2.0, shared={"decay-U": 1.5})
    dur, s = duration_stats(a, b)
    assert abs(dur - 100.0) < 1e-9
    assert abs(s - math.sqrt(2**2 + 2**2 - 2 * 1.5 * 1.5)) < 1e-6   # Vo+Vy−2Cov
    _, s_indep = duration_stats(dist_from(700.0, 2.0), dist_from(600.0, 2.0))
    assert s < s_indep                                       # 공유 성분이 오차를 상쇄


def test_duration_variance_floored_at_zero():
    # 공유 성분이 과대여도 Var(dur) 는 음수로 안 감(√ 안전).
    a = dist_from(700.0, 1.0, shared={"c": 5.0})
    b = dist_from(600.0, 1.0, shared={"c": 5.0})
    assert duration_stats(a, b)[1] == 0.0


def test_combine_propagates_shared_components():
    a = dist_from(100.0, 1.0, shared={"cal": 0.6})
    b = dist_from(102.0, 1.0, shared={"cal": 0.4})
    out = inverse_variance_combine([a, b], "joint")
    assert out["fidelity"] == "joint"
    assert abs(component_sigmas(out)["cal"] - 0.5) < 1e-6    # 동일가중 0.5·0.6+0.5·0.4


def test_age_depth_linear_propagates_shared():
    h1 = {"dist": dist_from(250.0, 1.0, shared={"cal": 1.0}), "params": {"depth": 0}, "port": "h"}
    h2 = {"dist": dist_from(260.0, 1.0, shared={"cal": 1.0}), "params": {"depth": 10}, "port": "h"}
    out = age_depth_model([h1, h2], {"method": "linear", "target_depth": 5})
    assert abs(component_sigmas(out)["cal"] - 1.0) < 1e-6    # 0.5·1 + 0.5·1


def test_shared_components_roundtrip():
    d = dist_from(100.0, 1.0, shared={"x": 0.5})
    assert Distribution.from_dict(d).to_dict() == d


def test_passthrough_preserves_shared_components():
    d = dist_from(251.9, 0.3, shared={"decay-U": 0.2})
    assert compute("process", "calibration-transfer", [{"dist": d, "params": {}}], {}) == d


# --- P06.2: duration_gate (L2 fail / L1b covariance-aware warn) ---

from engine.evaluate import duration_gate                       # noqa: E402


def test_duration_gate_pass_when_well_separated():
    # 잘 분리된 assert 쌍 → L2 pass, L1b pass.
    pairs = [(dist_from(300, 0.5), dist_from(250, 0.5), "a", "b"),
             (dist_from(250, 0.5), dist_from(200, 0.5), "b", "c")]
    l2, l1b, notes, degen = duration_gate(pairs)
    assert l2 == "pass" and l1b == "pass" and notes == [] and degen == []


def test_duration_gate_l2_fail_on_degenerate():
    # assert 쌍의 두 base 동일 → 영-길이 유닛 → L2 fail. 퇴화 쌍 라벨을 함께 돌려준다.
    l2, _, _, degen = duration_gate([(dist_from(250, 0.5), dist_from(250, 0.5), "a", "b")])
    assert l2 == "fail"
    assert len(degen) == 1 and degen[0].startswith("a↔b")


def test_duration_gate_l1b_warn_on_2sigma_overlap():
    # gap 3.8, 각 σ1=1.5 → 2σ_gap≈4.24 > gap → 통계적으로 미해결(warn), L2 는 여전히 pass.
    pairs = [(dist_from(250.8, 1.5), dist_from(247.0, 1.5), "older", "younger")]
    l2, l1b, notes, degen = duration_gate(pairs)
    assert l2 == "pass" and l1b == "warn" and notes and degen == []


def test_duration_gate_shared_component_resolves_overlap():
    # 같은 gap·같은 marginal ± 이지만 공유 계통(σ 1.4)으로 σ_gap 축소 → 해소(pass).
    shared = {"decay-U": 1.4}
    pairs = [(dist_from(250.8, 1.5, shared=shared), dist_from(247.0, 1.5, shared=shared), "older", "younger")]
    l2, l1b, _, _ = duration_gate(pairs)
    assert l2 == "pass" and l1b == "pass"           # 공분산 인지: 겹침 해소


def test_duration_gate_no_assertion_skips():
    # 선후를 assert 하지 않으면(order edge 없음) 판정 자체가 없다 — 떨어져 있는 경계엔 경고 안 함.
    l2, l1b, notes, degen = duration_gate([])
    assert l2 == "skip" and l1b == "skip" and notes == [] and degen == []

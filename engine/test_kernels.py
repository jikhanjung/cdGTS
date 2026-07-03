"""engine.kernels 단위 테스트 — 실제 계산(역분산 결합·절단). DB 불요."""
import math

from engine.kernels import (
    age_depth_model, compute, dist_from, inverse_variance_combine, moments, range_clamp,
)


def _sym(value, sigma1):
    return {"fidelity": "decomposed", "value_ma": value, "sigma": 1, "budget": {"model": sigma1}}


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

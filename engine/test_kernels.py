"""engine.kernels 단위 테스트 — 실제 계산(역분산 결합·절단). DB 불요."""
import math

from engine.kernels import (
    age_depth_model, calibration_constant, compute, dist_from, inverse_variance_combine,
    moments, order_check, range_clamp,
)
from nodes.distribution import covariance


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


def test_compute_data_emits_params():
    d = _sym(1.0, 0.1)
    assert compute("data", "radiometric-uPb", [], {"distribution": d}) == d


# --- calibration-constant (공유 보정 파라미터 leaf, R04) ---

def test_calibration_constant_self_tags_shared_component():
    # 저작된 대칭 분포(σ1=0.03) → 자기 자신(symbol)을 가리키는 shared_component 로 태깅, joint 승격.
    d = _sym(28.201, 0.03)
    out = calibration_constant({"distribution": d, "symbol": "FCs", "kind": "monitor-age"})
    assert out["fidelity"] == "joint"
    assert out["value_ma"] == 28.201
    assert out["shared_components"] == [{"ref": "FCs", "sigma": 0.03}]

def test_calibration_constant_makes_dependents_covary():
    # 같은 보정 노드(FCs)를 태그로 상속한 두 연대 → covariance() 가 계통오차 상관을 복원.
    fcs = calibration_constant({"distribution": _sym(28.201, 0.05), "symbol": "FCs"})
    tag = fcs["shared_components"]                       # 하류 연대가 물려받는 공유원 태그
    age_a = {**_sym(250.0, 0.2), "shared_components": tag}
    age_b = {**_sym(300.0, 0.2), "shared_components": tag}
    assert covariance(age_a, age_b) == 0.05 * 0.05      # 공유 FCs 성분만큼 상관

def test_calibration_constant_passes_exact_through():
    # 불확실성 없는 값(exact)은 공분산 기여가 없으니 원본 그대로.
    d = {"fidelity": "exact", "value_ma": 28.201}
    assert calibration_constant({"distribution": d, "symbol": "FCs"}) == d

def test_calibration_constant_respects_authored_components():
    # 이미 shared_components 저작돼 있으면 재태깅하지 않음.
    d = {"fidelity": "joint", "value_ma": 28.201, "sigma": 1,
         "budget": {"model": 0.03}, "shared_components": [{"ref": "custom", "sigma": 0.01}]}
    assert calibration_constant({"distribution": d, "symbol": "FCs"}) == d

def test_calibration_constant_via_compute_dispatch():
    # data 카테고리지만 compute 가 slug 특수처리로 태그를 실어 방출(plain data early-return 우회).
    out = compute("data", "calibration-constant", [], {"distribution": _sym(28.201, 0.03), "symbol": "FCs"})
    assert out["shared_components"] == [{"ref": "FCs", "sigma": 0.03}]


# --- radiometric-uPb: calibration 입력을 접어넣는 소비자 (R04 vertical slice) ---

def _cal_in(ref, sigma):
    # calibration-constant 출력 모양(auto-tag 된 공유원)을 calibration 포트 입력으로.
    return {"dist": {"fidelity": "joint", "value_ma": 248.0, "shared_components": [{"ref": ref, "sigma": sigma}]},
            "params": {}, "port": "calibration"}


def test_radiometric_age_without_calibration_is_opaque_leaf():
    d = _sym(249.0, 0.5385)
    assert compute("data", "radiometric-uPb", [], {"distribution": d}) == d      # 하위호환: 입력 없으면 원본

def test_radiometric_age_folds_calibration_into_marginal_and_tag():
    d = {"fidelity": "decomposed", "value_ma": 249.0, "sigma": 1, "budget": {"analytical": 0.5385}}
    out = compute("data", "radiometric-uPb", [_cal_in("decay-238U", 1.4)], {"distribution": d})
    assert out["value_ma"] == 249.0                                  # 값 불변(재계산 아님)
    assert out["budget"]["systematic"] == 1.4                        # 계통 σ 가 marginal 에 접힘
    assert abs(moments(out)[1] - 1.5) < 1e-4                         # √(0.5385²+1.4²)≈1.5
    assert out["shared_components"] == [{"ref": "decay-238U", "sigma": 1.4}]  # 공분산 태그

def test_two_ages_sharing_one_calibration_node_covary():
    # 같은 보정 노드(같은 ref)를 소비한 두 연대 → duration_stats 가 공분산으로 σ_gap 축소.
    cal = _cal_in("decay-238U", 1.4)
    older = compute("data", "radiometric-uPb", [cal],
                    {"distribution": {"fidelity": "decomposed", "value_ma": 249.0, "sigma": 1, "budget": {"analytical": 0.5385}}})
    younger = compute("data", "radiometric-uPb", [cal],
                      {"distribution": {"fidelity": "decomposed", "value_ma": 247.0, "sigma": 1, "budget": {"analytical": 0.5385}}})
    assert abs(covariance(older, younger) - 1.96) < 1e-6            # 1.4·1.4
    from engine.kernels import duration_stats
    gap, sig = duration_stats(older, younger)
    assert gap == 2.0 and 2 * sig < 2.0                            # 상관으로 2σ_gap<2 → 해소(L1b pass)

def test_two_ages_with_different_calibration_refs_do_not_covary():
    # 서로 다른 보정 노드(ref 다름) → Cov 0 → 2σ_gap 큼(L1b warn).
    older = compute("data", "radiometric-uPb", [_cal_in("decay-238U·A", 1.4)],
                    {"distribution": {"fidelity": "decomposed", "value_ma": 249.0, "sigma": 1, "budget": {"analytical": 0.5385}}})
    younger = compute("data", "radiometric-uPb", [_cal_in("decay-238U·B", 1.4)],
                      {"distribution": {"fidelity": "decomposed", "value_ma": 247.0, "sigma": 1, "budget": {"analytical": 0.5385}}})
    assert covariance(older, younger) == 0.0
    from engine.kernels import duration_stats
    _, sig = duration_stats(older, younger)
    assert 2 * sig > 2.0


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


# --- R05 §2 회귀: spline 경로 공유 계통 성분 유실 ---
# 버그: _spline_age_depth 가 horizon 의 comps 를 안 읽어 method="spline" 이면 공분산 백본이 조용히 끊겼다
# (linear 은 _blend_components 로 보존). → 보간 방법 선택이 공분산 의미론을 바꿔선 안 된다.

def _horizon_shared(depth, value, sigma1, ref, ref_sigma):
    """공유 계통원이 marginal 예산에 접혀 있으면서 동시에 태깅된 horizon(radiometric-uPb 출력 모양)."""
    indep = math.sqrt(max(sigma1 ** 2 - ref_sigma ** 2, 0.0))
    return {"dist": {"fidelity": "joint", "value_ma": value, "sigma": 1,
                     "budget": {"analytical": indep, "systematic": ref_sigma},
                     "shared_components": [{"ref": ref, "sigma": ref_sigma}]},
            "params": {"depth": depth}, "port": "dated_horizons"}


def _shared_hs(ref="decay-238U", ref_sigma=0.4):
    return [_horizon_shared(d, v, 0.5, ref, ref_sigma)
            for d, v in ((10, 540.0), (20, 539.0), (40, 538.0), (50, 537.0))]


def test_age_depth_spline_keeps_shared_components():
    out = age_depth_model(_shared_hs(), {"method": "spline", "target_depth": 30})
    assert out["fidelity"] == "joint"
    # 전 horizon 이 같은 공유원을 σ=0.4 로 물고 카디널 가중치 합이 1 → 출력도 0.4 를 그대로 물려받는다.
    assert component_sigmas(out) == {"decay-238U": 0.4}


def test_age_depth_spline_and_linear_agree_on_shared_components():
    # 보간 방법은 값·marginal 에만 영향을 줘야 하고 공분산 구조를 바꿔선 안 된다.
    hs = _shared_hs()
    lin = age_depth_model(hs, {"method": "linear", "target_depth": 30})
    spl = age_depth_model(hs, {"method": "spline", "target_depth": 30})
    assert component_sigmas(spl) == component_sigmas(lin)


def test_age_depth_spline_shared_survives_into_duration_covariance():
    # 버그의 실제 증상: 두 경계가 같은 붕괴상수를 공유하는데 Cov 가 0 이라 duration 오차가 과대평가됐다.
    older = age_depth_model(_shared_hs(), {"method": "spline", "target_depth": 45})
    younger = age_depth_model(_shared_hs(), {"method": "spline", "target_depth": 15})
    assert covariance(older, younger) == 0.4 * 0.4                 # 수정 전 0.0
    _, sig_corr = duration_stats(older, younger)
    stripped = [{k: v for k, v in d.items() if k != "shared_components"} for d in (older, younger)]
    _, sig_naive = duration_stats(*stripped)
    assert sig_corr < sig_naive        # 공유원이 차이에서 상쇄 → 정직한 duration 은 더 좁다 (Ch.14 §16.5)


def test_summarize_samples_joint_keeps_shape_fields():
    # 왜도 + 공유성분 공존 시 둘 다 살아야 한다(라벨은 joint, shape 필드 유지) — fidelity enum 이 강요하던 손실.
    from engine.kernels import _summarize_samples
    skewed = [1.0] * 90 + [50.0] * 10                       # mean 이 median 에서 크게 벗어남
    out = _summarize_samples(skewed, "t", shared={"decay-U": 0.5})
    assert out["fidelity"] == "joint"
    assert out["shape"]["hpd95"] and component_sigmas(out) == {"decay-U": 0.5}


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

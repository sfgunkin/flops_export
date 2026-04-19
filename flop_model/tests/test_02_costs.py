"""Test 02: Unit cost formulas."""

import config
from src.b_costs import compute_pue, compute_raw_cost


def test_pue_cold_climate():
    assert compute_pue(10.0) == config.PHI
    assert compute_pue(14.9) == config.PHI
    assert compute_pue(-3.0) == config.PHI


def test_pue_at_threshold():
    assert compute_pue(config.THETA_BAR) == config.PHI


def test_pue_hot_climate():
    assert abs(compute_pue(25.0) - (1.08 + 0.015 * 10)) < 1e-10
    assert abs(compute_pue(37.1) - (1.08 + 0.015 * 22.1)) < 1e-10


def test_pue_range():
    for theta in range(-5, 41):
        pue = compute_pue(theta)
        assert 1.08 <= pue <= 1.46


def test_minimum_cost_bound(panel):
    min_bound = config.RHO + config.ETA
    for _, row in panel.iterrows():
        assert row["c_raw"] >= min_bound - 1e-6, \
            f"{row['country_name']}: c_raw={row['c_raw']:.4f} < {min_bound:.4f}"


def test_cost_increases_with_electricity():
    c1 = compute_raw_cost(1.08, 0.05, 10.0)
    c2 = compute_raw_cost(1.08, 0.10, 10.0)
    assert c2 > c1


def test_cost_increases_with_pue():
    c1 = compute_raw_cost(1.08, 0.05, 10.0)
    c2 = compute_raw_cost(1.20, 0.05, 10.0)
    assert c2 > c1


def test_cost_increases_with_construction():
    c1 = compute_raw_cost(1.08, 0.05, 8.0)
    c2 = compute_raw_cost(1.08, 0.05, 14.0)
    assert c2 > c1


def test_hardware_dominates(panel):
    for _, row in panel.iterrows():
        assert config.RHO / row["c_raw"] > 0.75, \
            f"{row['country_name']}: hardware share = {config.RHO/row['c_raw']:.1%}"


def test_cost_spread(panel):
    costs = panel["c_raw"]
    spread = (costs.max() - costs.min()) / costs.min()
    assert 0.05 < spread < 0.50, f"Cost spread = {spread:.1%}"


def test_cr_geq_raw_cost(panel):
    for _, row in panel.iterrows():
        assert row["c_cr"] >= row["c_raw"] - 1e-6


def test_construction_regression_n_obs(reg_diagnostics):
    assert reg_diagnostics["n_obs"] >= 30
    assert reg_diagnostics["n_obs"] <= 42


def test_construction_regression_r2(reg_diagnostics):
    assert reg_diagnostics["R2"] > 0.20


def test_construction_predicted_positive(panel):
    assert (panel["construction_per_watt"] > 0).all()


def test_construction_predicted_range(panel):
    assert (panel["construction_per_watt"] >= 3).all()
    assert (panel["construction_per_watt"] <= 25).all()

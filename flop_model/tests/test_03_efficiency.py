"""Test 03: xi computation."""

import config
from src.c_efficiency import compute_xi, compute_adj_cost


def test_xi_perfect_governance():
    assert compute_xi(1.0, 1.0) == 1.0


def test_xi_symmetric_at_equal_weight():
    assert abs(compute_xi(0.8, 0.6) - compute_xi(0.6, 0.8)) < 1e-10


def test_xi_decreases_with_worse_governance():
    assert compute_xi(0.5, 0.8) < compute_xi(0.9, 0.8)


def test_xi_decreases_with_worse_grid():
    assert compute_xi(0.8, 0.5) < compute_xi(0.8, 0.9)


def test_xi_range(panel):
    for _, row in panel.iterrows():
        assert 0 < row["xi"] <= 1.0, f"{row['country_name']}: xi = {row['xi']}"


def test_adj_cost_geq_cr_cost(panel):
    for _, row in panel.iterrows():
        assert row["c_adj"] >= row["c_cr"] - 1e-6


def test_adj_cost_equals_cr_when_xi_one(panel):
    for _, row in panel.iterrows():
        if abs(row["xi"] - 1.0) < 0.01:
            assert abs(row["c_adj"] - row["c_cr"]) < 0.01


def test_adj_cost_form_b_formula(panel):
    for _, row in panel.iterrows():
        expected = config.RHO + (row["c_cr"] - config.RHO) / row["xi"]
        assert abs(row["c_adj"] - expected) < 1e-6


def test_hardware_component_unchanged(panel):
    for _, row in panel.iterrows():
        non_hw_raw = row["c_cr"] - config.RHO
        non_hw_adj = row["c_adj"] - config.RHO
        assert abs(non_hw_adj - non_hw_raw / row["xi"]) < 1e-6

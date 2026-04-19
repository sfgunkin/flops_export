"""Test 01: Data completeness and range."""

import config


def test_country_count(panel):
    assert len(panel) == 85


def test_no_missing_values(panel):
    required = ["p_E_raw", "p_E_cr", "theta", "construction_per_watt",
                "G_governance", "R_grid", "capacity_mw", "demand_share"]
    for col in required:
        assert panel[col].notna().all(), f"Missing values in {col}"


def test_electricity_prices_positive(panel):
    assert (panel["p_E_raw"] > 0).all()
    assert (panel["p_E_cr"] > 0).all()


def test_electricity_prices_reasonable(panel):
    assert (panel["p_E_raw"] >= 0.004).all()
    assert (panel["p_E_raw"] <= 0.30).all()


def test_temperature_range(panel):
    assert (panel["theta"] >= -5).all()
    assert (panel["theta"] <= 40).all()


def test_governance_range(panel):
    assert (panel["G_governance"] >= 0).all()
    assert (panel["G_governance"] <= 1).all()


def test_grid_reliability_range(panel):
    assert (panel["R_grid"] >= 0).all()
    assert (panel["R_grid"] <= 1).all()


def test_exactly_13_subsidized(panel):
    assert panel["is_subsidized"].sum() == 13


def test_cr_equals_raw_for_nonsubsidized(panel):
    mask = ~panel["is_subsidized"]
    assert (panel.loc[mask, "p_E_cr"] == panel.loc[mask, "p_E_raw"]).all()


def test_cr_geq_raw_for_subsidized(panel):
    mask = panel["is_subsidized"]
    assert (panel.loc[mask, "p_E_cr"] >= panel.loc[mask, "p_E_raw"]).all()


def test_capacity_positive(panel):
    assert (panel["capacity_mw"] > 0).all()


def test_demand_shares_sum_to_one(panel):
    total = panel["demand_share"].sum()
    assert abs(total - 1.0) < 1e-6

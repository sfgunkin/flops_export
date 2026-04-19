"""Test 07: Economic reasonableness checks."""


def test_scandinavia_in_top_10(panel):
    for name in ["Norway", "Finland", "Sweden"]:
        rank = panel[panel["country_name"] == name]["rank_adj"].iloc[0]
        assert rank <= 10, f"{name} rank = {rank}"


def test_cost_spread_narrow(panel):
    ratio = panel["c_adj"].max() / panel["c_adj"].min()
    assert ratio < 2.5, f"Cost ratio = {ratio:.2f}"


def test_cost_minimum_above_rho_eta(panel):
    import config
    assert panel["c_raw"].min() >= config.RHO + config.ETA - 0.001


def test_xi_oecd_high(panel):
    oecd = ["Norway", "Finland", "Sweden", "Denmark", "Canada"]
    for name in oecd:
        xi = panel[panel["country_name"] == name]["xi"].iloc[0]
        assert xi > 0.80, f"{name}: xi = {xi}"

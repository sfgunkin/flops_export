"""Test 05: Equilibrium properties and propositions."""


ALL_SPECS = ["col1", "col2", "col3", "col4", "col6", "col7"]


def test_valid_regime_codes(results):
    valid = {"EE", "IE", "ID", "DD", "II"}
    for spec in ALL_SPECS:
        regimes = set(results[spec]["regime"].values())
        assert regimes <= valid, f"Invalid regimes in {spec}: {regimes - valid}"


def test_no_ed_regime(results):
    for spec in ALL_SPECS:
        assert "ED" not in results[spec]["regime"].values()


def test_hhi_bounded(results):
    for spec in ALL_SPECS:
        assert 0 <= results[spec]["hhi_training"] <= 1


def test_lambda_star_formula(panel, results):
    p_T = results["col4"]["p_T"]
    for iso in panel["country_iso3"]:
        expected = panel.loc[iso, "c_adj"] / p_T - 1
        actual = results["col4"]["lambda_star"][iso]
        assert abs(actual - expected) < 1e-6


def test_shadow_value_non_negative(results):
    for spec in ALL_SPECS:
        for j, mu in results[spec]["shadow_value"].items():
            assert mu >= -1e-6, f"{j}: mu = {mu}"


def test_training_price_positive(results):
    for spec in ALL_SPECS:
        assert results[spec]["p_T"] > 0

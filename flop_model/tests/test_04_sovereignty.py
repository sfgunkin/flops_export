"""Test 04: lambda matrix properties."""

import math


def test_domestic_lambda_zero(panel, lambdas_and_latency):
    lambdas, _ = lambdas_and_latency
    lam_b = lambdas["bilateral"]
    for iso in panel["country_iso3"]:
        assert lam_b[(iso, iso)] == 0.0


def test_sanctions_infinite(lambdas_and_latency):
    lambdas, _ = lambdas_and_latency
    lam_b = lambdas["bilateral"]
    assert lam_b[("IRN", "USA")] == math.inf
    assert lam_b[("RUS", "USA")] == math.inf


def test_lambda_non_negative(panel, lambdas_and_latency):
    lambdas, _ = lambdas_and_latency
    lam_b = lambdas["bilateral"]
    for (i, j), v in lam_b.items():
        assert v >= 0, f"lambda({i},{j}) = {v}"


def test_eu_internal_low(lambdas_and_latency):
    lambdas, _ = lambdas_and_latency
    lam_b = lambdas["bilateral"]
    eu_pairs = [("FRA", "DEU"), ("FRA", "NLD"), ("DEU", "ITA")]
    for a, b in eu_pairs:
        lam = lam_b[(a, b)]
        assert lam < 0.05, f"lambda({a},{b}) = {lam}"


def test_uniform_constant(panel, lambdas_and_latency):
    lambdas, _ = lambdas_and_latency
    lam_u = lambdas["uniform"]
    for (i, j), v in lam_u.items():
        if i != j and v < math.inf:
            assert abs(v - 0.10) < 1e-6, f"lambda_uniform({i},{j}) = {v}"

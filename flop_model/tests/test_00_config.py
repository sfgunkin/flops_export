"""Test 00: Parameter sanity checks."""

import config


def test_rho_value():
    """rho = P_GPU / (L * H * beta) ~ $1.358"""
    expected = 25000 / (3 * 8766 * 0.70)
    assert abs(config.RHO - expected) < 0.001


def test_rho_plus_eta_minimum():
    """Minimum possible unit cost = rho + eta ~ $1.508"""
    assert config.RHO + config.ETA > 1.50
    assert config.RHO + config.ETA < 1.52


def test_parameters_positive():
    for name, val in [("GAMMA_KW", config.GAMMA_KW), ("PHI", config.PHI),
                      ("DELTA", config.DELTA), ("TAU", config.TAU),
                      ("ALPHA1", config.ALPHA1), ("ALPHA2", config.ALPHA2),
                      ("ALPHA3", config.ALPHA3), ("ETA", config.ETA),
                      ("Q_TOTAL", config.Q_TOTAL)]:
        assert val > 0, f"{name} must be positive"


def test_omega_in_range():
    assert 0 < config.OMEGA < 1


def test_alpha_train_in_range():
    assert 0 < config.ALPHA_TRAIN < 1


def test_n_countries():
    assert config.N_COUNTRIES == 85

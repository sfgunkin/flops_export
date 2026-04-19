"""Shared test fixtures — load panel and results once."""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from src.a_ingest import ingest_all
from src.b_costs import estimate_construction_regression, compute_all_costs
from src.c_efficiency import compute_all_efficiency
from src.d_sovereignty import compute_all_sovereignty
from src.e_equilibrium import run_all_specifications


@pytest.fixture(scope="session")
def panel():
    """Load and compute the full panel (once per test session)."""
    p = ingest_all()
    p, _ = estimate_construction_regression(p)
    p = compute_all_costs(p)
    p = compute_all_efficiency(p)
    return p


@pytest.fixture(scope="session")
def lambdas_and_latency(panel):
    """Compute sovereignty matrices and latency."""
    return compute_all_sovereignty(panel)


@pytest.fixture(scope="session")
def results(panel, lambdas_and_latency):
    """Run all equilibrium specifications."""
    lambdas, latency = lambdas_and_latency
    return run_all_specifications(panel, lambdas, latency)


@pytest.fixture(scope="session")
def reg_diagnostics(panel):
    """Get the regression diagnostics (re-run since estimate modifies panel)."""
    p = ingest_all()
    _, diag = estimate_construction_regression(p)
    return diag

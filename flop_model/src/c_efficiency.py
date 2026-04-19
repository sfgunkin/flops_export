"""
Step C: ξ (production efficiency index) and efficiency-adjusted cost.

Input: Panel with costs from b_costs
Output: Panel with added columns: xi, c_adj, rank_adj
"""

import config
from .utils import rank_series


def compute_xi(G, R, omega=None):
    """
    v29 formula (no floor): ξ = G^ω · R^(1−ω)

    G and R are floored at XI_MIN to prevent division by zero.
    """
    if omega is None:
        omega = config.OMEGA
    G_safe = max(G, config.XI_MIN)
    R_safe = max(R, config.XI_MIN)
    return G_safe ** omega * R_safe ** (1 - omega)


def compute_adj_cost(c_cr, xi, rho=None):
    """
    Eq. (3) Form B: c_adj = ρ + (c_cr − ρ) / ξ

    Efficiency penalty applies only to non-hardware costs.
    """
    if rho is None:
        rho = config.RHO
    return rho + (c_cr - rho) / xi


def compute_adj_cost_form_a(c_cr, xi):
    """
    Form A: c_adj = c_cr / ξ
    Used in sensitivity analysis only.
    """
    return c_cr / xi


def compute_all_efficiency(panel, omega=None, rho=None, form="B"):
    """Add xi, c_adj, rank_adj to the panel."""
    if omega is None:
        omega = config.OMEGA
    if rho is None:
        rho = config.RHO

    panel = panel.copy()

    panel["xi"] = panel.apply(
        lambda r: compute_xi(r["G_governance"], r["R_grid"], omega), axis=1
    )

    if form == "B":
        panel["c_adj"] = panel.apply(
            lambda r: compute_adj_cost(r["c_cr"], r["xi"], rho), axis=1
        )
    else:  # Form A
        panel["c_adj"] = panel.apply(
            lambda r: compute_adj_cost_form_a(r["c_cr"], r["xi"]), axis=1
        )

    panel["rank_adj"] = rank_series(panel["c_adj"])

    return panel
